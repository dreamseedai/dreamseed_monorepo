from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from .db import get_session


def list_results_by_user_exam(
    *,
    user_id: Optional[str] = None,
    exam_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List results filtered by user_id and/or exam_id.

    Requires DATABASE_URL to be configured; returns empty list if no rows.
    """
    where = []
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if user_id:
        where.append("user_id = :uid")
        params["uid"] = user_id
    if exam_id is not None:
        where.append("exam_id = :eid")
        params["eid"] = exam_id
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
    SELECT id, session_id, user_id, exam_id, status, score_raw, score_scaled, created_at, updated_at
    FROM exam_results
    {clause}
    ORDER BY updated_at DESC, id DESC
    LIMIT :limit OFFSET :offset
    """
    with get_session() as s:
        rows = s.execute(text(sql), params).mappings().all()
        return [dict(r) for r in rows]


def list_results_keyset(
    *,
    user_id: Optional[str] = None,
    org_id: Optional[int] = None,
    exam_id: Optional[int] = None,
    status_in: Optional[List[str]] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    updated_from: Optional[datetime] = None,
    updated_to: Optional[datetime] = None,
    min_score_scaled: Optional[float] = None,
    max_score_scaled: Optional[float] = None,
    min_score_raw: Optional[float] = None,
    max_score_raw: Optional[float] = None,
    score_scaled_eq: Optional[float] = None,
    score_raw_eq: Optional[float] = None,
    sort_by: str = "updated_at",
    order: str = "desc",
    limit: int = 50,
    cursor: Optional[Tuple[datetime, str]] = None,
) -> Dict[str, Any]:
    """Keyset pagination with filters.

    - sort_by: 'updated_at' | 'created_at'
    - order: 'desc' | 'asc'
    - cursor: tuple(timestamp, id) for keyset
    Returns { items: [...], next_cursor: {<sort_by>, id} | None }
    """
    field = "updated_at" if sort_by not in ("updated_at", "created_at") else sort_by
    ord_dir = "DESC" if order.lower() != "asc" else "ASC"
    cmp_op = "<" if ord_dir == "DESC" else ">"

    where = []
    params: Dict[str, Any] = {"limit": limit + 1}
    if user_id:
        where.append("user_id = :uid")
        params["uid"] = user_id
    if org_id is not None:
        where.append("org_id = :org_id")
        params["org_id"] = int(org_id)
    if exam_id is not None:
        where.append("exam_id = :eid")
        params["eid"] = exam_id
    if status_in:
        where.append("status = ANY(:status)")
        params["status"] = status_in
    # Independent date ranges on created_at / updated_at
    if created_from:
        where.append("created_at >= :created_from")
        params["created_from"] = created_from
    if created_to:
        where.append("created_at <= :created_to")
        params["created_to"] = created_to
    if updated_from:
        where.append("updated_at >= :updated_from")
        params["updated_from"] = updated_from
    if updated_to:
        where.append("updated_at <= :updated_to")
        params["updated_to"] = updated_to
    # Score filters (equality overrides min/max for the same field)
    if score_scaled_eq is not None:
        where.append("score_scaled = :score_scaled_eq")
        params["score_scaled_eq"] = score_scaled_eq
    else:
        if min_score_scaled is not None:
            where.append("score_scaled >= :min_score_scaled")
            params["min_score_scaled"] = min_score_scaled
        if max_score_scaled is not None:
            where.append("score_scaled <= :max_score_scaled")
            params["max_score_scaled"] = max_score_scaled
    if score_raw_eq is not None:
        where.append("score_raw = :score_raw_eq")
        params["score_raw_eq"] = score_raw_eq
    else:
        if min_score_raw is not None:
            where.append("score_raw >= :min_score_raw")
            params["min_score_raw"] = min_score_raw
        if max_score_raw is not None:
            where.append("score_raw <= :max_score_raw")
            params["max_score_raw"] = max_score_raw
    if cursor is not None:
        where.append(f"({field}, id) {cmp_op} (:cur_ts, :cur_id)")
        params["cur_ts"], params["cur_id"] = cursor
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
    SELECT id, session_id, user_id, exam_id, status, score_raw, score_scaled, created_at, updated_at
    FROM exam_results
    {clause}
    ORDER BY {field} {ord_dir}, id {ord_dir}
    LIMIT :limit
    """
    with get_session() as s:
        rows = s.execute(text(sql), params).mappings().all()
        items = [dict(r) for r in rows[:limit]]
        # Normalize Decimal to float for JSON compatibility
        for it in items:
            for k in ("score_raw", "score_scaled"):
                v = it.get(k)
                if isinstance(v, Decimal):
                    it[k] = float(v)
        next_cur = None
        if len(rows) > limit:
            last = rows[limit - 1]
            next_cur = {field: last[field], "id": str(last["id"])}
        return {"items": items, "next_cursor": next_cur}
