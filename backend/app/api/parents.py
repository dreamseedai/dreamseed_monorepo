# backend/app/api/parents.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.models.user import User
from app.core.database import get_db
from app.schemas.students import ChildDetail, StudentDetail
from app.services.students import get_student_detail_for_teacher

router = APIRouter(prefix="/api/parents", tags=["parents"])


@router.get("/test/{parent_id}/children/{child_id}")
def get_child_detail_test(
    parent_id: int,
    child_id: int,
    db: Session = Depends(get_db),
):
    """[TEST] 자녀 상세 정보 조회 (인증 없음)"""
    detail = get_student_detail_for_teacher(db, parent_id, child_id)
    if not detail:
        raise HTTPException(404, "Student not found")
    return detail


@router.get("/{parent_id}/children/{child_id}")
def get_child_detail(
    parent_id: int,
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChildDetail:
    """부모용 자녀 상세 정보 조회 (Integer ID)"""
    if current_user.role not in ("parent", "admin"):
        raise HTTPException(403, "Forbidden")

    # "me" alias
    if parent_id == 0:
        parent_id = current_user.id

    detail = get_student_detail_for_teacher(db, parent_id, child_id)
    if not detail:
        raise HTTPException(404, "Child not found")

    return detail
