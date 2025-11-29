# backend/api/recommendation_api.py

from fastapi import APIRouter, Query
from app.services.recommendation_service import gpt_emotion_recommend

router = APIRouter()


@router.get("/api/gpt-recommend")
def gpt_recommend(emotion: str = Query(..., description="사용자의 감정 키워드")):
    """
    GPT 감정 기반 추천 요청 후 구조화된 리스트로 반환

    반환 예시:
    {
        "emotion": "설렘",
        "items": [
            {
                "title": "도깨비 고백 장면",
                "description": "설렘 가득한 드라마 명장면",
                "url": "https://example.com/goblin",
                "source": "GPT"
            },
            ...
        ]
    }
    """
    items = gpt_emotion_recommend(emotion)
    return {"emotion": emotion, "items": items}
