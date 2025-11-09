# backend/services/openai_service.py

import os
import openai

# ✅ 환경변수에서 OpenAI API 키 로드
openai.api_key = os.getenv("OPENAI_API_KEY")


def ask_gpt(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    """
    주어진 프롬프트를 GPT 모델에 전달하고 응답을 문자열로 반환합니다.
    """
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=300,
    )
    return response.choices[0].message["content"]
