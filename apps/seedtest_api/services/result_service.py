from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError

from ..settings import Settings
from .adaptive_engine import get_session_state
from .db import get_engine, get_session
from .scoring import aggregate_from_session_state

try:
    # Optional Sentry for error notifications
    import sentry_sdk as _sentry_mod

    SENTRY_SDK: Any | None = _sentry_mod
except Exception:  # pragma: no cover - optional dependency
    SENTRY_SDK = None

logger = logging.getLogger(__name__)


def _has_db() -> bool:
    # Fresh read of settings so test-time env changes are respected
    return bool(Settings().DATABASE_URL)


def compute_result(
    session_id: str,
    force: bool = False,
    *,
    user_id: Optional[str] = None,
    exam_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute (and persist if DB configured) the exam result for a session.

    Returns a normalized API response document.
    """
    # Optional pre-check: if DB and exam_sessions row exists and is not completed, bail early
    if _has_db():
        try:
            with get_engine().connect() as conn:
                row = (
                    conn.execute(
                        text(
                            "SELECT completed FROM exam_sessions WHERE session_id = :sid"
                        ),
                        {"sid": session_id},
                    )
                    .mappings()
                    .first()
                )
                if row is not None:
                    completed = row.get("completed")
                    if not bool(completed):
                        return {
                            "session_id": session_id,
                            "status": "not_completed",
                            "detail": "session_not_completed",
                        }
        except Exception:
            # If table doesn't exist or any error occurs, do not block computation
            pass

    # If DB exists, try fetch existing when not forcing refresh
    if _has_db() and not force:
        existing = get_result_from_db(session_id)
        if existing is not None:
            return existing

    # Compute from session state
    state = get_session_state(session_id)
    if not state:
        # No session data
        return {
            "session_id": session_id,
            "status": "not_found",
            "detail": "session_not_found",
        }

    # capture org_id from state when available for persistence
    org_id = None
    try:
        org_val = state.get("org_id")
        org_id = int(org_val) if org_val is not None else None
    except Exception:
        org_id = None

    try:
        compute_ts = datetime.now(timezone.utc)
        result_json, _topics = aggregate_from_session_state(state)
        # Best-effort enrichment: fill explanations and correct answers from DB if missing
        try:
            _enrich_questions_from_db(result_json)
        except Exception:
            # Non-fatal enrichment failure
            pass

        score_raw = result_json.get("score", {}).get("raw")
        score_scaled = result_json.get("score", {}).get("scaled")
        standard_error = result_json.get("standard_error")
        percentile = result_json.get("percentile")

        # Persist if DB configured
        if _has_db():
            try:
                upsert_result(
                    session_id,
                    result_json,
                    score_raw,
                    score_scaled,
                    standard_error=standard_error,
                    percentile=percentile,
                    org_id=org_id,
                    user_id=user_id,
                    exam_id=exam_id,
                )
            except IntegrityError:
                # Rare concurrent race; treat as conflict and surface cached row if present
                existing = get_result_from_db(session_id, expected_user_id=user_id)
                if existing is not None:
                    return {**existing, "status": existing.get("status") or "ready"}
                return {"session_id": session_id, "status": "conflict"}
            except Exception:
                # Persist failure status if possible
                try:
                    _upsert_failed(session_id, user_id=user_id, exam_id=exam_id)
                except Exception:
                    pass
                # Log and forward to caller
                logger.exception("Result upsert failed: session_id=%s", session_id)
                if SENTRY_SDK is not None:
                    try:
                        SENTRY_SDK.capture_exception()
                    except Exception:
                        pass
                raise

        return {
            "session_id": session_id,
            "status": "ready",
            "computed_at": compute_ts,
            **result_json,
        }
    except Exception:
        # On any compute error, mark failed if DB and propagate
        if _has_db():
            try:
                _upsert_failed(session_id, user_id=user_id, exam_id=exam_id)
            except Exception:
                pass
        # Log the compute error
        logger.exception("Result compute failed: session_id=%s", session_id)
        if SENTRY_SDK is not None:
            try:
                SENTRY_SDK.capture_exception()
            except Exception:
                pass
        raise


def finish_exam(
    session_id: str,
    *,
    user_id: Optional[str] = None,
    exam_id: Optional[int] = None,
    force: bool = True,
) -> Dict[str, Any]:
    """Finalize an exam session and compute the result.

    Best-effort: if a DB is configured, mark the exam session as completed
    before computing the result; then delegate to compute_result (idempotent).
    Also triggers IRT ability update in background.
    """
    if _has_db():
        try:
            with get_engine().connect() as conn:
                conn.execute(
                    text(
                        """
                        UPDATE exam_sessions
                        SET completed = TRUE, updated_at = NOW()
                        WHERE session_id = :sid
                        """
                    ),
                    {"sid": session_id},
                )
        except Exception:
            # Non-fatal; continue to compute
            pass
    
    result = compute_result(session_id, force=force, user_id=user_id, exam_id=exam_id)
    
    # Trigger session completion hooks (including IRT theta update)
    if user_id:
        try:
            from ..services.session_hooks import on_session_complete
            on_session_complete(user_id, session_id)
        except Exception:
            # Non-fatal; hook failure should not block session completion
            pass
    
    return result


def get_result_from_db(
    session_id: str, expected_user_id: str | None = None
) -> Optional[Dict[str, Any]]:
    if not _has_db():
        return None
    with get_session() as s:
        sql = """
            SELECT session_id, user_id, exam_id, status, result_json, score_raw, score_scaled,
                   standard_error, percentile, created_at, updated_at
            FROM exam_results
            WHERE session_id = :sid
        """
        params = {"sid": session_id}
        if expected_user_id is not None:
            sql += " AND user_id = :uid"
            params["uid"] = expected_user_id
        row = (
            s.execute(
                text(
                    """
            """
                    + sql
                ),
                params,
            )
            .mappings()
            .first()
        )
        if not row:
            return None
        data = dict(row)
        return {
            "session_id": data["session_id"],
            "user_id": data.get("user_id"),
            "exam_id": data.get("exam_id"),
            "status": data["status"],
            **(data.get("result_json") or {}),
            "score_raw": data.get("score_raw"),
            "score_scaled": data.get("score_scaled"),
            "standard_error": data.get("standard_error"),
            "percentile": data.get("percentile"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
        }


def upsert_result(
    session_id: str,
    result_json: Dict[str, Any],
    score_raw: Any,
    score_scaled: Any,
    *,
    standard_error: Any | None = None,
    percentile: Any | None = None,
    org_id: Optional[int] = None,
    user_id: Optional[str] = None,
    exam_id: Optional[int] = None,
) -> None:
    # Use PostgreSQL INSERT..ON CONFLICT
    with get_session() as s:
        # Inline insert w/ ON CONFLICT via SQL text; bind result_json as JSONB
        stmt = text(
            """
            INSERT INTO exam_results (
                session_id, status, result_json, score_raw, score_scaled,
                standard_error, percentile, org_id, user_id, exam_id,
                created_at, updated_at
            )
            VALUES (
                :sid, 'ready', :rjson, :sraw, :sscaled, :se, :pct,
                :org, :uid, :eid, NOW(), NOW()
            )
            ON CONFLICT (session_id)
            DO UPDATE SET
              status = EXCLUDED.status,
              result_json = EXCLUDED.result_json,
              score_raw = EXCLUDED.score_raw,
              score_scaled = EXCLUDED.score_scaled,
              standard_error = EXCLUDED.standard_error,
              percentile = EXCLUDED.percentile,
              org_id = COALESCE(EXCLUDED.org_id, exam_results.org_id),
              user_id = COALESCE(EXCLUDED.user_id, exam_results.user_id),
              exam_id = COALESCE(EXCLUDED.exam_id, exam_results.exam_id),
              updated_at = NOW()
            """
        ).bindparams(sa.bindparam("rjson", type_=JSONB))

        s.execute(
            stmt,
            {
                "sid": session_id,
                "rjson": result_json,
                "sraw": score_raw,
                "sscaled": score_scaled,
                "se": standard_error,
                "pct": percentile,
                "org": org_id,
                "uid": user_id,
                "eid": exam_id,
            },
        )


def _upsert_failed(
    session_id: str, *, user_id: Optional[str] = None, exam_id: Optional[int] = None
) -> None:
    """Mark a result row as failed in case of compute/persist errors."""
    if not _has_db():
        return
    with get_session() as s:
        s.execute(
            text(
                """
                INSERT INTO exam_results (session_id, status, result_json, user_id, exam_id, created_at, updated_at)
                VALUES (:sid, 'failed', '{}'::jsonb, :uid, :eid, NOW(), NOW())
                ON CONFLICT (session_id)
                DO UPDATE SET status='failed', updated_at=NOW()
                """
            ),
            {"sid": session_id, "uid": user_id, "eid": exam_id},
        )
    # Emit a lightweight error signal to Sentry if available
    if SENTRY_SDK is not None:
        try:
            SENTRY_SDK.capture_message(
                f"exam_result_failed: session_id={session_id} user_id={user_id} exam_id={exam_id}",
                level="error",
            )
        except Exception:
            pass


def _enrich_questions_from_db(result_json: Dict[str, Any]) -> None:
    """Fill missing explanation and correct_answer for questions using DB lookups.

    Best-effort: silently returns if DB is not configured or on any error.
    """
    if not _has_db():
        return
    questions = result_json.get("questions") or []
    if not isinstance(questions, list) or not questions:
        return
    qids: List[int] = []
    for q in questions:
        qid = q.get("question_id")
        try:
            if qid is not None:
                qids.append(int(qid))
        except Exception:
            continue
    if not qids:
        return
    with get_engine().connect() as conn:
        # Explanations from questions
        rows = (
            conn.execute(
                text(
                    """
                SELECT question_id, explanation
                FROM questions
                WHERE question_id = ANY(:ids)
            """
                ),
                {"ids": qids},
            )
            .mappings()
            .all()
        )
        exp_map = {int(r["question_id"]): r.get("explanation") for r in rows}
        # Correct answers from choices
        rows2 = (
            conn.execute(
                text(
                    """
                SELECT question_id, content AS correct_answer
                FROM choices
                WHERE question_id = ANY(:ids) AND is_correct = TRUE
                """
                ),
                {"ids": qids},
            )
            .mappings()
            .all()
        )
        ans_map = {int(r["question_id"]): r.get("correct_answer") for r in rows2}
    # Apply enrichment if fields missing
    for q in questions:
        try:
            qid = (
                int(q.get("question_id")) if q.get("question_id") is not None else None
            )
        except Exception:
            qid = None
        if qid is None:
            continue
        if not q.get("explanation") and qid in exp_map:
            q["explanation"] = exp_map[qid]
        if not q.get("correct_answer") and qid in ans_map:
            q["correct_answer"] = ans_map[qid]
