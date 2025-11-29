"""
AI Request tracking model

Tracks all AI API calls for:
- Cost monitoring
- Usage analytics
- Audit trails
- Rate limiting
- Quality assurance
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Numeric,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AIRequest(Base):
    """
    Log all AI API calls (OpenAI, Claude, etc.)

    Tracks:
    - User/student making request
    - Model used (gpt-4, claude-3-opus, etc.)
    - Token usage and costs
    - Request/response content
    - Success/failure status
    - Response time

    Used for:
    - Cost tracking and billing
    - Usage analytics
    - Rate limiting enforcement
    - Quality monitoring
    - Debugging and support

    Usage:
        request = AIRequest(
            user_id=123,
            student_id=456,
            request_type="tutor_chat",
            model="gpt-4-turbo",
            prompt="Explain quadratic equations",
            response="A quadratic equation is...",
            prompt_tokens=25,
            completion_tokens=150,
            total_tokens=175,
            cost_usd=0.0035,
            success=True,
            response_time_ms=1250
        )
    """

    __tablename__ = "ai_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    # Context
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    session_id = Column(
        BigInteger, nullable=True, index=True
    )  # Exam session or tutor session

    # Request details
    request_type = Column(
        String(50), nullable=False, index=True
    )  # 'tutor_chat', 'content_generation', 'grading', 'hint', etc.
    model = Column(
        String(100), nullable=False, index=True
    )  # 'gpt-4-turbo', 'claude-3-opus', etc.
    prompt = Column(Text, nullable=True)  # Request content (may be large)
    response = Column(Text, nullable=True)  # Response content (may be large)

    # Token usage
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Cost tracking
    cost_usd = Column(Numeric(10, 6), nullable=True)  # Cost in USD

    # Status
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=True)  # HTTP status or error code

    # Performance
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds

    # Metadata
    meta = Column(JSON, nullable=True)  # API version, temperature, max_tokens, etc.
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user = relationship("User", backref="ai_requests")
    student = relationship("Student", backref="ai_requests")

    def __repr__(self):
        return f"<AIRequest(id={self.id}, type={self.request_type}, model={self.model}, success={self.success})>"

    def cost_summary(self) -> dict:
        """
        Get cost summary for reporting
        """
        return {
            "cost_usd": float(self.cost_usd) if self.cost_usd is not None else 0.0,  # type: ignore[arg-type]
            "tokens": self.total_tokens or 0,
            "model": self.model,
            "success": self.success,
        }
