# backend/geo_emotion_api.py
from fastapi import APIRouter
import random

router = APIRouter()


@router.get("/api/geo-emotions")
def get_geo_emotions():
    # 임시 국가별 감정 분포 데이터
    emotions = ["기쁨", "외로움", "스트레스", "안정", "그리움"]
    countries = ["한국", "미국", "중국", "일본", "독일", "영국"]
    coordinates = {
        "한국": [37.5665, 126.9780],
        "미국": [38.9072, -77.0369],
        "중국": [39.9042, 116.4074],
        "일본": [35.6895, 139.6917],
        "독일": [52.5200, 13.4050],
        "영국": [51.5074, -0.1278],
    }
    result = []
    for c in countries:
        result.append(
            {
                "country": c,
                "emotion": random.choice(emotions),
                "count": random.randint(5, 200),
                "lat": coordinates[c][0],
                "lng": coordinates[c][1],
            }
        )
    return result
