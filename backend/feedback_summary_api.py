# backend/feedback_summary_api.py
from fastapi import APIRouter
import os
import json
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()

FEEDBACK_FILE = os.path.join(
    os.path.dirname(__file__), "../frontend/src/data/feedback.json"
)


@router.get("/api/feedback/summary")
def summarize_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return {"summary": ["피드백 데이터가 없습니다."]}

    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        feedbacks = json.load(f)

    comments = [
        f"{f['rating']}점: {f['comment']}" for f in feedbacks if f.get("comment")
    ]
    if not comments:
        return {"summary": ["분석할 의견이 없습니다."]}

    prompt = (
        "다음은 사용자 피드백입니다. 공통된 감정, 불만, 긍정적 반응을 요약해 주세요:\n"
        + "\n".join(f"- {c}" for c in comments[-20:])  # 최근 20개만 분석
    )

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 AI 피드백 분석가입니다."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
        )
        lines = [
            line.strip("- ")
            for line in completion.choices[0].message.content.split("\n")
            if line.strip()
        ]
        return {"summary": lines}
    except Exception as e:
        return {"summary": [f"[오류] {str(e)}"]}
