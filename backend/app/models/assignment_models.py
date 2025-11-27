"""
Assignment and Submission models for homework management system.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class Assignment(Base):
    """Assignment model - represents homework, quizzes, tests, or projects."""

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    teacher_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    class_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    assignment_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # homework, quiz, test, project
    template_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    total_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    assigned_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="active", index=True
    )
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    assignment_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    assignment_students: Mapped[List["AssignmentStudent"]] = relationship(
        "AssignmentStudent", back_populates="assignment", cascade="all, delete-orphan"
    )
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "assignment_type IN ('homework', 'quiz', 'test', 'project')",
            name="ck_assignment_type",
        ),
        CheckConstraint(
            "status IN ('active', 'archived', 'draft')", name="ck_assignment_status"
        ),
    )


class AssignmentStudent(Base):
    """Junction table for many-to-many relationship between assignments and students."""

    __tablename__ = "assignment_students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assignment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    notified: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )

    # Relationships
    assignment: Mapped["Assignment"] = relationship(
        "Assignment", back_populates="assignment_students"
    )

    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student"),
    )


class Submission(Base):
    """Submission model - represents a student's submission for an assignment."""

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assignment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submission_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    is_late: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="submitted", index=True
    )
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    graded_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rubric_scores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    submission_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    assignment: Mapped["Assignment"] = relationship(
        "Assignment", back_populates="submissions"
    )
    history: Mapped[List["SubmissionHistory"]] = relationship(
        "SubmissionHistory", back_populates="submission", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "assignment_id", "student_id", name="uq_submission_assignment_student"
        ),
        CheckConstraint(
            "status IN ('submitted', 'graded', 'returned')", name="ck_submission_status"
        ),
    )


class SubmissionHistory(Base):
    """Submission history model - tracks revisions of submissions."""

    __tablename__ = "submission_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    submission_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    submission: Mapped["Submission"] = relationship(
        "Submission", back_populates="history"
    )
