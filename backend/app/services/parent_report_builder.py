"""
Parent report builder service - Combines ability data + teacher/tutor comments.

This module integrates:
1. IRT ability data (irt_student_abilities table)
2. Teacher/tutor comments (report_comments table)
3. Multi-source comment aggregation (school > academy > tutor priority)

Usage:
    report_data = await build_parent_report_data(
        db=db,
        student_id=uuid.UUID("..."),
        period_start=datetime(2025, 11, 1),
        period_end=datetime(2025, 11, 30),
    )
    
    # Generate PDF
    pdf_bytes = generate_parent_report_pdf(report_data, ...)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam_models import IRTStudentAbility
from app.models.report_models import ReportComment, ReportSection, ReportSourceType
from app.schemas.ability_schemas import ParentReportData, ParentReportSubject
from app.services.ability_analytics import (
    classify_theta_band,
    assess_risk_level,
    compute_delta_theta,
    theta_to_percentile,
)


# ============================================================================
# Comment Aggregation Helpers
# ============================================================================

def pick_comment(
    comments: list[ReportComment],
    source_type: ReportSourceType,
    section: ReportSection,
    language: str,
) -> Optional[str]:
    """
    Select most recent comment matching criteria.
    
    Args:
        comments: All published comments for student+period
        source_type: Filter by source (SCHOOL_TEACHER, ACADEMY_TEACHER, TUTOR)
        section: Filter by section (SUMMARY, NEXT_4W_PLAN, PARENT_GUIDANCE)
        language: Filter by language (ko, en)
    
    Returns:
        Comment content or None if no match
        
    Selection logic:
    - Filter by source_type, section, language
    - Sort by updated_at DESC
    - Return first (most recent)
    """
    candidates = [
        c for c in comments
        if c.source_type == source_type
        and c.section == section
        and c.language == language
    ]
    
    if not candidates:
        return None
    
    # Most recent update wins
    candidates.sort(key=lambda c: c.updated_at, reverse=True)
    return candidates[0].content


def pick_comment_any_tutor(
    comments: list[ReportComment],
    section: ReportSection,
    language: str,
) -> Optional[str]:
    """
    Select most recent comment from any tutoring source (academy or private tutor).
    
    Priority: ACADEMY_TEACHER > TUTOR (if both exist, academy wins).
    """
    # Try academy first
    academy_comment = pick_comment(
        comments, ReportSourceType.ACADEMY_TEACHER, section, language
    )
    if academy_comment:
        return academy_comment
    
    # Fallback to private tutor
    return pick_comment(
        comments, ReportSourceType.TUTOR, section, language
    )


def collect_all_plans(
    comments: list[ReportComment],
    language: str,
) -> list[str]:
    """
    Collect all NEXT_4W_PLAN comments from all sources.
    
    Returns:
    - List of plan items (strings)
    - Ordered by: school first, then tutoring sources, then by updated_at DESC
    """
    school_plans = [
        c.content for c in comments
        if c.source_type == ReportSourceType.SCHOOL_TEACHER
        and c.section == ReportSection.NEXT_4W_PLAN
        and c.language == language
    ]
    
    tutor_plans = [
        c.content for c in comments
        if c.source_type in (ReportSourceType.ACADEMY_TEACHER, ReportSourceType.TUTOR)
        and c.section == ReportSection.NEXT_4W_PLAN
        and c.language == language
    ]
    
    # Sort each group by updated_at DESC
    school_plans.sort(key=lambda c: c, reverse=True)  # Already strings, use as-is
    tutor_plans.sort(key=lambda c: c, reverse=True)
    
    return school_plans + tutor_plans


# ============================================================================
# Ability Data Aggregation
# ============================================================================

async def compute_parent_subject_summaries(
    db: AsyncSession,
    student_id: uuid.UUID,
    period_start: datetime,
    period_end: datetime,
) -> list[ParentReportSubject]:
    """
    Compute per-subject summaries for parent report.
    
    For each subject:
    1. Get latest ability in period
    2. Compute 4-week delta
    3. Classify band, compute percentile, assess risk
    
    Returns:
        List of ParentReportSubject schemas
    """
    # Query all abilities in period
    result = await db.execute(
        select(IRTStudentAbility)
        .where(
            and_(
                IRTStudentAbility.user_id == student_id,
                IRTStudentAbility.calibrated_at >= period_start,
                IRTStudentAbility.calibrated_at <= period_end,
            )
        )
        .order_by(IRTStudentAbility.calibrated_at.desc())
    )
    abilities = result.scalars().all()
    
    if not abilities:
        return []
    
    # Group by subject, take most recent
    subject_map: dict[str, IRTStudentAbility] = {}
    for ability in abilities:
        subject = ability.subject or "unknown"
        if subject not in subject_map:
            subject_map[subject] = ability
    
    # Build summaries
    summaries = []
    for subject, ability in subject_map.items():
        # Compute 4-week delta
        delta_4w = await compute_delta_theta(
            db, str(student_id), subject, days=28  # ~4 weeks
        )
        
        # Classify
        band = classify_theta_band(ability.theta)
        percentile = theta_to_percentile(ability.theta)
        risk_level = assess_risk_level(ability.theta, ability.theta_se)
        
        # Map risk level to string labels
        risk_label_ko = {
            "low": "안정",
            "medium": "주의",
            "high": "위험",
        }.get(risk_level.value, "알 수 없음")
        
        risk_label_en = {
            "low": "Stable",
            "medium": "Caution",
            "high": "At Risk",
        }.get(risk_level.value, "Unknown")
        
        summaries.append(
            ParentReportSubject(
                subjectLabelKo=subject,
                subjectLabelEn=subject,  # TODO: Add translation map
                theta=ability.theta,
                thetaBand=band,
                percentile=percentile,
                deltaTheta4w=delta_4w or 0.0,
                riskLabelKo=risk_label_ko,
                riskLabelEn=risk_label_en,
            )
        )
    
    return summaries


# ============================================================================
# Main Report Builder
# ============================================================================

async def build_parent_report_data(
    db: AsyncSession,
    student_id: uuid.UUID,
    period_start: datetime,
    period_end: datetime,
) -> ParentReportData:
    """
    Build complete parent report data structure.
    
    Combines:
    1. Ability summaries (per subject)
    2. Published comments from school teachers
    3. Published comments from academy teachers/tutors
    4. Next 4-week plans from all sources
    5. Parent guidance (school priority, tutor fallback)
    
    Args:
        db: Async database session
        student_id: Target student UUID
        period_start: Report period start (inclusive)
        period_end: Report period end (inclusive)
    
    Returns:
        ParentReportData schema ready for PDF generation
        
    Comment selection logic:
    - School teacher comments take priority over tutors
    - SUMMARY section: Separate school vs tutor comments
    - NEXT_4W_PLAN section: Collect all plans from all sources
    - PARENT_GUIDANCE section: School first, tutor fallback
    - Always use most recent (updated_at DESC) within each category
    """
    # 1. Load ability summaries
    subjects = await compute_parent_subject_summaries(
        db, student_id, period_start, period_end
    )
    
    # 2. Load published comments
    comments_result = await db.execute(
        select(ReportComment)
        .where(
            and_(
                ReportComment.student_id == student_id,
                ReportComment.period_start == period_start,
                ReportComment.period_end == period_end,
                ReportComment.is_published == True,
            )
        )
    )
    comments = list(comments_result.scalars().all())
    
    # 3. Extract school teacher comments (SUMMARY section)
    school_comment_ko = pick_comment(
        comments, ReportSourceType.SCHOOL_TEACHER, ReportSection.SUMMARY, "ko"
    )
    school_comment_en = pick_comment(
        comments, ReportSourceType.SCHOOL_TEACHER, ReportSection.SUMMARY, "en"
    )
    
    # 4. Extract tutor comments (SUMMARY section)
    tutor_comment_ko = pick_comment_any_tutor(
        comments, ReportSection.SUMMARY, "ko"
    )
    tutor_comment_en = pick_comment_any_tutor(
        comments, ReportSection.SUMMARY, "en"
    )
    
    # 5. Collect all NEXT_4W_PLAN items
    next_plans_ko = collect_all_plans(comments, "ko")
    next_plans_en = collect_all_plans(comments, "en")
    
    # 6. Parent guidance (school priority, tutor fallback)
    parent_guidance_ko = (
        pick_comment(comments, ReportSourceType.SCHOOL_TEACHER, ReportSection.PARENT_GUIDANCE, "ko")
        or pick_comment_any_tutor(comments, ReportSection.PARENT_GUIDANCE, "ko")
    )
    parent_guidance_en = (
        pick_comment(comments, ReportSourceType.SCHOOL_TEACHER, ReportSection.PARENT_GUIDANCE, "en")
        or pick_comment_any_tutor(comments, ReportSection.PARENT_GUIDANCE, "en")
    )
    
    # 7. Generate parent-friendly summary (auto-generated from ability data)
    summary_ko = generate_parent_summary_ko(subjects, period_start, period_end)
    summary_en = generate_parent_summary_en(subjects, period_start, period_end)
    
    # 8. Build final data structure
    return ParentReportData(
        studentName="학생",  # TODO: Fetch from user table
        school=None,  # TODO: Fetch from user profile
        grade=None,  # TODO: Fetch from user profile
        periodStart=period_start.strftime("%Y-%m-%d"),
        periodEnd=period_end.strftime("%Y-%m-%d"),
        generatedAt=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        parentFriendlySummaryKo=summary_ko,
        parentFriendlySummaryEn=summary_en,
        subjects=subjects,
        trendChartUrl="",  # Set by PDF generation service
        schoolTeacherCommentKo=school_comment_ko,
        schoolTeacherCommentEn=school_comment_en,
        tutorCommentKo=tutor_comment_ko,
        tutorCommentEn=tutor_comment_en,
        nextPlansKo=next_plans_ko,
        nextPlansEn=next_plans_en,
        parentGuidanceKo=parent_guidance_ko,
        parentGuidanceEn=parent_guidance_en,
    )


# ============================================================================
# Auto-Generated Summaries
# ============================================================================

def generate_parent_summary_ko(
    subjects: list[ParentReportSubject],
    period_start: datetime,
    period_end: datetime,
) -> str:
    """
    Generate Korean parent summary from ability data.
    
    Format:
    - Overall performance across subjects
    - Highlight strengths and concerns
    - 2-3 sentences
    """
    if not subjects:
        return "이번 기간 동안 측정된 능력 데이터가 없습니다."
    
    # Count subjects by risk level
    at_risk = sum(1 for s in subjects if "위험" in s.risk_label_ko)
    stable = sum(1 for s in subjects if "안정" in s.risk_label_ko)
    
    # Average delta
    avg_delta = sum(s.delta_theta_4w or 0.0 for s in subjects) / len(subjects)
    
    if at_risk > 0:
        return (
            f"이번 기간 동안 {len(subjects)}개 과목에서 능력이 측정되었습니다. "
            f"{at_risk}개 과목에서 주의가 필요하며, 특히 {subjects[0].subject_label_ko} 과목의 집중 관리가 권장됩니다. "
            f"평균 능력 변화는 {avg_delta:+.2f}입니다."
        )
    elif avg_delta > 0.1:
        return (
            f"이번 기간 동안 {len(subjects)}개 과목에서 능력이 측정되었습니다. "
            f"전반적으로 안정적인 성장세를 보이고 있으며, 평균 능력 변화는 {avg_delta:+.2f}입니다. "
            f"현재 학습 방향을 유지하는 것이 좋습니다."
        )
    else:
        return (
            f"이번 기간 동안 {len(subjects)}개 과목에서 능력이 측정되었습니다. "
            f"{stable}개 과목에서 안정적인 상태를 유지하고 있습니다. "
            f"추가적인 학습 자극을 통해 성장 기회를 모색하는 것이 좋습니다."
        )


def generate_parent_summary_en(
    subjects: list[ParentReportSubject],
    period_start: datetime,
    period_end: datetime,
) -> str:
    """Generate English parent summary from ability data."""
    if not subjects:
        return "No ability data available for this period."
    
    at_risk = sum(1 for s in subjects if "Risk" in s.risk_label_en)
    stable = sum(1 for s in subjects if "Stable" in s.risk_label_en)
    avg_delta = sum(s.delta_theta_4w or 0.0 for s in subjects) / len(subjects)
    
    if at_risk > 0:
        return (
            f"During this period, abilities were measured across {len(subjects)} subjects. "
            f"{at_risk} subject(s) require attention, particularly {subjects[0].subject_label_en}. "
            f"Average ability change: {avg_delta:+.2f}."
        )
    elif avg_delta > 0.1:
        return (
            f"During this period, abilities were measured across {len(subjects)} subjects. "
            f"Overall, the student shows steady growth with average ability change of {avg_delta:+.2f}. "
            f"Continue with current learning approach."
        )
    else:
        return (
            f"During this period, abilities were measured across {len(subjects)} subjects. "
            f"{stable} subject(s) remain stable. "
            f"Consider additional learning activities to create growth opportunities."
        )
