from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from weasyprint import HTML
import os
from typing import List, Dict

router = APIRouter(prefix="/api/sponsor", tags=["Sponsor"])

# -------------------- 기본 브랜드 데이터 --------------------
sponsor_data = {
    "happycola": {
        "brand_name": "Happy Cola",
        "total_views": 128309,
        "total_inserted_ads": 94,
        "total_star_balloons": 2284,
        "viewer_distribution": {
            "gender": {"male": 45, "female": 53, "other": 2},
            "age": {"10s": 12, "20s": 38, "30s": 30, "40s+": 20},
            "country": {"KR": 70, "US": 15, "JP": 10, "Other": 5},
        },
    },
}


# -------------------- 요약 정보 --------------------
@router.get("/{brand_id}/summary")
def get_sponsor_summary(brand_id: str) -> Dict:
    brand = sponsor_data.get(brand_id.lower())
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


# -------------------- 감정 반응 리포트 --------------------
@router.get("/{brand_id}/emotion-report")
def get_emotion_report(brand_id: str):
    mock_emotion_data = {
        "happycola": [
            {
                "emotion": "nostalgia",
                "engagement_score": 8.2,
                "top_age": "30s",
                "top_country": "KR",
                "best_programs": ["추억의 K-POP", "응답하라 콘텐츠"],
            },
            {
                "emotion": "joy",
                "engagement_score": 7.8,
                "top_age": "20s",
                "top_country": "US",
                "best_programs": ["K-POP Highlights", "AI 웃긴 방송"],
            },
        ]
    }

    data = mock_emotion_data.get(brand_id.lower())
    if not data:
        raise HTTPException(status_code=404, detail="Emotion data not found")
    return {"emotions": data}


@router.get("/{brand_id}/contracts")
def list_contracts(brand_id: str) -> List[dict]:
    path = "/tmp"
    keyword = f"contract_{brand_id}_"
    contracts = []

    for fname in os.listdir(path):
        if fname.startswith(keyword) and fname.endswith(".pdf"):
            contracts.append(
                {
                    "file_name": fname,
                    "url": f"/api/sponsor/{brand_id}/contracts/{fname}",
                }
            )

    return contracts


# -------------------- 광고 전략 도우미 --------------------
class RecommendationRequest(BaseModel):
    target_age: str
    target_gender: str
    target_emotion: str
    budget: float


class RecommendedSlot(BaseModel):
    program: str
    emotion: str
    time_range: str
    expected_cpm: float
    expected_reach: int


class ContractRequest(BaseModel):
    brand_name: str
    start_date: str  # "YYYY-MM-DD"
    end_date: str
    total_price: float
    contact_person: str


@router.post("/{brand_id}/recommendations")
def recommend_slots(
    brand_id: str, request: RecommendationRequest
) -> List[RecommendedSlot]:
    # 실제 AI 분석 또는 DB 로직 대체 가능
    return [
        {
            "program": "K-POP Festival Highlights",
            "emotion": request.target_emotion,
            "time_range": "Sat 20:00–22:00",
            "expected_cpm": 4.2,
            "expected_reach": 12000,
        },
        {
            "program": "AI 감정 뉴스 리포트",
            "emotion": request.target_emotion,
            "time_range": "Mon 08:00–10:00",
            "expected_cpm": 3.5,
            "expected_reach": 9500,
        },
    ]


@router.post("/{brand_id}/contract")
def generate_contract_pdf(brand_id: str, contract: ContractRequest):
    filename = f"/tmp/contract_{brand_id}_{contract.start_date}.pdf"

    html = f"""
    <html>
      <head>
        <style>
          body {{ font-family: sans-serif; padding: 30px; line-height: 1.6; }}
          h1 {{ color: #2c3e50; }}
          .section {{ margin-bottom: 24px; }}
        </style>
      </head>
      <body>
        <h1>📄 광고 계약서</h1>
        <div class="section">계약 브랜드: <strong>{contract.brand_name}</strong></div>
        <div class="section">계약 기간: {contract.start_date} ~ {contract.end_date}</div>
        <div class="section">총 금액: <strong>${contract.total_price:,.2f}</strong> (USD)</div>
        <div class="section">담당자명: {contract.contact_person}</div>

        <div class="section">
          <p>본 계약은 광고 서비스 제공을 목적으로 하며, 양 당사자는 상호 협의하에 계약 내용을 성실히 이행할 것을 동의합니다.</p>
        </div>

        <div style="margin-top:50px;">
          <p>광고주 서명: _____________________________</p>
          <p>플랫폼 서명: _____________________________</p>
        </div>
      </body>
    </html>
    """

    try:
        HTML(string=html).write_pdf(filename)
        return FileResponse(
            filename, media_type="application/pdf", filename=os.path.basename(filename)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 생성 실패: {str(e)}")
