from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import User, get_current_user, require_session_access
from ..schemas.analysis import AnalysisReport
from ..services.analysis_service import compute_analysis
from ..settings import Settings, settings

router = APIRouter(prefix=f"{settings.API_PREFIX}", tags=["analysis"])


@router.get(
    "/exams/{session_id}/analysis",
    summary="Get detailed analysis and AI feedback for a result",
    response_model=AnalysisReport,
    response_model_exclude_none=True,
)
async def get_analysis(
    session_id: str,
    goal_targets: str | None = Query(
        default=None, description="CSV of target scores, e.g., '140,150'"
    ),
    goal_horizons: str | None = Query(
        default=None, description="CSV of horizons (steps), e.g., '3,5,10'"
    ),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_session_access),
) -> Any:
    s = Settings()
    if not s.ENABLE_ANALYSIS:
        raise HTTPException(status_code=501, detail="Analysis disabled")
    uid = current_user.user_id if current_user else None
    # Parse overrides if provided
    targets_list: list[float] | None = None
    horizons_list: list[int] | None = None
    try:
        if goal_targets:
            parts = [p.strip() for p in goal_targets.split(",") if p.strip()]
            targets_list = []
            for p in parts:
                try:
                    targets_list.append(float(p))
                except Exception:
                    continue
    except Exception:
        pass
    try:
        if goal_horizons:
            parts = [p.strip() for p in goal_horizons.split(",") if p.strip()]
            horizons_list = []
            for p in parts:
                try:
                    v = int(p)
                    if v > 0:
                        horizons_list.append(v)
                except Exception:
                    continue
    except Exception:
        pass
    return compute_analysis(
        session_id, user_id=uid, goal_targets=targets_list, goal_horizons=horizons_list
    )
