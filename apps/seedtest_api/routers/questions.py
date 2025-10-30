from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request
from pydantic import BaseModel, Field, field_validator

from ..deps import User, get_current_user
from ..settings import settings
from ..services.cache import get_cache
from ..services import db as db_service
from ..services import idempotency as idem_svc
from ..services.choices_adapter import (
    read_options_answer,
    write_choices_from_options,
    read_options_answer_batch,
)
from ..services import legacy_mpc_adapter as legacy_mpc
from ..models.question import QuestionRow
from ..models.topic import TopicRow
from sqlalchemy import select, func, and_, or_, Integer
import time as _time


router = APIRouter(prefix=f"{settings.API_PREFIX}", tags=["questions"])


# ---- Schemas ----
Difficulty = Literal["easy", "medium", "hard"]
Status = Literal["draft", "published", "deleted"]


class Question(BaseModel):
    org_id: int | None = None
    id: str
    title: str | None = None
    stem: str
    explanation: str | None = None
    options: list[str]
    answer: int = Field(ge=0)
    difficulty: Difficulty
    topic: str | None = None
    topic_id: int | None = None
    tags: list[str] = []
    status: Status = "draft"
    author: str | None = None
    created_by: str | None = None
    updated_by: str | None = None
    discrimination: float | None = None
    guessing: float | None = None
    created_at: float | None = None
    updated_at: float | None = None

    @field_validator("options")
    @classmethod
    def _validate_options(cls, v: list[str]):
        if not v or not isinstance(v, list):
            raise ValueError("options must be a non-empty list")
        if any(not isinstance(x, str) or not x.strip() for x in v):
            raise ValueError("options must be non-empty strings")
        return v

    @field_validator("answer")
    @classmethod
    def _validate_answer(cls, v: int, info):
        # Can't access options length here reliably; range check on update/create
        if v < 0:
            raise ValueError("answer must be >= 0")
        return v


class QuestionInput(BaseModel):
    # Admin only: optionally set org_id for creation; ignored/guarded for teachers
    org_id: int | None = None
    title: str | None = None
    stem: str
    explanation: str | None = None
    options: list[str]
    answer: int = Field(ge=0)
    difficulty: Difficulty
    topic: str | None = None
    topic_id: int | None = None
    tags: list[str] = []
    status: Status = "draft"
    author: str | None = None
    discrimination: float | None = None
    guessing: float | None = None

    @field_validator("discrimination")
    @classmethod
    def _validate_discrimination(cls, v: float | None):
        if v is None:
            return v
        if not isinstance(v, (int, float)):
            raise ValueError("discrimination must be a number")
        if v <= 0:
            raise ValueError("discrimination (a) must be > 0")
        return float(v)

    @field_validator("guessing")
    @classmethod
    def _validate_guessing(cls, v: float | None):
        if v is None:
            return v
        if not isinstance(v, (int, float)):
            raise ValueError("guessing must be a number")
        # 3PL c parameter: 0 <= c < 1
        if v < 0 or v >= 1:
            raise ValueError("guessing (c) must satisfy 0 <= c < 1")
        return float(v)


class QuestionListResponse(BaseModel):
    results: list[Question]
    total: int
    next_cursor_opaque: str | None = None


class OkResponse(BaseModel):
    ok: bool = True
def _irt_recommended_warnings(a: float | None, c: float | None) -> list[str]:
    warnings: list[str] = []
    try:
        if a is not None and (a < 0.5 or a > 2.5):
            warnings.append("discrimination a outside recommended 0.5-2.5")
    except Exception:
        pass
    try:
        if c is not None and (c > 0.35):
            warnings.append("guessing c outside recommended 0.00-0.35")
    except Exception:
        pass
    return warnings


def _require_admin(user: User):
    if not user or not user.is_admin():
        raise HTTPException(403, "admin_only")


class TopicCreate(BaseModel):
    name: str
    org_id: int | None = None
    parent_topic_id: int | None = None


class TopicUpdate(BaseModel):
    name: str | None = None
    parent_topic_id: int | None = None


class TopicMerge(BaseModel):
    target_id: int


# ---- In-memory store (process-local) ----
_LOCK = threading.Lock()
_STORE: dict[str, Question] = {}


def _now() -> float:
    return time.time()


def _require_teacher_or_admin(user: User):
    if not user:
        raise HTTPException(401, "unauthorized")
    if not (user.is_teacher() or user.is_admin()):
        raise HTTPException(403, "forbidden")


def _ensure_teacher_can_write(user: User, row: QuestionRow):
    """Enforce org-based write access for teachers. Admins are allowed.

    - Teacher cannot modify global questions (org_id is NULL)
    - Teacher's org_id must match the row's org_id
    """
    if user.is_admin():
        return
    if not user.is_teacher():
        raise HTTPException(403, "forbidden")
    # Teacher path
    row_org = getattr(row, "org_id", None)
    if row_org is None:
        # Exception: allow if teacher is the creator/author of the global question
        created_by = getattr(row, "created_by", None)
        author = getattr(row, "author", None)
        if (created_by and str(created_by) == str(user.user_id)) or (author and str(author) == str(user.user_id)):
            return
        raise HTTPException(403, "forbidden_global")
    if user.org_id is None or int(user.org_id) != int(row_org):
        raise HTTPException(403, "forbidden_org")


def _db_enabled() -> bool:
    try:
        return bool(settings.DATABASE_URL)
    except Exception:
        return False


def _row_to_question(r: QuestionRow) -> Question:
    """Map ORM row to Pydantic model safely for type checkers."""
    _id = str(getattr(r, "id"))
    _title = getattr(r, "title", None)
    _org = getattr(r, "org_id", None)
    _stem = getattr(r, "stem")
    _explanation = getattr(r, "explanation", None)
    _options = getattr(r, "options") or []
    _answer = int(getattr(r, "answer"))
    _difficulty = getattr(r, "difficulty")
    _topic = getattr(r, "topic")
    _topic_id = getattr(r, "topic_id", None)
    _tags = getattr(r, "tags") or []
    _status = getattr(r, "status")
    _author = getattr(r, "author")
    _created_by = getattr(r, "created_by", None)
    _updated_by = getattr(r, "updated_by", None)
    _discrimination = getattr(r, "discrimination", None)
    _guessing = getattr(r, "guessing", None)
    _created = getattr(r, "created_at")
    _updated = getattr(r, "updated_at")
    created_ts = _created.timestamp() if _created is not None else None
    updated_ts = _updated.timestamp() if _updated is not None else None
    return Question(
        org_id=_org if _org is None else int(_org),
        id=_id,
        title=_title,
        stem=_stem,
        explanation=_explanation,
        options=list(_options),
        answer=_answer,
        difficulty=_difficulty,
        topic=_topic,
        topic_id=int(_topic_id) if _topic_id is not None else None,
        tags=list(_tags),
        status=_status,
        author=_author,
        created_by=_created_by,
        updated_by=_updated_by,
        discrimination=_discrimination,
        guessing=_guessing,
        created_at=created_ts,
        updated_at=updated_ts,
    )


def _seed_if_empty():
    if _STORE:
        return
    with _LOCK:
        if _STORE:
            return
        # Minimal seed for first run
        for i in range(1, 7):
            qid = str(i)
            now = _now()
            _STORE[qid] = Question(
                org_id=None,
                id=qid,
                title=f"샘플 문항 {i}",
                stem=f"샘플 문항 {i}. 다음 중 옳은 것을 고르시오.",
                explanation=None,
                options=["A", "B", "C", "D"],
                answer=i % 4,
                difficulty=("easy", "medium", "hard")[i % 3],
                topic=("대수", "기하", "확률")[i % 3],
                tags=["기초", "핵심"][: (i % 2) + 1],
                status="draft" if (i % 2) else "published",
                author="system",
                discrimination=None,
                guessing=None,
                created_at=now,
                updated_at=now,
            )


