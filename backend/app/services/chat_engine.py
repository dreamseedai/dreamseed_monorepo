# app/services/chat_engine.py

from app.services.ai_flags import USE_LOCAL_AI

if USE_LOCAL_AI:
    from transformers import AutoTokenizer, AutoModelForCausalLM

    model_id = "meta-llama/Llama-2-7b-chat-hf"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id)
else:
    tokenizer = None
    model = None

from openai import OpenAI
import os

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_local_response(prompt: str) -> str:
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=100)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


def generate_openai_response(prompt: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def generate_chat_response(prompt: str) -> str:
    if USE_LOCAL_AI and model and tokenizer:
        try:
            return generate_local_response(prompt)
        except Exception as e:
            print(f"❌ 로컬 모델 실패: {e} → OpenAI fallback")

    return generate_openai_response(prompt)


# ✅ TTS fallback
from app.services.tts_engine import speak_korean_local, speak_korean_openai


def speak_korean(text: str) -> str:
    if USE_LOCAL_AI:
        try:
            return speak_korean_local(text)
        except Exception as e:
            print(f"❌ 로컬 TTS 실패: {e} → OpenAI fallback")
    return speak_korean_openai(text)


# ✅ 번역 fallback
from app.services.translate_engine import (
    translate_en_to_ko_local,
    translate_en_to_ko_openai,
)


def translate_en_to_ko(text: str) -> str:
    if USE_LOCAL_AI:
        try:
            return translate_en_to_ko_local(text)
        except Exception as e:
            print(f"❌ 로컬 번역 실패: {e} → OpenAI fallback")
    return translate_en_to_ko_openai(text)
