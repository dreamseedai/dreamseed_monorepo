# app/routes/whisper_emotion.py

from fastapi import APIRouter, UploadFile, File
import tempfile
import os
from openai import OpenAI

from app.services.db import save_emotion_log
from app.services.whisper_model import get_whisper_model

router = APIRouter()


def analyze_emotion(text: str) -> str:
    prompt = f"""
    다음 텍스트의 화자 감정을 아래 중 하나로 판단하세요:
    [기쁨, 슬픔, 분노, 놀람, 평온, 불안, 사랑]

    텍스트: "{text}"
    감정만 한 단어로 반환하세요.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # ✅ 요청 시점 초기화
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


@router.post("/whisper/transcribe-analyze")
async def transcribe_and_analyze(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    model = get_whisper_model()  # ✅ 요청 시점에 로딩

    result = model.transcribe(tmp_path, language="ko")
    text = result["text"]

    emotion = analyze_emotion(text)
    save_emotion_log(text, emotion)

    return {"transcript": text, "emotion": emotion}