@router.get(
    "/questions",
    summary="List questions with simple filters, pagination, and sorting",
    response_model=QuestionListResponse,
)
def list_questions(
    q: str | None = Query(default=None, description="Keyword in stem or tags (alias: keyword)"),
    keyword: str | None = Query(default=None, description="Alias for q; preferred in OpenAPI"),
    topic: str | None = Query(default=None),
    topic_id: int | None = Query(default=None, description="Filter by topic id (when topics table is enabled)"),
    difficulty: Difficulty | None = Query(default=None),
    status: Status | None = Query(default=None),
    page: int = Query(default=1, ge=1, description="1-based page number (offset pagination)"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page (alias: page_size)"),
    page_size: int | None = Query(default=None, ge=1, le=100, description="Alias for limit"),
    sort_by: str = Query(default="updated_at", pattern="^(updated_at|created_at|difficulty|topic|status)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    *,
    response: Response,
    current_user: User = Depends(get_current_user),
    cursor: str | None = Query(default=None, description="Opaque cursor for keyset pagination (sort_by must be created_at or updated_at)"),
    org_id: int | None = Query(default=None, description="Filter by org (admin only)")
) -> Any:
    _require_teacher_or_admin(current_user)
    # Normalize aliases
    q_eff = keyword if (keyword and keyword.strip()) else q
    per_page = page_size if (page_size and page_size > 0) else limit
    # Legacy read-only bridge (serve from mpcstudy via HTTP adapter)
    if getattr(settings, "USE_MPC_LEGACY_READONLY", False):
        try:
            res = legacy_mpc.list_questions(
                q=q_eff,
                topic=topic,
                topic_id=topic_id,
                difficulty=difficulty,
                status=status,
                page=page,
                limit=per_page,
                sort_by=sort_by,
                order=order,
                cursor=cursor,
            )
            # Mark data source for frontend hints
            try:
                src = "legacy"
                try:
                    if legacy_mpc.is_pg_configured():
                        src = "legacy:postgres"
                    elif legacy_mpc.is_mysql_configured():
                        src = "legacy:mysql"
                    elif legacy_mpc.is_http_configured():
                        src = "legacy:http"
                except Exception:
                    pass
                response.headers["X-Data-Source"] = src
            except Exception:
                pass
            # Response shape already matches
            return res
        except HTTPException:
            raise
        except Exception:
            # Fallback to normal paths on adapter failure
            pass

    # If DB enabled, serve from DB; else fallback to in-memory store
    if _db_enabled():
        with db_service.get_session() as s:
            # Base query with filters
            where = []
            # Prefer direct column filter when topic_id is provided
            if topic_id is not None:
                where.append(QuestionRow.topic_id == int(topic_id))
            if q_eff:
                k = f"%{q_eff.lower()}%"
                where.append(func.lower(QuestionRow.stem).like(k))
            # Fallback to topic string filter
            if topic and topic_id is None:
                where.append(QuestionRow.topic == topic)
            if difficulty:
                where.append(QuestionRow.difficulty == difficulty)
            if status:
                where.append(QuestionRow.status == status)
            else:
                where.append(QuestionRow.status != "deleted")

            # Role/org-based visibility
            if current_user.is_teacher():
                # Teachers must have org and may view own-org items and global items
                if current_user.org_id is None:
                    raise HTTPException(403, "missing_org")
                where.append(
                    or_(
                        QuestionRow.org_id == int(current_user.org_id),
                        QuestionRow.org_id.is_(None),
                    )
                )
            elif current_user.is_admin():
                # Admin optional org filter
                if org_id is not None:
                    where.append(QuestionRow.org_id == int(org_id))

            query = select(QuestionRow).where(and_(*where)) if where else select(QuestionRow)

            # Sorting
            if sort_by == "updated_at":
                order_col = QuestionRow.updated_at
            elif sort_by == "created_at":
                order_col = QuestionRow.created_at
            elif sort_by == "difficulty":
                # Map difficulty to rank via CASE: easy<medium<hard
                from sqlalchemy import case
                order_col = case(
                    (QuestionRow.difficulty == "easy", 0),
                    (QuestionRow.difficulty == "medium", 1),
                    (QuestionRow.difficulty == "hard", 2),
                    else_=99,
                )
            elif sort_by == "topic":
                order_col = QuestionRow.topic
            elif sort_by == "status":
                order_col = QuestionRow.status
            else:
                order_col = QuestionRow.updated_at

            if order == "desc":
                query = query.order_by(order_col.desc(), QuestionRow.id.desc())
            else:
                query = query.order_by(order_col.asc(), QuestionRow.id.asc())

            total = s.execute(select(func.count()).select_from(query.subquery())).scalar_one()

            next_cursor_token = None
            if cursor and sort_by in ("updated_at", "created_at"):
                try:
                    cur_ts, cur_id = _decode_cursor(cursor)
                    import datetime as _dt
                    if cur_ts.endswith("Z"):
                        cur_ts = cur_ts.replace("Z", "+00:00")
                    ts_dt = _dt.datetime.fromisoformat(cur_ts)
                    
                    # Convert cursor datetime to epoch seconds (UTC)
                    if ts_dt.tzinfo is None:
                        # naive → treat as UTC
                        ts_dt = ts_dt.replace(tzinfo=_dt.timezone.utc)
                    else:
                        # ensure UTC
                        ts_dt = ts_dt.astimezone(_dt.timezone.utc)
                    ts_epoch = int(ts_dt.timestamp())
                except Exception:
                    raise HTTPException(400, "invalid_cursor")
                
                sort_col = QuestionRow.updated_at if sort_by == "updated_at" else QuestionRow.created_at
                
                # Build keyset filter based on database dialect
                try:
                    bind = s.get_bind()
                    dialect = getattr(bind, "dialect", None)
                    dname = getattr(dialect, "name", "") if dialect else ""
                    
                    if dname == "sqlite":
                        # SQLite: compare epoch seconds using strftime
                        # Cast to integer for proper numeric comparison
                        epoch_col = func.cast(func.strftime('%s', sort_col, 'utc'), Integer)
                        if order == "desc":
                            cursor_filter = or_(
                                epoch_col < ts_epoch,
                                and_(epoch_col == ts_epoch, QuestionRow.id < cur_id)
                            )
                        else:
                            cursor_filter = or_(
                                epoch_col > ts_epoch,
                                and_(epoch_col == ts_epoch, QuestionRow.id > cur_id)
                            )
                    else:
                        # PostgreSQL and others: direct datetime comparison
                        if order == "desc":
                            cursor_filter = or_(
                                sort_col < ts_dt,
                                and_(sort_col == ts_dt, QuestionRow.id < cur_id)
                            )
                        else:
                            cursor_filter = or_(
                                sort_col > ts_dt,
                                and_(sort_col == ts_dt, QuestionRow.id > cur_id)
                            )
                except Exception:
                    # Fallback: direct datetime comparison
                    if order == "desc":
                        cursor_filter = or_(
                            sort_col < ts_dt,
                            and_(sort_col == ts_dt, QuestionRow.id < cur_id)
                        )
                    else:
                        cursor_filter = or_(
                            sort_col > ts_dt,
                            and_(sort_col == ts_dt, QuestionRow.id > cur_id)
                        )
                
                query = query.where(cursor_filter)
                rows = s.execute(query.limit(per_page)).scalars().all()
            else:
                rows = s.execute(query.offset((page - 1) * per_page).limit(per_page)).scalars().all()

            # Map rows to full Question models (including title/explanation/params)
            items = [_row_to_question(r) for r in rows]

            # If using choices table, batch-load options/answer to avoid N+1 and override per item
            if getattr(settings, "USE_CHOICES_TABLE", False) and items:
                try:
                    id_list = [str(getattr(r, "id")) for r in rows]
                    mapping = read_options_answer_batch(s.connection(), id_list)
                    for it in items:
                        m = mapping.get(str(it.id))
                        if m is not None:
                            opts, ans = m
                            it.options = opts
                            if ans >= 0:
                                it.answer = ans
                except Exception:
                    # Graceful fallback if choices table absent or query fails
                    pass

            if sort_by in ("updated_at", "created_at") and len(items) == per_page and total > per_page:
                last = items[-1]
                import datetime as _dt
                ts_val = (last.updated_at if sort_by == "updated_at" else last.created_at) or 0.0
                ts_iso = _dt.datetime.fromtimestamp(float(ts_val), _dt.UTC).isoformat().replace("+00:00", "") + "Z"
                next_cursor_token = _encode_cursor_v1(ts_iso, str(last.id), sort_by)

            return {"results": items, "total": int(total), "next_cursor_opaque": next_cursor_token}

    # In-memory fallback
    _seed_if_empty()
    with _LOCK:
        # ... existing in-memory logic remains unchanged ...
        items = list(_STORE.values())
        def match(x: Question) -> bool:
            # Role/org-based visibility for in-memory fallback
            if current_user.is_teacher():
                if current_user.org_id is None:
                    raise HTTPException(403, "missing_org")
                if not (x.org_id is None or int(x.org_id) == int(current_user.org_id)):
                    return False
            if q_eff:
                k = q_eff.lower()
                if not (
                    x.stem.lower().find(k) >= 0
                    or any((t or "").lower().find(k) >= 0 for t in x.tags)
                ):
                    return False
            if topic and x.topic != topic:
                return False
            if difficulty and x.difficulty != difficulty:
                return False
            if status:
                if x.status != status:
                    return False
            else:
                if x.status == "deleted":
                    return False
            return True

        hits = [x for x in items if match(x)]
        reverse = (order == "desc")
        def key_func(x: Question):
            if sort_by == "updated_at":
                v = x.updated_at or x.created_at or 0.0
                return float(v)
            if sort_by == "created_at":
                v = x.created_at or 0.0
                return float(v)
            if sort_by == "difficulty":
                rank = {"easy": 0, "medium": 1, "hard": 2}
                return rank.get(x.difficulty, 99)
            if sort_by == "topic":
                return (x.topic or "")
            if sort_by == "status":
                return (x.status or "")
            return 0
        try:
            hits.sort(key=key_func, reverse=reverse)
        except Exception:
            pass
        total = len(hits)
        next_cursor = None
        if cursor and sort_by in ("updated_at", "created_at"):
            try:
                cur_ts, cur_id = _decode_cursor(cursor)
            except Exception:
                raise HTTPException(400, "invalid_cursor")
            try:
                import datetime as _dt
                if cur_ts.endswith("Z"):
                    cur_ts = cur_ts.replace("Z", "+00:00")
                ts_dt = _dt.datetime.fromisoformat(cur_ts)
                cur_ts_val = ts_dt.timestamp()
            except Exception:
                raise HTTPException(400, "invalid_cursor")
            def tval(x: Question) -> float:
                return float((x.updated_at if sort_by == "updated_at" else x.created_at) or 0.0)
            def before_desc(x: Question) -> bool:
                tv = tval(x)
                if tv < cur_ts_val:
                    return True
                if tv > cur_ts_val:
                    return False
                return str(x.id) < str(cur_id)
            def after_asc(x: Question) -> bool:
                tv = tval(x)
                if tv > cur_ts_val:
                    return True
                if tv < cur_ts_val:
                    return False
                return str(x.id) > str(cur_id)
            pred = before_desc if order == "desc" else after_asc
            page_items = [x for x in hits if pred(x)][:per_page]
        else:
            start = (page - 1) * per_page
            end = start + per_page
            page_items = hits[start:end]
        if sort_by in ("updated_at", "created_at") and len(page_items) == per_page and (len(hits) > per_page):
            last = page_items[-1]
            import datetime as _dt
            ts_val = (last.updated_at if sort_by == "updated_at" else last.created_at) or 0.0
            ts_iso = _dt.datetime.fromtimestamp(float(ts_val), _dt.UTC).isoformat().replace("+00:00", "") + "Z"
            next_cursor = _encode_cursor_v1(ts_iso, str(last.id), sort_by)
        return {"results": page_items, "total": total, "next_cursor_opaque": next_cursor}


@router.get(
    "/questions/topics",
    summary="List unique topics",
    response_model=list[str],
)
def list_topics(current_user: User = Depends(get_current_user)) -> Any:
    _require_teacher_or_admin(current_user)
    # Shared cache (Redis when available) with local TTL fallback
    cache = get_cache()
    ttl = getattr(settings, "TOPICS_CACHE_TTL_SECS", 300) or 300
    use_table = getattr(settings, "USE_TOPICS_TABLE", False)
    # Include org in cache key when using topics table with org scoping
    if use_table and current_user.is_teacher():
        org_key = f"org_{int(current_user.org_id) if current_user.org_id is not None else 0}"
    else:
        org_key = "global"
    key = f"topics:{'table' if use_table else 'legacy'}:{org_key}"

    def _fetch_topics() -> list[str]:
        if _db_enabled():
            try:
                with db_service.get_session() as s:
                    if use_table:
                        # From topics table with org scoping
                        where = []
                        if current_user.is_teacher():
                            if current_user.org_id is None:
                                raise HTTPException(403, "missing_org")
                            where.append(or_(TopicRow.org_id.is_(None), TopicRow.org_id == int(current_user.org_id)))
                        else:
                            # Admin: return global topics for now
                            where.append(TopicRow.org_id.is_(None))
                        stmt = select(TopicRow.name).where(and_(*where)) if where else select(TopicRow.name)
                        rows = s.execute(stmt).all()
                        vals: set[str] = set()
                        for (name,) in rows:
                            if name and isinstance(name, str) and name.strip():
                                vals.add(name.strip())
                        return sorted(vals)
                    else:
                        # Legacy: distinct topics from questions table
                        rows = s.execute(
                            select(QuestionRow.topic).where(and_(QuestionRow.status != "deleted", QuestionRow.topic.is_not(None)))
                        ).all()
                        vals: set[str] = set()
                        for (t,) in rows:
                            if t and isinstance(t, str) and t.strip():
                                vals.add(t.strip())
                        return sorted(vals)
            except Exception:
                # On DB errors (e.g., unmigrated schema), fall through to in-memory fallback
                pass
        _seed_if_empty()
        with _LOCK:
            topics: set[str] = set()
            for q in _STORE.values():
                if q.status == "deleted":
                    continue
                t = (q.topic or "").strip()
                if t:
                    topics.add(t)
            return sorted(topics)

    return cache.cached_get_set(key, ttl, _fetch_topics)


@router.get(
    "/questions/{question_id}",
    summary="Get a question by id",
    response_model=Question,
)
def get_question(question_id: str, response: Response, current_user: User = Depends(get_current_user)) -> Any:
    _require_teacher_or_admin(current_user)
    # Legacy read-only bridge first
    if getattr(settings, "USE_MPC_LEGACY_READONLY", False):
        try:
            item = legacy_mpc.get_question(question_id)
            # No ETag from legacy; omit header
            try:
                if response is not None:
                    src = "legacy"
                    try:
                        if legacy_mpc.is_pg_configured():
                            src = "legacy:postgres"
                        elif legacy_mpc.is_mysql_configured():
                            src = "legacy:mysql"
                        elif legacy_mpc.is_http_configured():
                            src = "legacy:http"
                    except Exception:
                        pass
                    response.headers["X-Data-Source"] = src
            except Exception:
                pass
            return Question(**item)  # type: ignore[arg-type]
        except HTTPException:
            raise
        except Exception:
            pass
    if _db_enabled():
        with db_service.get_session() as s:
            row = s.get(QuestionRow, question_id)
            if row is None or getattr(row, "status") == "deleted":
                raise HTTPException(404, "not_found")
            # Teacher can view only own-org and global
            if current_user.is_teacher():
                row_org = getattr(row, "org_id", None)
                if row_org is not None and (
                    current_user.org_id is None or int(current_user.org_id) != int(row_org)
                ):
                    raise HTTPException(403, "forbidden_org")
            # Map to Pydantic
            q = _row_to_question(row)
            # Set ETag header based on updated_at
            try:
                etag = _compute_etag(row)
                if etag and response is not None:
                    response.headers["ETag"] = etag
            except Exception:
                pass
            # Optionally override options/answer from choices table for response
            if getattr(settings, "USE_CHOICES_TABLE", False):
                try:
                    res = read_options_answer(s.connection(), question_id)
                    if res is not None:
                        opts, ans = res
                        q.options = opts
                        q.answer = ans if ans >= 0 else q.answer
                except Exception:
                    # If table missing or error occurs, ignore and keep row-based fields
                    pass
            return q
    with _LOCK:
        q = _STORE.get(question_id)
        if not q:
            raise HTTPException(404, "not_found")
        if q.status == "deleted":
            raise HTTPException(404, "not_found")
        # Set ETag for in-memory mode
        try:
            if q.updated_at is not None:
                ms = int(float(q.updated_at) * 1000)
                et = f'W/"q:{q.id}:{ms}"'
                response.headers["ETag"] = et
        except Exception:
            pass
        return q


@router.post(
    "/questions",
    summary="Create a question",
    response_model=Question,
    status_code=201,
)
def create_question(
    body: QuestionInput, response: Response, request: Request, current_user: User = Depends(get_current_user)
) -> Any:
    _require_teacher_or_admin(current_user)
    if body.answer >= len(body.options):
        raise HTTPException(400, "answer_out_of_range")
    if _db_enabled():
        with db_service.get_session() as s:
            # Idempotency: check stored result first when key provided
            idem_key = None
            try:
                idem_key = request.headers.get("Idempotency-Key") if request else None
            except Exception:
                idem_key = None
            if idem_key:
                user_id_str = getattr(current_user, "user_id", None)
                org_id_attr = getattr(current_user, "org_id", None)
                try:
                    org_id_val = int(org_id_attr) if org_id_attr is not None else None
                except Exception:
                    org_id_val = None
                existing = idem_svc.find_existing(
                    s,
                    method="POST",
                    path=str(request.url.path if request else f"{settings.API_PREFIX}/questions"),
                    user_id=user_id_str,
                    org_id=org_id_val,
                    idem_key=str(idem_key),
                )
                if existing:
                    req_hash_existing, stored = existing
                    new_hash = idem_svc.compute_request_hash(body)
                    if req_hash_existing and new_hash != req_hash_existing:
                        raise HTTPException(409, "idempotency_key_conflict")
                    # Replay stored
                    if response is not None and stored.headers_json:
                        try:
                            for k, v in stored.headers_json.items():
                                if v is not None:
                                    response.headers[str(k)] = str(v)
                        except Exception:
                            pass
                    from fastapi.responses import JSONResponse
                    return JSONResponse(status_code=stored.status_code, content=stored.body_json)
            qid = str(uuid.uuid4())
            # Determine org_id based on role and policy
            new_org_id: int | None = None
            if current_user.is_teacher():
                if current_user.org_id is None:
                    raise HTTPException(403, "missing_org")
                # Teachers cannot override to another org or global
                if body.org_id is not None and int(body.org_id) != int(current_user.org_id):
                    raise HTTPException(403, "forbidden_org_override")
                new_org_id = int(current_user.org_id)
            elif current_user.is_admin():
                # Admin may set org_id explicitly; else follow DEFAULT_GLOBAL_ON_ADMIN_CREATE (default global)
                if body.org_id is not None:
                    new_org_id = int(body.org_id)
                else:
                    new_org_id = None
            # Resolve topic from topic_id if provided (topics table)
            topic_name: str | None = body.topic
            topic_id_val: int | None = None
            if body.topic_id is not None and getattr(settings, "USE_TOPICS_TABLE", False):
                try:
                    from ..models.topic import TopicRow  # local import
                    tr = s.get(TopicRow, int(body.topic_id))
                    if tr is None:
                        raise HTTPException(422, "invalid_topic_id")
                    if current_user.is_teacher():
                        if current_user.org_id is None:
                            raise HTTPException(403, "missing_org")
                        t_org = getattr(tr, "org_id", None)
                        if t_org is not None and int(t_org) != int(current_user.org_id):
                            raise HTTPException(403, "forbidden_org_topic")
                    topic_name = getattr(tr, "name", None) or topic_name
                    topic_id_val = int(getattr(tr, "id"))
                except HTTPException:
                    raise
                except Exception:
                    # If topics table isn't available, ignore and fall back to body.topic
                    pass

            row = QuestionRow(
                id=qid,
                org_id=new_org_id,
                title=body.title,
                stem=body.stem,
                explanation=body.explanation,
                options=list(body.options or []),
                answer=int(body.answer),
                difficulty=body.difficulty,
                topic=topic_name,
                topic_id=topic_id_val,
                status=body.status,
                author=current_user.user_id,
                created_by=current_user.user_id,
                updated_by=current_user.user_id,
                discrimination=body.discrimination,
                guessing=body.guessing,
            )
            # Admins: default-global on create can be adjusted by settings; teachers always set org
            # For now, we honor DEFAULT_GLOBAL_ON_ADMIN_CREATE (True by default) implicitly via org_id=None above.
            s.add(row)
            s.flush()
            # If configured, write choices from options/answer for storage
            if getattr(settings, "USE_CHOICES_TABLE", False):
                try:
                    write_choices_from_options(s.connection(), qid, list(body.options or []), int(body.answer))
                except Exception:
                    pass
            # Fetch timestamps
            s.refresh(row)
            q = _row_to_question(row)
            # For response, prefer choices table values if enabled
            if getattr(settings, "USE_CHOICES_TABLE", False):
                try:
                    res = read_options_answer(s.connection(), qid)
                    if res is not None:
                        opts, ans = res
                        q.options = opts
                        if ans >= 0:
                            q.answer = ans
                except Exception:
                    pass
            # Attach soft warnings for out-of-range IRT values (not validation errors)
            if response is not None:
                warns = _irt_recommended_warnings(body.discrimination, body.guessing)
                if warns:
                    try:
                        warning_text = "; ".join(warns)
                        response.headers["Warning"] = warning_text
                        response.headers["X-Warning"] = warning_text
                    except Exception:
                        pass
            # Also set ETag of created resource
            if response is not None:
                try:
                    etag = _compute_etag(row)
                    if etag:
                        response.headers["ETag"] = etag
                except Exception:
                    pass
            # Store idempotency record after success
            if idem_key:
                try:
                    headers_subset = {k: response.headers.get(k) for k in ("ETag", "Warning", "X-Warning", "Content-Type")}
                except Exception:
                    headers_subset = None
                try:
                    user_id_str = getattr(current_user, "user_id", None)
                    org_id_attr = getattr(current_user, "org_id", None)
                    try:
                        org_id_val = int(org_id_attr) if org_id_attr is not None else None
                    except Exception:
                        org_id_val = None
                    idem_svc.store_result(
                        s,
                        method="POST",
                        path=str(request.url.path if request else f"{settings.API_PREFIX}/questions"),
                        user_id=user_id_str,
                        org_id=org_id_val,
                        idem_key=str(idem_key),
                        req_hash=idem_svc.compute_request_hash(body),
                        status_code=201,
                        body=q.model_dump() if hasattr(q, "model_dump") else q,
                        headers=headers_subset,
                    )
                except Exception:
                    pass
            return q
    with _LOCK:
        qid = str(uuid.uuid4())
        now = _now()
        # In-memory Idempotency replay
        idem_key = None
        try:
            idem_key = request.headers.get("Idempotency-Key") if request else None
        except Exception:
            idem_key = None
        if idem_key:
            existing = idem_svc.find_existing(
                None,
                method="POST",
                path=f"{settings.API_PREFIX}/questions",
                user_id=getattr(current_user, "user_id", None),
                org_id=(
                    (lambda _val: (int(_val) if _val is not None else None))(
                        getattr(current_user, "org_id", None)
                    )
                ),
                idem_key=str(idem_key),
            )
            if existing:
                req_hash_existing, stored = existing
                new_hash = idem_svc.compute_request_hash(body)
                if req_hash_existing and new_hash != req_hash_existing:
                    raise HTTPException(409, "idempotency_key_conflict")
                if stored.headers_json:
                    try:
                        for k, v in stored.headers_json.items():
                            if v is not None:
                                response.headers[str(k)] = str(v)
                    except Exception:
                        pass
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=stored.status_code, content=stored.body_json)
        # In-memory org logic mirrors DB path
        if current_user.is_teacher():
            if current_user.org_id is None:
                raise HTTPException(403, "missing_org")
            if body.org_id is not None and int(body.org_id) != int(current_user.org_id):
                raise HTTPException(403, "forbidden_org_override")
            org_val = int(current_user.org_id)
        elif current_user.is_admin():
            org_val = int(body.org_id) if body.org_id is not None else None
        else:
            raise HTTPException(403, "forbidden")
        q = Question(
            org_id=org_val,
            id=qid,
            title=body.title,
            stem=body.stem,
            explanation=body.explanation,
            options=body.options,
            answer=int(body.answer),
            difficulty=body.difficulty,
            topic=body.topic,
            tags=list(body.tags or []),
            status=body.status,
            author=current_user.user_id,
            created_by=current_user.user_id,
            updated_by=current_user.user_id,
            discrimination=body.discrimination,
            guessing=body.guessing,
            created_at=now,
            updated_at=now,
        )
        _STORE[qid] = q
        # ETag + store idempotent result
        try:
            ms = int(float(q.updated_at or now) * 1000)
            response.headers["ETag"] = f'W/"q:{qid}:{ms}"'
        except Exception:
            pass
        # Attach soft warnings for out-of-range IRT values (not validation errors)
        if response is not None:
            warns = _irt_recommended_warnings(body.discrimination, body.guessing)
            if warns:
                try:
                    response.headers["Warning"] = "; ".join(warns)
                    response.headers["X-Warning"] = "; ".join(warns)
                except Exception:
                    pass
        if idem_key:
            try:
                headers_subset = {k: response.headers.get(k) for k in ("ETag", "Warning", "X-Warning", "Content-Type")}
            except Exception:
                headers_subset = None
            try:
                # Normalize org context for idempotency scope
                _user_id_str = getattr(current_user, "user_id", None)
                _org_attr = getattr(current_user, "org_id", None)
                try:
                    _org_val = int(_org_attr) if _org_attr is not None else None
                except Exception:
                    _org_val = None
                idem_svc.store_result(
                    None,
                    method="POST",
                    path=f"{settings.API_PREFIX}/questions",
                    user_id=_user_id_str,
                    org_id=_org_val,
                    idem_key=str(idem_key),
                    req_hash=idem_svc.compute_request_hash(body),
                    status_code=201,
                    body=q.model_dump() if hasattr(q, "model_dump") else q,
                    headers=headers_subset,
                )
            except Exception:
                pass
        return q


@router.put(
    "/questions/{question_id}",
    summary="Update a question",
    response_model=Question,
)
def update_question(
    question_id: str, body: QuestionInput, response: Response, request: Request, current_user: User = Depends(get_current_user)
) -> Any:
    _require_teacher_or_admin(current_user)
    if body.answer >= len(body.options):
        raise HTTPException(400, "answer_out_of_range")
    if _db_enabled():
        with db_service.get_session() as s:
            # Idempotency: check existing stored result
            idem_key = None
            try:
                idem_key = request.headers.get("Idempotency-Key") if request else None
            except Exception:
                idem_key = None
            if idem_key:
                user_id_str = getattr(current_user, "user_id", None)
                org_id_attr = getattr(current_user, "org_id", None)
                try:
                    org_id_val = int(org_id_attr) if org_id_attr is not None else None
                except Exception:
                    org_id_val = None
                existing = idem_svc.find_existing(
                    s,
                    method="PUT",
                    path=str(request.url.path if request else f"{settings.API_PREFIX}/questions/{question_id}"),
                    user_id=user_id_str,
                    org_id=org_id_val,
                    idem_key=str(idem_key),
                )
                if existing:
                    req_hash_existing, stored = existing
                    new_hash = idem_svc.compute_request_hash(body)
                    if req_hash_existing and new_hash != req_hash_existing:
                        raise HTTPException(409, "idempotency_key_conflict")
                    if response is not None and stored.headers_json:
                        try:
                            for k, v in stored.headers_json.items():
                                if v is not None:
                                    response.headers[str(k)] = str(v)
                        except Exception:
                            pass
                    from fastapi.responses import JSONResponse
                    return JSONResponse(status_code=stored.status_code, content=stored.body_json)

            row = s.get(QuestionRow, question_id)
            if row is None:
                raise HTTPException(404, "not_found")
            # ETag precondition
            current_etag = None
            try:
                current_etag = _compute_etag(row)
                if response is not None and current_etag:
                    response.headers["ETag"] = current_etag
            except Exception:
                current_etag = None
            if_match = None
            try:
                if_match = request.headers.get("If-Match") if request else None
            except Exception:
                if_match = None
            # Check environment variable directly to support dynamic test configuration
            import os
            require_precondition = os.environ.get("REQUIRE_IF_MATCH_PRECONDITION", "").lower() in ("true", "1", "yes") or getattr(settings, "REQUIRE_IF_MATCH_PRECONDITION", False)
            if require_precondition and not if_match:
                raise HTTPException(428, "precondition_required")
            if if_match and current_etag and not _etag_matches(if_match, current_etag):
                raise HTTPException(412, "etag_mismatch")
            _ensure_teacher_can_write(current_user, row)
            # Enforce admin global edit policy: block if global and flag is False
            if current_user.is_admin() and getattr(row, "org_id", None) is None and not settings.PLATFORM_GLOBAL_EDITABLE:
                raise HTTPException(403, "forbidden_global")
            # Resolve topic from topic_id if provided
            topic_name: str | None = body.topic
            topic_id_val: int | None = None
            if body.topic_id is not None and getattr(settings, "USE_TOPICS_TABLE", False):
                try:
                    from ..models.topic import TopicRow  # local import
                    tr = s.get(TopicRow, int(body.topic_id))
                    if tr is None:
                        raise HTTPException(422, "invalid_topic_id")
                    if current_user.is_teacher():
                        if current_user.org_id is None:
                            raise HTTPException(403, "missing_org")
                        t_org = getattr(tr, "org_id", None)
                        if t_org is not None and int(t_org) != int(current_user.org_id):
                            raise HTTPException(403, "forbidden_org_topic")
                    topic_name = getattr(tr, "name", None) or topic_name
                    topic_id_val = int(getattr(tr, "id"))
                except HTTPException:
                    raise
                except Exception:
                    pass

            setattr(row, "title", body.title)
            setattr(row, "stem", body.stem)
            setattr(row, "explanation", body.explanation)
            setattr(row, "options", list(body.options or []))
            setattr(row, "answer", int(body.answer))
            setattr(row, "difficulty", body.difficulty)
            setattr(row, "topic", topic_name)
            setattr(row, "topic_id", topic_id_val)
            # Tags persistence is disabled here to avoid type mismatches across DBs
            # (jsonb vs text[]). API responses normalize None -> [].
            setattr(row, "status", body.status)
            setattr(row, "discrimination", body.discrimination)
            setattr(row, "guessing", body.guessing)
            if not getattr(row, "author"):
                setattr(row, "author", current_user.user_id)
            # Always update audit trail's updated_by
            try:
                setattr(row, "updated_by", current_user.user_id)
            except Exception:
                pass
            s.flush()
            # If configured, replace choices rows to match incoming options/answer
            if getattr(settings, "USE_CHOICES_TABLE", False):
                try:
                    write_choices_from_options(s.connection(), question_id, list(body.options or []), int(body.answer))
                except Exception:
                    pass
            s.refresh(row)
            q = _row_to_question(row)
            if getattr(settings, "USE_CHOICES_TABLE", False):
                try:
                    res = read_options_answer(s.connection(), question_id)
                    if res is not None:
                        opts, ans = res
                        q.options = opts
                        if ans >= 0:
                            q.answer = ans
                except Exception:
                    pass
            if response is not None:
                warns = _irt_recommended_warnings(body.discrimination, body.guessing)
                if warns:
                    try:
                        response.headers["Warning"] = "; ".join(warns)
                        response.headers["X-Warning"] = "; ".join(warns)
                    except Exception:
                        pass
                # Set new ETag after update
                try:
                    new_etag = _compute_etag(row)
                    if new_etag:
                        response.headers["ETag"] = new_etag
                except Exception:
                    pass
            # Store idempotency record
            if idem_key:
                try:
                    headers_subset = {k: response.headers.get(k) for k in ("ETag", "Warning", "X-Warning", "Content-Type")}
                except Exception:
                    headers_subset = None
                try:
                    user_id_str = getattr(current_user, "user_id", None)
                    org_id_attr = getattr(current_user, "org_id", None)
                    try:
                        org_id_val = int(org_id_attr) if org_id_attr is not None else None
                    except Exception:
                        org_id_val = None
                    idem_svc.store_result(
                        s,
                        method="PUT",
                        path=str(request.url.path if request else f"{settings.API_PREFIX}/questions/{question_id}"),
                        user_id=user_id_str,
                        org_id=org_id_val,
                        idem_key=str(idem_key),
                        req_hash=idem_svc.compute_request_hash(body),
                        status_code=200,
                        body=q.model_dump() if hasattr(q, "model_dump") else q,
                        headers=headers_subset,
                    )
                except Exception:
                    pass
            return q
    with _LOCK:
        old = _STORE.get(question_id)
        if not old:
            raise HTTPException(404, "not_found")
        # In-memory ETag precondition
        try:
            if_match = request.headers.get("If-Match") if request else None
        except Exception:
            if_match = None
        try:
            cur_ms = int(float(old.updated_at or 0.0) * 1000)
            current_etag = f'W/"q:{old.id}:{cur_ms}"'
        except Exception:
            current_etag = None
        # Check environment variable directly to support dynamic test configuration
        import os
        require_precondition = os.environ.get("REQUIRE_IF_MATCH_PRECONDITION", "").lower() in ("true", "1", "yes") or getattr(settings, "REQUIRE_IF_MATCH_PRECONDITION", False)
        if require_precondition and not if_match:
            raise HTTPException(428, "precondition_required")
        if if_match and current_etag:
            def _norm(x: str) -> str:
                x = x.strip()
                return x[2:] if x.startswith("W/") else x
            if _norm(if_match) != _norm(current_etag):
                raise HTTPException(412, "etag_mismatch")
        # In-memory Idempotency replay
        idem_key = None
        try:
            idem_key = request.headers.get("Idempotency-Key") if request else None
        except Exception:
            idem_key = None
        if idem_key:
            existing = idem_svc.find_existing(
                None,
                method="PUT",
                path=f"{settings.API_PREFIX}/questions/{question_id}",
                user_id=getattr(current_user, "user_id", None),
                org_id=(
                    (lambda _val: (int(_val) if _val is not None else None))(
                        getattr(current_user, "org_id", None)
                    )
                ),
                idem_key=str(idem_key),
            )
            if existing:
                req_hash_existing, stored = existing
                new_hash = idem_svc.compute_request_hash(body)
                if req_hash_existing and new_hash != req_hash_existing:
                    raise HTTPException(409, "idempotency_key_conflict")
                if stored.headers_json:
                    try:
                        for k, v in stored.headers_json.items():
                            if v is not None:
                                response.headers[str(k)] = str(v)
                    except Exception:
                        pass
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=stored.status_code, content=stored.body_json)
        # Enforce write permissions in-memory
        if current_user.is_teacher():
            if old.org_id is None:
                # Allow teacher to edit global only if they authored/created it
                if not ( (old.created_by and str(old.created_by) == str(current_user.user_id)) or (old.author and str(old.author) == str(current_user.user_id)) ):
                    raise HTTPException(403, "forbidden_global")
            if current_user.org_id is None or (old.org_id is not None and int(current_user.org_id) != int(old.org_id)):
                raise HTTPException(403, "forbidden_org")
        elif current_user.is_admin():
            if old.org_id is None and not settings.PLATFORM_GLOBAL_EDITABLE:
                raise HTTPException(403, "forbidden_global")
        now = _now()
        q = Question(
            org_id=old.org_id,
            id=old.id,
            title=body.title,
            stem=body.stem,
            explanation=body.explanation,
            options=body.options,
            answer=int(body.answer),
            difficulty=body.difficulty,
            topic=body.topic,
            tags=list(body.tags or []),
            status=body.status,
            author=old.author or current_user.user_id,
            created_by=old.created_by or old.author or current_user.user_id,
            updated_by=current_user.user_id,
            discrimination=body.discrimination,
            guessing=body.guessing,
            created_at=old.created_at or now,
            updated_at=now,
        )
        _STORE[question_id] = q
        # Set ETag and store idempotent result
        try:
            ms = int(float(q.updated_at or now) * 1000)
            response.headers["ETag"] = f'W/"q:{q.id}:{ms}"'
        except Exception:
            pass
        # Attach soft warnings for out-of-range IRT values (not validation errors)
        if response is not None:
            warns = _irt_recommended_warnings(body.discrimination, body.guessing)
            if warns:
                try:
                    response.headers["Warning"] = "; ".join(warns)
                    response.headers["X-Warning"] = "; ".join(warns)
                except Exception:
                    pass
        if idem_key:
            try:
                headers_subset = {k: response.headers.get(k) for k in ("ETag", "Warning", "X-Warning", "Content-Type")}
            except Exception:
                headers_subset = None
            try:
                # Normalize org context for idempotency scope
                _user_id_str = getattr(current_user, "user_id", None)
                _org_attr = getattr(current_user, "org_id", None)
                try:
                    _org_val = int(_org_attr) if _org_attr is not None else None
                except Exception:
                    _org_val = None
                idem_svc.store_result(
                    None,
                    method="PUT",
                    path=f"{settings.API_PREFIX}/questions/{question_id}",
                    user_id=_user_id_str,
                    org_id=_org_val,
                    idem_key=str(idem_key),
                    req_hash=idem_svc.compute_request_hash(body),
                    status_code=200,
                    body=q.model_dump() if hasattr(q, "model_dump") else q,
                    headers=headers_subset,
                )
            except Exception:
                pass
        return q


