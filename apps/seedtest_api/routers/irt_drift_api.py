"""CAT exposure adjustment API for drift-based item management.

Provides endpoints to:
1. Get exposure weights based on drift alerts
2. Get non-exposure list (items to exclude)
3. Resolve drift alerts after action taken
4. Export rules for CAT selector

Integrates with apps/seedtest_api/app_adaptive_demo.py exposure control.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/irt", tags=["irt_drift"])


class ExposureWeights(BaseModel):
    """Item exposure weights for CAT selection."""

    item_id: str
    weight: float = Field(
        ge=0.0, le=1.0, description="Selection weight (0=excluded, 1=normal)"
    )
    reason: str = Field(description="Reason for weight adjustment")
    alert_severity: Optional[str] = None


class ExposureRulesResponse(BaseModel):
    """Export of CAT exposure rules."""

    run_id: str
    generated_at: datetime
    weights: Dict[str, float] = Field(description="item_id -> weight")
    excluded_items: List[str] = Field(description="Items to exclude completely")
    notes: str


class ResolveAlertRequest(BaseModel):
    """Request to resolve a drift alert."""

    alert_ids: List[int]
    action_taken: str = Field(description="Description of action")


class ResolveAlertResponse(BaseModel):
    """Response after resolving alerts."""

    resolved_count: int
    alert_ids: List[int]


# Stub: replace with actual DB session dependency
async def get_db() -> AsyncSession:
    """Get database session (stub)."""
    raise NotImplementedError("Replace with actual DB session dependency")


@router.get("/exposure/weights", response_model=List[ExposureWeights])
async def get_exposure_weights(
    run_id: Optional[str] = Query(
        None, description="Specific run ID; defaults to latest"
    ),
    severity_threshold: str = Query(
        "moderate", description="Include alerts >= this severity"
    ),
    db: AsyncSession = Depends(get_db),
) -> List[ExposureWeights]:
    """Get item exposure weights based on drift alerts.

    Returns weight adjustments for items with drift alerts:
    - severe: weight = 0.0 (excluded)
    - moderate: weight = 0.5 (reduced exposure)
    - minor: weight = 0.8 (slight reduction)

    Items without alerts get weight = 1.0 (normal).
    """
    # Stub implementation; replace with actual DB queries
    logger.warning("get_exposure_weights: using stub implementation")

    # Example query (pseudo-code):
    # if run_id is None:
    #     # Get latest run
    #     run_id = await db.scalar(select(DriftAlert.run_id).order_by(desc(DriftAlert.created_at)).limit(1))
    #
    # alerts = await db.execute(
    #     select(DriftAlert)
    #     .filter(DriftAlert.run_id == run_id)
    #     .filter(DriftAlert.resolved_at.is_(None))
    # )
    # alerts = alerts.scalars().all()

    # Stub data
    return [
        ExposureWeights(
            item_id="item_123",
            weight=0.0,
            reason="Severe drift in difficulty (Δb=0.42)",
            alert_severity="severe",
        ),
        ExposureWeights(
            item_id="item_456",
            weight=0.5,
            reason="Moderate drift in discrimination (Δa=0.28)",
            alert_severity="moderate",
        ),
        ExposureWeights(
            item_id="item_789",
            weight=0.8,
            reason="Minor drift in guessing (Δc=0.04)",
            alert_severity="minor",
        ),
    ]


@router.get("/exposure/excluded", response_model=List[str])
async def get_excluded_items(
    run_id: Optional[str] = Query(
        None, description="Specific run ID; defaults to latest"
    ),
    db: AsyncSession = Depends(get_db),
) -> List[str]:
    """Get list of items to completely exclude from CAT.

    Returns item IDs with severe drift alerts (unresolved).
    """
    logger.warning("get_excluded_items: using stub implementation")

    # Stub: query for severe alerts
    # alerts = await db.execute(
    #     select(DriftAlert.item_id)
    #     .filter(DriftAlert.run_id == run_id)
    #     .filter(DriftAlert.severity == "severe")
    #     .filter(DriftAlert.resolved_at.is_(None))
    #     .distinct()
    # )
    # return [item_id for item_id, in alerts]

    return ["item_123", "item_999"]


@router.get("/exposure/rules", response_model=ExposureRulesResponse)
async def export_exposure_rules(
    run_id: Optional[str] = Query(
        None, description="Specific run ID; defaults to latest"
    ),
    format: str = Query("json", description="Output format: json, yaml, or env"),
    db: AsyncSession = Depends(get_db),
) -> ExposureRulesResponse:
    """Export complete CAT exposure rules for integration.

    Returns weights and exclusion list suitable for loading into:
    - CAT selector (select_next_with_constraints)
    - Environment variables
    - Configuration files
    """
    logger.warning("export_exposure_rules: using stub implementation")

    # Build rules from alerts
    weights_data = await get_exposure_weights(run_id=run_id, db=db)
    excluded_data = await get_excluded_items(run_id=run_id, db=db)

    weights_dict = {w.item_id: w.weight for w in weights_data}

    return ExposureRulesResponse(
        run_id=run_id or "drift_20251104_160000",
        generated_at=datetime.now(timezone.utc),
        weights=weights_dict,
        excluded_items=excluded_data,
        notes=(
            f"Exposure rules generated from drift alerts. "
            f"{len(excluded_data)} items excluded; "
            f"{len(weights_dict)} items with adjusted weights."
        ),
    )


@router.post("/alerts/resolve", response_model=ResolveAlertResponse)
async def resolve_alerts(
    request: ResolveAlertRequest,
    db: AsyncSession = Depends(get_db),
) -> ResolveAlertResponse:
    """Mark drift alerts as resolved after action taken.

    Updates resolved_at timestamp and logs action taken.
    Use after:
    - Item removed from CAT
    - Parameters recalibrated
    - Exposure weight adjusted
    """
    logger.warning("resolve_alerts: using stub implementation")

    # Stub: update alerts
    # await db.execute(
    #     update(DriftAlert)
    #     .where(DriftAlert.id.in_(request.alert_ids))
    #     .values(resolved_at=datetime.now(timezone.utc))
    # )
    # await db.commit()

    logger.info(
        f"Resolved {len(request.alert_ids)} alerts. Action: {request.action_taken}"
    )

    return ResolveAlertResponse(
        resolved_count=len(request.alert_ids),
        alert_ids=request.alert_ids,
    )


@router.get("/alerts/unresolved", response_model=Dict[str, int])
async def get_unresolved_alert_summary(
    run_id: Optional[str] = Query(
        None, description="Specific run ID; defaults to latest"
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, int]:
    """Get count of unresolved alerts by severity.

    Returns: {"severe": 3, "moderate": 12, "minor": 5}
    """
    logger.warning("get_unresolved_alert_summary: using stub implementation")

    # Stub: count alerts by severity
    # result = await db.execute(
    #     select(DriftAlert.severity, func.count())
    #     .filter(DriftAlert.run_id == run_id)
    #     .filter(DriftAlert.resolved_at.is_(None))
    #     .group_by(DriftAlert.severity)
    # )
    # return {severity: count for severity, count in result}

    return {"severe": 2, "moderate": 8, "minor": 3}


# Integration helper for CAT adaptive demo
def load_drift_exposure_weights(run_id: Optional[str] = None) -> Dict[str, float]:
    """Load drift-based exposure weights for CAT selector.

    Call this in app_adaptive_demo.py to apply drift-based constraints:

    ```python
    from apps.seedtest_api.routers.irt_drift_api import load_drift_exposure_weights

    drift_weights = load_drift_exposure_weights()

    # Apply to CAT selector
    item, info, _ = select_next_with_constraints(
        theta_new,
        DEMO_POOL,
        used_ids=used_ids,
        keymap=km,
        acceptance_probs=drift_weights,  # Override with drift weights
        ...
    )
    ```

    Returns dict: {item_id: weight} where weight in [0.0, 1.0]
    """
    # Stub: in production, query DB or cache
    logger.warning("load_drift_exposure_weights: using stub; implement DB query")
    return {
        "item_123": 0.0,  # Excluded (severe drift)
        "item_456": 0.5,  # Reduced (moderate drift)
        "item_789": 0.8,  # Slightly reduced (minor drift)
    }


# Include router in main app:
# from apps.seedtest_api.routers.irt_drift_api import router as irt_drift_router
# app.include_router(irt_drift_router)
