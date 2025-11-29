"""
Analytics service for irt_student_abilities.

Provides computational logic for:
- Theta band classification
- Risk level assessment
- Priority scoring (tutor)
- Percentile calculation
- Delta theta computation
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam_models import IRTStudentAbility, ExamSession
from app.schemas.ability_schemas import RiskLevel, StudentFlag, ThetaBand


# ============================================================================
# Theta Band Classification
# ============================================================================


def classify_theta_band(theta: float) -> ThetaBand:
    """
    Classify theta into ability band.

    Bands:
        A:  θ ≥ 1.0 (top ~16%)
        B+: 0.3 ≤ θ < 1.0 (upper-mid)
        B:  -0.3 ≤ θ < 0.3 (average)
        C:  -1.0 ≤ θ < -0.3 (lower-mid)
        D:  θ < -1.0 (bottom ~16%)

    Args:
        theta: Ability estimate on logit scale

    Returns:
        ThetaBand enum value
    """
    if theta >= 1.0:
        return ThetaBand.A
    elif theta >= 0.3:
        return ThetaBand.B_PLUS
    elif theta >= -0.3:
        return ThetaBand.B
    elif theta >= -1.0:
        return ThetaBand.C
    else:
        return ThetaBand.D


# ============================================================================
# Risk Level Assessment
# ============================================================================


def assess_risk_level(theta: float, theta_se: float) -> RiskLevel:
    """
    Assess student risk level for intervention prioritization.

    Logic:
        - HIGH: θ < -0.3 OR θ_se > 0.6 (struggling or highly uncertain)
        - MEDIUM: -0.3 ≤ θ < 0.3 (average, monitor)
        - LOW: θ ≥ 0.3 AND θ_se ≤ 0.5 (stable and proficient)

    Args:
        theta: Current ability estimate
        theta_se: Standard error of theta

    Returns:
        RiskLevel enum value
    """
    if theta < -0.3 or theta_se > 0.6:
        return RiskLevel.HIGH
    elif theta < 0.3:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


# ============================================================================
# Percentile Calculation
# ============================================================================


def theta_to_percentile(theta: float) -> int:
    """
    Convert theta to percentile rank (0-100).

    Assumes θ ~ N(0, 1) for simplicity. In production, use empirical
    distribution from irt_student_abilities table.

    Args:
        theta: Ability estimate on logit scale

    Returns:
        Percentile rank (0-100)

    Examples:
        θ = -2.0 → ~2nd percentile
        θ = -1.0 → ~16th percentile
        θ =  0.0 → 50th percentile
        θ = +1.0 → ~84th percentile
        θ = +2.0 → ~98th percentile
    """
    from scipy.stats import norm

    # CDF of standard normal
    percentile = norm.cdf(theta) * 100
    # Convert to Python float to avoid numpy scalar issues
    percentile_float = float(percentile)
    return max(0, min(100, int(round(percentile_float))))


async def compute_empirical_percentile(
    db: AsyncSession,
    subject: str,
    theta: float,
) -> int:
    """
    Compute empirical percentile rank within subject cohort.

    This is more accurate than using theoretical N(0,1) distribution,
    especially after calibration drift.

    Args:
        db: Database session
        subject: Subject name (e.g., 'math')
        theta: Student's theta value

    Returns:
        Empirical percentile rank (0-100)
    """
    # Count students with lower theta in this subject
    stmt = (
        select(func.count())
        .select_from(IRTStudentAbility)
        .where(
            IRTStudentAbility.subject == subject,
            IRTStudentAbility.theta < theta,
        )
    )
    result = await db.execute(stmt)
    lower_count = result.scalar() or 0

    # Total students in this subject
    stmt_total = (
        select(func.count())
        .select_from(IRTStudentAbility)
        .where(IRTStudentAbility.subject == subject)
    )
    result_total = await db.execute(stmt_total)
    total_count = result_total.scalar() or 1  # Avoid division by zero

    percentile = (lower_count / total_count) * 100
    return max(0, min(100, int(round(percentile))))


# ============================================================================
# Delta Theta Computation
# ============================================================================


async def compute_delta_theta(
    db: AsyncSession,
    user_id: str,
    subject: str,
    days: int,
) -> Optional[float]:
    """
    Compute change in theta over specified time window.

    Logic:
        1. Find most recent calibration
        2. Find calibration from `days` ago (within ±2 days tolerance)
        3. Return theta_recent - theta_old

    Args:
        db: Database session
        user_id: Student UUID
        subject: Subject name
        days: Lookback window (e.g., 7, 14, 30)

    Returns:
        Delta theta, or None if insufficient history
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)

    # Most recent calibration
    stmt_recent = (
        select(IRTStudentAbility)
        .where(
            IRTStudentAbility.user_id == user_id,
            IRTStudentAbility.subject == subject,
        )
        .order_by(IRTStudentAbility.calibrated_at.desc())
        .limit(1)
    )
    result_recent = await db.execute(stmt_recent)
    recent = result_recent.scalar_one_or_none()

    if not recent:
        return None

    # Calibration near cutoff (±2 days tolerance)
    stmt_old = (
        select(IRTStudentAbility)
        .where(
            IRTStudentAbility.user_id == user_id,
            IRTStudentAbility.subject == subject,
            IRTStudentAbility.calibrated_at <= cutoff + timedelta(days=2),
            IRTStudentAbility.calibrated_at >= cutoff - timedelta(days=2),
        )
        .order_by(IRTStudentAbility.calibrated_at.desc())
        .limit(1)
    )
    result_old = await db.execute(stmt_old)
    old = result_old.scalar_one_or_none()

    if not old:
        return None

    return recent.theta - old.theta


