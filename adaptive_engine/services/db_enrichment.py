from __future__ import annotations

from typing import Dict, Any, Iterable
from adaptive_engine.config import get_settings
from collections import defaultdict


def _get_psycopg2():
    try:
        import psycopg2  # type: ignore
        return psycopg2
    except Exception:
        return None


def fetch_solutions(question_ids: Iterable[str | int]) -> Dict[str | int, Dict[str, Any]]:
    s = get_settings()
    if not s.database_url or not s.questions_table:
        return {}
    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        return {}
    ids = list(question_ids)
    if not ids:
        return {}
    qmarks = ",".join(["%s"] * len(ids))
    out: Dict[str | int, Dict[str, Any]] = {}
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(s.database_url)
        cur = conn.cursor()
        cur.execute(
            f"SELECT question_id, solution_html, topic FROM {s.questions_table} WHERE question_id IN ({qmarks})",
            tuple(ids),
        )
        for row in cur.fetchall():
            out[row[0]] = {"solution_html": row[1], "topic": row[2]}
    except Exception:
        return {}
    finally:
        try:
            if cur:
                cur.close()
        finally:
            if conn:
                conn.close()
    return out


def topic_averages() -> Dict[str, float]:
    s = get_settings()
    if not s.database_url or not s.responses_table or not s.questions_table:
        return {}
    psycopg2 = _get_psycopg2()
    if psycopg2 is None:
        return {}
    conn = None
    cur = None
    out: Dict[str, float] = {}
    try:
        conn = psycopg2.connect(s.database_url)
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT q.topic, AVG(CASE WHEN r.is_correct THEN 1.0 ELSE 0.0 END) AS topic_correct_rate
            FROM {s.responses_table} r
            JOIN {s.questions_table} q USING (question_id)
            GROUP BY q.topic
            """
        )
        for row in cur.fetchall():
            if row[0] is not None:
                out[str(row[0])] = float(row[1] or 0.0)
    except Exception:
        return {}
    finally:
        try:
            if cur:
                cur.close()
        finally:
            if conn:
                conn.close()
    return out


def enrich_finish_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Augment finish payload with solution_html per item and topic-average benchmarks when configured.
    Expects payload to contain an 'items_review' list with entries that have 'question_id' and 'topic' keys.
    """
    items = payload.get("items_review") or []
    qids = [it.get("question_id") for it in items if it and "question_id" in it]
    sol = fetch_solutions(qids)
    for it in items:
        qid = it.get("question_id")
        if qid in sol:
            it["solution_html"] = sol[qid].get("solution_html")
            it.setdefault("topic", sol[qid].get("topic"))
    # Topic benchmarks
    tavg = topic_averages()
    if tavg:
        payload["topic_benchmarks"] = tavg
    return payload
