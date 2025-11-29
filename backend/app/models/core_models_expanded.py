"""
core_models_expanded.py

DreamSeedAI – Expanded Core Models (Aligned with IRT/CAT Engine)

This file refines and extends the main ORM models so that:
 - ExamSession and Attempt integrate naturally with the AdaptiveEngine
 - Item table is included with IRT parameters (a, b, c)
 - student ↔ class, teacher ↔ class relationships are optimized
 - DB structures are ready for adaptive testing sequence

NOTE: This file is a template. Copy/move into `core/models.py` as needed.
      Or use alongside existing models for gradual migration.

Usage:
    from app.models.core_models_expanded import (
        Organization, User, Teacher, Student, Class,
        StudentClassroom, Item, ExamSession, Attempt
    )
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
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
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ---------------------------------------------------------------------------
# Organization (Multi-tenant support)
# ---------------------------------------------------------------------------
# DISABLED: Use app.models.org_models.Organization instead to avoid conflicts
# class Organization(Base):
#     """
#     Organization/Institution model for multi-tenant architecture.
#
#     Attributes:
#         id: Primary key
#         name: Organization name
#         type: Organization type (e.g., 'school', 'tutoring_center')
#         created_at: Timestamp of creation
#         updated_at: Timestamp of last update
#     """
#
#     __tablename__ = "organizations"
#     __table_args__ = {"extend_existing": True}
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(255), nullable=False)
#     type = Column(String(50))
#     created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
#     updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: Primary key
        org_id: Foreign key to organization
        email: Unique email address (indexed)
        username: Optional unique username
        password_hash: Hashed password
        role: User role (student/teacher/parent/admin)
        is_active: Account active status
    """

    __tablename__ = "users"

    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"))

    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # student/teacher/parent/admin
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", backref="users")
    student = relationship("Student", uselist=False, back_populates="user")
    teacher = relationship("Teacher", uselist=False, back_populates="user")


# ---------------------------------------------------------------------------
# Teacher
# ---------------------------------------------------------------------------
# DISABLED: Teacher - use primary model file
# class Teacher(Base):
#     """
#     Teacher profile extending User.

#     Attributes:
#         id: Primary key
#         user_id: Foreign key to users table (unique)
#         org_id: Foreign key to organization
#         subject: Primary subject taught
#         meta: JSON field for additional metadata
#     """

#     __tablename__ = "teachers"

#     __table_args__ = {"extend_existing": True}
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
#     org_id = Column(Integer, ForeignKey("organizations.id"))

#     subject = Column(String(100))
#     meta = Column(JSON)
#     created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

#     # Relationships
#     user = relationship("User", back_populates="teacher")
#     organization = relationship("Organization", backref="teachers")
#     classes = relationship("Class", back_populates="teacher")


# # ---------------------------------------------------------------------------
# # Student
# # ---------------------------------------------------------------------------
class Student(Base):
    """
    Student profile extending User.

    Attributes:
        id: Primary key
        user_id: Foreign key to users table (unique)
        org_id: Foreign key to organization
        grade: Student grade level
        birth_year: Year of birth
        locale: Locale/language preference
        meta: JSON field for additional metadata
    """

    __tablename__ = "students"

    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"))

    grade = Column(String(20))
    birth_year = Column(Integer)
    locale = Column(String(20))
    meta = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="student")
    organization = relationship("Organization", backref="students")

    classes = relationship(
        "Class", secondary="student_classroom", back_populates="students"
    )

    exam_sessions = relationship("ExamSession", back_populates="student")
    attempts = relationship("Attempt", back_populates="student")


# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------
class Class(Base):
    """
    Class/Classroom model.

    Attributes:
        id: Primary key
        org_id: Foreign key to organization
        teacher_id: Foreign key to teacher
        name: Class name
        grade: Grade level
        subject: Subject area
        meta: JSON field for additional metadata
    """

    __tablename__ = "classes"

    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))

    name = Column(String(255), nullable=False)
    grade = Column(String(20))
    subject = Column(String(100))
    meta = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", backref="classes")
    teacher = relationship("Teacher", back_populates="classes")

    students = relationship(
        "Student", secondary="student_classroom", back_populates="classes"
    )

    exam_sessions = relationship("ExamSession", back_populates="clazz")


# ---------------------------------------------------------------------------
# Student-Classroom Association
# ---------------------------------------------------------------------------
# DISABLED: StudentClassroom - use primary model file
# class StudentClassroom(Base):
#     """
#     Many-to-many association table for students and classes.

#     Attributes:
#         student_id: Foreign key to students table (composite primary key)
#         class_id: Foreign key to classes table (composite primary key)
#     """

#     __tablename__ = "student_classroom"

#     __table_args__ = {"extend_existing": True}
#     student_id = Column(Integer, ForeignKey("students.id"), primary_key=True)
#     class_id = Column(Integer, ForeignKey("classes.id"), primary_key=True)


