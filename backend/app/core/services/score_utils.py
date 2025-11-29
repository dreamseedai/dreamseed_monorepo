"""
core/services/score_utils.py

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
"""

from __future__ import annotations
from typing import Dict, Tuple
import math


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Theta → 0~100 점수 (선형 스케일)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
        theta: IRT 능력치 (일반적으로 -3.0 ~ 3.0 범위)
        min_theta: 0점에 매핑될 theta 값 (기본값: -3.0)
        max_theta: 100점에 매핑될 theta 값 (기본값: 3.0)
        
    Returns:
        0~100 사이의 점수
        
    Raises:
        ValueError: max_theta <= min_theta인 경우
        
    Example:
        >>> theta_to_0_100(0.0)
        50.0
        >>> theta_to_0_100(1.5)
        75.0
        >>> theta_to_0_100(-1.5)
        25.0
    """
    if max_theta <= min_theta:
        raise ValueError("max_theta must be greater than min_theta")

    # 선형 스케일링
    score = (theta - min_theta) / (max_theta - min_theta) * 100.0
    # 클램핑
    return max(0.0, min(100.0, score))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Theta → 표준점수 (T-score 스타일)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def theta_to_t_score(
    theta: float,
    mean: float = 50.0,
    sd: float = 10.0,
) -> float:
    """
    Theta를 T-score 스타일 표준점수로 변환.
    
    - 보통 theta ~ N(0,1)을 가정하면 T = 50 + 10 * theta 형태가 됩니다.
    - mean, sd 파라미터로 다양한 스케일에 맞춤 가능합니다.
    
    Args:
        theta: IRT 능력치
        mean: 표준점수의 평균 (기본값: 50.0)
        sd: 표준점수의 표준편차 (기본값: 10.0)
        
    Returns:
        T-score 형태의 표준점수
        
    Example:
        >>> theta_to_t_score(0.0)
        50.0
        >>> theta_to_t_score(1.0)
        60.0
        >>> theta_to_t_score(-2.0)
        30.0
    """
    return mean + sd * theta


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Theta → 퍼센타일 (정규분포 근사)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _normal_cdf(x: float) -> float:
    """
    표준정규분포 CDF 근사 (math.erf 사용).
    
    Φ(x) = 0.5 * (1 + erf(x / sqrt(2)))
    
    Args:
        x: 표준정규분포 값
        
    Returns:
        누적분포함수 값 (0~1)
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def theta_to_percentile(theta: float) -> float:
    """
    Theta를 퍼센타일(0~100)로 근사 변환.
    
    - theta가 표준정규분포 N(0,1)을 따른다고 가정.
    - Φ(theta) * 100 으로 계산.
    
    Args:
        theta: IRT 능력치
        
    Returns:
        0~100 사이의 퍼센타일
        
    Example:
        >>> theta_to_percentile(0.0)
        50.0
        >>> theta_to_percentile(1.0)  # doctest: +ELLIPSIS
        84.1...
        >>> theta_to_percentile(-1.0)  # doctest: +ELLIPSIS
        15.8...
    """
    return _normal_cdf(theta) * 100.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Theta → 등급 매핑 (1~N 등급, 또는 A/B/C 등)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
    
    등급 매핑 예시:
      - theta >= 1.0   → 1등급
      - theta >= 0.5   → 2등급
      - theta >= 0.0   → 3등급
      - theta >= -0.5  → 4등급
      - theta >= -1.0  → 5등급
      - theta >= -1.5  → 6등급
      - theta >= -2.0  → 7등급
      - theta >= -2.5  → 8등급
      - theta < -2.5   → 9등급
    
    Args:
        theta: IRT 능력치
        cutoffs: 등급 기준 theta 값들 (높은 등급부터 내림차순)
        
    Returns:
        1부터 시작하는 등급 번호
        
    Note:
        기본값은 대략적인 예시로, 실제 수능/내신 기준은 도메인별로 조정 필요.
        
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
    bands: Dict[str, Tuple[float, float]] | None = None,
) -> str:
    """
    퍼센타일 → A/B/C/D/F 등의 **문자 등급**으로 변환.
    
    Args:
        percentile: 0~100 사이의 퍼센타일
        bands: 등급별 퍼센타일 범위 딕셔너리
               기본값:
               {
                   "A": (90, 100),
                   "B": (75, 90),
                   "C": (50, 75),
                   "D": (25, 50),
                   "F": (0, 25),
               }
               
    Returns:
        문자 등급 (A, B, C, D, F)
        
    Example:
        >>> percentile_to_letter_grade(95.0)
        'A'
        >>> percentile_to_letter_grade(80.0)
        'B'
        >>> percentile_to_letter_grade(60.0)
        'C'
        >>> percentile_to_letter_grade(30.0)
        'D'
        >>> percentile_to_letter_grade(10.0)
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
    
    # 100.0 정확히인 경우 A 처리
    if percentile >= 100.0:
        return "A"
    
    # 범위 밖인 경우 보수적으로 처리
    return "F"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 편의 함수: Theta → (점수, 퍼센타일, 등급) 한 번에
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def summarize_theta(
    theta: float,
    min_theta: float = -3.0,
    max_theta: float = 3.0,
) -> Dict[str, float | int | str]:
    """
    Theta 하나로부터 여러 형태의 요약 정보를 반환.
    
    Args:
        theta: IRT 능력치
        min_theta: 0~100 점수 변환 시 최소 theta (기본값: -3.0)
        max_theta: 0~100 점수 변환 시 최대 theta (기본값: 3.0)
        
    Returns:
        다양한 점수/등급 변환 결과를 담은 딕셔너리:
        {
          "theta": 원본 theta 값,
          "score_0_100": 0~100 점수,
          "t_score": T-score (평균 50, 표준편차 10),
          "percentile": 퍼센타일 (0~100),
          "grade_numeric": 숫자 등급 (1~9),
          "grade_letter": 문자 등급 (A/B/C/D/F),
        }
        
    Example:
        >>> result = summarize_theta(0.5)
        >>> result['theta']
        0.5
        >>> result['score_0_100']  # doctest: +ELLIPSIS
        58.3...
        >>> result['t_score']
        55.0
        >>> result['grade_numeric']
        2
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
