from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as OrmSession

from ....models.session import Session as SessionModel
from ....schemas.sessions import SessionCreate, SessionOut
from ....security.jwt import require_scopes, same_org_guard
from ....services.db import get_session as session_cm
from ....settings import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}/sessions", tags=["sessions"])


def db_dep():
    """FastAPI-friendly DB session dependency using our contextmanager."""
    with session_cm() as s:
        yield s


@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: str,
    db: OrmSession = Depends(db_dep),
    user=Depends(require_scopes("exam:read")),
):
    roles = set((user.get("roles") or [])) if isinstance(user, dict) else set()
    obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Session not found")

    # Admins can access any session
    if "admin" in roles:
        return obj

    # Teachers must be in the same org as the session
    if "teacher" in roles:
        org_val = getattr(obj, "org_id", None)
        if org_val is None:
            # Defensively block if org is missing to avoid cross-org access
            raise HTTPException(403, "missing_org")
        same_org_guard(user, int(org_val))
        return obj

    # Students: must own the session and be in same org
    org_val = getattr(obj, "org_id", None)
    if org_val is None:
        raise HTTPException(403, "missing_org")
    same_org_guard(user, int(org_val))
    if obj.user_id != user.get("sub"):
        raise HTTPException(403, "forbidden_owner")
    return obj


@router.post("/", response_model=SessionOut, status_code=201)
def create_session(
    payload: SessionCreate,
    db: OrmSession = Depends(db_dep),
    user=Depends(require_scopes("exam:write")),
):
    roles = set((user.get("roles") or [])) if isinstance(user, dict) else set()

    # If session exists, return it idempotently
    exists = db.query(SessionModel).filter(SessionModel.id == payload.id).first()
    if exists:
        # Access control on existing session mirrors GET rules
        if "admin" in roles:
            return exists
        if "teacher" in roles:
            exists_org = getattr(exists, "org_id", None)
            if exists_org is None:
                raise HTTPException(403, "missing_org")
            same_org_guard(user, int(exists_org))
            return exists
        # student must own
        exists_org = getattr(exists, "org_id", None)
        if exists_org is None:
            raise HTTPException(403, "missing_org")
        same_org_guard(user, int(exists_org))
        if exists.user_id != user.get("sub"):
            raise HTTPException(403, "forbidden_owner")
        return exists

    # Determine effective ownership
    effective_user_id = payload.user_id
    effective_org_id = payload.org_id
    user_org_id = user.get("org_id")  # type: ignore

    if "admin" in roles:
        # Admin can set or omit; if omitted, default from caller
        effective_user_id = effective_user_id or user.get("sub")
        effective_org_id = effective_org_id or int(user_org_id or 0)
    elif "teacher" in roles:
        # Teacher must stay within their org; user_id optional
        teacher_org = int(user_org_id or 0)
        eff_org = effective_org_id if effective_org_id is not None else teacher_org
        same_org_guard(user, int(eff_org))
        effective_org_id = int(eff_org)
        effective_user_id = effective_user_id or user.get("sub")
    else:
        # Student: can only create for themselves within their org
        if effective_user_id and effective_user_id != user.get("sub"):
            raise HTTPException(403, "forbidden_owner")
        if effective_org_id and int(effective_org_id) != int(user_org_id or 0):
            raise HTTPException(403, "forbidden_org")
        effective_user_id = user.get("sub")
        effective_org_id = int(user_org_id or 0)

    obj = SessionModel(
        id=payload.id,
        classroom_id=payload.classroom_id,
        exam_id=payload.exam_id,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        status=payload.status,
        user_id=effective_user_id,
        org_id=effective_org_id,
    )
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj
