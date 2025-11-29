"""Mixed-Effects Model for fair ability estimation.

혼합효과 모형(Mixed-Effects Model)을 통한 공정한 능력 추정
==========================================================

이 모듈은 학생 개인차(랜덤 효과)와 문항 난이도(고정/랜덤 효과)를 동시에 고려하여
편향을 보정하고 공정한 능력 추정을 수행합니다.

핵심 개념
--------
1. 학생 능력(θ_i): 각 학생의 고유한 능력 (랜덤 효과)
2. 문항 난이도(b_j): 각 문항의 난이도 (고정/랜덤 효과)
3. 상호 보정: 모든 학생이 어려워한 문항은 난이도↑, 모든 문항을 잘 푸는 학생은 능력↑

모델 정의
--------
혼합효과 로지스틱 회귀:
    logit(P(Y_ij = 1)) = a_j(θ_i - b_j) + c_j

    where:
    - Y_ij: 학생 i가 문항 j에 대한 응답 (1=정답, 0=오답)
    - θ_i: 학생 i의 능력 (랜덤 효과, θ_i ~ N(μ_θ, σ_θ²))
    - b_j: 문항 j의 난이도 (고정 효과 또는 랜덤 효과)
    - a_j: 문항 j의 변별력 (고정 효과)
    - c_j: 문항 j의 추측도 (고정 효과)

장점
----
1. 공정성: 시험 난이도 편차를 보정하여 학생 능력을 공정하게 측정
2. 정확성: IRT만 사용할 때보다 더 정확한 능력 추정
3. 해석성: 학생 능력과 문항 난이도를 명확히 분리

사용 시나리오
-----------
- 초기 단계: 데이터 부족 시 IRT 사용 (shared.irt 모듈)
- 중기 단계: 데이터 축적 후 혼합효과 모형으로 전환
- 고급 단계: 베이지안 혼합효과 모형으로 확장 (PyMC3/PyMC)

구현 전략
--------
1. Phase 1 (현재): 간단한 반복 알고리즘으로 θ_i와 b_j 추정
   - EM-like 접근: θ 고정 → b 추정 → b 고정 → θ 추정 반복

2. Phase 2 (향후): statsmodels의 MixedLM 사용
   - 더 정교한 분산 구조 추정

3. Phase 3 (향후): 베이지안 접근 (PyMC)
   - 불확실성 정량화 강화
   - 계층적 prior 설정

References
----------
- Pinheiro & Bates (2000). Mixed-Effects Models in S and S-PLUS
- De Boeck et al. (2011). The estimation of item response models with the lmer function
- van der Linden (2016). Handbook of Item Response Theory, Volume 1
"""

from __future__ import annotations

import math
import warnings
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

# IRT 기본 함수 임포트
from .irt import irf_3pl, item_information_3pl

_EPS = 1e-12


# ==============================================================================
# Data Structures
# ==============================================================================


class StudentAbility:
    """학생 능력 추정 결과"""

    def __init__(
        self,
        student_id: str,
        theta: float,
        se: float,
        n_responses: int,
        method: str = "mixed_effects",
    ):
        self.student_id = student_id
        self.theta = theta  # 능력 추정치
        self.se = se  # 표준오차
        self.n_responses = n_responses  # 응답 수
        self.method = method  # 추정 방법

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "theta": self.theta,
            "se": self.se,
            "n_responses": self.n_responses,
            "method": self.method,
        }

    def __repr__(self) -> str:
        return f"StudentAbility(id={self.student_id}, θ={self.theta:.3f}, SE={self.se:.3f})"


class ItemDifficulty:
    """문항 난이도 추정 결과"""

    def __init__(
        self,
        item_id: str,
        b: float,
        se: float,
        n_responses: int,
        a: Optional[float] = None,
        c: Optional[float] = None,
    ):
        self.item_id = item_id
        self.b = b  # 난이도 추정치
        self.se = se  # 표준오차
        self.n_responses = n_responses  # 응답 수
        self.a = a  # 변별력 (선택적)
        self.c = c  # 추측도 (선택적)

    def to_dict(self) -> dict:
        result = {
            "item_id": self.item_id,
            "b": self.b,
            "se": self.se,
            "n_responses": self.n_responses,
        }
        if self.a is not None:
            result["a"] = self.a
        if self.c is not None:
            result["c"] = self.c
        return result

    def __repr__(self) -> str:
        return f"ItemDifficulty(id={self.item_id}, b={self.b:.3f}, SE={self.se:.3f})"


