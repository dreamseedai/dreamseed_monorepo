# backend/app/api/teachers.py
"""
Teacher API 라우터

엔드포인트:
- GET /api/teachers/{teacher_id}/students - 학생 목록
- GET /api/teachers/{teacher_id}/students/{student_id} - 학생 상세
"""

# backend/app/api/teachers.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.models.user import User
from app.core.database import get_db
from app.schemas.students import StudentSummary, StudentDetail
from app.services.students import (
    list_students_for_teacher,
    get_student_detail_for_teacher,
)

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


@router.get("/test/{teacher_id}/students")
def list_students_test(
    teacher_id: int,
    q: str | None = None,
    class_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """[TEST] 선생님의 학생 목록 조회 (인증 없음)"""
    items, total = list_students_for_teacher(
        db, teacher_id, q, class_id, status, page, page_size
    )

    return {
        "total_count": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/{teacher_id}/students")
def list_students(
    teacher_id: int,
    q: str | None = None,
    class_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """선생님의 학생 목록 조회 (Integer ID 기반)"""
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(403, "Forbidden")

    # "me" alias 지원
    if teacher_id == 0:
        teacher_id = current_user.id

    items, total = list_students_for_teacher(
        db, teacher_id, q, class_id, status, page, page_size
    )

    return {
        "total_count": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/{teacher_id}/students/{student_id}")
def get_student_detail(
    teacher_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentDetail:
    """학생 상세 정보 조회 (Integer ID)"""
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(403, "Forbidden")

    if teacher_id == 0:
        teacher_id = current_user.id

    detail = get_student_detail_for_teacher(db, teacher_id, student_id)
    if not detail:
        raise HTTPException(404, "Student not found")

    return detail
