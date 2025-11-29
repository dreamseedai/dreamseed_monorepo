# backend/sponsor_stats_api.py
from fastapi import APIRouter
from pydantic import BaseModel
import random
import os
from fpdf import FPDF
import datetime

router = APIRouter()


@router.get("/api/sponsor-stats/{brand}")
def sponsor_stats(brand: str):
    sample_data = [
        {
            "program": "감성 드라마 채널",
            "views": random.randint(1000, 5000),
            "stars": random.randint(10, 200),
            "emotion": random.choice(["감동", "회상", "기쁨"]),
            "age_group": random.choice(["10대", "20대", "30대", "40대", "50대"]),
            "gender": random.choice(["남성", "여성"]),
            "country": random.choice(["한국", "미국", "일본", "중국"]),
        }
        for _ in range(10)
    ]
    return sample_data


class SummaryRequest(BaseModel):
    brand: str
    summary: str


@router.post("/api/sponsor-summary-pdf")
def generate_sponsor_pdf(req: SummaryRequest):
    filename = (
        f"sponsor_{req.brand}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    filepath = os.path.join("frontend", "public", filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt=f"{req.brand} 광고 효과 전략 요약", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, req.summary)

    pdf.output(filepath)
    return {"file": f"/{filename}"}
