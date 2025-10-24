from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..deps import User, get_current_user, require_session_access
from ..schemas.result import ResultContract
from ..services.result_query import list_results_keyset
from ..services.result_service import compute_result, get_result_from_db
from ..settings import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}", tags=["results"])


# --- Helpers for opaque cursor encoding/decoding ---
def _b64url_encode(b: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    import base64

    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _encode_cursor_v1(ts_iso: str, item_id: str, field: str) -> str:
    import json

    payload = {"ts": ts_iso, "id": str(item_id), "field": field}
    return "v1:" + _b64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )


def _decode_cursor(token: str) -> tuple[str, str] | None:
    """Return (ts_iso, id) if decodable, else None."""
    try:
        if token.startswith("v1:"):
            raw = _b64url_decode(token[3:])
            import json

            obj = json.loads(raw.decode("utf-8"))
            ts = obj.get("ts")
            cid = obj.get("id")
            if isinstance(ts, str) and isinstance(cid, str | int):
                return ts, str(cid)
        # Future: support other versions
    except Exception:
        return None
    return None


# Request body model for POST force override
class ForceRequest(BaseModel):
    force: bool = False


@router.post(
    "/exams/{session_id}/result",
    summary="Create or refresh exam result (idempotent)",
    description=(
        "Compute and persist the result for a completed session.\n\n"
        "Behavior:\n"
        "- If a cached result exists with status=ready and force=false, returns the cached result.\n"
        "- If force=true (query or body), recomputes and upserts (idempotent via ON CONFLICT on session_id).\n"
        "- Requires authorization and access to the target session.\n\n"
        "Query/body parameters:\n"
        "- force (bool): when true, recompute even if cached.\n"
        "- exam_id (int, optional): persist exam_id alongside the result if provided.\n\n"
        "- stable (bool, optional): when true, omit volatile fields (timestamps) from the response;\n"
        "  when false, force-include them; when omitted, the server setting RESULT_EXCLUDE_TIMESTAMPS applies.\n\n"
        "Response schema (ResultContract):\n\n"
        "| Field | Type | Description |\n"
        "|---|---|---|\n"
        "| exam_session_id | string | Session identifier |\n"
        "| user_id | string | Owner of the session (student) |\n"
        "| exam_id | integer | Exam identifier (optional) |\n"
        "| score | number | Scaled score |\n"
        "| ability_estimate | number | Final ability estimate (θ) |\n"
        "| standard_error | number | Standard error of θ |\n"
        "| percentile | number | Percentile (0-100) |\n"
        "| topic_breakdown | array | Per-topic aggregates: topic, correct, total, accuracy |\n"
        "| questions | array | Per-question summary (id, correctness, answers, explanation, topic) |\n"
        "| recommendations | array | Study recommendations (strings) |\n"
        "| created_at | string | ISO timestamp of result creation |\n"
        "| status | string | 'ready' or 'failed' |\n\n"
        "Error codes:\n\n"
        "- 400: invalid request or not finished\n"
        "- 401: unauthorized\n"
        "- 403: forbidden (no access to session)\n"
        "- 404: session/result not found\n"
        "- 409: conflict (rare concurrent upsert)\n"
        "- 500: internal error\n"
    ),
    response_model=ResultContract,
    response_model_exclude={"score_detail", "updated_at"},
    # Keep None fields in POST response so contract keyset remains stable (exam_id may be null)
    response_model_exclude_none=False,
    responses={
        200: {
            "description": "Result created/refreshed",
            "content": {
                "application/json": {
                    "example": {
                        "exam_session_id": "d1f67...89",
                        "user_id": "42",
                        "exam_id": 5,
                        "score": 128.5,
                        "score_detail": {"raw": 34.0, "scaled": 128.5},
                        "ability_estimate": 0.55,
                        "standard_error": 0.32,
                        "percentile": 85,
                        "topic_breakdown": [
                            {
                                "topic": "대수",
                                "correct": 5,
                                "total": 7,
                                "accuracy": 0.714,
                            }
                        ],
                        "questions": [
                            {
                                "question_id": 101,
                                "is_correct": True,
                                "user_answer": "C",
                                "correct_answer": "C",
                                "explanation": "...",
                                "topic": "기하",
                            }
                        ],
                        "recommendations": ["확률통계 영역 복습 권장"],
                        "created_at": "2025-10-18T09:45:00Z",
                        "updated_at": "2025-10-18T10:00:00Z",
                        "status": "ready",
                    }
                }
            },
        }
    },
)
async def create_or_refresh_result(
    session_id: str,
    force: bool = Query(
        default=False,
        description="Force recompute even if cached (deprecated, prefer body)",
    ),
    exam_id: int | None = Query(
        default=None, description="Optional exam id to persist with result"
    ),
    stable: bool | None = Query(
        default=None,
        description=(
            "When true, omit volatile fields (timestamps). When false, force include. "
            "When omitted, uses RESULT_EXCLUDE_TIMESTAMPS setting."
        ),
    ),
    body: ForceRequest | None = None,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_session_access),
) -> Any:
    # Note: We sometimes return a Response to bypass response_model serialization when excluding timestamps
    # Body.force overrides query param if provided
    effective_force = body.force if body is not None else force
    user_id = current_user.user_id if current_user else None
    try:
        res = compute_result(
            session_id, force=effective_force, user_id=user_id, exam_id=exam_id
        )
    except Exception:
        # Service already marks status=failed and logs; return generic 500
        raise HTTPException(500, "Internal error computing result")
    status = str(res.get("status") or "").lower()
    if status == "not_found":
        raise HTTPException(404, "Result not found or exam not completed")
    if status == "not_completed":
        raise HTTPException(400, "Exam session not completed")
    if status == "conflict":
        raise HTTPException(409, "conflict")
    # Build contract-shaped response
    resp = _to_contract_response(
        res,
        fallback_session_id=session_id,
        user_id=user_id,
        exam_id=exam_id,
        stable=stable,
    )
    # IMPORTANT: When timestamps are excluded (stable=true or env flag), bypass
    # response_model serialization to avoid Pydantic re-inserting fields as null.
    try:
        from ..settings import Settings

        exclude_ts = (
            bool(stable)
            if stable is not None
            else bool(Settings().RESULT_EXCLUDE_TIMESTAMPS)
        )
        if exclude_ts:
            return JSONResponse(content=resp)
    except Exception:
        # Non-fatal: fall back to default behavior
        pass
    return resp


