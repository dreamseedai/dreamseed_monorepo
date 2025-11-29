from sqlalchemy import Column, Integer, String, DateTime
from app.db.database import Base
from datetime import datetime


class GptRecommendation(Base):
    __tablename__ = "gpt_recommendations"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    url = Column(String)
    source = Column(String)
    emotion = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
