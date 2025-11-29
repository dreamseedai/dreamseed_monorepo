from __future__ import annotations

from typing import Optional

from adaptive_engine.config import get_settings


def _get_psycopg2():
    try:
        import psycopg2  # type: ignore

        return psycopg2
    except Exception:
        return None


def get_initial_theta(user_id: int, exam_id: int) -> float:
    """Derive initial theta for a new session.

    Strategy:
      - If database configured, try reading last known theta for the user (optionally per exam).
      - Fallback to 0.0 if not found or DB disabled.
    """
    s = get_settings()
    if not s.database_url:
        return 0.0
    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        return 0.0
    try:
        conn = psycopg2.connect(s.database_url)
        cur = conn.cursor()
        # Example schema: user_ability(user_id, exam_id, theta)
        # If you only store per-user (not per-exam), ignore exam_id filter.
        try:
            cur.execute(
                "SELECT theta FROM user_ability WHERE user_id=%s AND exam_id=%s ORDER BY updated_at DESC LIMIT 1",
                (user_id, exam_id),
            )
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()
        if row and row[0] is not None:
            return float(row[0])
    except Exception:
        pass
    return 0.0