class ResponseData:
    """응답 데이터 구조"""

    def __init__(
        self,
        student_id: str,
        item_id: str,
        correct: bool,
        a: float = 1.0,
        b: float = 0.0,
        c: float = 0.0,
    ):
        self.student_id = student_id
        self.item_id = item_id
        self.correct = correct
        self.a = a  # 문항 변별력
        self.b = b  # 문항 난이도 (초기값)
        self.c = c  # 추측도

    @classmethod
    def from_dict(cls, data: Mapping) -> ResponseData:
        return cls(
            student_id=str(data["student_id"]),
            item_id=str(data["item_id"]),
            correct=bool(data.get("correct", False)),
            a=float(data.get("a", 1.0)),
            b=float(data.get("b", 0.0)),
            c=float(data.get("c", 0.0)),
        )


# ==============================================================================
# Mixed-Effects Estimation (EM-like Iterative Algorithm)
# ==============================================================================


def _estimate_theta_given_items(
    responses: List[ResponseData],
    item_difficulties: Dict[str, float],
    prior_mean: float = 0.0,
    prior_var: float = 1.0,
    max_iter: int = 10,
    tol: float = 1e-3,
) -> float:
    """
    문항 난이도가 주어졌을 때 학생 능력(θ) 추정 (MAP 방식)

    Uses Newton-Raphson with Gaussian prior N(prior_mean, prior_var)
    """
    if not responses:
        return prior_mean

    theta = prior_mean

    for iteration in range(max_iter):
        score = 0.0  # First derivative of log-posterior
        info = 0.0  # Second derivative (Fisher information)

        for resp in responses:
            # 업데이트된 난이도 사용
            b_updated = item_difficulties.get(resp.item_id, resp.b)

            # IRT 확률 계산
            P = irf_3pl(theta, resp.a, b_updated, resp.c)
            P = max(min(P, 1.0 - _EPS), _EPS)

            # Score 계산
            y = 1 if resp.correct else 0
            denom_p = 1.0 - resp.c
            if denom_p < _EPS:
                continue

            dP_dtheta = resp.a * (P - resp.c) * (1.0 - P) / denom_p
            score += (y - P) * dP_dtheta / (P * (1.0 - P))

            # Information 계산
            info += item_information_3pl(theta, resp.a, b_updated, resp.c)

        # Prior 기여분 추가
        if prior_var > _EPS:
            score -= (theta - prior_mean) / prior_var
            info += 1.0 / prior_var

        # Newton-Raphson 업데이트
        if info < _EPS:
            break

        delta = score / info
        theta_new = theta + delta

        # Convergence check
        if abs(delta) < tol:
            theta = theta_new
            break

        theta = theta_new

    # Clip to reasonable range
    return max(min(theta, 4.0), -4.0)


def _estimate_difficulty_given_thetas(
    item_id: str,
    responses: List[ResponseData],
    student_abilities: Dict[str, float],
    max_iter: int = 10,
    tol: float = 1e-3,
) -> float:
    """
    학생 능력이 주어졌을 때 문항 난이도(b) 추정

    Uses Newton-Raphson to maximize likelihood
    """
    if not responses:
        return 0.0

    # 초기값: 현재 난이도의 평균
    b = sum(r.b for r in responses) / len(responses) if responses else 0.0

    for iteration in range(max_iter):
        score = 0.0  # First derivative
        info = 0.0  # Second derivative (observed information)

        for resp in responses:
            theta = student_abilities.get(resp.student_id, 0.0)

            # IRT 확률 계산
            P = irf_3pl(theta, resp.a, b, resp.c)
            P = max(min(P, 1.0 - _EPS), _EPS)

            # Score 계산 (∂logL/∂b)
            y = 1 if resp.correct else 0
            denom_p = 1.0 - resp.c
            if denom_p < _EPS:
                continue

            # dP/db = -a * (P - c) * (1 - P) / (1 - c)
            dP_db = -resp.a * (P - resp.c) * (1.0 - P) / denom_p
            score += (y - P) * dP_db / (P * (1.0 - P))

            # 근사적 observed information
            info += resp.a * resp.a * ((P - resp.c) / denom_p) ** 2 * (1.0 - P) / P

        # Newton-Raphson 업데이트
        if info < _EPS:
            break

        delta = score / info
        b_new = b + delta

        # Convergence check
        if abs(delta) < tol:
            b = b_new
            break

        b = b_new

    # Clip to reasonable range
    return max(min(b, 4.0), -4.0)


