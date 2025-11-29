"""
Student ability history model for tracking IRT theta over time
"""
from sqlalchemy import Column, Integer, Date, Float, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class StudentAbilityHistory(Base):
    """Time-series data for student ability (IRT theta)"""
    __tablename__ = "student_ability_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    as_of_date = Column(Date, nullable=False, index=True)
    theta = Column(Float, nullable=False)
    source = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "as_of_date", name="uq_student_ability_history_student_date"),
    )

    def __repr__(self):
        return f"<StudentAbilityHistory(student_id={self.student_id}, date={self.as_of_date}, theta={self.theta})>"
