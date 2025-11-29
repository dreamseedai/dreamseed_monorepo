from __future__ import annotations

from typing import Optional

from adaptive_engine.config import get_settings


def _get_psycopg2():
    try:
        import psycopg2  # type: ignore
        return psycopg2
    except Exception:
        return None


def log_exposure(session_id: str, user_id: int, exam_id: int, question_id: str | int) -> None:
    s = get_settings()
    if not s.database_url:
        return
    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        return
    try:
        conn = psycopg2.connect(s.database_url)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO item_exposure(session_id, user_id, exam_id, question_id)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, user_id, exam_id, str(question_id)),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()
    except Exception:
        # swallow logging errors
        return


def log_response(session_id: str, user_id: int, exam_id: int, question_id: str | int, is_correct: bool, ability_after: float | None = None) -> None:
    s = get_settings()
    if not s.database_url:
        return
    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        return
    try:
        conn = psycopg2.connect(s.database_url)
        cur = conn.cursor()
        try:
            if ability_after is None:
                cur.execute(
                    """
                    INSERT INTO item_response(session_id, user_id, exam_id, question_id, is_correct)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (session_id, user_id, exam_id, str(question_id), bool(is_correct)),
                )
            else:
                # Optional column 'ability_after' if available
                try:
                    cur.execute(
                        """
                        INSERT INTO item_response(session_id, user_id, exam_id, question_id, is_correct, ability_after)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (session_id, user_id, exam_id, str(question_id), bool(is_correct), float(ability_after)),
                    )
                except Exception:
                    # Fallback to schema without ability_after
                    cur.execute(
                        """
                        INSERT INTO item_response(session_id, user_id, exam_id, question_id, is_correct)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (session_id, user_id, exam_id, str(question_id), bool(is_correct)),
                    )
            conn.commit()
        finally:
            cur.close()
            conn.close()
    except Exception:
        return


def get_overexposed_question_ids(threshold: int, window_hours: int) -> set[str]:
    """Return a set of question_ids that have at least `threshold` exposures in the last `window_hours` hours.

    Safe no-op if DB is not configured/available. Question IDs are returned as strings.
    """
    s = get_settings()
    if not s.database_url or threshold <= 0:
        return set()
    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        return set()
    try:
        conn = psycopg2.connect(s.database_url)
        cur = conn.cursor()
        try:
            # Assume item_exposure has columns: question_id (text/varchar), occurred_at (timestamp)
            cur.execute(
                f"""
                SELECT question_id
                FROM {s.item_exposure_table}
                WHERE occurred_at >= NOW() - INTERVAL %s
                GROUP BY question_id
                HAVING COUNT(*) >= %s
                """,
                (f"{int(window_hours)} hours", int(threshold)),
            )
            rows = cur.fetchall()
            return {str(r[0]) for r in rows}
        finally:
            cur.close()
            conn.close()
    except Exception:
        return set()
