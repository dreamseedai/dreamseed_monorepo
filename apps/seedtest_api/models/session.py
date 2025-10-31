"""Session model for learning/assessment session metadata."""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Text
from sqlalchemy import Integer
from sqlalchemy.sql import func

from ..db.base import Base


class Session(Base):
    """Session table for tracking learning/assessment activities."""

    __tablename__ = "session"

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=True, index=True)
    org_id = Column(Integer, nullable=True, index=True)
    classroom_id = Column(Text, nullable=True, index=True)
    exam_id = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Text, nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id!r}, classroom_id={self.classroom_id!r}, status={self.status!r})>"
