"""
Student Dashboard API Router (Hybrid LLM with Accept-Language Priority)
========================================================================
Enhanced version with Accept-Language header priority over JWT.

Language detection priority:
1. Accept-Language header (q-value aware)
2. JWT lang field
3. Default 'en'

Hybrid routing:
- Korean (ko) → Local RTX 5090 (Qwen2.5-7B-Instruct)
- English (en) → Local RTX 5090 (Llama-3.1-8B-Instruct)
- Chinese (zh) → DeepSeek Cloud (deepseek-chat)

Usage:
    # In portal_api/main.py
    from portal_api.routers import student_dashboard_hybrid
    app.include_router(student_dashboard_hybrid.router)
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func

# Import shared modules
from shared.db.models.student_emotive import (
    StudentMood,
    StudentDailyLog,
    StudentGoal,
    StudentAIMessage,
)
from shared.auth.deps_student import require_student, UserContext
from shared.analytics.ai_empathy_llm import make_message_llm
from shared.web.locale import pick_accept_language

# Note: Update this import based on your actual DB session setup
# from shared.db.session import get_db


def get_db():
    """Placeholder for DB session dependency. Replace with actual implementation."""
    raise NotImplementedError("Replace with actual get_db() from shared.db.session")


router = APIRouter(prefix="/api/student", tags=["student"])


# ============================================================================
# Response Models
# ============================================================================


class GoalOut(BaseModel):
    """Goal output model"""

    id: str
    title: str
    target_date: Optional[str] = None
    done: bool = False


class DashboardOut(BaseModel):
    """Dashboard summary response"""

    week_growth: float
    today_mood: Optional[str] = None
    streak_days: int
    goals: List[GoalOut]
    ai_message: Optional[str] = None
    ai_tone: Optional[str] = None


# ============================================================================
# Request Models
# ============================================================================


class MoodIn(BaseModel):
    """Mood input model"""

    mood: str  # happy|neutral|sad
    note: Optional[str] = None


class GoalIn(BaseModel):
    """Goal creation input model"""

    title: str
    target_date: Optional[date] = None


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/dashboard", response_model=DashboardOut)
async def get_dashboard(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_student),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    Get student dashboard summary with hybrid LLM routing.

    Language detection priority:
    1. Accept-Language header (highest q-value)
    2. JWT lang field
    3. Default 'en'

    Returns:
    - week_growth: 7-day average theta delta
    - today_mood: Today's mood (if set)
    - streak_days: Consecutive study days
    - goals: List of open goals
    - ai_message: LLM-generated encouragement message
    - ai_tone: Message tone (warm/gentle/energetic)
    """
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    tenant_uuid = UUID(user.tenant_id)
    student_uuid = UUID(user.user_id)

    # Calculate 7-day growth from IrtSnapshot
    # Note: Adjust table name based on your schema
    week_growth = 0.0
    # rows = db.execute(
    #     select(func.avg(IrtSnapshot.delta_theta))
    #     .where(
    #         IrtSnapshot.tenant_id == tenant_uuid,
    #         IrtSnapshot.student_id == student_uuid,
    #         IrtSnapshot.week_start == week_start
    #     )
    # ).all()
    # week_growth = float(rows[0][0] or 0.0)

    # Get today's mood
    mood_row = (
        db.execute(
            select(StudentMood).where(
                StudentMood.tenant_id == tenant_uuid,
                StudentMood.student_id == student_uuid,
                StudentMood.day == today,
            )
        )
        .scalars()
        .first()
    )
    today_mood = mood_row.mood if mood_row else None

    # Calculate streak: consecutive days with any log
    log_days = (
        db.execute(
            select(StudentDailyLog.day)
            .where(
                StudentDailyLog.tenant_id == tenant_uuid,
                StudentDailyLog.student_id == student_uuid,
            )
            .order_by(StudentDailyLog.day.desc())
            .limit(30)
        )
        .scalars()
        .all()
    )

    streak = 0
    check_date = today
    for _ in range(30):
        if check_date in log_days:
            streak += 1
            check_date = check_date - timedelta(days=1)
        else:
            break

    # Get open goals (not done)
    goal_rows = (
        db.execute(
            select(StudentGoal)
            .where(
                StudentGoal.tenant_id == tenant_uuid,
                StudentGoal.student_id == student_uuid,
                StudentGoal.done == False,
            )
            .order_by(StudentGoal.created_at.desc())
            .limit(5)
        )
        .scalars()
        .all()
    )

    goals = [
        GoalOut(
            id=str(g.id),
            title=g.title,
            target_date=g.target_date.isoformat() if g.target_date else None,
            done=g.done,
        )
        for g in goal_rows
    ]

    # Language detection priority:
    # 1. Accept-Language header (highest priority)
    # 2. JWT lang field
    # 3. Default 'en'
    lang = "en"
    if accept_language:
        # Priority 1: Accept-Language header
        lang = pick_accept_language(accept_language)
    elif hasattr(user, "lang") and user.lang:
        # Priority 2: JWT lang field
        lang = user.lang
    # Priority 3: Default 'en' (already set)    # Get or generate AI message
    # (cached by day)
    cached_msg = (
        db.execute(
            select(StudentAIMessage).where(
                StudentAIMessage.tenant_id == tenant_uuid,
                StudentAIMessage.student_id == student_uuid,
                StudentAIMessage.day == today,
            )
        )
        .scalars()
        .first()
    )

    if cached_msg:
        msg, tone = cached_msg.message, cached_msg.tone
    else:
        # Collect goal titles for LLM context
        goal_titles = [g.title for g in goal_rows[:3]]

        # Generate new message with hybrid LLM routing
        msg, tone = await make_message_llm(
            theta_delta_7d=week_growth,
            mood=today_mood,
            streak_days=streak,
            goal_titles=goal_titles,
            lang=lang,
        )

        # Cache it
        new_msg = StudentAIMessage(
            tenant_id=tenant_uuid,
            student_id=student_uuid,
            day=today,
            message=msg,
            tone=tone,
            meta={
                "week_growth": week_growth,
                "mood": today_mood,
                "lang": lang,
                "streak": streak,
                "goal_count": len(goal_titles),
                "lang_source": (
                    "header"
                    if accept_language
                    else ("jwt" if hasattr(user, "lang") and user.lang else "default")
                ),
            },
        )
        db.add(new_msg)
        db.commit()

    return DashboardOut(
        week_growth=week_growth,
        today_mood=today_mood,
        streak_days=streak,
        goals=goals,
        ai_message=msg,
        ai_tone=tone,
    )


