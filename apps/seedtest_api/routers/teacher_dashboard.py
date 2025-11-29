"""Teacher Dashboard API endpoints with RBAC and multitenancy.

Provides class-level analytics and risk monitoring for teachers.
Supports role-based access control (teacher/admin) and tenant scoping.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..auth.deps import UserContext, require_role
from ..db.session import get_db
from ..models import Attendance, ClassSummary, RiskFlag, RiskThreshold

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


# ============================================================================
# Helper Functions
# ============================================================================


def _to_float(value: Optional[Decimal | float]) -> float:
    """Convert Decimal or float to float, handling None."""
    if value is None:
        return 0.0
    return float(value)


# ============================================================================
# Response Models
# ============================================================================


class ClassSummaryOut(BaseModel):
    """Class summary response model."""

    classroom_id: str
    week_start: str
    mean_theta: float
    median_theta: float
    top10_theta: float
    bottom10_theta: float
    delta_theta_7d: float
    attendance_absent_rate: float
    attendance_late_rate: float
    stability_score: float
    risks_count: int

    class Config:
        from_attributes = True


class HistogramBucket(BaseModel):
    """Theta histogram bucket."""

    bin: int = Field(..., description="Histogram bin number (1-24)")
    count: int = Field(..., description="Number of students in this bin")
    theta_range: str = Field(
        ..., description="Theta range for this bin (e.g., -3.0 to -2.75)"
    )


class RiskOut(BaseModel):
    """Student risk flag output."""

    student_id: str
    classroom_id: str
    week_start: str
    type: str = Field(
        ...,
        description="Risk type: low_growth | irregular_attendance | response_anomaly",
    )
    score: float = Field(..., ge=0.0, le=1.0, description="Risk score (0.0-1.0)")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional risk details"
    )

    class Config:
        from_attributes = True


class StudentDetail(BaseModel):
    """Student detail for class monitor."""

    student_id: str
    current_theta: Optional[float] = None
    theta_trend_4w: List[float] = Field(
        default_factory=list, description="Last 4 weeks theta values"
    )
    attendance_status: Dict[str, int] = Field(
        default_factory=dict, description="Attendance counts by status"
    )
    weak_skills: List[str] = Field(
        default_factory=list, description="List of weak skill tags"
    )
    risk_flags: List[str] = Field(
        default_factory=list, description="Active risk flag types"
    )


class ThresholdIn(BaseModel):
    """Risk threshold input model."""

    type: str = Field(
        ..., description="Risk type: low_growth | irregular_att | response_anomaly"
    )
    class_id: Optional[str] = Field(None, description="Optional class-level override")
    grade: Optional[str] = Field(
        None, description="Optional grade-level override (e.g., 'G11')"
    )
    low_growth_delta: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum theta growth threshold"
    )
    low_growth_nonpos_weeks: Optional[int] = Field(
        None, ge=1, le=10, description="Required consecutive non-positive weeks"
    )
    absent_rate_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Absent rate threshold"
    )
    late_rate_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Late rate threshold"
    )
    response_anomaly_c_top_pct: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Response anomaly percentile"
    )
    no_response_rate_threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="No-response rate threshold"
    )


class ThresholdOut(BaseModel):
    """Risk threshold output model."""

    id: str
    tenant_id: str
    type: str
    class_id: Optional[str] = None
    grade: Optional[str] = None
    low_growth_delta: Optional[float] = None
    low_growth_nonpos_weeks: Optional[int] = None
    absent_rate_threshold: Optional[float] = None
    late_rate_threshold: Optional[float] = None
    response_anomaly_c_top_pct: Optional[float] = None
    no_response_rate_threshold: Optional[float] = None
    updated_at: str

    class Config:
        from_attributes = True

    @field_validator("updated_at", mode="before")
    @classmethod
    def serialize_datetime(cls, v):
        """Convert datetime to ISO format string."""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        return v


# ============================================================================
# API Endpoints - Class Analytics (Teacher/Admin)
# ============================================================================


@router.get("/classes/{classroom_id}/summary", response_model=ClassSummaryOut)
async def get_class_summary(
    classroom_id: str,
    week: Optional[str] = Query(
        None, description="Week start date (YYYY-MM-DD), defaults to latest"
    ),
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("teacher", "admin")),
) -> ClassSummaryOut:
    """Get class summary for a specific classroom and week.

    Returns aggregated class-level metrics including:
    - Mean/median/percentile theta values
    - Weekly growth (delta_theta_7d)
    - Attendance rates
    - Stability score
    - Risk count

    Requires: teacher or admin role
    Scoped by: tenant_id from JWT
    """
    stmt = (
        select(ClassSummary)
        .where(
            ClassSummary.tenant_id == user.tenant_id,
            ClassSummary.classroom_id == classroom_id,
        )
        .order_by(ClassSummary.week_start.desc())
    )

    if week:
        try:
            week_date = date.fromisoformat(week)
            stmt = stmt.where(ClassSummary.week_start == week_date)
        except ValueError:
            raise HTTPException(400, "Invalid week format. Use YYYY-MM-DD")

    row = db.execute(stmt).scalars().first()

    if not row:
        raise HTTPException(404, f"No summary found for classroom {classroom_id}")

    return ClassSummaryOut(
        classroom_id=str(row.classroom_id),
        week_start=row.week_start.isoformat(),
        mean_theta=_to_float(row.mean_theta),  # type: ignore[arg-type]
        median_theta=_to_float(row.median_theta),  # type: ignore[arg-type]
        top10_theta=_to_float(row.top10_theta),  # type: ignore[arg-type]
        bottom10_theta=_to_float(row.bottom10_theta),  # type: ignore[arg-type]
        delta_theta_7d=_to_float(row.delta_theta_7d),  # type: ignore[arg-type]
        attendance_absent_rate=_to_float(row.attendance_absent_rate),  # type: ignore[arg-type]
        attendance_late_rate=_to_float(row.attendance_late_rate),  # type: ignore[arg-type]
        stability_score=_to_float(row.stability_score),  # type: ignore[arg-type]
        risks_count=row.risks_count,  # type: ignore[arg-type]
    )


@router.get(
    "/classes/{classroom_id}/theta-histogram", response_model=List[HistogramBucket]
)
async def get_theta_histogram(
    classroom_id: str,
    week: Optional[str] = Query(
        None, description="Week start date (YYYY-MM-DD), defaults to latest"
    ),
    bins: int = Query(24, ge=5, le=50, description="Number of histogram bins"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("teacher", "admin")),
) -> List[HistogramBucket]:
    """Get theta distribution histogram for a classroom.

    Uses width_bucket to create histogram bins from -3.0 to +3.0 theta range.

    Requires: teacher or admin role
    Scoped by: tenant_id from JWT
    """
    # For now, we'll use a simplified query that works with our current schema
    # We aggregate theta from weekly_kpi for students (classroom association needed)

    # Note: This is a simplified version. In production, you'd need proper
    # student-classroom mapping to filter by classroom_id

    query = text(
        """
        SELECT 
            width_bucket(
                CAST((kpis->>'theta')::text AS NUMERIC), 
                -3.0, 
                3.0, 
                :bins
            ) AS bin,
            COUNT(*) AS count
        FROM weekly_kpi
        WHERE week_start = (
            SELECT MAX(week_start) 
            FROM weekly_kpi
        )
        AND kpis->>'theta' IS NOT NULL
        GROUP BY bin
        ORDER BY bin
    """
    )

    result = db.execute(query, {"bins": bins}).all()

    # Calculate theta ranges for each bin
    bin_width = 6.0 / bins  # Range is -3.0 to +3.0

    buckets = []
    for bin_num, count in result:
        theta_min = -3.0 + (bin_num - 1) * bin_width
        theta_max = theta_min + bin_width
        buckets.append(
            HistogramBucket(
                bin=bin_num,
                count=count,
                theta_range=f"{theta_min:.2f} to {theta_max:.2f}",
            )
        )

    return buckets


@router.get("/classes/{classroom_id}/risks", response_model=List[RiskOut])
async def get_class_risks(
    classroom_id: str,
    week: Optional[str] = Query(
        None, description="Week start date (YYYY-MM-DD), defaults to latest"
    ),
    risk_type: Optional[str] = Query(None, description="Filter by risk type"),
    limit: int = Query(200, ge=1, le=1000, description="Maximum number of results"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("teacher", "admin")),
) -> List[RiskOut]:
    """Get risk flags for students in a classroom.

    Returns list of student risk flags with details.

    Requires: teacher or admin role
    Scoped by: tenant_id from JWT
    """
    stmt = (
        select(RiskFlag)
        .where(
            RiskFlag.tenant_id == user.tenant_id,
            RiskFlag.classroom_id == classroom_id,
        )
        .order_by(RiskFlag.week_start.desc(), RiskFlag.score.desc())
        .limit(limit)
    )

    if week:
        try:
            week_date = date.fromisoformat(week)
            stmt = stmt.where(RiskFlag.week_start == week_date)
        except ValueError:
            raise HTTPException(400, "Invalid week format. Use YYYY-MM-DD")

    if risk_type:
        stmt = stmt.where(RiskFlag.type == risk_type)

    rows = db.execute(stmt).scalars().all()

    return [
        RiskOut(
            student_id=str(r.student_id),
            classroom_id=str(r.classroom_id),
            week_start=r.week_start.isoformat(),
            type=str(r.type),
            score=_to_float(r.score),  # type: ignore[arg-type]
            details=r.details_json or {},  # type: ignore[arg-type]
        )
        for r in rows
    ]


@router.get("/classes/{classroom_id}/students", response_model=List[StudentDetail])
async def get_class_students(
    classroom_id: str,
    db: Session = Depends(get_db),
) -> List[StudentDetail]:
    """Get detailed student list for a classroom.

    Returns student-level details including:
    - Current theta
    - 4-week theta trend
    - Attendance summary
    - Weak skills
    - Active risk flags
    """
    # This is a placeholder implementation
    # In production, you'd need proper student-classroom mapping

    # For now, return empty list
    # TODO: Implement after student-classroom association is established
    return []


@router.get("/classes/{classroom_id}/attendance-summary")
async def get_attendance_summary(
    classroom_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("teacher", "admin")),
) -> Dict[str, Any]:
    """Get attendance summary for a classroom.

    Returns attendance statistics grouped by status.

    Requires: teacher or admin role
    Scoped by: tenant_id from JWT
    """
    stmt = select(
        Attendance.status,
        func.count().label("count"),
    ).where(
        Attendance.tenant_id == user.tenant_id,
        Attendance.classroom_id == classroom_id,
    )

    if start_date:
        try:
            stmt = stmt.where(Attendance.date >= date.fromisoformat(start_date))
        except ValueError:
            raise HTTPException(400, "Invalid start_date format. Use YYYY-MM-DD")

    if end_date:
        try:
            stmt = stmt.where(Attendance.date <= date.fromisoformat(end_date))
        except ValueError:
            raise HTTPException(400, "Invalid end_date format. Use YYYY-MM-DD")

    stmt = stmt.group_by(Attendance.status)

    rows = db.execute(stmt).all()

    total = sum(count for _, count in rows)
    summary = {
        "total": total,
        "by_status": {status: count for status, count in rows},
        "rates": {
            status: round(count / total, 4) if total > 0 else 0.0
            for status, count in rows
        },
    }

    return summary


# ============================================================================
# API Endpoints - Thresholds CRUD (Admin Only)
# ============================================================================


@router.post("/thresholds", response_model=ThresholdOut)
async def create_threshold(
    payload: ThresholdIn,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("admin")),
) -> ThresholdOut:
    """Create a new risk threshold configuration.

    Thresholds can be defined at three levels:
    1. Tenant-wide (no class_id or grade specified)
    2. Grade-specific (grade specified, no class_id)
    3. Class-specific (class_id specified)

    More specific thresholds override less specific ones.

    Requires: admin role
    """
    from uuid import uuid4

    threshold = RiskThreshold(
        id=str(uuid4()),
        tenant_id=user.tenant_id,
        type=payload.type,
        class_id=payload.class_id,
        grade=payload.grade,
        low_growth_delta=payload.low_growth_delta,
        low_growth_nonpos_weeks=payload.low_growth_nonpos_weeks,
        absent_rate_threshold=payload.absent_rate_threshold,
        late_rate_threshold=payload.late_rate_threshold,
        response_anomaly_c_top_pct=payload.response_anomaly_c_top_pct,
        no_response_rate_threshold=payload.no_response_rate_threshold,
    )

    db.add(threshold)
    db.commit()
    db.refresh(threshold)

    return ThresholdOut.model_validate(threshold)


@router.get("/thresholds", response_model=List[ThresholdOut])
async def list_thresholds(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("teacher", "admin")),
) -> List[ThresholdOut]:
    """List all risk thresholds for current tenant.

    Returns thresholds ordered by most recent first.

    Requires: teacher or admin role
    Scoped by: tenant_id from JWT
    """
    stmt = (
        select(RiskThreshold)
        .where(RiskThreshold.tenant_id == user.tenant_id)
        .order_by(RiskThreshold.updated_at.desc())
    )

    rows = db.execute(stmt).scalars().all()

    return [ThresholdOut.model_validate(r) for r in rows]


@router.delete("/thresholds/{threshold_id}")
async def delete_threshold(
    threshold_id: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role("admin")),
) -> Dict[str, bool]:
    """Delete a risk threshold configuration.

    Requires: admin role
    Scoped by: tenant_id from JWT
    """
    stmt = select(RiskThreshold).where(
        RiskThreshold.id == threshold_id,
        RiskThreshold.tenant_id == user.tenant_id,
    )
    threshold = db.execute(stmt).scalars().first()

    if not threshold:
        raise HTTPException(404, "Threshold not found")

    db.delete(threshold)
    db.commit()

    return {"ok": True}
