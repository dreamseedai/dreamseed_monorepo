"""Interest goal model for user-topic targets."""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Numeric, SmallInteger, Text
from sqlalchemy.sql import func

from ..db.base import Base


class InterestGoal(Base):
    """Interest goal table for user-topic learning targets."""

    __tablename__ = "interest_goal"

    user_id = Column(Text, primary_key=True, index=True)
    topic_id = Column(Text, primary_key=True, index=True)
    target_level = Column(Numeric(6, 3), nullable=True)
    priority = Column(SmallInteger, nullable=False, server_default="0")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<InterestGoal(user_id={self.user_id!r}, topic_id={self.topic_id!r}, target_level={self.target_level})>"
