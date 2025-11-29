"""
FastAPI router for exam session management

Provides endpoints for:
- Starting exam sessions
- Submitting answers
- Completing exams
- Retrieving exam progress

This router handles the core CAT exam flow. The adaptive algorithm
logic (item selection, theta estimation) can be integrated as a
separate service layer.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.core_entities import ExamSession, Attempt
from app.models.student import Student, Class
from app.schemas.core_schemas import (
    ExamSessionCreate,
    ExamSessionResponse,
    ExamSessionUpdate,
    ExamSessionWithAttempts,
    AnswerSubmit,
    AttemptResponse,
)

router = APIRouter(prefix="/api/exams", tags=["exams"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper: Get current user (placeholder for auth integration)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def get_current_user(db: Session = Depends(get_db)):
    """
    TODO: Replace with actual JWT/session authentication.

    This is a placeholder that should be replaced with your
    authentication system. Should return a User object with:
    - id: user ID
    - role: user role (student, teacher, admin, etc.)
    - student: related Student object (if role == 'student')
    """

    # For now, return a mock user for testing
    # In production, this should decode JWT token and fetch user from DB
    class MockUser:
        def __init__(self):
            self.id = 1  # Replace with actual user ID from JWT
            self.role = "student"  # Replace with actual role
            self.student_id = 1  # Replace with actual student ID

    return MockUser()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Exam Session Management
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post(
    "/start", response_model=ExamSessionResponse, status_code=status.HTTP_201_CREATED
)
def start_exam(
    payload: ExamSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Start a new exam session for the authenticated student.

    Workflow:
    1. Verify user is a student
    2. Get student record from user
    3. Validate class_id (if provided)
    4. Create new exam session with status='in_progress'
    5. Return exam session details

    Next steps:
    - Client can call /next-item to get first question
    - Client submits answers via /answer endpoint
    - Client completes exam via /complete endpoint
    """
    # Verify student role
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can take exams. Current role: " + current_user.role,
        )

    # Get student record
    query = select(Student).where(Student.user_id == current_user.id)
    student = db.execute(query).scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student profile not found for user {current_user.id}",
        )

    # Validate class (if provided)
    if payload.class_id is not None:
        query = select(Class).where(Class.id == payload.class_id)
        clazz = db.execute(query).scalar_one_or_none()

        if not clazz:
            raise HTTPException(
                status_code=404, detail=f"Class {payload.class_id} not found"
            )

    # Create exam session
    exam_session = ExamSession(
        student_id=student.id,
        class_id=payload.class_id,
        exam_type=payload.exam_type,
        status="in_progress",
        meta=payload.meta,
    )

    db.add(exam_session)
    db.commit()
    db.refresh(exam_session)

    return exam_session