@router.get(
    "/exams/{session_id}/result",
    summary="Get exam result (optionally refresh)",
    description=(
        "Retrieve a cached result by session_id, or recompute when refresh=true.\n\n"
        "Behavior:\n"
        "- Default: fetch from DB; if missing or not 'ready', returns 404.\n"
        "- refresh=true: recompute + upsert, then return fresh result.\n"
        "- Requires authorization and access to the target session.\n\n"
        "Response schema (ResultContract): same as POST.\n\n"
        "Query parameter overrides for response shape:\n"
        "- stable (bool): true omits timestamps; false forces include; omitted uses server setting.\n\n"
        "Error codes:\n\n"
        "- 400: invalid request\n"
        "- 401: unauthorized\n"
        "- 403: forbidden (no access to session)\n"
        "- 404: result not found / not ready\n"
        "- 500: internal error\n"
    ),
    response_model=ResultContract,
    response_model_exclude={"score_detail", "updated_at"},
    response_model_exclude_none=True,
    responses={
        200: {
            "description": "Result found",
            "content": {
                "application/json": {
                    "example": {
                        "exam_session_id": "d1f67...89",
                        "user_id": "42",
                        "exam_id": 5,
                        "score": 128.5,
                        "score_detail": {"raw": 34.0, "scaled": 128.5},
                        "ability_estimate": 0.55,
                        "standard_error": 0.32,
                        "percentile": 85,
                        "topic_breakdown": [
                            {
                                "topic": "대수",
                                "correct": 5,
                                "total": 7,
                                "accuracy": 0.714,
                            }
                        ],
                        "questions": [
                            {
                                "question_id": 101,
                                "is_correct": True,
                                "user_answer": "C",
                                "correct_answer": "C",
                                "explanation": "...",
                                "topic": "기하",
                            }
                        ],
                        "recommendations": ["확률통계 영역 복습 권장"],
                        "created_at": "2025-10-18T09:45:00Z",
                        "updated_at": "2025-10-18T10:00:00Z",
                        "status": "ready",
                    }
                }
            },
        },
        404: {"description": "Result not found"},
    },
)
async def get_result(
    session_id: str,
    refresh: bool = Query(default=False, description="Recompute if true"),
    exam_id: int | None = Query(
        default=None,
        description="Optional exam id to persist with result when recomputing",
    ),
    stable: bool | None = Query(
        default=None,
        description=(
            "When true, omit volatile fields (timestamps). When false, force include. "
            "When omitted, uses RESULT_EXCLUDE_TIMESTAMPS setting."
        ),
    ),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_session_access),
) -> dict[str, Any]:
    if refresh:
        user_id = current_user.user_id if current_user else None
        try:
            res = compute_result(
                session_id, force=True, user_id=user_id, exam_id=exam_id
            )
        except Exception:
            raise HTTPException(500, "Internal error computing result")
        status = str(res.get("status") or "").lower()
        if status == "not_found":
            raise HTTPException(404, "Result not found or exam not completed")
        if status == "not_completed":
            raise HTTPException(400, "Exam session not completed")
        if status == "conflict":
            raise HTTPException(409, "conflict")
        return _to_contract_response(
            res,
            fallback_session_id=session_id,
            user_id=user_id,
            exam_id=exam_id,
            stable=stable,
        )
    # DB guard: if student, enforce ownership via query; for teacher/admin, omit user constraint
    expected_uid = (
        current_user.user_id if (current_user and current_user.is_student()) else None
    )
    db_res = get_result_from_db(session_id, expected_user_id=expected_uid)
    if db_res is None:
        # Strict mode: not found without refresh
        raise HTTPException(404, "Result not found or exam not completed")
    # If found but not ready (e.g., failed/pending), do not return body here; require refresh
    if str(db_res.get("status") or "").lower() != "ready":
        raise HTTPException(404, "Result not found or exam not completed")
    return _to_contract_response(db_res, fallback_session_id=session_id, stable=stable)


