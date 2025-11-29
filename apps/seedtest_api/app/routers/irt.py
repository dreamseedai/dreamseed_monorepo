"""
IRT Drift Monitoring API Endpoints
===================================
FastAPI router for IRT item parameters, calibration, and drift alerts
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

# Assume these imports exist in your FastAPI app
# from app.database import get_db_session
# from app.models import (shared_irt schema models if using SQLAlchemy ORM)

router = APIRouter(prefix="/api/v1/irt", tags=["IRT"])


# ==============================================================================
# Pydantic Models
# ==============================================================================
class ItemBase(BaseModel):
    """Item base schema"""

    id: int
    id_str: Optional[str]
    bank_id: str
    lang: str
    topic_tags: List[str] = []
    subtopic_tags: List[str] = []
    is_anchor: bool = False
    exposure_count: int = 0


class ItemWithParams(ItemBase):
    """Item with current IRT parameters"""

    model: Optional[str] = None
    a: Optional[float] = None
    b: Optional[float] = None
    c: Optional[float] = None
    a_se: Optional[float] = None
    b_se: Optional[float] = None
    c_se: Optional[float] = None
    param_version: Optional[int] = None
    effective_from: Optional[datetime] = None


class WindowCreate(BaseModel):
    """Create window request"""

    label: str = Field(..., example="2025-10 monthly")
    start_at: datetime
    end_at: datetime
    population_tags: List[str] = Field(
        default=[], example=["cohort:2025-Q4", "lang:ko"]
    )


class WindowResponse(BaseModel):
    """Window response"""

    id: int
    label: str
    start_at: datetime
    end_at: datetime
    population_tags: List[str]
    created_at: datetime


class CalibrationResult(BaseModel):
    """Item calibration result"""

    id: int
    item_id: int
    window_id: int
    model: str
    a_hat: Optional[float]
    b_hat: float
    c_hat: Optional[float]
    n_responses: int
    drift_flag: Optional[str]
    created_at: datetime


class DriftAlert(BaseModel):
    """Drift alert"""

    id: int
    item_id: int
    item_id_str: Optional[str]
    bank_id: str
    window_id: int
    window_label: str
    metric: str
    value: Optional[float]
    threshold: Optional[float]
    severity: str
    message: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime


class DriftAlertResolve(BaseModel):
    """Resolve drift alert request"""

    resolved: bool = True


# ==============================================================================
# Endpoints
# ==============================================================================


@router.get("/items", response_model=List[ItemWithParams])
async def get_items(
    bank_id: Optional[str] = Query(None, description="Filter by bank ID"),
    lang: Optional[str] = Query(None, description="Filter by language"),
    is_anchor: Optional[bool] = Query(None, description="Filter anchor items"),
    limit: int = Query(100, le=1000, description="Result limit"),
    offset: int = Query(0, ge=0, description="Result offset"),
    # db: AsyncSession = Depends(get_db_session)
):
    """
    Get items with current IRT parameters

    Filters:
    - bank_id: Item bank/pool identifier
    - lang: Language (en/ko/zh-Hans/zh-Hant)
    - is_anchor: True for anchor items only
    """
    # SQL query (adapt to your ORM or use raw SQL)
    query = """
    SELECT 
      i.id, i.id_str, i.bank_id, i.lang, i.topic_tags, i.subtopic_tags,
      i.is_anchor, i.exposure_count,
      p.model, p.a, p.b, p.c, p.a_se, p.b_se, p.c_se,
      p.version AS param_version, p.effective_from
    FROM shared_irt.items i
    LEFT JOIN shared_irt.item_parameters_current p ON i.id = p.item_id
    WHERE 1=1
    """

    params = []
    if bank_id:
        query += f" AND i.bank_id = ${len(params) + 1}"
        params.append(bank_id)
    if lang:
        query += f" AND i.lang = ${len(params) + 1}"
        params.append(lang)
    if is_anchor is not None:
        query += f" AND i.is_anchor = ${len(params) + 1}"
        params.append(is_anchor)

    query += f" ORDER BY i.id LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([limit, offset])

    # Execute query and return results
    # rows = await db.fetch_all(query, params)
    # return [ItemWithParams(**dict(row)) for row in rows]

    # Placeholder for demonstration
    return []


@router.post("/windows", response_model=WindowResponse, status_code=201)
async def create_window(
    window: WindowCreate,
    # db: AsyncSession = Depends(get_db_session)
):
    """
    Create a calibration window

    Windows define time periods and population filters for cohort-based calibration.
    """
    # Insert window
    query = """
    INSERT INTO shared_irt.windows (label, start_at, end_at, population_tags)
    VALUES ($1, $2, $3, $4)
    RETURNING id, label, start_at, end_at, population_tags, created_at
    """

    # row = await db.fetch_one(query, [
    #     window.label,
    #     window.start_at,
    #     window.end_at,
    #     window.population_tags
    # ])

    # return WindowResponse(**dict(row))

    # Placeholder
    raise HTTPException(501, "Not implemented")


@router.get("/windows", response_model=List[WindowResponse])
async def get_windows(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    # db: AsyncSession = Depends(get_db_session)
):
    """List calibration windows"""
    query = """
    SELECT id, label, start_at, end_at, population_tags, created_at
    FROM shared_irt.windows
    ORDER BY created_at DESC
    LIMIT $1 OFFSET $2
    """

    # rows = await db.fetch_all(query, [limit, offset])
    # return [WindowResponse(**dict(row)) for row in rows]

    return []


@router.get("/calibrations/{window_id}", response_model=List[CalibrationResult])
async def get_calibrations_for_window(
    window_id: int,
    drift_only: bool = Query(False, description="Return only items with drift"),
    # db: AsyncSession = Depends(get_db_session)
):
    """
    Get calibration results for a window

    - drift_only=true: Returns only items with detected parameter drift
    """
    query = """
    SELECT id, item_id, window_id, model, a_hat, b_hat, c_hat, n_responses, drift_flag, created_at
    FROM shared_irt.item_calibration
    WHERE window_id = $1
    """

    if drift_only:
        query += " AND drift_flag IS NOT NULL"

    query += " ORDER BY item_id"

    # rows = await db.fetch_all(query, [window_id])
    # return [CalibrationResult(**dict(row)) for row in rows]

    return []


@router.get("/drift-alerts", response_model=List[DriftAlert])
async def get_drift_alerts(
    active_only: bool = Query(True, description="Show only unresolved alerts"),
    severity: Optional[str] = Query(None, regex="^(low|medium|high)$"),
    window_id: Optional[int] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    # db: AsyncSession = Depends(get_db_session)
):
    """
    Get drift alerts

    Filters:
    - active_only: Only unresolved alerts (resolved_at IS NULL)
    - severity: Filter by severity (low/medium/high)
    - window_id: Filter by specific window
    """
    # Use view for convenience
    query = """
    SELECT id, item_id, item_id_str, bank_id, window_id, window_label,
           metric, value, threshold, severity, message, created_at
    FROM shared_irt.v_active_drift_alerts
    WHERE 1=1
    """

    params = []
    if not active_only:
        # Switch to base table if including resolved
        query = """
        SELECT 
          da.id, da.item_id, i.id_str as item_id_str, i.bank_id,
          da.window_id, w.label as window_label,
          da.metric, da.value, da.threshold, da.severity, da.message,
          da.resolved_at, da.created_at
        FROM shared_irt.drift_alerts da
        JOIN shared_irt.items i ON da.item_id = i.id
        JOIN shared_irt.windows w ON da.window_id = w.id
        WHERE 1=1
        """

    if severity:
        query += f" AND severity = ${len(params) + 1}"
        params.append(severity)

    if window_id:
        query += f" AND window_id = ${len(params) + 1}"
        params.append(window_id)

    query += f" ORDER BY severity DESC, created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([limit, offset])

    # rows = await db.fetch_all(query, params)
    # return [DriftAlert(**dict(row)) for row in rows]

    return []


@router.patch("/drift-alerts/{alert_id}", response_model=DriftAlert)
async def resolve_drift_alert(
    alert_id: int,
    action: DriftAlertResolve,
    # db: AsyncSession = Depends(get_db_session)
):
    """
    Resolve or unresolve a drift alert

    - resolved=true: Mark as resolved (sets resolved_at timestamp)
    - resolved=false: Reopen alert (sets resolved_at to NULL)
    """
    if action.resolved:
        query = """
        UPDATE shared_irt.drift_alerts
        SET resolved_at = now()
        WHERE id = $1 AND resolved_at IS NULL
        RETURNING id
        """
    else:
        query = """
        UPDATE shared_irt.drift_alerts
        SET resolved_at = NULL
        WHERE id = $1
        RETURNING id
        """

    # row = await db.fetch_one(query, [alert_id])

    # if not row:
    #     raise HTTPException(404, "Alert not found or already in requested state")

    # # Fetch updated alert
    # alert = await db.fetch_one(
    #     "SELECT * FROM shared_irt.drift_alerts WHERE id = $1",
    #     [alert_id]
    # )
    # return DriftAlert(**dict(alert))

    raise HTTPException(501, "Not implemented")


@router.get("/items/{item_id}/history", response_model=List[CalibrationResult])
async def get_item_calibration_history(
    item_id: int,
    # db: AsyncSession = Depends(get_db_session)
):
    """
    Get calibration history for an item across all windows

    Useful for plotting parameter stability over time
    """
    query = """
    SELECT 
      ic.id, ic.item_id, ic.window_id, ic.model, 
      ic.a_hat, ic.b_hat, ic.c_hat, ic.n_responses, ic.drift_flag,
      ic.created_at, w.label as window_label, w.start_at, w.end_at
    FROM shared_irt.item_calibration ic
    JOIN shared_irt.windows w ON ic.window_id = w.id
    WHERE ic.item_id = $1
    ORDER BY w.start_at DESC
    """

    # rows = await db.fetch_all(query, [item_id])
    # return [CalibrationResult(**dict(row)) for row in rows]

    return []


# ==============================================================================
# Statistics Endpoints
# ==============================================================================


@router.get("/stats/summary")
async def get_irt_stats_summary(
    # db: AsyncSession = Depends(get_db_session)
):
    """
    Get IRT system summary statistics

    Returns:
    - Total items
    - Items with parameters
    - Total windows
    - Active drift alerts (by severity)
    - Recent calibrations
    """
    stats = {
        "total_items": 0,
        "items_with_params": 0,
        "anchor_items": 0,
        "total_windows": 0,
        "active_alerts": {"high": 0, "medium": 0, "low": 0, "total": 0},
        "recent_calibrations": [],
    }

    # Query stats
    # query = """
    # SELECT
    #   (SELECT COUNT(*) FROM shared_irt.items) as total_items,
    #   (SELECT COUNT(*) FROM shared_irt.item_parameters_current) as items_with_params,
    #   (SELECT COUNT(*) FROM shared_irt.items WHERE is_anchor = TRUE) as anchor_items,
    #   (SELECT COUNT(*) FROM shared_irt.windows) as total_windows,
    #   (SELECT COUNT(*) FROM shared_irt.drift_alerts WHERE resolved_at IS NULL AND severity = 'high') as alerts_high,
    #   (SELECT COUNT(*) FROM shared_irt.drift_alerts WHERE resolved_at IS NULL AND severity = 'medium') as alerts_medium,
    #   (SELECT COUNT(*) FROM shared_irt.drift_alerts WHERE resolved_at IS NULL AND severity = 'low') as alerts_low
    # """

    # row = await db.fetch_one(query)
    # stats.update(dict(row))

    return stats
