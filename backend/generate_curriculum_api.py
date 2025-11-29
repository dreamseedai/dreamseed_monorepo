# backend/generate_curriculum_api.py
from fastapi import APIRouter
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()


class CurriculumRequest(BaseModel):
    mood: str
    duration: int  # minutes
    category: str = "감성"


@router.post("/api/generate-curriculum")
def generate_curriculum(req: CurriculumRequest):
    prompt = (
        f"감정: {req.mood}\n"
        f"카테고리: {req.category}\n"
        f"방송 시간: {req.duration}분\n"
        f"위 조건에 맞는 AI 감성 채널 큐리큘럼을 제안해 주세요."
    )

    try:
        res = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 감정 기반 방송 흐름을 설계하는 감성 큐레이터입니다.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        lines = res.choices[0].message.content.strip().split("\n")
        return {"curriculum": [line.strip("-• ") for line in lines if line.strip()]}
    except Exception as e:
        return {"curriculum": [f"[오류] {str(e)}"]}
