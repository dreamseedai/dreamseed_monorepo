from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, Text, Float, BigInteger, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from ..db.base import Base
from ..settings import settings


class QuestionRow(Base):
    __tablename__ = "questions"

    id = Column(Text, primary_key=True)
    # NULL org_id means a global (platform) question shared across orgs
    org_id = Column(Integer, nullable=True, index=True)
    title = Column(Text, nullable=True)
    stem = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    options = Column(JSON, nullable=False)  # list[str]
    answer = Column(Integer, nullable=False)
    difficulty = Column(Text, nullable=False)  # easy|medium|hard
    topic = Column(Text, nullable=True)
    # Conditionally wire FK to topics table only when feature flag is enabled
    if getattr(settings, "USE_TOPICS_TABLE", False):
        topic_id = Column(
            BigInteger,
            ForeignKey("topics.id", onupdate="CASCADE", ondelete="SET NULL"),
            nullable=True,
            index=True,
        )
    else:
        topic_id = Column(BigInteger, nullable=True, index=True)
    # Note: tags column type varies by migration (jsonb or text[]). Keep this nullable
    # and without a Python-side default to avoid INSERTs on DBs where the column type
    # differs. Routers map None -> [] in API responses.
    tags = Column(JSON, nullable=True)  # list[str] (jsonb preferred; may be text[] in some DBs)
    status = Column(Text, nullable=False, default="draft", index=True)  # draft|published|deleted
    author = Column(Text, nullable=True)
    created_by = Column(Text, nullable=True, index=True)
    updated_by = Column(Text, nullable=True, index=True)
    discrimination = Column(Float, nullable=True)
    guessing = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
