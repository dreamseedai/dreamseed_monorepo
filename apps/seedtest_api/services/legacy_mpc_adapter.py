from __future__ import annotations

"""
legacy_mpc_adapter: Read-only bridge to serve questions from a legacy schema (mpcstudy)

This adapter lets us surface "real" production data without migrating schemas.
It supports an HTTP JSON bridge via two configurable URL templates in settings:

- settings.MPC_HTTP_LIST_URL: e.g.,
  "https://mpcstudy.com/api/questions?query={q}&page={page}&limit={limit}"
- settings.MPC_HTTP_DETAIL_URL: e.g.,
  "https://mpcstudy.com/api/questions/{id}"

Both templates are formatted with safe parameters; missing placeholders are ignored.
Expected response shapes are flexible, and mapping heuristics normalize to our Question contract.

IMPORTANT: This is read-only and used only by GET endpoints when
settings.USE_MPC_LEGACY_READONLY is True.
"""

from typing import Any, Dict, List, Optional, Tuple
import json
import re
import requests

from ..settings import settings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Minimal Pydantic-like dict shape expected by routers.questions.Question
QuestionDict = Dict[str, Any]


def _fmt_url(tpl: str, params: Dict[str, Any]) -> str:
    # Safe format: only replace known placeholders; ignore KeyError gracefully
    try:
        return tpl.format(**params)
    except Exception:
        return tpl


