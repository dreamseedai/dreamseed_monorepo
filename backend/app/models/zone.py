"""
Zone model for content organization

Zones represent hierarchical content organization:
- Subjects (Math, Science, English)
- Chapters within subjects
- Topics within chapters
- Subtopics

Used for:
- Content organization
- Progress tracking
- Curriculum mapping
"""

from __future__ import annotations

from typing import cast

from app.core.database import Base
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Zone(Base):
    """
    Hierarchical content organization (subject → chapter → topic → subtopic)

    Examples:
    - Level 0 (Subject): "Mathematics"
    - Level 1 (Chapter): "Algebra"
    - Level 2 (Topic): "Linear Equations"
    - Level 3 (Subtopic): "Solving for x"

    Supports self-referential hierarchy via parent_id.

    Usage:
        # Create subject
        math = Zone(name="Mathematics", level=0, zone_type="subject")

        # Create chapter under math
        algebra = Zone(name="Algebra", level=1, zone_type="chapter", parent_id=math.id)

        # Create topic under algebra
        linear_eq = Zone(name="Linear Equations", level=2, zone_type="topic", parent_id=algebra.id)
    """

    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Hierarchy
    parent_id = Column(
        Integer, ForeignKey("zones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    level = Column(
        Integer, nullable=False, default=0, index=True
    )  # 0=subject, 1=chapter, 2=topic, 3=subtopic

    # Content
    name = Column(String(255), nullable=False, index=True)
    zone_type = Column(
        String(50), nullable=True
    )  # 'subject', 'chapter', 'topic', 'subtopic'
    code = Column(
        String(50), nullable=True, unique=True, index=True
    )  # Unique identifier like 'MATH-ALG-01'
    description = Column(Text, nullable=True)

    # Ordering
    sequence = Column(Integer, nullable=True)  # Order within parent

    # Metadata
    meta = Column(JSON, nullable=True)  # Standards alignment, grade level, difficulty
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
    parent = relationship("Zone", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<Zone(id={self.id}, name={self.name}, level={self.level}, type={self.zone_type})>"

    def get_full_path(self) -> str:
        """
        Get full hierarchical path (e.g., "Mathematics / Algebra / Linear Equations")
        """
        name = cast(str, self.name)
        if self.parent:
            return f"{self.parent.get_full_path()} / {name}"
        return name
