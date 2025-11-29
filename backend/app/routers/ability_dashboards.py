"""
FastAPI router for irt_student_abilities-based dashboards.

Endpoints:
- GET /api/abilities/me/summary - Student ability summary (all subjects)
- GET /api/abilities/me/trend - Student theta trend over time
- GET /api/tutor/priorities - Tutor priority list of students
- GET /api/parent/reports/{studentId} - Parent PDF report generation
"""

import uuid
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.exam_models import IRTStudentAbility
from app.models.user import (
    User,  # TODO: Adjust import based on actual User model location
)
from app.schemas.ability_schemas import (
    ParentReportData,
    StudentAbilitySummaryResponse,
    StudentThetaTrendResponse,
    SubjectAbilitySummary,
    ThetaTrendPoint,
    TutorPriorityListResponse,
    TutorPriorityStudent,
)
from app.services.ability_analytics import (
    assess_risk_level,
    classify_theta_band,
    compute_delta_theta,
    compute_empirical_percentile,
    compute_priority_score,
    compute_student_flags,
    count_recent_sessions,
    generate_recommended_action,
    generate_student_status_label,
    generate_tutor_recommended_focus,
    get_last_activity,
    theta_to_percentile,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["abilities"])


# ============================================================================
# Student Dashboard Endpoints
# ============================================================================


