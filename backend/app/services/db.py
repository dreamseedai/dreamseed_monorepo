# app/services/db.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import SessionLocal
from app.db.models import EmotionLog, RecommendationLog


# ✅ DB 연결 테스트 (헬스 체크)
def health_check() -> bool:
    db: Session = SessionLocal()
    try:
        db.execute("SELECT 1")  # 간단한 ping
        return True
    except SQLAlchemyError:
        return False
    finally:
        db.close()


# ✅ 감정 로그 저장
def save_emotion_log(text: str, emotion: str):
    db: Session = SessionLocal()
    try:
        log = EmotionLog(input=text, emotion=emotion)
        db.add(log)
        db.commit()
    finally:
        db.close()


# ✅ 추천 로그 저장 (strategy 포함 가능)
def save_recommendation_log(
    emotion: str,
    keywords: list[str],
    category: str,
    description: str,
    strategy: str = "gpt",  # 기본값: gpt
):
    db: Session = SessionLocal()
    try:
        log = RecommendationLog(
            emotion=emotion,
            keywords=",".join(keywords),
            category=category,
            description=description,
            strategy=strategy,
        )
        db.add(log)
        db.commit()
    finally:
        db.close()


def get_emotion_logs(user_id: str, limit: int = 10) -> list:
    # 예시: 임시 메모리 기반 mock
    return [
        {"emotion": "슬픔", "timestamp": "2025-05-27T12:00:00"},
        {"emotion": "기쁨", "timestamp": "2025-05-27T12:10:00"},
        # ...
    ]
