"""Features topic daily model for daily user/topic aggregates."""

from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, Text
from sqlalchemy.sql import func

from ..db.base import Base


class FeaturesTopicDaily(Base):
    """Daily aggregates per user/topic for analytics and ML features.

    Columns align with KPI pipeline (Dev Contract 2-6):
    - attempts: total question attempts for this topic on this date
    - correct: number of correct attempts
    - avg_time_ms: average response time in milliseconds
    - hints: total hints used
    - theta_estimate: IRT ability estimate (mean theta for topic)
    - theta_sd: standard deviation of theta estimates
    - rt_median: median response time (milliseconds)
    - improvement: delta from previous period (e.g., accuracy gain)
    """

    __tablename__ = "features_topic_daily"

    user_id = Column(Text, primary_key=True)
    topic_id = Column(Text, primary_key=True, index=True)
    date = Column(Date, primary_key=True, index=True)

    # Core metrics
    attempts = Column(Integer, nullable=False, server_default="0")
    correct = Column(Integer, nullable=False, server_default="0")
    avg_time_ms = Column(Integer, nullable=True)
    hints = Column(Integer, nullable=False, server_default="0")

    # IRT metrics
    theta_estimate = Column(
        Numeric(6, 3), nullable=True, comment="Mean theta for topic on date"
    )
    theta_sd = Column(
        Numeric(6, 3), nullable=True, comment="Standard deviation of theta"
    )

    # Additional KPI metrics
    rt_median = Column(Integer, nullable=True, comment="Median response time (ms)")
    improvement = Column(
        Numeric(6, 3), nullable=True, comment="Improvement delta (e.g., accuracy gain)"
    )

    # Metadata
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    computed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<FeaturesTopicDaily(user_id={self.user_id!r}, topic_id={self.topic_id!r}, date={self.date!r})>"
