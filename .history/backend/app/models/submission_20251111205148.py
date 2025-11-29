"""
Submission model
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Submission(Base):
    """Submission model"""
    __tablename__ = "submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    answer = Column(Text, nullable=False)
    is_correct = Column(Boolean)
    ai_feedback = Column(Text)
    score = Column(Integer)  # 0-100
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Submission(id={self.id}, problem={self.problem_id}, score={self.score})>"
