# backend/creator_map_api.py
from fastapi import APIRouter
import random

router = APIRouter()


@router.get("/api/creator-map/{creator_id}")
def get_creator_map(creator_id: str):
    countries = ["한국", "미국", "중국", "일본", "독일", "영국"]
    emotions = ["기쁨", "감동", "스트레스", "공감", "재미"]
    coordinates = {
        "한국": [37.5665, 126.9780],
        "미국": [38.9072, -77.0369],
        "중국": [39.9042, 116.4074],
        "일본": [35.6895, 139.6917],
        "독일": [52.5200, 13.4050],
        "영국": [51.5074, -0.1278],
    }
    return [
        {
            "country": c,
            "lat": coordinates[c][0],
            "lng": coordinates[c][1],
            "emotion": random.choice(emotions),
            "count": random.randint(10, 300),
        }
        for c in countries
    ]
