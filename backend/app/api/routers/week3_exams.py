"""
Week 3 Exam Flow Router - 5 REST API endpoints

Implements the exact API contract defined in examClient.ts:
1. GET /exams/{exam_id} - Get exam details
2. POST /exams/{exam_id}/sessions - Create/resume session
3. GET /exam-sessions/{session_id}/current-question - Get next adaptive question
4. POST /exam-sessions/{session_id}/answer - Submit answer, update θ
5. GET /exam-sessions/{session_id}/summary - Get final results

All endpoints require authentication (student role).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.security import get_current_student
from app.core.users import User
from app.models.exam_models import (
    Exam,
    ExamItem,
    ExamSession,
    ExamSessionResponse,
)
from app.models.item import (
    Item,
    ItemChoice,
)  # Primary models (ItemChoice = ItemOption equivalent)
from app.schemas.week3_exam_schemas import (
    ExamDetailResponse,
    ExamSessionResponse as ExamSessionOut,
    QuestionPayloadResponse,
    QuestionOptionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    ExamResultSummaryResponse,
)
from app.services.week3_cat_service import (
    select_next_item_for_session,
    update_theta_for_response,
    calculate_raw_score,
)


# Two routers to match frontend API structure
exams_router = APIRouter(prefix="/exams", tags=["Week 3 - Exams"])
sessions_router = APIRouter(prefix="/exam-sessions", tags=["Week 3 - Exam Sessions"])


# ===== 1. GET /exams/{exam_id} - Exam Detail =====


@exams_router.get("/{exam_id}", response_model=ExamDetailResponse)
async def get_exam_detail(
    exam_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_student),
):
    """
    Get exam details.

    Matches: fetchExamDetail(examId) in examClient.ts

    Returns:
    - Exam title, description, subject
    - Duration in minutes
    - Total questions available
    - Status (upcoming/in_progress/completed)
    """
    # Load exam
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Count total questions in pool
    total_questions_result = await db.execute(
        select(func.count(ExamItem.id)).where(ExamItem.exam_id == exam.id)
    )
    total_questions = total_questions_result.scalar_one() or exam.max_questions

    # Determine status (simple logic for alpha)
    # TODO: In future, check scheduled_at timestamp
    status = "in_progress"  # For alpha, all exams are available

    return ExamDetailResponse(
        id=exam.id,
        title=exam.title,
        description=exam.description,
        subject=exam.subject,
        durationMinutes=exam.duration_minutes,
        totalQuestions=total_questions,
        status=status,
    )


# ===== 2. POST /exams/{exam_id}/sessions - Create/Resume Session =====


@exams_router.post("/{exam_id}/sessions", response_model=ExamSessionOut)
async def create_or_resume_session(
    exam_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_student),
):
    """
    Create new exam session or resume existing in-progress session.

    Matches: createOrResumeSession(examId) in examClient.ts

    Returns:
    - Session ID
    - Exam ID
    - Started timestamp
    - Ends timestamp (optional, based on duration)
    - Status
    """
    # Check if exam exists
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Check for existing in-progress session
    result = await db.execute(
        select(ExamSession)
        .where(
            ExamSession.exam_id == exam_id,
            ExamSession.user_id == current_user.id,
            ExamSession.status == "in_progress",
        )
        .order_by(ExamSession.started_at.desc())
    )
    existing_session = result.scalar_one_or_none()

    if existing_session:
        # Resume existing session
        ends_at = None
        if exam.duration_minutes > 0:
            ends_at = (
                existing_session.started_at + timedelta(minutes=exam.duration_minutes)
            ).isoformat()

        return ExamSessionOut(
            id=existing_session.id,
            examId=existing_session.exam_id,
            startedAt=existing_session.started_at.isoformat(),
            endsAt=ends_at,
            status=existing_session.status,
        )

    # Create new session
    now = datetime.utcnow()
    session_obj = ExamSession(
        exam_id=exam.id,
        user_id=current_user.id,
        status="in_progress",
        started_at=now,
        last_activity_at=now,
        theta=0.0,
        theta_se=1.0,
        questions_answered=0,
        correct_count=0,
        wrong_count=0,
        omitted_count=0,
        raw_score=0.0,
        total_score=float(exam.max_questions),  # Assuming 1 point per question
    )
    db.add(session_obj)
    await db.commit()
    await db.refresh(session_obj)

    ends_at = None
    if exam.duration_minutes > 0:
        ends_at = (now + timedelta(minutes=exam.duration_minutes)).isoformat()

    return ExamSessionOut(
        id=session_obj.id,
        examId=session_obj.exam_id,
        startedAt=session_obj.started_at.isoformat(),
        endsAt=ends_at,
        status=session_obj.status,
    )


# ===== 3. GET /exam-sessions/{session_id}/current-question - Next Question =====


@sessions_router.get(
    "/{session_id}/current-question", response_model=QuestionPayloadResponse
)
async def get_current_question(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_student),
):
    """
    Get next adaptive question based on CAT algorithm.

    Matches: fetchCurrentQuestion(sessionId) in examClient.ts

    Returns:
    - Question ID, stem HTML, options
    - Current progress (questionIndex / totalQuestions)
    - Time remaining (optional)

    Raises:
    - 404 "no_more_questions" when exam is complete
    """
    # Load session
    result = await db.execute(
        select(ExamSession)
        .where(
            ExamSession.id == session_id,
            ExamSession.user_id == current_user.id,
        )
        .options(selectinload(ExamSession.exam))
    )
    exam_session = result.scalar_one_or_none()
    if not exam_session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    if exam_session.status != "in_progress":
        raise HTTPException(
            status_code=400,
            detail="Exam session is not in progress",
        )

    exam = exam_session.exam

    # Load exam items (pool)
    exam_items_result = await db.execute(
        select(ExamItem)
        .where(ExamItem.exam_id == exam.id)
        .options(selectinload(ExamItem.item))
    )
    exam_items = list(exam_items_result.scalars().all())

    # Load responses
    responses_result = await db.execute(
        select(ExamSessionResponse)
        .where(ExamSessionResponse.session_id == exam_session.id)
        .order_by(ExamSessionResponse.question_index)
    )
    responses = list(responses_result.scalars().all())

    # CAT: Select next item
    cat_result = await select_next_item_for_session(
        exam, exam_session, responses, exam_items
    )

    if cat_result is None or cat_result.terminate:
        # No more questions or termination criteria met
        raise HTTPException(
            status_code=404,
            detail="no_more_questions",
        )

    item = cat_result.item

    # Load options
    options_result = await db.execute(
        select(ItemOption)
        .where(ItemOption.item_id == item.id)
        .order_by(ItemOption.label)
    )
    options = list(options_result.scalars().all())

    # Calculate progress
    total_questions = exam.max_questions
    question_index = len(responses) + 1

    # Calculate time remaining (optional)
    time_remaining_seconds: Optional[int] = None
    if exam.duration_minutes > 0:
        elapsed = (datetime.utcnow() - exam_session.started_at).total_seconds()
        total_duration = exam.duration_minutes * 60
        remaining = int(total_duration - elapsed)
        if remaining > 0:
            time_remaining_seconds = remaining
        else:
            time_remaining_seconds = 0

    return QuestionPayloadResponse(
        id=item.id,
        stemHtml=item.stem_html,
        options=[
            QuestionOptionResponse(id=o.id, label=o.label, text=o.text_html)
            for o in options
        ],
        questionIndex=question_index,
        totalQuestions=total_questions,
        timeRemainingSeconds=time_remaining_seconds,
    )


# ===== 4. POST /exam-sessions/{session_id}/answer - Submit Answer =====


@sessions_router.post("/{session_id}/answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    session_id: uuid.UUID,
    payload: SubmitAnswerRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_student),
):
    """
    Submit answer and update theta.

    Matches: submitAnswer(sessionId, questionId, optionId) in examClient.ts

    Returns:
    - Whether answer was correct
    - Explanation HTML (optional)

    Side effects:
    - Creates ExamSessionResponse record
    - Updates session theta, theta_se
    - Updates session statistics (correct_count, etc.)
    """
    # Load session
    result = await db.execute(
        select(ExamSession)
        .where(
            ExamSession.id == session_id,
            ExamSession.user_id == current_user.id,
        )
        .options(selectinload(ExamSession.exam))
    )
    exam_session = result.scalar_one_or_none()
    if not exam_session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    if exam_session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Exam session is not in progress")

    # Load item
    item_result = await db.execute(select(Item).where(Item.id == payload.question_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Load selected option
    option_result = await db.execute(
        select(ItemOption).where(
            ItemOption.id == payload.selected_option_id,
            ItemOption.item_id == item.id,
        )
    )
    option = option_result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=404, detail="Selected option not found")

    # Check correctness
    is_correct = option.is_correct

    # Load all responses (need full history for EAP)
    responses_result = await db.execute(
        select(ExamSessionResponse)
        .where(ExamSessionResponse.session_id == exam_session.id)
        .join(Item, ExamSessionResponse.item_id == Item.id)
        .options(selectinload(ExamSessionResponse.item))
        .order_by(ExamSessionResponse.question_index)
    )
    responses = list(responses_result.scalars().all())
    question_index = len(responses) + 1

    # Update theta using mirt-aligned EAP (passes full response history)
    theta_before = exam_session.theta
    new_theta, new_theta_se = await update_theta_for_response(
        exam_session, responses, item, is_correct
    )

    # Create response record
    response_obj = ExamSessionResponse(
        session_id=exam_session.id,
        item_id=item.id,
        option_id=option.id,
        question_index=question_index,
        is_correct=is_correct,
        time_spent_seconds=payload.time_spent_seconds,
        theta_before=theta_before,
        theta_after=new_theta,
    )
    db.add(response_obj)

    # Update session
    exam_session.theta = new_theta
    exam_session.theta_se = new_theta_se
    exam_session.questions_answered = question_index
    exam_session.last_activity_at = datetime.utcnow()

    if is_correct:
        exam_session.correct_count += 1
        exam_session.raw_score += item.max_score
    else:
        exam_session.wrong_count += 1

    await db.commit()
    await db.refresh(exam_session)

    # TODO: Load explanation from item or separate table
    explanation_html = None

    return SubmitAnswerResponse(
        correct=is_correct,
        explanationHtml=explanation_html,
    )


# ===== 5. GET /exam-sessions/{session_id}/summary - Results =====


@sessions_router.get("/{session_id}/summary", response_model=ExamResultSummaryResponse)
async def get_exam_session_summary(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_student),
):
    """
    Get final exam results.

    Matches: fetchExamResult(sessionId) in examClient.ts

    Returns:
    - Session ID, exam ID
    - Score, total score
    - Correct/wrong/omitted counts

    Side effects:
    - Marks session as "completed" if not already
    """
    # Load session
    result = await db.execute(
        select(ExamSession).where(
            ExamSession.id == session_id,
            ExamSession.user_id == current_user.id,
        )
    )
    exam_session = result.scalar_one_or_none()
    if not exam_session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    # Load responses to recalculate statistics
    responses_result = await db.execute(
        select(ExamSessionResponse).where(
            ExamSessionResponse.session_id == exam_session.id
        )
    )
    responses = list(responses_result.scalars().all())

    # Recalculate raw score
    raw_score = await calculate_raw_score(exam_session, responses)

    # Mark as completed
    if exam_session.status != "completed":
        exam_session.status = "completed"
        exam_session.completed_at = datetime.utcnow()
        exam_session.raw_score = raw_score
        await db.commit()
        await db.refresh(exam_session)

    return ExamResultSummaryResponse(
        sessionId=exam_session.id,
        examId=exam_session.exam_id,
        score=exam_session.raw_score,
        totalScore=exam_session.total_score,
        correctCount=exam_session.correct_count,
        wrongCount=exam_session.wrong_count,
        omittedCount=exam_session.omitted_count,
    )
