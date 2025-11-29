# backend/advertiser_email_api.py
from fastapi import APIRouter
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()


class EmailDraftRequest(BaseModel):
    brand: str
    emotion: str
    summary: str


@router.post("/api/advertiser-email")
def generate_email(req: EmailDraftRequest):
    prompt = f"감정: {req.emotion}\n브랜드: {req.brand}\n전략 요약: {req.summary}\n\n이 내용을 바탕으로 광고주에게 보내는 감성적이고 설득력 있는 이메일 초안을 생성해 주세요. 문장은 자연스럽고 브랜드 호감도를 높이는 방향으로 작성하세요."

    try:
        res = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 감성 기반 광고 이메일을 작성하는 마케팅 전문가입니다.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
        )
        return {"email": res.choices[0].message.content.strip()}
    except Exception as e:
        return {"email": f"[오류] {str(e)}"}
