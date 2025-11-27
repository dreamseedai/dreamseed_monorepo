"""
Item model with IRT parameters for Adaptive Testing

This module defines the Item model for CAT (Computerized Adaptive Testing):
- IRT parameters (a, b, c) for 3PL model
- Question content and metadata
- Relationships to attempts

Integrates with AdaptiveEngine for item selection and ability estimation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Numeric,
    Text,
    DateTime,
    JSON,
    Integer,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Item(Base):
    """
    Item (question) with IRT parameters for adaptive testing.

    IRT Parameters (3PL Model):
    - a: Discrimination (0.5-2.5, typical)
        Higher a = item better distinguishes between ability levels
    - b: Difficulty (-3 to +3, typical)
        Higher b = more difficult item
    - c: Guessing (0-0.3, typical)
        Lower c = less chance of guessing correctly

    These parameters are used by the AdaptiveEngine to:
    1. Calculate probability of correct response
    2. Compute Fisher information
    3. Select optimal next item
    4. Update ability estimate (theta)

    Usage:
        item = Item(
            topic="algebra",
            a=1.2,  # Good discrimination
            b=0.5,  # Medium difficulty
            c=0.2,  # Low guessing
            question_text="Solve for x: 2x + 5 = 13",
            correct_answer="4",
            explanation="Subtract 5 from both sides, then divide by 2"
        )
    """

    __tablename__ = "items"

    __table_args__ = {"extend_existing": True}
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Content
    topic = Column(
        String(255), nullable=True, index=True
    )  # 'algebra', 'geometry', 'calculus'
    question_text = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=True)  # For auto-grading
    explanation = Column(Text, nullable=True)  # Solution explanation

    # IRT Parameters (3PL Model)
    a = Column(Numeric(6, 3), nullable=False, comment="Discrimination parameter")
    b = Column(Numeric(6, 3), nullable=False, comment="Difficulty parameter")
    c = Column(Numeric(6, 3), nullable=False, comment="Guessing parameter")

    # Metadata
    meta = Column(JSON, nullable=True)  # Question type, tags, standards, etc.
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    # attempts = relationship("Attempt", back_populates="item")  # Disabled - Attempt.item also disabled
    choices = relationship(
        "ItemChoice", back_populates="item", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Item(id={self.id}, topic={self.topic}, a={self.a}, b={self.b}, c={self.c})>"

    def to_engine_format(self) -> dict:
        """
        Convert to format expected by AdaptiveEngine.

        Returns:
            Dict with keys: id, a, b, c
        """
        return {
            "id": self.id,
            "a": float(self.a),  # type: ignore
            "b": float(self.b),  # type: ignore
            "c": float(self.c),  # type: ignore
        }


class ItemChoice(Base):
    """
    Multiple choice options for an item.

    Used for multiple-choice questions. Each item can have 2-5 choices.
    One choice should be marked as correct.
    """

    __tablename__ = "item_choices"

    __table_args__ = {"extend_existing": True}
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    item_id = Column(
        BigInteger,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    choice_num = Column(Integer, nullable=False)  # 1, 2, 3, 4, 5
    choice_text = Column(Text, nullable=False)
    is_correct = Column(
        Integer, nullable=False, default=0
    )  # 0 or 1 (SQLite compatibility)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    item = relationship("Item", back_populates="choices")

    def __repr__(self):
        return f"<ItemChoice(item_id={self.item_id}, num={self.choice_num}, correct={bool(self.is_correct)})>"


class ItemPool(Base):
    """
    Named collections of items for organizing questions.

    Examples:
    - "Grade 8 Math Placement Test"
    - "Algebra Unit 3 Practice"
    - "SAT Math Practice Pool"

    Items can belong to multiple pools via item_pool_membership table.
    """

    __tablename__ = "item_pools"

    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=True, index=True)
    grade_level = Column(String(20), nullable=True)

    meta = Column(JSON, nullable=True)  # Pool configuration, constraints
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    items = relationship("Item", secondary="item_pool_membership", backref="pools")

    def __repr__(self):
        return f"<ItemPool(id={self.id}, name={self.name}, subject={self.subject})>"


class ItemPoolMembership(Base):
    """
    Junction table for Item <-> ItemPool many-to-many relationship.
    """

    __tablename__ = "item_pool_membership"

    __table_args__ = {"extend_existing": True}
    item_id = Column(
        BigInteger, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    pool_id = Column(
        Integer, ForeignKey("item_pools.id", ondelete="CASCADE"), primary_key=True
    )

    # Optional: Item order or weight within pool
    sequence = Column(Integer, nullable=True)
    weight = Column(Numeric(5, 2), nullable=True, default=1.0)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<ItemPoolMembership(item_id={self.item_id}, pool_id={self.pool_id})>"