@router.delete(
    "/questions/{question_id}",
    summary="Delete a question",
    response_model=OkResponse,
)
def delete_question(question_id: str, request: Request, current_user: User = Depends(get_current_user)) -> Any:
    _require_teacher_or_admin(current_user)
    if _db_enabled():
        with db_service.get_session() as s:
            # Pre-fetch for ETag
            row_pre = s.get(QuestionRow, question_id)
            if row_pre is None:
                raise HTTPException(404, "not_found")
            # ETag precondition
            current_etag = None
            try:
                current_etag = _compute_etag(row_pre)
            except Exception:
                current_etag = None
            try:
                if_match = request.headers.get("If-Match") if request else None
            except Exception:
                if_match = None
            if settings.REQUIRE_IF_MATCH_PRECONDITION and not if_match:
                raise HTTPException(428, "precondition_required")
            if if_match and current_etag and not _etag_matches(if_match, current_etag):
                raise HTTPException(412, "etag_mismatch")
            # Optional deletion restriction if question has responses
            if getattr(settings, "ENFORCE_DELETE_RESTRICT_ON_RESPONSES", False):
                try:
                    bind = s.get_bind()
                    dialect = getattr(bind, "dialect", None)
                    dname = getattr(dialect, "name", "") if dialect else ""
                    if dname == "postgresql":
                        from sqlalchemy import text as _text
                        res = s.execute(
                            _text(
                                """
                                SELECT 1
                                FROM exam_results
                                WHERE EXISTS (
                                  SELECT 1
                                  FROM jsonb_array_elements(result_json->'responses') AS r
                                  WHERE (r->>'question_id') = :qid
                                )
                                LIMIT 1
                                """
                            ),
                            {"qid": str(question_id)},
                        ).first()
                        if res is not None:
                            raise HTTPException(409, "question_has_responses")
                    # For non-Postgres or when JSON ops unavailable, skip strict check
                except HTTPException:
                    raise
                except Exception:
                    # Best-effort only; continue if check fails
                    pass
            row = row_pre
            _ensure_teacher_can_write(current_user, row)
            # Admin global edit policy
            if current_user.is_admin() and getattr(row, "org_id", None) is None and not settings.PLATFORM_GLOBAL_EDITABLE:
                raise HTTPException(403, "forbidden_global")
            setattr(row, "status", "deleted")
            try:
                setattr(row, "updated_by", current_user.user_id)
            except Exception:
                pass
            s.flush()
            # Idempotency for DELETE: record success and replay if seen again
            idem_key = None
            try:
                idem_key = request.headers.get("Idempotency-Key") if request else None
            except Exception:
                idem_key = None
            if idem_key:
                user_id_str = getattr(current_user, "user_id", None)
                org_id_attr = getattr(current_user, "org_id", None)
                try:
                    org_id_val = int(org_id_attr) if org_id_attr is not None else None
                except Exception:
                    org_id_val = None
                existing = idem_svc.find_existing(
                    s,
                    method="DELETE",
                    path=str(request.url.path if request else f"{settings.API_PREFIX}/questions/{question_id}"),
                    user_id=user_id_str,
                    org_id=org_id_val,
                    idem_key=str(idem_key),
                )
                if existing:
                    from fastapi.responses import JSONResponse
                    _req_hash, stored = existing
                    return JSONResponse(status_code=stored.status_code, content=stored.body_json)
                try:
                    idem_svc.store_result(
                        s,
                        method="DELETE",
                        path=str(request.url.path if request else f"{settings.API_PREFIX}/questions/{question_id}"),
                        user_id=user_id_str,
                        org_id=org_id_val,
                        idem_key=str(idem_key),
                        req_hash="",
                        status_code=200,
                        body={"ok": True},
                        headers=None,
                    )
                except Exception:
                    pass
            # Invalidate topics cache after delete
            try:
                cache = get_cache()
                cache.delete_prefix("topics:")
            except Exception:
                pass
            return {"ok": True}
    with _LOCK:
        if question_id in _STORE:
            q = _STORE[question_id]
            # ETag precondition
            try:
                if_match = request.headers.get("If-Match") if request else None
            except Exception:
                if_match = None
            try:
                cur_ms = int(float(q.updated_at or 0.0) * 1000)
                current_etag = f'W/"q:{q.id}:{cur_ms}"'
            except Exception:
                current_etag = None
            # Check environment variable directly to support dynamic test configuration
            import os
            require_precondition = os.environ.get("REQUIRE_IF_MATCH_PRECONDITION", "").lower() in ("true", "1", "yes") or getattr(settings, "REQUIRE_IF_MATCH_PRECONDITION", False)
            if require_precondition and not if_match:
                raise HTTPException(428, "precondition_required")
            if if_match and current_etag:
                def _norm(x: str) -> str:
                    x = x.strip()
                    return x[2:] if x.startswith("W/") else x
                if _norm(if_match) != _norm(current_etag):
                    raise HTTPException(412, "etag_mismatch")
            # Idempotency replay
            idem_key = None
            try:
                idem_key = request.headers.get("Idempotency-Key") if request else None
            except Exception:
                idem_key = None
            if idem_key:
                existing = idem_svc.find_existing(
                    None,
                    method="DELETE",
                    path=f"{settings.API_PREFIX}/questions/{question_id}",
                    user_id=getattr(current_user, "user_id", None),
                    org_id=(
                        (lambda _val: (int(_val) if _val is not None else None))(
                            getattr(current_user, "org_id", None)
                        )
                    ),
                    idem_key=str(idem_key),
                )
                if existing:
                    from fastapi.responses import JSONResponse
                    _req_hash, stored = existing
                    return JSONResponse(status_code=stored.status_code, content=stored.body_json)
            if current_user.is_teacher():
                if q.org_id is None:
                    # Allow delete for global only if authored by teacher
                    if not ( (q.created_by and str(q.created_by) == str(current_user.user_id)) or (q.author and str(q.author) == str(current_user.user_id)) ):
                        raise HTTPException(403, "forbidden_global")
                if current_user.org_id is None or (q.org_id is not None and int(current_user.org_id) != int(q.org_id)):
                    raise HTTPException(403, "forbidden_org")
            elif current_user.is_admin():
                if q.org_id is None and not settings.PLATFORM_GLOBAL_EDITABLE:
                    raise HTTPException(403, "forbidden_global")
            now = _now()
            _STORE[question_id] = q.model_copy(update={"status": "deleted", "updated_at": now})
            # Store idempotent success
            if idem_key:
                try:
                    # Normalize org context for idempotency scope
                    _user_id_str = getattr(current_user, "user_id", None)
                    _org_attr = getattr(current_user, "org_id", None)
                    try:
                        _org_val = int(_org_attr) if _org_attr is not None else None
                    except Exception:
                        _org_val = None
                    idem_svc.store_result(
                        None,
                        method="DELETE",
                        path=f"{settings.API_PREFIX}/questions/{question_id}",
                        user_id=_user_id_str,
                        org_id=_org_val,
                        idem_key=str(idem_key),
                        req_hash="",
                        status_code=200,
                        body={"ok": True},
                        headers=None,
                    )
                except Exception:
                    pass
            # Invalidate topics cache after delete
            try:
                cache = get_cache()
                cache.delete_prefix("topics:")
            except Exception:
                pass
            return {"ok": True}
        raise HTTPException(404, "not_found")


