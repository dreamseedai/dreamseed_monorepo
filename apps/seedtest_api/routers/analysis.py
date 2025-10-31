from __future__ import annotations

from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from datetime import date, datetime, timezone

from ..deps import User, get_current_user, require_session_access
from ..schemas.analysis import AnalysisReport, WeeklyKPI, KPIValues
from ..services.analysis_service import compute_analysis
from ..settings import Settings, settings
from ..db.session import get_db
from ..services.metrics import (
    list_weekly_kpi,
    calculate_and_store_weekly_kpi,
    week_start as iso_week_start,
)
from ..security.jwt import bearer, decode_token
import sqlalchemy as sa
import os

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


# ---- Metrics section ----

def _require_scopes_any(*scopes):
    """Factory: allow access if token has any of the provided scopes; supports LOCAL_DEV shortcut."""
    async def checker(creds=Depends(bearer)):
        # LOCAL_DEV shortcut when no creds
        is_local = Settings().LOCAL_DEV or (os.getenv("LOCAL_DEV", "false").lower() == "true")
        if is_local and not creds:
            return {"sub": "dev-user", "scope": "reports:view analysis:run"}
        if not creds:
            raise HTTPException(401, "Missing Authorization", headers={"WWW-Authenticate": "Bearer"})
        payload = await decode_token(creds.credentials)
        token_scopes = set((payload.get("scope") or "").split())
        if not any(s in token_scopes for s in scopes):
            raise HTTPException(403, "insufficient_scope")
        return payload
    return checker


@router.get(
    "/analysis/metrics/weekly",
    summary="List recent weekly KPIs for a user",
    response_model=List[WeeklyKPI],
)
async def get_weekly_metrics(
    user_id: str = Query(..., description="User ID"),
    weeks: int = Query(4, description="Number of weeks (1..12)"),
    include_empty: bool = Query(False, description="Return [] instead of 404 when empty"),
    _user: Dict = Depends(_require_scopes_any("reports:view", "analysis:run")),
    db=Depends(get_db),
) -> List[WeeklyKPI]:
    if not user_id or not user_id.strip():
        raise HTTPException(400, "invalid user_id")
    # Clamp explicitly per spec
    weeks = max(1, min(12, int(weeks)))
    rows = list_weekly_kpi(db, user_id.strip(), weeks)
    if not rows and not include_empty:
        raise HTTPException(404, "not_found")
    # Pydantic will coerce dict kpis into KPIValues
    return [WeeklyKPI(**r) for r in rows]


class _RecomputeBody(WeeklyKPI):
    # Narrow to required fields for input; week_start optional in body
    week_start: Optional[date] = None  # type: ignore[assignment]


@router.post(
    "/analysis/metrics/recompute",
    summary="Recompute and upsert KPI for a user/week",
    response_model=WeeklyKPI,
)
async def recompute_weekly_metrics(
    body: Dict = Body(..., description="{user_id, week_start?}"),
    _user: Dict = Depends(_require_scopes_any("analysis:run")),
    db=Depends(get_db),
) -> WeeklyKPI:
    try:
        user_id = str(body.get("user_id") or "").strip()
        if not user_id:
            raise HTTPException(400, "invalid body: user_id required")
        ws_val = body.get("week_start")
        if ws_val is None:
            ws = iso_week_start(date.today())
        else:
            # Accept both date object (from client) or ISO string
            if isinstance(ws_val, str):
                try:
                    ws = date.fromisoformat(ws_val)
                except Exception:
                    raise HTTPException(400, "invalid week_start format")
            elif isinstance(ws_val, date):
                ws = ws_val
            else:
                raise HTTPException(400, "invalid week_start type")

        result = calculate_and_store_weekly_kpi(db, user_id, ws)
        kpis = result.get("kpis") or {}
        if not result or all(v is None for v in kpis.values()):
            raise HTTPException(404, "no_data_to_compute")
        # Ensure week_start is a date
        ws_out = result.get("week_start")
        if isinstance(ws_out, str):
            ws_out = date.fromisoformat(ws_out)
        if ws_out is None:
            ws_out = ws
        return WeeklyKPI(user_id=user_id, week_start=ws_out, kpis=KPIValues(**kpis))
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"upsert_failed: {e}")


@router.get(
    "/analysis/irt/theta",
    summary="Get topic-level IRT theta for a user",
)
async def get_irt_theta(
    user_id: str = Query(..., description="User ID"),
    since: Optional[str] = Query(None, description="ISO date to filter from"),
    topics: Optional[str] = Query(None, description="CSV of topic_ids"),
    _user: Dict = Depends(_require_scopes_any("reports:view", "analysis:run")),
    db=Depends(get_db),
) -> List[Dict[str, Any]]:
    if not user_id or not user_id.strip():
        raise HTTPException(400, "invalid user_id")
    topic_ids: Optional[List[str]] = None
    if topics:
        topic_ids = [t.strip() for t in topics.split(",") if t.strip()]
    since_dt = None
    if since:
        try:
            sdt = date.fromisoformat(since)
            since_dt = datetime(sdt.year, sdt.month, sdt.day, 0, 0, 0, tzinfo=timezone.utc)
        except Exception:
            raise HTTPException(400, "invalid since date format")

    # Prefer student_topic_theta; else fallback to mirt_ability as general ability
    try:
        params: Dict[str, Any] = {"uid": user_id.strip()}
        cond = ["user_id = :uid"]
        if since_dt is not None:
            cond.append("fitted_at >= :since")
            params["since"] = since_dt
        if topic_ids:
            # Build list parameter safely
            in_clause = ",".join(f":t{i}" for i in range(len(topic_ids)))
            cond.append(f"topic_id IN ({in_clause})")
            for i, t in enumerate(topic_ids):
                params[f"t{i}"] = t
        sql = sa.text(
            f"""
            SELECT topic_id, theta, se, fitted_at
            FROM student_topic_theta
            WHERE {' AND '.join(cond)}
            ORDER BY fitted_at DESC
            LIMIT 200
            """
        )
        rows = db.execute(sql, params).mappings().all()
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "topic_id": r.get("topic_id"),
                    "theta": float(r.get("theta")) if r.get("theta") is not None else None,
                    "se": float(r.get("se")) if r.get("se") is not None else None,
                    "model": "mirt",  # topic-level store assumed mirt-derived
                    "fitted_at": (r.get("fitted_at").isoformat() if isinstance(r.get("fitted_at"), datetime) else str(r.get("fitted_at"))),
                }
            )
        if out:
            return out
    except Exception:
        pass

    # Fallback to general ability
    try:
        params = {"uid": user_id.strip()}
        sql2 = sa.text(
            """
            SELECT theta, se, fitted_at
            FROM mirt_ability
            WHERE user_id = :uid
            ORDER BY fitted_at DESC
            LIMIT 50
            """
        )
        rows2 = db.execute(sql2, params).mappings().all()
        if not rows2:
            raise HTTPException(404, "not_found")
        out2: List[Dict[str, Any]] = []
        for r in rows2:
            out2.append(
                {
                    "topic_id": None,
                    "theta": float(r.get("theta")) if r.get("theta") is not None else None,
                    "se": float(r.get("se")) if r.get("se") is not None else None,
                    "model": "mirt",
                    "fitted_at": (r.get("fitted_at").isoformat() if isinstance(r.get("fitted_at"), datetime) else str(r.get("fitted_at"))),
                }
            )
        return out2
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "not_found")
