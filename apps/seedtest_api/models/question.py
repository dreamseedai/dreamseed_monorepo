"""Question model for storing items with IRT parameters."""

from __future__ import annotations

from sqlalchemy import BigInteger, Column, DateTime, Numeric, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ..db.base import Base


class Question(Base):
    """Question/item model with metadata for IRT parameters.

    The `meta` JSONB column stores IRT parameters and tags:

    Example meta structure:
    {
        "irt": {
            "a": 1.2,        // discrimination (2PL/3PL)
            "b": -0.6,       // difficulty
            "c": 0.2,        // guessing (3PL only, null for 2PL/Rasch)
            "model": "3PL",  // "Rasch" | "2PL" | "3PL"
            "version": "2025-01"  // calibration version
        },
        "tags": ["algebra", "one-step", "linear-eq"]
    }

    Access IRT params via JSON operators:
        SELECT (meta->'irt'->>'a')::float AS discrimination FROM question WHERE id=...;
    """

    __tablename__ = "question"

    id = Column(BigInteger, primary_key=True)
    content = Column(Text, nullable=False)
    difficulty = Column(Numeric, nullable=True, comment="Legacy difficulty score")
    topic_id = Column(Text, nullable=True, index=True)
    meta = Column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
        comment="IRT parameters and tags (JSON)",
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.id!r}, topic_id={self.topic_id!r})>"
