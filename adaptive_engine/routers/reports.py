from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from adaptive_engine.utils.plotting import theta_se_curve
from adaptive_engine.services.session_repo import get_session_repo


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/theta-se.png")
def theta_se_png(
    session_id: Optional[str] = None,
    theta: Optional[List[float]] = Query(default=None),
    se: Optional[List[float]] = Query(default=None),
    title: Optional[str] = None,
):
    """Return a PNG of the theta–SE curve.

    Use one of:
      - session_id: derive curve from session answered items (SE per step) and theta updates (if available)
      - theta & se arrays directly as query parameters (e.g., ?theta=0&theta=0.5&se=0.6&se=0.5)
    """
    thetas: List[float] = []
    ses: List[float] = []
    if session_id:
        repo = get_session_repo()
        st = repo.get(session_id)
        if not st:
            raise HTTPException(status_code=404, detail="session not found")
        # Prefer true histories if present; else proxy by answered info
        if (
            getattr(st, "theta_history", None)
            and getattr(st, "se_history", None)
            and len(st.theta_history) == len(st.se_history)
            and len(st.theta_history) > 0
        ):
            thetas = list(st.theta_history)
            ses = list(st.se_history)
        else:
            ses = [it.info**-0.5 if it.info > 0 else 1.0 for it in st.answered]
            thetas = list(range(len(ses)))
        if not ses:
            raise HTTPException(status_code=400, detail="no answered items to plot")
    elif theta is not None and se is not None:
        thetas = list(theta)
        ses = list(se)
        if len(thetas) != len(ses) or len(thetas) == 0:
            raise HTTPException(
                status_code=400,
                detail="theta and se arrays must be same length and non-empty",
            )
    else:
        raise HTTPException(
            status_code=400, detail="provide session_id or theta & se arrays"
        )

    img = theta_se_curve(thetas, ses, title=title)
    return Response(content=img, media_type="image/png")
