"""
Exam Result PDF Renderer
Generates branded PDF reports for exam results with score breakdown and analysis.
"""
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _setup_korean_font(font_path: Optional[str] = None, font_name: str = "NotoSans"):
    """Register Korean font if available"""
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            return font_name
        except Exception:
            pass
    return "Helvetica"


def _get_page_size(format: str = "A4"):
    """Get page size (A4 or Letter)"""
    return A4 if format.upper() == "A4" else letter


def render_exam_pdf(
    result_data: Dict[str, Any],
    tutor_brand: str = "DreamSeed",
    logo_url: Optional[str] = None,
    page_format: str = "A4",
    korean_font_path: Optional[str] = None,
) -> bytes:
    """
    Render exam result to PDF bytes.
    
    Args:
        result_data: Exam result JSON (from /api/seedtest/exams/{session_id}/result)
        tutor_brand: School/Tutor brand name
        logo_url: Optional logo URL (not implemented yet)
        page_format: "A4" or "Letter"
        korean_font_path: Path to Korean TTF font
        
    Returns:
        PDF bytes
    """
    font_name = _setup_korean_font(korean_font_path)
    pagesize = _get_page_size(page_format)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=18,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=12,
    )
    
    # 1. Header (Brand + Title)
    story.append(Paragraph(tutor_brand, title_style))
    story.append(Paragraph("Exam Result Report", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * inch))
    
    # 2. Student Info
    session_id = result_data.get("session_id", "N/A")
    user_id = result_data.get("user_id", "Anonymous")
    created_at = result_data.get("created_at", "")
    
    info_data = [
        ["Session ID:", session_id],
        ["Student:", user_id],
        ["Date:", created_at[:19] if created_at else "N/A"],
    ]
    
    info_table = Table(info_data, colWidths=[1.5 * inch, 4 * inch])
    info_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    story.append(info_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # 3. Score Summary
    summary = result_data.get("summary", {})
    score_scaled = summary.get("score_scaled", 0)
    correct = summary.get("correct", 0)
    total = summary.get("total", 0)
    percentile = summary.get("percentile", 0)
    
    story.append(Paragraph("Score Summary", styles["Heading3"]))
    score_data = [
        ["Scaled Score", f"{score_scaled:.1f}"],
        ["Correct / Total", f"{correct} / {total}"],
        ["Percentile", f"{percentile:.1f}%"],
    ]
    
    score_table = Table(score_data, colWidths=[2 * inch, 2 * inch])
    score_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f4f6")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#374151")),
            ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor("#1e40af")),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWHEIGHT", (0, 0), (-1, -1), 24),
        ])
    )
    story.append(score_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # 4. Topic Breakdown
    by_topic = result_data.get("breakdown", {}).get("by_topic", [])
    if by_topic:
        story.append(Paragraph("Topic Breakdown", styles["Heading3"]))
        
        topic_data = [["Topic", "Correct", "Total", "Accuracy"]]
        for topic in by_topic[:10]:  # Limit to 10 topics
            name = topic.get("topic", "Unknown")
            tc = topic.get("correct", 0)
            tt = topic.get("total", 0)
            acc = (tc / tt * 100) if tt > 0 else 0
            topic_data.append([name, str(tc), str(tt), f"{acc:.0f}%"])
        
        topic_table = Table(
            topic_data,
            colWidths=[2.5 * inch, 0.8 * inch, 0.8 * inch, 1 * inch],
        )
        topic_table.setStyle(
            TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ])
        )
        story.append(topic_table)
        story.append(Spacer(1, 0.2 * inch))
    
    # 5. Recommendations
    recs = result_data.get("recommendations", [])
    if recs:
        story.append(Paragraph("Recommendations", styles["Heading3"]))
        for i, rec in enumerate(recs[:5], 1):  # Top 5
            story.append(Paragraph(f"{i}. {rec}", styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))
    
    # 6. Footer
    story.append(Spacer(1, 0.5 * inch))
    footer_text = f"Generated by {tutor_brand} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(Paragraph(footer_text, styles["Italic"]))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()
