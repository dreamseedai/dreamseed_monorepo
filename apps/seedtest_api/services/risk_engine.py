"""Risk engine for detecting student learning/behavioral risks with multitenancy support."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from statistics import mean, median
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Attendance, ClassSummary, RiskFlag
from ..models.metrics import WeeklyKPI
from .thresholds import resolve_thresholds


def compute_week_start(d: date) -> date:
    """Compute Monday of the week containing date d."""
    return d - timedelta(days=d.weekday())


def build_class_summary(
    db: Session, tenant_id: str, classroom_id: str, week: date
) -> None:
    """Build class summary for a given classroom and week.
    
    Aggregates:
    - Mean/median/top10/bottom10 theta
    - 7-day theta growth (delta_theta_7d)
    - Attendance rates (absent/late)
    - Stability score (1/IQR of theta distribution)
    - Risk count
    
    Args:
        db: Database session
        tenant_id: Tenant identifier for multitenancy
        classroom_id: Classroom identifier
        week: Week start date (Monday)
    """
    # Fetch all student theta values for this class and week
    # Using weekly_kpi which contains aggregated theta estimates per user
    kpi_stmt = select(WeeklyKPI).where(WeeklyKPI.week_start == week)
    kpi_rows = db.execute(kpi_stmt).scalars().all()
    
    theta_values = []
    for kpi in kpi_rows:
        if isinstance(kpi.kpis, dict) and "theta" in kpi.kpis:
            theta_values.append(float(kpi.kpis["theta"]))
    
    if not theta_values:
        # No data for this week, skip
        return

    mean_theta = float(mean(theta_values))
    median_theta = float(median(theta_values))
    
    sorted_thetas = sorted(theta_values)
    n = len(sorted_thetas)
    top10_idx = max(int(n * 0.9) - 1, 0)
    bottom10_idx = max(int(n * 0.1) - 1, 0)
    top10_theta = float(sorted_thetas[top10_idx]) if top10_idx < n else mean_theta
    bottom10_theta = float(sorted_thetas[bottom10_idx]) if bottom10_idx < n else mean_theta

    # 7-day growth: average delta_theta from current week
    delta_values = [
        float(kpi.kpis.get("delta_theta", 0))
        for kpi in kpi_rows
        if isinstance(kpi.kpis, dict) and "delta_theta" in kpi.kpis
    ]
    delta_theta_7d = float(mean(delta_values)) if delta_values else 0.0

    # Attendance rates for the week
    week_end = week + timedelta(days=7)
    att_stmt = (
        select(Attendance.status, func.count())
        .where(
            Attendance.tenant_id == tenant_id,
            Attendance.classroom_id == classroom_id,
            Attendance.date >= week,
            Attendance.date < week_end,
        )
        .group_by(Attendance.status)
    )
    att_rows = db.execute(att_stmt).all()
    
    total_att = sum(count for _, count in att_rows) or 1
    late_count = next((count for status, count in att_rows if status == "late"), 0)
    absent_count = next((count for status, count in att_rows if status == "absent"), 0)
    
    late_rate = float(late_count) / total_att
    absent_rate = float(absent_count) / total_att

    # Stability score: inverse of IQR (interquartile range)
    q1_idx = max(int(n * 0.25) - 1, 0)
    q3_idx = max(int(n * 0.75) - 1, 0)
    q1 = sorted_thetas[q1_idx] if q1_idx < n else mean_theta
    q3 = sorted_thetas[q3_idx] if q3_idx < n else mean_theta
    iqr = max(q3 - q1, 1e-6)
    stability_score = float(1.0 / iqr)

    # Risk count
    risk_count_stmt = select(func.count()).where(
        RiskFlag.tenant_id == tenant_id,
        RiskFlag.classroom_id == classroom_id,
        RiskFlag.week_start == week,
    )
    risks_count = db.execute(risk_count_stmt).scalar() or 0

    # Upsert class_summary
    # Check if exists
    existing = db.execute(
        select(ClassSummary).where(
            ClassSummary.tenant_id == tenant_id,
            ClassSummary.classroom_id == classroom_id,
            ClassSummary.week_start == week,
        )
    ).scalar_one_or_none()

    if existing:
        existing.mean_theta = Decimal(str(mean_theta))
        existing.median_theta = Decimal(str(median_theta))
        existing.top10_theta = Decimal(str(top10_theta))
        existing.bottom10_theta = Decimal(str(bottom10_theta))
        existing.delta_theta_7d = Decimal(str(delta_theta_7d))
        existing.attendance_absent_rate = Decimal(str(absent_rate))
        existing.attendance_late_rate = Decimal(str(late_rate))
        existing.stability_score = Decimal(str(stability_score))
        existing.risks_count = int(risks_count)
    else:
        from uuid import uuid4

        summary = ClassSummary(
            id=str(uuid4()),
            tenant_id=tenant_id,
            classroom_id=classroom_id,
            week_start=week,
            mean_theta=Decimal(str(mean_theta)),
            median_theta=Decimal(str(median_theta)),
            top10_theta=Decimal(str(top10_theta)),
            bottom10_theta=Decimal(str(bottom10_theta)),
            delta_theta_7d=Decimal(str(delta_theta_7d)),
            attendance_absent_rate=Decimal(str(absent_rate)),
            attendance_late_rate=Decimal(str(late_rate)),
            stability_score=Decimal(str(stability_score)),
            risks_count=int(risks_count),
        )
        db.add(summary)


def run_risk_rules(
    db: Session, tenant_id: str, classroom_id: str, week: date, grade: str | None = None
) -> None:
    """Run risk detection rules for a classroom and week using dynamic thresholds.
    
    Rules:
    1. Low growth: Δθ_7d < threshold AND last N weeks all Δθ ≤ 0 (N from threshold)
    2. Irregular attendance: absent_rate ≥ threshold OR late_rate ≥ threshold
    3. Response anomaly: (future) guessing probability c_hat or omit_rate
    
    Args:
        db: Database session
        tenant_id: Tenant identifier for multitenancy
        classroom_id: Classroom identifier
        week: Week start date (Monday)
        grade: Optional grade level for grade-specific thresholds
    """
    from uuid import uuid4

    # Resolve dynamic thresholds (class > grade > tenant > default)
    thr_growth = resolve_thresholds(
        db, tenant_id, "low_growth", class_id=classroom_id, grade=grade
    )
    thr_att = resolve_thresholds(
        db, tenant_id, "irregular_att", class_id=classroom_id, grade=grade
    )

    # Rule 1: Low growth
    # Get last 4 weeks of data per student
    weeks = [week - timedelta(days=7 * i) for i in range(0, 4)]
    kpi_stmt = select(WeeklyKPI).where(WeeklyKPI.week_start.in_(weeks))
    kpi_rows = db.execute(kpi_stmt).scalars().all()

    by_student: Dict[str, List[tuple[date, float]]] = {}
    for kpi in kpi_rows:
        if isinstance(kpi.kpis, dict) and "delta_theta" in kpi.kpis:
            delta = float(kpi.kpis["delta_theta"])
            by_student.setdefault(kpi.user_id, []).append((kpi.week_start, delta))

    for student_id, deltas in by_student.items():
        deltas.sort(key=lambda x: x[0])
        
        if len(deltas) >= 3:
            last_delta = deltas[-1][1]
            required_weeks = thr_growth.low_growth_nonpos_weeks
            last_n_deltas = [d for _, d in deltas[-required_weeks:]]
            
            # Check if low growth
            if (
                last_delta < thr_growth.low_growth_delta
                and all(d <= 0 for d in last_n_deltas)
            ):
                # Create risk flag
                risk = RiskFlag(
                    id=str(uuid4()),
                    tenant_id=tenant_id,
                    student_id=student_id,
                    classroom_id=classroom_id,
                    week_start=week,
                    type="low_growth",
                    score=Decimal("1.0"),
                    details_json={
                        "last_n_deltas": last_n_deltas,
                        "threshold": thr_growth.low_growth_delta,
                        "required_weeks": required_weeks,
                    },
                )
                db.add(risk)

    # Rule 2: Irregular attendance
    # Get attendance for last 4 weeks per student
    week_start_4w = week - timedelta(days=28)
    att_stmt = (
        select(Attendance.student_id, Attendance.status, func.count())
        .where(
            Attendance.tenant_id == tenant_id,
            Attendance.classroom_id == classroom_id,
            Attendance.date >= week_start_4w,
            Attendance.date < week + timedelta(days=7),
        )
        .group_by(Attendance.student_id, Attendance.status)
    )
    att_rows = db.execute(att_stmt).all()

    by_student_att: Dict[str, Dict[str, int]] = {}
    for student_id, status, count in att_rows:
        by_student_att.setdefault(student_id, {})[status] = int(count)

    for student_id, status_counts in by_student_att.items():
        total = sum(status_counts.values()) or 1
        absent_rate = status_counts.get("absent", 0) / total
        late_rate = status_counts.get("late", 0) / total

        if (
            absent_rate >= thr_att.absent_rate_threshold
            or late_rate >= thr_att.late_rate_threshold
        ):
            risk = RiskFlag(
                id=str(uuid4()),
                tenant_id=tenant_id,
                student_id=student_id,
                classroom_id=classroom_id,
                week_start=week,
                type="irregular_attendance",
                score=Decimal(str(max(absent_rate, late_rate))),
                details_json={
                    "absent_rate": absent_rate,
                    "late_rate": late_rate,
                    "status_counts": status_counts,
                    "absent_threshold": thr_att.absent_rate_threshold,
                    "late_threshold": thr_att.late_rate_threshold,
                },
            )
            db.add(risk)

    # Rule 3: Response anomaly (placeholder for future implementation)
    # This would require response-level data (c_hat, omit_rate from IRT analysis)
    # For now, we skip this rule
    pass


def run_teacher_dashboard_batch(
    db: Session, tenant_id: str, classroom_ids: List[str], grade_map: Dict[str, str] | None = None
) -> None:
    """Main entrypoint for teacher dashboard batch processing with multitenancy.
    
    Args:
        db: Database session
        tenant_id: Tenant identifier for multitenancy
        classroom_ids: List of classroom IDs to process
        grade_map: Optional mapping of classroom_id -> grade for grade-specific thresholds
    """
    today = date.today()
    week = compute_week_start(today)

    for classroom_id in classroom_ids:
        grade = grade_map.get(classroom_id) if grade_map else None
        
        # Run risk detection with dynamic thresholds
        run_risk_rules(db, tenant_id, classroom_id, week, grade)
        
        # Build class summary
        build_class_summary(db, tenant_id, classroom_id, week)

    db.commit()