# ============================================================================
# Priority Scoring (Tutor)
# ============================================================================


def compute_priority_score(
    theta: float,
    theta_se: float,
    delta_theta_14d: Optional[float],
    sessions_last_7d: int,
    last_activity_at: Optional[datetime],
) -> float:
    """
    Compute tutor priority score for student intervention.

    Formula:
        priority_score = w1 * risk_score
                       + w2 * decline_score
                       + w3 * inactivity_score

    Components:
        - risk_score: Based on theta level (low ability = higher score)
        - decline_score: Recent negative delta_theta (decline = higher score)
        - inactivity_score: Days since last activity (longer = higher score)

    Weights:
        w1 = 3.0 (risk)
        w2 = 2.0 (decline)
        w3 = 1.5 (inactivity)

    Args:
        theta: Current ability
        theta_se: Standard error
        delta_theta_14d: 14-day change in theta (None if unavailable)
        sessions_last_7d: Number of sessions in last 7 days
        last_activity_at: Timestamp of last session (None if never)

    Returns:
        Priority score (higher = more urgent)
    """
    # Risk score: 0-3 based on theta
    if theta < -1.0:
        risk_score = 3.0
    elif theta < -0.3:
        risk_score = 2.0
    elif theta < 0.3:
        risk_score = 1.0
    else:
        risk_score = 0.0

    # Add uncertainty penalty
    if theta_se > 0.6:
        risk_score += 1.0

    # Decline score: 0-3 based on delta_theta_14d
    if delta_theta_14d is not None and delta_theta_14d < -0.15:
        decline_score = 3.0  # Significant decline
    elif delta_theta_14d is not None and delta_theta_14d < 0.0:
        decline_score = 1.5  # Slight decline
    else:
        decline_score = 0.0

    # Inactivity score: 0-3 based on last_activity_at
    if last_activity_at is None:
        inactivity_score = 3.0  # Never active
    else:
        days_since = (datetime.utcnow() - last_activity_at).days
        if days_since >= 7:
            inactivity_score = 2.0
        elif days_since >= 3:
            inactivity_score = 1.0
        else:
            inactivity_score = 0.0

    # Weighted sum
    w1, w2, w3 = 3.0, 2.0, 1.5
    priority = w1 * risk_score + w2 * decline_score + w3 * inactivity_score

    return round(priority, 2)


# ============================================================================
# Student Flags
# ============================================================================


def compute_student_flags(
    theta: float,
    theta_se: float,
    delta_theta_14d: Optional[float],
    sessions_last_7d: int,
) -> List[StudentFlag]:
    """
    Generate status flags for student.

    Flags:
        - RECENT_DECLINE: Δθ < -0.15 over 14d
        - NO_ACTIVITY_7D: No sessions in last 7d
        - HIGH_UNCERTAINTY: θ_se > 0.6
        - STEADY_PROGRESS: Δθ > 0.10 over 14d
        - LOW_BASELINE: θ < -1.0

    Args:
        theta: Current ability
        theta_se: Standard error
        delta_theta_14d: 14-day change (None if unavailable)
        sessions_last_7d: Number of recent sessions

    Returns:
        List of applicable flags
    """
    flags = []

    if delta_theta_14d is not None and delta_theta_14d < -0.15:
        flags.append(StudentFlag.RECENT_DECLINE)

    if sessions_last_7d == 0:
        flags.append(StudentFlag.NO_ACTIVITY_7D)

    if theta_se > 0.6:
        flags.append(StudentFlag.HIGH_UNCERTAINTY)

    if delta_theta_14d is not None and delta_theta_14d > 0.10:
        flags.append(StudentFlag.STEADY_PROGRESS)

    if theta < -1.0:
        flags.append(StudentFlag.LOW_BASELINE)

    return flags