def _pick(obj: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in obj and obj[k] is not None:
            return obj[k]
    return None


def _to_str_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        out: List[str] = []
        for it in v:
            try:
                s = str(it).strip()
                if s:
                    out.append(s)
            except Exception:
                pass
        return out
    try:
        s = str(v).strip()
        return [s] if s else []
    except Exception:
        return []


def _to_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _norm_difficulty(v: Any) -> str:
    # Map numeric to buckets; pass through strings when valid
    s = str(v).strip().lower() if v is not None else ""
    if s in ("easy", "medium", "hard"):
        return s
    try:
        f = float(v)
        if f < 0.34:
            return "easy"
        if f < 0.67:
            return "medium"
        return "hard"
    except Exception:
        return "medium"


def _extract_options_answer(obj: Dict[str, Any]) -> Tuple[List[str], int]:
    # Try common shapes
    # 1) options: [str], answer as index/int
    opts = obj.get("options")
    ans = obj.get("answer")
    if isinstance(opts, list) and all(isinstance(x, (str, int, float)) for x in opts):
        return [str(x) for x in opts], _to_int(ans, 0)
    # 2) choices: [{content, is_correct}] or similar
    ch = obj.get("choices") or obj.get("choice_list")
    if isinstance(ch, list) and ch:
        options: List[str] = []
        ans_idx = 0
        for i, c in enumerate(ch):
            if isinstance(c, dict):
                ct = _pick(c, "content", "text", "label", "title")
                options.append(str(ct or f"Option {i+1}"))
                if bool(c.get("is_correct") or c.get("correct")) and ans_idx == 0:
                    ans_idx = i
            else:
                options.append(str(c))
        return options, ans_idx
    # 3) Single string of delimited options
    s = _pick(obj, "options_csv", "choices_csv", "options_str", "choices_str")
    if isinstance(s, str) and s.strip():
        parts = [p.strip() for p in re.split(r"[|;,]", s) if p.strip()]
        return parts, min(len(parts) - 1, _to_int(ans, 0))
    # Fallback
    return ["A", "B", "C", "D"], 0


def _parse_maybe_json_list(s: Any) -> Optional[List[str]]:
    try:
        if s is None:
            return None
        if isinstance(s, list):
            return [str(it) for it in s]
        if isinstance(s, str):
            st = s.strip()
            if st.startswith("[") and st.endswith("]"):
                arr = json.loads(st)
                if isinstance(arr, list):
                    return [str(it) for it in arr]
        return None
    except Exception:
        return None


def _split_delimited(s: Any) -> Optional[List[str]]:
    if s is None:
        return None
    try:
        text = str(s)
        # Try common delimiters used in exports
        parts = [p.strip() for p in re.split(r"\r?\n|\|\||[|;,]", text) if p.strip()]
        return parts if parts else None
    except Exception:
        return None


def _answer_char_to_index(c: Any) -> int:
    try:
        if c is None:
            return 0
        ch = str(c).strip().upper()
        if not ch:
            return 0
        return max(0, ord(ch[0]) - ord('A'))
    except Exception:
        return 0


def _map_legacy_item(x: Dict[str, Any]) -> QuestionDict:
    qid = str(_pick(x, "id", "question_id", "qid", "uuid", "slug") or "")
    # Prefer English-labeled fields when available
    title = _pick(x, "que_en_title", "title_en", "title", "name")
    stem = _pick(x, "que_en_desc", "que_en_stem", "que_en_content", "stem", "content", "question", "body", "text") or ""
    explanation = _pick(x, "que_en_solution", "solution_en", "explanation", "solution", "desc", "explain")
    
    # Handle MySQL legacy format: options_raw (text) + answer_char (A,B,C,D)
    # Options/answer extraction with MySQL/English variants
    options_raw = x.get("options_raw")
    answer_char = x.get("answer_char")
    options_en = _pick(x, "que_en_answers", "answers_en")
    answer_char_en = _pick(x, "que_en_answerm", "answer_en_char")
    answer_idx_fields = _pick(x, "que_en_answer_idx", "answer_idx", "answer_index")

    options: List[str]
    answer: int

    if options_en is not None:
        opts = _parse_maybe_json_list(options_en) or _split_delimited(options_en) or []
        if answer_char_en is not None:
            ans_idx = _answer_char_to_index(answer_char_en)
        elif answer_idx_fields is not None:
            ans_idx = _to_int(answer_idx_fields, 0)
        elif answer_char is not None:
            ans_idx = _answer_char_to_index(answer_char)
        else:
            ans_idx = _to_int(_pick(x, "answer"), 0)
        options, answer = (opts or ["A", "B", "C", "D"]), ans_idx
    elif options_raw and answer_char:
        # Parse options_raw: try JSON first, then split by newline/delimiter
        opts_list = _parse_maybe_json_list(options_raw) or _split_delimited(options_raw) or []
        options = opts_list or ["A", "B", "C", "D"]
        answer = _answer_char_to_index(answer_char)
    else:
        options, answer = _extract_options_answer(x)
    
    # Map que_level (1,2,3) to difficulty (easy, medium, hard)
    level_val = _pick(x, "que_level", "level")
    if level_val:
        difficulty = "easy" if int(level_val) == 1 else ("medium" if int(level_val) == 2 else "hard")
    else:
        difficulty = _norm_difficulty(_pick(x, "difficulty", "diff", "difficulty_score"))
    
    # Map que_class (M, P, C, etc.) to topic name
    que_class = _pick(x, "que_class", "class")
    que_grade = _pick(x, "que_grade", "grade")
    topic_name = _pick(x, "topic", "topic_name", "subject")
    if que_class and not topic_name:
        class_map = {"M": "Mathematics", "P": "Physics", "C": "Chemistry", "B": "Biology", "E": "English"}
        topic_name = class_map.get(str(que_class).upper(), str(que_class).upper())
        if que_grade:
            topic_name = f"{topic_name} {que_grade}"
    
    topic = topic_name
    topic_id = _pick(x, "topic_id", "tid")
    tags = _to_str_list(_pick(x, "tags", "tag_list", "keywords"))
    status = str(_pick(x, "status", "state") or "published").strip() or "published"
    author = _pick(x, "author", "created_by", "writer")
    created_at = _pick(x, "created_at", "created", "created_ts")
    updated_at = _pick(x, "updated_at", "updated", "updated_ts")

    def _ts(v: Any) -> Optional[float]:
        try:
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return float(v)
            # try ISO8601
            import datetime as _dt
            s = str(v)
            if s.endswith("Z"):
                s = s.replace("Z", "+00:00")
            dt = _dt.datetime.fromisoformat(s)
            return float(dt.timestamp())
        except Exception:
            return None

    return {
        "org_id": None,
        "id": qid,
        "title": title,
        "stem": str(stem),
        "explanation": explanation,
        "options": options,
        "answer": int(answer),
        "difficulty": difficulty,
        "topic": topic,
        "topic_id": int(topic_id) if topic_id is not None else None,
        "tags": tags,
        "status": status,
        "author": author,
        "discrimination": None,
        "guessing": None,
        "created_at": _ts(created_at),
        "updated_at": _ts(updated_at),
    }


_PG_ENGINE: Optional[Engine] = None
_MYSQL_ENGINE: Optional[Engine] = None


def _get_pg_engine() -> Engine:
    global _PG_ENGINE
    if _PG_ENGINE is None:
        if not settings.MPC_PG_URL:
            raise RuntimeError("MPC_PG_URL is not configured")
        _PG_ENGINE = create_engine(settings.MPC_PG_URL, future=True)
    return _PG_ENGINE


def _get_mysql_engine() -> Engine:
    global _MYSQL_ENGINE
    if _MYSQL_ENGINE is None:
        if not settings.MPC_MYSQL_URL:
            raise RuntimeError("MPC_MYSQL_URL is not configured")
        # Use pool_pre_ping to avoid stale connections; future=True for SQLAlchemy 2.0 style
        _MYSQL_ENGINE = create_engine(
            settings.MPC_MYSQL_URL,
            future=True,
            pool_pre_ping=True,
        )
    return _MYSQL_ENGINE


def is_http_configured() -> bool:
    return bool(settings.MPC_HTTP_LIST_URL and settings.MPC_HTTP_DETAIL_URL)


def is_pg_configured() -> bool:
    return bool(settings.MPC_PG_URL and settings.MPC_PG_LIST_SQL and settings.MPC_PG_DETAIL_SQL)


def is_mysql_configured() -> bool:
    return bool(settings.MPC_MYSQL_URL and settings.MPC_MYSQL_LIST_SQL and settings.MPC_MYSQL_DETAIL_SQL)


def list_questions(
    q: Optional[str], topic: Optional[str], topic_id: Optional[int], difficulty: Optional[str], status: Optional[str],
    page: int, limit: int, sort_by: str, order: str, cursor: Optional[str]
) -> Dict[str, Any]:
    if is_pg_configured():
        eng = _get_pg_engine()
        with eng.connect() as conn:
            sql = settings.MPC_PG_LIST_SQL or ""
            # Calculate offset for MySQL compatibility
            offset = (int(page) - 1) * int(limit)
            params = {
                "q": q or "",
                "topic": topic or "",
                "topic_id": topic_id,
                "difficulty": difficulty or "",
                "status": status or "",
                "page": int(page),
                "limit": int(limit),
                "offset": offset,
                "sort_by": sort_by,
                "order": order,
                "cursor": cursor or "",
            }
            rows = conn.execute(text(sql), params).mappings().all()
            items = [_map_legacy_item(dict(r)) for r in rows]
            # If your SQL returns total and next_cursor, expose them via first row columns
            total = None
            next_cursor = None
            if rows:
                first = rows[0]
                total = first.get("_total") if "_total" in first else None
                next_cursor = first.get("_next_cursor") if "_next_cursor" in first else None
            return {"results": items, "total": int(total) if total is not None else len(items), "next_cursor_opaque": next_cursor}

    if is_mysql_configured():
        eng = _get_mysql_engine()
        with eng.connect() as conn:
            sql = settings.MPC_MYSQL_LIST_SQL or ""
            # MySQL uses LIMIT :limit OFFSET :offset; compute offset for pagination
            offset = (int(page) - 1) * int(limit)
            params = {
                "q": q or "",
                "topic": topic or "",
                "topic_id": topic_id,
                "difficulty": difficulty or "",
                "status": status or "",
                "page": int(page),
                "limit": int(limit),
                "offset": offset,
                "sort_by": sort_by,
                "order": order,
                "cursor": cursor or "",
            }
            rows = conn.execute(text(sql), params).mappings().all()
            items = [_map_legacy_item(dict(r)) for r in rows]
            total = None
            next_cursor = None
            if rows:
                first = rows[0]
                total = first.get("_total") if "_total" in first else None
                next_cursor = first.get("_next_cursor") if "_next_cursor" in first else None
            return {"results": items, "total": int(total) if total is not None else len(items), "next_cursor_opaque": next_cursor}

    if is_http_configured():
        params = {
            "q": q or "",
            "keyword": q or "",
            "topic": topic or "",
            "topic_id": topic_id or "",
            "difficulty": difficulty or "",
            "status": status or "",
            "page": page,
            "limit": limit,
            "sort_by": sort_by,
            "order": order,
            "cursor": cursor or "",
        }
        url = _fmt_url(settings.MPC_HTTP_LIST_URL or "", params)
        resp = requests.get(url, timeout=settings.MPC_HTTP_TIMEOUT_SECS)
        resp.raise_for_status()

        data = resp.json()
        items_raw: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            raw = data.get("results")
            if isinstance(raw, list):
                items_raw = raw  # type: ignore[assignment]
            total = int(data.get("total", len(items_raw)))
            next_cursor = data.get("next_cursor")
        else:
            if isinstance(data, list):
                items_raw = data  # type: ignore[assignment]
            total = len(items_raw)
            next_cursor = None

        items = [_map_legacy_item(x) for x in (items_raw or [])]
        return {"results": items, "total": total, "next_cursor_opaque": next_cursor}

    from fastapi import HTTPException
    raise HTTPException(503, "legacy_adapter_unconfigured")


def get_question(question_id: str) -> QuestionDict:
    if is_pg_configured():
        eng = _get_pg_engine()
        with eng.connect() as conn:
            sql = settings.MPC_PG_DETAIL_SQL or ""
            row = conn.execute(text(sql), {"id": question_id}).mappings().first()
            if row is None:
                from fastapi import HTTPException
                raise HTTPException(404, "not_found")
            return _map_legacy_item(dict(row))

    if is_mysql_configured():
        eng = _get_mysql_engine()
        with eng.connect() as conn:
            sql = settings.MPC_MYSQL_DETAIL_SQL or ""
            row = conn.execute(text(sql), {"id": question_id}).mappings().first()
            if row is None:
                from fastapi import HTTPException
                raise HTTPException(404, "not_found")
            return _map_legacy_item(dict(row))

    if is_http_configured():
        url = _fmt_url(settings.MPC_HTTP_DETAIL_URL or "", {"id": question_id})
        resp = requests.get(url, timeout=settings.MPC_HTTP_TIMEOUT_SECS)
        if resp.status_code == 404:
            from fastapi import HTTPException
            raise HTTPException(404, "not_found")
        resp.raise_for_status()
        data = resp.json()
        item = data.get("item") if isinstance(data, dict) and "item" in data else data
        return _map_legacy_item(item or {})

    from fastapi import HTTPException
    raise HTTPException(503, "legacy_adapter_unconfigured")