@router.get("/abilities/me/summary", response_model=StudentAbilitySummaryResponse)
async def get_student_ability_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current ability summary for logged-in student (all subjects).

    Returns:
        - Current theta, SE, band, percentile per subject
        - 7-day delta theta
        - Risk level and status label
        - Recommended next action

    Authorization:
        Requires student role (self-view only)
    """
    # Query all abilities for this student
    stmt = (
        select(IRTStudentAbility)
        .where(IRTStudentAbility.user_id == str(current_user.id))
        .order_by(IRTStudentAbility.subject, IRTStudentAbility.calibrated_at.desc())
    )
    result = await db.execute(stmt)
    abilities = result.scalars().all()

    if not abilities:
        raise HTTPException(
            status_code=404,
            detail="No ability data found. Complete at least one exam to get your ability estimate.",
        )

    # Group by subject, take most recent per subject
    subject_map = {}
    for ability in abilities:
        if ability.subject not in subject_map:
            subject_map[ability.subject] = ability

    # Build summary for each subject
    subject_summaries = []
    latest_calibration = max(a.calibrated_at for a in abilities)

    for subject, ability in subject_map.items():
        # Compute delta theta (7 days)
        delta_theta_7d = await compute_delta_theta(
            db=db,
            user_id=str(current_user.id),
            subject=subject,
            days=7,
        )

        # Classify
        theta_band = classify_theta_band(ability.theta)
        risk_level = assess_risk_level(ability.theta, ability.theta_se)

        # Percentile (empirical if possible, else theoretical)
        try:
            percentile = await compute_empirical_percentile(
                db=db, subject=subject, theta=ability.theta
            )
        except Exception:
            percentile = theta_to_percentile(ability.theta)

        # Status and recommendation
        status_label = generate_student_status_label(risk_level, delta_theta_7d)
        recommended_action = generate_recommended_action(
            theta=ability.theta,
            theta_band=theta_band,
            delta_theta_7d=delta_theta_7d,
            risk_level=risk_level,
        )

        subject_summaries.append(
            SubjectAbilitySummary(
                subject=subject,
                theta=ability.theta,
                thetaSe=ability.theta_se,
                thetaBand=theta_band,
                percentile=percentile,
                deltaTheta7d=delta_theta_7d,
                riskLevel=risk_level,
                statusLabel=status_label,
                recommendedAction=recommended_action,
            )
        )

    return StudentAbilitySummaryResponse(
        studentId=str(current_user.id),
        asOf=latest_calibration,
        subjects=subject_summaries,
    )


@router.get("/abilities/me/trend", response_model=StudentThetaTrendResponse)
async def get_student_theta_trend(
    subject: str = Query(..., description="Subject name (e.g., 'math')"),
    days: int = Query(60, ge=7, le=365, description="Lookback window in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get theta trend over time for a single subject.

    Returns time series of (calibrated_at, theta, theta_se) for visualization.

    Args:
        subject: Subject name filter
        days: Lookback window (default: 60 days)

    Authorization:
        Requires student role (self-view only)
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    stmt = (
        select(IRTStudentAbility)
        .where(
            IRTStudentAbility.user_id == str(current_user.id),
            IRTStudentAbility.subject == subject,
            IRTStudentAbility.calibrated_at >= cutoff,
        )
        .order_by(IRTStudentAbility.calibrated_at)
    )
    result = await db.execute(stmt)
    abilities = result.scalars().all()

    if not abilities:
        raise HTTPException(
            status_code=404,
            detail=f"No ability data found for subject '{subject}' in last {days} days.",
        )

    points = [
        ThetaTrendPoint(
            calibratedAt=ability.calibrated_at,
            theta=ability.theta,
            thetaSe=ability.theta_se,
        )
        for ability in abilities
    ]

    return StudentThetaTrendResponse(
        studentId=str(current_user.id),
        subject=subject,
        points=points,
    )


# ============================================================================
# Tutor Priority List Endpoint
# ============================================================================


@router.get("/tutor/priorities", response_model=TutorPriorityListResponse)
async def get_tutor_priority_list(
    subject: str = Query(..., description="Subject filter (e.g., 'math')"),
    window_days: int = Query(14, ge=7, le=60, description="Analysis window in days"),
    limit: int = Query(30, ge=5, le=100, description="Max students to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get priority list of students needing intervention (tutor view).

    Returns students sorted by priority_score (desc), with:
        - Current ability and risk level
        - Recent activity and delta theta
        - Suggested focus areas and actions

    Args:
        subject: Subject to filter (e.g., 'math')
        window_days: Analysis window (default: 14 days)
        limit: Maximum students to return (default: 30)

    Authorization:
        Requires tutor or teacher role

    TODO: Add tutor_id → students relationship query when User model supports it
    """
    # TODO: Verify current_user is tutor/teacher
    # if current_user.role not in ["tutor", "teacher"]:
    #     raise HTTPException(status_code=403, detail="Requires tutor or teacher role")

    # Get all students' latest abilities in this subject
    # TODO: Filter by tutor's assigned students when relationship exists
    stmt = (
        select(IRTStudentAbility)
        .where(IRTStudentAbility.subject == subject)
        .order_by(IRTStudentAbility.user_id, IRTStudentAbility.calibrated_at.desc())
    )
    result = await db.execute(stmt)
    abilities = result.scalars().all()

    # Group by user_id, take most recent
    user_ability_map = {}
    for ability in abilities:
        if ability.user_id not in user_ability_map:
            user_ability_map[ability.user_id] = ability

    # Build priority list
    priority_students = []

    for user_id, ability in user_ability_map.items():
        # Compute metrics
        delta_theta_14d = await compute_delta_theta(
            db=db, user_id=user_id, subject=subject, days=window_days
        )
        sessions_last_7d = await count_recent_sessions(db=db, user_id=user_id, days=7)
        last_activity_at = await get_last_activity(db=db, user_id=user_id)

        # Classify
        theta_band = classify_theta_band(ability.theta)
        risk_level = assess_risk_level(ability.theta, ability.theta_se)

        # Priority score
        priority_score = compute_priority_score(
            theta=ability.theta,
            theta_se=ability.theta_se,
            delta_theta_14d=delta_theta_14d,
            sessions_last_7d=sessions_last_7d,
            last_activity_at=last_activity_at,
        )

        # Flags and recommendations
        flags = compute_student_flags(
            theta=ability.theta,
            theta_se=ability.theta_se,
            delta_theta_14d=delta_theta_14d,
            sessions_last_7d=sessions_last_7d,
        )
        recommended_focus = generate_tutor_recommended_focus(ability.theta, flags)

        # TODO: Fetch student metadata from User table
        # For now, use placeholder
        priority_students.append(
            TutorPriorityStudent(
                studentId=user_id,
                studentName=f"Student {user_id[:8]}",  # TODO: Load from User
                school=None,
                grade=None,
                theta=ability.theta,
                thetaSe=ability.theta_se,
                thetaBand=theta_band,
                deltaTheta14d=delta_theta_14d,
                lastActivityAt=last_activity_at,
                sessionsLast7d=sessions_last_7d,
                priorityScore=priority_score,
                riskLevel=risk_level,
                flags=flags,
                recommendedFocus=recommended_focus,
                nextSuggestedActions=[],  # TODO: Generate based on exam inventory
            )
        )

    # Sort by priority_score (desc) and limit
    priority_students.sort(key=lambda s: s.priorityScore, reverse=True)
    priority_students = priority_students[:limit]

    return TutorPriorityListResponse(
        tutorId=str(current_user.id),
        subject=subject,
        generatedAt=datetime.utcnow(),
        windowDays=window_days,
        students=priority_students,
    )


