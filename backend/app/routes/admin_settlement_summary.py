# backend/routes/admin_settlement_summary.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# 예시 데이터 (실제 DB에서 집계 예정)
mock_settlement_summary = [
    {
        "month": "2024-05",
        "ads_total": 4820,
        "stars_total": 2170,
        "fee": 699.0,
        "tax": 210.0,
        "net_total": 6081.0,
    },
    {
        "month": "2024-06",
        "ads_total": 3550,
        "stars_total": 1850,
        "fee": 540.0,
        "tax": 160.0,
        "net_total": 4700.0,
    },
]


@router.get("/settlement-summary")
def get_monthly_settlement_summary():
    return {"summary": mock_settlement_summary}
