"""
Teacher portal API - Class management and student reports

Endpoints:
- GET /api/teacher/class-list: Get students in teacher's classes with ability data
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.security import get_current_school_teacher
from app.models.exam_models import IRTStudentAbility
from app.models.org_models import Organization, OrgMembership, StudentOrgEnrollment
from app.models.user import User
from app.schemas.teacher_schemas import TeacherClassListResponse, TeacherClassStudent
from app.services.ability_analytics import (
    assess_risk_level,
    classify_theta_band,
    compute_delta_theta,
)


# Type conversion helpers
def to_uuid(value: Any) -> UUID:
    """Convert Column[int] or int to UUID"""
    return UUID(int=int(value))


router = APIRouter(prefix="/api/teacher", tags=["teacher:class"])


@router.get("/class-list", response_model=TeacherClassListResponse)
async def get_teacher_class_list(
    subject: str = Query(..., description="Subject code (e.g., 'math', 'english')"),
    klass: Optional[str] = Query(None, description="Class label (e.g., '3-1', 'A반')"),
    window_days: int = Query(
        30, ge=1, le=90, description="Days to look back for ability data"
    ),
    db: AsyncSession = Depends(get_async_session),
    ctx: tuple[User, Organization, OrgMembership] = Depends(get_current_school_teacher),
):
    """
    Get list of students in teacher's classes with ability tracking data.

    Filters:
    - Organization: Teacher's school
    - Class (optional): Specific class label
    - Subject: Math, English, etc.
    - Time window: Recent ability measurements

    Returns:
    - Student list with θ, SE, band, risk level, delta θ (14d)
    """
    teacher, org, _ = ctx
    now = datetime.utcnow()
    since = now - timedelta(days=window_days)

    # 1) Get students enrolled in this organization (+ optional class filter)
    enrollment_query = (
        select(StudentOrgEnrollment)
        .where(StudentOrgEnrollment.organization_id == org.id)
        .options(selectinload(StudentOrgEnrollment.student))
    )
    if klass:
        enrollment_query = enrollment_query.where(StudentOrgEnrollment.label == klass)

    enrollments_result = await db.execute(enrollment_query)
    enrollments = enrollments_result.scalars().all()

    if not enrollments:
        return TeacherClassListResponse(
            teacherId=to_uuid(teacher.id),
            organizationId=to_uuid(org.id),
            subject=subject,
            klass=klass,
            windowDays=window_days,
            students=[],
        )

    student_ids = [e.student_id for e in enrollments]

    # 2) Get most recent ability snapshot for each student
    abilities_query = (
        select(IRTStudentAbility)
        .where(
            IRTStudentAbility.user_id.in_(student_ids),
            IRTStudentAbility.subject == subject,
            IRTStudentAbility.calibrated_at >= since,
        )
        .order_by(
            IRTStudentAbility.user_id,
            IRTStudentAbility.calibrated_at.desc(),
        )
    )
    abilities_result = await db.execute(abilities_query)
    abilities_all = abilities_result.scalars().all()

    # Group by student (keep most recent)
    ability_by_student: dict[UUID, IRTStudentAbility] = {}
    for ab in abilities_all:
        if ab.user_id not in ability_by_student:
            ability_by_student[ab.user_id] = ab

    # 3) Get user details for names
    users_query = select(User).where(User.id.in_(student_ids))
    users_result = await db.execute(users_query)
    # Build dict with type: ignore for Column[int] runtime values
    users: dict[int, User] = {}
    for u in users_result.scalars().all():
        users[int(u.id)] = u  # type: ignore[arg-type]

    # 4) Build response
    students: list[TeacherClassStudent] = []
    for enrollment in enrollments:
        ability = ability_by_student.get(enrollment.student_id)
        if not ability:
            continue  # Skip students with no recent ability data

        user = users.get(int(enrollment.student_id))
        student_name = user.email.split("@")[0] if user else "Unknown"

        # Compute analytics
        band = classify_theta_band(ability.theta)
        risk = assess_risk_level(ability.theta, ability.theta_se or 1.0)

        # Compute 14-day delta
        delta_14d = None
        try:
            delta_14d = await compute_delta_theta(
                db=db,
                user_id=str(enrollment.student_id),
                subject=subject,
                days=14,
            )
        except Exception:
            pass  # Delta calculation optional

        students.append(
            TeacherClassStudent(
                studentId=to_uuid(enrollment.student_id),
                studentName=student_name,
                school=org.name,
                grade=None,  # TODO: Add grade to enrollment or user profile
                label=enrollment.label,
                subject=subject,
                theta=ability.theta,
                thetaSe=ability.theta_se or 1.0,
                thetaBand=band.value if hasattr(band, "value") else str(band),
                riskLevel=risk.value if hasattr(risk, "value") else str(risk),
                deltaTheta14d=delta_14d,
            )
        )

    return TeacherClassListResponse(
        teacherId=to_uuid(teacher.id),
        organizationId=to_uuid(org.id),
        subject=subject,
        klass=klass,
        windowDays=window_days,
        students=students,
    )
