"""
Exam Models - CAT/IRT-ready schema for adaptive testing

This module defines the database schema for exams, items, and sessions
to support Computer Adaptive Testing (CAT) with Item Response Theory (IRT).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base


class Exam(Base):
    """
    Exam metadata - defines a test with title, subject, duration, etc.
    """

    __tablename__ = "exams"

    __table_args__ = {"extend_existing": True}
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    max_questions: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    is_adaptive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    items: Mapped[list["ExamItem"]] = relationship(
        "ExamItem", back_populates="exam", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["ExamSession"]] = relationship(
        "ExamSession", back_populates="exam"
    )


# DISABLED: Duplicate of item.py Item (Primary model)
# class Item(Base):
#     """
#     Item bank - question items with IRT parameters (a, b, c)
#
#     IRT Parameters:
#     - a_discrimination: How well the item distinguishes between abilities
#     - b_difficulty: Item difficulty on the ability scale
#     - c_guessing: Probability of guessing correctly
#     """
#
#     __tablename__ = "items"
#
#     __table_args__ = {"extend_existing": True}
#     id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
#     )
#
#     subject: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
#     stem_html: Mapped[str] = mapped_column(Text, nullable=False)
#
#     # IRT parameters (2PL/3PL model)
#     a_discrimination: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
#     b_difficulty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
#     c_guessing: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
#
#     # Metadata
#     max_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
#     is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
#
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True), default=datetime.utcnow, nullable=False
#     )
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         default=datetime.utcnow,
#         onupdate=datetime.utcnow,
#         nullable=False,
#     )
#
#     options: Mapped[list["ItemOption"]] = relationship(
#         "ItemOption", back_populates="item", cascade="all, delete-orphan"
#     )
#     exams: Mapped[list["ExamItem"]] = relationship("ExamItem", back_populates="item")
#
#
# DISABLED: ItemOption depends on Item class (also disabled)
# DISABLED: ItemOption replaced by ItemChoice in item.py
# class ItemOption(Base):
#     """
#     Multiple choice options for items
#     """
#
#     __tablename__ = "item_options"
#
#     __table_args__ = {"extend_existing": True}
#     id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
#     )
#     item_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False
#     )
#
#     label: Mapped[str] = mapped_column(String(10), nullable=False)  # "A", "B", "C", "D"
#     text_html: Mapped[str] = mapped_column(Text, nullable=False)
#     is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
#
#     item: Mapped["Item"] = relationship("Item", back_populates="options")


class ExamItem(Base):
    """
    Junction table - links exams to their item pool
    CAT engine selects adaptively from this pool
    """

    __tablename__ = "exam_items"
    __table_args__ = (
        UniqueConstraint("exam_id", "item_id", name="uq_exam_item_exam_id_item_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )

    # For fixed-form exams (optional)
    fixed_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    exam: Mapped[Exam] = relationship("Exam", back_populates="items")
    # item: Mapped[Item] = relationship("Item", back_populates="exams")  # Disabled - Item from item.py


class ExamSession(Base):
    """
    Student exam session - tracks CAT/IRT state and progress

    CAT/IRT State:
    - theta: Estimated ability level
    - theta_se: Standard error of theta estimate

    Progress Tracking:
    - questions_answered: Number of questions answered
    - correct_count, wrong_count, omitted_count: Response statistics
    - raw_score, total_score: Scoring metrics
    """

    __tablename__ = "exam_sessions"

    __table_args__ = {"extend_existing": True}
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum("in_progress", "completed", "cancelled", name="exam_session_status"),
        default="in_progress",
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # CAT/IRT state
    theta: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    theta_se: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Progress statistics
    questions_answered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    omitted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    exam: Mapped[Exam] = relationship("Exam", back_populates="sessions")
    responses: Mapped[list["ExamSessionResponse"]] = relationship(
        "ExamSessionResponse", back_populates="session", cascade="all, delete-orphan"
    )


class ExamSessionResponse(Base):
    """
    Individual response record for a session

    Tracks:
    - Student's selected option
    - Correctness
    - Time spent
    - Theta before/after this response (for CAT debugging)
    """

    __tablename__ = "exam_session_responses"

    __table_args__ = {"extend_existing": True}
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    # Temporarily disabled FK to item_options (use item_choices in item.py instead)
    option_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("item_options.id", ondelete="SET NULL"),
        nullable=True,
    )

    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # CAT/IRT tracking
    theta_before: Mapped[float] = mapped_column(Float, nullable=False)
    theta_after: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    session: Mapped[ExamSession] = relationship(
        "ExamSession", back_populates="responses"
    )
    # item: Mapped[Item] = relationship("Item")  # Disabled - Item from item.py
    # option: Mapped[Optional[ItemOption]] = relationship("ItemOption")  # Disabled


class IRTStudentAbility(Base):
    """
    IRT student ability snapshots - persistent theta estimates for dashboards.

    This table stores calibrated theta values from R mirt pipeline for:
    - Student self-view (ability history)
    - Teacher class-view (student rankings)
    - Tutor priority lists (at-risk identification)
    - Parent reports (progress tracking)

    Unlike exam_sessions.theta (live CAT), these are periodic snapshots
    from offline calibration, enabling longitudinal analysis.
    """

    __tablename__ = "irt_student_abilities"

    __table_args__ = {"extend_existing": True}
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="CASCADE"),  # TODO: Adjust based on User model
        nullable=False,
    )

    subject: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    theta: Mapped[float] = mapped_column(Float, nullable=False)
    theta_se: Mapped[float] = mapped_column(Float, nullable=False)

    exam_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="SET NULL"),
        nullable=True,
    )

    calibrated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # TODO: Add relationships when User model available
    # user: Mapped[User] = relationship("User", back_populates="abilities")
    exam: Mapped[Optional[Exam]] = relationship("Exam")