def fit_mixed_effects(
    responses: Sequence[Mapping],
    prior_mean: float = 0.0,
    prior_var: float = 1.0,
    max_em_iter: int = 20,
    em_tol: float = 1e-4,
    verbose: bool = False,
) -> Tuple[Dict[str, StudentAbility], Dict[str, ItemDifficulty]]:
    """
    혼합효과 모형을 사용하여 학생 능력과 문항 난이도를 동시에 추정

    EM-like alternating optimization:
    1. 문항 난이도를 고정하고 학생 능력 추정
    2. 학생 능력을 고정하고 문항 난이도 추정
    3. 수렴할 때까지 반복

    Parameters
    ----------
    responses : Sequence[Mapping]
        응답 데이터 리스트. 각 항목은 다음 키를 포함:
        - student_id: 학생 ID
        - item_id: 문항 ID
        - correct: 정답 여부 (bool)
        - a: 변별력 (선택, 기본값 1.0)
        - b: 초기 난이도 (선택, 기본값 0.0)
        - c: 추측도 (선택, 기본값 0.0)

    prior_mean : float
        학생 능력의 사전 평균 (기본값 0.0)

    prior_var : float
        학생 능력의 사전 분산 (기본값 1.0)

    max_em_iter : int
        EM 알고리즘의 최대 반복 횟수

    em_tol : float
        수렴 판단 기준 (난이도 변화량)

    verbose : bool
        진행 상황 출력 여부

    Returns
    -------
    student_abilities : Dict[str, StudentAbility]
        학생별 능력 추정 결과

    item_difficulties : Dict[str, ItemDifficulty]
        문항별 난이도 추정 결과

    Examples
    --------
    >>> responses = [
    ...     {"student_id": "s1", "item_id": "q1", "correct": True, "a": 1.2, "b": 0.5, "c": 0.2},
    ...     {"student_id": "s1", "item_id": "q2", "correct": False, "a": 1.0, "b": -0.5, "c": 0.2},
    ...     {"student_id": "s2", "item_id": "q1", "correct": True, "a": 1.2, "b": 0.5, "c": 0.2},
    ...     {"student_id": "s2", "item_id": "q2", "correct": True, "a": 1.0, "b": -0.5, "c": 0.2},
    ... ]
    >>> abilities, difficulties = fit_mixed_effects(responses)
    >>> print(abilities["s1"])
    StudentAbility(id=s1, θ=..., SE=...)
    """

    # 응답 데이터 변환
    resp_list = [ResponseData.from_dict(r) for r in responses]

    if not resp_list:
        warnings.warn("No responses provided, returning empty results")
        return {}, {}

    # 학생별, 문항별 그룹화
    student_responses: Dict[str, List[ResponseData]] = {}
    item_responses: Dict[str, List[ResponseData]] = {}

    for resp in resp_list:
        student_responses.setdefault(resp.student_id, []).append(resp)
        item_responses.setdefault(resp.item_id, []).append(resp)

    # 초기 난이도: 각 문항의 정답률 기반 logit 변환
    item_difficulties: Dict[str, float] = {}
    for item_id, resps in item_responses.items():
        n_correct = sum(1 for r in resps if r.correct)
        p_correct = n_correct / len(resps) if resps else 0.5
        # Prevent extreme values
        p_correct = max(min(p_correct, 0.99), 0.01)
        # b ≈ -logit(p) for rough initialization
        item_difficulties[item_id] = -math.log(p_correct / (1.0 - p_correct))

    # 초기 학생 능력: prior mean
    student_thetas: Dict[str, float] = {
        sid: prior_mean for sid in student_responses.keys()
    }

    # EM-like iteration
    for em_iter in range(max_em_iter):
        # E-step: 현재 난이도를 고정하고 학생 능력 추정
        new_thetas: Dict[str, float] = {}
        for student_id, resps in student_responses.items():
            theta = _estimate_theta_given_items(
                resps, item_difficulties, prior_mean, prior_var
            )
            new_thetas[student_id] = theta

        student_thetas = new_thetas

        # M-step: 현재 학생 능력을 고정하고 문항 난이도 추정
        new_difficulties: Dict[str, float] = {}
        for item_id, resps in item_responses.items():
            b = _estimate_difficulty_given_thetas(item_id, resps, student_thetas)
            new_difficulties[item_id] = b

        # Convergence check
        max_diff = max(
            abs(new_difficulties[iid] - item_difficulties[iid])
            for iid in item_difficulties.keys()
        )

        if verbose:
            print(f"EM iteration {em_iter + 1}/{max_em_iter}: max_diff={max_diff:.6f}")

        item_difficulties = new_difficulties

        if max_diff < em_tol:
            if verbose:
                print(f"Converged at iteration {em_iter + 1}")
            break

    # 최종 결과 포장
    # 각 학생의 SE 계산
    student_ability_results: Dict[str, StudentAbility] = {}
    for student_id, resps in student_responses.items():
        theta = student_thetas[student_id]

        # Fisher information 계산
        total_info = 0.0
        for resp in resps:
            b_final = item_difficulties[resp.item_id]
            total_info += item_information_3pl(theta, resp.a, b_final, resp.c)

        se = (1.0 / total_info) ** 0.5 if total_info > _EPS else float("inf")

        student_ability_results[student_id] = StudentAbility(
            student_id=student_id,
            theta=theta,
            se=se,
            n_responses=len(resps),
            method="mixed_effects",
        )

    # 각 문항의 SE 계산 (근사)
    item_difficulty_results: Dict[str, ItemDifficulty] = {}
    for item_id, resps in item_responses.items():
        b_final = item_difficulties[item_id]

        # 평균 변별력
        avg_a = sum(r.a for r in resps) / len(resps) if resps else 1.0
        avg_c = sum(r.c for r in resps) / len(resps) if resps else 0.0

        # Approximate SE for difficulty
        # Using average information across student abilities
        total_info = 0.0
        for resp in resps:
            theta = student_thetas[resp.student_id]
            # Information about b is approximately a^2 * variance term
            P = irf_3pl(theta, resp.a, b_final, resp.c)
            P = max(min(P, 1.0 - _EPS), _EPS)
            denom = 1.0 - resp.c
            if denom > _EPS:
                total_info += (resp.a**2) * ((P - resp.c) / denom) ** 2 * (1.0 - P) / P

        se = (1.0 / total_info) ** 0.5 if total_info > _EPS else float("inf")

        item_difficulty_results[item_id] = ItemDifficulty(
            item_id=item_id,
            b=b_final,
            se=se,
            n_responses=len(resps),
            a=avg_a,
            c=avg_c,
        )

    return student_ability_results, item_difficulty_results


