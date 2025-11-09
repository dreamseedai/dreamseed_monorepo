# app/services/xp.py

from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from collections import defaultdict
from datetime import datetime

from app.db.models import EmotionLog


# ✅ 감정별 누적 횟수 (XP 유사 개념)
def get_emotion_xp_summary(db: Session):
    rows = (
        db.query(EmotionLog.emotion, func.count().label("count"))
        .group_by(EmotionLog.emotion)
        .order_by(func.count().desc())
        .all()
    )
    return {row.emotion: row.count for row in rows}


# ✅ 날짜별 감정 추이 (선택된 감정 필터 지원)
def get_emotion_trend(
    db: Session,
    emotion: str = None,
    from_date: datetime = None,
    to_date: datetime = None,
):
    query = db.query(
        cast(EmotionLog.created_at, Date).label("date"),
        EmotionLog.emotion,
        func.count().label("count"),
    )

    if emotion:
        query = query.filter(EmotionLog.emotion == emotion)
    if from_date:
        query = query.filter(EmotionLog.created_at >= from_date)
    if to_date:
        query = query.filter(EmotionLog.created_at <= to_date)

    query = query.group_by("date", EmotionLog.emotion).order_by("date")
    rows = query.all()

    # ✅ 날짜별 감정 count 구조로 재구성
    result = defaultdict(dict)
    for row in rows:
        result[str(row.date)][row.emotion] = row.count
    return result


# ✅ 감정 기반 XP 부여 로직
XP_TABLE = {
    "기쁨": 10,
    "슬픔": 5,
    "분노": 3,
    "놀람": 4,
    "평온": 8,
    "불안": 2,
    "사랑": 12,
}


def grant_xp_for_emotion(user_id: int, emotion: str, db: Session) -> int:
    xp = XP_TABLE.get(emotion, 1)

    # TODO: 실제 사용자 XP 업데이트 로직을 구현해야 함
    print(f"✅ 사용자 {user_id}에게 {xp} XP 부여 (감정: {emotion})")

    return xp
