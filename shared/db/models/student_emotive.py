"""
Student Emotive Dashboard Models
=================================
Multitenant + RBAC models for student mood tracking, daily logs, goals, and AI messages.

Tables:
- student_mood: Daily mood tracking (happy/neutral/sad)
- student_daily_log: Study minutes, tasks done, theta delta
- student_goal: Student goals with target dates
- student_ai_message: AI-generated encouragement messages
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Integer,
    String,
    Date,
    DateTime,
    Float,
    JSON,
    Index,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
import uuid

Base = declarative_base()


# Helper functions for common column patterns
def _uuid():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _tenant():
    return mapped_column(UUID(as_uuid=True), index=True)


def _student():
    return mapped_column(UUID(as_uuid=True), index=True)


class StudentMood(Base):
    """
    Daily mood tracking for students.

    Unique constraint: One mood entry per student per day per tenant.
    """

    __tablename__ = "student_mood"

    id = _uuid()
    tenant_id = _tenant()
    student_id = _student()
    day: Mapped[date] = mapped_column(Date, index=True)
    mood: Mapped[str] = mapped_column(String(8))  # happy|neutral|sad
    note: Mapped[Optional[str]] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "day", name="uq_mood_tenant_student_day"
        ),
        Index("ix_mood_tenant_student_day", "tenant_id", "student_id", "day"),
    )


class StudentDailyLog(Base):
    """
    Daily activity log for students.

    Tracks study time, completed tasks, and IRT theta changes.
    Unique constraint: One log entry per student per day per tenant.
    """

    __tablename__ = "student_daily_log"

    id = _uuid()
    tenant_id = _tenant()
    student_id = _student()
    day: Mapped[date] = mapped_column(Date, index=True)
    study_minutes: Mapped[int] = mapped_column(Integer, default=0)
    tasks_done: Mapped[int] = mapped_column(Integer, default=0)
    theta_delta: Mapped[float] = mapped_column(Float, default=0.0)
    reflections: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "day", name="uq_log_tenant_student_day"
        ),
        Index("ix_log_tenant_student_day", "tenant_id", "student_id", "day"),
    )


class StudentGoal(Base):
    """
    Student goals with optional target dates.

    Students can set personal learning goals and mark them as done.
    """

    __tablename__ = "student_goal"

    id = _uuid()
    tenant_id = _tenant()
    student_id = _student()
    title: Mapped[str] = mapped_column(String(200))
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "ix_goal_tenant_student_created", "tenant_id", "student_id", "created_at"
        ),
    )


class StudentAIMessage(Base):
    """
    AI-generated encouragement messages for students.

    Cached daily messages with tone (warm/gentle) and metadata.
    Unique constraint: One message per student per day per tenant.
    """

    __tablename__ = "student_ai_message"

    id = _uuid()
    tenant_id = _tenant()
    student_id = _student()
    day: Mapped[date] = mapped_column(Date, index=True)
    message: Mapped[str] = mapped_column(String(1000))
    tone: Mapped[str] = mapped_column(String(24), default="warm")
    meta: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "day", name="uq_msg_tenant_student_day"
        ),
        Index("ix_msg_tenant_student_day", "tenant_id", "student_id", "day"),
    )
