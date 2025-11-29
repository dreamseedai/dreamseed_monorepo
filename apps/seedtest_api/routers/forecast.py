from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db.session import get_db

router = APIRouter(prefix="/forecast", tags=["forecast"])

# 점수<->능력치(θ) 선형 변환 파라미터 (환경변수로 주입)
A = float(os.getenv("ABILITY_TO_SCORE_A", "1.0"))
B = float(os.getenv("ABILITY_TO_SCORE_B", "0.0"))


def score_to_theta(target_score: float) -> float:
    if A == 0:
        return target_score  # 안전장치: 변환 비활성
    return (target_score - B) / A


@router.get("/student")
async def forecast_student(
    user_id: str = Query(...),
    target: float = Query(...),
    horizon: int = Query(5),
    db: Session = Depends(get_db),
):
    # Prefer GLMM theta if available, else fallback to attempts percentile->proxy
    row = (
        db.execute(
            text(
                "SELECT theta, se FROM ability_estimates WHERE user_id=:u ORDER BY updated_at DESC LIMIT 1"
            ),
            {"u": user_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "no ability estimate")

    theta = float(row["theta"]) if row["theta"] is not None else 0.0
    se = float(row["se"]) if row["se"] is not None else 0.0

    # target은 기본적으로 '점수' 기준이라고 가정 → θ 기준으로 변환
    target_theta = score_to_theta(target)

    # 기본 응답 데이터 구성
    data = {
        "user_id": user_id,
        "theta": theta,
        "se": se,
        "target": target,
        "target_theta": target_theta,
        "horizon": horizon,
    }

    # reports.py 내 응답 직전 패턴 적용: forecast 계산은 옵션, 실패 시 무시
    try:
        from ..score_analysis.growth import forecast_summary

        # target/horizon은 설정/질의로 변경 가능
        fcast = forecast_summary(
            theta or 0.0, se or 0.0, target=target_theta, k=horizon
        )
        data["forecast"] = fcast
    except Exception:
        pass

    return data
