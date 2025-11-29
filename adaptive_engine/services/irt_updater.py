from __future__ import annotations

from typing import Iterable, Dict, Any, Callable, Optional, Iterator
from adaptive_engine.config import get_settings
import math
import uuid
from datetime import datetime, timezone


def update_item_difficulty(current_b: float, correct_rate: float, target_rate: float = 0.5, learning_rate: float = 0.1) -> float:
    """Heuristic adjustment of item difficulty 'b' based on observed correct rate.

    If actual correct rate is lower than target, increase b (harder).
    """
    delta = target_rate - correct_rate
    new_b = current_b - learning_rate * delta
    return round(float(new_b), 3)


def _moment_b_from_correct_rate(a: float, b: float, c: float, correct_rate: float) -> float:
    """Approximate b by inverting 3PL ICC at θ≈0 using observed correct rate.

    Solve p = c + (1-c)/(1+exp(-a(θ-b))) at θ=0 → b ≈ -(1/a) * log( (1-c)/(p-c) - 1 ).
    Clamp to reasonable range.
    """
    p = float(correct_rate)
    a = float(a or 1.0)
    c = float(c)
    p = min(max(p, c + 1e-5), 1.0 - 1e-5)
    try:
        denom = (p - c)
        t = (1.0 - c) / denom - 1.0
        x = math.log(max(t, 1e-9))
        b_new = - x / max(a, 1e-6)
    except Exception:
        b_new = b
    return float(max(min(b_new, 4.0), -4.0))


_CURRENT_RUN_ID: Optional[str] = None


def _new_run_id() -> str:
    return f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def run_irt_update_once(fetch_stats: Optional[Callable[[], Iterator[Dict[str, Any]]]] = None,
                        persist_update: Optional[Callable[[str | int, float, float, float], None]] = None) -> int:
    """Run a single IRT parameter update cycle.

    - fetch_stats: should return an iterable of dicts with keys: question_id, a, b, c, correct_rate
    - persist_update: called per item with (question_id, new_a, new_b, new_c)

    Returns number of items updated.
    """
    updated = 0
    if fetch_stats is None:
        return 0
    s = get_settings()
    items = list(fetch_stats())
    # Set a run id for change-log correlation (best-effort)
    global _CURRENT_RUN_ID
    _CURRENT_RUN_ID = _new_run_id()
    method = (getattr(s, "irt_update_method", "heuristic") or "heuristic").lower()
    target = float(getattr(s, "irt_target_correct_rate", 0.5))
    lr = float(getattr(s, "irt_learning_rate", 0.1))
    max_updates = getattr(s, "irt_update_max_items_per_run", None)
    for it in items:
        try:
            qid = it["question_id"]
            a = float(it.get("a", 1.0))
            b = float(it.get("b", 0.0))
            c = float(it.get("c", 0.2))
            cr = float(it.get("correct_rate", 0.5))
            if method == "heuristic":
                new_b = update_item_difficulty(b, cr, target_rate=target, learning_rate=lr)
            else:
                # moment-based approx for mml/bayes placeholders
                new_b = _moment_b_from_correct_rate(a, b, c, cr)
            if persist_update is not None:
                persist_update(qid, a, new_b, c)
            updated += 1
            if isinstance(max_updates, int) and max_updates > 0 and updated >= max_updates:
                break
        except Exception:
            # Skip bad records
            continue
    return updated


def _get_psycopg2():
    try:
        import psycopg2  # type: ignore
        return psycopg2
    except Exception:
        return None


def fetch_stats_from_db() -> Iterator[Dict[str, Any]]:
    s = get_settings()
    if not s.database_url:
        return iter(())
    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        return iter(())
    def _iter():
        conn = None
        cur = None
        try:
            conn = psycopg2.connect(s.database_url)
            cur = conn.cursor()
            cur.execute(f"SELECT question_id, a, b, c, correct_rate FROM {s.irt_stats_view}")
            for row in cur.fetchall():
                yield {
                    "question_id": row[0],
                    "a": row[1],
                    "b": row[2],
                    "c": row[3],
                    "correct_rate": row[4],
                }
        except Exception:
            return
        finally:
            try:
                if cur:
                    cur.close()
            finally:
                if conn:
                    conn.close()
    return _iter()


def persist_update_to_db(question_id: str | int, a: float, b: float, c: float) -> None:
    s = get_settings()
    if not s.database_url:
        return
    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        return
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(s.database_url)
        cur = conn.cursor()
        # Capture old params (if exist) for change-log
        old_a = None
        old_b = None
        old_c = None
        try:
            cur.execute(f"SELECT a, b, c FROM {s.items_table} WHERE question_id = %s", (question_id,))
            row = cur.fetchone()
            if row:
                old_a, old_b, old_c = float(row[0]), float(row[1]), float(row[2])
        except Exception:
            pass
        # Upsert pattern; assumes unique key on question_id
        cur.execute(
            f"""
            INSERT INTO {s.items_table} (question_id, a, b, c)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (question_id) DO UPDATE SET a = EXCLUDED.a, b = EXCLUDED.b, c = EXCLUDED.c
            """,
            (question_id, a, b, c),
        )
        # Optional change-log
        if getattr(s, "irt_change_log_table", None):
            # Try to pull evidence from stats view (n_responses, log_likelihood) if available
            n_responses: Optional[int] = None
            log_likelihood: Optional[float] = None
            try:
                cur.execute(
                    f"SELECT correct_rate FROM {s.irt_stats_view} WHERE question_id = %s",
                    (question_id,),
                )
                _ = cur.fetchone()
                # Best effort: if view has n_responses/log_likelihood, grab them
                try:
                    cur.execute(
                        f"SELECT n_responses, log_likelihood FROM {s.irt_stats_view} WHERE question_id = %s",
                        (question_id,),
                    )
                    row2 = cur.fetchone()
                    if row2:
                        n_responses = int(row2[0]) if row2[0] is not None else None
                        log_likelihood = float(row2[1]) if row2[1] is not None else None
                except Exception:
                    pass
            except Exception:
                pass
            run_id = _CURRENT_RUN_ID or _new_run_id()
            ts = datetime.now(timezone.utc)
            try:
                cur.execute(
                    f"""
                    INSERT INTO {s.irt_change_log_table} (
                        run_id, changed_at, question_id,
                        old_a, old_b, old_c, new_a, new_b, new_c,
                        n_responses, log_likelihood
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id, ts, question_id,
                        old_a, old_b, old_c, a, b, c,
                        n_responses, log_likelihood,
                    ),
                )
            except Exception:
                # Don't fail the update if change-log fails
                pass
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
    finally:
        try:
            if cur:
                cur.close()
        finally:
            if conn:
                conn.close()

