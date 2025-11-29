from fastapi import APIRouter, HTTPException
from backend.services.settlement_data import get_creator_settlement_data
from backend.utils.lang_loader import load_translation
from backend.config import email_config
from weasyprint import HTML
from email.message import EmailMessage
import smtplib
import os
from datetime import datetime

router = APIRouter(prefix="/api/settlement", tags=["Settlement"])


@router.post("/send-email")
def send_settlement_email(creator_id: str, recipient_email: str, lang: str = "en"):
    # PDF 생성
    now = datetime.now().strftime("%Y-%m-%d")
    filename = f"/tmp/settlement_report_{creator_id}_{now}.pdf"
    t = load_translation(lang)
    data = get_creator_settlement_data(creator_id)

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
    <html><body>
    <h1>{t.get("SETTLEMENT_SUMMARY", "정산 보고서")} – {now}</h1>
    <p>{t.get("CREATOR", "크리에이터")}: {creator_id}</p>
    <table border="1" cellspacing="0" cellpadding="5">
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
    </table></body></html>
    """

    HTML(string=html).write_pdf(filename)

    # 이메일 구성
    msg = EmailMessage()
    msg["Subject"] = f"{t.get('SETTLEMENT_SUMMARY', '정산 보고서')} – {creator_id}"
    msg["From"] = email_config.EMAIL_ADDRESS
    msg["To"] = recipient_email
    msg.set_content("정산서를 첨부해 드립니다. 감사합니다.")

    with open(filename, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(filename),
        )

    # 이메일 발송
    try:
        with smtplib.SMTP(email_config.EMAIL_HOST, email_config.EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(email_config.EMAIL_ADDRESS, email_config.EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이메일 전송 실패: {str(e)}")

    return {"message": "정산서 이메일 발송 완료", "to": recipient_email}
