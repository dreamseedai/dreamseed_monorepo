"""
Service layer for student-related operations
"""
from typing import List, Optional, Tuple, cast
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.student import Student, Class, StudentClass
from app.models.ability_history import StudentAbilityHistory
from app.schemas.students import (
    StudentSummary,
    StudentDetail,
    AbilityPoint,
    RecentTest,
    ChildDetail,
)


def list_students_for_teacher(
    db: Session,
    teacher_id: int,
    q: Optional[str],
    class_id: Optional[int],
    status: Optional[str],
    page: int,
    page_size: int,
) -> Tuple[List[StudentSummary], int]:
    stmt = (
        select(Student, Class)
        .join(StudentClass, StudentClass.student_id == Student.id, isouter=True)
        .join(Class, Class.id == StudentClass.class_id, isouter=True)
        .where(Class.teacher_id == teacher_id)
    )

    if q:
        stmt = stmt.where(Student.name.ilike(f"%{q}%"))

    if class_id:
        stmt = stmt.where(Class.id == class_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    rows = db.execute(stmt).all()
    results: List[StudentSummary] = []
    for s, c in rows:
        results.append(
            StudentSummary(
                id=str(s.id),
                name=s.name,
                class_id=str(c.id) if c else None,
                class_name=c.name if c else None,
                current_ability_theta=None,
                recent_score=None,
                status="On Track",
                risk_flags=[],
            )
        )

    return results, total or 0


def get_student_detail_for_teacher(
    db: Session,
    teacher_id: int,
    student_id: int,
) -> Optional[StudentDetail]:
    student = db.get(Student, student_id)
    if student is None:
        return None

    hist_stmt = (
        select(StudentAbilityHistory)
        .where(StudentAbilityHistory.student_id == student_id)
        .order_by(StudentAbilityHistory.as_of_date.desc())
        .limit(10)
    )
    rows = list(reversed(db.scalars(hist_stmt).all()))
    ability_trend = [
        AbilityPoint(label=row.as_of_date.isoformat(), value=cast(float, row.theta))
        for row in rows
    ]

    recent_tests: List[RecentTest] = []

    return StudentDetail(
        id=str(student.id),
        name=cast(str, student.name),
        class_id=None,
        class_name=None,
        current_ability_theta=ability_trend[-1].value if ability_trend else None,
        recent_score=None,
        status="On Track",
        risk_flags=[],
        ability_trend=ability_trend,
        recent_tests=recent_tests,
    )


def get_child_detail_for_parent(
    db: Session,
    parent_id: int,
    child_id: int,
) -> Optional[ChildDetail]:
    """
    Get detailed information about a child for parent view
    
    Args:
        db: Database session
        parent_id: Parent's user ID
        child_id: Child (student) ID
        
    Returns:
        ChildDetail or None if not found/no access
    """
    # TODO: Implement parent-child relationship verification
    # For now, we'll fetch student data similar to teacher view
    
    student = db.get(Student, child_id)
    if student is None:
        return None
    
    # Get ability history
    hist_stmt = (
        select(StudentAbilityHistory)
        .where(StudentAbilityHistory.student_id == child_id)
        .order_by(StudentAbilityHistory.as_of_date.desc())
        .limit(10)
    )
    hist_rows = list(reversed(db.scalars(hist_stmt).all()))
    
    ability_trend = [
        AbilityPoint(label=row.as_of_date.isoformat(), value=cast(float, row.theta))
        for row in hist_rows
    ]
    
    current_theta = ability_trend[-1].value if ability_trend else None
    
    # Compute status
    if current_theta is None:
        status_val = "On Track"
    elif current_theta < -0.5:
        status_val = "Struggling"
    elif current_theta < 0:
        status_val = "At Risk"
    else:
        status_val = "On Track"
    
    return ChildDetail(
        id=str(student.id),
        name=cast(str, student.name),
        class_id=None,
        class_name=None,
        current_ability_theta=current_theta,
        recent_score=None,
        status=status_val,
        risk_flags=[],
        ability_trend=ability_trend,
        recent_tests=[],
        study_time_month=None,
        strengths=[],
        areasToImprove=[],
        recentActivity=[],
    )


def get_student_ability_history(
    db: Session,
    student_id: int,
    limit: int = 30,
    from_date: Optional[date] = None,
) -> List[AbilityPoint]:
    """
    Get ability (IRT theta) history for a student
    
    Args:
        db: Database session
        student_id: Student's ID
        limit: Maximum number of points to return
        from_date: Optional start date filter
        
    Returns:
        List of AbilityPoint (chronologically ordered)
    """
    stmt = (
        select(StudentAbilityHistory)
        .where(StudentAbilityHistory.student_id == student_id)
    )
    
    if from_date:
        stmt = stmt.where(StudentAbilityHistory.as_of_date >= from_date)
    
    stmt = stmt.order_by(StudentAbilityHistory.as_of_date.desc()).limit(limit)
    
    rows = list(reversed(db.scalars(stmt).all()))
    
    return [
        AbilityPoint(
            label=row.as_of_date.isoformat(),
            value=cast(float, row.theta),
        )
        for row in rows
    ]
