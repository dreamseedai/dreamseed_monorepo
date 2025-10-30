"""
AI 알고리즘 및 분석(피드백 생성) — 구현 개요

본 모듈은 성적 리포트 생성 시 다음 요소를 종합하여 개인화 피드백을 생성합니다.

1) 혼합효과 모델(Mixed Effects)
    - 많은 응답 데이터가 축적될 경우, 학생 개인차(능력)와 문항 난이도를 동시에 추정하여 편향을 제거합니다.
    - 구성요소: 학생 랜덤효과(ability), 문항 난이도(item difficulty). 결과는 공정하고 일관된 능력 측정을 담보합니다.
    - 구성 선택: config.ANALYSIS_ENGINE = "heuristic" | "irt" | "mixed_effects" 에 따라 엔진이 교체됩니다.

2) 성장 예측(Growth Forecast)
    - 현재 점수/능력을 기반으로 향후 성취 궤적을 예측합니다.
    - 본 구현은 기본적으로 완만한 선형-감쇠 가정(linear taper)을 사용하되,
      표준오차(SE)를 활용해 목표 점수 도달 확률(예: 5회 내 150점 달성 확률)을 계산하여 리포트에 포함합니다.
    - Bayesian Update 기반의 보다 정교한 추정은 엔진 확장 시 대체 가능합니다.

3) 추천 엔진(Recommendations)
    - 약점 토픽을 추정하여 학습 리소스를 추천합니다.
    - 기본(rule-based) → 고장 시 내부 규칙으로 폴백. 향후 협업필터링/콘텐츠 메타데이터 기반 엔진으로 교체 가능.

4) 비교 및 벤치마크(Benchmark)
    - 개인 성적과 집단 통계(백분위 등)를 연결합니다.
    - 전체 분포는 배치로 갱신 가능(예: 1일 1회), 조회 시 최신 기준을 표시합니다.

본 파일의 compute_analysis()는 위 요소들을 조합하여 AnalysisReport 스키마를 반환합니다.
"""
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
from ..core.config import config


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
    s = config
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
                    theta=0.0, standard_error=None, method=getattr(s, "ANALYSIS_ENGINE", "heuristic")
                ),
            )

    topics = res.get("topics") or res.get("topic_breakdown") or []
    insights = _derive_topic_insights(topics if isinstance(topics, list) else [])
    # Ability estimate: delegate to configured engine (heuristic | irt | mixed_effects)
    eng = get_engine(getattr(s, "ANALYSIS_ENGINE", "heuristic"))
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

    # Use pluggable recommender (defaults to rule-based); prefer passing computed ability
    try:
        rec_engine = get_recommender(getattr(s, "RECOMMENDER_ENGINE", "rule"))
        recs = rec_engine.recommend(insights, ability_theta=ability.theta, top_k=3)
        if not isinstance(recs, list) or not all(hasattr(r, "message") for r in recs):
            raise ValueError("invalid_recs")
    except Exception:
        recs = _recommend_from_topics(insights)

    # Growth forecast from current score (ensure we cover requested horizons if any)
    score_scaled = res.get("score_scaled") or (
        (res.get("score") or {}).get("scaled")
        if isinstance(res.get("score"), dict)
        else None
    )
    # Resolve goal config: prefer per-request overrides, else settings
    if not goal_targets:
        # Prefer uppercase env-driven names; keep lowercase for back-compat
        goal_targets = (
            getattr(s, "ANALYSIS_GOAL_TARGETS", None)
            or getattr(s, "analysis_goal_targets", None)
            or []
        )
    if not goal_horizons:
        goal_horizons = (
            getattr(s, "ANALYSIS_GOAL_HORIZONS", None)
            or getattr(s, "analysis_goal_horizons", None)
            or []
        )
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
