# app/models/recommendation_strategy.py

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.db.database import Base


class RecommendationStrategy(Base):
    __tablename__ = "recommendation_strategies"

    id = Column(Integer, primary_key=True)
    emotion = Column(String, nullable=False)
    category = Column(String, nullable=False)
    q_value = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