# ============================================================================
# Parent Report Endpoints
# ============================================================================


@router.get("/parent/reports/{student_id}", response_model=ParentReportData)
async def get_parent_report_data(
    student_id: str,
    period: str = Query("last4w", regex="^(last4w|last8w|last12w)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get report data for parent PDF generation (JSON response).

    Returns structured data combining IRT ability data + teacher/tutor comments.

    Args:
        student_id: Student UUID (must be current_user's child)
        period: Report period (last4w, last8w, last12w)

    Authorization:
        Requires parent role + ownership verification

    NEW (2025-11-25):
        - Uses parent_report_builder service to aggregate multi-source comments
        - Separates school teacher vs academy/tutor comments
        - Combines ability data with published report_comments

    TODO:
        - Verify parent-child relationship
        - Generate trend chart image (matplotlib → PNG)

    Note:
        This endpoint returns JSON data. Use
        GET /parent/reports/{student_id}/pdf for PDF download.
    """
    # TODO: Verify current_user is parent of student_id
    # if current_user.role != "parent":
    #     raise HTTPException(status_code=403, detail="Requires parent role")
    # if student_id not in current_user.children_ids:
    #     raise HTTPException(status_code=403, detail="Not your child")

    # Parse period
    period_map = {"last4w": 28, "last8w": 56, "last12w": 84}
    days = period_map[period]
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    # Use parent_report_builder to aggregate ability + comments
    from app.services.parent_report_builder import build_parent_report_data

    try:
        report_data = await build_parent_report_data(
            db=db,
            student_id=uuid.UUID(student_id),
            period_start=period_start,
            period_end=period_end,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid period: {str(e)}")

    if not report_data.subjects:
        raise HTTPException(
            status_code=404,
            detail=f"No ability data found for student in last {days} days.",
        )

    # TODO: Generate trend chart (matplotlib → save PNG → return URL)
    # Use model_copy to add trend chart URL
    report_data = report_data.model_copy(
        update={"trendChartUrl": "/static/reports/trend_placeholder.png"}
    )

    return report_data


@router.get("/parent/reports/{student_id}/pdf")
async def download_parent_report_pdf(
    student_id: str,
    period: str = Query("last4w", regex="^(last4w|last8w|last12w)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download parent report as PDF file.

    Generates complete PDF with trend charts and returns as
    application/pdf response.

    Args:
        student_id: Student UUID (must be current_user's child)
        period: Report period (last4w, last8w, last12w)

    Authorization:
        Requires parent role + ownership verification

    Returns:
        PDF file download (Content-Type: application/pdf)
    """
    from app.schemas.ability_schemas import ThetaTrendPoint
    from app.services.pdf_report_service import generate_parent_report_with_chart
    from fastapi.responses import Response

    # Get report data (reuse existing endpoint logic)
    report_data = await get_parent_report_data(
        student_id=student_id,
        period=period,
        current_user=current_user,
        db=db,
    )

    # Fetch trend points for chart generation
    period_map = {"last4w": 28, "last8w": 56, "last12w": 84}
    days = period_map[period]
    cutoff = datetime.utcnow() - timedelta(days=days)

    trend_points_by_subject = {}
    for subject_summary in report_data.subjects:
        subject = subject_summary.subject_label_en.lower()

        # Query trend points
        stmt = (
            select(IRTStudentAbility)
            .where(
                IRTStudentAbility.user_id == student_id,
                IRTStudentAbility.subject == subject,
                IRTStudentAbility.calibrated_at >= cutoff,
            )
            .order_by(IRTStudentAbility.calibrated_at)
        )
        result = await db.execute(stmt)
        abilities = result.scalars().all()

        if abilities:
            trend_points_by_subject[subject] = [
                ThetaTrendPoint(
                    calibratedAt=ability.calibrated_at,
                    theta=ability.theta,
                    thetaSe=ability.theta_se,
                )
                for ability in abilities
            ]

    # Generate PDF with charts
    pdf_bytes = await generate_parent_report_with_chart(
        report_data=report_data,
        trend_points_by_subject=trend_points_by_subject,
    )

    # Return as PDF download
    filename = f"DreamSeedAI_Report_{student_id[:8]}_{period}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
