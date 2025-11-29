"""
Dashboard API for Teachers, Parents, and Tutors

DreamSeedAI - CAT 결과 조회 대시보드

교사/학부모/튜터가 학생의 적응형 시험(CAT) 결과를 조회하는 API.
ExamSession.score와 meta.grade_* 정보를 사용하여 점수/등급을 제공합니다.

주요 기능:
 - 교사/튜터: 반 전체 시험 요약, 개별 학생 시험 히스토리
 - 학부모: 자녀 시험 히스토리 및 성적 분석
 - 튜터: 담당 학생 전체 요약

Usage:
    # 교사/튜터용
    GET /api/dashboard/teacher/classes/{class_id}/exams
    GET /api/dashboard/teacher/students/{student_id}/exams

    # 튜터용
    GET /api/dashboard/tutor/students/exams

    # 학부모용
    GET /api/dashboard/parent/children/{student_id}/exams

    # 공통
    GET /api/dashboard/exams/{exam_session_id}
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.student import Student, Class, StudentClass
from app.models.core_entities import Teacher, StudentClassroom
from app.models.exam_models import ExamSession  # Primary model

# Note: Attempt model is currently disabled
from app.core.services.score_utils import summarize_theta

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper Functions: Role Verification
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def get_teacher_or_403(current_user: User, db: Session) -> Teacher:
    """Verify user is a teacher/tutor and return Teacher record."""
    if current_user.role not in ("teacher", "tutor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="교사 또는 튜터만 접근할 수 있습니다.",
        )

    # Get teacher record
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher profile not found"
        )

    return teacher  # type: ignore


def get_parent_or_403(current_user: User) -> User:
    """Verify user is a parent."""
    if current_user.role != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="학부모만 접근할 수 있습니다."
        )
    return current_user


def verify_teacher_access_to_student(
    teacher: Teacher, student_id: int, db: Session
) -> Student:
    """
    Verify teacher has access to student (through class enrollment).
    Returns Student if access granted, raises 403 otherwise.
    """
    # Check if student exists
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # Check if student is in any of teacher's classes
    # Try StudentClass junction table first
    access = (
        db.query(StudentClass)
        .join(Class, Class.id == StudentClass.class_id)
        .filter(
            StudentClass.student_id == student_id, Class.teacher_id == teacher.user_id
        )
        .first()
    )

    if not access:
        # Try alternative StudentClassroom junction table
        access = (
            db.query(StudentClassroom)
            .join(Class, Class.id == StudentClassroom.class_id)
            .filter(
                StudentClassroom.student_id == student_id,
                Class.teacher_id == teacher.user_id,
            )
            .first()
        )

    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 학생은 귀하의 반에 속해 있지 않습니다.",
        )

    return student


def verify_parent_access_to_student(
    parent: User, student_id: int, db: Session
) -> Student:
    """
    Verify parent has access to student (as their child).

    TODO: Implement actual parent-child relationship verification.
    Currently uses basic student existence check.
    In production, check ParentApproval table or parent_student junction.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # TODO: Add actual parent-child relationship check
    # Example: Check if parent.id is in student's approved parent list
    # For now, we allow access (MVP only - add proper verification in production)

    return student


def ensure_score_and_grades(exam_session: ExamSession) -> None:
    """
    Ensure ExamSession has score and grade information.
    If missing, calculate from theta using score_utils.

    Modifies exam_session in-place (does not commit to DB).
    """
    if exam_session.theta is None:
        return  # No theta, can't calculate

    # Calculate if score is missing
    if exam_session.score is None:
        summary = summarize_theta(float(exam_session.theta))
        exam_session.score = summary["score_0_100"]

        # Also populate meta if empty
        if exam_session.meta is None:
            exam_session.meta = {}

        exam_session.meta.setdefault("t_score", summary["t_score"])
        exam_session.meta.setdefault("percentile", summary["percentile"])
        exam_session.meta.setdefault("grade_numeric", summary["grade_numeric"])
        exam_session.meta.setdefault("grade_letter", summary["grade_letter"])


