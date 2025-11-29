from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.db.database import Base


class RecommendationStrategy(Base):
    __tablename__ = "recommendation_strategy"

    id = Column(Integer, primary_key=True)
    emotion = Column(String)
    content_title = Column(String)
    q_value = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)
