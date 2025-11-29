# backend/analytics_api.py
from fastapi import APIRouter
import random

router = APIRouter()


@router.get("/api/analytics/global")
def global_analytics():
    # 임시 더미 데이터 - 실제로는 DB나 로그에서 집계해야 함
    users_by_country = {
        "한국": random.randint(100, 500),
        "미국": random.randint(100, 500),
        "중국": random.randint(100, 500),
        "일본": random.randint(100, 500),
        "독일": random.randint(50, 200),
        "기타": random.randint(20, 100),
    }

    usage_by_mode = [
        {"mode": "tv", "avgMinutes": random.randint(20, 60)},
        {"mode": "radio", "avgMinutes": random.randint(30, 90)},
        {"mode": "news", "avgMinutes": random.randint(10, 40)},
    ]

    return {"usersByCountry": users_by_country, "usageByMode": usage_by_mode}
