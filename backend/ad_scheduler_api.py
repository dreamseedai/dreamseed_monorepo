# backend/ad_scheduler_api.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter()


class AdSlot(BaseModel):
    time_slot: str  # "07:00", "21:00"
    emotion: str
    brand: str
    message: str


ad_schedule: List[AdSlot] = [
    AdSlot(
        time_slot="08:00",
        emotion="스트레스 해소",
        brand="삼성헬스",
        message="오늘도 편안하게 시작해보세요.",
    ),
    AdSlot(
        time_slot="21:00",
        emotion="회상",
        brand="현대자동차",
        message="그 시절 감성에 함께합니다.",
    ),
]


@router.get("/api/ad-scheduler")
def get_schedule():
    return ad_schedule


@router.post("/api/ad-scheduler")
def add_slot(slot: AdSlot):
    ad_schedule.append(slot)
    return {"status": "added", "slot": slot}


@router.get("/api/ad-scheduler/now")
def get_now_ad():
    now = datetime.now().strftime("%H:00")
    for ad in ad_schedule:
        if ad.time_slot == now:
            return ad
    return {"status": "no-ad"}
