"""
score_utils.py

DreamSeedAI – Theta → Score/Grade Conversion Utilities

이 모듈은 IRT 능력치(theta)를 사람/서비스가 이해하기 쉬운
점수/등급 스케일로 변환하는 유틸 함수들을 제공합니다.

주요 기능:
 - theta → 0~100 점수 (선형 스케일)
 - theta → 표준점수 (mean/sd 기반 T-score 스타일)
 - theta → 퍼센타일 (정규분포 근사)
 - theta → 등급(예: 1~9등급, A/B/C 등) 매핑

주의:
 - 실제 입시/내신 시스템과의 매핑은 각 도메인에 맞게
   cut-off 값을 조정해야 합니다.
 - 여기서는 일반적인 기본값/예시만 제공합니다.

Usage:
    from app.services.score_utils import summarize_theta
    
    summary = summarize_theta(theta=0.45)
    print(summary)
    # {
    #   "theta": 0.45,
    #   "score_0_100": 74.5,
    #   "t_score": 54.5,
    #   "percentile": 67.0,
    #   "grade_numeric": 3,
    #   "grade_letter": "B"
    # }
"""

from __future__ import annotations
from typing import Dict, Tuple
import math


# ---------------------------------------------------------------------------
# 1. Theta → 0~100 점수 (선형 스케일)
# ---------------------------------------------------------------------------

def theta_to_0_100(
    theta: float,
    min_theta: float = -3.0,
    max_theta: float = 3.0
) -> float:
    """
    Theta를 0~100 점수로 선형 변환.
    
    - min_theta 에서 0점, max_theta 에서 100점이 되도록 스케일링합니다.
    - 범위를 벗어나면 0~100 사이로 클램핑합니다.
    
    Args:
        theta: IRT ability estimate (능력치)
        min_theta: 0점에 해당하는 theta 값 (default: -3.0)
        max_theta: 100점에 해당하는 theta 값 (default: 3.0)
    
    Returns:
        float: 0~100 사이의 점수
    
    Example:
        >>> theta_to_0_100(0.0)
        50.0
        >>> theta_to_0_100(1.5)
        75.0
        >>> theta_to_0_100(-3.0)
        0.0
        >>> theta_to_0_100(3.0)
        100.0
    """
    if max_theta <= min_theta:
        raise ValueError("max_theta must be greater than min_theta")

    # 선형 스케일링
    score = (theta - min_theta) / (max_theta - min_theta) * 100.0
    
    # 클램핑 (0~100 범위 보장)
    return max(0.0, min(100.0, score))


# ---------------------------------------------------------------------------
# 2. Theta → 표준점수 (T-score 스타일)
# ---------------------------------------------------------------------------

def theta_to_t_score(
    theta: float,
    mean: float = 50.0,
    sd: float = 10.0,
) -> float:
    """
    Theta를 T-score 스타일 표준점수로 변환.
    
    - 보통 theta ~ N(0,1)을 가정하면 T = 50 + 10 * theta 형태가 됩니다.
    - mean, sd 파라미터로 다양한 스케일에 맞출 수 있습니다.
    
    Args:
        theta: IRT ability estimate
        mean: 표준점수의 평균 (default: 50.0)
        sd: 표준점수의 표준편차 (default: 10.0)
    
    Returns:
        float: 표준점수 (T-score)
    
    Example:
        >>> theta_to_t_score(0.0)
        50.0
        >>> theta_to_t_score(1.0)
        60.0
        >>> theta_to_t_score(-1.0)
        40.0
        >>> theta_to_t_score(2.0)
        70.0
    """
    return mean + sd * theta


# ---------------------------------------------------------------------------
# 3. Theta → 퍼센타일 (정규분포 근사)
# ---------------------------------------------------------------------------