# # ---------------------------------------------------------------------------
# # Item Table (with IRT params)
# # ---------------------------------------------------------------------------
# DISABLED: Item - use primary model file
# class Item(Base):
#     """
#     Test item/problem with IRT (Item Response Theory) parameters.

#     IRT 3PL Model:
#         P(θ) = c + (1 - c) / (1 + exp(-a(θ - b)))

#     Attributes:
#         id: Primary key
#         topic: Subject area or topic
#         a: Discrimination parameter (typically 0.5-2.5)
#         b: Difficulty parameter (typically -3 to +3)
#         c: Guessing parameter (typically 0.1-0.3)
#         question_text: The actual question content
#         explanation: Solution explanation
#         meta: JSON field for additional data (choices, hints, etc.)
#     """

#     __tablename__ = "items"

#     __table_args__ = {"extend_existing": True}
#     id = Column(BigInteger, primary_key=True)
#     topic = Column(String(255))

#     # IRT parameters (3PL model)
#     a = Column(Numeric(6, 3), nullable=False)  # discrimination
#     b = Column(Numeric(6, 3), nullable=False)  # difficulty
#     c = Column(Numeric(6, 3), nullable=False)  # guessing

#     question_text = Column(Text, nullable=False)
#     explanation = Column(Text)
#     meta = Column(JSON)  # choices, hints, images, etc.

#     # Relationships
#     attempts = relationship("Attempt", back_populates="item")


# # ---------------------------------------------------------------------------
# # ExamSession (Adaptive Testing Session)
# # ---------------------------------------------------------------------------
# DISABLED: ExamSession - use primary model file
# class ExamSession(Base):
#     """
#     Exam session model for adaptive testing.

#     Integrates with AdaptiveEngine to track:
#      - Current theta estimate
#      - Standard error
#      - Session status
#      - Adaptive testing state

#     Attributes:
#         id: Primary key
#         student_id: Foreign key to student
#         class_id: Foreign key to class (optional)
#         exam_type: Type of exam (e.g., 'placement', 'practice', 'final')
#         status: Session status ('in_progress', 'completed', 'abandoned')
#         started_at: Session start timestamp
#         ended_at: Session end timestamp
#         score: Final score/percentage
#         duration_sec: Total duration in seconds
#         theta: Final theta (ability) estimate
#         standard_error: Final standard error of theta
#         meta: JSON field for adaptive engine state, item history, etc.
#     """

#     __tablename__ = "exam_sessions"

#     __table_args__ = {"extend_existing": True}
#     id = Column(BigInteger, primary_key=True)
#     student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
#     class_id = Column(Integer, ForeignKey("classes.id"))

#     exam_type = Column(String(50), nullable=False)
#     status = Column(String(20), default="in_progress", nullable=False)

#     started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
#     ended_at = Column(DateTime)

#     score = Column(Numeric(5, 2))
#     duration_sec = Column(Integer)

#     # IRT/CAT tracking
#     theta = Column(Numeric(6, 3))
#     standard_error = Column(Numeric(6, 3))
#     meta = Column(JSON)  # AdaptiveEngine state, item history, termination reason

#     # Relationships
#     student = relationship("Student", back_populates="exam_sessions")
#     clazz = relationship("Class", back_populates="exam_sessions")
#     attempts = relationship(
#         "Attempt", back_populates="exam_session", order_by="Attempt.created_at"
#     )


# # ---------------------------------------------------------------------------
# # Attempt (Individual Item Response)
# # ---------------------------------------------------------------------------
# DISABLED: Attempt - use primary model file
# class Attempt(Base):
#     """
#     Individual item attempt within an exam session.

#     Attributes:
#         id: Primary key
#         student_id: Foreign key to student
#         exam_session_id: Foreign key to exam session
#         item_id: Foreign key to item
#         correct: Whether the answer was correct
#         submitted_answer: Raw answer submitted by student
#         selected_choice: Choice index for multiple choice questions
#         response_time_ms: Time taken to answer in milliseconds
#         created_at: Timestamp of attempt
#         meta: JSON field for additional data (theta at time of attempt, etc.)
#     """

#     __tablename__ = "attempts"

#     __table_args__ = {"extend_existing": True}
#     id = Column(BigInteger, primary_key=True)
#     student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
#     exam_session_id = Column(BigInteger, ForeignKey("exam_sessions.id"), nullable=False)
#     item_id = Column(BigInteger, ForeignKey("items.id"))

#     correct = Column(Boolean, nullable=False)
#     submitted_answer = Column(Text)
#     selected_choice = Column(Integer)
#     response_time_ms = Column(Integer)

#     created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
#     meta = Column(JSON)  # theta_before, theta_after, information, etc.

#     # Relationships
#     student = relationship("Student", back_populates="attempts")
#     exam_session = relationship("ExamSession", back_populates="attempts")
#     item = relationship("Item", back_populates="attempts")
