# app/routes/recommendation_log.py

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.db import save_recommendation_log
from app.services.strategy import update_q_value

router = APIRouter()


class RecommendationLogInput(BaseModel):
    emotion: str
    keywords: list[str]
    category: str
    description: str
    strategy: str  # "gpt" or "rl"


@router.post("/recommendation-log")
def log_recommendation_click(payload: RecommendationLogInput):
    # 1. 로그 저장
    save_recommendation_log(
        emotion=payload.emotion,
        keywords=payload.keywords,
        category=payload.category,
        description=payload.description,
        strategy=payload.strategy,
    )

    # 2. RL 전략인 경우 Q-value 강화
    if payload.strategy == "rl":
        update_q_value(payload.emotion, payload.category, reward=1.0)

    return {"status": "logged"}
