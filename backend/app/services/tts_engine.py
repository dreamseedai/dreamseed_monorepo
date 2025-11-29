# app/services/tts_engine.py
from app.services.ai_flags import USE_LOCAL_AI

if USE_LOCAL_AI:
    from TTS.api import TTS

    tts = TTS(model_name="tts_models/ko/kss/tacotron2-DDC", progress_bar=False)
else:
    tts = None