def _to_contract_response(
    src: dict,
    *,
    fallback_session_id: str,
    user_id: str | None = None,
    exam_id: int | None = None,
    stable: bool | None = None,
) -> dict[str, Any]:
    """Map internal result structure (DB or computed) to the UI contract.

    Expected src may be either DB-enriched (from get_result_from_db) or compute_result output.
    """
    # Session / identity
    sid = src.get("session_id") or fallback_session_id
    uid = src.get("user_id") or user_id
    eid = src.get("exam_id") or exam_id

    # Scores
    # Prefer explicit top-level fields if present (from DB path), else nested result_json.score
    score_scaled = src.get("score_scaled")
    if score_scaled is None:
        score_scaled = (
            (src.get("score") or {}).get("scaled")
            if isinstance(src.get("score"), dict)
            else None
        )
    score_raw = src.get("score_raw")
    if score_raw is None:
        score_raw = (
            (src.get("score") or {}).get("raw")
            if isinstance(src.get("score"), dict)
            else None
        )

    # Ability/SE/percentile (optional)
    ability = src.get("ability_estimate")
    se = src.get("standard_error")
    pct = src.get("percentile")

    # Topics -> topic_breakdown
    topics = src.get("topics") or []
    topic_breakdown = topics if isinstance(topics, list) else []

    # Questions list if provided in src (optional)
    questions = src.get("questions") or []

    # Recommendations
    recs = src.get("recommendations") or []

    # Timestamps / status
    # Normalize created_at to ISO string if a datetime was provided
    created_at = src.get("created_at")
    if created_at is not None and not isinstance(created_at, str):
        try:
            from datetime import datetime, timezone

            if isinstance(created_at, datetime):
                # Convert to ISO 8601 and prefer Z suffix for UTC
                iso = created_at.astimezone(timezone.utc).isoformat()
                created_at = iso.replace("+00:00", "Z")
            else:
                created_at = str(created_at)
        except Exception:
            created_at = str(created_at)
    updated_at = src.get("updated_at")
    if updated_at is not None and not isinstance(updated_at, str):
        try:
            from datetime import datetime, timezone

            if isinstance(updated_at, datetime):
                iso2 = updated_at.astimezone(timezone.utc).isoformat()
                updated_at = iso2.replace("+00:00", "Z")
            else:
                updated_at = str(updated_at)
        except Exception:
            updated_at = str(updated_at)
    status = src.get("status") or "ready"

    # Build score_detail object consistently for contract consumers
    score_detail = {"raw": score_raw, "scaled": score_scaled}

    # Fallback: if created_at missing and a compute timestamp is present, use it
    if (created_at is None) and (src.get("computed_at") is not None):
        try:
            from datetime import datetime, timezone

            ca = src.get("computed_at")
            if isinstance(ca, datetime):
                created_at = (
                    ca.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
                )
            else:
                # best-effort string
                created_at = str(ca)
        except Exception:
            pass

    resp = {
        "exam_session_id": sid,
        "user_id": uid,
        "exam_id": eid,
        "score": score_scaled,
        "score_detail": score_detail,
        "ability_estimate": ability,
        "standard_error": se,
        "percentile": pct,
        "topic_breakdown": topic_breakdown,
        "questions": questions,
        "recommendations": recs,
        "created_at": created_at,
        "updated_at": updated_at,
        "status": status,
    }

    # Optionally drop volatile fields to stabilize contract snapshots
    try:
        from datetime import datetime, timezone

        from ..settings import Settings

        # Determine exclusion according to per-request override or global flag
        exclude_ts = (
            bool(stable)
            if stable is not None
            else bool(Settings().RESULT_EXCLUDE_TIMESTAMPS)
        )
        if exclude_ts:
            # Remove both timestamps if present
            resp.pop("created_at", None)
            resp.pop("updated_at", None)
        else:
            # When explicitly stable=false, force-include created_at by providing a value if missing.
            # Prefer the compute timestamp if available; fallback to 'now' as last resort.
            if "created_at" not in resp or resp["created_at"] is None:
                ca = src.get("computed_at")
                if ca is not None and isinstance(ca, datetime):
                    resp["created_at"] = (
                        ca.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
                    )
                else:
                    now_iso = (
                        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    )
                    resp["created_at"] = now_iso
    except Exception:
        # Non-fatal if settings import fails unexpectedly
        pass

    return resp


