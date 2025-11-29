"""
Classes router - Teacher dashboard endpoints for class management

Provides endpoints for:
- Class summary statistics (average score, student count, exam counts)
- Student roster per class
- Class-level performance analytics

This router uses synchronous database sessions matching the existing infrastructure.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.student import Class, Student, StudentClass
from app.models.core_entities import Teacher
from app.models.exam_models import ExamSession  # Primary model

router = APIRouter(prefix="/api/classes", tags=["classes"])


# TODO: Replace with actual JWT authentication
def get_current_user(db: Session = Depends(get_db)):
    """
    Mock authentication - returns a fake teacher user.

    REPLACE THIS with actual JWT token validation:
    - Decode and verify JWT token from Authorization header
    - Extract user_id and role
    - Query users table
    - Return authenticated User object
    """
    return {"id": 1, "role": "teacher", "email": "teacher@example.com"}


@router.get("/{class_id}/summary")
def get_class_summary(
    class_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get class summary statistics for teacher dashboard.

    Returns:
    - Class metadata (name, subject, grade)
    - Student count
    - Average score across all completed exams
    - Recent exam count

    Access Control:
    - Teachers: Can only view their own classes
    - Admins/Super Admins: Can view any class

    Args:
        class_id: Class identifier
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        {
            "class_id": 1,
            "name": "고2-1반 수학",
            "subject": "math",
            "grade": "11",
            "student_count": 25,
            "average_score": 78.5,
            "recent_exam_count": 120
        }

    Raises:
        HTTPException 403: User lacks permission
        HTTPException 404: Class not found
    """
    # Role-based access control
    if current_user["role"] not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다. 교사 또는 관리자만 접근 가능합니다.",
        )

    # Fetch class
    clazz = db.query(Class).filter(Class.id == class_id).first()  # type: ignore
    if not clazz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Class not found: {class_id}"
        )

    # Teacher authorization: Can only view their own classes
    if current_user["role"] == "teacher":
        # Check if current user is the teacher for this class
        # Class.teacher_id references users.id directly
        if clazz.teacher_id != current_user["id"]:  # type: ignore
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 반에 대한 권한이 없습니다. 본인이 담당하는 반만 조회 가능합니다.",
            )

    # Get student IDs enrolled in this class
    student_ids = (
        db.query(Student.id)  # type: ignore
        .join(StudentClass, StudentClass.student_id == Student.id)  # type: ignore
        .filter(StudentClass.class_id == class_id)  # type: ignore
        .all()
    )
    student_ids = [sid[0] for sid in student_ids]

    # Handle empty class
    if not student_ids:
        return {
            "class_id": class_id,
            "name": clazz.name,  # type: ignore
            "subject": clazz.subject,  # type: ignore
            "grade": clazz.grade,  # type: ignore
            "student_count": 0,
            "average_score": None,
            "recent_exam_count": 0,
        }

    # Calculate average score and exam count
    # Only count completed exams
    result = (
        db.query(
            func.avg(ExamSession.score),  # type: ignore
            func.count(ExamSession.id),  # type: ignore
        )
        .filter(
            ExamSession.student_id.in_(student_ids),  # type: ignore
            ExamSession.status == "completed",  # type: ignore
        )
        .first()
    )

    avg_score, exam_count = result if result else (None, 0)

    return {
        "class_id": class_id,
        "name": clazz.name,  # type: ignore
        "subject": clazz.subject,  # type: ignore
        "grade": clazz.grade,  # type: ignore
        "student_count": len(student_ids),
        "average_score": float(avg_score) if avg_score is not None else None,
        "recent_exam_count": exam_count,
    }


