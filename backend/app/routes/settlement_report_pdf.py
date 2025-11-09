# backend/routes/settlement_report_pdf.py
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from app.services.lang_loader import load_translation
from app.services.settlement_data import get_creator_settlement_data
from weasyprint import HTML
import os
from datetime import datetime

router = APIRouter(prefix="/api/settlement", tags=["Settlement"])


@router.get("/settlement-report.pdf")
def get_settlement_report_pdf(creator: str, lang: str = Query("ko")):
    now = datetime.now().strftime("%Y-%m-%d")
    filename = f"/tmp/settlement_report_{creator}_{lang}_{now}.pdf"
    t = load_translation(lang)
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
        <meta charset=\"utf-8\" />
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
              <th>{t.get("FEE", "수수료")}</th>
              <th>{t.get("TAX", "세금")}</th>
              <th>{t.get("TOTAL", "정산액")}</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </body>
    </html>
    """

    HTML(string=html).write_pdf(filename)
    return FileResponse(
        filename, media_type="application/pdf", filename=os.path.basename(filename)
    )
