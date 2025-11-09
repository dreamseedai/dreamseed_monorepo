# backend/creator_feedback_api.py
from fastapi import APIRouter
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()


@router.get("/api/creator-feedback/{creator_id}")
def get_creator_feedback(creator_id: str):
    # 예시 사용자 로그 흐름 (실제 데이터 연동 필요)
    usage_log = [
        "20대 여성 / 한국 / 밤 9시: K-POP 집중 청취",
        "40대 남성 / 미국 / 오전 8시: 뉴스 위주 감상",
        "30대 여성 / 일본 / 오후 7시: 드라마 연속 시청",
    ]

    prompt = (
        "당신은 AI 방송 전략가입니다.\n"
        "다음은 특정 크리에이터 채널의 시청자 사용 로그입니다.\n"
        "이 데이터를 바탕으로 전략적 피드백 3가지를 작성하세요.\n"
        + "\n".join(f"- {line}" for line in usage_log)
    )

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 크리에이터에게 전략적으로 조언하는 AI 방송 전략가입니다.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        message = completion.choices[0].message.content.strip()
        lines = [line.strip("- ") for line in message.split("\n") if line.strip()]
        return {"creator_id": creator_id, "summary": lines}
    except Exception as e:
        return {"creator_id": creator_id, "summary": [f"[오류] {str(e)}"]}