@router.post(
    "/answer", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED
)
def submit_answer(
    payload: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Submit an answer for an exam item.

    Workflow:
    1. Verify user is a student
    2. Verify exam session exists and belongs to student
    3. Verify exam is still in progress
    4. Record attempt in database
    5. (Optional) Update theta estimate via CAT service
    6. (Optional) Check termination criteria

    Note: In v0.5, correctness is determined client-side.
    In production, move scoring logic to server.
    """
    # Verify student role
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit answers",
        )

    # Get exam session and verify ownership
    query = (
        select(ExamSession)
        .join(Student, ExamSession.student_id == Student.id)
        .where(
            ExamSession.id == payload.exam_session_id,
            Student.user_id == current_user.id,
        )
    )
    exam_session: Optional[ExamSession] = db.execute(query).scalar_one_or_none()  # type: ignore

    if not exam_session:
        raise HTTPException(
            status_code=404,
            detail=f"Exam session {payload.exam_session_id} not found or not owned by current user",
        )

    # Verify exam is still in progress (type: ignore for SQLAlchemy Column access)
    if exam_session.status != "in_progress":  # type: ignore
        raise HTTPException(
            status_code=400,
            detail=f"Exam session is {exam_session.status}. Cannot submit answers.",
        )

    # Create attempt record
    attempt = Attempt(
        student_id=exam_session.student_id,
        exam_session_id=exam_session.id,
        item_id=payload.item_id,
        correct=payload.correct,
        submitted_answer=payload.answer,
        selected_choice=payload.selected_choice,
        response_time_ms=payload.response_time_ms,
    )

    db.add(attempt)

    # TODO: Integrate CAT service here
    # - Update theta estimate based on item difficulty and correctness
    # - Check termination criteria (SE < threshold, max items, etc.)
    # - If termination criteria met, auto-complete exam
    #
    # Example:
    # if should_terminate(exam_session, attempt):
    #     exam_session.status = "completed"
    #     exam_session.ended_at = datetime.utcnow()
    #     exam_session.theta = calculate_theta(exam_session)
    #     exam_session.standard_error = calculate_se(exam_session)

    db.commit()
    db.refresh(attempt)

    return attempt


@router.patch("/{session_id}/complete", response_model=ExamSessionResponse)
def complete_exam(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Mark an exam session as completed.

    Workflow:
    1. Verify exam session exists and belongs to student
    2. Calculate final score and theta estimate
    3. Update exam session status to 'completed'
    4. Record completion timestamp

    This endpoint can be called by:
    - Student when manually finishing exam
    - Server automatically when termination criteria met
    """
    # Get exam session and verify ownership
    query = (
        select(ExamSession)
        .join(Student, ExamSession.student_id == Student.id)
        .where(
            ExamSession.id == session_id,
            Student.user_id == current_user.id,
        )
        .options(selectinload(ExamSession.attempts))
    )
    exam_session: Optional[ExamSession] = db.execute(query).scalar_one_or_none()  # type: ignore

    if not exam_session:
        raise HTTPException(
            status_code=404,
            detail=f"Exam session {session_id} not found or not owned by current user",
        )

    if exam_session.status == "completed":  # type: ignore
        raise HTTPException(status_code=400, detail="Exam already completed")

    # Calculate final metrics
    # TODO: Integrate CAT service for accurate theta/SE calculation
    attempts = exam_session.attempts
    total_attempts = len(attempts)
    correct_attempts = sum(1 for a in attempts if a.correct)  # type: ignore

    # Simple score calculation (replace with proper IRT scoring)
    from decimal import Decimal

    if total_attempts > 0:
        exam_session.score = Decimal(str((correct_attempts / total_attempts) * 100))  # type: ignore

    # Calculate duration
    if exam_session.started_at:  # type: ignore
        duration = datetime.utcnow() - exam_session.started_at  # type: ignore
        exam_session.duration_sec = int(duration.total_seconds())  # type: ignore

    # Mark as completed
    exam_session.status = "completed"  # type: ignore
    exam_session.ended_at = datetime.utcnow()  # type: ignore

    # TODO: Calculate theta and standard_error using IRT
    # exam_session.theta = calculate_theta_from_attempts(attempts)
    # exam_session.standard_error = calculate_se_from_attempts(attempts)

    db.commit()
    db.refresh(exam_session)

    return exam_session


@router.get("/{session_id}", response_model=ExamSessionWithAttempts)
def get_exam_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get exam session details with all attempts.

    Returns:
    - Exam session metadata
    - All recorded attempts
    - Current theta/score (if available)

    Access control:
    - Students can view their own exams
    - Teachers can view exams in their classes
    - Admins can view all exams
    """
    query = (
        select(ExamSession)
        .where(ExamSession.id == session_id)
        .options(selectinload(ExamSession.attempts))
    )
    exam_session = db.execute(query).scalar_one_or_none()

    if not exam_session:
        raise HTTPException(
            status_code=404, detail=f"Exam session {session_id} not found"
        )

    # TODO: Implement proper access control
    # For now, allow access if user is the student or has appropriate role
    if current_user.role == "student":
        query = select(Student).where(Student.user_id == current_user.id)
        student = db.execute(query).scalar_one_or_none()

        if not student or exam_session.student_id != student.id:  # type: ignore
            raise HTTPException(
                status_code=403, detail="You don't have permission to view this exam"
            )

    return exam_session


@router.get("/student/history", response_model=List[ExamSessionResponse])
def get_student_exam_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    exam_type: Optional[str] = Query(None, description="Filter by exam type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get exam history for the current student.

    Returns all exam sessions for the authenticated student,
    ordered by most recent first.

    Supports filtering by:
    - exam_type (placement, practice, mock, official, quiz)
    - status (in_progress, completed, abandoned)
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=403, detail="Only students can view their exam history"
        )

    # Get student record
    query = select(Student).where(Student.user_id == current_user.id)
    student = db.execute(query).scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Build query with filters
    query = select(ExamSession).where(ExamSession.student_id == student.id)

    if exam_type:
        query = query.where(ExamSession.exam_type == exam_type)
    if status:
        query = query.where(ExamSession.status == status)

    query = query.order_by(ExamSession.started_at.desc()).offset(skip).limit(limit)

    exams = db.execute(query).scalars().all()
    return exams


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Future: Next Item Selection (CAT Integration Point)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/{session_id}/next-item")
def get_next_item(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get the next item to present in the adaptive exam.

    TODO: Implement CAT item selection logic

    Algorithm:
    1. Get current theta estimate
    2. Query item pool for items matching target difficulty
    3. Exclude already-answered items
    4. Apply constraints (content balancing, exposure control)
    5. Select item with maximum information at current theta
    6. Return item to client

    For now, returns a placeholder response.
    """
    # Verify exam session exists and belongs to student
    query = (
        select(ExamSession)
        .join(Student, ExamSession.student_id == Student.id)
        .where(
            ExamSession.id == session_id,
            Student.user_id == current_user.id,
        )
    )
    exam_session = db.execute(query).scalar_one_or_none()

    if not exam_session:
        raise HTTPException(
            status_code=404, detail=f"Exam session {session_id} not found"
        )

    if exam_session.status != "in_progress":  # type: ignore
        raise HTTPException(status_code=400, detail="Exam is not in progress")

    # TODO: Implement actual CAT item selection
    return {
        "message": "CAT item selection not yet implemented",
        "exam_session_id": session_id,
        "current_theta": exam_session.theta,
        "next_item_id": None,
        "suggestion": "Integrate with adaptive_engine service or implement IRT-based item selection",
    }