# ==============================================================================
# Utility Functions
# ==============================================================================


def estimate_single_student_with_calibrated_items(
    student_responses: Sequence[Mapping],
    calibrated_items: Dict[str, ItemDifficulty],
    prior_mean: float = 0.0,
    prior_var: float = 1.0,
) -> StudentAbility:
    """
    이미 보정된 문항 난이도를 사용하여 단일 학생의 능력 추정

    이 함수는 많은 데이터를 통해 사전에 문항 난이도를 추정한 후,
    새로운 학생의 능력을 추정할 때 사용합니다.

    Parameters
    ----------
    student_responses : Sequence[Mapping]
        학생의 응답 데이터

    calibrated_items : Dict[str, ItemDifficulty]
        사전 보정된 문항 난이도 정보

    prior_mean, prior_var : float
        학생 능력의 사전 분포

    Returns
    -------
    StudentAbility
        추정된 학생 능력
    """
    resp_list = [ResponseData.from_dict(r) for r in student_responses]

    if not resp_list:
        return StudentAbility(
            student_id="unknown",
            theta=prior_mean,
            se=float("inf"),
            n_responses=0,
            method="mixed_effects",
        )

    # 보정된 난이도로 업데이트
    item_difficulties: Dict[str, float] = {}
    for resp in resp_list:
        if resp.item_id in calibrated_items:
            item_difficulties[resp.item_id] = calibrated_items[resp.item_id].b
        else:
            # Calibrated item not found, use default
            item_difficulties[resp.item_id] = resp.b

    # 능력 추정
    theta = _estimate_theta_given_items(
        resp_list, item_difficulties, prior_mean, prior_var
    )

    # SE 계산
    total_info = 0.0
    for resp in resp_list:
        b_calibrated = item_difficulties[resp.item_id]
        total_info += item_information_3pl(theta, resp.a, b_calibrated, resp.c)

    se = (1.0 / total_info) ** 0.5 if total_info > _EPS else float("inf")

    student_id = resp_list[0].student_id if resp_list else "unknown"

    return StudentAbility(
        student_id=student_id,
        theta=theta,
        se=se,
        n_responses=len(resp_list),
        method="mixed_effects",
    )


__all__ = [
    "StudentAbility",
    "ItemDifficulty",
    "ResponseData",
    "fit_mixed_effects",
    "estimate_single_student_with_calibrated_items",
]
