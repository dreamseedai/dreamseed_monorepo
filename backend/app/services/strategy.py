# app/services/strategy.py

import random
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import RecommendationStrategy


# ✅ Q값 업데이트 (기존 값이 있으면 업데이트, 없으면 생성)
def update_q_value(emotion: str, category: str, reward: float, alpha: float = 0.1):
    db: Session = SessionLocal()
    try:
        row = (
            db.query(RecommendationStrategy)
            .filter_by(emotion=emotion, category=category)
            .first()
        )
        if row:
            row.q_value += alpha * (reward - row.q_value)
        else:
            row = RecommendationStrategy(
                emotion=emotion, category=category, q_value=reward
            )
            db.add(row)
        db.commit()
    finally:
        db.close()


# ✅ 가장 높은 Q값을 가진 추천 카테고리 반환
def get_best_recommendation(emotion: str) -> str:
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(RecommendationStrategy)
            .filter_by(emotion=emotion)
            .order_by(RecommendationStrategy.q_value.desc())
            .all()
        )
        return rows[0].category if rows else "K-Drama"
    finally:
        db.close()


# ✅ ε-greedy 기반 추천 전략 (탐색/활용 혼합)
def get_epsilon_greedy_recommendation(emotion: str, epsilon: float = 0.2) -> str:
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(RecommendationStrategy)
            .filter_by(emotion=emotion)
            .order_by(RecommendationStrategy.q_value.desc())
            .all()
        )
        if not rows:
            return "K-Drama"  # fallback

        if random.random() < epsilon:
            return random.choice(rows).category  # 탐색
        else:
            return rows[0].category  # 활용
    finally:
        db.close()