@router.post("/mood")
def set_mood(
    payload: MoodIn,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_student),
):
    """
    Set today's mood.

    Creates or updates mood entry for today.
    """
    today = date.today()
    tenant_uuid = UUID(user.tenant_id)
    student_uuid = UUID(user.user_id)

    # Check if mood already exists for today
    existing = (
        db.execute(
            select(StudentMood).where(
                StudentMood.tenant_id == tenant_uuid,
                StudentMood.student_id == student_uuid,
                StudentMood.day == today,
            )
        )
        .scalars()
        .first()
    )

    if existing:
        # Update existing
        existing.mood = payload.mood
        existing.note = payload.note
    else:
        # Create new
        new_mood = StudentMood(
            tenant_id=tenant_uuid,
            student_id=student_uuid,
            day=today,
            mood=payload.mood,
            note=payload.note,
        )
        db.add(new_mood)

    db.commit()
    return {"ok": True}


@router.post("/goals")
def add_goal(
    payload: GoalIn,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_student),
):
    """
    Add a new goal.

    Returns:
        Goal ID
    """
    tenant_uuid = UUID(user.tenant_id)
    student_uuid = UUID(user.user_id)

    new_goal = StudentGoal(
        tenant_id=tenant_uuid,
        student_id=student_uuid,
        title=payload.title,
        target_date=payload.target_date,
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)

    return {"id": str(new_goal.id)}


@router.post("/goals/{goal_id}/done")
def complete_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_student),
):
    """
    Mark a goal as complete.

    Raises:
        404: Goal not found or doesn't belong to user
    """
    tenant_uuid = UUID(user.tenant_id)
    student_uuid = UUID(user.user_id)

    try:
        goal_uuid = UUID(goal_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid goal ID format"
        )

    goal = db.get(StudentGoal, goal_uuid)

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found"
        )

    # Verify ownership (tenant + student)
    if goal.tenant_id != tenant_uuid or goal.student_id != student_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found"
        )

    goal.done = True
    db.commit()

    return {"ok": True}
