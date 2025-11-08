"""Attendance model for tracking student attendance in sessions."""

from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Index, String, Text
from sqlalchemy.sql import func

from ..db.base import Base


class Attendance(Base):
    """Attendance tracking table for students in sessions."""

    __tablename__ = "attendance"

    id = Column(Text, primary_key=True)
    tenant_id = Column(Text, nullable=False, index=True)
    student_id = Column(Text, nullable=False, index=True)
    classroom_id = Column(Text, nullable=False, index=True)
    session_id = Column(Text, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(
        String(16), nullable=False
    )  # present | late | absent | excused
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_attendance_classroom_date", "classroom_id", "date"),
        Index("ix_attendance_student_date", "student_id", "date"),
        Index("ix_attendance_tenant_classroom_date", "tenant_id", "classroom_id", "date"),
        Index("ix_attendance_tenant_student_date", "tenant_id", "student_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<Attendance(student_id={self.student_id!r}, date={self.date}, status={self.status!r})>"
