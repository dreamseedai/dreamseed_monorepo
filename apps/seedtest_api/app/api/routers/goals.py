from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as OrmSession

from ....services.db import get_session as session_cm
from ....settings import settings
from ....models.interest_goal import InterestGoal
from ....schemas.interest_goal import InterestGoalCreate, InterestGoalOut
from ....security.jwt import require_scopes

router = APIRouter(prefix=f"{settings.API_PREFIX}/interest-goals", tags=["interest-goals"]) 


def db_dep():
    with session_cm() as s:
        yield s


@router.post("/", response_model=InterestGoalOut, status_code=201)
def upsert_goal(
    payload: InterestGoalCreate,
    db: OrmSession = Depends(db_dep),
    user=Depends(require_scopes("exam:write")),
):
    roles = set((user.get("roles") or [])) if isinstance(user, dict) else set()
    if not ("admin" in roles or "teacher" in roles):
        # Students can only upsert their own goals
        if str(user.get("sub")) != payload.user_id:
            raise HTTPException(403, "forbidden_user")
    obj = (
        db.query(InterestGoal)
        .filter(
            InterestGoal.user_id == payload.user_id,
            InterestGoal.topic_id == payload.topic_id,
        )
        .first()
    )
    if obj:
        obj.target_level = payload.target_level  # type: ignore[assignment]
        obj.priority = payload.priority  # type: ignore[assignment]
    else:
        obj = InterestGoal(**payload.model_dump())
        db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[InterestGoalOut])
def list_goals(
    user_id: str,
    db: OrmSession = Depends(db_dep),
    user=Depends(require_scopes("exam:read")),
):
    roles = set((user.get("roles") or [])) if isinstance(user, dict) else set()
    if not ("admin" in roles or "teacher" in roles):
        if str(user.get("sub")) != user_id:
            raise HTTPException(403, "forbidden_user")
    return db.query(InterestGoal).filter(InterestGoal.user_id == user_id).all()