def format_exam_session(session: ExamSession) -> Dict[str, Any]:
    """Format ExamSession for API response."""
    ensure_score_and_grades(session)

    return {
        "exam_session_id": session.id,
        "exam_type": session.exam_type,
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "duration_sec": session.duration_sec,
        "theta": float(session.theta) if session.theta is not None else None,
        "standard_error": (
            float(session.standard_error)
            if session.standard_error is not None
            else None
        ),
        "score": float(session.score) if session.score is not None else None,
        "grade_numeric": session.meta.get("grade_numeric") if session.meta else None,
        "grade_letter": session.meta.get("grade_letter") if session.meta else None,
        "percentile": session.meta.get("percentile") if session.meta else None,
        "t_score": session.meta.get("t_score") if session.meta else None,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Teacher/Tutor: Class Exam Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/teacher/classes/{class_id}/exams")
def get_class_exam_summary(
    class_id: int,
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of exam sessions to return"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    교사/튜터용: 특정 반의 시험 요약 정보

    Returns:
    - 반 정보 (name, subject)
    - 학생 수
    - 최근 완료된 시험 세션 목록 (점수/등급 포함)
    - 학생별 최근 시험 요약

    Permissions:
    - 해당 반을 담당하는 교사/튜터만 접근 가능
    """
    teacher = get_teacher_or_403(current_user, db)

    # Verify class exists and belongs to teacher
    clazz = db.query(Class).filter(Class.id == class_id).first()
    if not clazz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    if clazz.teacher_id != teacher.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 반에 대한 권한이 없습니다.",
        )

    # Get students in this class
    student_ids = [
        sc.student_id
        for sc in db.query(StudentClass).filter(StudentClass.class_id == class_id).all()
    ]

    if not student_ids:
        # Try alternative junction table
        student_ids = [
            sc.student_id
            for sc in db.query(StudentClassroom)
            .filter(StudentClassroom.class_id == class_id)
            .all()
        ]

    if not student_ids:
        return {
            "class_id": class_id,
            "name": clazz.name,
            "subject": clazz.subject,
            "grade": clazz.grade,
            "student_count": 0,
            "exam_sessions": [],
            "students": [],
        }

    # Get recent completed exam sessions for this class
    exam_sessions = (
        db.query(ExamSession)
        .filter(
            ExamSession.class_id == class_id,
            ExamSession.status == "completed",
        )
        .order_by(desc(ExamSession.ended_at))
        .limit(limit)
        .all()
    )

    # Format exam sessions
    exam_list = [format_exam_session(session) for session in exam_sessions]

    # Create student summary (latest exam per student)
    student_exam_map = {}
    for session in exam_sessions:
        sid = session.student_id
        if sid not in student_exam_map:
            student_exam_map[sid] = format_exam_session(session)

    # Get student info
    students = db.query(Student).filter(Student.id.in_(student_ids)).all()
    student_summary = []

    for student in students:
        latest_exam = student_exam_map.get(student.id)
        exam_count = sum(1 for s in exam_sessions if s.student_id == student.id)

        student_summary.append(
            {
                "student_id": student.id,
                "name": student.name,
                "grade": student.grade,
                "exam_count": exam_count,
                "latest_exam": latest_exam,
            }
        )

    # Sort students by latest exam date
    student_summary.sort(
        key=lambda x: x["latest_exam"]["ended_at"] if x["latest_exam"] else "",
        reverse=True,
    )

    return {
        "class_id": class_id,
        "name": clazz.name,
        "subject": clazz.subject,
        "grade": clazz.grade,
        "student_count": len(student_ids),
        "exam_sessions": exam_list,
        "students": student_summary,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Teacher/Tutor: Student Exam History
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/teacher/students/{student_id}/exams")
def get_student_exam_history_for_teacher(
    student_id: int,
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of exam sessions to return"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    교사/튜터용: 특정 학생의 시험 히스토리

    Returns:
    - 학생 정보
    - 최근 N개 시험 결과 (점수/등급/θ/SE 포함)
    - 통계 (평균 점수, 최고/최저 등)

    Permissions:
    - 해당 학생을 가르치는 교사/튜터만 접근 가능
    """
    teacher = get_teacher_or_403(current_user, db)
    student = verify_teacher_access_to_student(teacher, student_id, db)

    # Get exam sessions for this student
    exam_sessions = (
        db.query(ExamSession)
        .filter(ExamSession.student_id == student_id)
        .order_by(desc(ExamSession.started_at))
        .limit(limit)
        .all()
    )

    # Format sessions
    exams = [format_exam_session(session) for session in exam_sessions]

    # Calculate statistics
    completed_exams = [
        e for e in exams if e["status"] == "completed" and e["score"] is not None
    ]

    stats = None
    if completed_exams:
        scores = [e["score"] for e in completed_exams]
        stats = {
            "total_exams": len(completed_exams),
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "latest_score": completed_exams[0]["score"] if completed_exams else None,
        }

    return {
        "student_id": student_id,
        "student_name": student.name,
        "student_grade": student.grade,
        "exams": exams,
        "statistics": stats,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Parent: Child Exam History
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/parent/children/{student_id}/exams")
def get_child_exam_history_for_parent(
    student_id: int,
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of exam sessions to return"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    학부모용: 자녀의 시험 히스토리

    Returns:
    - 자녀 정보
    - 최근 N개 시험 결과 (점수/등급/백분위 포함)
    - θ/SE는 제외 (학부모는 IRT 기술적 세부사항 불필요)

    Permissions:
    - 해당 학생의 학부모만 접근 가능
    """
    parent = get_parent_or_403(current_user)
    student = verify_parent_access_to_student(parent, student_id, db)

    # Get exam sessions for this student
    exam_sessions = (
        db.query(ExamSession)
        .filter(
            ExamSession.student_id == student_id,
            ExamSession.status == "completed",  # Parents only see completed exams
        )
        .order_by(desc(ExamSession.ended_at))
        .limit(limit)
        .all()
    )

    # Format sessions (simplified for parents - no theta/SE)
    exams = []
    for session in exam_sessions:
        ensure_score_and_grades(session)

        exams.append(
            {
                "exam_session_id": session.id,
                "exam_type": session.exam_type,
                "date": (
                    session.ended_at.isoformat()
                    if session.ended_at
                    else session.started_at.isoformat()
                ),
                "duration_sec": session.duration_sec,
                "score": float(session.score) if session.score is not None else None,
                "grade_numeric": (
                    session.meta.get("grade_numeric") if session.meta else None
                ),
                "grade_letter": (
                    session.meta.get("grade_letter") if session.meta else None
                ),
                "percentile": session.meta.get("percentile") if session.meta else None,
            }
        )

    # Calculate statistics
    completed_exams = [e for e in exams if e["score"] is not None]

    stats = None
    if completed_exams:
        scores = [e["score"] for e in completed_exams]
        stats = {
            "total_exams": len(completed_exams),
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "recent_trend": (
                "improving" if len(scores) >= 2 and scores[0] > scores[-1] else "stable"
            ),
        }

    return {
        "student_id": student_id,
        "student_name": student.name,
        "student_grade": student.grade,
        "exams": exams,
        "statistics": stats,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Tutor: All Students Exam Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/tutor/students/exams")
def get_all_students_for_tutor(
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of students to return"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    튜터용: 담당 학생 전체의 최근 시험 요약

    Returns:
    - 담당 학생 목록 (각 학생의 최근 시험 정보 포함)
    - 전체 평균 점수

    Permissions:
    - 튜터만 접근 가능
    """
    if current_user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="튜터만 접근할 수 있습니다."
        )

    teacher = get_teacher_or_403(current_user, db)

    # Get all classes taught by this tutor
    classes = db.query(Class).filter(Class.teacher_id == teacher.user_id).all()

    if not classes:
        return {
            "tutor_id": teacher.id,
            "students": [],
            "statistics": None,
        }

    # Get all student IDs from these classes
    class_ids = [c.id for c in classes]
    student_ids = set()

    for class_id in class_ids:
        sids = [
            sc.student_id
            for sc in db.query(StudentClass)
            .filter(StudentClass.class_id == class_id)
            .all()
        ]
        student_ids.update(sids)

        # Try alternative junction table
        sids = [
            sc.student_id
            for sc in db.query(StudentClassroom)
            .filter(StudentClassroom.class_id == class_id)
            .all()
        ]
        student_ids.update(sids)

    student_ids = list(student_ids)[:limit]

    if not student_ids:
        return {
            "tutor_id": teacher.id,
            "students": [],
            "statistics": None,
        }

    # Get students
    students = db.query(Student).filter(Student.id.in_(student_ids)).all()

    # Get latest exam for each student
    student_summary = []
    all_scores = []

    for student in students:
        latest_exam = (
            db.query(ExamSession)
            .filter(
                ExamSession.student_id == student.id,
                ExamSession.status == "completed",
            )
            .order_by(desc(ExamSession.ended_at))
            .first()
        )

        latest_exam_data = None
        if latest_exam:
            latest_exam_data = format_exam_session(latest_exam)
            if latest_exam_data["score"] is not None:
                all_scores.append(latest_exam_data["score"])

        # Count total exams
        exam_count = (
            db.query(func.count(ExamSession.id))
            .filter(
                ExamSession.student_id == student.id,
                ExamSession.status == "completed",
            )
            .scalar()
        )

        student_summary.append(
            {
                "student_id": student.id,
                "name": student.name,
                "grade": student.grade,
                "exam_count": exam_count,
                "latest_exam": latest_exam_data,
            }
        )

    # Sort by latest exam date
    student_summary.sort(
        key=lambda x: x["latest_exam"]["ended_at"] if x["latest_exam"] else "",
        reverse=True,
    )

    # Calculate overall statistics
    stats = None
    if all_scores:
        stats = {
            "total_students": len(students),
            "students_with_exams": len(all_scores),
            "avg_score": sum(all_scores) / len(all_scores),
            "max_score": max(all_scores),
            "min_score": min(all_scores),
        }

    return {
        "tutor_id": teacher.id,
        "students": student_summary,
        "statistics": stats,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Common: Single Exam Session Detail
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/exams/{exam_session_id}")
def get_exam_session_detail(
    exam_session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    공통: 특정 시험 세션의 상세 정보

    Returns:
    - 시험 정보 (점수/등급/θ/SE)
    - 문항별 응답 정보 (Attempt 목록)

    Permissions:
    - 교사: 자신의 학생만
    - 학부모: 자신의 자녀만
    - 튜터: 자신의 학생만
    - 학생: 자신의 시험만
    """
    exam_session = (
        db.query(ExamSession).filter(ExamSession.id == exam_session_id).first()
    )

    if not exam_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam session not found"
        )

    # Verify access based on role
    if current_user.role == "student":
        # Students can only view their own exams
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student or exam_session.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인의 시험만 볼 수 있습니다.",
            )

    elif current_user.role in ("teacher", "tutor"):
        # Teachers/tutors can view exams of their students
        teacher = get_teacher_or_403(current_user, db)
        try:
            verify_teacher_access_to_student(teacher, exam_session.student_id, db)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="귀하의 학생이 아닙니다."
            )

    elif current_user.role == "parent":
        # Parents can view exams of their children
        parent = get_parent_or_403(current_user)
        try:
            verify_parent_access_to_student(parent, exam_session.student_id, db)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="귀하의 자녀가 아닙니다."
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다."
        )

    # Format exam session
    exam_data = format_exam_session(exam_session)

    # Get attempts (item responses)
    attempts = (
        db.query(Attempt)
        .filter(Attempt.exam_session_id == exam_session_id)
        .order_by(Attempt.created_at)
        .all()
    )

    attempt_list = [
        {
            "attempt_id": att.id,
            "item_id": att.item_id,
            "correct": att.correct,
            "response_time_ms": att.response_time_ms,
            "selected_choice_id": att.selected_choice_id,
            "theta_before": (
                float(att.theta_before) if att.theta_before is not None else None
            ),
            "theta_after": (
                float(att.theta_after) if att.theta_after is not None else None
            ),
            "created_at": att.created_at.isoformat() if att.created_at else None,
        }
        for att in attempts
    ]

    # Add student info
    student = db.query(Student).filter(Student.id == exam_session.student_id).first()

    return {
        "exam_session": exam_data,
        "student": (
            {
                "id": student.id,
                "name": student.name,
                "grade": student.grade,
            }
            if student
            else None
        ),
        "attempts": attempt_list,
        "attempt_count": len(attempt_list),
    }