# TODO(feature): Wire a feature flag (e.g., Settings().FEATURE_RESULT_PDF) to gate this
# endpoint and flip to implementation when the renderer is ready. Keep returning 501 until then.
@router.get(
    "/exams/{session_id}/result/pdf",
    summary="Result PDF (stub)",
    description=(
        "PDF generation is not implemented yet. This endpoint currently returns 501.\n"
        "Future behavior: render a PDF report (graphs, breakdowns) and stream the file or return a download link."
    ),
)
async def get_result_pdf(
    session_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_session_access),
) -> None:
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/results", summary="List results with filters + keyset pagination")
async def list_results(
    user_id: str | None = Query(default=None),
    org_id: int | None = Query(
        default=None, description="Override org filter (teacher/admin only)"
    ),
    exam_id: int | None = Query(default=None),
    status: list[str] | None = Query(
        default=None, description="Filter by status (multi)"
    ),
    status_csv: str | None = Query(
        default=None, description="Comma-separated statuses"
    ),
    last_n_days: int | None = Query(
        default=None,
        ge=1,
        description="Convenience: set updated_from to now - N days (ignored if updated_from provided)",
    ),
    last_n_hours: int | None = Query(
        default=None,
        ge=1,
        description="Convenience: set updated_from to now - N hours (ignored if updated_from provided)",
    ),
    last_n_weeks: int | None = Query(
        default=None,
        ge=1,
        description="Convenience: set updated_from to now - N weeks (ignored if updated_from provided)",
    ),
    min_score_scaled: float | None = Query(
        default=None, description="Minimum scaled score (inclusive)"
    ),
    max_score_scaled: float | None = Query(
        default=None, description="Maximum scaled score (inclusive)"
    ),
    min_score_raw: float | None = Query(
        default=None, description="Minimum raw score (inclusive)"
    ),
    max_score_raw: float | None = Query(
        default=None, description="Maximum raw score (inclusive)"
    ),
    score_scaled_eq: float | None = Query(
        default=None, description="Exact match for scaled score (overrides min/max)"
    ),
    score_raw_eq: float | None = Query(
        default=None, description="Exact match for raw score (overrides min/max)"
    ),
    sort_by: str = Query(default="updated_at", pattern="^(updated_at|created_at)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=200),
    cursor_ts: str | None = Query(
        default=None,
        description="ISO timestamp of last item for keyset (matches sort_by)",
    ),
    cursor_id: str | None = Query(
        default=None, description="ID (UUID) of last item from previous page"
    ),
    cursor: str | None = Query(
        default=None,
        description=(
            "Opaque cursor token (v1) produced by next_cursor_opaque. Takes precedence over cursor_ts/cursor_id."
        ),
    ),
    created_from: str | None = Query(
        default=None, description="ISO lower bound for created_at"
    ),
    created_to: str | None = Query(
        default=None, description="ISO upper bound for created_at"
    ),
    updated_from: str | None = Query(
        default=None, description="ISO lower bound for updated_at"
    ),
    updated_to: str | None = Query(
        default=None, description="ISO upper bound for updated_at"
    ),
    created_last_n_hours: int | None = Query(
        default=None,
        ge=1,
        description="Convenience: set created_from to now - N hours (ignored if created_from provided)",
    ),
    created_last_n_days: int | None = Query(
        default=None,
        ge=1,
        description="Convenience: set created_from to now - N days (ignored if created_from provided)",
    ),
    created_last_n_weeks: int | None = Query(
        default=None,
        ge=1,
        description="Convenience: set created_from to now - N weeks (ignored if created_from provided)",
    ),
    stable: bool | None = Query(
        default=None,
        description=(
            "When true, omit volatile fields (timestamps) from items. When false, force include. "
            "When omitted, uses RESULT_EXCLUDE_TIMESTAMPS setting. next_cursor is unaffected."
        ),
    ),
    current_user: User = Depends(get_current_user),
) -> Any:
    # TODO(next): Consider a compare endpoint (e.g., /results/compare) that accepts
    # multiple session_ids and returns a consolidated comparison payload.
    # This list endpoint remains focused on filtering and keyset pagination.
    from datetime import datetime, timedelta, timezone

    cur = None
    if cursor:
        dec = _decode_cursor(cursor)
        if dec is None:
            raise HTTPException(400, "invalid_cursor")
        try:
            ts = datetime.fromisoformat(dec[0].replace("Z", "+00:00"))
            cur = (ts, dec[1])
        except Exception:
            raise HTTPException(400, "invalid_cursor")
    elif cursor_ts and cursor_id:
        try:
            ts = datetime.fromisoformat(cursor_ts.replace("Z", "+00:00"))
            cur = (ts, cursor_id)
        except Exception:
            raise HTTPException(400, "invalid_cursor")
    # Parse CSV statuses and merge with list[], keep working list and derive optional at the end
    status_list_work: list[str] = list(status or [])
    if status_csv:
        status_list_work.extend([s.strip() for s in status_csv.split(",") if s.strip()])
    status_list_unique: list[str] = list(dict.fromkeys(status_list_work))
    status_list_opt: list[str] | None = (
        status_list_unique if status_list_unique else None
    )

    # Parse date ranges
    cfrom = cto = ufrom = uto = None
    try:
        if created_from:
            cfrom = datetime.fromisoformat(created_from.replace("Z", "+00:00"))
        if created_to:
            cto = datetime.fromisoformat(created_to.replace("Z", "+00:00"))
        if updated_from:
            ufrom = datetime.fromisoformat(updated_from.replace("Z", "+00:00"))
        if updated_to:
            uto = datetime.fromisoformat(updated_to.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(400, "invalid_date_range")

    # Convenience: compute updated_from if not explicitly provided.
    # Priority if multiple provided: hours > days > weeks (most specific first).
    if ufrom is None:
        if last_n_hours is not None:
            try:
                ufrom = datetime.now(timezone.utc) - timedelta(hours=int(last_n_hours))
            except Exception:
                raise HTTPException(400, "invalid_last_n_hours")
        elif last_n_days is not None:
            try:
                ufrom = datetime.now(timezone.utc) - timedelta(days=int(last_n_days))
            except Exception:
                raise HTTPException(400, "invalid_last_n_days")
        elif last_n_weeks is not None:
            try:
                ufrom = datetime.now(timezone.utc) - timedelta(weeks=int(last_n_weeks))
            except Exception:
                raise HTTPException(400, "invalid_last_n_weeks")

    # Convenience: compute created_from if not explicitly provided.
    if cfrom is None:
        if created_last_n_hours is not None:
            try:
                cfrom = datetime.now(timezone.utc) - timedelta(
                    hours=int(created_last_n_hours)
                )
            except Exception:
                raise HTTPException(400, "invalid_created_last_n_hours")
        elif created_last_n_days is not None:
            try:
                cfrom = datetime.now(timezone.utc) - timedelta(
                    days=int(created_last_n_days)
                )
            except Exception:
                raise HTTPException(400, "invalid_created_last_n_days")
        elif created_last_n_weeks is not None:
            try:
                cfrom = datetime.now(timezone.utc) - timedelta(
                    weeks=int(created_last_n_weeks)
                )
            except Exception:
                raise HTTPException(400, "invalid_created_last_n_weeks")
    # Authorization: auto-limit student to their own records (unless LOCAL_DEV)
    import os

    from ..settings import Settings

    effective_user_id = user_id
    effective_org_id = None
    # Use fresh Settings instance so env changes during tests are picked up
    _s = Settings()
    is_local_dev = _s.LOCAL_DEV or (os.getenv("LOCAL_DEV", "false").lower() == "true")
    if not is_local_dev:
        if current_user:
            if current_user.is_student():
                # Students cannot scope by org; auto-limit to their own user_id
                if org_id is not None:
                    raise HTTPException(403, "forbidden_org")
                effective_user_id = current_user.user_id
            elif current_user.is_teacher():
                # Teachers default to their own org; overriding to other orgs is forbidden
                if org_id is None:
                    if current_user.org_id is None:
                        raise HTTPException(403, "forbidden_org")
                    effective_org_id = int(current_user.org_id)
                else:
                    if current_user.org_id is None or int(org_id) != int(
                        current_user.org_id
                    ):
                        raise HTTPException(403, "forbidden_org_override")
                    effective_org_id = int(current_user.org_id)
            else:
                # Admins: honor org_id if provided, else unrestricted
                effective_org_id = org_id if org_id is not None else None

    result = list_results_keyset(
        user_id=effective_user_id,
        org_id=effective_org_id,
        exam_id=exam_id,
        status_in=status_list_opt,
        created_from=cfrom,
        created_to=cto,
        updated_from=ufrom,
        updated_to=uto,
        min_score_scaled=(min_score_scaled if score_scaled_eq is None else None),
        max_score_scaled=(max_score_scaled if score_scaled_eq is None else None),
        min_score_raw=min_score_raw,
        max_score_raw=(max_score_raw if score_raw_eq is None else None),
        score_scaled_eq=score_scaled_eq,
        score_raw_eq=score_raw_eq,
        sort_by=sort_by,
        order=order,
        limit=limit,
        cursor=cur,
    )
    # Attach opaque cursor (alongside legacy next_cursor for compatibility)
    try:
        nxt = result.get("next_cursor")
        if nxt:
            # Prefer exact key according to sort_by; fallback to updated_at/created_at
            ts_val = nxt.get(sort_by) or nxt.get("updated_at") or nxt.get("created_at")
            if isinstance(ts_val, datetime):
                ts_iso = (
                    ts_val.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
                )
            else:
                ts_iso = str(ts_val)
            token = _encode_cursor_v1(ts_iso, str(nxt.get("id")), sort_by)
            result["next_cursor_opaque"] = token
    except Exception:
        # Non-fatal: omit opaque cursor if any error occurs
        pass
    # Apply stable flag to items: drop or include timestamps per-request or global setting
    try:
        from datetime import datetime, timezone

        from ..settings import Settings

        exclude_ts = (
            bool(stable)
            if stable is not None
            else bool(Settings().RESULT_EXCLUDE_TIMESTAMPS)
        )
        items = list(result.get("items") or [])
        if exclude_ts:
            for it in items:
                it.pop("created_at", None)
                it.pop("updated_at", None)
        else:
            # Force include created_at if missing; prefer updated_at as a fallback, else 'now'
            for it in items:
                if "created_at" not in it or it["created_at"] is None:
                    ca = it.get("updated_at")
                    if ca is not None:
                        it["created_at"] = ca
                    else:
                        it["created_at"] = (
                            datetime.now(timezone.utc)
                            .isoformat()
                            .replace("+00:00", "Z")
                        )
        result["items"] = items
    except Exception:
        pass
    return result
