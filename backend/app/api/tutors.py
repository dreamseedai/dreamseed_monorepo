# backend/app/api/tutors.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.models.user import User
from app.core.database import get_db
from app.schemas.tutors import TutorSessionSummary, TutorSessionDetail
from app.services.tutors import list_sessions_for_tutor, get_session_detail

router = APIRouter(prefix="/api/tutors", tags=["tutors"])


@router.get("/test/{tutor_id}/sessions")
def list_sessions_test(
    tutor_id: int,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """[TEST] 튜터의 세션 목록 조회 (인증 없음)"""
    items, total = list_sessions_for_tutor(
        db, tutor_id, status, page, page_size
    )
    return {
        "total_count": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/{tutor_id}/sessions")
def list_sessions(
    tutor_id: int,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """튜터 세션 목록 조회 (Integer ID)"""
    if current_user.role not in ("tutor", "admin"):
        raise HTTPException(403, "Forbidden")

    if tutor_id == 0:
        tutor_id = current_user.id

    items, total = list_sessions_for_tutor(
        db, tutor_id, status, page, page_size
    )
    return {
        "total_count": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/{tutor_id}/sessions/{session_id}")
def session_detail(
    tutor_id: int,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TutorSessionDetail:
    """세션 상세 정보 조회 (Integer ID)"""
    if current_user.role not in ("tutor", "admin"):
        raise HTTPException(403, "Forbidden")

    if tutor_id == 0:
        tutor_id = current_user.id

    detail = get_session_detail(db, tutor_id, session_id)
    if not detail:
        raise HTTPException(404, "Session not found")

    return detail
