from fastapi import APIRouter
from fastapi.responses import FileResponse
import csv
import os

router = APIRouter(prefix="/api/settlement", tags=["Settlement"])


@router.get("/creator/{creator_id}")
def download_settlement_csv(creator_id: str, lang: str = "en"):
    filename = f"/tmp/settlement_{creator_id}_{lang}.csv"

    # 예시 정산 데이터 (실제로는 DB 조회)
    data = [
        {"date": "2025-05-01", "ads": 150.0, "stars": 70.0},
        {"date": "2025-05-02", "ads": 90.0, "stars": 120.0},
        {"date": "2025-05-03", "ads": 110.0, "stars": 60.0},
    ]

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["날짜", "광고 수익", "별풍선 수익", "수수료(10%)", "세금(3%)", "정산액"]
        )
        for row in data:
            fee = (row["ads"] + row["stars"]) * 0.10
            tax = (row["ads"] + row["stars"]) * 0.03
            net = (row["ads"] + row["stars"]) - fee - tax
            writer.writerow(
                [
                    row["date"],
                    row["ads"],
                    row["stars"],
                    round(fee, 2),
                    round(tax, 2),
                    round(net, 2),
                ]
            )

    return FileResponse(
        filename, media_type="text/csv", filename=os.path.basename(filename)
    )
