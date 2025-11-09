# app/db/models.py

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)

    # 관계 설정
    emotion_logs = relationship("EmotionLog", back_populates="user")
    recommendation_strategies = relationship(
        "UserRecommendationStrategy", back_populates="user"
    )


class EmotionLog(Base):
    __tablename__ = "emotion_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    input = Column(String, nullable=False)
    emotion = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="emotion_logs")


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id = Column(Integer, primary_key=True, index=True)
    emotion = Column(String, nullable=False)
    keywords = Column(String)  # JSON string or comma-separated
    category = Column(String)
    description = Column(String)
    strategy = Column(String)  # e.g., "gpt" or "rl"
    clicked_at = Column(DateTime, default=func.now())


class RecommendationStrategy(Base):
    __tablename__ = "recommendation_strategies"

    id = Column(Integer, primary_key=True)
    emotion = Column(String, nullable=False)
    category = Column(String, nullable=False)
    q_value = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserRecommendationStrategy(Base):
    __tablename__ = "user_recommendation_strategies"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emotion = Column(String, nullable=False)
    category = Column(String, nullable=False)
    q_value = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="recommendation_strategies")
