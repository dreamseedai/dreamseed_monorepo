# backend/star_gift_api.py
from fastapi import APIRouter
from pydantic import BaseModel
import os
import json

router = APIRouter()

STAR_FILE = os.path.join(
    os.path.dirname(__file__), "../frontend/src/data/star_gifts.json"
)


class StarGift(BaseModel):
    sender_id: str
    receiver_id: str
    amount: int
    message: str
    country: str
    timestamp: str


@router.get("/api/star-gifts/{receiver_id}")
def get_star_gifts(receiver_id: str):
    if os.path.exists(STAR_FILE):
        with open(STAR_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
            return [g for g in all_data if g["receiver_id"] == receiver_id]
    return []


@router.post("/api/star-gifts")
def post_star_gift(gift: StarGift):
    data = []
    if os.path.exists(STAR_FILE):
        with open(STAR_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append(gift.dict())
    with open(STAR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"status": "sent", "gift": gift}
