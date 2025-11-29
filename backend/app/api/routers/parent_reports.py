"""
Parent report PDF download API

Endpoints:
- GET /api/parent/reports/{student_id}/pdf: Download parent report as PDF
"""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_current_parent
from app.models.parent_models import ParentChildLink
from app.models.user import User
from app.services.parent_report_builder import build_parent_report_data
from app.services.pdf_report_service import generate_parent_report_pdf

router = APIRouter(prefix="/api/parent/reports", tags=["parent:reports"])


def parse_period(period: str) -> tuple[datetime, datetime]:
    """
    Parse period string to start/end datetime.

    Supported formats:
    - "last4w": Last 4 weeks (28 days)
    - "last8w": Last 8 weeks (56 days)
    - "semester": Last semester (~120 days)
    - "2024-11-01,2024-11-30": Custom date range (YYYY-MM-DD,YYYY-MM-DD)

    Returns:
        Tuple of (start_datetime, end_datetime)

    Raises:
        HTTPException 400: If period format is invalid
    """
    now = datetime.utcnow()

    if period == "last4w":
        return now - timedelta(days=28), now
    elif period == "last8w":
        return now - timedelta(days=56), now
    elif period == "semester":
        return now - timedelta(days=120), now
    elif "," in period:
        try:
            start_str, end_str = period.split(",")
            start = datetime.strptime(start_str.strip(), "%Y-%m-%d")
            end = datetime.strptime(end_str.strip(), "%Y-%m-%d")
            return start, end
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date range format. Use YYYY-MM-DD,YYYY-MM-DD: {e}",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid period. Use 'last4w', 'last8w', 'semester', or 'YYYY-MM-DD,YYYY-MM-DD'",
        )


@router.get("/{student_id}/pdf")
async def download_parent_report_pdf(
    student_id: UUID,
    period: str = "last4w",
    db: AsyncSession = Depends(get_async_session),
    parent: User = Depends(get_current_parent),
):
    """
    Download parent report as PDF.

    Args:
        student_id: Child's user ID
        period: Time period for report (default: last4w)

    Returns:
        PDF file as application/pdf response

    Raises:
        HTTPException 403: If parent doesn't have access to this child
        HTTPException 404: If no data found for period
    """
    # Verify parent-child relationship
    link_query = select(ParentChildLink).where(
        ParentChildLink.parent_id == parent.id,
        ParentChildLink.child_id == student_id,
    )
    link_result = await db.execute(link_query)
    link = link_result.scalar_one_or_none()

    if not link:
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this student's reports",
        )

    # Parse period
    start, end = parse_period(period)

    # Build report data (multi-source: ability + teacher + tutor comments)
    try:
        report_data = await build_parent_report_data(
            db=db,
            student_id=student_id,
            period_start=start,
            period_end=end,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build report data: {str(e)}",
        )

    # Generate PDF
    try:
        pdf_bytes = generate_parent_report_pdf(report_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}",
        )

    # Return as downloadable file
    filename = f"DreamSeed_Report_{student_id}_{period}.pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers,
    )
