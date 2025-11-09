# backend/live_status_api.py
from fastapi import APIRouter
import random

router = APIRouter()


@router.get("/api/live-status/{creator_id}")
def get_live_status(creator_id: str):
    # TODO: Replace with actual stream check logic
    is_live = random.choice([True, False])
    return {"creator_id": creator_id, "live": is_live}
