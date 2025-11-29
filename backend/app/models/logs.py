# app/models/logs.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class UserActivityLog(Base):
    __tablename__ = "user_activity_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    country = Column(String)
    city = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    content_type = Column(String)
    emotion = Column(String)
    duration_seconds = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class UserPurchaseLog(Base):
    __tablename__ = "user_purchase_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    package_name = Column(String)
    amount = Column(Integer)
    currency = Column(String, default="KRW")
    country = Column(String)
    city = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