@router.get(
    "/topics",
    summary="List topics (alias endpoint)",
    response_model=list[str],
)
def list_topics_alias(
    subject: str | None = Query(default=None),
    org_id: int | None = Query(default=None, description="Admin-only: scope to an org's topics"),
    include_global: bool = Query(default=True, description="Include global topics when org_id is provided (admin only)"),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Alias for topics listing to support /api/seedtest/topics as specified in OpenAPI.

    - Optional subject parameter currently ignored (no subjects table); kept for forward compatibility.
    """
    _require_teacher_or_admin(current_user)
    cache = get_cache()
    ttl = getattr(settings, "TOPICS_CACHE_TTL_SECS", 300) or 300

    use_table = getattr(settings, "USE_TOPICS_TABLE", False)
    role_key = "admin" if current_user.is_admin() else "teacher"
    key = f"topics_alias:{'table' if use_table else 'legacy'}:{role_key}:org={org_id}:glob={int(bool(include_global))}"

    def _fetch() -> list[str]:
        if _db_enabled():
            try:
                with db_service.get_session() as s:
                    if use_table:
                        # Topics from topics table with scoping
                        if current_user.is_teacher():
                            if current_user.org_id is None:
                                raise HTTPException(403, "missing_org")
                            stmt = select(TopicRow.name).where(
                                or_(TopicRow.org_id.is_(None), TopicRow.org_id == int(current_user.org_id))
                            )
                        else:
                            # Admin path
                            if org_id is None:
                                # Default: global only
                                stmt = select(TopicRow.name).where(TopicRow.org_id.is_(None))
                            else:
                                if include_global:
                                    stmt = select(TopicRow.name).where(
                                        or_(TopicRow.org_id.is_(None), TopicRow.org_id == int(org_id))
                                    )
                                else:
                                    stmt = select(TopicRow.name).where(TopicRow.org_id == int(org_id))
                        rows = s.execute(stmt).all()
                        vals: set[str] = set()
                        for (name,) in rows:
                            if name and isinstance(name, str) and name.strip():
                                vals.add(name.strip())
                        return sorted(vals)
                    else:
                        # Legacy path: distinct topics from questions table with optional org filtering
                        where = [QuestionRow.status != "deleted", QuestionRow.topic.is_not(None)]
                        if current_user.is_teacher():
                            if current_user.org_id is None:
                                raise HTTPException(403, "missing_org")
                            where.append(or_(QuestionRow.org_id.is_(None), QuestionRow.org_id == int(current_user.org_id)))
                        else:
                            if org_id is None:
                                # Global only
                                where.append(QuestionRow.org_id.is_(None))
                            else:
                                if include_global:
                                    where.append(or_(QuestionRow.org_id.is_(None), QuestionRow.org_id == int(org_id)))
                                else:
                                    where.append(QuestionRow.org_id == int(org_id))
                        rows = s.execute(select(QuestionRow.topic).where(and_(*where))).all()
                        vals: set[str] = set()
                        for (t,) in rows:
                            if t and isinstance(t, str) and t.strip():
                                vals.add(t.strip())
                        return sorted(vals)
            except Exception:
                # On DB errors (e.g., unmigrated schema), fall through to in-memory fallback
                pass
        # In-memory fallback
        _seed_if_empty()
        with _LOCK:
            topics: set[str] = set()
            for q in _STORE.values():
                if q.status == "deleted":
                    continue
                t = (q.topic or "").strip()
                if t:
                    topics.add(t)
            return sorted(topics)

    return cache.cached_get_set(key, ttl, _fetch)


@router.post(
    "/topics",
    summary="Create a topic (admin)",
    response_model=OkResponse,
)
def create_topic(body: TopicCreate, current_user: User = Depends(get_current_user)) -> Any:
    _require_admin(current_user)
    if not _db_enabled():
        raise HTTPException(503, "db_required")
    from ..models.topic import TopicRow
    with db_service.get_session() as s:
        # Basic uniqueness check (DB also enforces via indexes on Postgres)
        try:
            tr = TopicRow(name=body.name.strip(), org_id=body.org_id, parent_topic_id=body.parent_topic_id)
            s.add(tr)
            s.flush()
            s.refresh(tr)
            # Invalidate topics caches
            cache = get_cache()
            cache.delete_prefix("topics:")
            cache.delete_prefix("topics_alias:")
            return {"id": int(getattr(tr, "id")), "name": getattr(tr, "name"), "org_id": getattr(tr, "org_id", None), "parent_topic_id": getattr(tr, "parent_topic_id", None)}
        except Exception:
            raise HTTPException(409, "topic_conflict")


@router.put(
    "/topics/{topic_id}",
    summary="Update a topic (admin)",
    response_model=OkResponse,
)
def update_topic(topic_id: int, body: TopicUpdate, current_user: User = Depends(get_current_user)) -> Any:
    _require_admin(current_user)
    if not _db_enabled():
        raise HTTPException(503, "db_required")
    from ..models.topic import TopicRow
    with db_service.get_session() as s:
        tr = s.get(TopicRow, int(topic_id))
        if tr is None:
            raise HTTPException(404, "not_found")
        try:
            if body.name is not None:
                setattr(tr, "name", body.name.strip())
            if body.parent_topic_id is not None:
                setattr(tr, "parent_topic_id", int(body.parent_topic_id))
            s.flush()
            s.refresh(tr)
            cache = get_cache()
            cache.delete_prefix("topics:")
            cache.delete_prefix("topics_alias:")
            return {"id": int(getattr(tr, "id")), "name": getattr(tr, "name"), "org_id": getattr(tr, "org_id", None), "parent_topic_id": getattr(tr, "parent_topic_id", None)}
        except Exception:
            raise HTTPException(409, "topic_conflict")


@router.delete(
    "/topics/{topic_id}",
    summary="Delete a topic (admin)",
    response_model=dict,
)
def delete_topic(topic_id: int, current_user: User = Depends(get_current_user)) -> Any:
    _require_admin(current_user)
    if not _db_enabled():
        raise HTTPException(503, "db_required")
    from ..models.topic import TopicRow
    with db_service.get_session() as s:
        tr = s.get(TopicRow, int(topic_id))
        if tr is None:
            raise HTTPException(404, "not_found")
        # Capture before delete for response
        deleted_obj = {
            "id": int(getattr(tr, "id")),
            "name": getattr(tr, "name"),
            "org_id": getattr(tr, "org_id", None),
            "parent_topic_id": getattr(tr, "parent_topic_id", None),
        }
        # Check usage in questions
        used = s.execute(select(func.count()).select_from(QuestionRow).where(QuestionRow.topic_id == int(topic_id))).scalar_one()
        if int(used or 0) > 0:
            raise HTTPException(409, "topic_in_use_merge_required")
        s.delete(tr)
        s.flush()
        cache = get_cache()
        cache.delete_prefix("topics:")
        cache.delete_prefix("topics_alias:")
        return {"message": "Topic deleted", "deleted_id": int(topic_id), "deleted": deleted_obj}


@router.post(
    "/topics/{topic_id}/merge",
    summary="Merge a topic into another (admin)",
    response_model=dict,
)
def merge_topic(topic_id: int, body: TopicMerge, current_user: User = Depends(get_current_user)) -> Any:
    _require_admin(current_user)
    if not _db_enabled():
        raise HTTPException(503, "db_required")
    if int(topic_id) == int(body.target_id):
        raise HTTPException(422, "same_topic")
    from ..models.topic import TopicRow
    with db_service.get_session() as s:
        src = s.get(TopicRow, int(topic_id))
        dst = s.get(TopicRow, int(body.target_id))
        if src is None or dst is None:
            raise HTTPException(404, "not_found")
        # Update questions to point to target topic_id and normalize topic name to target
        dst_name = getattr(dst, "name")
        src_obj = {
            "id": int(getattr(src, "id")),
            "name": getattr(src, "name"),
            "org_id": getattr(src, "org_id", None),
            "parent_topic_id": getattr(src, "parent_topic_id", None),
        }
        dst_obj = {
            "id": int(getattr(dst, "id")),
            "name": getattr(dst, "name"),
            "org_id": getattr(dst, "org_id", None),
            "parent_topic_id": getattr(dst, "parent_topic_id", None),
        }
        s.execute(
            select(QuestionRow).where(QuestionRow.topic_id == int(topic_id))
        )  # No-op to ensure table present; real update below
        try:
            # Bulk updates
            from sqlalchemy import update as _update
            res = s.execute(
                _update(QuestionRow)
                .where(QuestionRow.topic_id == int(topic_id))
                .values(topic_id=int(body.target_id), topic=dst_name)
            )
            updated_count = getattr(res, "rowcount", None)
            # Optionally also fix legacy name-only questions that match the source name
            src_name = getattr(src, "name")
            if src_name and dst_name and src_name != dst_name:
                s.execute(
                    _update(QuestionRow)
                    .where(QuestionRow.topic_id.is_(None))
                    .where(QuestionRow.topic == src_name)
                    .values(topic=dst_name)
                )
            # Delete source topic
            s.delete(src)
            s.flush()
            cache = get_cache()
            cache.delete_prefix("topics:")
            cache.delete_prefix("topics_alias:")
            return {
                "message": "Merged",
                "from": src_obj,
                "to": dst_obj,
                "updated_questions": int(updated_count) if updated_count is not None else None,
            }
        except Exception:
            raise HTTPException(409, "merge_conflict")


@router.post(
    "/topics/cache/invalidate",
    summary="Invalidate topics cache (admin)",
    response_model=dict,
)
def invalidate_topics_cache(current_user: User = Depends(get_current_user)) -> Any:
    _require_admin(current_user)
    cache = get_cache()
    c1 = cache.delete_prefix("topics:")
    c2 = cache.delete_prefix("topics_alias:")
    return {"message": "Cache invalidated", "deleted_keys": c1 + c2}


# --- Cursor helpers (opaque) ---
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
    return "v1:" + _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def _decode_cursor(token: str) -> tuple[str, str]:
    if not token or not isinstance(token, str):
        raise ValueError("bad token")
    if token.startswith("v1:"):
        raw = _b64url_decode(token[3:])
        import json
        obj = json.loads(raw.decode("utf-8"))
        ts = obj.get("ts")
        cid = obj.get("id")
        if isinstance(ts, str) and isinstance(cid, (str, int)):
            return ts, str(cid)
    raise ValueError("bad token")


# --- ETag helpers ---
def _compute_etag(row: QuestionRow) -> str | None:
    try:
        import datetime as _dt
        uid = str(getattr(row, "id"))
        ts = getattr(row, "updated_at", None)
        if ts is None:
            return None
        if isinstance(ts, (int, float)):
            ms = int(float(ts) * 1000)
        else:
            ms = int(ts.timestamp() * 1000)
        return f'W/"q:{uid}:{ms}"'
    except Exception:
        return None


def _etag_matches(if_match_val: str, current_etag: str) -> bool:
    try:
        val = if_match_val.strip()
        if val == "*":
            return True
        def norm(x: str) -> str:
            x = x.strip()
            return x[2:] if x.startswith("W/") else x
        return norm(val) == norm(current_etag)
    except Exception:
        return False