@router.get("/{class_id}/students")
def get_class_students(
    class_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get list of students enrolled in a class.

    Returns student roster with basic info and latest exam results.

    Access Control:
    - Teachers: Can only view their own classes
    - Admins: Can view any class

    Args:
        class_id: Class identifier
        skip: Pagination offset (default: 0)
        limit: Maximum results (default: 50, max: 100)
        db: Database session
        current_user: Authenticated user

    Returns:
        {
            "class_id": 1,
            "students": [
                {
                    "student_id": 10,
                    "name": "김철수",
                    "grade": "11",
                    "latest_score": 85.5,
                    "exam_count": 5,
                    "enrolled_at": "2024-03-01T09:00:00Z"
                },
                ...
            ],
            "total_count": 25
        }

    Raises:
        HTTPException 403: User lacks permission
        HTTPException 404: Class not found
    """
    # Role-based access control
    if current_user["role"] not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다."
        )

    # Fetch class and verify authorization
    clazz = db.query(Class).filter(Class.id == class_id).first()  # type: ignore
    if not clazz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Class not found: {class_id}"
        )

    if current_user["role"] == "teacher" and clazz.teacher_id != current_user["id"]:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 반에 대한 권한이 없습니다.",
        )

    # Enforce pagination limits
    limit = min(limit, 100)

    # Get students with enrollment info
    enrollments = (
        db.query(Student, StudentClass.created_at)  # type: ignore
        .join(StudentClass, StudentClass.student_id == Student.id)  # type: ignore
        .filter(StudentClass.class_id == class_id)  # type: ignore
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Get total count for pagination
    total_count = (
        db.query(func.count(StudentClass.student_id))  # type: ignore
        .filter(StudentClass.class_id == class_id)  # type: ignore
        .scalar()
    )

    students_data = []
    for student, enrolled_at in enrollments:
        # Get latest exam results for this student
        latest_exam = (
            db.query(ExamSession)
            .filter(
                ExamSession.student_id == student.id,  # type: ignore
                ExamSession.status == "completed",  # type: ignore
            )
            .order_by(ExamSession.ended_at.desc())  # type: ignore
            .first()
        )

        # Count total completed exams
        exam_count = (
            db.query(func.count(ExamSession.id))  # type: ignore
            .filter(
                ExamSession.student_id == student.id,  # type: ignore
                ExamSession.status == "completed",  # type: ignore
            )
            .scalar()
        )

        students_data.append(
            {
                "student_id": student.id,  # type: ignore
                "name": student.name,  # type: ignore
                "grade": student.grade,  # type: ignore
                "latest_score": float(latest_exam.score) if latest_exam and latest_exam.score else None,  # type: ignore
                "exam_count": exam_count or 0,
                "enrolled_at": enrolled_at.isoformat() if enrolled_at else None,
            }
        )

    return {
        "class_id": class_id,
        "students": students_data,
        "total_count": total_count or 0,
    }


@router.get("/{class_id}/exam-stats")
def get_class_exam_stats(
    class_id: int,
    exam_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get detailed exam statistics for a class.

    Provides aggregated metrics:
    - Score distribution (min, max, avg, median, std dev)
    - Theta distribution for IRT-based analysis
    - Exam completion rates
    - Time-based performance trends

    Access Control:
    - Teachers: Own classes only
    - Admins: Any class

    Args:
        class_id: Class identifier
        exam_type: Optional filter (placement, practice, mock, official, quiz)
        db: Database session
        current_user: Authenticated user

    Returns:
        {
            "class_id": 1,
            "exam_type": "mock",
            "stats": {
                "total_exams": 150,
                "completed_exams": 145,
                "avg_score": 78.5,
                "min_score": 45.0,
                "max_score": 98.5,
                "std_dev": 12.3,
                "avg_theta": 0.25,
                "avg_duration_sec": 3600
            }
        }

    Raises:
        HTTPException 403: User lacks permission
        HTTPException 404: Class not found
    """
    # Role-based access control
    if current_user["role"] not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다."
        )

    # Fetch class and verify authorization
    clazz = db.query(Class).filter(Class.id == class_id).first()  # type: ignore
    if not clazz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Class not found: {class_id}"
        )

    if current_user["role"] == "teacher" and clazz.teacher_id != current_user["id"]:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 반에 대한 권한이 없습니다.",
        )

    # Get student IDs in this class
    student_ids = (
        db.query(Student.id)  # type: ignore
        .join(StudentClass, StudentClass.student_id == Student.id)  # type: ignore
        .filter(StudentClass.class_id == class_id)  # type: ignore
        .all()
    )
    student_ids = [sid[0] for sid in student_ids]

    if not student_ids:
        return {
            "class_id": class_id,
            "exam_type": exam_type,
            "stats": {
                "total_exams": 0,
                "completed_exams": 0,
                "avg_score": None,
                "min_score": None,
                "max_score": None,
                "std_dev": None,
                "avg_theta": None,
                "avg_duration_sec": None,
            },
        }

    # Build query with optional exam_type filter
    query = db.query(ExamSession).filter(ExamSession.student_id.in_(student_ids))  # type: ignore
    if exam_type:
        query = query.filter(ExamSession.exam_type == exam_type)  # type: ignore

    # Get completed exams for statistics
    completed_exams = query.filter(ExamSession.status == "completed").all()  # type: ignore
    total_exams = query.count()

    if not completed_exams:
        return {
            "class_id": class_id,
            "exam_type": exam_type,
            "stats": {
                "total_exams": total_exams,
                "completed_exams": 0,
                "avg_score": None,
                "min_score": None,
                "max_score": None,
                "std_dev": None,
                "avg_theta": None,
                "avg_duration_sec": None,
            },
        }

    # Calculate statistics
    scores = [exam.score for exam in completed_exams if exam.score is not None]  # type: ignore
    thetas = [exam.theta for exam in completed_exams if exam.theta is not None]  # type: ignore
    durations = [exam.duration_sec for exam in completed_exams if exam.duration_sec is not None]  # type: ignore

    # Use SQL aggregates for better performance
    stats_result = (
        query.filter(ExamSession.status == "completed")  # type: ignore
        .with_entities(
            func.avg(ExamSession.score),  # type: ignore
            func.min(ExamSession.score),  # type: ignore
            func.max(ExamSession.score),  # type: ignore
            func.stddev(ExamSession.score),  # type: ignore
            func.avg(ExamSession.theta),  # type: ignore
            func.avg(ExamSession.duration_sec),  # type: ignore
        )
        .first()
    )

    avg_score, min_score, max_score, std_dev, avg_theta, avg_duration = (
        stats_result if stats_result else (None,) * 6
    )

    return {
        "class_id": class_id,
        "exam_type": exam_type,
        "stats": {
            "total_exams": total_exams,
            "completed_exams": len(completed_exams),
            "avg_score": float(avg_score) if avg_score is not None else None,
            "min_score": float(min_score) if min_score is not None else None,
            "max_score": float(max_score) if max_score is not None else None,
            "std_dev": float(std_dev) if std_dev is not None else None,
            "avg_theta": float(avg_theta) if avg_theta is not None else None,
            "avg_duration_sec": int(avg_duration) if avg_duration is not None else None,
        },
    }
