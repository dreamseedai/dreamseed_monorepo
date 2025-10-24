from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ..db.base import Base


class ExamResult(Base):
    __tablename__ = "exam_results"

    id = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(Text, unique=True, nullable=False, index=True)
    user_id = Column(Text, nullable=True, index=False)
    org_id = Column(Integer, nullable=True, index=True)
    exam_id = Column(Integer, nullable=True, index=False)
    status = Column(Text, nullable=False, default="ready")
    result_json = Column(JSONB, nullable=False)
    score_raw = Column(Numeric, nullable=True)
    score_scaled = Column(Numeric, nullable=True)
    standard_error = Column(Numeric, nullable=True)
    percentile = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
