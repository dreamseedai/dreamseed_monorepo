from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.database import Base
from datetime import datetime


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    content_title = Column(String)
    clicked = Column(Boolean)
    emotion = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
