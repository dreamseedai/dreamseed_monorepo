# app/routes/whisper_emotion.py

from fastapi import APIRouter, UploadFile, File, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import tempfile
import os
import random

from openai import OpenAI

from app.db.database import get_db  # FastAPI DI 방식으로 변경
from app.db.models import EmotionLog
from app.services.db import save_emotion_log
from app.services.emotion_recommendation import generate_emotion_recommendation
from app.services.strategy import get_epsilon_greedy_recommendation
from app.services.whisper_model import get_whisper_model  # lazy load 방식 적용

router = APIRouter()


def analyze_emotion(text: str) -> str:
    prompt = f"""
    다음 텍스트의 화자 감정을 아래 중 하나로 판단하세요:
    [기쁨, 슬픔, 분노, 놀람, 평온, 불안, 사랑]

    텍스트: "{text}"
    감정만 한 단어로 반환하세요.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # 요청 시점 초기화
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

    try:
        model = get_whisper_model()
        result = model.transcribe(tmp_path, language="ko")
        text = result["text"]

        emotion = analyze_emotion(text)
        save_emotion_log(text, emotion)

        strategy = random.choice(["gpt", "rl"])

        if strategy == "gpt":
            recommendation = generate_emotion_recommendation(emotion)
            recommendation["strategy"] = "gpt"
        else:
            category = get_epsilon_greedy_recommendation(emotion, epsilon=0.2)
            recommendation = {
                "feedback": f"'{emotion}' 감정에 공감하며 추천드려요.",
                "keywords": [emotion, "감정"],
                "category": category,
                "description": f"{category} 콘텐츠로 감정을 표현하고 배워보세요.",
                "strategy": "rl",
            }

        return {
            "transcript": text,
            "emotion": emotion,
            "recommendation": recommendation,
        }
    finally:
        os.remove(tmp_path)


@router.get("/emotion-log-recent")
def recent_emotion_logs(
    emotion: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),  # FastAPI 방식으로 DB 세션 주입
):
    query = db.query(EmotionLog)

    if emotion:
        query = query.filter(EmotionLog.emotion == emotion)
    if from_date:
        query = query.filter(EmotionLog.created_at >= from_date)
    if to_date:
        query = query.filter(EmotionLog.created_at <= to_date)

    logs = query.order_by(EmotionLog.created_at.desc()).limit(100).all()

    return [
        {
            "id": log.id,
            "emotion": log.emotion,
            "input": log.input,
            "created_at": log.created_at,
        }
        for log in logs
    ]
