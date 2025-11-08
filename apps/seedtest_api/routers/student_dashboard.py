"""Student Dashboard API Router (Multitenant + RBAC: student role)

Endpoints for student-facing emotive dashboard:
- GET /api/student/dashboard: Main dashboard data (growth, mood, streak, goals, AI message)
- POST /api/student/mood: Set today's mood
- POST /api/student/goals: Create new goal
- POST /api/student/goals/{goal_id}/done: Mark goal as complete

All endpoints require 'student' role and automatically scope to user's tenant_id.
"""
from __future__ import annotations
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from apps.seedtest_api.db.session import get_db
from apps.seedtest_api.models.student_emotive import (
    StudentMood,
    StudentDailyLog,
    StudentGoal,
    StudentAIMessage
)
from apps.seedtest_api.auth.deps import UserContext, require_role
from apps.seedtest_api.services.ai_empathy import make_message

router = APIRouter(prefix='/api/student', tags=['student'])


# ============================================================================
# Response Models
# ============================================================================

class GoalOut(BaseModel):
    """Goal response schema"""
    id: str
    title: str
    target_date: Optional[str] = None
    done: bool
    
    class Config:
        from_attributes = True


class DashboardOut(BaseModel):
    """Main dashboard response"""
    week_growth: float = Field(..., description="7-day average theta delta (IRT ability change)")
    today_mood: Optional[str] = Field(None, description="Today's mood: 'happy' | 'neutral' | 'sad'")
    streak_days: int = Field(..., description="Consecutive days with learning activity")
    goals: List[GoalOut] = Field(..., description="Active (not done) goals, max 5 recent")
    ai_message: Optional[str] = Field(None, description="AI-generated encouragement message")
    ai_tone: Optional[str] = Field(None, description="Message tone: 'warm' | 'gentle' | 'energetic'")


# ============================================================================
# Main Dashboard Endpoint
# ============================================================================

@router.get('/dashboard', response_model=DashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("student"))
):
    """Get student dashboard data
    
    Returns:
    - week_growth: 7-day average theta delta from IRT snapshots
    - today_mood: Mood logged today (if any)
    - streak_days: Consecutive days with daily log entries
    - goals: Active goals (done=False), up to 5 most recent
    - ai_message: Cached or newly generated encouragement
    - ai_tone: Message tone for UI styling
    
    All data is automatically scoped to current user's tenant_id + student_id.
    """
    today = date.today()
    
    # Calculate 7-day growth (from daily logs, not IRT snapshots for now)
    # TODO: Integrate with IrtSnapshot if available
    week_start = today - timedelta(days=7)
    logs_7d = db.execute(
        select(func.avg(StudentDailyLog.theta_delta))
        .where(
            and_(
                StudentDailyLog.tenant_id == user.tenant_id,
                StudentDailyLog.student_id == user.user_id,
                StudentDailyLog.day >= week_start,
                StudentDailyLog.day <= today
            )
        )
    ).scalar()
    week_growth = float(logs_7d or 0.0)
    
    # Get today's mood
    mood_row = db.execute(
        select(StudentMood)
        .where(
            and_(
                StudentMood.tenant_id == user.tenant_id,
                StudentMood.student_id == user.user_id,
                StudentMood.day == today
            )
        )
    ).scalar_one_or_none()
    today_mood = mood_row.mood if mood_row else None
    
    # Calculate streak (consecutive days with daily log)
    all_log_days = db.execute(
        select(StudentDailyLog.day)
        .where(
            and_(
                StudentDailyLog.tenant_id == user.tenant_id,
                StudentDailyLog.student_id == user.user_id
            )
        )
        .order_by(StudentDailyLog.day.desc())
        .limit(30)
    ).scalars().all()
    
    streak_days = 0
    check_date = today
    for _ in range(30):
        if check_date in all_log_days:
            streak_days += 1
            check_date = check_date - timedelta(days=1)
        else:
            break
    
    # Get active goals (done=False), max 5 recent
    goals = db.execute(
        select(StudentGoal)
        .where(
            and_(
                StudentGoal.tenant_id == user.tenant_id,
                StudentGoal.student_id == user.user_id,
                StudentGoal.done.is_(False)
            )
        )
        .order_by(StudentGoal.created_at.desc())
        .limit(5)
    ).scalars().all()
    
    goals_out = [
        GoalOut(
            id=g.id,
            title=g.title,
            target_date=g.target_date.isoformat() if g.target_date else None,
            done=g.done
        )
        for g in goals
    ]
    
    # Get or generate AI message (cached by day)
    cached_msg = db.execute(
        select(StudentAIMessage)
        .where(
            and_(
                StudentAIMessage.tenant_id == user.tenant_id,
                StudentAIMessage.student_id == user.user_id,
                StudentAIMessage.day == today
            )
        )
    ).scalar_one_or_none()
    
    if cached_msg:
        ai_message = cached_msg.message
        ai_tone = cached_msg.tone
    else:
        # Generate new message
        msg_obj = make_message(
            theta_delta_7d=week_growth,
            mood=today_mood,  # type: ignore
            streak_days=streak_days
        )
        ai_message = msg_obj.text
        ai_tone = msg_obj.tone
        
        # Cache for today
        new_msg = StudentAIMessage(
            tenant_id=user.tenant_id,
            student_id=user.user_id,
            day=today,
            message=ai_message,
            tone=ai_tone,
            meta=msg_obj.context
        )
        db.add(new_msg)
        db.commit()
    
    return DashboardOut(
        week_growth=week_growth,
        today_mood=today_mood,
        streak_days=streak_days,
        goals=goals_out,
        ai_message=ai_message,
        ai_tone=ai_tone
    )


