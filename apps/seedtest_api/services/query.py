from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..settings import settings
from .db import get_session

_TAGS_KIND_CACHE: Tuple[float, Literal["text[]", "jsonb"]] | None = None


def detect_tags_column_kind(session: Session) -> Literal["text[]", "jsonb"]:
    """Detect the type of questions.tags column as 'text[]' or 'jsonb'.

    Caches the result for TAGS_KIND_TTL_SEC seconds unless TTL is 0.
    """
    global _TAGS_KIND_CACHE
    ttl = settings.TAGS_KIND_TTL_SEC or 300
    now = time.time()
    if ttl > 0 and _TAGS_KIND_CACHE is not None:
        ts, kind = _TAGS_KIND_CACHE
        if now - ts < ttl:
            return kind

    # Postgres system catalog query to read data_type info.
    # Fallback: inspect a sample row.
    sql = text(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'questions' AND column_name = 'tags'
        LIMIT 1
        """
    )
    row = session.execute(sql).fetchone()
    kind: Literal["text[]", "jsonb"] | None = None
    if row and row[0]:
        dt = (row[0] or "").lower()
        if "json" in dt:
            kind = "jsonb"
        elif "array" in dt or "text" in dt:
            kind = "text[]"

    if kind is None:
        # Heuristic probe omitted; default to jsonb if unknown (safer for modern schemas)
        kind = "jsonb"

    _TAGS_KIND_CACHE = (now, kind)
    return kind


def build_questions_query(filters: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    """Build a SELECT SQL string for questions based on filters.

    Applies tags filter using text[] '&&' or jsonb '?|' according to detection.
    """
    conditions: List[str] = ["1=1"]
    params: Dict[str, Any] = {}

    if filters.get("org_id") is not None:
        conditions.append("org_id = :org_id")
        params["org_id"] = filters["org_id"]

    if filters.get("subject"):
        conditions.append("subject = :subject")
        params["subject"] = filters["subject"]

    if filters.get("diff_min") is not None:
        conditions.append("difficulty >= :diff_min")
        params["diff_min"] = filters["diff_min"]

    if filters.get("diff_max") is not None:
        conditions.append("difficulty <= :diff_max")
        params["diff_max"] = filters["diff_max"]

    topics: List[int] = filters.get("topics") or []
    if topics:
        conditions.append("topic_id = ANY(:topics)")
        params["topics"] = topics

    tags: List[str] = filters.get("tags") or []
    if tags:
        # We can't detect kind without a session; leave a placeholder. The execute helper will finalize.
        conditions.append("{TAGS_PREDICATE}")
        params["tags"] = tags

    where_sql = " AND ".join(conditions)
    base_sql = f"SELECT question_id, content, difficulty, topic_id, tags FROM questions WHERE {where_sql}"
    return base_sql, params


def execute_questions_query(filters: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
    """Execute the built query with proper tags predicate expansion based on detected kind.
    Returns a list of rows as dicts.
    """
    sql_tmpl, params = build_questions_query(filters)
    with get_session() as session:
        kind = detect_tags_column_kind(session)
        if "{TAGS_PREDICATE}" in sql_tmpl and params.get("tags"):
            if kind == "text[]":
                # text[] && :tags::text[]
                sql = sql_tmpl.replace("{TAGS_PREDICATE}", "tags && :tags::text[]")
            else:
                # jsonb ?| :tags::text[]
                sql = sql_tmpl.replace("{TAGS_PREDICATE}", "tags ?| :tags::text[]")
        else:
            sql = sql_tmpl

        sql = sql + " ORDER BY difficulty NULLS LAST LIMIT :limit"
        params = dict(params)
        params["limit"] = limit

        result = session.execute(text(sql), params)
        rows = [dict(r._mapping) for r in result.fetchall()]
        return rows
