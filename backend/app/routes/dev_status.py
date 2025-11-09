# app/routes/dev_status.py

from fastapi import APIRouter, Request
from datetime import datetime
from app.services.model_registry import get_registered_models
import os

# 선택적 모듈 import
try:
    import torch
except ImportError:
    torch = None

try:
    import psutil
except ImportError:
    psutil = None

try:
    import transformers
except ImportError:
    transformers = None

from app.services.ai_flags import USE_LOCAL_AI

router = APIRouter()


@router.get("/api/dev/status")
def get_dev_status(request: Request):
    # GPU 상태
    gpu_status = {}
    if torch and torch.cuda.is_available():
        gpu_status = {
            "torch_cuda_available": True,
            "cuda_device_count": torch.cuda.device_count(),
            "cuda_device_name": torch.cuda.get_device_name(0),
            "cuda_memory_allocated_MB": round(
                torch.cuda.memory_allocated(0) / (1024**2), 2
            ),
            "cuda_memory_reserved_MB": round(
                torch.cuda.memory_reserved(0) / (1024**2), 2
            ),
        }
    elif torch:
        gpu_status = {"torch_cuda_available": False}

    # 시스템 메모리 상태
    memory_status = {}
    if psutil:
        mem = psutil.virtual_memory()
        memory_status = {
            "total_memory_MB": round(mem.total / (1024**2), 2),
            "available_memory_MB": round(mem.available / (1024**2), 2),
            "used_memory_MB": round(mem.used / (1024**2), 2),
            "memory_usage_percent": mem.percent,
        }

    # 로딩된 모델 정보 (심화 확장 가능)
    loaded_model_info = {
        "transformers_version": transformers.__version__ if transformers else None,
        "models_loaded": get_registered_models(),
    }

    # 등록된 FastAPI 라우터 목록
    route_info = [
        {
            "path": route.path,
            "name": route.name,
            "method": list(route.methods)[0] if route.methods else "N/A",
        }
        for route in request.app.routes
        if route.path.startswith("/api")
    ]

    return {
        "app_version": os.getenv("APP_VERSION", "dev"),
        "server_time": datetime.now().isoformat(),
        "USE_LOCAL_AI": USE_LOCAL_AI,
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "WHISPER_ACTIVE": True,
        "TTS_ACTIVE": True,
        "CHAT_ACTIVE": True,
        "TRANSLATE_ACTIVE": True,
        "gpu_status": gpu_status,
        "memory_status": memory_status,
        "loaded_model_info": loaded_model_info,
        "registered_routes": route_info,
        "registered_route_count": len(route_info),
    }
