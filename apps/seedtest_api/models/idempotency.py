from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.sql import func

from ..db.base import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    method = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
    user_id = Column(Text, nullable=True)
    org_id = Column(Integer, nullable=True)
    idempotency_key = Column(Text, nullable=False)
    req_hash = Column(Text, nullable=False)
    status_code = Column(Integer, nullable=False)
    response_body = Column(Text, nullable=False)  # JSON-serialized
    response_headers = Column(Text, nullable=True)  # JSON-serialized subset
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "method",
            "path",
            "user_id",
            "org_id",
            "idempotency_key",
            name="uq_idem_scope_key",
        ),
    )

__all__ = ["IdempotencyRecord"]
