"""
IRT Analytics API Router
=========================
FastAPI endpoints for IRT drift monitoring, information curves, and statistics.

Endpoints:
- GET /api/analytics/irt/drift/summary - Recent windows with drift statistics
- GET /api/analytics/irt/drift/alerts/{window_id} - Drift alerts for specific window
- POST /api/analytics/irt/info/curves - Item information curves
- GET /api/analytics/irt/stats/global - Global IRT system statistics
- GET /api/analytics/irt/items/{item_id}/history - Parameter history for item

Usage:
    from app.routers.analytics_irt import router
    app.include_router(router)
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.engine import Connection

from shared.auth.dependencies import get_current_user  # type: ignore
from shared.db import get_db
from shared.irt.models import (
    CalibrationResult,
    DriftAlertOut,
    IRTStats,
    ItemHistory,
    ItemInfoCurve,
    Severity,
    TestInfoCurve,
    WindowSummary,
)
from shared.irt.service import fetch_item_info_curves, fetch_test_info_curve

router = APIRouter(prefix="/api/analytics/irt", tags=["IRT Analytics"])


# ==============================================================================
# Drift Monitoring Endpoints
# ==============================================================================

@router.get("/drift/summary", response_model=List[WindowSummary])
async def get_drift_summary(
    limit: int = Query(12, ge=1, le=100, description="Number of recent windows"),
    db: Connection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get summary of recent calibration windows with drift statistics.
    
    Returns last N windows with:
    - Number of calibrated items
    - Number of active drift alerts
    - Breakdown by metric (Δb, Δa, Δc, DIF)
    """
    # Main query with CTEs
    rows = db.execute(
        text("""
            WITH w AS (
                SELECT id, label, start_at, end_at
                FROM shared_irt.windows
                ORDER BY start_at DESC
                LIMIT :limit
            ),
            items AS (
                SELECT window_id, COUNT(DISTINCT item_id) AS n_items
                FROM shared_irt.item_calibration
                WHERE window_id IN (SELECT id FROM w)
                GROUP BY window_id
            ),
            alerts AS (
                SELECT window_id, COUNT(*) AS n_alerts
                FROM shared_irt.drift_alerts
                WHERE window_id IN (SELECT id FROM w)
                  AND resolved_at IS NULL
                GROUP BY window_id
            )
            SELECT 
                w.id,
                w.label,
                w.start_at,
                w.end_at,
                COALESCE(items.n_items, 0) AS n_items,
                COALESCE(alerts.n_alerts, 0) AS n_alerts
            FROM w
            LEFT JOIN items ON items.window_id = w.id
            LEFT JOIN alerts ON alerts.window_id = w.id
            ORDER BY w.start_at DESC
        """),
        {"limit": limit}
    ).mappings().all()
    
    # Build response with metric breakdown
    result = []
    for row in rows:
        # Get alert breakdown by metric
        metric_rows = db.execute(
            text("""
                SELECT metric, COUNT(*) AS cnt
                FROM shared_irt.drift_alerts
                WHERE window_id = :wid
                  AND resolved_at IS NULL
                GROUP BY metric
            """),
            {"wid": row['id']}
        ).mappings().all()
        
        alerts_by_metric = {m['metric']: int(m['cnt']) for m in metric_rows}
        
        result.append(WindowSummary(
            window_id=int(row['id']),
            label=row['label'],
            start_at=row['start_at'],
            end_at=row['end_at'],
            n_items=int(row['n_items']),
            n_alerts=int(row['n_alerts']),
            alerts_by_metric=alerts_by_metric
        ))
    
    return result


