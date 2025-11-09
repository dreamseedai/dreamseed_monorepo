# backend/routes/status.py
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_optional_user  # 현재 로그인 유저 확인용
from app.services.llama_model import is_model_ready  # 모델 상태 확인 함수
from app.services.db import health_check  # DB 연결 테스트 함수

router = APIRouter()


@router.get("/api/status")
def get_system_status(current_user=Depends(get_optional_user)):
    return {
        "api": "ok",  # API 살아있음
        "db": "ok" if health_check() else "error",
        "user": current_user or None,
        "model": "connected" if is_model_ready() else "disconnected",
    }
