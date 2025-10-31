"""핵심 지표 API 엔드포인트

학습 분석을 위한 핵심 지표들을 제공하는 API입니다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..services.metrics_calculator import MetricsCalculator, get_metrics_calculator
from ..services.weekly_kpi_job import recompute_weekly_kpi_for_recent_users
from ..services.topic_ability_service import TopicAbilityService, get_topic_ability_service
from ..core.config import config
from ..deps import get_current_user

router = APIRouter(prefix=f"{config.API_PREFIX}/metrics", tags=["metrics"])


# === 요청/응답 모델 ===

class ImprovementIndexRequest(BaseModel):
    topic_id: Optional[str] = None
    weeks: int = 2
    exposure_penalty: float = 0.1
    confidence_penalty: float = 0.05


class ImprovementIndexResponse(BaseModel):
    improvement_index: float
    theta_improvement: float
    exposure_factor: float
    confidence_factor: float
    method: str


class EfficiencyIndexRequest(BaseModel):
    topic_id: Optional[str] = None
    weeks: int = 2


class EfficiencyIndexResponse(BaseModel):
    efficiency_index: float
    recent_median_time: float
    earlier_median_time: float
    improvement_rate: float
    method: str


class RecoveryIndexRequest(BaseModel):
    topic_id: Optional[str] = None
    weeks: int = 2
    weakness_threshold: float = 0.6


class RecoveryIndexResponse(BaseModel):
    recovery_index: float
    weak_concepts: List[str]
    total_transitions: int
    successful_transitions: int
    method: str


class EngagementIndexRequest(BaseModel):
    weeks: int = 2
    weights: Optional[Dict[str, float]] = None


class EngagementIndexResponse(BaseModel):
    engagement_index: float
    session_frequency: float
    learning_interval: float
    hint_usage: float
    dwell_time: float
    method: str


class DropoutRiskRequest(BaseModel):
    days_threshold: int = 14
    baseline_risk: float = 0.1


class DropoutRiskResponse(BaseModel):
    dropout_risk: float
    days_since_access: int
    risk_level: str  # "low", "medium", "high", "critical"
    method: str


class TopicAbilityRequest(BaseModel):
    topic_id: str
    responses: List[Dict[str, Any]]
    prior_mean: float = 0.0
    prior_sd: float = 1.0


class TopicAbilityResponse(BaseModel):
    topic_id: str
    theta: float
    standard_error: float
    method: str


class ComprehensiveMetricsResponse(BaseModel):
    user_id: str
    improvement_index: float
    efficiency_index: float
    recovery_index: float
    engagement_index: float
    dropout_risk: float
    topic_abilities: Dict[str, Dict[str, Any]]
    calculated_at: str


class WeeklyRecomputeRequest(BaseModel):
    weeks_window: int = 1
    limit_users: Optional[int] = None


class WeeklyRecomputeResponse(BaseModel):
    week_start: str
    users_considered: int
    users_processed: int


# === API 엔드포인트 ===

@router.post("/improvement", response_model=ImprovementIndexResponse)
async def calculate_improvement_index(
    request: ImprovementIndexRequest,
    current_user: Any = Depends(get_current_user),
    calculator: MetricsCalculator = Depends(get_metrics_calculator)
) -> ImprovementIndexResponse:
    """향상지수 I_t 계산"""
    try:
        user_id = str(current_user.user_id)
        
        improvement_index = calculator.calculate_improvement_index(
            user_id=user_id,
            topic_id=request.topic_id,
            weeks=request.weeks,
            exposure_penalty=request.exposure_penalty,
            confidence_penalty=request.confidence_penalty
        )
        
        # 상세 정보 계산 (더미 데이터)
        theta_improvement = 0.2  # TODO: 실제 계산
        exposure_factor = 0.8    # TODO: 실제 계산
        confidence_factor = 0.7  # TODO: 실제 계산
        
        return ImprovementIndexResponse(
            improvement_index=improvement_index,
            theta_improvement=theta_improvement,
            exposure_factor=exposure_factor,
            confidence_factor=confidence_factor,
            method="improvement_calculation"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"향상지수 계산 실패: {str(e)}")


@router.post("/efficiency", response_model=EfficiencyIndexResponse)
async def calculate_efficiency_index(
    request: EfficiencyIndexRequest,
    current_user: Any = Depends(get_current_user),
    calculator: MetricsCalculator = Depends(get_metrics_calculator)
) -> EfficiencyIndexResponse:
    """시간효율 E_t 계산"""
    try:
        user_id = str(current_user.user_id)
        
        efficiency_index = calculator.calculate_efficiency_index(
            user_id=user_id,
            topic_id=request.topic_id,
            weeks=request.weeks
        )
        
        # 상세 정보 계산 (더미 데이터)
        recent_median_time = 25.5  # TODO: 실제 계산
        earlier_median_time = 35.2  # TODO: 실제 계산
        improvement_rate = efficiency_index
        
        return EfficiencyIndexResponse(
            efficiency_index=efficiency_index,
            recent_median_time=recent_median_time,
            earlier_median_time=earlier_median_time,
            improvement_rate=improvement_rate,
            method="efficiency_calculation"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시간효율 계산 실패: {str(e)}")


@router.post("/recovery", response_model=RecoveryIndexResponse)
async def calculate_recovery_index(
    request: RecoveryIndexRequest,
    current_user: Any = Depends(get_current_user),
    calculator: MetricsCalculator = Depends(get_metrics_calculator)
) -> RecoveryIndexResponse:
    """회복도 R_t 계산"""
    try:
        user_id = str(current_user.user_id)
        
        recovery_index = calculator.calculate_recovery_index(
            user_id=user_id,
            topic_id=request.topic_id,
            weeks=request.weeks,
            weakness_threshold=request.weakness_threshold
        )
        
        # 상세 정보 계산 (더미 데이터)
        weak_concepts = ["concept_1", "concept_2"]  # TODO: 실제 계산
        total_transitions = 10  # TODO: 실제 계산
        successful_transitions = int(recovery_index * total_transitions)
        
        return RecoveryIndexResponse(
            recovery_index=recovery_index,
            weak_concepts=weak_concepts,
            total_transitions=total_transitions,
            successful_transitions=successful_transitions,
            method="recovery_calculation"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회복도 계산 실패: {str(e)}")


@router.post("/engagement", response_model=EngagementIndexResponse)
async def calculate_engagement_index(
    request: EngagementIndexRequest,
    current_user: Any = Depends(get_current_user),
    calculator: MetricsCalculator = Depends(get_metrics_calculator)
) -> EngagementIndexResponse:
    """참여도 A_t 계산"""
    try:
        user_id = str(current_user.user_id)
        
        engagement_index = calculator.calculate_engagement_index(
            user_id=user_id,
            weeks=request.weeks,
            weights=request.weights
        )
        
        # 상세 정보 계산 (더미 데이터)
        session_frequency = 0.8  # TODO: 실제 계산
        learning_interval = 0.7  # TODO: 실제 계산
        hint_usage = 0.6         # TODO: 실제 계산
        dwell_time = 0.9         # TODO: 실제 계산
        
        return EngagementIndexResponse(
            engagement_index=engagement_index,
            session_frequency=session_frequency,
            learning_interval=learning_interval,
            hint_usage=hint_usage,
            dwell_time=dwell_time,
            method="engagement_calculation"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"참여도 계산 실패: {str(e)}")


@router.post("/dropout-risk", response_model=DropoutRiskResponse)
async def calculate_dropout_risk(
    request: DropoutRiskRequest,
    current_user: Any = Depends(get_current_user),
    calculator: MetricsCalculator = Depends(get_metrics_calculator)
) -> DropoutRiskResponse:
    """이탈위험 S(t) 계산"""
    try:
        user_id = str(current_user.user_id)
        
        dropout_risk = calculator.calculate_dropout_risk(
            user_id=user_id,
            days_threshold=request.days_threshold,
            baseline_risk=request.baseline_risk
        )
        
        # 위험도 레벨 결정
        if dropout_risk < 0.3:
            risk_level = "low"
        elif dropout_risk < 0.6:
            risk_level = "medium"
        elif dropout_risk < 0.8:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        # 상세 정보 계산 (더미 데이터)
        days_since_access = 5  # TODO: 실제 계산
        
        return DropoutRiskResponse(
            dropout_risk=dropout_risk,
            days_since_access=days_since_access,
            risk_level=risk_level,
            method="dropout_risk_calculation"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이탈위험 계산 실패: {str(e)}")


@router.post("/topic-ability", response_model=TopicAbilityResponse)
async def calculate_topic_ability(
    request: TopicAbilityRequest,
    current_user: Any = Depends(get_current_user),
    service: TopicAbilityService = Depends(get_topic_ability_service)
) -> TopicAbilityResponse:
    """토픽별 숙련도 θ 추정"""
    try:
        user_id = str(current_user.user_id)
        
        theta, se, method = service.estimate_topic_ability(
            user_id=user_id,
            topic_id=request.topic_id,
            responses=request.responses,
            prior_mean=request.prior_mean,
            prior_sd=request.prior_sd
        )
        
        return TopicAbilityResponse(
            topic_id=request.topic_id,
            theta=theta,
            standard_error=se,
            method=method
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"토픽별 숙련도 계산 실패: {str(e)}")


@router.get("/topic-abilities")
async def get_topic_abilities(
    topic_ids: Optional[List[str]] = Query(default=None),
    current_user: Any = Depends(get_current_user),
    service: TopicAbilityService = Depends(get_topic_ability_service)
) -> Dict[str, Any]:
    """사용자의 토픽별 숙련도 조회"""
    try:
        user_id = str(current_user.user_id)
        
        abilities = service.get_topic_abilities(user_id, topic_ids)
        
        return {
            "user_id": user_id,
            "topic_abilities": abilities,
            "total_topics": len(abilities)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"토픽별 숙련도 조회 실패: {str(e)}")


@router.get("/comprehensive")
async def get_comprehensive_metrics(
    weeks: int = Query(default=2, description="분석 기간 (주)"),
    current_user: Any = Depends(get_current_user),
    calculator: MetricsCalculator = Depends(get_metrics_calculator),
    service: TopicAbilityService = Depends(get_topic_ability_service)
) -> ComprehensiveMetricsResponse:
    """종합 핵심 지표 조회"""
    try:
        user_id = str(current_user.user_id)
        
        # 모든 지표 계산
        improvement_index = calculator.calculate_improvement_index(user_id, weeks=weeks)
        efficiency_index = calculator.calculate_efficiency_index(user_id, weeks=weeks)
        recovery_index = calculator.calculate_recovery_index(user_id, weeks=weeks)
        engagement_index = calculator.calculate_engagement_index(user_id, weeks=weeks)
        dropout_risk = calculator.calculate_dropout_risk(user_id)
        
        # 토픽별 숙련도 조회
        topic_abilities = service.get_topic_abilities(user_id)
        
        return ComprehensiveMetricsResponse(
            user_id=user_id,
            improvement_index=improvement_index,
            efficiency_index=efficiency_index,
            recovery_index=recovery_index,
            engagement_index=engagement_index,
            dropout_risk=dropout_risk,
            topic_abilities=topic_abilities,
            calculated_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"종합 지표 계산 실패: {str(e)}")


@router.get("/weak-topics")
async def get_weak_topics(
    threshold: float = Query(default=-0.5, description="취약 토픽 임계값"),
    min_responses: int = Query(default=5, description="최소 응답 수"),
    current_user: Any = Depends(get_current_user),
    service: TopicAbilityService = Depends(get_topic_ability_service)
) -> Dict[str, Any]:
    """취약 토픽 식별"""
    try:
        user_id = str(current_user.user_id)
        
        weak_topics = service.identify_weak_topics(
            user_id=user_id,
            threshold=threshold,
            min_responses=min_responses
        )
        
        return {
            "user_id": user_id,
            "weak_topics": weak_topics,
            "total_weak_topics": len(weak_topics),
            "threshold": threshold
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"취약 토픽 식별 실패: {str(e)}")


@router.post("/weekly/recompute", response_model=WeeklyRecomputeResponse)
async def recompute_weekly_kpi(
    request: WeeklyRecomputeRequest,
    current_user: Any = Depends(get_current_user),
    calculator: MetricsCalculator = Depends(get_metrics_calculator),
) -> WeeklyRecomputeResponse:
    """최근 활동 사용자를 대상으로 이번 주 KPI를 재계산하여 저장합니다.

    참고: 현재 구현은 '이번 주' 버킷에만 저장하며, 과거 주차 백필은 포함하지 않습니다.
    """
    try:
        # FastAPI DI로 세션이 열린 calculator를 받았으므로 동일 세션을 활용
        summary = recompute_weekly_kpi_for_recent_users(
            db=calculator.db,
            weeks_window=max(1, request.weeks_window),
            limit_users=request.limit_users,
        )
        return WeeklyRecomputeResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주간 KPI 재계산 실패: {str(e)}")
