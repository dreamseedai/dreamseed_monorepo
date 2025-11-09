# backend/brand_match_api.py
from fastapi import APIRouter
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()


class BrandMatchRequest(BaseModel):
    emotion: str


@router.post("/api/match-brand-by-emotion")
def match_brand(req: BrandMatchRequest):
    prompt = f"감정: {req.emotion}\n이 감정과 어울리는 광고 브랜드 3개를 제안해 주세요."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 감정에 어울리는 광고 브랜드를 추천하는 전문가입니다.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
        )
        lines = response.choices[0].message.content.strip().split("\n")
        return {"brands": [line.strip("-• ") for line in lines if line.strip()]}
    except Exception as e:
        return {"brands": [f"[오류] {str(e)}"]}