# ============================================================================
# Mood Tracking
# ============================================================================

class MoodIn(BaseModel):
    """Mood input schema"""
    mood: str = Field(..., pattern="^(happy|neutral|sad)$", description="Mood: 'happy' | 'neutral' | 'sad'")
    note: Optional[str] = Field(None, max_length=512, description="Optional note about mood")


@router.post('/mood')
def set_mood(
    payload: MoodIn,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("student"))
):
    """Set today's mood
    
    Updates existing mood record or creates new one.
    One mood per student per day (upsert behavior).
    """
    today = date.today()
    
    # Try to find existing mood for today
    existing = db.execute(
        select(StudentMood)
        .where(
            and_(
                StudentMood.tenant_id == user.tenant_id,
                StudentMood.student_id == user.user_id,
                StudentMood.day == today
            )
        )
    ).scalar_one_or_none()
    
    if existing:
        # Update existing
        existing.mood = payload.mood
        existing.note = payload.note
    else:
        # Create new
        new_mood = StudentMood(
            tenant_id=user.tenant_id,
            student_id=user.user_id,
            day=today,
            mood=payload.mood,
            note=payload.note
        )
        db.add(new_mood)
    
    db.commit()
    return {"ok": True, "mood": payload.mood}


# ============================================================================
# Goals Management
# ============================================================================

class GoalIn(BaseModel):
    """Goal creation input"""
    title: str = Field(..., min_length=1, max_length=200, description="Goal title")
    target_date: Optional[date] = Field(None, description="Target completion date (optional)")


@router.post('/goals')
def add_goal(
    payload: GoalIn,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("student"))
):
    """Create new goal
    
    Returns newly created goal ID.
    """
    goal = StudentGoal(
        tenant_id=user.tenant_id,
        student_id=user.user_id,
        title=payload.title,
        target_date=payload.target_date
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    return {"id": goal.id, "title": goal.title}


@router.post('/goals/{goal_id}/done')
def complete_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("student"))
):
    """Mark goal as complete
    
    Returns 404 if goal doesn't exist or doesn't belong to current user.
    """
    goal = db.execute(
        select(StudentGoal)
        .where(
            and_(
                StudentGoal.id == goal_id,
                StudentGoal.tenant_id == user.tenant_id,
                StudentGoal.student_id == user.user_id
            )
        )
    ).scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    goal.done = True
    db.commit()
    
    return {"ok": True, "goal_id": goal_id}


@router.delete('/goals/{goal_id}')
def delete_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("student"))
):
    """Delete goal
    
    Returns 404 if goal doesn't exist or doesn't belong to current user.
    """
    goal = db.execute(
        select(StudentGoal)
        .where(
            and_(
                StudentGoal.id == goal_id,
                StudentGoal.tenant_id == user.tenant_id,
                StudentGoal.student_id == user.user_id
            )
        )
    ).scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db.delete(goal)
    db.commit()
    
    return {"ok": True, "deleted_id": goal_id}
