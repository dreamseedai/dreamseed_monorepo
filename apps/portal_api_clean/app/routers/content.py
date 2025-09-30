from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Content, ContentAuditLog
from app.schemas.content import ContentIn, ContentOut
from typing import List, Optional
from sqlalchemy import func, or_, cast, Text
import asyncio
from app.core.cache import get_or_set, delete_prefix
from app.core.config import get_settings
from app.deps import get_current_user_id, get_current_user, require_roles


router = APIRouter(prefix="/content", tags=["content"])


@router.get("/", response_model=List[ContentOut])
async def list_content(
    mine: bool = False,
    after_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    async def maker():
        query = db.query(Content).filter(Content.deleted_at.is_(None))
        if mine and getattr(user, "role", "user") != "admin":
            query = query.filter(Content.author_id == user.id)
        if after_id:
            query = query.filter(Content.id < after_id)
        if q:
            q_norm = q.strip().lower()
            if len(q_norm) <= 2:
                query = query.filter(func.lower(Content.title).like(q_norm + "%"))
            else:
                query = query.filter(
                    or_(
                        func.lower(Content.title).like("%" + q_norm + "%"),
                        func.lower(cast(Content.doc, Text)).like("%" + q_norm + "%"),
                    )
                )
        rows = query.order_by(Content.id.desc()).limit(limit).all()
        return rows

    return await get_or_set(
        "content:list",
        maker,
        ttl=get_settings().cache_ttl_seconds,
        mine=mine,
        after_id=after_id,
        limit=limit,
        user_id=(None if getattr(user, "role", "user") == "admin" else user.id),
        q=q or None,
    )


def _audit(db: Session, *, action: str, user_id: int | None, content_id: int | None, before: dict | None, after: dict | None, req: Request | None):
    ip = None
    ua = None
    if req:
        ip = req.headers.get("x-forwarded-for") or (getattr(getattr(req, "client", None), "host", None))
        ua = req.headers.get("user-agent")
    row = ContentAuditLog(
        content_id=content_id,
        user_id=user_id,
        action=action,
        before=before,
        after=after,
        ip=ip,
        user_agent=ua,
    )
    db.add(row)


@router.post("/", response_model=ContentOut)
async def create_content(payload: ContentIn, request: Request, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = Content(title=payload.title, doc=payload.doc, author_id=user_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    _audit(db, action="create", user_id=user_id, content_id=row.id, before=None, after={"title": row.title, "doc": row.doc}, req=request)
    db.commit()
    await delete_prefix("content:list")
    return row


@router.get("/{content_id}", response_model=ContentOut)
def get_content(content_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = db.get(Content, content_id)
    if not row or row.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Not found")
    return row


@router.put("/{content_id}", response_model=ContentOut)
async def update_content(content_id: int, payload: ContentIn, request: Request, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = db.get(Content, content_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    before = {"title": row.title, "doc": row.doc}
    row.title = payload.title
    row.doc = payload.doc
    db.commit()
    db.refresh(row)
    _audit(db, action="update", user_id=user_id, content_id=row.id, before=before, after={"title": row.title, "doc": row.doc}, req=request)
    db.commit()
    await delete_prefix("content:list")
    return row


@router.delete("/{content_id}")
async def delete_content(content_id: int, request: Request, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = db.get(Content, content_id)
    if not row or row.deleted_at is not None:
        return {"ok": True}
    before = {"title": row.title, "doc": row.doc}
    from datetime import datetime, timezone
    row.deleted_at = datetime.now(timezone.utc)
    db.commit()
    _audit(db, action="delete", user_id=user_id, content_id=content_id, before=before, after=None, req=request)
    db.commit()
    await delete_prefix("content:list")
    return {"ok": True}


@router.get("/audit")
def list_content_audit(
    content_id: int | None = None,
    user_id: int | None = None,
    action: str | None = Query(None, pattern="^(create|update|delete)$"),
    after_id: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    q = db.query(ContentAuditLog).order_by(ContentAuditLog.id.desc())
    if getattr(user, "role", "user") != "admin":
        q = q.filter(ContentAuditLog.user_id == user.id)
    if content_id:
        q = q.filter(ContentAuditLog.content_id == content_id)
    if user_id:
        if getattr(user, "role", "user") != "admin" and user_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
        q = q.filter(ContentAuditLog.user_id == user_id)
    if action:
        q = q.filter(ContentAuditLog.action == action)
    if after_id:
        q = q.filter(ContentAuditLog.id < after_id)
    rows = q.limit(limit).all()
    return [
        {
            "id": r.id,
            "content_id": r.content_id,
            "user_id": r.user_id,
            "action": r.action,
            "ip": r.ip,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/{content_id}/undelete")
async def undelete_content(
    content_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(require_roles("admin")),
):
    row = db.get(Content, content_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    if row.deleted_at is None:
        return {"ok": True, "message": "not deleted"}
    before = {"title": row.title, "doc": row.doc}
    row.deleted_at = None
    db.commit()
    db.refresh(row)
    _audit(db, action="undelete", user_id=user.id, content_id=row.id, before=before, after={"title": row.title, "doc": row.doc}, req=request)
    db.commit()
    await delete_prefix("content:list")
    return {"ok": True}


@router.delete("/{content_id}/hard")
async def hard_delete_content(
    content_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(require_roles("admin")),
):
    row = db.get(Content, content_id)
    if not row:
        return {"ok": True}
    before = {"title": row.title, "doc": row.doc}
    db.delete(row)
    db.commit()
    _audit(db, action="hard_delete", user_id=user.id, content_id=content_id, before=before, after=None, req=request)
    db.commit()
    await delete_prefix("content:list")
    return {"ok": True}
