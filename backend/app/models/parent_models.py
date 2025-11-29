"""
Parent-child relationship models
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ParentChildLink(Base):
    """
    Parent-child relationship table.

    Allows parent users to access their children's reports and data.
    One parent can have multiple children, one child can have multiple parents.
    """

    __tablename__ = "parent_child_links"
    __table_args__ = (
        UniqueConstraint("parent_id", "child_id", name="uq_parent_child_link"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    child_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    parent = relationship(
        "User",
        foreign_keys=[parent_id],
        back_populates="children_links",
    )
    child = relationship(
        "User",
        foreign_keys=[child_id],
        back_populates="parent_links",
    )

    def __repr__(self) -> str:
        return (
            f"<ParentChildLink(parent_id={self.parent_id}, child_id={self.child_id})>"
        )
