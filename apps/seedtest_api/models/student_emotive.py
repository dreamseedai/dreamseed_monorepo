"""Student Emotive Dashboard Models (TEXT-based IDs)

Tables for student-facing dashboard:
- student_mood: Daily mood tracking (happy/neutral/sad)
- student_daily_log: Study minutes, tasks, theta delta, reflections
- student_goal: Personal goals with target dates
- student_ai_message: AI-generated encouragement messages

All tables use:
- TEXT-based IDs (not UUID)
- tenant_id + student_id for multitenancy
- Composite indexes for performance
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    String,
    Date,
    DateTime,
    Float,
    Integer,
    Boolean,
    JSON,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from apps.seedtest_api.models.base import Base


class StudentMood(Base):
    """Daily mood tracking for students

    Tracks student's emotional state each day with optional notes.
    One record per student per day (enforced by unique constraint).
    """

    __tablename__ = "student_mood"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, server_default=text("gen_random_uuid()::text")
    )
    tenant_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    student_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    day: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    mood: Mapped[str] = mapped_column(
        String(8), nullable=False
    )  # 'happy' | 'neutral' | 'sad'
    note: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "day", name="uq_mood_tenant_student_day"
        ),
        Index("ix_mood_tenant_student_day", "tenant_id", "student_id", "day"),
    )


class StudentDailyLog(Base):
    """Daily learning activity log

    Tracks quantitative learning metrics:
    - study_minutes: Total study time
    - tasks_done: Number of completed tasks
    - theta_delta: IRT ability change
    - reflections: Free-form text notes
    """

    __tablename__ = "student_daily_log"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, server_default=text("gen_random_uuid()::text")
    )
    tenant_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    student_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    day: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    study_minutes: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    tasks_done: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    theta_delta: Mapped[float] = mapped_column(
        Float, server_default="0.0", nullable=False
    )
    reflections: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "day", name="uq_log_tenant_student_day"
        ),
        Index("ix_log_tenant_student_day", "tenant_id", "student_id", "day"),
    )


class StudentGoal(Base):
    """Personal learning goals

    Students can set goals with optional target dates.
    Goals can be marked as done (completed).
    """

    __tablename__ = "student_goal"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, server_default=text("gen_random_uuid()::text")
    )
    tenant_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    student_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("now()"))

    __table_args__ = (
        Index(
            "ix_goal_tenant_student_created", "tenant_id", "student_id", "created_at"
        ),
    )


class StudentAIMessage(Base):
    """AI-generated encouragement messages

    Cached daily messages generated based on:
    - Recent performance (theta_delta)
    - Mood history
    - Learning patterns

    One message per student per day (cached to avoid regeneration).
    """

    __tablename__ = "student_ai_message"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, server_default=text("gen_random_uuid()::text")
    )
    tenant_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    student_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    day: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    tone: Mapped[str] = mapped_column(
        String(24), server_default="'warm'", nullable=False
    )  # 'warm' | 'gentle' | 'energetic'
    meta: Mapped[dict] = mapped_column(
        JSON, server_default="{}", nullable=False
    )  # Metadata (e.g., generation context)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "day", name="uq_msg_tenant_student_day"
        ),
        Index("ix_msg_tenant_student_day", "tenant_id", "student_id", "day"),
    )
