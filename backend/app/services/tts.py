# services/tts.py

from gtts import gTTS
import os
import uuid


def speak_korean(text: str) -> str:
    """
    입력된 텍스트를 한국어 TTS로 변환하고 mp3 파일로 저장한 뒤 경로 반환
    """
    tts = gTTS(text=text, lang="ko")
    filename = f"tts_{uuid.uuid4().hex}.mp3"
    filepath = f"static/tts/{filename}"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    tts.save(filepath)
    return f"/static/tts/{filename}"
