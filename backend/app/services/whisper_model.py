# app/services/whisper_model.py

import whisper

_model = None


def get_whisper_model():
    global _model
    if _model is None:
        print("✅ Whisper 모델 최초 로딩 중...")
        _model = whisper.load_model("base", device="cpu")  # 또는 "cuda"
    return _model
