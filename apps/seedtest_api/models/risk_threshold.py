"""Risk threshold model for hierarchical risk detection configuration."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.sql import func

from ..db.base import Base


class RiskThreshold(Base):
    """Hierarchical risk threshold configuration.

    Thresholds can be defined at three levels (most specific wins):
    1. Class-specific: (tenant_id, class_id)
    2. Grade-specific: (tenant_id, grade)
    3. Tenant-wide: (tenant_id, NULL, NULL)

    Type can be: low_growth | irregular_att | response_anomaly
    """

    __tablename__ = "risk_threshold"

    id = Column(Text, primary_key=True)
    tenant_id = Column(Text, nullable=False, index=True)
    type = Column(String(64), nullable=False, index=True)

    # Optional scoping (class-level overrides grade-level overrides tenant-level)
    class_id = Column(Text, nullable=True, index=True)
    grade = Column(String(16), nullable=True, index=True)

    # Threshold values (NULL means inherit from less specific level)
    low_growth_delta = Column(Float, nullable=True)  # default: 0.05
    low_growth_nonpos_weeks = Column(Integer, nullable=True)  # default: 3
    absent_rate_threshold = Column(Float, nullable=True)  # default: 0.10
    late_rate_threshold = Column(Float, nullable=True)  # default: 0.15
    response_anomaly_c_top_pct = Column(Float, nullable=True)  # default: 0.20
    no_response_rate_threshold = Column(Float, nullable=True)  # default: 0.08

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (Index("ix_threshold_tenant_type", "tenant_id", "type"),)

    def __repr__(self) -> str:
        scope = f"class={self.class_id}" if self.class_id else (f"grade={self.grade}" if self.grade else "tenant")
        return f"<RiskThreshold(type={self.type!r}, scope={scope})>"
