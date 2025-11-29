# backend/feedback_api.py
from fastapi import APIRouter
from pydantic import BaseModel
import os
import json

router = APIRouter()

FEEDBACK_FILE = os.path.join(
    os.path.dirname(__file__), "../frontend/src/data/feedback.json"
)


class FeedbackItem(BaseModel):
    user_id: str
    content_title: str
    rating: int  # 1 to 5
    comment: str
    timestamp: str


@router.get("/api/feedback")
def get_feedback():
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@router.post("/api/feedback")
def save_feedback(feedback: FeedbackItem):
    existing = []
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    existing.append(feedback.dict())
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    return {"status": "received"}
