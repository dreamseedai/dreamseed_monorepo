# backend/routes/admin.py
from fastapi import APIRouter, Depends
from typing import Dict
from fastapi.responses import FileResponse
from weasyprint import HTML
from datetime import datetime
import os
import json

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/finance-summary")
def get_finance_summary() -> Dict:
    return {
        "total_ad_revenue": 18230,
        "total_star_balloons": 4021,
        "total_payments": 12435,
        "by_emotion": {"joy": 6200, "nostalgia": 5300, "healing": 2700},
        "by_country": {"KR": 8200, "US": 5800, "JP": 3300},
        "by_age": {"10s": 2400, "20s": 6800, "30s": 5400, "40s+": 2631},
        "by_gender": {"female": 9200, "male": 8000, "other": 1030},
        "by_hour": {
            "00:00–06:00": 1200,
            "06:00–12:00": 3400,
            "12:00–18:00": 5100,
            "18:00–24:00": 7530,
        },
    }


def load_translation(lang: str) -> dict:
    path = f"./backend/lang/{lang}.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


@router.get("/finance-report.pdf")
def get_lang_context() -> dict:
    # Example implementation of get_lang_context
    return {"lang": "en"}


def get_finance_report_pdf(t: dict = Depends(get_lang_context)):
    lang = t.get("lang", "en")
    t = load_translation(lang)
    now = datetime.now().strftime("%Y-%m-%d")
    filename = f"/tmp/finance_report_{lang}_{now}.pdf"

    html = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          body {{ font-family: sans-serif; padding: 20px; line-height: 1.6; }}
          h1 {{ color: #2c3e50; }}
        </style>
      </head>
      <body>
        <h1>{t.get("STRATEGY_SUMMARY", "Strategy Summary")} - {now}</h1>
        <p>{t.get("BRAND_NAME", "Brand Name")}: Happy Cola</p>
        <p>{t.get("LANGUAGE", "Language")}: {lang}</p>
      </body>
    </html>
    """

    HTML(string=html).write_pdf(filename)
    return FileResponse(
        filename, media_type="application/pdf", filename=os.path.basename(filename)
    )
