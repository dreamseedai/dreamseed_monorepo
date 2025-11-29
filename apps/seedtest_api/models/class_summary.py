"""Class summary model for aggregated class-level metrics."""

from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Index, Integer, Numeric, Text
from sqlalchemy.sql import func

from ..db.base import Base


class ClassSummary(Base):
    """Class summary table for weekly aggregated class-level metrics."""

    __tablename__ = "class_summary"

    id = Column(Text, primary_key=True)
    tenant_id = Column(Text, nullable=False, index=True)
    classroom_id = Column(Text, nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)
    mean_theta = Column(Numeric(6, 3), nullable=False)
    median_theta = Column(Numeric(6, 3), nullable=False)
    top10_theta = Column(Numeric(6, 3), nullable=False)
    bottom10_theta = Column(Numeric(6, 3), nullable=False)
    delta_theta_7d = Column(Numeric(6, 3), nullable=False, default=0.0)
    attendance_absent_rate = Column(Numeric(5, 4), nullable=False, default=0.0)
    attendance_late_rate = Column(Numeric(5, 4), nullable=False, default=0.0)
    stability_score = Column(Numeric(6, 3), nullable=False, default=0.0)
    risks_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_class_summary_classroom_week", "classroom_id", "week_start", unique=True
        ),
        Index(
            "ix_class_summary_tenant_classroom_week",
            "tenant_id",
            "classroom_id",
            "week_start",
        ),
    )

    def __repr__(self) -> str:
        return f"<ClassSummary(classroom_id={self.classroom_id!r}, week_start={self.week_start}, mean_theta={self.mean_theta})>"
