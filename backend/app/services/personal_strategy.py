# app/services/personal_strategy.py

import random
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import UserRecommendationStrategy


# ✅ 사용자별 Q값 업데이트 (강화학습 기본 학습 로직)
def update_user_q_value(
    user_id: str, emotion: str, category: str, reward: float, alpha=0.1
):
    db: Session = SessionLocal()
    try:
        row = (
            db.query(UserRecommendationStrategy)
            .filter_by(user_id=user_id, emotion=emotion, category=category)
            .first()
        )
        if row:
            row.q_value += alpha * (reward - row.q_value)
        else:
            row = UserRecommendationStrategy(
                user_id=user_id, emotion=emotion, category=category, q_value=reward
            )
            db.add(row)
        db.commit()
    finally:
        db.close()


# ✅ 사용자별 ε-greedy 추천 선택
def get_user_epsilon_greedy_recommendation(
    user_id: str, emotion: str, epsilon=0.2
) -> str:
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(UserRecommendationStrategy)
            .filter_by(user_id=user_id, emotion=emotion)
            .order_by(UserRecommendationStrategy.q_value.desc())
            .all()
        )
        if not rows:
            return "K-Drama"

        if random.random() < epsilon:
            return random.choice(rows).category
        else:
            return rows[0].category
    finally:
        db.close()


# ✅ 사용자 전략 초기화/리셋 함수
def reset_user_strategy(user_id: str, emotion: str = None):
    db: Session = SessionLocal()
    try:
        q = db.query(UserRecommendationStrategy).filter_by(user_id=user_id)
        if emotion:
            q = q.filter_by(emotion=emotion)
        q.delete()
        db.commit()
    finally:
        db.close()
