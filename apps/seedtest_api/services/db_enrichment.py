from __future__ import annotations

from typing import Any, Dict, Iterable

from sqlalchemy import create_engine, text

from ..settings import settings


def _get_engine():
    if not settings.DATABASE_URL:
        return None
    try:
        return create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    except Exception:
        return None


def fetch_solutions(question_ids: Iterable[str | int]) -> Dict[str | int, Dict[str, Any]]:
    """Fetch solution_html (and optional topic) for the given question ids.

    Assumptions:
    - Table name: 'questions' (override later if settings adds a table name)
    - Columns: question_id (PK), solution_html (TEXT nullable), topic (TEXT nullable)
    """
    ids = [qid for qid in question_ids if qid is not None]
    if not ids:
        return {}
    eng = _get_engine()
    if not eng:
        return {}
    sql = text(
        """
        SELECT question_id, solution_html, topic
        FROM questions
        WHERE question_id = ANY(:qids)
        """
    )
    out: Dict[str | int, Dict[str, Any]] = {}
    try:
        with eng.connect() as conn:
            rows = conn.execute(sql, {"qids": ids}).all()
            for row in rows:
                qid = row[0]
                out[qid] = {"solution_html": row[1], "topic": row[2]}
    except Exception:
        return {}
    return out


def enrich_items_review(items: list[dict]) -> list[dict]:
    """Attach solution_html to each item if present in DB."""
    if not items:
        return items
    qids = [x for x in ((it.get("item_id") or it.get("question_id")) for it in items if it) if x is not None]
    sol = fetch_solutions(qids)
    for it in items:
        qid = it.get("item_id") or it.get("question_id")
        if qid in sol:
            it["solution_html"] = sol[qid].get("solution_html")
            # If topic not set, fill from DB for potential future use
            it.setdefault("topic", sol[qid].get("topic"))
    return items
