# app/services/emotion_recommendation.py

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_emotion_recommendation(emotion: str) -> dict:
    prompt = f"""
    사용자 감정이 '{emotion}'일 때, 한글 학습 또는 위로 콘텐츠를 다음 형식으로 추천해 주세요:

    - 감정 피드백 메시지: 한 문장 (예: 당신의 감정을 이해해요. 함께 이겨낼 수 있어요!)
    - 추천 키워드: 2~3개 단어 (예: 희망, 친구, 자연)
    - 추천 콘텐츠 유형: [K-Drama, K-Pop, K-Food, 속담, 명언, 한글학습] 중 선택
    - 콘텐츠 설명: 한 줄 설명

    반드시 JSON 형식으로 응답해 주세요:
    {{
        "feedback": "...",
        "keywords": ["...", "..."],
        "category": "...",
        "description": "..."
    }}
    """

    res = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    import json

    return json.loads(res.choices[0].message.content.strip())
