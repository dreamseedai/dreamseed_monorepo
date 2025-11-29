# backend/routes/settlement.py
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from backend.utils.lang_loader import get_lang_context
from backend.services.settlement_data import get_creator_settlement_data
from weasyprint import HTML
import csv
import os
from datetime import datetime

router = APIRouter(prefix="/api/settlement", tags=["Settlement"])


# settlement_data.py
def get_creator_settlement_data(creator_id: str):
    # Mock implementation for demonstration
    return [
        {"date": "2023-10-01", "ads": 100, "stars": 50},
        {"date": "2023-10-02", "ads": 200, "stars": 75},
    ]


@router.get("/creator/{creator_id}")
def download_settlement_csv(creator_id: str, lang: str = "en"):
    filename = f"/tmp/settlement_{creator_id}_{lang}.csv"
    data = get_creator_settlement_data(creator_id)

    # 언어 번역 로드
    from backend.utils.lang_loader import load_translation

    t = load_translation(lang)

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                t.get("SETTLEMENT_DATE", "날짜"),
                t.get("ADS_REVENUE", "광고 수익"),
                t.get("STARS_REVENUE", "별풍선 수익"),
                t.get("FEE", "수수료(10%)"),
                t.get("TAX", "세금(3%)"),
                t.get("TOTAL", "정산액"),
            ]
        )
        for row in data:
            total = row["ads"] + row["stars"]
            fee = round(total * 0.10, 2)
            tax = round(total * 0.03, 2)
            net = round(total - fee - tax, 2)
            writer.writerow([row["date"], row["ads"], row["stars"], fee, tax, net])

    return FileResponse(
        filename,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={os.path.basename(filename)}"
        },
    )


@router.get("/settlement-report.pdf")
def get_settlement_report_pdf(creator: str, t: dict = Depends(get_lang_context)):
    now = datetime.now().strftime("%Y-%m-%d")
    filename = f"/tmp/settlement_report_{creator}_{now}.pdf"
    data = get_creator_settlement_data(creator)

    rows = ""
    for row in data:
        total = row["ads"] + row["stars"]
        fee = round(total * 0.10, 2)
        tax = round(total * 0.03, 2)
        net = round(total - fee - tax, 2)

        rows += f"""
            <tr>
                <td>{row['date']}</td>
                <td>{row['ads']}</td>
                <td>{row['stars']}</td>
                <td>{fee}</td>
                <td>{tax}</td>
                <td>{net}</td>
            </tr>
        """

    html = f"""
        <html>
        <head>
        <meta charset="utf-8" />
        <style>
        body {{ font-family: sans-serif; padding: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
        th {{ background: #f4f4f4; }}
        </style>
        </head>
        <body>
        <h1>{t.get("SETTLEMENT_SUMMARY", "정산 보고서")} – {now}</h1>
        <p>{t.get("CREATOR", "크리에이터")}: {creator}</p>

        <table>
        <thead>
            <tr>
            <th>{t.get("SETTLEMENT_DATE", "날짜")}</th>
            <th>{t.get("ADS_REVENUE", "광고 수익")}</th>
            <th>{t.get("STARS_REVENUE", "별풍선 수익")}</th>
            <th>{t.get("FEE", "수수료(10%)")}</th>
            <th>{t.get("TAX", "세금(3%)")}</th>
            <th>{t.get("TOTAL", "정산액")}</th>
            </tr>
        </thead>
        <tbody>
        {rows}
        </tbody>
        </table>

        <div style="margin-top:40px;">
        <p>{t.get("CREATOR_SIGNATURE", "크리에이터 서명")}:</p>
        <img src="file:///home/won/myktube_clean/static/signatures/{creator}.png" width="200" />

        <p>{t.get("PLATFORM_SIGNATURE", "플랫폼 서명")}:</p>
        <img src="file:///home/won/myktube_clean/static/signatures/platform.png" width="200" />
        </div>

        </body>
        </html>
    """
    HTML(string=html).write_pdf(filename)
    return FileResponse(
        filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={os.path.basename(filename)}"
        },
    )
