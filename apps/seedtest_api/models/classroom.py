"""Classroom model for organizing students by org and grade."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, SmallInteger, Text, UniqueConstraint
from sqlalchemy.sql import func

from ..db.base import Base


class Classroom(Base):
    """Classroom table for org-scoped student grouping."""

    __tablename__ = "classroom"

    id = Column(Text, primary_key=True)
    org_id = Column(Text, nullable=False, index=True)
    name = Column(Text, nullable=False)
    grade = Column(SmallInteger, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_classroom_org_name"),)

    def __repr__(self) -> str:
        return (
            f"<Classroom(id={self.id!r}, org_id={self.org_id!r}, name={self.name!r})>"
        )
