"""
DreamSeed AI – Adaptive Exam Router (IRT/CAT End-to-End API)

This router connects the core AdaptiveEngine to actual DB models:
 - POST /api/adaptive/start  → Start exam session
 - POST /api/adaptive/answer → Submit attempt + update theta
 - GET  /api/adaptive/next   → Get next item
 - GET  /api/adaptive/status → Get current exam status

This implementation uses:
 - app.models.core_entities (ExamSession, Attempt)
 - app.models.student (Student, Class)
 - app.models.item (Item, ItemChoice)
 - app.core.services.exam_engine (AdaptiveEngine)
 - app.core.database (get_db, synchronous Session)
 - app.core.security (get_current_user)
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List, Dict
from pydantic import BaseModel
import redis.asyncio as redis

# ORM Models
from app.models.student import Student, Class
from app.models.core_entities import Attempt
from app.models.exam_models import ExamSession  # Primary model
from app.models.item import Item, ItemChoice

# Adaptive Engine & Services
from app.core.services.exam_engine import AdaptiveEngine
from app.core.services.adaptive_state_store import AdaptiveEngineStateStore
from app.core.services.item_bank import ItemBankService
from app.core.services.score_utils import summarize_theta

# DB, Auth & Redis
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.redis import get_redis
from app.models.user import User

router = APIRouter(prefix="/api/adaptive", tags=["adaptive-exam"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Redis State Store - Sync Wrapper
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import asyncio
from functools import wraps
import nest_asyncio

# Allow nested event loops (needed for sync functions calling async Redis in FastAPI)
# Only apply if not using uvloop
try:
    import uvloop

    # uvloop is installed, skip nest_asyncio (they conflict)
except ImportError:
    nest_asyncio.apply()


class SyncStateStoreWrapper:
    """
    Synchronous wrapper for AdaptiveEngineStateStore.
    Allows sync endpoints to use async Redis operations.
    Uses nest_asyncio to handle event loop conflicts in FastAPI TestClient.
    """

    def __init__(self, redis_client: redis.Redis):
        self._store = AdaptiveEngineStateStore(redis_client)

    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        # Sync wrapper for async Redis operations
        # Works with FastAPI's sync endpoints running in thread pool
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        if loop and loop.is_running():
            # We're in an async context (FastAPI worker thread)
            # Use anyio's from_thread helper
            from anyio.from_thread import run as anyio_run

            return anyio_run(coro)
        else:
            # No running loop, create new one
            return asyncio.run(coro)

    def load_engine(
        self, exam_session_id: int, initial_theta: float = 0.0
    ) -> AdaptiveEngine:
        """Load engine from Redis (sync)"""
        return self._run_async(self._store.load_engine(exam_session_id, initial_theta))

    def save_engine(
        self, exam_session_id: int, engine: AdaptiveEngine, ttl_sec: int = 3600
    ) -> None:
        """Save engine to Redis (sync)"""
        return self._run_async(
            self._store.save_engine(exam_session_id, engine, ttl_sec)
        )

    def delete_engine(self, exam_session_id: int) -> None:
        """Delete engine from Redis (sync)"""
        return self._run_async(self._store.delete_engine(exam_session_id))

    def exists(self, exam_session_id: int) -> bool:
        """Check if engine exists in Redis (sync)"""
        return self._run_async(self._store.exists(exam_session_id))


def get_state_store(
    redis_client: redis.Redis = Depends(get_redis),
) -> SyncStateStoreWrapper:
    """Get sync wrapper for AdaptiveEngineStateStore"""
    return SyncStateStoreWrapper(redis_client)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Request/Response Models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class StartExamRequest(BaseModel):
    exam_type: str  # placement, practice, mock, official, quiz
    class_id: Optional[int] = None


class StartExamResponse(BaseModel):
    exam_session_id: int
    message: str
    initial_theta: float


class SubmitAnswerRequest(BaseModel):
    exam_session_id: int
    item_id: int
    correct: bool
    selected_choice: Optional[int] = None  # 1-5 for multiple choice
    submitted_answer: Optional[str] = None  # For open-ended
    response_time_ms: Optional[int] = None


class SubmitAnswerResponse(BaseModel):
    attempt_id: int
    theta: float
    standard_error: float
    completed: bool
    message: str


class ItemChoiceResponse(BaseModel):
    choice_num: int
    choice_text: str


class NextItemResponse(BaseModel):
    item_id: int
    question_text: str
    topic: Optional[str]
    choices: List[ItemChoiceResponse]
    current_theta: float
    current_se: Optional[float]
    attempt_count: int
    completed: bool


class ExamStatusResponse(BaseModel):
    exam_session_id: int
    status: str
    exam_type: str
    started_at: datetime
    ended_at: Optional[datetime]
    theta: Optional[float]
    standard_error: Optional[float]
    score: Optional[float]
    duration_sec: Optional[int]
    attempt_count: int
    completed: bool


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def get_student_by_user(user_id: int, db: Session) -> Student:
    """
    Get student record by user_id.

    Args:
        user_id: User ID from authentication
        db: Database session

    Returns:
        Student object

    Raises:
        HTTPException: If student not found
    """
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student record not found for this user",
        )
    return student


# Removed: get_or_create_engine - now handled by state_store.load_engine()
# Removed: restore_engine_state - engine state is now persisted in Redis


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POST /start – Begin adaptive exam
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post("/start", response_model=StartExamResponse)
def start_adaptive_exam(
    request: StartExamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    state_store: SyncStateStoreWrapper = Depends(get_state_store),
):
    """
    Start a new adaptive exam session.

    Args:
        request: Start exam request with exam_type and optional class_id
        db: Database session
        current_user: Authenticated user
        state_store: Redis state store for engine persistence

    Returns:
        Exam session information

    Raises:
        HTTPException: If user is not a student or class not found
    """
    # Verify student role
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can start exams",
        )

    # Get student record
    student = get_student_by_user(current_user.id, db)

    # Validate class if provided
    if request.class_id is not None:
        clazz = db.query(Class).filter(Class.id == request.class_id).first()
        if not clazz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
            )

    # Create exam session
    exam_session = ExamSession(
        student_id=student.id,
        class_id=request.class_id,
        exam_type=request.exam_type,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
        theta=0.0,
        standard_error=None,
    )
    db.add(exam_session)
    db.commit()
    db.refresh(exam_session)

    # Initialize adaptive engine and save to Redis
    engine = AdaptiveEngine(initial_theta=0.0)
    state_store.save_engine(exam_session.id, engine, ttl_sec=7200)  # 2 hour TTL

    return StartExamResponse(
        exam_session_id=exam_session.id,
        message="Adaptive exam started successfully",
        initial_theta=0.0,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POST /answer – Submit answer and update ability
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post("/answer", response_model=SubmitAnswerResponse)
def submit_adaptive_answer(
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    state_store: SyncStateStoreWrapper = Depends(get_state_store),
):
    """
    Submit answer to current item and update ability estimate.

    Args:
        request: Answer submission with item_id, correctness, and response details
        db: Database session
        current_user: Authenticated user
        state_store: Redis state store for engine persistence

    Returns:
        Updated theta, standard error, and completion status

    Raises:
        HTTPException: If session not found, completed, or unauthorized
    """
    # Verify student role
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit answers",
        )

    # Get student record
    student = get_student_by_user(current_user.id, db)

    # Load exam session and verify ownership
    exam_session = (
        db.query(ExamSession)
        .filter(
            ExamSession.id == request.exam_session_id,
            ExamSession.student_id == student.id,
        )
        .first()
    )

    if not exam_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam session not found or unauthorized",
        )

    if exam_session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exam is already {exam_session.status}",
        )

    # Load item parameters
    item = db.query(Item).filter(Item.id == request.item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    # Load engine from Redis
    engine = state_store.load_engine(
        exam_session.id, initial_theta=float(exam_session.theta or 0.0)
    )

    # Record attempt in engine
    params = {
        "a": float(item.a),
        "b": float(item.b),
        "c": float(item.c),
    }
    updated = engine.record_attempt(params, request.correct)

    # Save updated engine to Redis
    state_store.save_engine(exam_session.id, engine, ttl_sec=7200)

    # Save attempt in DB
    attempt = Attempt(
        student_id=student.id,
        exam_session_id=exam_session.id,
        item_id=item.id,
        correct=request.correct,
        selected_choice=request.selected_choice,
        submitted_answer=request.submitted_answer,
        response_time_ms=request.response_time_ms,
        created_at=datetime.now(timezone.utc),
    )
    db.add(attempt)

    # Update exam session
    exam_session.theta = updated["theta"]
    exam_session.standard_error = updated["standard_error"]

    # Check termination condition
    completed = engine.should_stop()
    if completed:
        exam_session.status = "completed"
        exam_session.ended_at = datetime.now(timezone.utc)
        exam_session.duration_sec = int(
            (exam_session.ended_at - exam_session.started_at).total_seconds()
        )

        # Convert theta to scores/grades using score_utils
        summary = summarize_theta(float(exam_session.theta or 0.0))
        exam_session.score = summary["score_0_100"]

        # Store additional score information in meta
        current_meta = exam_session.meta or {}
        if isinstance(current_meta, str):
            import json

            try:
                current_meta = json.loads(current_meta)
            except:
                current_meta = {}

        exam_session.meta = {
            **current_meta,
            "t_score": summary["t_score"],
            "percentile": summary["percentile"],
            "grade_numeric": summary["grade_numeric"],
            "grade_letter": summary["grade_letter"],
        }

        # Delete engine from Redis (exam completed)
        state_store.delete_engine(exam_session.id)

    db.commit()
    db.refresh(attempt)

    return SubmitAnswerResponse(
        attempt_id=attempt.id,
        theta=float(exam_session.theta),
        standard_error=float(exam_session.standard_error or 0.0),
        completed=completed,
        message="Answer submitted successfully" if not completed else "Exam completed",
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GET /next – Provide next item based on engine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/next", response_model=NextItemResponse)
def get_next_item(
    exam_session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    state_store: SyncStateStoreWrapper = Depends(get_state_store),
):
    """
    Get next item based on adaptive algorithm using ItemBank.

    Args:
        exam_session_id: Exam session ID
        db: Database session
        current_user: Authenticated user
        state_store: Redis state store for engine persistence

    Returns:
        Next item with question text, choices, and current ability estimate

    Raises:
        HTTPException: If session not found or unauthorized
    """
    # Verify student role
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can receive next item",
        )

    # Get student record
    student = get_student_by_user(current_user.id, db)

    # Load exam session and verify ownership
    exam_session = (
        db.query(ExamSession)
        .filter(
            ExamSession.id == exam_session_id,
            ExamSession.student_id == student.id,
        )
        .first()
    )

    if not exam_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam session not found or unauthorized",
        )

    if exam_session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exam is already {exam_session.status}. No more items available.",
        )

    # Load engine from Redis
    engine = state_store.load_engine(
        exam_session.id, initial_theta=float(exam_session.theta or 0.0)
    )

    # Get items already attempted
    attempts = (
        db.query(Attempt).filter(Attempt.exam_session_id == exam_session.id).all()
    )
    attempted_ids = [att.item_id for att in attempts if att.item_id is not None]

    # Use ItemBankService to select next item
    item_bank = ItemBankService(db)
    candidates = item_bank.get_candidate_items(
        exam_session_id=exam_session.id,
        theta=engine.theta,
        window=2.0,  # ±2.0 difficulty range
    )

    best_item = item_bank.pick_best_item(candidates) if candidates else None
    next_item_id = best_item["id"] if best_item else None

    if next_item_id is None:
        # No remaining items - complete exam
        exam_session.status = "completed"
        exam_session.ended_at = datetime.now(timezone.utc)
        exam_session.duration_sec = int(
            (exam_session.ended_at - exam_session.started_at).total_seconds()
        )

        # Convert theta to scores/grades using score_utils
        summary = summarize_theta(float(exam_session.theta or 0.0))
        exam_session.score = summary["score_0_100"]

        # Store additional score information in meta
        current_meta = exam_session.meta or {}
        if isinstance(current_meta, str):
            import json

            try:
                current_meta = json.loads(current_meta)
            except:
                current_meta = {}

        exam_session.meta = {
            **current_meta,
            "t_score": summary["t_score"],
            "percentile": summary["percentile"],
            "grade_numeric": summary["grade_numeric"],
            "grade_letter": summary["grade_letter"],
        }

        db.commit()
        state_store.delete_engine(exam_session.id)

        raise HTTPException(
            status_code=status.HTTP_200_OK, detail="No remaining items. Exam completed."
        )

    # Load full item details
    next_item = db.query(Item).filter(Item.id == next_item_id).first()
    if not next_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected item not found in database",
        )

    # Load item choices
    choices = (
        db.query(ItemChoice)
        .filter(ItemChoice.item_id == next_item.id)
        .order_by(ItemChoice.choice_num)
        .all()
    )

    choice_responses = [
        ItemChoiceResponse(
            choice_num=choice.choice_num,
            choice_text=choice.choice_text,
        )
        for choice in choices
    ]

    return NextItemResponse(
        item_id=next_item.id,
        question_text=next_item.question_text,
        topic=next_item.topic,
        choices=choice_responses,
        current_theta=float(exam_session.theta or 0.0),
        current_se=(
            float(exam_session.standard_error) if exam_session.standard_error else None
        ),
        attempt_count=len(attempts),
        completed=False,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GET /status – Get current exam status
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get("/status", response_model=ExamStatusResponse)
def get_exam_status(
    exam_session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current status of an exam session.

    Args:
        exam_session_id: Exam session ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Exam session status and statistics

    Raises:
        HTTPException: If session not found or unauthorized
    """
    # Verify student role
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view exam status",
        )

    # Get student record
    student = get_student_by_user(current_user.id, db)

    # Load exam session and verify ownership
    exam_session = (
        db.query(ExamSession)
        .filter(
            ExamSession.id == exam_session_id,
            ExamSession.student_id == student.id,
        )
        .first()
    )

    if not exam_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam session not found or unauthorized",
        )

    # Count attempts
    attempt_count = (
        db.query(Attempt).filter(Attempt.exam_session_id == exam_session.id).count()
    )

    return ExamStatusResponse(
        exam_session_id=exam_session.id,
        status=exam_session.status,
        exam_type=exam_session.exam_type,
        started_at=exam_session.started_at,
        ended_at=exam_session.ended_at,
        theta=float(exam_session.theta) if exam_session.theta else None,
        standard_error=(
            float(exam_session.standard_error) if exam_session.standard_error else None
        ),
        score=float(exam_session.score) if exam_session.score else None,
        duration_sec=exam_session.duration_sec,
        attempt_count=attempt_count,
        completed=exam_session.status == "completed",
    )