# ============================================================================
# Recommended Actions (Natural Language)
# ============================================================================


def generate_student_status_label(
    risk_level: RiskLevel,
    delta_theta_7d: Optional[float],
) -> str:
    """
    Generate human-readable status label for student dashboard.

    Args:
        risk_level: Assessed risk level
        delta_theta_7d: 7-day theta change (None if unavailable)

    Returns:
        Korean status label
    """
    if risk_level == RiskLevel.HIGH:
        if delta_theta_7d is not None and delta_theta_7d < -0.10:
            return "⚠️ 주의 필요 (최근 하락)"
        else:
            return "⚠️ 주의 필요"

    elif risk_level == RiskLevel.MEDIUM:
        if delta_theta_7d is not None and delta_theta_7d > 0.05:
            return "📈 개선 중"
        else:
            return "📊 보통 수준"

    else:  # LOW
        if delta_theta_7d is not None and delta_theta_7d > 0.10:
            return "🌟 안정적 성장 중"
        else:
            return "✅ 안정적"


def generate_recommended_action(
    theta: float,
    theta_band: ThetaBand,
    delta_theta_7d: Optional[float],
    risk_level: RiskLevel,
) -> str:
    """
    Generate recommended action for student.

    Args:
        theta: Current ability
        theta_band: Classified band
        delta_theta_7d: 7-day change
        risk_level: Risk level

    Returns:
        Korean recommendation text
    """
    if risk_level == RiskLevel.HIGH:
        return "기초 개념을 다시 확인하고, 쉬운 문제부터 차근차근 풀어보세요."

    elif risk_level == RiskLevel.MEDIUM:
        if delta_theta_7d is not None and delta_theta_7d > 0.05:
            return "현재 방향이 좋습니다. 꾸준히 학습을 이어가세요."
        else:
            return "약점 단원을 집중 보완하면 실력이 크게 향상될 것입니다."

    else:  # LOW
        if theta_band == ThetaBand.A:
            return "난이도 최상 문제에 도전하여 실력을 더욱 끌어올려 보세요."
        else:
            return f"다음 단계로 올라가기 위해 난이도 중상 문제(θ≈{theta+0.3:.1f}~{theta+0.7:.1f})를 중심으로 연습하세요."


def generate_tutor_recommended_focus(
    theta: float,
    flags: List[StudentFlag],
) -> List[str]:
    """
    Generate focus areas for tutor.

    Args:
        theta: Student ability
        flags: Status flags

    Returns:
        List of focus area strings (Korean)
    """
    focus_areas = []

    if StudentFlag.LOW_BASELINE in flags:
        focus_areas.append("기초 개념 재정리")

    if StudentFlag.RECENT_DECLINE in flags:
        focus_areas.append("최근 틀린 문제 유형 복습")
        focus_areas.append("단기 목표 점수 재설정")

    if StudentFlag.HIGH_UNCERTAINTY in flags:
        focus_areas.append("다양한 난이도 문제 풀이 (θ 안정화)")

    if StudentFlag.NO_ACTIVITY_7D in flags:
        focus_areas.append("학습 동기 부여 및 일정 재조정")

    if StudentFlag.STEADY_PROGRESS in flags:
        focus_areas.append("난이도 상 문제 도전")
        focus_areas.append("다음 모의고사 목표 점수 상향")

    if not focus_areas:
        focus_areas.append("현재 수준 유지 및 꾸준한 연습")

    return focus_areas


# ============================================================================
# Session Activity Queries
# ============================================================================


async def count_recent_sessions(
    db: AsyncSession,
    user_id: str,
    days: int,
) -> int:
    """
    Count exam sessions in last N days.

    Args:
        db: Database session
        user_id: Student UUID
        days: Lookback window

    Returns:
        Number of sessions
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    stmt = (
        select(func.count())
        .select_from(ExamSession)
        .where(
            ExamSession.user_id == user_id,
            ExamSession.created_at >= cutoff,
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def get_last_activity(
    db: AsyncSession,
    user_id: str,
) -> Optional[datetime]:
    """
    Get timestamp of most recent exam session.

    Args:
        db: Database session
        user_id: Student UUID

    Returns:
        Last activity timestamp, or None if never active
    """
    stmt = (
        select(ExamSession.created_at)
        .where(ExamSession.user_id == user_id)
        .order_by(ExamSession.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
