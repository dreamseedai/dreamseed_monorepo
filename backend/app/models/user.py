"""
User model
"""
from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.parent_models import ParentChildLink


class User(Base):
    """User model - supports multiple roles (student, parent, teacher, tutor, admin)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False, index=True)  # student, parent, teacher, tutor, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships for parent-child links (Week 4)
    children_links = relationship(
        "ParentChildLink",
        foreign_keys="ParentChildLink.parent_id",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    parent_links = relationship(
        "ParentChildLink",
        foreign_keys="ParentChildLink.child_id",
        back_populates="child",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
