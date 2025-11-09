# backend/creator_assist_api.py
from fastapi import APIRouter
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import openai  # type: ignore
    openai.api_key = os.getenv("OPENAI_API_KEY")
    _HAS_OPENAI = True
except Exception:
    openai = None  # type: ignore
    _HAS_OPENAI = False

router = APIRouter()


class CreatorAssistRequest(BaseModel):
    creator_id: str
    question: str


@router.post("/api/creator-assist")
def creator_assist(req: CreatorAssistRequest):
    prompt = f"크리에이터 ID: {req.creator_id}\n질문: {req.question}\n방송 전략가로서 친절하게 도와주세요."

    # 모듈이 없거나 API 키가 설정되지 않은 경우 데모 응답으로 폴백
    api_key = os.getenv("OPENAI_API_KEY") or getattr(openai, "api_key", None)
    if (not _HAS_OPENAI) or (not api_key):
        return {"reply": "[데모] OPENAI_API_KEY 미설정 – 예시 전략:\n1) 타깃 청중 포맷 고정\n2) 라이브 상호작용 유도\n3) 하이라이트 클립 재활용"}
    try:
        response = openai.ChatCompletion.create(  # type: ignore[attr-defined]
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 감성 기반 방송 전략을 제안하는 AI 도우미입니다.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
        )
        return {"reply": response.choices[0].message.content.strip()}
    except Exception as e:
        return {"reply": f"[오류] {str(e)}"}
