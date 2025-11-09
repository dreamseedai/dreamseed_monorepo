# routes/admin_strategy.py
from fastapi import APIRouter
from sqlalchemy.orm import Session, sessionmaker
from app.db.database import (
    engine,
)  # Adjust the import path based on your project structure
from typing import Optional
from app.models.recommendation_strategy import (
    RecommendationStrategy,
)  # Adjust the import path based on your project structure

router = APIRouter()


@router.post("/admin/strategy-reset")
def reset_strategy(emotion: Optional[str] = None):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db: Session = SessionLocal()
    try:
        q = db.query(RecommendationStrategy)
        if emotion:
            q = q.filter_by(emotion=emotion)
        q.delete()
        db.commit()
        return {"status": "reset"}
    finally:
        db.close()
