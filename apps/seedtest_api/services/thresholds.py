"""Hierarchical threshold resolution service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.risk_threshold import RiskThreshold


@dataclass
class EffectiveThresholds:
    """Resolved threshold values after applying hierarchy.

    Hierarchy priority (most specific wins):
    1. Class-specific override
    2. Grade-specific override
    3. Tenant-wide default
    4. System default (hardcoded)
    """

    low_growth_delta: float = 0.05
    low_growth_nonpos_weeks: int = 3
    absent_rate_threshold: float = 0.10
    late_rate_threshold: float = 0.15
    response_anomaly_c_top_pct: float = 0.20
    no_response_rate_threshold: float = 0.08


# Priority order for threshold lookup
PRIORITY = [
    (
        "class",
        lambda t, class_id, grade: (RiskThreshold.class_id == class_id),
    ),
    (
        "grade",
        lambda t, class_id, grade: (
            (RiskThreshold.grade == grade) & (RiskThreshold.class_id == None)  # noqa: E711
        ),
    ),
    (
        "tenant",
        lambda t, class_id, grade: (
            (RiskThreshold.class_id == None) & (RiskThreshold.grade == None)  # noqa: E711
        ),
    ),
]


def resolve_thresholds(
    db: Session,
    tenant_id: str,
    type_: str,
    class_id: str | None = None,
    grade: str | None = None,
) -> EffectiveThresholds:
    """Resolve effective thresholds using hierarchical inheritance.

    Args:
        db: Database session
        tenant_id: Tenant identifier
        type_: Risk type (low_growth | irregular_att | response_anomaly)
        class_id: Optional class identifier for class-specific overrides
        grade: Optional grade level for grade-specific overrides

    Returns:
        EffectiveThresholds with resolved values

    Example:
        >>> thresholds = resolve_thresholds(db, tenant_id="t1", type_="low_growth", class_id="c1")
        >>> if student_delta < thresholds.low_growth_delta:
        ...     flag_risk(student)
    """
    eff = EffectiveThresholds()

    # Try each level in priority order (most specific first)
    for _, cond_fn in PRIORITY:
        stmt = (
            select(RiskThreshold)
            .where(RiskThreshold.tenant_id == tenant_id, RiskThreshold.type == type_)
            .where(cond_fn(RiskThreshold, class_id, grade))
            .order_by(RiskThreshold.updated_at.desc())
            .limit(1)
        )
        row = db.execute(stmt).scalars().first()

        if row:
            # Apply non-NULL values from this level
            if row.low_growth_delta is not None:
                eff.low_growth_delta = row.low_growth_delta
            if row.low_growth_nonpos_weeks is not None:
                eff.low_growth_nonpos_weeks = row.low_growth_nonpos_weeks
            if row.absent_rate_threshold is not None:
                eff.absent_rate_threshold = row.absent_rate_threshold
            if row.late_rate_threshold is not None:
                eff.late_rate_threshold = row.late_rate_threshold
            if row.response_anomaly_c_top_pct is not None:
                eff.response_anomaly_c_top_pct = row.response_anomaly_c_top_pct
            if row.no_response_rate_threshold is not None:
                eff.no_response_rate_threshold = row.no_response_rate_threshold

            # Most specific match found, stop searching
            break

    return eff
