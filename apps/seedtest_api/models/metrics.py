from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ..db.base import Base


class WeeklyKPI(Base):
    __tablename__ = "weekly_kpi"

    user_id = Column(Text, primary_key=True)
    week_start = Column(Date, primary_key=True)
    kpis = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class StudentTopicTheta(Base):
    __tablename__ = "student_topic_theta"

    user_id = Column(Text, primary_key=True)
    topic_id = Column(Text, primary_key=True)
    theta = Column(Numeric, nullable=True)
    standard_error = Column(Numeric, nullable=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
