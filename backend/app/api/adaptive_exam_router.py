"""
adaptive_exam_router.py

FastAPI router for adaptive testing (IRT/CAT) exam endpoints.

This router integrates:
 - AdaptiveEngine (exam_engine.py) for IRT/CAT logic
 - Core ORM models (Item, ExamSession, Attempt)
 - Database session management

Endpoints:
 - POST /api/exams/start - Start new adaptive exam session
 - POST /api/exams/answer - Submit answer and get next item
 - GET /api/exams/next - Get next item without submitting
 - GET /api/exams/{session_id} - Get exam session summary
 - POST /api/exams/{session_id}/complete - Manually complete exam

Example Integration:
    from app.api.adaptive_exam_router import router as exam_router
    app.include_router(exam_router, prefix="/api", tags=["adaptive-exams"])
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.services.exam_engine import AdaptiveEngine
from app.models.core_models_expanded import Student, ExamSession, Attempt, Item, Class
from app.schemas.exam_schemas import (
    ExamStartRequest,
    ExamStartResponse,
    AnswerSubmitRequest,
    AnswerSubmitResponse,
    NextItemRequest,
    NextItemResponse,
    ExamSessionSummary,
    AttemptSummary,
    ItemResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _get_adaptive_engine_from_session(
    exam_session: ExamSession, max_items: Optional[int] = None
) -> AdaptiveEngine:
    """
    Reconstruct AdaptiveEngine from exam session state.

    Args:
        exam_session: ExamSession ORM object
        max_items: Override max items (optional)

    Returns:
        AdaptiveEngine instance with restored state
    """
    # Get engine config from meta or use defaults
    meta = exam_session.meta or {}
    initial_theta = float(exam_session.theta or 0.0)
    max_items_cfg = max_items or meta.get("max_items", 20)

    # Create engine
    engine = AdaptiveEngine(initial_theta=initial_theta, max_items=max_items_cfg)

    # Restore attempt history
    for attempt in exam_session.attempts:
        if attempt.item:
            engine.record_attempt(
                item_id=attempt.item_id,
                params={
                    "a": float(attempt.item.a),
                    "b": float(attempt.item.b),
                    "c": float(attempt.item.c),
                },
                correct=attempt.correct,
            )

    return engine


def _select_next_item(
    db: Session,
    engine: AdaptiveEngine,
    exam_session: ExamSession,
    exclude_topics: Optional[List[str]] = None,
    max_exposure: Optional[int] = None,
) -> Optional[Item]:
    """
    Select next item using adaptive engine and database query.

    Args:
        db: Database session
        engine: AdaptiveEngine instance
        exam_session: Current exam session
        exclude_topics: Topics to exclude (optional)
        max_exposure: Max exposure count per item (optional)

    Returns:
        Selected Item or None if no suitable items
    """
    # Get already attempted item IDs
    attempted_ids = [att.item_id for att in exam_session.attempts if att.item_id]

    # Build query for available items
    query = select(Item).where(Item.id.not_in(attempted_ids) if attempted_ids else True)

    # Exclude topics if specified
    if exclude_topics:
        query = query.where(Item.topic.not_in(exclude_topics))

    # Execute query
    result = db.execute(query)
    available_items = result.scalars().all()

    if not available_items:
        return None

    # Convert to format expected by engine
    item_pool = [
        {"id": item.id, "a": float(item.a), "b": float(item.b), "c": float(item.c)}
        for item in available_items
    ]

    # Let engine pick best item
    selected_item_data = engine.pick_item(item_pool)

    if not selected_item_data:
        return None

    # Find and return the ORM object
    selected_id = selected_item_data["item_id"]
    return next((item for item in available_items if item.id == selected_id), None)


def _compute_score(exam_session: ExamSession) -> float:
    """
    Compute percentage score from attempts.

    Args:
        exam_session: ExamSession with attempts loaded

    Returns:
        Score as percentage (0-100)
    """
    if not exam_session.attempts:
        return 0.0

    correct_count = sum(1 for att in exam_session.attempts if att.correct)
    total_count = len(exam_session.attempts)

    return round((correct_count / total_count) * 100, 2)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/exams/start",
    response_model=ExamStartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_exam(request: ExamStartRequest, db: Session = Depends(get_db)):
    """
    Start a new adaptive exam session.

    Creates:
     - ExamSession record with initial theta
     - AdaptiveEngine instance
     - Selects first item

    Returns:
     - Exam session info with first item
    """
    # Validate student exists
    student = db.get(Student, request.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {request.student_id} not found",
        )

    # Validate class if provided
    if request.class_id:
        clazz = db.get(Class, request.class_id)
        if not clazz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class {request.class_id} not found",
            )

    # Create exam session
    exam_session = ExamSession(
        student_id=request.student_id,
        class_id=request.class_id,
        exam_type=request.exam_type,
        status="in_progress",
        started_at=datetime.utcnow(),
        theta=Decimal(str(request.initial_theta)),
        standard_error=Decimal("999.0"),  # Will be updated after first item
        meta={"max_items": request.max_items, "initial_theta": request.initial_theta},
    )

    db.add(exam_session)
    db.commit()
    db.refresh(exam_session)

    # Create adaptive engine
    engine = AdaptiveEngine(
        initial_theta=request.initial_theta, max_items=request.max_items
    )

    # Select first item
    next_item = _select_next_item(db, engine, exam_session)

    # Convert to response model
    next_item_response = None
    if next_item:
        next_item_response = ItemResponse(
            id=next_item.id,
            topic=next_item.topic,
            question_text=next_item.question_text,
            meta=next_item.meta,
        )

    return ExamStartResponse(
        exam_session_id=exam_session.id,
        status=exam_session.status,
        started_at=exam_session.started_at,
        current_theta=float(exam_session.theta),
        standard_error=float(exam_session.standard_error),
        max_items=request.max_items,
        next_item=next_item_response,
    )


@router.post("/exams/answer", response_model=AnswerSubmitResponse)
async def submit_answer(request: AnswerSubmitRequest, db: Session = Depends(get_db)):
    """
    Submit an answer and update theta estimate.

    Process:
     1. Validate exam session
     2. Load item and IRT parameters
     3. Create attempt record
     4. Update theta using AdaptiveEngine
     5. Check termination conditions
     6. Select next item (if continuing)

    Returns:
     - Updated theta, SE, termination status, next item
    """
    # Load exam session with attempts and student
    exam_session = db.execute(
        select(ExamSession)
        .options(joinedload(ExamSession.attempts).joinedload(Attempt.item))
        .where(ExamSession.id == request.exam_session_id)
    ).scalar_one_or_none()

    if not exam_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam session {request.exam_session_id} not found",
        )

    if exam_session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exam session is {exam_session.status}, cannot submit answer",
        )

    # Load item
    item = db.get(Item, request.item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {request.item_id} not found",
        )

    # Create attempt record
    attempt = Attempt(
        student_id=exam_session.student_id,
        exam_session_id=exam_session.id,
        item_id=item.id,
        correct=request.correct,
        submitted_answer=request.submitted_answer,
        selected_choice=request.selected_choice,
        response_time_ms=request.response_time_ms,
        created_at=datetime.utcnow(),
        meta={"theta_before": float(exam_session.theta)},
    )

    db.add(attempt)
    db.flush()  # Get attempt ID

    # Reconstruct adaptive engine
    engine = _get_adaptive_engine_from_session(exam_session)

    # Record this attempt in engine (updates theta)
    engine.record_attempt(
        item_id=item.id,
        params={"a": float(item.a), "b": float(item.b), "c": float(item.c)},
        correct=request.correct,
    )

    # Get updated theta and SE
    summary = engine.get_session_summary()
    new_theta = summary["current_theta"]
    new_se = summary["standard_error"]

    # Update attempt meta with theta_after
    attempt.meta["theta_after"] = new_theta

    # Update exam session
    exam_session.theta = Decimal(str(new_theta))
    exam_session.standard_error = Decimal(str(new_se))

    # Check termination
    should_terminate = engine.should_stop()
    termination_reason = None
    next_item_response = None

    if should_terminate:
        # Complete the exam
        exam_session.status = "completed"
        exam_session.ended_at = datetime.utcnow()
        exam_session.duration_sec = int(
            (exam_session.ended_at - exam_session.started_at).total_seconds()
        )
        exam_session.score = Decimal(str(_compute_score(exam_session)))

        # Determine termination reason
        if new_se < 0.3:
            termination_reason = "standard_error_threshold"
        elif len(exam_session.attempts) >= summary["max_items"]:
            termination_reason = "max_items_reached"
        else:
            termination_reason = "other"

        exam_session.meta = exam_session.meta or {}
        exam_session.meta["termination_reason"] = termination_reason
    else:
        # Select next item
        next_item = _select_next_item(db, engine, exam_session)
        if next_item:
            next_item_response = ItemResponse(
                id=next_item.id,
                topic=next_item.topic,
                question_text=next_item.question_text,
                meta=next_item.meta,
            )
        else:
            # No more items available
            should_terminate = True
            termination_reason = "no_items_available"
            exam_session.status = "completed"
            exam_session.ended_at = datetime.utcnow()
            exam_session.duration_sec = int(
                (exam_session.ended_at - exam_session.started_at).total_seconds()
            )
            exam_session.score = Decimal(str(_compute_score(exam_session)))

    db.commit()

    return AnswerSubmitResponse(
        attempt_id=attempt.id,
        correct=request.correct,
        current_theta=new_theta,
        standard_error=new_se,
        items_completed=len(exam_session.attempts),
        should_terminate=should_terminate,
        termination_reason=termination_reason,
        next_item=next_item_response,
    )


@router.post("/exams/next", response_model=NextItemResponse)
async def get_next_item(request: NextItemRequest, db: Session = Depends(get_db)):
    """
    Get next item without submitting an answer.

    Useful for:
     - Previewing next question
     - Skipping items
     - Refreshing item after network error

    Returns:
     - Next item with current theta/SE
    """
    # Load exam session
    exam_session = db.execute(
        select(ExamSession)
        .options(joinedload(ExamSession.attempts).joinedload(Attempt.item))
        .where(ExamSession.id == request.exam_session_id)
    ).scalar_one_or_none()

    if not exam_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam session {request.exam_session_id} not found",
        )

    if exam_session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exam session is {exam_session.status}, cannot get next item",
        )

    # Reconstruct engine
    engine = _get_adaptive_engine_from_session(exam_session)

    # Select next item
    next_item = _select_next_item(
        db,
        engine,
        exam_session,
        exclude_topics=request.exclude_topics,
        max_exposure=request.max_exposure,
    )

    if not next_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No suitable items available"
        )

    summary = engine.get_session_summary()

    return NextItemResponse(
        item=ItemResponse(
            id=next_item.id,
            topic=next_item.topic,
            question_text=next_item.question_text,
            meta=next_item.meta,
        ),
        current_theta=summary["current_theta"],
        standard_error=summary["standard_error"],
        items_completed=len(exam_session.attempts),
        max_items=summary["max_items"],
    )


@router.get("/exams/{session_id}", response_model=ExamSessionSummary)
async def get_exam_session(session_id: int, db: Session = Depends(get_db)):
    """
    Get exam session summary with all attempts.

    Returns:
     - Complete session info
     - All attempts with items
     - Final scores and statistics
    """
    # Load session with all relationships
    exam_session = db.execute(
        select(ExamSession)
        .options(
            joinedload(ExamSession.attempts).joinedload(Attempt.item),
            joinedload(ExamSession.student),
        )
        .where(ExamSession.id == session_id)
    ).scalar_one_or_none()

    if not exam_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam session {session_id} not found",
        )

    # Build attempt summaries
    attempt_summaries = [
        AttemptSummary(
            attempt_id=att.id,
            item_id=att.item_id,
            correct=att.correct,
            response_time_ms=att.response_time_ms,
            created_at=att.created_at,
        )
        for att in exam_session.attempts
    ]

    # Get termination reason from meta
    termination_reason = None
    if exam_session.meta:
        termination_reason = exam_session.meta.get("termination_reason")

    return ExamSessionSummary(
        exam_session_id=exam_session.id,
        student_id=exam_session.student_id,
        exam_type=exam_session.exam_type,
        status=exam_session.status,
        started_at=exam_session.started_at,
        ended_at=exam_session.ended_at,
        duration_sec=exam_session.duration_sec,
        final_theta=float(exam_session.theta) if exam_session.theta else None,
        standard_error=(
            float(exam_session.standard_error) if exam_session.standard_error else None
        ),
        score=float(exam_session.score) if exam_session.score else None,
        items_completed=len(exam_session.attempts),
        termination_reason=termination_reason,
        attempts=attempt_summaries,
    )


@router.post("/exams/{session_id}/complete", response_model=ExamSessionSummary)
async def complete_exam_manually(session_id: int, db: Session = Depends(get_db)):
    """
    Manually complete an exam session.

    Use cases:
     - Student wants to stop early
     - Time limit reached
     - Emergency termination

    Returns:
     - Final exam session summary
    """
    # Load session
    exam_session = db.execute(
        select(ExamSession)
        .options(joinedload(ExamSession.attempts))
        .where(ExamSession.id == session_id)
    ).scalar_one_or_none()

    if not exam_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam session {session_id} not found",
        )

    if exam_session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exam session is already {exam_session.status}",
        )

    # Update session
    exam_session.status = "completed"
    exam_session.ended_at = datetime.utcnow()
    exam_session.duration_sec = int(
        (exam_session.ended_at - exam_session.started_at).total_seconds()
    )
    exam_session.score = Decimal(str(_compute_score(exam_session)))

    exam_session.meta = exam_session.meta or {}
    exam_session.meta["termination_reason"] = "manual_completion"

    db.commit()

    # Return summary
    return await get_exam_session(session_id, db)


# ---------------------------------------------------------------------------
# Admin/Debug Endpoints (Optional)
# ---------------------------------------------------------------------------


@router.get("/exams/{session_id}/debug", response_model=Dict[str, Any])
async def get_exam_debug_info(session_id: int, db: Session = Depends(get_db)):
    """
    Get detailed debug information for an exam session.

    Includes:
     - AdaptiveEngine state
     - Item parameters
     - Theta progression
     - Information values

    NOTE: This endpoint should be protected/admin-only in production.
    """
    # Load session with items
    exam_session = db.execute(
        select(ExamSession)
        .options(joinedload(ExamSession.attempts).joinedload(Attempt.item))
        .where(ExamSession.id == session_id)
    ).scalar_one_or_none()

    if not exam_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam session {session_id} not found",
        )

    # Reconstruct engine
    engine = _get_adaptive_engine_from_session(exam_session)
    summary = engine.get_session_summary()

    # Build attempt details with IRT info
    attempt_details = []
    for att in exam_session.attempts:
        if att.item:
            attempt_details.append(
                {
                    "item_id": att.item_id,
                    "correct": att.correct,
                    "item_params": {
                        "a": float(att.item.a),
                        "b": float(att.item.b),
                        "c": float(att.item.c),
                    },
                    "theta_before": att.meta.get("theta_before") if att.meta else None,
                    "theta_after": att.meta.get("theta_after") if att.meta else None,
                    "response_time_ms": att.response_time_ms,
                }
            )

    return {
        "session_id": exam_session.id,
        "status": exam_session.status,
        "engine_summary": summary,
        "attempt_details": attempt_details,
        "final_score": float(exam_session.score) if exam_session.score else None,
    }
