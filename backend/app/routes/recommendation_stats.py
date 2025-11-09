from fastapi import APIRouter
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import RecommendationLog

router = APIRouter()


@router.get("/recommendation-ctr")
def get_recommendation_ctr():
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(RecommendationLog.emotion, func.count().label("count"))
            .group_by(RecommendationLog.emotion)
            .all()
        )
        return [{"emotion": row[0], "clicks": row[1]} for row in rows]
    finally:
        db.close()


from fastapi import APIRouter
from sqlalchemy import func

router = APIRouter()


@router.get("/admin/recommendation-strategy-summary")
def get_strategy_ctr():
    db: Session = SessionLocal()
    try:
        results = (
            db.query(
                RecommendationLog.strategy,
                RecommendationLog.emotion,
                func.count().label("total"),
                func.sum(
                    func.case((RecommendationLog.clicked_at != None, 1), else_=0)
                ).label("clicks"),
            )
            .group_by(RecommendationLog.strategy, RecommendationLog.emotion)
            .all()
        )
        return [
            {
                "strategy": row[0],
                "emotion": row[1],
                "total": row[2],
                "clicks": row[3],
                "ctr": round(row[3] / row[2], 3) if row[2] else 0,
            }
            for row in results
        ]
    finally:
        db.close()