@router.get("/drift/alerts/{window_id}", response_model=List[DriftAlertOut])
async def get_drift_alerts(
    window_id: int,
    severity: Optional[Severity] = Query(None, description="Filter by severity"),
    resolved: bool = Query(False, description="Include resolved alerts"),
    db: Connection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get drift alerts for a specific calibration window.
    
    Args:
        window_id: Calibration window ID
        severity: Optional filter by severity (low/medium/high)
        resolved: Include resolved alerts (default: False)
    
    Returns:
        List of drift alerts ordered by severity and creation time
    """
    # Build query with filters
    query = """
        SELECT 
            item_id,
            window_id,
            metric,
            value,
            threshold,
            severity,
            message,
            created_at,
            resolved_at
        FROM shared_irt.drift_alerts
        WHERE window_id = :wid
    """
    
    params = {"wid": window_id}
    
    if not resolved:
        query += " AND resolved_at IS NULL"
    
    if severity:
        query += " AND severity = :sev"
        params["sev"] = severity
    
    query += """
        ORDER BY 
            CASE severity 
                WHEN 'high' THEN 1 
                WHEN 'medium' THEN 2 
                WHEN 'low' THEN 3 
            END,
            created_at DESC
    """
    
    rows = db.execute(text(query), params).mappings().all()
    
    return [DriftAlertOut(**dict(row)) for row in rows]


@router.patch("/drift/alerts/{alert_id}/resolve")
async def resolve_drift_alert(
    alert_id: int,
    resolved: bool = Query(..., description="True to resolve, False to reopen"),
    db: Connection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Resolve or reopen a drift alert.
    
    Args:
        alert_id: Alert ID
        resolved: True to resolve, False to reopen
    """
    if resolved:
        # Resolve alert
        result = db.execute(
            text("""
                UPDATE shared_irt.drift_alerts
                SET resolved_at = now()
                WHERE id = :aid
                  AND resolved_at IS NULL
                RETURNING id
            """),
            {"aid": alert_id}
        )
    else:
        # Reopen alert
        result = db.execute(
            text("""
                UPDATE shared_irt.drift_alerts
                SET resolved_at = NULL
                WHERE id = :aid
                  AND resolved_at IS NOT NULL
                RETURNING id
            """),
            {"aid": alert_id}
        )
    
    if not result.fetchone():
        raise HTTPException(
            status_code=404,
            detail=f"Alert {alert_id} not found or already in target state"
        )
    
    db.commit()
    
    return {"success": True, "alert_id": alert_id, "resolved": resolved}


# ==============================================================================
# Information Curve Endpoints
# ==============================================================================

@router.post("/info/curves/items", response_model=List[ItemInfoCurve])
async def get_item_info_curves(
    item_ids: List[int],
    theta_min: float = Query(-4.0, ge=-6.0, le=0.0),
    theta_max: float = Query(4.0, ge=0.0, le=6.0),
    steps: int = Query(81, ge=21, le=201),
    db: Connection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get item information curves for specified items.
    
    Args:
        item_ids: List of item IDs
        theta_min: Minimum θ value (default: -4.0)
        theta_max: Maximum θ value (default: 4.0)
        steps: Number of points on curve (default: 81)
    
    Returns:
        List of ItemInfoCurve objects with information values at each θ
    """
    if len(item_ids) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 items per request"
        )
    
    curves = fetch_item_info_curves(
        conn=db,
        item_ids=item_ids,
        theta_min=theta_min,
        theta_max=theta_max,
        steps=steps
    )
    
    return curves


@router.post("/info/curves/test", response_model=TestInfoCurve)
async def get_test_info_curve(
    item_ids: List[int],
    theta_min: float = Query(-4.0, ge=-6.0, le=0.0),
    theta_max: float = Query(4.0, ge=0.0, le=6.0),
    steps: int = Query(81, ge=21, le=201),
    db: Connection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get test information curve (sum of item curves).
    
    Args:
        item_ids: List of item IDs in test
        theta_min: Minimum θ value (default: -4.0)
        theta_max: Maximum θ value (default: 4.0)
        steps: Number of points on curve (default: 81)
    
    Returns:
        TestInfoCurve with aggregated information and SEM
    """
    if len(item_ids) > 200:
        raise HTTPException(
            status_code=400,
            detail="Maximum 200 items per test"
        )
    
    if not item_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one item required"
        )
    
    curve = fetch_test_info_curve(
        conn=db,
        item_ids=item_ids,
        theta_min=theta_min,
        theta_max=theta_max,
        steps=steps
    )
    
    return curve


# ==============================================================================
# Statistics Endpoints
# ==============================================================================

@router.get("/stats/global", response_model=IRTStats)
async def get_global_stats(
    db: Connection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get global IRT system statistics.
    
    Returns:
        - Total items
        - Anchor items
        - Active drift alerts (by severity)
        - Total calibration windows
        - Latest window label
        - Items by language
        - Items by bank
    """
    # Main statistics
    stats_row = db.execute(
        text("""
            SELECT 
                COUNT(*) AS total_items,
                COUNT(*) FILTER (WHERE is_anchor = TRUE) AS anchor_items
            FROM shared_irt.items
        """)
    ).mappings().first()
    
    # Active alerts by severity
    alert_rows = db.execute(
        text("""
            SELECT severity, COUNT(*) AS cnt
            FROM shared_irt.drift_alerts
            WHERE resolved_at IS NULL
            GROUP BY severity
        """)
    ).mappings().all()
    
    alerts_by_severity = {row['severity']: int(row['cnt']) for row in alert_rows}
    active_drift_alerts = sum(alerts_by_severity.values())
    
    # Window count and latest
    window_row = db.execute(
        text("""
            SELECT 
                COUNT(*) AS total_windows,
                (SELECT label FROM shared_irt.windows ORDER BY start_at DESC LIMIT 1) AS latest_label
            FROM shared_irt.windows
        """)
    ).mappings().first()
    
    # Items by language
    lang_rows = db.execute(
        text("""
            SELECT lang, COUNT(*) AS cnt
            FROM shared_irt.items
            GROUP BY lang
        """)
    ).mappings().all()
    
    items_by_lang = {row['lang']: int(row['cnt']) for row in lang_rows}
    
    # Items by bank
    bank_rows = db.execute(
        text("""
            SELECT bank_id, COUNT(*) AS cnt
            FROM shared_irt.items
            GROUP BY bank_id
            ORDER BY cnt DESC
            LIMIT 20
        """)
    ).mappings().all()
    
    items_by_bank = {row['bank_id']: int(row['cnt']) for row in bank_rows}
    
    return IRTStats(
        total_items=int(stats_row['total_items']),
        anchor_items=int(stats_row['anchor_items']),
        active_drift_alerts=active_drift_alerts,
        alerts_by_severity=alerts_by_severity,
        total_calibration_windows=int(window_row['total_windows']),
        latest_window_label=window_row['latest_label'],
        items_by_lang=items_by_lang,
        items_by_bank=items_by_bank
    )


@router.get("/items/{item_id}/history", response_model=ItemHistory)
async def get_item_history(
    item_id: int,
    db: Connection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get parameter history for a specific item across all calibration windows.
    
    Args:
        item_id: Item ID
    
    Returns:
        ItemHistory with ordered list of calibrations (oldest to newest)
    """
    # Get item info
    item_row = db.execute(
        text("""
            SELECT id, id_str, is_anchor
            FROM shared_irt.items
            WHERE id = :iid
        """),
        {"iid": item_id}
    ).mappings().first()
    
    if not item_row:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    
    # Get calibration history
    calib_rows = db.execute(
        text("""
            SELECT 
                ic.item_id,
                ic.window_id,
                ic.model,
                ic.a_hat,
                ic.b_hat,
                ic.c_hat,
                ic.a_se,
                ic.b_se,
                ic.c_se,
                ic.a_ci_low,
                ic.a_ci_high,
                ic.b_ci_low,
                ic.b_ci_high,
                ic.c_ci_low,
                ic.c_ci_high,
                ic.n_responses,
                ic.loglik,
                ic.fit_statistics,
                ic.drift_flag,
                ic.dif_metadata,
                ic.created_at,
                w.start_at,
                w.label
            FROM shared_irt.item_calibration ic
            JOIN shared_irt.windows w ON w.id = ic.window_id
            WHERE ic.item_id = :iid
            ORDER BY w.start_at ASC
        """),
        {"iid": item_id}
    ).mappings().all()
    
    history = [CalibrationResult(**dict(row)) for row in calib_rows]
    
    return ItemHistory(
        item_id=int(item_row['id']),
        id_str=item_row['id_str'],
        is_anchor=item_row['is_anchor'],
        history=history
    )


# ==============================================================================
# Window Management Endpoints
# ==============================================================================

@router.get("/windows", response_model=List[WindowSummary])
async def list_windows(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Connection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List calibration windows with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum records to return
    
    Returns:
        List of WindowSummary objects
    """
    rows = db.execute(
        text("""
            SELECT 
                w.id,
                w.label,
                w.start_at,
                w.end_at,
                COUNT(DISTINCT ic.item_id) AS n_items,
                COUNT(da.id) FILTER (WHERE da.resolved_at IS NULL) AS n_alerts
            FROM shared_irt.windows w
            LEFT JOIN shared_irt.item_calibration ic ON ic.window_id = w.id
            LEFT JOIN shared_irt.drift_alerts da ON da.window_id = w.id
            GROUP BY w.id, w.label, w.start_at, w.end_at
            ORDER BY w.start_at DESC
            OFFSET :skip
            LIMIT :limit
        """),
        {"skip": skip, "limit": limit}
    ).mappings().all()
    
    result = []
    for row in rows:
        # Get metric breakdown
        metric_rows = db.execute(
            text("""
                SELECT metric, COUNT(*) AS cnt
                FROM shared_irt.drift_alerts
                WHERE window_id = :wid
                  AND resolved_at IS NULL
                GROUP BY metric
            """),
            {"wid": row['id']}
        ).mappings().all()
        
        alerts_by_metric = {m['metric']: int(m['cnt']) for m in metric_rows}
        
        result.append(WindowSummary(
            window_id=int(row['id']),
            label=row['label'],
            start_at=row['start_at'],
            end_at=row['end_at'],
            n_items=int(row['n_items']),
            n_alerts=int(row['n_alerts']),
            alerts_by_metric=alerts_by_metric
        ))
    
    return result


# ==============================================================================
# Report Generation Endpoints
# ==============================================================================

@router.get("/report/monthly")
async def generate_monthly_report(
    window_id: int = Query(..., description="Calibration window ID"),
    format: str = Query("pdf", regex="^(pdf|html)$", description="Output format"),
    download: bool = Query(True, description="Download file (True) or return path (False)"),
    db: Connection = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate monthly IRT drift report.
    
    Args:
        window_id: Calibration window ID
        format: Output format ('pdf' or 'html')
        download: If True, returns file for download; if False, returns file path
    
    Returns:
        File download or JSON with file path
    
    Example:
        GET /api/analytics/irt/report/monthly?window_id=45
        GET /api/analytics/irt/report/monthly?window_id=45&format=html
        GET /api/analytics/irt/report/monthly?window_id=45&download=false
    """
    import tempfile
    from pathlib import Path
    from fastapi.responses import FileResponse
    
    try:
        from shared.irt.reports import generate_monthly_report
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Report generation not available. Install dependencies: pip install jinja2 weasyprint"
        )
    
    # Verify window exists
    window_result = db.execute(
        text("SELECT id, label FROM shared_irt.windows WHERE id = :wid"),
        {"wid": window_id}
    ).mappings().first()
    
    if not window_result:
        raise HTTPException(
            status_code=404,
            detail=f"Window {window_id} not found"
        )
    
    window_label = window_result['label']
    
    # Generate report in temp directory
    temp_dir = Path(tempfile.gettempdir()) / "irt_reports"
    temp_dir.mkdir(exist_ok=True)
    
    # Sanitize filename
    safe_label = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in window_label)
    filename = f"drift_report_{safe_label}.{format}"
    output_path = temp_dir / filename
    
    try:
        # Generate report
        report_path = generate_monthly_report(
            window_id=window_id,
            out_path=str(output_path),
            format=format,
            include_curves=True,
            max_curves=10
        )
        
        if download:
            # Return file for download
            media_type = "application/pdf" if format == "pdf" else "text/html"
            return FileResponse(
                path=report_path,
                media_type=media_type,
                filename=filename,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
        else:
            # Return file path
            file_size = Path(report_path).stat().st_size
            return {
                "success": True,
                "window_id": window_id,
                "window_label": window_label,
                "format": format,
                "file_path": report_path,
                "file_size_bytes": file_size,
                "file_size_kb": round(file_size / 1024, 2)
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


# ==============================================================================
# Health Check
# ==============================================================================

@router.get("/health")
async def health_check(
    db: Connection = Depends(get_db)
):
    """
    Health check for IRT analytics system.
    
    Returns:
        Status and basic connectivity test
    """
    try:
        # Simple query to verify DB connection
        result = db.execute(text("SELECT COUNT(*) FROM shared_irt.items")).scalar()
        
        return {
            "status": "healthy",
            "database": "connected",
            "total_items": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"IRT analytics system unhealthy: {str(e)}"
        )