def _normal_cdf(x: float) -> float:
    """
    표준정규분포 CDF 근사 (math.erf 사용).
    
    Φ(x) = 0.5 * (1 + erf(x / sqrt(2)))
    
    Args:
        x: 표준정규분포 값
    
    Returns:
        float: 누적확률 (0~1)
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def theta_to_percentile(theta: float) -> float:
    """
    Theta를 퍼센타일(0~100)로 근사 변환.
    
    - theta가 표준정규분포 N(0,1)을 따른다고 가정.
    - Φ(theta) * 100 으로 계산.
    
    Args:
        theta: IRT ability estimate
    
    Returns:
        float: 퍼센타일 (0~100)
    
    Example:
        >>> theta_to_percentile(0.0)
        50.0
        >>> theta_to_percentile(1.0)
        84.13...
        >>> theta_to_percentile(-1.0)
        15.86...
        >>> theta_to_percentile(2.0)
        97.72...
    """
    return _normal_cdf(theta) * 100.0


# ---------------------------------------------------------------------------
# 4. Theta → 등급 매핑 (1~N 등급, 또는 A/B/C 등)
# ---------------------------------------------------------------------------

def theta_to_grade_numeric(
    theta: float,
    cutoffs: Tuple[float, ...] = (
        1.0,   # 1등급 기준
        0.5,   # 2등급 기준
        0.0,   # 3등급 기준
        -0.5,  # 4등급 기준
        -1.0,  # 5등급 기준
        -1.5,  # 6등급 기준
        -2.0,  # 7등급 기준
        -2.5,  # 8등급 기준
        # 나머지는 9등급
    ),
) -> int:
    """
    Theta를 1~9 등급 같은 **숫자 등급**으로 변환.
    
    cutoffs는 높은 등급부터 내림차순으로 기준 theta를 나열합니다.
    
    예: (1.0, 0.5, 0.0, -0.5, ...) →
      - theta >= 1.0   → 1등급
      - theta >= 0.5   → 2등급
      - theta >= 0.0   → 3등급
      - ...
      - theta < 마지막 cutoffs → 마지막+1 등급
    
    기본값은 대략적인 예시로, 실제 수능/내신 기준은 도메인별로 조정 필요.
    
    Args:
        theta: IRT ability estimate
        cutoffs: 등급 기준 theta 값들 (내림차순)
    
    Returns:
        int: 등급 번호 (1부터 시작)
    
    Example:
        >>> theta_to_grade_numeric(1.2)
        1
        >>> theta_to_grade_numeric(0.7)
        2
        >>> theta_to_grade_numeric(0.0)
        3
        >>> theta_to_grade_numeric(-3.0)
        9
    """
    for i, threshold in enumerate(cutoffs, start=1):
        if theta >= threshold:
            return i
    
    # cutoffs를 모두 통과 못하면 마지막 등급+1
    return len(cutoffs) + 1


def percentile_to_letter_grade(
    percentile: float,
    bands: Dict[str, Tuple[float, float]] = None,
) -> str:
    """
    퍼센타일 → A/B/C/D/F 등의 **문자 등급**으로 변환.
    
    bands 예시 (기본값):
        {
            "A": (90, 100),
            "B": (75, 90),
            "C": (50, 75),
            "D": (25, 50),
            "F": (0, 25),
        }
    
    Args:
        percentile: 퍼센타일 (0~100)
        bands: 등급별 퍼센타일 범위 (default: A/B/C/D/F)
    
    Returns:
        str: 문자 등급
    
    Example:
        >>> percentile_to_letter_grade(95)
        'A'
        >>> percentile_to_letter_grade(80)
        'B'
        >>> percentile_to_letter_grade(60)
        'C'
        >>> percentile_to_letter_grade(30)
        'D'
        >>> percentile_to_letter_grade(10)
        'F'
    """
    if bands is None:
        bands = {
            "A": (90.0, 100.0),
            "B": (75.0, 90.0),
            "C": (50.0, 75.0),
            "D": (25.0, 50.0),
            "F": (0.0, 25.0),
        }

    for grade, (lo, hi) in bands.items():
        if lo <= percentile < hi:
            return grade
    
    # 범위 밖인 경우 보수적으로 처리
    return "F"


# ---------------------------------------------------------------------------
# 5. 편의 함수: Theta → (점수, 퍼센타일, 등급) 한 번에
# ---------------------------------------------------------------------------

def summarize_theta(
    theta: float,
    min_theta: float = -3.0,
    max_theta: float = 3.0,
) -> Dict[str, float | int | str]:
    """
    Theta 하나로부터 여러 형태의 요약 정보를 반환.
    
    Args:
        theta: IRT ability estimate
        min_theta: 0점에 해당하는 theta (default: -3.0)
        max_theta: 100점에 해당하는 theta (default: 3.0)
    
    Returns:
        Dict with keys:
            - theta: 원본 theta 값
            - score_0_100: 0~100 점수
            - t_score: T-score (평균 50, 표준편차 10)
            - percentile: 퍼센타일 (0~100)
            - grade_numeric: 숫자 등급 (1~9)
            - grade_letter: 문자 등급 (A/B/C/D/F)
    
    Example:
        >>> summary = summarize_theta(0.45)
        >>> summary
        {
            'theta': 0.45,
            'score_0_100': 74.5,
            't_score': 54.5,
            'percentile': 67.36...,
            'grade_numeric': 3,
            'grade_letter': 'C'
        }
    """
    score_0_100 = theta_to_0_100(theta, min_theta=min_theta, max_theta=max_theta)
    t_score = theta_to_t_score(theta)
    percentile = theta_to_percentile(theta)
    grade_numeric = theta_to_grade_numeric(theta)
    grade_letter = percentile_to_letter_grade(percentile)

    return {
        "theta": theta,
        "score_0_100": score_0_100,
        "t_score": t_score,
        "percentile": percentile,
        "grade_numeric": grade_numeric,
        "grade_letter": grade_letter,
    }


# ---------------------------------------------------------------------------
# 6. 역변환 유틸리티 (선택적)
# ---------------------------------------------------------------------------

def score_0_100_to_theta(
    score: float,
    min_theta: float = -3.0,
    max_theta: float = 3.0
) -> float:
    """
    0~100 점수를 theta로 역변환.
    
    Args:
        score: 0~100 사이의 점수
        min_theta: 0점에 해당하는 theta
        max_theta: 100점에 해당하는 theta
    
    Returns:
        float: theta 값
    
    Example:
        >>> score_0_100_to_theta(50.0)
        0.0
        >>> score_0_100_to_theta(75.0)
        1.5
        >>> score_0_100_to_theta(0.0)
        -3.0
    """
    if max_theta <= min_theta:
        raise ValueError("max_theta must be greater than min_theta")
    
    # 클램핑
    score = max(0.0, min(100.0, score))
    
    # 역변환
    theta = min_theta + (score / 100.0) * (max_theta - min_theta)
    return theta


def t_score_to_theta(
    t_score: float,
    mean: float = 50.0,
    sd: float = 10.0
) -> float:
    """
    T-score를 theta로 역변환.
    
    Args:
        t_score: 표준점수
        mean: T-score 평균
        sd: T-score 표준편차
    
    Returns:
        float: theta 값
    
    Example:
        >>> t_score_to_theta(50.0)
        0.0
        >>> t_score_to_theta(60.0)
        1.0
        >>> t_score_to_theta(40.0)
        -1.0
    """
    return (t_score - mean) / sd


# ---------------------------------------------------------------------------
# 7. 배치 변환 유틸리티
# ---------------------------------------------------------------------------

def batch_summarize_theta(
    theta_list: list[float],
    min_theta: float = -3.0,
    max_theta: float = 3.0,
) -> list[Dict[str, float | int | str]]:
    """
    여러 theta 값을 한 번에 요약.
    
    Args:
        theta_list: theta 값들의 리스트
        min_theta: 0점 기준 theta
        max_theta: 100점 기준 theta
    
    Returns:
        list: 각 theta의 요약 정보 딕셔너리 리스트
    
    Example:
        >>> summaries = batch_summarize_theta([0.0, 0.5, 1.0])
        >>> len(summaries)
        3
        >>> summaries[0]['score_0_100']
        50.0
    """
    return [
        summarize_theta(theta, min_theta=min_theta, max_theta=max_theta)
        for theta in theta_list
    ]


# ---------------------------------------------------------------------------
# 8. 한국 교육 시스템 특화 함수 (선택적)
# ---------------------------------------------------------------------------

def theta_to_korean_grade(
    theta: float,
    system: str = "9grade"
) -> int:
    """
    한국 교육 시스템의 등급제로 변환.
    
    Args:
        theta: IRT ability estimate
        system: 등급 시스템 ("9grade" 또는 "5grade")
    
    Returns:
        int: 등급 번호
    
    Example:
        >>> theta_to_korean_grade(1.2, "9grade")
        1
        >>> theta_to_korean_grade(0.0, "5grade")
        3
    """
    if system == "9grade":
        # 수능 9등급제 (상위 4%, 7%, 12%, 17%, 23%, 29%, 40%, 60%, 나머지)
        # 정규분포 기준 theta 커트라인 근사
        cutoffs = (
            1.75,   # 1등급: 상위 4% (z≈1.75)
            1.48,   # 2등급: 상위 11% (4+7)
            1.17,   # 3등급: 상위 23% (4+7+12)
            0.95,   # 4등급: 상위 40%
            0.74,   # 5등급: 상위 60%
            0.52,   # 6등급: 상위 77%
            0.25,   # 7등급: 상위 89%
            -0.25,  # 8등급: 상위 96%
            # 9등급: 나머지
        )
        return theta_to_grade_numeric(theta, cutoffs=cutoffs)
    
    elif system == "5grade":
        # 5등급제 (20% 간격)
        cutoffs = (
            0.84,   # 1등급: 상위 20%
            0.25,   # 2등급: 상위 40%
            -0.25,  # 3등급: 상위 60%
            -0.84,  # 4등급: 상위 80%
            # 5등급: 나머지
        )
        return theta_to_grade_numeric(theta, cutoffs=cutoffs)
    
    else:
        raise ValueError(f"Unknown system: {system}")


def theta_to_sat_score(
    theta: float,
    section: str = "math"
) -> int:
    """
    Theta를 SAT 점수로 변환 (참고용).
    
    Args:
        theta: IRT ability estimate
        section: "math" 또는 "verbal"
    
    Returns:
        int: SAT 점수 (200~800)
    
    Example:
        >>> theta_to_sat_score(0.0)
        500
        >>> theta_to_sat_score(2.0)
        700
    """
    # SAT는 평균 500, 표준편차 100 정도
    # theta ~ N(0,1)을 가정하면 SAT ≈ 500 + 100*theta
    sat_score = 500 + 100 * theta
    
    # 200~800 클램핑
    return int(max(200, min(800, sat_score)))


# ---------------------------------------------------------------------------
# 9. 디버깅/시각화 헬퍼
# ---------------------------------------------------------------------------

def print_theta_summary(theta: float) -> None:
    """
    Theta 요약 정보를 보기 좋게 출력 (디버깅용).
    
    Args:
        theta: IRT ability estimate
    
    Example:
        >>> print_theta_summary(0.45)
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        Theta Summary: θ = 0.450
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        0~100 Score:     74.5
        T-Score:         54.5
        Percentile:      67.4%
        Grade (1~9):     3
        Letter Grade:    C
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    summary = summarize_theta(theta)
    
    print("━" * 42)
    print(f"Theta Summary: θ = {theta:.3f}")
    print("━" * 42)
    print(f"0~100 Score:     {summary['score_0_100']:.1f}")
    print(f"T-Score:         {summary['t_score']:.1f}")
    print(f"Percentile:      {summary['percentile']:.1f}%")
    print(f"Grade (1~9):     {summary['grade_numeric']}")
    print(f"Letter Grade:    {summary['grade_letter']}")
    print("━" * 42)
