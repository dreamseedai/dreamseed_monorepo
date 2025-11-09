# backend/routes/settlement_excel_api.py
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from openpyxl import Workbook
from app.services.lang_loader import load_translation
from app.services.settlement_data import get_creator_settlement_data
import os
from datetime import datetime

router = APIRouter(prefix="/api/settlement", tags=["Settlement"])


@router.get("/settlement-report.xlsx")
def download_settlement_excel(creator: str, lang: str = Query("ko")):
    now = datetime.now().strftime("%Y-%m-%d")
    filename = f"/tmp/settlement_{creator}_{lang}_{now}.xlsx"
    t = load_translation(lang)
    data = get_creator_settlement_data(creator)

    wb = Workbook()
    ws = wb.active
    ws.title = t.get("SETTLEMENT_SUMMARY", "정산 보고서")

    headers = [
        t.get("SETTLEMENT_DATE", "날짜"),
        t.get("ADS_REVENUE", "광고 수익"),
        t.get("STARS_REVENUE", "별풍선 수익"),
        t.get("FEE", "수수료"),
        t.get("TAX", "세금"),
        t.get("TOTAL", "정산액"),
    ]
    ws.append(headers)

    for row in data:
        total = row["ads"] + row["stars"]
        fee = round(total * 0.10, 2)
        tax = round(total * 0.03, 2)
        net = round(total - fee - tax, 2)

        ws.append([row["date"], row["ads"], row["stars"], fee, tax, net])

    wb.save(filename)
    return FileResponse(
        filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(filename),
    )
