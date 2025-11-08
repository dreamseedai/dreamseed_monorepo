"""Risk flag model for tracking student learning/behavioral risks."""

from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ..db.base import Base


class RiskFlag(Base):
    """Risk flag table for student risk detection and tracking."""

    __tablename__ = "risk_flag"

    id = Column(Text, primary_key=True)
    tenant_id = Column(Text, nullable=False, index=True)
    student_id = Column(Text, nullable=False, index=True)
    classroom_id = Column(Text, nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)
    type = Column(
        String(64), nullable=False, index=True
    )  # low_growth | irregular_attendance | response_anomaly | composite
    score = Column(Numeric(5, 2), nullable=False, default=0.0)  # 0.00 ~ 1.00
    details_json = Column(JSONB, nullable=True, default=dict)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_risk_classroom_week", "classroom_id", "week_start"),
        Index("ix_risk_student_week", "student_id", "week_start"),
        Index("ix_risk_type_week", "type", "week_start"),
        Index("ix_risk_flag_tenant_classroom_week", "tenant_id", "classroom_id", "week_start"),
        Index("ix_risk_flag_tenant_student_week", "tenant_id", "student_id", "week_start"),
    )

    def __repr__(self) -> str:
        return f"<RiskFlag(student_id={self.student_id!r}, type={self.type!r}, score={self.score})>"
