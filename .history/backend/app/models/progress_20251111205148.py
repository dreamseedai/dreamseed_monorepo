"""
Progress model
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Progress(Base):
    """Progress model"""
    __tablename__ = "progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"))
    status = Column(String(20))  # not_started, in_progress, completed
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        UniqueConstraint('user_id', 'problem_id', name='uq_user_problem'),
    )
    
    def __repr__(self):
        return f"<Progress(user={self.user_id}, problem={self.problem_id}, status={self.status})>"
