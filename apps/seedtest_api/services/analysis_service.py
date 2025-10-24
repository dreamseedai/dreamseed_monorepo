from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..schemas.analysis import (
    AbilityEstimate,
    AnalysisReport,
    Benchmark,
    GrowthForecast,
    GrowthForecastPoint,
    RecommendationItem,
    TopicInsight,
)
from ..services import result_service
from ..services.recommendation import get_recommender
from ..services.score_analysis import get_engine
from ..settings import Settings


def _derive_topic_insights(topics: List[Dict[str, Any]]) -> List[TopicInsight]:
    out: List[TopicInsight] = []
    for t in topics or []:
        acc = float(t.get("accuracy") or 0.0)
        out.append(
            TopicInsight(
                topic=str(t.get("topic") or "general"),
                accuracy=acc,
                correct=int(t.get("correct") or 0),
                total=int(t.get("total") or 0),
                strength=acc >= 0.75,
            )
        )
    return out


def _recommend_from_topics(insights: List[TopicInsight]) -> List[RecommendationItem]:
    recs: List[RecommendationItem] = []
    weaknesses = [ti for ti in insights if ti.accuracy <= 0.6]
    for w in weaknesses[:3]:
        recs.append(
            RecommendationItem(
                topic=w.topic,
                kind="study",
                message=f"{w.topic} 영역: 핵심 개념 복습과 유사 문항 반복 풀이를 권장합니다.",
            )
        )
    if not recs:
        recs.append(
            RecommendationItem(
                kind="meta",
                message="현재 전반적인 성취도가 양호합니다. 오답 노트 기반의 약점 보완과 시간 배분 연습을 지속하세요.",
            )
        )
    return recs


def _simple_forecast(score_scaled: Optional[float], horizon: int = 6) -> GrowthForecast:
    # Minimal forecast: assume small linear improvement tapering over horizon
    base = float(score_scaled or 0.0)
    points: List[GrowthForecastPoint] = []
    for i in range(1, horizon + 1):
        inc = max(0.0, (horizon - i + 1)) * 0.5  # diminishing increments
        points.append(GrowthForecastPoint(step=i, score_scaled=base + inc))
    return GrowthForecast(horizon=horizon, points=points, method="linear_taper")


def _benchmark(percentile: Optional[int]) -> Optional[Benchmark]:
    if percentile is None:
        return None
    label = "cohort"
    return Benchmark(percentile=int(percentile), label=label)


def compute_analysis(
    session_id: str,
    *,
    user_id: Optional[str] = None,
    goal_targets: Optional[list[float]] = None,
    goal_horizons: Optional[list[int]] = None,
) -> AnalysisReport:
    s = Settings()
    # Prefer cached result from DB; otherwise compute in-memory
    try:
        res = result_service.get_result_from_db(session_id, expected_user_id=user_id)
    except Exception as e:
        logging.getLogger(__name__).warning(
            "analysis.compute: DB fetch failed for session_id=%s (err=%s); falling back to compute_result",
            session_id,
            e,
        )
        res = None

    if res is None:
        res = result_service.compute_result(session_id, force=True, user_id=user_id)
        if str(res.get("status") or "").lower() not in ("ready",):
            # Fallback empty shell
            return AnalysisReport(
                exam_session_id=session_id,
                user_id=user_id,
                ability=AbilityEstimate(
                    theta=0.0, standard_error=None, method=s.ANALYSIS_ENGINE
                ),
            )

    topics = res.get("topics") or res.get("topic_breakdown") or []
    insights = _derive_topic_insights(topics if isinstance(topics, list) else [])
    # Use pluggable recommender (defaults to rule-based); fall back to internal rule if anything fails
    try:
        rec_engine = get_recommender(s.RECOMMENDER_ENGINE)
        recs = rec_engine.recommend(insights, ability_theta=None, top_k=3)
        if not isinstance(recs, list) or not all(hasattr(r, "message") for r in recs):
            raise ValueError("invalid_recs")
    except Exception:
        recs = _recommend_from_topics(insights)

    # Ability estimate: delegate to configured engine (heuristic | irt | mixed_effects)
    eng = get_engine(s.ANALYSIS_ENGINE)
    theta, se, method = eng.estimate_ability(
        score_scaled=res.get("score_scaled")
        or (
            (res.get("score") or {}).get("scaled")
            if isinstance(res.get("score"), dict)
            else None
        ),
        ability_estimate=res.get("ability_estimate"),
        standard_error=(
            res.get("standard_error")
            if isinstance(res.get("standard_error"), (int, float))
            else None
        ),
        topics=topics,
    )
    ability = AbilityEstimate(
        theta=float(theta),
        standard_error=(float(se) if se is not None else None),
        method=method,
    )

    # Growth forecast from current score (ensure we cover requested horizons if any)
    score_scaled = res.get("score_scaled") or (
        (res.get("score") or {}).get("scaled")
        if isinstance(res.get("score"), dict)
        else None
    )
    # Resolve goal config: prefer per-request overrides, else settings
    if not goal_targets:
        goal_targets = s.analysis_goal_targets or []
    if not goal_horizons:
        goal_horizons = s.analysis_goal_horizons or []
    # Defaults if still empty
    if not goal_targets:
        goal_targets = [150.0]
    if not goal_horizons:
        goal_horizons = [5]
    max_h = max(6, max(goal_horizons) if goal_horizons else 6)
    forecast = _simple_forecast(score_scaled, horizon=max_h)

    # Benchmark:
    pct_val = res.get("percentile")
    pct: Optional[int] = int(pct_val) if isinstance(pct_val, (int, float)) else None
    bench = _benchmark(pct)

    uid = res.get("user_id") or user_id

    # Augment forecast with probability-of-achievement goals for configured targets/horizons
    try:
        if forecast is not None:

            def _normal_cdf(z: float) -> float:
                import math

                return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

            # Convert theta SE to scaled-score sigma; if missing, use a conservative default
            sigma = (float(se) * 50.0) if (se is not None) else 12.0
            if forecast.points:
                from ..schemas.analysis import GrowthForecast as GF

                for h in goal_horizons or [5]:
                    if h <= 0:
                        continue
                    if h > len(forecast.points):
                        # safety: cap to last available point
                        h_idx = len(forecast.points) - 1
                    else:
                        h_idx = h - 1
                    mean_at_h = float(forecast.points[h_idx].score_scaled)
                    for target in goal_targets or [150.0]:
                        if sigma <= 0:
                            prob = 1.0 if mean_at_h >= float(target) else 0.0
                        else:
                            z = (mean_at_h - float(target)) / float(sigma)
                            prob = 1.0 - _normal_cdf(-z)
                        forecast.goals.append(
                            GF.ForecastGoal(
                                target_score=float(target),
                                horizon=int(h),
                                probability=max(0.0, min(1.0, float(prob))),
                            )
                        )
    except Exception:
        # Non-fatal; omit goals on error
        pass

    return AnalysisReport(
        exam_session_id=session_id,
        user_id=uid,
        ability=ability,
        topic_insights=insights,
        recommendations=recs,
        forecast=forecast,
        benchmark=bench,
    )
