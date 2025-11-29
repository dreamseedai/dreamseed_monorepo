"""
Tutor Domain Models

튜터(가정교사) 도메인 엔티티:
- Tutor: 튜터 프로필
- TutorSession: 튜터링 세션
- TutorNote: 세션 피드백/과제
- TutorSessionTask: 세션 내 TODO
- TutorStudentRelation: 튜터-학생 관계
- TutorAvailability: 가용 시간
- TutorRating: 튜터 평가
"""

from datetime import datetime, time
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Date,
    DateTime,
    Time,
    ForeignKey,
    Boolean,
    Numeric,
    CheckConstraint,
    Index,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Tutor(Base):
    """
    튜터 프로필

    Teacher vs Tutor:
    - Teacher: 학교/학원 소속, 반(class) 관리
    - Tutor: 개인/플랫폼 소속, 1:1 또는 소그룹 지도
    """

    __tablename__ = "tutors"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    subjects = Column(ARRAY(Text))  # ['math', 'physics', 'english']
    bio = Column(Text)
    hourly_rate = Column(Numeric(10, 2))
    years_experience = Column(Integer)
    education = Column(Text)
    certifications = Column(ARRAY(Text))
    available_hours = Column(JSONB)  # {mon: ['09:00-12:00'], ...}
    rating_avg = Column(Numeric(3, 2), default=0.0)
    rating_count = Column(Integer, default=0)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    meta = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", backref="tutor_profile")
    organization = relationship("Organization", backref="tutors")
    student_relations = relationship(
        "TutorStudentRelation", back_populates="tutor", cascade="all, delete-orphan"
    )
    availability_slots = relationship(
        "TutorAvailability", back_populates="tutor", cascade="all, delete-orphan"
    )
    ratings = relationship("TutorRating", back_populates="tutor")

    def __repr__(self):
        return (
            f"<Tutor(id={self.id}, user_id={self.user_id}, subjects={self.subjects})>"
        )


class TutorSession(Base):
    """
    튜터링 세션 기록

    1:1 또는 소그룹 수업 세션
    """

    __tablename__ = "tutor_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tutor_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False, index=True)
    subject = Column(Text)
    topic = Column(Text)
    status = Column(String(20), nullable=False, server_default="upcoming", index=True)
    duration_minutes = Column(Integer)
    mode = Column(String(20))  # 'online', 'offline', 'video', 'chat'
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    notes = Column(Text)
    session_rating = Column(Integer)
    session_feedback = Column(Text)
    meta = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    tutor_user = relationship("User", foreign_keys=[tutor_id])
    student = relationship("Student", backref="tutor_sessions")
    tasks = relationship(
        "TutorSessionTask", back_populates="session", cascade="all, delete-orphan"
    )
    notes_list = relationship(
        "TutorNote", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TutorSession(id={self.id}, date={self.date}, status={self.status})>"


class TutorSessionTask(Base):
    """
    세션 내 TODO 항목

    과제, 준비물, 복습 내용 등
    """

    __tablename__ = "tutor_session_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        Integer, ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False
    )
    label = Column(Text, nullable=False)
    done = Column(Boolean, nullable=False, server_default="false")
    sort_order = Column(Integer, server_default="0")

    # Relationships
    session = relationship("TutorSession", back_populates="tasks")

    def __repr__(self):
        return f"<TutorSessionTask(id={self.id}, label={self.label}, done={self.done})>"


class TutorNote(Base):
    """
    세션 피드백 및 노트

    튜터가 세션 후 작성하는 다양한 노트:
    - summary: 세션 요약
    - homework: 과제
    - parent_message: 학부모 메시지
    - progress: 진도 기록
    - concern: 특이사항/우려사항
    """

    __tablename__ = "tutor_notes"

    id = Column(BigInteger, primary_key=True)
    tutor_session_id = Column(
        BigInteger,
        ForeignKey("tutor_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    note_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255))
    content = Column(Text, nullable=False)
    is_visible_to_student = Column(Boolean, nullable=False, default=True)
    is_visible_to_parent = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    meta = Column(JSONB)

    # Relationships
    session = relationship("TutorSession", back_populates="notes_list")
    author = relationship("User")

    def __repr__(self):
        return f"<TutorNote(id={self.id}, type={self.note_type}, session_id={self.tutor_session_id})>"


class TutorStudentRelation(Base):
    """
    튜터-학생 관계 (계약/매칭)

    튜터가 담당하는 학생 목록 관리
    """

    __tablename__ = "tutor_student_relations"

    id = Column(BigInteger, primary_key=True)
    tutor_id = Column(
        Integer, ForeignKey("tutors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(20), nullable=False, default="pending", index=True)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    subjects = Column(ARRAY(Text))
    weekly_hours = Column(Numeric(4, 1))
    contract_type = Column(String(50))  # 'monthly', 'per_session', 'package'
    rate_per_hour = Column(Numeric(10, 2))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    meta = Column(JSONB)

    # Relationships
    tutor = relationship("Tutor", back_populates="student_relations")
    student = relationship("Student", backref="tutor_relations")

    __table_args__ = (
        Index(
            "uq_tutor_student_active",
            "tutor_id",
            "student_id",
            unique=True,
            postgresql_where=(status == "active"),
        ),
    )

    def __repr__(self):
        return f"<TutorStudentRelation(id={self.id}, tutor_id={self.tutor_id}, student_id={self.student_id}, status={self.status})>"


class TutorAvailability(Base):
    """
    튜터 가용 시간

    주간 스케줄 관리
    """

    __tablename__ = "tutor_availability"

    id = Column(BigInteger, primary_key=True)
    tutor_id = Column(
        Integer, ForeignKey("tutors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week = Column(Integer, nullable=False, index=True)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_available = Column(Boolean, nullable=False, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tutor = relationship("Tutor", back_populates="availability_slots")

    def __repr__(self):
        return f"<TutorAvailability(id={self.id}, tutor_id={self.tutor_id}, day={self.day_of_week})>"


class TutorRating(Base):
    """
    튜터 평가

    학생/학부모가 남기는 튜터 평가
    """

    __tablename__ = "tutor_ratings"

    id = Column(BigInteger, primary_key=True)
    tutor_id = Column(
        Integer, ForeignKey("tutors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        BigInteger, ForeignKey("tutor_sessions.id", ondelete="SET NULL"), index=True
    )
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    meta = Column(JSONB)

    # Relationships
    tutor = relationship("Tutor", back_populates="ratings")
    student = relationship("Student")
    session = relationship("TutorSession")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )

    def __repr__(self):
        return f"<TutorRating(id={self.id}, tutor_id={self.tutor_id}, rating={self.rating})>"
