"""Bayesian Growth Prediction - 베이지안 성장 예측

베이지안 업데이트를 통한 향후 성적 향상 가능성 예측
=================================================

이 모듈은 다음 기능을 제공합니다:
1. 베이지안 posterior 분포를 활용한 능력치 불확실성 모델링
2. 몬테카를로 시뮬레이션을 통한 미래 성적 예측
3. 목표 점수 도달 확률 계산
4. 신뢰구간을 포함한 성장 시나리오

References
----------
- Bayesian Item Response Theory: van der Linden (2016)
- Growth Prediction: Embretson & Reise (2013)
- Monte Carlo Simulation: Robert & Casella (2004)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class GrowthPrediction:
    """성장 예측 결과"""

    current_theta: float
    current_score: int
    target_score: int
    success_probability: float
    expected_trials: float
    confidence_interval: Tuple[float, float]
    forecast_steps: List[Dict]
    learning_rate_estimate: float

    def to_dict(self) -> dict:
        return {
            "current_theta": self.current_theta,
            "current_score": self.current_score,
            "target_score": self.target_score,
            "success_probability": self.success_probability,
            "expected_trials": self.expected_trials,
            "confidence_interval": {
                "low": self.confidence_interval[0],
                "high": self.confidence_interval[1],
            },
            "forecast_steps": self.forecast_steps,
            "learning_rate_estimate": self.learning_rate_estimate,
        }


@dataclass
class BayesianAbilityDistribution:
    """베이지안 능력 분포"""

    mean: float
    std: float
    posterior_samples: Optional[List[float]] = None

    def sample(self, n: int = 1) -> List[float]:
        """posterior에서 샘플링"""
        if self.posterior_samples and len(self.posterior_samples) >= n:
            return random.sample(self.posterior_samples, n)

        # Normal 분포에서 샘플링
        if HAS_NUMPY:
            return np.random.normal(self.mean, self.std, n).tolist()
        else:
            return [random.gauss(self.mean, self.std) for _ in range(n)]


# ==============================================================================
# Bayesian Growth Prediction
# ==============================================================================


class BayesianGrowthPredictor:
    """베이지안 성장 예측기

    Parameters
    ----------
    scale_A, scale_B : float
        척도 점수 변환 계수 (score = A * theta + B)

    learning_rate_prior : Tuple[float, float]
        학습률의 prior 분포 (mean, std)
        학습률: 시도당 능력 향상 폭

    n_simulations : int
        몬테카를로 시뮬레이션 횟수
    """

    def __init__(
        self,
        scale_A: float = 100.0,
        scale_B: float = 500.0,
        learning_rate_prior: Tuple[float, float] = (0.05, 0.02),
        n_simulations: int = 1000,
    ):
        self.scale_A = scale_A
        self.scale_B = scale_B
        self.learning_rate_mean = learning_rate_prior[0]
        self.learning_rate_std = learning_rate_prior[1]
        self.n_simulations = n_simulations

    def estimate_ability_distribution(
        self,
        theta: float,
        se: float,
        n_responses: int,
    ) -> BayesianAbilityDistribution:
        """능력치의 posterior 분포 추정

        Returns
        -------
        BayesianAbilityDistribution
            평균, 표준편차, posterior 샘플
        """
        # SE를 posterior std로 사용
        posterior_std = se

        # 신뢰도 향상 (응답 수가 많을수록 분산 감소)
        adjustment = math.sqrt(max(10, n_responses) / 10)
        adjusted_std = posterior_std / adjustment

        return BayesianAbilityDistribution(
            mean=theta,
            std=adjusted_std,
        )

    def estimate_learning_rate(
        self,
        current_accuracy: float,
        n_responses: int,
    ) -> Tuple[float, float]:
        """학습률 추정

        현재 정답률과 응답 수를 기반으로 학습률을 추정합니다.
        정답률이 낮을수록 향상 여지가 크므로 학습률이 높습니다.

        Returns
        -------
        (learning_rate_mean, learning_rate_std)
        """
        # 정답률 기반 학습 여지 계산
        # 정답률 50% → 학습률 높음
        # 정답률 90% → 학습률 낮음
        potential = 1.0 - current_accuracy

        # 학습률 조정
        lr_mean = self.learning_rate_mean * (0.5 + potential)
        lr_std = self.learning_rate_std

        # 응답 수가 적으면 불확실성 증가
        if n_responses < 20:
            lr_std *= 1.5

        return lr_mean, lr_std

    def simulate_growth_trajectory(
        self,
        ability_dist: BayesianAbilityDistribution,
        learning_rate_mean: float,
        learning_rate_std: float,
        n_steps: int = 10,
    ) -> List[float]:
        """단일 성장 궤적 시뮬레이션

        Returns
        -------
        List[float]
            각 단계별 능력치
        """
        # 초기 능력치 샘플링
        theta = ability_dist.sample(1)[0]

        # 학습률 샘플링
        lr = max(0.01, random.gauss(learning_rate_mean, learning_rate_std))

        trajectory = [theta]

        for step in range(1, n_steps + 1):
            # 학습 효과 (지수 감소)
            decay = math.exp(-0.1 * step)
            improvement = lr * decay

            # 무작위 변동 추가 (현실적 노이즈)
            noise = random.gauss(0, 0.05)

            # 다음 능력치
            theta_next = theta + improvement + noise

            # 상한/하한 제약
            theta_next = max(min(theta_next, 4.0), -4.0)

            trajectory.append(theta_next)
            theta = theta_next

        return trajectory

    def monte_carlo_forecast(
        self,
        ability_dist: BayesianAbilityDistribution,
        learning_rate_mean: float,
        learning_rate_std: float,
        n_steps: int = 10,
    ) -> Dict:
        """몬테카를로 시뮬레이션으로 성장 예측

        Returns
        -------
        dict
            - mean_trajectory: 평균 궤적
            - percentile_05: 5 percentile
            - percentile_95: 95 percentile
            - all_trajectories: 모든 시뮬레이션 결과
        """
        all_trajectories = []

        for _ in range(self.n_simulations):
            trajectory = self.simulate_growth_trajectory(
                ability_dist,
                learning_rate_mean,
                learning_rate_std,
                n_steps,
            )
            all_trajectories.append(trajectory)

        # 각 단계별 통계 계산
        mean_trajectory = []
        p05_trajectory = []
        p95_trajectory = []

        for step in range(n_steps + 1):
            values = [traj[step] for traj in all_trajectories]

            if HAS_NUMPY:
                mean_trajectory.append(float(np.mean(values)))
                p05_trajectory.append(float(np.percentile(values, 5)))
                p95_trajectory.append(float(np.percentile(values, 95)))
            else:
                values_sorted = sorted(values)
                mean_trajectory.append(sum(values) / len(values))
                p05_trajectory.append(values_sorted[int(len(values) * 0.05)])
                p95_trajectory.append(values_sorted[int(len(values) * 0.95)])

        return {
            "mean_trajectory": mean_trajectory,
            "percentile_05": p05_trajectory,
            "percentile_95": p95_trajectory,
            "all_trajectories": all_trajectories,
        }

    def calculate_target_probability(
        self,
        all_trajectories: List[List[float]],
        target_theta: float,
        max_trials: int = 10,
    ) -> Tuple[float, float]:
        """목표 능력치 도달 확률 계산

        Returns
        -------
        (success_probability, expected_trials)
            - success_probability: max_trials 내 목표 도달 확률
            - expected_trials: 목표 도달까지 예상 시도 횟수
        """
        n_success = 0
        total_trials = 0
        trials_to_success = []

        for trajectory in all_trajectories:
            reached = False
            for step, theta in enumerate(trajectory[1:], 1):  # 0단계 제외
                if theta >= target_theta:
                    n_success += 1
                    trials_to_success.append(step)
                    reached = True
                    break

            if not reached and len(trajectory) > 0:
                # 도달하지 못한 경우
                trials_to_success.append(max_trials + 1)

        success_prob = n_success / len(all_trajectories) if all_trajectories else 0.0

        # 성공한 경우만 고려한 평균 시도 횟수
        if trials_to_success:
            expected = sum(t for t in trials_to_success if t <= max_trials) / max(
                1, n_success
            )
        else:
            expected = float("inf")

        return success_prob, expected

    def predict_growth(
        self,
        current_theta: float,
        theta_se: float,
        current_accuracy: float,
        n_responses: int,
        target_score: int,
        n_forecast_steps: int = 10,
    ) -> GrowthPrediction:
        """종합 성장 예측

        Parameters
        ----------
        current_theta : float
            현재 능력치

        theta_se : float
            능력치 표준오차

        current_accuracy : float
            현재 정답률 (0.0 ~ 1.0)

        n_responses : int
            응답 수

        target_score : int
            목표 척도 점수

        n_forecast_steps : int
            예측 단계 수

        Returns
        -------
        GrowthPrediction
            종합 성장 예측 결과
        """
        # 1. 능력 분포 추정
        ability_dist = self.estimate_ability_distribution(
            current_theta, theta_se, n_responses
        )

        # 2. 학습률 추정
        lr_mean, lr_std = self.estimate_learning_rate(current_accuracy, n_responses)

        # 3. 몬테카를로 시뮬레이션
        mc_result = self.monte_carlo_forecast(
            ability_dist,
            lr_mean,
            lr_std,
            n_forecast_steps,
        )

        # 4. 목표 점수를 theta로 변환
        target_theta = (target_score - self.scale_B) / self.scale_A

        # 5. 목표 도달 확률 계산
        success_prob, expected_trials = self.calculate_target_probability(
            mc_result["all_trajectories"],
            target_theta,
            n_forecast_steps,
        )

        # 6. 예측 단계별 정보 구성
        forecast_steps = []
        for step in range(1, n_forecast_steps + 1):
            mean_theta = mc_result["mean_trajectory"][step]
            p05_theta = mc_result["percentile_05"][step]
            p95_theta = mc_result["percentile_95"][step]

            forecast_steps.append(
                {
                    "step": step,
                    "theta_mean": round(mean_theta, 3),
                    "theta_p05": round(p05_theta, 3),
                    "theta_p95": round(p95_theta, 3),
                    "score_mean": int(round(self.scale_A * mean_theta + self.scale_B)),
                    "score_p05": int(round(self.scale_A * p05_theta + self.scale_B)),
                    "score_p95": int(round(self.scale_A * p95_theta + self.scale_B)),
                }
            )

        # 7. 신뢰구간 (최종 단계)
        final_p05 = mc_result["percentile_05"][-1]
        final_p95 = mc_result["percentile_95"][-1]

        # 8. 현재 점수
        current_score = int(round(self.scale_A * current_theta + self.scale_B))

        return GrowthPrediction(
            current_theta=current_theta,
            current_score=current_score,
            target_score=target_score,
            success_probability=success_prob,
            expected_trials=(
                expected_trials if expected_trials != float("inf") else n_forecast_steps
            ),
            confidence_interval=(
                self.scale_A * final_p05 + self.scale_B,
                self.scale_A * final_p95 + self.scale_B,
            ),
            forecast_steps=forecast_steps,
            learning_rate_estimate=lr_mean,
        )


# ==============================================================================
# Collaborative Filtering (선택적)
# ==============================================================================


class CollaborativeGrowthPredictor:
    """협업 필터링 기반 성장 예측

    유사한 학생들의 과거 향상도를 참고하여 예측합니다.
    """

    def __init__(self):
        self.historical_data: List[Dict] = []

    def add_historical_data(
        self,
        student_id: str,
        initial_theta: float,
        final_theta: float,
        n_trials: int,
        features: Dict,
    ):
        """과거 데이터 추가

        Parameters
        ----------
        student_id : str
        initial_theta : float
            초기 능력치
        final_theta : float
            최종 능력치
        n_trials : int
            시도 횟수
        features : Dict
            학생 특징 (정답률, 토픽 분포 등)
        """
        self.historical_data.append(
            {
                "student_id": student_id,
                "initial_theta": initial_theta,
                "final_theta": final_theta,
                "improvement": final_theta - initial_theta,
                "n_trials": n_trials,
                "improvement_rate": (final_theta - initial_theta) / max(1, n_trials),
                "features": features,
            }
        )

    def find_similar_students(
        self,
        current_theta: float,
        current_accuracy: float,
        top_k: int = 10,
    ) -> List[Dict]:
        """유사한 학생 찾기

        Returns
        -------
        List[Dict]
            유사한 학생들의 데이터
        """
        if not self.historical_data:
            return []

        # 유사도 계산 (간단한 유클리드 거리)
        similarities = []
        for record in self.historical_data:
            theta_diff = abs(record["initial_theta"] - current_theta)
            acc_diff = abs(record["features"].get("accuracy", 0.5) - current_accuracy)

            distance = math.sqrt(theta_diff**2 + acc_diff**2)
            similarities.append((distance, record))

        # 상위 k개 선택
        similarities.sort(key=lambda x: x[0])
        return [record for _, record in similarities[:top_k]]

    def predict_from_similar_students(
        self,
        current_theta: float,
        current_accuracy: float,
    ) -> Tuple[float, float]:
        """유사 학생 기반 예측

        Returns
        -------
        (expected_improvement_rate, std)
        """
        similar = self.find_similar_students(current_theta, current_accuracy)

        if not similar:
            # 기본값 반환
            return 0.05, 0.02

        rates = [s["improvement_rate"] for s in similar]

        if HAS_NUMPY:
            mean_rate = float(np.mean(rates))
            std_rate = float(np.std(rates))
        else:
            mean_rate = sum(rates) / len(rates)
            variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
            std_rate = math.sqrt(variance)

        return mean_rate, std_rate


__all__ = [
    "BayesianGrowthPredictor",
    "GrowthPrediction",
    "BayesianAbilityDistribution",
    "CollaborativeGrowthPredictor",
]
