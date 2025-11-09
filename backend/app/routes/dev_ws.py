# app/routes/dev_ws.py

from fastapi import APIRouter, WebSocket
from datetime import datetime
import asyncio
import os
import json

try:
    import torch
except ImportError:
    torch = None

try:
    import psutil
except ImportError:
    psutil = None

router = APIRouter()


def get_realtime_status():
    return {
        "timestamp": datetime.now().isoformat(),
        "gpu_memory_allocated_MB": (
            round(torch.cuda.memory_allocated(0) / (1024**2), 2)
            if torch and torch.cuda.is_available()
            else 0
        ),
        "memory_usage_percent": psutil.virtual_memory().percent if psutil else 0,
        "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
    }


@router.websocket("/ws/dev/status")
async def stream_dev_status(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            status = get_realtime_status()
            await websocket.send_text(json.dumps(status))
            await asyncio.sleep(5)
    except Exception as e:
        print(f"[WebSocket] Connection closed: {e}")
