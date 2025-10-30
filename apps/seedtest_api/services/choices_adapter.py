from __future__ import annotations

"""
choices_adapter: helpers to map between question_choices table and (options, answer) fields

Usage patterns (SQLAlchemy 2.0 style):

from sqlalchemy import text
from ..services.db import get_session
from .choices_adapter import read_options_answer, write_choices_from_options

with get_session() as s:
    # Read
    oa = read_options_answer(s, question_id)
    if oa is not None:
        options, answer = oa

    # Write (replace all choices for question)
    write_choices_from_options(s, question_id, ["A","B","C","D"], answer=2)
    s.flush()

These helpers don't alter the questions table. They operate only on question_choices.
They are optional and safe to call even when no choices exist yet.
"""

from typing import Any, Iterable, Optional, Tuple, Dict, List
from sqlalchemy import text, bindparam
from sqlalchemy.engine import Connection


def read_options_answer(conn: Connection, question_id: str) -> Optional[Tuple[list[str], int]]:
    """
    Load options/answer from question_choices if any exist for the question.
    Returns (options, answer_index). If no choices found, returns None.
    If there is no correct choice, answer_index will be -1.
    """
    rows = conn.execute(
        text(
            """
            SELECT sort_order, content, is_correct
            FROM question_choices
            WHERE question_id = :qid
            ORDER BY sort_order ASC
            """
        ),
        {"qid": question_id},
    ).fetchall()
    if not rows:
        return None

    options: list[str] = []
    ans_idx: int = -1
    for idx, (sort_order, content, is_correct) in enumerate(rows):
        options.append(str(content))
        if is_correct and ans_idx == -1:
            ans_idx = int(sort_order)
    # Normalize answer index to within range if sort_order stored as 0..n-1
    # If sort_order differs from enumerate index, we still return sort_order as API answer index.
    if ans_idx < 0:
        # No correct marked; caller can decide policy
        ans_idx = -1
    return options, ans_idx


def write_choices_from_options(
    conn: Connection, question_id: str, options: Iterable[str], answer: int
) -> int:
    """
    Replace all choices for the given question_id based on (options, answer).

    - Deletes existing choices
    - Inserts new rows with sort_order starting at 0
    - Sets is_correct=true for the row matching the answer index

    Returns the number of inserted rows.
    """
    opts = list(options)
    if not opts:
        # Remove all choices when no options provided
        conn.execute(text("DELETE FROM question_choices WHERE question_id = :qid"), {"qid": question_id})
        return 0

    if answer < 0 or answer >= len(opts):
        raise ValueError("answer index out of range for provided options")

    # Delete existing
    conn.execute(text("DELETE FROM question_choices WHERE question_id = :qid"), {"qid": question_id})

    # Bulk insert
    inserted = 0
    for i, content in enumerate(opts):
        content_str = str(content).strip()
        if not content_str:
            raise ValueError("choice content must be non-empty")
        conn.execute(
            text(
                """
                INSERT INTO question_choices (question_id, sort_order, content, is_correct)
                VALUES (:qid, :ord, :content, :is_correct)
                """
            ),
            {"qid": question_id, "ord": int(i), "content": content_str, "is_correct": (i == int(answer))},
        )
        inserted += 1
    return inserted


def read_options_answer_batch(conn: Connection, question_ids: Iterable[str]) -> Dict[str, Tuple[List[str], int]]:
    """
    Batch-load options/answer for multiple question_ids without N+1.

    Returns a mapping: question_id -> (options, answer_idx)
    If no correct choice exists for a question, answer_idx will be -1.
    Unknown question_ids (no rows) will be omitted from the result.
    """
    qids = list(dict.fromkeys(str(q) for q in question_ids))
    if not qids:
        return {}

    stmt = text(
        """
        SELECT question_id, sort_order, content, is_correct
        FROM question_choices
        WHERE question_id IN :qids
        ORDER BY question_id, sort_order
        """
    ).bindparams(bindparam("qids", expanding=True))

    rows = conn.execute(stmt, {"qids": qids}).fetchall()
    out: Dict[str, Tuple[List[str], int]] = {}
    for question_id, sort_order, content, is_correct in rows:
        bucket = out.get(question_id)
        if bucket is None:
            bucket = ([], -1)
            out[question_id] = bucket
        options_list, ans_idx = bucket
        # Ensure options_list extends up to sort_order
        # But since sort_order is expected 0..n-1 contiguous, we simply append in order
        options_list.append(str(content))
        if is_correct and ans_idx == -1:
            out[question_id] = (options_list, int(sort_order))
        else:
            out[question_id] = (options_list, ans_idx)
    return out
