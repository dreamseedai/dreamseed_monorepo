"""
실시간 드리프트 탐지 모델
베이지안 업데이트 기반 IRT 파라미터 변화 감지
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum


class DriftLevel(str, Enum):
    """드리프트 경보 레벨"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DriftType(str, Enum):
    """드리프트 유형"""
    DIFFICULTY_MIGRATION = "difficulty_migration"
    GUESSING_INSTABILITY = "guessing_instability"
    ANCHOR_EROSION = "anchor_erosion"
    CURRICULUM_SHIFT = "curriculum_shift"
    LATENCY_CREEP = "latency_creep"
    REGION_LANGUAGE_DRIFT = "region_language_drift"


@dataclass
class DriftAlert:
    """드리프트 경보"""
    type: DriftType
    level: DriftLevel
    title: str
    message: str
    probability: float
    metric_value: float
    threshold: float
    action: str
    timestamp: str


class BayesianDriftDetector:
    """베이지안 드리프트 탐지기"""
    
    def __init__(self, thresholds: Dict[str, float] = None):
        self.thresholds = thresholds or {
            'delta_b': 0.35,  # 난이도 변화 (표준편차 단위)
            'delta_a': 0.40,  # 변별도 변화
            'delta_c': 0.06,  # 추측도 변화
            'omit_rate': 0.08,  # 무응답률
            'last_option_rate': 0.30,  # 마지막 보기 선택률
            'latency_p95': 120.0,  # 95th percentile 응답시간 (초)
            'accuracy_diff': 0.15,  # 지역별 정답률 차이
        }
    
    def detect_anchor_erosion(
        self,
        anchor_params: Dict[str, Tuple[float, float]],  # item_id -> (b_current, b_baseline)
        window_days: int = 7
    ) -> List[DriftAlert]:
        """앵커 문항 파라미터 변화 감지"""
        alerts = []
        
        for item_id, (b_current, b_baseline) in anchor_params.items():
            delta_b = abs(b_current - b_baseline)
            
            # 베이지안 확률 추정 (간단한 근사)
            # P(drift) = 1 - exp(-lambda * delta^2)
            prob_drift = 1 - np.exp(-2 * (delta_b / self.thresholds['delta_b']) ** 2)
            
            if delta_b > self.thresholds['delta_b']:
                level = DriftLevel.HIGH if delta_b > 2 * self.thresholds['delta_b'] else DriftLevel.MEDIUM
                
                alerts.append(DriftAlert(
                    type=DriftType.ANCHOR_EROSION,
                    level=level,
                    title="Anchor Erosion",
                    message=f"앵커 문항 {item_id}의 난이도 변화 Δb = {delta_b:.3f} ({window_days}일 이동창). "
                            f"P(drift) = {prob_drift:.2f}. 대응: 재보정 큐에 편성.",
                    probability=prob_drift,
                    metric_value=delta_b,
                    threshold=self.thresholds['delta_b'],
                    action="recalibrate_anchor",
                    timestamp=np.datetime64('now').astype(str)
                ))
        
        return alerts
    
    def detect_guessing_instability(
        self,
        c_params: Dict[str, List[float]],  # grade -> [c_values over time]
        window_days: int = 14
    ) -> List[DriftAlert]:
        """추측 행동 불안정성 감지"""
        alerts = []
        
        for grade, c_values in c_params.items():
            if len(c_values) < 2:
                continue
            
            c_mean_current = np.mean(c_values[-7:])  # 최근 7일
            c_mean_baseline = np.mean(c_values[:-7])  # 이전 기간
            delta_c = c_mean_current - c_mean_baseline
            
            if abs(delta_c) > self.thresholds['delta_c']:
                level = DriftLevel.HIGH if abs(delta_c) > 2 * self.thresholds['delta_c'] else DriftLevel.MEDIUM
                
                alerts.append(DriftAlert(
                    type=DriftType.GUESSING_INSTABILITY,
                    level=level,
                    title="Guessing Instability",
                    message=f"{grade} 학년 추측도 변화 Δc = {delta_c:+.3f} ({window_days}일). "
                            f"대응: 보기 난이도/길이 점검.",
                    probability=min(abs(delta_c) / self.thresholds['delta_c'], 1.0),
                    metric_value=delta_c,
                    threshold=self.thresholds['delta_c'],
                    action="review_item_options",
                    timestamp=np.datetime64('now').astype(str)
                ))
        
        return alerts
    
    def detect_difficulty_migration(
        self,
        b_distribution: np.ndarray,  # 현재 난이도 분포
        b_baseline: np.ndarray,  # 기준 난이도 분포
    ) -> List[DriftAlert]:
        """난이도 분포 이동 감지"""
        alerts = []
        
        # KL divergence 계산 (간단한 히스토그램 기반)
        bins = np.linspace(-3, 3, 20)
        hist_current, _ = np.histogram(b_distribution, bins=bins, density=True)
        hist_baseline, _ = np.histogram(b_baseline, bins=bins, density=True)
        
        # 작은 값 처리
        hist_current = hist_current + 1e-10
        hist_baseline = hist_baseline + 1e-10
        
        kl_div = np.sum(hist_current * np.log(hist_current / hist_baseline))
        
        mean_shift = np.mean(b_distribution) - np.mean(b_baseline)
        
        if kl_div > 0.5 or abs(mean_shift) > 0.3:
            level = DriftLevel.HIGH if kl_div > 1.0 else DriftLevel.MEDIUM
            
            direction = "쉬움" if mean_shift < 0 else "어려움"
            
            alerts.append(DriftAlert(
                type=DriftType.DIFFICULTY_MIGRATION,
                level=level,
                title="Difficulty Migration",
                message=f"문항 난이도 분포가 {direction} 쪽으로 이동 (Δμ = {mean_shift:+.3f}, KL = {kl_div:.3f}). "
                        f"θ 추정 편향 위험. 대응: 문항 풀 재균형.",
                probability=min(kl_div / 0.5, 1.0),
                metric_value=mean_shift,
                threshold=0.3,
                action="rebalance_item_pool",
                timestamp=np.datetime64('now').astype(str)
            ))
        
        return alerts
    
    def detect_region_language_drift(
        self,
        accuracy_by_region: Dict[str, float],  # region -> accuracy
    ) -> List[DriftAlert]:
        """지역/언어별 정답률 격차 감지"""
        alerts = []
        
        if len(accuracy_by_region) < 2:
            return alerts
        
        accuracies = list(accuracy_by_region.values())
        max_acc = max(accuracies)
        min_acc = min(accuracies)
        diff = max_acc - min_acc
        
        if diff > self.thresholds['accuracy_diff']:
            level = DriftLevel.HIGH if diff > 2 * self.thresholds['accuracy_diff'] else DriftLevel.MEDIUM
            
            max_region = max(accuracy_by_region, key=accuracy_by_region.get)
            min_region = min(accuracy_by_region, key=accuracy_by_region.get)
            
            alerts.append(DriftAlert(
                type=DriftType.REGION_LANGUAGE_DRIFT,
                level=level,
                title="Region-Language Drift",
                message=f"지역별 정답률 격차 확대: {max_region} ({max_acc:.1%}) vs {min_region} ({min_acc:.1%}). "
                        f"차이 = {diff:.1%}. 대응: 언어별 문항 난이도 재검토.",
                probability=min(diff / self.thresholds['accuracy_diff'], 1.0),
                metric_value=diff,
                threshold=self.thresholds['accuracy_diff'],
                action="review_language_items",
                timestamp=np.datetime64('now').astype(str)
            ))
        
        return alerts
    
    def detect_latency_creep(
        self,
        latency_p95_current: float,
        latency_p95_baseline: float,
    ) -> List[DriftAlert]:
        """응답 시간 증가 감지"""
        alerts = []
        
        if latency_p95_current > self.thresholds['latency_p95']:
            increase_pct = (latency_p95_current - latency_p95_baseline) / latency_p95_baseline
            
            if increase_pct > 0.2:  # 20% 이상 증가
                level = DriftLevel.HIGH if increase_pct > 0.5 else DriftLevel.MEDIUM
                
                alerts.append(DriftAlert(
                    type=DriftType.LATENCY_CREEP,
                    level=level,
                    title="Latency Creep",
                    message=f"응답 시간 P95 증가: {latency_p95_current:.1f}초 "
                            f"(+{increase_pct:.1%} vs 기준). 피로/UI 지연 가능. "
                            f"대응: 성능 프로파일링.",
                    probability=min(increase_pct / 0.2, 1.0),
                    metric_value=latency_p95_current,
                    threshold=self.thresholds['latency_p95'],
                    action="profile_performance",
                    timestamp=np.datetime64('now').astype(str)
                ))
        
        return alerts
    
    def aggregate_alerts(
        self,
        alerts: List[DriftAlert],
        min_consecutive_days: int = 3
    ) -> List[DriftAlert]:
        """경보 집계 및 필터링 (지속성 조건)"""
        # 실제 구현에서는 Redis/DB에서 이전 경보 이력을 조회하여
        # 연속 발생 여부를 확인해야 함
        
        # 높은 확률의 경보만 반환
        high_confidence_alerts = [
            alert for alert in alerts
            if alert.probability > 0.8 or alert.level == DriftLevel.HIGH
        ]
        
        return high_confidence_alerts
