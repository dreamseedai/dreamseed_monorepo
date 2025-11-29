# backend/routes/pattern_api.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()


# 🔹 요청/응답 모델 정의
class RecommendRequest(BaseModel):
    mode: str
    category: str
    keywords: List[str]


class RecommendItem(BaseModel):
    title: str
    type: str
    source: str
    url: str


# 🔹 테스트용 GET
@router.get("/pattern")
def get_pattern():
    return {"message": "Pattern API is working"}


# 🔹 추천 API
@router.post("/api/recommend", response_model=List[RecommendItem])
def recommend(req: RecommendRequest):
    prompt = f"추천할 {req.mode} 콘텐츠: 카테고리={req.category}, 키워드={', '.join(req.keywords)}"
    return [
        RecommendItem(
            title="청춘 블루스",
            type="video",
            source="YouTube",
            url="https://example.com/1",
        ),
        RecommendItem(
            title="감성의 순간",
            type="video",
            source="YouTube",
            url="https://example.com/2",
        ),
    ]
