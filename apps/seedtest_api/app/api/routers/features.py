from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session as OrmSession

from ....services.db import get_session as session_cm
from ....settings import settings
from ....models.features_topic_daily import FeaturesTopicDaily
from ....schemas.features import FeaturesTopicDailyCreate, FeaturesTopicDailyOut
from ....security.jwt import require_scopes

router = APIRouter(prefix=f"{settings.API_PREFIX}/features", tags=["features"])


def db_dep():
    with session_cm() as s:
        yield s


@router.post("/daily", response_model=FeaturesTopicDailyOut, status_code=201)
def upsert_daily(
    payload: FeaturesTopicDailyCreate,
    db: OrmSession = Depends(db_dep),
    user=Depends(require_scopes("exam:write")),
):
    roles = set((user.get("roles") or [])) if isinstance(user, dict) else set()
    if not ("admin" in roles or "teacher" in roles):
        if str(user.get("sub")) != payload.user_id:
            raise HTTPException(403, "forbidden_user")
    obj = (
        db.query(FeaturesTopicDaily)
        .filter(
            FeaturesTopicDaily.user_id == payload.user_id,
            FeaturesTopicDaily.topic_id == payload.topic_id,
            FeaturesTopicDaily.date == payload.date,
        )
        .first()
    )
    if obj:
        # update fields if provided
        for field, value in payload.model_dump().items():
            setattr(obj, field, value)
    else:
        obj = FeaturesTopicDaily(**payload.model_dump())
        db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


@router.get("/daily", response_model=list[FeaturesTopicDailyOut])
def list_daily(
    user_id: str,
    topic_id: str | None = None,
    start: date | None = Query(None),
    end: date | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: OrmSession = Depends(db_dep),
    user=Depends(require_scopes("exam:read")),
):
    roles = set((user.get("roles") or [])) if isinstance(user, dict) else set()
    if not ("admin" in roles or "teacher" in roles):
        if str(user.get("sub")) != user_id:
            raise HTTPException(403, "forbidden_user")
    q = db.query(FeaturesTopicDaily).filter(FeaturesTopicDaily.user_id == user_id)
    if topic_id:
        q = q.filter(FeaturesTopicDaily.topic_id == topic_id)
    if start:
        q = q.filter(FeaturesTopicDaily.date >= start)
    if end:
        q = q.filter(FeaturesTopicDaily.date <= end)
    return q.order_by(FeaturesTopicDaily.date.desc()).limit(limit).all()
