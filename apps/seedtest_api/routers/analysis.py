from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..deps import (
    User,
    get_current_user,
    require_session_access,
    get_r_plumber_client,
    get_r_irt_client,
)
from ..schemas.analysis import AnalysisReport
from ..services.analysis_service import compute_analysis
from ..core.config import config
from ..app.clients.r_plumber import RPlumberClient
from ..app.clients.r_irt import RIRTClient
from ..services.analysis_persistence import persist_irt_calibration

router = APIRouter(prefix=f"{config.API_PREFIX}", tags=["analysis"])


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
    if not getattr(config, "ENABLE_ANALYSIS", True):
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


# -------- R Plumber passthrough endpoints (GLMM, Forecast) --------


class Observation(BaseModel):
    student_id: str
    item_id: str
    correct: int


class GLMMFitRequest(BaseModel):
    observations: List[Observation] = Field(..., description="List of observations")
    formula: Optional[str] = Field(
        default=None,
        description="Optional R formula; default 'correct ~ 1 + (1|student_id) + (1|item_id)'.",
    )


class GLMMPredictRequest(BaseModel):
    model: Dict[str, Any]
    newdata: List[Dict[str, Any]]


@router.get(
    "/analysis/rplumber/health",
    summary="R Plumber health check passthrough",
)
async def rplumber_health(client: RPlumberClient = Depends(get_r_plumber_client)) -> Any:
    return await client.health()


@router.post(
    "/analysis/glmm/fit",
    summary="Fit GLMM via R Plumber and return compact model",
)
async def glmm_fit(
    body: GLMMFitRequest = Body(...),
    _: User = Depends(get_current_user),
    client: RPlumberClient = Depends(get_r_plumber_client),
) -> Any:
    return await client.glmm_fit(
        observations=[o.model_dump() for o in body.observations], formula=body.formula
    )


@router.post(
    "/analysis/glmm/predict",
    summary="Batch predict via R Plumber with compact model",
)
async def glmm_predict(
    body: GLMMPredictRequest = Body(...),
    _: User = Depends(get_current_user),
    client: RPlumberClient = Depends(get_r_plumber_client),
) -> Any:
    return await client.glmm_predict(model=body.model, newdata=body.newdata)


class ForecastRequest(BaseModel):
    mean: float
    sd: float
    target: float


@router.post(
    "/analysis/forecast/summary",
    summary="Forecast summary via R Plumber (Normal approx)",
)
async def forecast_summary(
    body: ForecastRequest = Body(...),
    _: User = Depends(get_current_user),
    client: RPlumberClient = Depends(get_r_plumber_client),
) -> Any:
    return await client.forecast_summary(
        mean=float(body.mean), sd=float(body.sd), target=float(body.target)
    )


# -------- Student abilities (ranef-based summary, computed in API) --------


class StudentAbilitiesRequest(BaseModel):
    model: Dict[str, Any]
    student_ids: Optional[List[str]] = Field(
        default=None, description="Subset of student_ids to include; default all"
    )
    include_fixed_intercept: bool = Field(
        default=True,
        description="If true, add fixed intercept to random effect for ability_logit",
    )


@router.post(
    "/analysis/student-abilities",
    summary="Compute per-student ability summaries from compact model (no R call)",
)
async def student_abilities(
    body: StudentAbilitiesRequest = Body(...),
    _: User = Depends(get_current_user),
) -> Any:
    m = body.model or {}
    # Fixed intercept
    fixef = m.get("fixed_effects") or {}
    # Accept both named and positional first value
    fixed_intercept = None
    if isinstance(fixef, dict):
        fixed_intercept = fixef.get("(Intercept)")
        if fixed_intercept is None:
            # Some serializers may use 'Intercept' key
            fixed_intercept = fixef.get("Intercept")
    if fixed_intercept is None:
        try:
            # Fallback: first numeric in dict values
            fixed_intercept = next(
                (float(v) for v in (fixef.values() if isinstance(fixef, dict) else []) if v is not None),
                0.0,
            )
        except Exception:
            fixed_intercept = 0.0

    # Ranef for students
    ranef = (m.get("ranef") or {}).get("student_id") or []
    # Build map: student_id -> random intercept
    re_map: Dict[str, float] = {}
    for row in ranef:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("id", ""))
        # Try common column names for random intercept
        val = None
        for key in ("(Intercept)", "intercept", "X.Intercept."):
            if key in row:
                try:
                    val = float(row[key])
                    break
                except Exception:
                    continue
        if sid:
            re_map[sid] = float(val) if val is not None else 0.0

    # Candidates
    ids: List[str]
    if body.student_ids:
        ids = [str(s) for s in body.student_ids]
    else:
        ids = list(re_map.keys())

    def inv_logit(x: float) -> float:
        try:
            import math

            return float(1.0 / (1.0 + math.exp(-x)))
        except Exception:
            return 0.0

    out = []
    for sid in ids:
        re_val = float(re_map.get(sid, 0.0))
        intercept = float(fixed_intercept or 0.0) if body.include_fixed_intercept else 0.0
        ability_logit = intercept + re_val
        out.append(
            {
                "student_id": sid,
                "components": {
                    "fixed_intercept": intercept,
                    "ranef_student": re_val,
                },
                "ability_logit": ability_logit,
                "ability_prob": inv_logit(ability_logit),
            }
        )

    return {"status": "ok", "count": len(out), "abilities": out}


# -------- IRT endpoints (calibrate, score via R IRT Plumber) --------


class IRTCalibrateRequest(BaseModel):
    responses: List[List[Optional[int]]] = Field(
        ..., description="Matrix-like list of rows (0/1/None)"
    )


class IRTScoreRequest(BaseModel):
    item_params: List[Dict[str, Any]]
    responses: List[List[Optional[int]]]


@router.get(
    "/analysis/irt/health",
    summary="R IRT Plumber health check",
)
async def r_irt_health(client: RIRTClient = Depends(get_r_irt_client)) -> Any:
    return await client.health()


@router.post(
    "/analysis/irt/calibrate",
    summary="Calibrate IRT (2PL) using R IRT Plumber",
)
async def irt_calibrate(
    body: IRTCalibrateRequest = Body(...),
    _: User = Depends(get_current_user),
    client: RIRTClient = Depends(get_r_irt_client),
) -> Any:
    result = await client.calibrate(responses=body.responses)
    # Try to persist item_params to registry; do not fail request on persistence errors
    item_params = result.get("item_params") if isinstance(result, dict) else None
    persisted: Dict[str, Any] | None = None
    if item_params:
        try:
            persisted = persist_irt_calibration("irt-2pl", item_params, extra_meta={"source": "cron_or_api"})
        except Exception:
            persisted = None
    out = {"status": "ok", "result": result}
    if persisted:
        out["persisted"] = persisted
    return out


@router.post(
    "/analysis/irt/score",
    summary="Score abilities using item parameters (may return 501)",
)
async def irt_score(
    body: IRTScoreRequest = Body(...),
    _: User = Depends(get_current_user),
    client: RIRTClient = Depends(get_r_irt_client),
) -> Any:
    return await client.score(item_params=body.item_params, responses=body.responses)
