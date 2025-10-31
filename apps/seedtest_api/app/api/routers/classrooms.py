from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as OrmSession

from ....services.db import get_session as session_cm
from ....settings import settings
from ....security.jwt import require_scopes, same_org_guard
from ....models.classroom import Classroom
from ....schemas.classroom import ClassroomCreate, ClassroomOut

router = APIRouter(prefix=f"{settings.API_PREFIX}/classrooms", tags=["classrooms"]) 


def db_dep():
    with session_cm() as s:
        yield s


@router.get("/", response_model=list[ClassroomOut])
def list_classrooms(
    org_id: str = Query(..., description="Filter by organization id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: OrmSession = Depends(db_dep),
    user=Depends(require_scopes("exam:read")),
):
    # Enforce same-org for non-admins
    # Guard: must be same org unless admin
    same_org_guard(user, int(org_id))
    q = db.query(Classroom).filter(Classroom.org_id == org_id)
    return q.order_by(Classroom.created_at.desc()).offset(offset).limit(limit).all()


@router.post("/", response_model=ClassroomOut, status_code=201)
def create_classroom(
    payload: ClassroomCreate,
    db: OrmSession = Depends(db_dep),
    user=Depends(require_scopes("exam:write")),
):
    roles = set((user.get("roles") or [])) if isinstance(user, dict) else set()
    if not ("admin" in roles or "teacher" in roles):
        raise HTTPException(403, "forbidden_role")
    exists = (
        db.query(Classroom)
        .filter(Classroom.org_id == payload.org_id, Classroom.name == payload.name)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Classroom already exists in org")

    obj = Classroom(
        id=payload.id,
        org_id=payload.org_id,
        name=payload.name,
        grade=payload.grade,
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj
