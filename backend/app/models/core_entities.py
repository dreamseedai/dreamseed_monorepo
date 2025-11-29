"""
Core entity models for DreamSeed CAT System (INTEGER-based)

This module defines the comprehensive data model including:
- Organizations (multi-tenancy)
- Teachers (extends users table)
- ExamSessions (CAT exam instances with IRT results)
- Attempts (item-level responses)
- StudentClassroom (N:N junction)

These models use INTEGER primary keys for better performance and
compatibility with existing systems. They integrate with existing
User, Student, and Class models.

These reuse the existing Base from app.core.database so that Alembic
can discover them if needed and FastAPI services can import them
alongside existing models.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


# DISABLED: Use app.models.org_models.Organization instead to avoid conflicts
# class Organization(Base):
#     """
#     Organization entity for multi-tenancy support.
#
#     Examples:
#     - Schools (public, private)
#     - Academies (cram schools, hagwon)
#     - Tutoring centers
#     - Individual teachers/tutors
#     """
#
#     __tablename__ = "organizations"
#     __table_args__ = {"extend_existing": True}
#
#     id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     name = Column(String(255), nullable=False)
#     type = Column(String(50), nullable=True)  # 'school', 'academy', 'tutoring_center'
#     created_at = Column(
#         DateTime(timezone=True), server_default=func.now(), nullable=False
#     )
#     updated_at = Column(
#         DateTime(timezone=True),
#         server_default=func.now(),
#         onupdate=func.now(),
#         nullable=False,
#     )
#
#     # Relationships
#     teachers = relationship("Teacher", back_populates="organization")
#
#     def __repr__(self):
#         return f"<Organization(id={self.id}, name={self.name}, type={self.type})>"


class Teacher(Base):
    """
    Teacher profile extending the User table.

    Contains teacher-specific attributes like:
    - Subject expertise
    - Certifications (in meta JSONB)
    - Teaching style preferences

    Links to existing users table via user_id foreign key.
    """

    __tablename__ = "teachers"

    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    subject = Column(
        String(100), nullable=True
    )  # Primary subject: 'math', 'english', 'science', etc.
    meta = Column(
        JSON, nullable=True
    )  # Certifications, bio, teaching preferences, etc.
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    # organization = relationship("Organization", back_populates="teachers")  # Disabled - Organization model moved to org_models.py

    def __repr__(self):
        return (
            f"<Teacher(id={self.id}, user_id={self.user_id}, subject={self.subject})>"
        )


class StudentClassroom(Base):
    """
    Junction table for N:N relationship between students and classes.

    A student can be enrolled in multiple classes.
    A class contains multiple students.

    Tracks enrollment timestamp for historical analysis.

    Note: This exists alongside the earlier student_classes table and can be
    used for new core flows without breaking existing code.
    """

    __tablename__ = "student_classroom"

    __table_args__ = {"extend_existing": True}
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    class_id = Column(
        Integer,
        ForeignKey("classes.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    enrolled_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<StudentClassroom(student_id={self.student_id}, class_id={self.class_id})>"


# DISABLED: Duplicate of exam_models.ExamSession (Primary model)
# class ExamSession(Base):
#     """
#     A single CAT (Computerized Adaptive Testing) exam session.
#
#     Tracks:
#     - Student taking the exam
#     - Class context (if applicable)
#     - Exam type and status
#     - IRT results (theta, standard error)
#     - Final score and duration
#
#     Exam Types:
#     - placement: Initial ability assessment
#     - practice: Low-stakes practice test
#     - mock: Simulated exam
#     - official: High-stakes graded exam
#     - quiz: Short formative assessment
#
#     IRT Fields:
#     - theta: Ability estimate (typically -3 to +3, mean=0, sd=1)
#     - standard_error: Precision of theta (lower = more accurate)
#     """
#
#     __tablename__ = "exam_sessions"
#
#     __table_args__ = {"extend_existing": True}
#     id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
#     student_id = Column(
#         Integer,
#         ForeignKey("students.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True,
#     )
#     class_id = Column(
#         Integer,
#         ForeignKey("classes.id", ondelete="SET NULL"),
#         nullable=True,
#         index=True,
#     )
#
#     exam_type = Column(
#         String(50), nullable=False, index=True
#     )  # placement, practice, mock, official, quiz
#     status = Column(
#         String(20), nullable=False, default="in_progress", index=True
#     )  # in_progress, completed, abandoned
#
#     started_at = Column(
#         DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
#     )
#     ended_at = Column(DateTime(timezone=True), nullable=True)
#
#     score = Column(Numeric(5, 2), nullable=True)  # Final score (0-100 scale)
#     duration_sec = Column(Integer, nullable=True)  # Total time spent in seconds
#
#     # IRT Results
#     theta = Column(
#         Numeric(6, 3), nullable=True
#     )  # Ability estimate (-3 to +3 typically)
#     standard_error = Column(Numeric(6, 3), nullable=True)  # Precision of theta estimate
#
#     meta = Column(
#         JSON, nullable=True
#     )  # Algorithm config, stopping rule criteria, adaptive history
#
#     # Relationships
#     student = relationship("Student", backref="exam_sessions_core")
#     clazz = relationship("Class", backref="exam_sessions_core")
#     # attempts = relationship(
#     #     "Attempt", back_populates="exam_session", cascade="all, delete-orphan"
#     # )
#
#     def __repr__(self):
#         return f"<ExamSession(id={self.id}, student_id={self.student_id}, exam_type={self.exam_type}, status={self.status})>"


class Attempt(Base):
    """
    Item-level response record within an exam session.

    Captures:
    - Which student answered
    - Which exam session
    - Which item/question
    - Correctness
    - Response content (for different question types)
    - Response time

    Response Types:
    - Multiple choice: Uses selected_choice (1-5)
    - Open-ended: Uses submitted_answer (text)
    - Essay: Uses submitted_answer (long text)

    The item_id links to an items table (to be defined separately)
    containing item parameters (difficulty, discrimination, etc.)
    """

    __tablename__ = "attempts"

    __table_args__ = {"extend_existing": True}
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_session_id = Column(
        BigInteger,
        ForeignKey("exam_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id = Column(
        BigInteger,
        ForeignKey("items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    correct = Column(Boolean, nullable=False)
    submitted_answer = Column(Text, nullable=True)  # Open-ended or essay response
    selected_choice = Column(
        Integer, nullable=True
    )  # Multiple-choice option (1-based index)
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    meta = Column(
        JSON, nullable=True
    )  # Item difficulty, discrimination, partial credit, hints used, etc.

    # Relationships - ExamSession relationship disabled to avoid duplication conflict
    student = relationship("Student", backref="attempts_core")
    # exam_session = relationship("ExamSession", back_populates="attempts")  # Disabled
    # item = relationship("Item", back_populates="attempts")  # Disabled

    def __repr__(self):
        return f"<Attempt(id={self.id}, exam_session_id={self.exam_session_id}, item_id={self.item_id}, correct={self.correct})>"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Export all models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

__all__ = [
    # "Organization",  # Removed - use org_models.Organization
    "Teacher",
    "StudentClassroom",
    # "ExamSession",  # Removed - use exam_models.ExamSession
    "Attempt",  # Re-enabled for item_bank.py (relationships disabled)
]
