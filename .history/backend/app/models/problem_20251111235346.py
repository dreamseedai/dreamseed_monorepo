"""
Problem model
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Problem(Base):
    """Problem model"""
    __tablename__ = "problems"
    
    id = Column(Integer, primary_key=True, autoincrement=False)
    title = Column(Text, nullable=False)  # VARCHAR 제한 제거
    description = Column(Text, nullable=False)
    difficulty = Column(String(20))  # easy, medium, hard
    category = Column(String(50), index=True)
    metadata = Column(JSONB, default={})  # MySQL 원본 데이터 보존
    created_by = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # 마이그레이션 데이터는 NULL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    # creator = relationship("User", backref="created_problems")
    
    def __repr__(self):
        return f"<Problem(id={self.id}, title={self.title}, difficulty={self.difficulty})>"
