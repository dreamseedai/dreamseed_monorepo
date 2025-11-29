# backend/recall_api.py

import os
import openai

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


def init_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    openai.api_key = api_key


# 🧠 모델 요청 스키마 정의
class RecallRequest(BaseModel):
    prompt: str
    age: Optional[int] = None
    gender: Optional[str] = None
    culture: Optional[str] = None
    emotion: Optional[str] = None
    event: Optional[str] = None


class RecallResponse(BaseModel):
    message: str


@router.post("/api/recall", response_model=RecallResponse)
def recall_memory(req: RecallRequest):
    try:
        user_context = f"나이: {req.age or '모름'}, 성별: {req.gender or '모름'}, 문화권: {req.culture or '모름'}, 감정 상태: {req.emotion or '모름'}, 최근 이벤트: {req.event or '모름'}"

        full_prompt = (
            f"당신은 사용자의 감정과 추억을 공감하고 회상하게 해주는 감성 AI입니다.\n"
            f"사용자 정보: {user_context}\n"
            f"최근 감상 기록:\n{req.prompt}\n"
            f"이 사용자가 추억과 감정에 공감할 수 있는 짧고 따뜻한 한 문장을 생성하세요."
        )

        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 감정 공감에 특화된 회상형 AI입니다.",
                },
                {"role": "user", "content": full_prompt},
            ],
            max_tokens=150,
            temperature=0.8,
        )
        message = completion.choices[0].message.content.strip()
        return RecallResponse(message=message)
    except Exception as e:
        return RecallResponse(message=f"[오류] 회상 메시지 생성 실패: {str(e)}")
