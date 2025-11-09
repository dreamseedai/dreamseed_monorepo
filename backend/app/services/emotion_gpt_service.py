# backend/services/emotion_gpt_service.py

from app.services.openai_service import ask_gpt


def detect_emotion_from_text(text: str) -> str:
    prompt = f"""
다음 문장에서 느껴지는 감정을 가능한 선택지 중 하나로 한 단어로만 답하세요.
선택지: 설렘, 슬픔, 분노, 행복, 피로, 놀람, 불안

문장: "{text}"

감정:
"""
    response = ask_gpt(prompt).strip()
    return response
