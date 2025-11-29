"""Score Analysis Service - AI 알고리즘 및 분석 (피드백 생성)

성적 리포트를 위한 AI 기반 분석 시스템
====================================

이 모듈은 다음 기능을 제공합니다:
1. 혼합효과 모형 기반 공정한 능력 추정
2. IRT 기반 기본 채점 (데이터 부족 시)
3. 토픽별 강약점 분석
4. 맞춤형 학습 추천
5. 성적 성장 예측
6. 비교 기준 (백분위) 제공

Usage
-----
from adaptive_engine.services.score_analysis import ScoreAnalysisService

service = ScoreAnalysisService(engine="mixed_effects")
report = service.generate_report(session_id="abc123", user_id="user1")
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Mapping, Any, Tuple
from enum import Enum

# IRT 기본 함수
from shared.irt import (
    mle_theta_fisher,
    eap_theta,
    item_information_3pl,
)

# 혼합효과 모형
from shared.mixed_effects import (
    fit_mixed_effects,
    estimate_single_student_with_calibrated_items,
    StudentAbility,
    ItemDifficulty,
)

# 베이지안 성장 예측
from shared.bayesian_growth import (
    BayesianGrowthPredictor,
    GrowthPrediction as BayesianGrowthPrediction,
)


class AnalysisEngine(str, Enum):
    """분석 엔진 종류"""
    IRT = "irt"  # 기본 IRT (데이터 부족 시)
    MIXED_EFFECTS = "mixed_effects"  # 혼합효과 모형 (권장)
    HYBRID = "hybrid"  # 자동 선택 (데이터 양에 따라)


@dataclass
class TopicInsight:
    """토픽별 분석 결과"""
    topic: str
    n_items: int
    n_correct: int
    accuracy: float
    avg_difficulty: float
    strength_level: str  # "strong" | "medium" | "weak"
    
    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "n_items": self.n_items,
            "n_correct": self.n_correct,
            "accuracy": self.accuracy,
            "avg_difficulty": self.avg_difficulty,
            "strength_level": self.strength_level,
        }


@dataclass
class Recommendation:
    """학습 추천"""
    type: str  # "concept" | "practice" | "review" | "challenge"
    topic: str
    message: str
    priority: int  # 1 (highest) to 5 (lowest)
    
    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "topic": self.topic,
            "message": self.message,
            "priority": self.priority,
        }


@dataclass
class GrowthForecast:
    """성적 성장 예측"""
    current_score: float
    forecast_steps: List[Dict[str, float]]  # [{"step": 1, "score": 520}, ...]
    confidence_level: float
    assumptions: List[str]
    
    def to_dict(self) -> dict:
        return {
            "current_score": self.current_score,
            "forecast_steps": self.forecast_steps,
            "confidence_level": self.confidence_level,
            "assumptions": self.assumptions,
        }


@dataclass
class Benchmark:
    """비교 기준"""
    percentile: float  # 0.0 ~ 1.0
    rank_description: str  # e.g., "상위 25%"
    cohort_size: Optional[int]
    next_goal: Optional[str]
    
    def to_dict(self) -> dict:
        return {
            "percentile": self.percentile,
            "rank_description": self.rank_description,
            "cohort_size": self.cohort_size,
            "next_goal": self.next_goal,
        }


@dataclass
class ScoreAnalysisReport:
    """종합 성적 분석 리포트"""
    student_id: str
    session_id: str
    
    # 능력 추정
    theta: float
    theta_se: float
    scaled_score: Optional[int]
    
    # 분석 엔진
    engine_used: str
    
    # 토픽별 분석
    topic_insights: List[TopicInsight]
    
    # 추천
    recommendations: List[Recommendation]
    
    # 성장 예측
    growth_forecast: Optional[GrowthForecast]
    
    # 비교 기준
    benchmark: Optional[Benchmark]
    
    # 메타 정보
    n_items: int
    n_correct: int
    overall_accuracy: float
    
    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "session_id": self.session_id,
            "ability": {
                "theta": self.theta,
                "se": self.theta_se,
                "scaled_score": self.scaled_score,
            },
            "engine_used": self.engine_used,
            "topic_insights": [t.to_dict() for t in self.topic_insights],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "growth_forecast": self.growth_forecast.to_dict() if self.growth_forecast else None,
            "benchmark": self.benchmark.to_dict() if self.benchmark else None,
            "summary": {
                "n_items": self.n_items,
                "n_correct": self.n_correct,
                "overall_accuracy": self.overall_accuracy,
            },
        }


# ==============================================================================
# Score Analysis Service
# ==============================================================================

class ScoreAnalysisService:
    """성적 분석 서비스
    
    Parameters
    ----------
    engine : AnalysisEngine
        사용할 분석 엔진 ("irt", "mixed_effects", "hybrid")
        
    min_responses_for_mixed : int
        혼합효과 모형 사용을 위한 최소 응답 수 (hybrid 모드용)
        
    scale_A : float
        척도 점수 변환 계수 A (scaled_score = A * theta + B)
        
    scale_B : float
        척도 점수 변환 계수 B
    """
    
    def __init__(
        self,
        engine: str = "hybrid",
        min_responses_for_mixed: int = 50,
        scale_A: float = 100.0,
        scale_B: float = 500.0,
        prior_mean: float = 0.0,
        prior_var: float = 1.0,
        use_bayesian_forecast: bool = True,
    ):
        self.engine = AnalysisEngine(engine)
        self.min_responses_for_mixed = min_responses_for_mixed
        self.scale_A = scale_A
        self.scale_B = scale_B
        self.prior_mean = prior_mean
        self.prior_var = prior_var
        self.use_bayesian_forecast = use_bayesian_forecast
        
        # 베이지안 성장 예측기 초기화
        if use_bayesian_forecast:
            self.bayesian_predictor = BayesianGrowthPredictor(
                scale_A=scale_A,
                scale_B=scale_B,
            )
        
    def _decide_engine(self, n_responses: int) -> AnalysisEngine:
        """데이터 양에 따라 분석 엔진 결정 (hybrid 모드)"""
        if self.engine == AnalysisEngine.HYBRID:
            if n_responses >= self.min_responses_for_mixed:
                return AnalysisEngine.MIXED_EFFECTS
            else:
                return AnalysisEngine.IRT
        return self.engine
        
    def _estimate_ability_irt(
        self,
        responses: List[Mapping]
    ) -> Tuple[float, float]:
        """IRT 기반 능력 추정
        
        Returns
        -------
        theta : float
        se : float
        """
        if not responses:
            return 0.0, float("inf")
            
        # 응답 데이터 변환
        items = []
        ys = []
        for r in responses:
            items.append({
                "a": float(r.get("a", 1.0)),
                "b": float(r.get("b", 0.0)),
                "c": float(r.get("c", 0.0)),
            })
            ys.append(1 if r.get("correct", False) else 0)
        
        # MLE 또는 EAP
        if len(responses) < 5:
            # 적은 응답: EAP 사용 (shrinkage 효과)
            theta = eap_theta(
                items, ys,
                prior_mean=self.prior_mean,
                prior_sd=math.sqrt(self.prior_var),
            )
        else:
            # 충분한 응답: MLE 사용
            theta = mle_theta_fisher(items, ys)
        
        # SE 계산
        total_info = sum(
            item_information_3pl(theta, it["a"], it["b"], it["c"])
            for it in items
        )
        se = (1.0 / total_info) ** 0.5 if total_info > 1e-12 else float("inf")
        
        return theta, se
        
    def _estimate_ability_mixed_effects(
        self,
        student_id: str,
        responses: List[Mapping],
        all_responses: Optional[List[Mapping]] = None,
    ) -> Tuple[float, float, str]:
        """혼합효과 모형 기반 능력 추정
        
        Parameters
        ----------
        student_id : str
        responses : List[Mapping]
            해당 학생의 응답
        all_responses : Optional[List[Mapping]]
            전체 학생의 응답 (문항 보정용, 없으면 해당 학생만 사용)
            
        Returns
        -------
        theta : float
        se : float
        engine_label : str
        """
        if not responses:
            return 0.0, float("inf"), "mixed_effects"
            
        # 전체 데이터가 없으면 IRT로 fallback
        if all_responses is None or len(all_responses) < self.min_responses_for_mixed:
            theta, se = self._estimate_ability_irt(responses)
            return theta, se, "irt_fallback"
        
        # 혼합효과 모형 적용
        try:
            abilities, difficulties = fit_mixed_effects(
                all_responses,
                prior_mean=self.prior_mean,
                prior_var=self.prior_var,
            )
            
            if student_id in abilities:
                ability = abilities[student_id]
                return ability.theta, ability.se, "mixed_effects"
            else:
                # 해당 학생이 결과에 없으면 IRT fallback
                theta, se = self._estimate_ability_irt(responses)
                return theta, se, "irt_fallback"
                
        except Exception as e:
            # 혼합효과 모형 실패 시 IRT fallback
            print(f"Mixed effects failed: {e}, falling back to IRT")
            theta, se = self._estimate_ability_irt(responses)
            return theta, se, "irt_fallback"
        
    def _analyze_topics(
        self,
        responses: List[Mapping],
        theta: float,
    ) -> List[TopicInsight]:
        """토픽별 강약점 분석"""
        topic_data: Dict[str, Dict[str, Any]] = {}
        
        for r in responses:
            topic = r.get("topic", "기타")
            if topic not in topic_data:
                topic_data[topic] = {
                    "n_items": 0,
                    "n_correct": 0,
                    "difficulties": [],
                }
            
            topic_data[topic]["n_items"] += 1
            if r.get("correct", False):
                topic_data[topic]["n_correct"] += 1
            topic_data[topic]["difficulties"].append(r.get("b", 0.0))
        
        # TopicInsight 생성
        insights: List[TopicInsight] = []
        for topic, data in topic_data.items():
            accuracy = data["n_correct"] / data["n_items"] if data["n_items"] > 0 else 0.0
            avg_diff = sum(data["difficulties"]) / len(data["difficulties"]) if data["difficulties"] else 0.0
            
            # 강약점 판단
            if accuracy >= 0.8:
                strength = "strong"
            elif accuracy >= 0.6:
                strength = "medium"
            else:
                strength = "weak"
            
            insights.append(TopicInsight(
                topic=topic,
                n_items=data["n_items"],
                n_correct=data["n_correct"],
                accuracy=accuracy,
                avg_difficulty=avg_diff,
                strength_level=strength,
            ))
        
        # 정확도 순으로 정렬 (약한 것부터)
        insights.sort(key=lambda x: x.accuracy)
        
        return insights
        
    def _generate_recommendations(
        self,
        topic_insights: List[TopicInsight],
        theta: float,
    ) -> List[Recommendation]:
        """맞춤형 학습 추천 생성"""
        recommendations: List[Recommendation] = []
        
        for insight in topic_insights:
            if insight.strength_level == "weak":
                # 약점 토픽: 개념 복습 + 연습
                recommendations.append(Recommendation(
                    type="concept",
                    topic=insight.topic,
                    message=f"'{insight.topic}' 토픽의 기본 개념을 복습하세요. (정답률 {insight.accuracy:.0%})",
                    priority=1,
                ))
                recommendations.append(Recommendation(
                    type="practice",
                    topic=insight.topic,
                    message=f"'{insight.topic}' 관련 연습 문제를 풀어보세요.",
                    priority=2,
                ))
            elif insight.strength_level == "medium":
                # 중간 토픽: 연습 강화
                recommendations.append(Recommendation(
                    type="practice",
                    topic=insight.topic,
                    message=f"'{insight.topic}' 토픽을 더 연습하여 정확도를 높이세요. (현재 {insight.accuracy:.0%})",
                    priority=3,
                ))
            else:
                # 강점 토픽: 심화 학습
                if theta > 0:  # 능력이 평균 이상일 때만
                    recommendations.append(Recommendation(
                        type="challenge",
                        topic=insight.topic,
                        message=f"'{insight.topic}' 토픽의 심화 문제에 도전해보세요!",
                        priority=4,
                    ))
        
        # 우선순위 순으로 정렬
        recommendations.sort(key=lambda x: x.priority)
        
        # 상위 5개만 반환
        return recommendations[:5]
        
    def _forecast_growth(
        self,
        current_theta: float,
        theta_se: float,
        responses: List[Mapping],
        n_steps: int = 5,
        target_score: Optional[int] = None,
    ) -> GrowthForecast:
        """성적 성장 예측
        
        베이지안 접근법 또는 간단한 선형 예측 사용
        """
        current_score = int(round(self.scale_A * current_theta + self.scale_B))
        
        # 현재 정답률 기반 학습 효과 추정
        n_correct = sum(1 for r in responses if r.get("correct", False))
        accuracy = n_correct / len(responses) if responses else 0.5
        
        # 베이지안 예측 사용
        if self.use_bayesian_forecast and hasattr(self, 'bayesian_predictor'):
            # 목표 점수 설정 (기본값: 현재 점수 + 100)
            if target_score is None:
                target_score = current_score + 100
            
            # 베이지안 성장 예측
            bayesian_result = self.bayesian_predictor.predict_growth(
                current_theta=current_theta,
                theta_se=theta_se,
                current_accuracy=accuracy,
                n_responses=len(responses),
                target_score=target_score,
                n_forecast_steps=n_steps,
            )
            
            # GrowthForecast 형식으로 변환
            return GrowthForecast(
                current_score=current_score,
                forecast_steps=bayesian_result.forecast_steps,
                confidence_level=bayesian_result.success_probability,
                assumptions=[
                    f"목표 점수 {target_score}점 도달 확률: {bayesian_result.success_probability:.1%}",
                    f"예상 도달 시점: {bayesian_result.expected_trials:.1f}회차",
                    f"최종 예상 점수 범위: {int(bayesian_result.confidence_interval[0])}~{int(bayesian_result.confidence_interval[1])}점",
                    "베이지안 몬테카를로 시뮬레이션 기반 (1000회)",
                    "정기적인 학습을 지속한다고 가정",
                ],
            )
        
        # 기존 간단한 예측 (fallback)
        learning_rate = 0.05 * (1.0 - accuracy)
        
        forecast_steps = []
        theta_pred = current_theta
        for step in range(1, n_steps + 1):
            theta_pred += learning_rate * math.exp(-0.2 * step)
            score_pred = int(round(self.scale_A * theta_pred + self.scale_B))
            forecast_steps.append({
                "step": step,
                "theta": round(theta_pred, 3),
                "score": score_pred,
            })
        
        return GrowthForecast(
            current_score=current_score,
            forecast_steps=forecast_steps,
            confidence_level=0.7,
            assumptions=[
                "정기적인 학습을 지속한다고 가정",
                "약점 토픽을 집중 보완한다고 가정",
                "실제 결과는 학습량과 방법에 따라 달라질 수 있음",
            ],
        )
        
    def _compute_benchmark(
        self,
        theta: float,
    ) -> Benchmark:
        """비교 기준 계산 (정규분포 가정)"""
        # 표준 정규분포에서의 백분위
        percentile = 0.5 * (1.0 + math.erf(theta / math.sqrt(2.0)))
        
        # 순위 설명
        if percentile >= 0.9:
            rank_desc = "상위 10%"
            next_goal = "최상위권 진입을 위해 심화 학습을 계속하세요!"
        elif percentile >= 0.75:
            rank_desc = "상위 25%"
            next_goal = "상위 10% 진입을 목표로 약점을 보완하세요."
        elif percentile >= 0.5:
            rank_desc = "상위 50%"
            next_goal = "상위 25% 진입을 위해 핵심 개념을 강화하세요."
        elif percentile >= 0.25:
            rank_desc = "상위 75%"
            next_goal = "평균 이상을 목표로 기본 개념을 다지세요."
        else:
            rank_desc = "하위 25%"
            next_goal = "기본 개념 학습에 집중하세요."
        
        return Benchmark(
            percentile=percentile,
            rank_description=rank_desc,
            cohort_size=None,  # 실제 코호트 데이터 필요
            next_goal=next_goal,
        )
        
    def generate_report(
        self,
        student_id: str,
        session_id: str,
        responses: List[Mapping],
        all_responses: Optional[List[Mapping]] = None,
        include_forecast: bool = True,
        include_benchmark: bool = True,
    ) -> ScoreAnalysisReport:
        """종합 성적 분석 리포트 생성
        
        Parameters
        ----------
        student_id : str
            학생 ID
            
        session_id : str
            세션 ID
            
        responses : List[Mapping]
            학생의 응답 데이터
            각 항목은 다음 키를 포함:
            - item_id: 문항 ID
            - correct: 정답 여부
            - a, b, c: IRT 파라미터
            - topic: 토픽 (선택)
            
        all_responses : Optional[List[Mapping]]
            전체 학생의 응답 데이터 (혼합효과 모형용)
            
        include_forecast : bool
            성장 예측 포함 여부
            
        include_benchmark : bool
            비교 기준 포함 여부
            
        Returns
        -------
        ScoreAnalysisReport
            종합 성적 분석 리포트
        """
        if not responses:
            raise ValueError("No responses provided")
        
        # 분석 엔진 결정
        n_responses = len(responses)
        engine = self._decide_engine(n_responses)
        
        # 능력 추정
        if engine == AnalysisEngine.MIXED_EFFECTS:
            theta, se, engine_label = self._estimate_ability_mixed_effects(
                student_id, responses, all_responses
            )
        else:
            theta, se = self._estimate_ability_irt(responses)
            engine_label = "irt"
        
        # 척도 점수
        scaled_score = int(round(self.scale_A * theta + self.scale_B))
        
        # 토픽별 분석
        topic_insights = self._analyze_topics(responses, theta)
        
        # 추천 생성
        recommendations = self._generate_recommendations(topic_insights, theta)
        
        # 성장 예측
        growth_forecast = None
        if include_forecast:
            growth_forecast = self._forecast_growth(theta, se, responses)
        
        # 비교 기준
        benchmark = None
        if include_benchmark:
            benchmark = self._compute_benchmark(theta)
        
        # 전체 정확도
        n_correct = sum(1 for r in responses if r.get("correct", False))
        overall_accuracy = n_correct / n_responses
        
        return ScoreAnalysisReport(
            student_id=student_id,
            session_id=session_id,
            theta=theta,
            theta_se=se,
            scaled_score=scaled_score,
            engine_used=engine_label,
            topic_insights=topic_insights,
            recommendations=recommendations,
            growth_forecast=growth_forecast,
            benchmark=benchmark,
            n_items=n_responses,
            n_correct=n_correct,
            overall_accuracy=overall_accuracy,
        )


__all__ = [
    "ScoreAnalysisService",
    "ScoreAnalysisReport",
    "TopicInsight",
    "Recommendation",
    "GrowthForecast",
    "Benchmark",
    "AnalysisEngine",
]

