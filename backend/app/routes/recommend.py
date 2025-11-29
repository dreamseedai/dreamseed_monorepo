# backend/app/routes/recommend.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class RecommendRequest(BaseModel):
    prompt: str
    emotion: Optional[str] = None


@router.post("/api/recommend")
def recommend_response(data: RecommendRequest):
    # TODO: 실제 GPT 모델 호출로 대체
    fake_response = f"[{data.emotion or '감정 미지정'}] 상황에 어울리는 K-드라마는 '나의 아저씨'입니다."
    return {"response": fake_response}
