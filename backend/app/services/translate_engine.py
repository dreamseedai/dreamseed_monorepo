# app/services/translate_engine.py

from app.services.ai_flags import USE_LOCAL_AI

if USE_LOCAL_AI:
    from transformers import MarianMTModel, MarianTokenizer

    model_name = "Helsinki-NLP/opus-mt-en-ko"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
else:
    model = None
    tokenizer = None


def translate_en_to_ko(text: str) -> str:
    if not model or not tokenizer:
        return "[로컬 번역기 비활성화]"

    inputs = tokenizer(text, return_tensors="pt", padding=True)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)


from app.services.ai_flags import USE_LOCAL_AI
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ✅ 1. NLLB 또는 DeepL (로컬/기본)
def translate_local(text: str, source_lang: str, target_lang: str) -> str:
    # 예시: 실제 DeepL 또는 HuggingFace NLLB API 연동
    if source_lang == "en" and target_lang == "ko":
        return "로컬 번역 결과 (예시)"
    raise Exception("로컬 번역 실패")


# ✅ 2. OpenAI GPT fallback
def translate_openai(text: str, source_lang: str, target_lang: str) -> str:
    prompt = (
        f"Translate the following text from {source_lang} to {target_lang}:\n{text}"
    )
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


# ✅ 3. 통합 함수: 로컬 → 실패 시 OpenAI
def translate(text: str, source_lang: str = "en", target_lang: str = "ko") -> str:
    try:
        return translate_local(text, source_lang, target_lang)
    except Exception as e:
        print(f"⚠️ 로컬 번역 실패 → OpenAI fallback: {e}")
        return translate_openai(text, source_lang, target_lang)
