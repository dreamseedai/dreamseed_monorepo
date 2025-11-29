# backend/advertiser_proposal_api.py
from fastapi import APIRouter
from pydantic import BaseModel
from fpdf import FPDF
import os
import datetime

router = APIRouter()


class ProposalRequest(BaseModel):
    emotion: str
    brands: list[str]
    summary: str


@router.post("/api/advertiser-proposal")
def generate_proposal(req: ProposalRequest):
    filename = f"proposal_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join("frontend", "public", filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="감성 채널 광고 제안서", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"📌 감정 주제: {req.emotion}")
    pdf.ln(5)
    pdf.multi_cell(0, 10, "💡 제안 브랜드:")
    for brand in req.brands:
        pdf.cell(10)
        pdf.multi_cell(0, 10, f"- {brand}")
    pdf.ln(5)
    pdf.multi_cell(0, 10, f"📋 전략 요약: {req.summary}")

    pdf.output(filepath)
    return {"file": f"/{filename}"}
