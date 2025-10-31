"""핵심 지표 계산 서비스

이 모듈은 학습 분석을 위한 핵심 지표들을 계산합니다:
- 향상지수 I_t: (최근 1~2주 θ 상승량) / (노출량 보정) × 신뢰구간 폭 패널티
- 시간효율 E_t: 올바른 시도당 중앙 반응시간 감소율
- 회복도 R_t: 취약개념에서의 오답→정답 전환 비율
- 참여도 A_t: 세션 빈도, 학습간격, 힌트 사용량, 체류시간의 가중 합
- 이탈위험 S(t): 생존분석 기반 위험도
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone, date
from typing import Any, Dict, List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.metrics import StudentTopicTheta, WeeklyKPI


class MetricsCalculator:
    """핵심 지표 계산기"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_improvement_index(
        self,
        user_id: str,
        topic_id: Optional[str] = None,
        weeks: int = 2,
        exposure_penalty: float = 0.1,
        confidence_penalty: float = 0.05
    ) -> float:
        """향상지수 I_t 계산
        
        Args:
            user_id: 사용자 ID
            topic_id: 토픽 ID (None이면 전체)
            weeks: 분석 기간 (주)
            exposure_penalty: 노출량 보정 계수
            confidence_penalty: 신뢰구간 폭 패널티 계수
            
        Returns:
            향상지수 (0.0 ~ 1.0+)
        """
        # 최근 weeks 주간의 θ 변화량 계산
        theta_changes = self._get_theta_changes(user_id, topic_id, weeks)
        if len(theta_changes) < 2:
            return 0.0
        
        # θ 상승량 계산
        theta_improvement = theta_changes[-1] - theta_changes[0]
        
        # 노출량 보정 (문제 수 기반)
        exposure_count = self._get_exposure_count(user_id, topic_id, weeks)
        exposure_factor = 1.0 / (1.0 + exposure_penalty * exposure_count)
        
        # 신뢰구간 폭 패널티 (표준오차 기반)
        confidence_factor = self._get_confidence_factor(user_id, topic_id, weeks)
        confidence_penalty_factor = 1.0 - (confidence_penalty * confidence_factor)
        
        # 향상지수 계산
        improvement_index = theta_improvement * exposure_factor * confidence_penalty_factor
        
        return max(0.0, improvement_index)
    
    def calculate_efficiency_index(
        self,
        user_id: str,
        topic_id: Optional[str] = None,
        weeks: int = 2
    ) -> float:
        """시간효율 E_t 계산
        
        Args:
            user_id: 사용자 ID
            topic_id: 토픽 ID (None이면 전체)
            weeks: 분석 기간 (주)
            
        Returns:
            시간효율 (0.0 ~ 1.0+)
        """
        # 최근 weeks 주간의 반응시간 데이터
        response_times = self._get_response_times(user_id, topic_id, weeks)
        if len(response_times) < 2:
            return 0.0
        
        # 올바른 답변의 반응시간만 필터링
        correct_times = [rt for rt, correct in response_times if correct]
        if len(correct_times) < 2:
            return 0.0
        
        # 중앙 반응시간 계산 (중앙값 사용)
        correct_times.sort()
        n = len(correct_times)
        if n % 2 == 0:
            median_time = (correct_times[n//2-1] + correct_times[n//2]) / 2
        else:
            median_time = correct_times[n//2]
        
        # 이전 기간과 비교하여 감소율 계산
        mid_point = n // 2
        recent_median = correct_times[mid_point:]
        earlier_median = correct_times[:mid_point]
        
        if len(recent_median) == 0 or len(earlier_median) == 0:
            return 0.0
        
        recent_median_time = sum(recent_median) / len(recent_median)
        earlier_median_time = sum(earlier_median) / len(earlier_median)
        
        if earlier_median_time <= 0:
            return 0.0
        
        # 감소율 계산 (음수면 개선, 양수면 악화)
        efficiency = (earlier_median_time - recent_median_time) / earlier_median_time
        
        return max(0.0, efficiency)
    
    def calculate_recovery_index(
        self,
        user_id: str,
        topic_id: Optional[str] = None,
        weeks: int = 2,
        weakness_threshold: float = 0.6
    ) -> float:
        """회복도 R_t 계산
        
        Args:
            user_id: 사용자 ID
            topic_id: 토픽 ID (None이면 전체)
            weeks: 분석 기간 (주)
            weakness_threshold: 취약개념 판단 임계값
            
        Returns:
            회복도 (0.0 ~ 1.0)
        """
        # 취약개념 식별
        weak_concepts = self._identify_weak_concepts(user_id, topic_id, weeks, weakness_threshold)
        if not weak_concepts:
            return 0.0
        
        # 취약개념에서의 오답→정답 전환 비율 계산
        total_transitions = 0
        successful_transitions = 0
        
        for concept in weak_concepts:
            transitions = self._get_concept_transitions(user_id, concept, weeks)
            total_transitions += len(transitions)
            successful_transitions += sum(1 for prev_correct, curr_correct in transitions 
                                       if not prev_correct and curr_correct)
        
        if total_transitions == 0:
            return 0.0
        
        recovery_rate = successful_transitions / total_transitions
        return recovery_rate
    
    def calculate_engagement_index(
        self,
        user_id: str,
        weeks: int = 2,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """참여도 A_t 계산
        
        Args:
            user_id: 사용자 ID
            weeks: 분석 기간 (주)
            weights: 각 요소별 가중치 {'session_freq': 0.3, 'learning_interval': 0.2, 
                    'hint_usage': 0.2, 'dwell_time': 0.3}
            
        Returns:
            참여도 (0.0 ~ 1.0)
        """
        if weights is None:
            weights = {
                'session_freq': 0.3,
                'learning_interval': 0.2,
                'hint_usage': 0.2,
                'dwell_time': 0.3
            }
        
        # 세션 빈도 (정규화된 값)
        session_freq = self._calculate_session_frequency(user_id, weeks)
        
        # 학습간격 (일관성 점수)
        learning_interval = self._calculate_learning_interval_consistency(user_id, weeks)
        
        # 힌트 사용량 (적절한 사용률)
        hint_usage = self._calculate_hint_usage_appropriateness(user_id, weeks)
        
        # 체류시간 (적절한 학습 시간)
        dwell_time = self._calculate_dwell_time_appropriateness(user_id, weeks)
        
        # 가중 합 계산
        engagement = (
            weights['session_freq'] * session_freq +
            weights['learning_interval'] * learning_interval +
            weights['hint_usage'] * hint_usage +
            weights['dwell_time'] * dwell_time
        )
        
        return min(1.0, max(0.0, engagement))
    
    def calculate_dropout_risk(
        self,
        user_id: str,
        days_threshold: int = 14,
        baseline_risk: float = 0.1
    ) -> float:
        """이탈위험 S(t) 계산
        
        Args:
            user_id: 사용자 ID
            days_threshold: 이탈 판단 기준 (일)
            baseline_risk: 베이스라인 위험도
            
        Returns:
            이탈위험 (0.0 ~ 1.0)
        """
        # 마지막 접속일 확인
        last_access = self._get_last_access_date(user_id)
        if last_access is None:
            return 1.0  # 접속 기록이 없으면 최고 위험
        
        # 접속하지 않은 일수
        now_utc = datetime.now(timezone.utc)
        if last_access.tzinfo is None:
            # If last_access is naive, assume UTC
            last_access = last_access.replace(tzinfo=timezone.utc)
        days_since_access = (now_utc - last_access).days
        
        # 베이스라인 위험도
        risk = baseline_risk
        
        # 시간 기반 위험도 증가
        if days_since_access >= days_threshold:
            risk = 1.0  # 임계값 초과시 최고 위험
        else:
            # 선형 증가
            risk += (days_since_access / days_threshold) * (1.0 - baseline_risk)
        
        # 공변량 기반 조정
        covariates = self._get_risk_covariates(user_id)
        risk = self._adjust_risk_with_covariates(risk, covariates)
        
        return min(1.0, max(0.0, risk))
    
    # === 헬퍼 메서드들 ===
    
    def _get_theta_changes(self, user_id: str, topic_id: Optional[str], weeks: int) -> List[float]:
        """θ 변화량 추적 (주간 평균).

        Uses exam_results.result_json->>'ability_estimate' when available; falls back to
        exam_results.standard_error/score if needed. Aggregates by ISO week starting Monday.
        """
        if weeks <= 0:
            return []
        now = datetime.now(timezone.utc)
        start_dt = now - timedelta(weeks=weeks)
        # Postgres: date_trunc('week', ts)
        sql = text(
            """
            SELECT date_trunc('week', COALESCE(updated_at, created_at))::date AS week_start,
                   AVG( COALESCE( (result_json->>'ability_estimate')::numeric, 0) ) AS avg_theta
            FROM exam_results
            WHERE user_id = :uid
              AND COALESCE(updated_at, created_at) >= :start
            GROUP BY 1
            ORDER BY 1
            """
        )
        rows = self.db.execute(sql, {"uid": user_id, "start": start_dt}).mappings().all()
        return [float(r["avg_theta"] or 0.0) for r in rows]
    
    def _get_exposure_count(self, user_id: str, topic_id: Optional[str], weeks: int) -> int:
        """노출량 계산: 최근 기간의 총 문제 수 (questions 배열 길이 합)."""
        now = datetime.now(timezone.utc)
        start_dt = now - timedelta(weeks=weeks)
        sql = text(
            """
            SELECT COALESCE(SUM(jsonb_array_length(result_json->'questions')), 0) AS q_cnt
            FROM exam_results
            WHERE user_id = :uid AND COALESCE(updated_at, created_at) >= :start
            """
        )
        row = self.db.execute(sql, {"uid": user_id, "start": start_dt}).mappings().first()
        return int(row["q_cnt"]) if row and row["q_cnt"] is not None else 0
    
    def _get_confidence_factor(self, user_id: str, topic_id: Optional[str], weeks: int) -> float:
        """신뢰구간 폭 요소: 최근 기간 표준오차 평균을 0..1로 정규화한 계수.

        Uses exam_results.standard_error when present; else pulls from result_json.
        """
        now = datetime.now(timezone.utc)
        start_dt = now - timedelta(weeks=weeks)
        sql = text(
            """
            SELECT AVG(
                COALESCE(standard_error,
                         NULLIF((result_json->>'standard_error')::numeric, NULL))
            ) AS avg_se
            FROM exam_results
            WHERE user_id = :uid AND COALESCE(updated_at, created_at) >= :start
            """
        )
        row = self.db.execute(sql, {"uid": user_id, "start": start_dt}).mappings().first()
        se = float(row["avg_se"]) if row and row["avg_se"] is not None else 0.0
        # Normalize: assume SE in ~[0,1], cap to 1
        return max(0.0, min(1.0, se))
    
    def _get_response_times(self, user_id: str, topic_id: Optional[str], weeks: int) -> List[Tuple[float, bool]]:
        """반응시간 데이터 조회.

        If result_json->questions contains time_spent_sec, extract it; else return empty.
        """
        now = datetime.now(timezone.utc)
        start_dt = now - timedelta(weeks=weeks)
        # Unnest is easier in SQL, but to avoid complex JSONB SQL, fetch minimal rows and parse in Python
        sql = text(
            """
            SELECT result_json
            FROM exam_results
            WHERE user_id = :uid AND COALESCE(updated_at, created_at) >= :start
            ORDER BY COALESCE(updated_at, created_at)
            LIMIT 200
            """
        )
        rows = self.db.execute(sql, {"uid": user_id, "start": start_dt}).fetchall()
        out: List[Tuple[float, bool]] = []
        for (doc,) in rows:
            try:
                qs = (doc or {}).get("questions") or []
                for q in qs:
                    t = q.get("time_spent_sec")
                    ok = bool(q.get("is_correct") or q.get("correct"))
                    if isinstance(t, (int, float)):
                        out.append((float(t), ok))
            except Exception:
                continue
        return out
    
    def _identify_weak_concepts(self, user_id: str, topic_id: Optional[str], weeks: int, threshold: float) -> List[str]:
        """취약개념 식별: 최근 기간 topic accuracy <= threshold."""
        now = datetime.now(timezone.utc)
        start_dt = now - timedelta(weeks=weeks)
        sql = text(
            """
            SELECT result_json
            FROM exam_results
            WHERE user_id = :uid AND COALESCE(updated_at, created_at) >= :start
            ORDER BY COALESCE(updated_at, created_at) DESC
            LIMIT 10
            """
        )
        rows = self.db.execute(sql, {"uid": user_id, "start": start_dt}).fetchall()
        # Look at the most recent document with topics
        for (doc,) in rows:
            try:
                topics = (doc or {}).get("topics") or []
                if isinstance(topics, list) and topics:
                    weak = [str(t.get("topic")) for t in topics if float(t.get("accuracy") or 0.0) <= float(threshold)]
                    return weak[:10]
            except Exception:
                continue
        return []
    
    def _get_concept_transitions(self, user_id: str, concept: str, weeks: int) -> List[Tuple[bool, bool]]:
        """개념별 오답→정답 전환 추적 (주간 단위 accuracy 임계치를 통한 근사)."""
        now = datetime.now(timezone.utc)
        start_dt = now - timedelta(weeks=weeks)
        sql = text(
            """
            SELECT date_trunc('week', COALESCE(updated_at, created_at))::date AS wk,
                   result_json
            FROM exam_results
            WHERE user_id = :uid AND COALESCE(updated_at, created_at) >= :start
            ORDER BY wk
            """
        )
        rows = self.db.execute(sql, {"uid": user_id, "start": start_dt}).fetchall()
        series: List[bool] = []
        for (_, doc) in rows:
            try:
                topics = (doc or {}).get("topics") or []
                acc = None
                for t in topics:
                    if str(t.get("topic")) == str(concept):
                        acc = float(t.get("accuracy") or 0.0)
                        break
                if acc is None:
                    continue
                series.append(acc >= 0.6)
            except Exception:
                continue
        trans: List[Tuple[bool, bool]] = []
        for i in range(1, len(series)):
            trans.append((series[i-1], series[i]))
        return trans
    
    def _calculate_session_frequency(self, user_id: str, weeks: int) -> float:
        """세션 빈도 계산 (정규화): 주당 세션 수를 0..1로 맵핑."""
        now = datetime.now(timezone.utc)
        start_dt = now - timedelta(weeks=weeks)
        row = self.db.execute(
            text(
                """
                SELECT COUNT(*) AS n
                FROM exam_results
                WHERE user_id = :uid AND COALESCE(updated_at, created_at) >= :start
                """
            ),
            {"uid": user_id, "start": start_dt},
        ).mappings().first()
        n = int(row["n"]) if row and row["n"] is not None else 0
        # Assume 7+ sessions/week is excellent -> 1.0
        target = max(1, weeks * 7)
        return max(0.0, min(1.0, n / target))
    
    def _calculate_learning_interval_consistency(self, user_id: str, weeks: int) -> float:
        """학습간격 일관성 계산: 간격 표준편차를 역으로 맵핑."""
        now = datetime.now(timezone.utc)
        start_dt = now - timedelta(weeks=weeks)
        rows = self.db.execute(
            text(
                """
                SELECT COALESCE(updated_at, created_at) AS ts
                FROM exam_results
                WHERE user_id = :uid AND COALESCE(updated_at, created_at) >= :start
                ORDER BY ts
                """
            ),
            {"uid": user_id, "start": start_dt},
        ).fetchall()
        if len(rows) < 3:
            return 0.5
        ts_list = [r[0] for r in rows]
        gaps = []
        for i in range(1, len(ts_list)):
            gaps.append((ts_list[i] - ts_list[i - 1]).total_seconds() / 86400.0)
        if not gaps:
            return 0.5
        mean_gap = sum(gaps) / len(gaps)
        var = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
        std = var ** 0.5
        # Map std to 0..1 where lower std (more consistent) => closer to 1
        return max(0.0, min(1.0, 1.0 - (std / 7.0)))
    
    def _calculate_hint_usage_appropriateness(self, user_id: str, weeks: int) -> float:
        """힌트 사용 적절성 계산 (데이터 없으면 0.5)."""
        return 0.5
    
    def _calculate_dwell_time_appropriateness(self, user_id: str, weeks: int) -> float:
        """체류시간 적절성 계산 (데이터 없으면 0.5)."""
        return 0.5
    
    def _get_last_access_date(self, user_id: str) -> Optional[datetime]:
        """마지막 접속일: exam_results.updated_at 최대값."""
        row = self.db.execute(
            text(
                """
                SELECT MAX(COALESCE(updated_at, created_at)) AS last_ts
                FROM exam_results
                WHERE user_id = :uid
                """
            ),
            {"uid": user_id},
        ).mappings().first()
        return row["last_ts"] if row and row["last_ts"] is not None else None
    
    def _get_risk_covariates(self, user_id: str) -> Dict[str, Any]:
        """위험도 공변량: 참여도와 성과 추세를 간단히 산출."""
        engagement = self._calculate_session_frequency(user_id, weeks=4)
        thetas = self._get_theta_changes(user_id, topic_id=None, weeks=4)
        trend = 0.0
        if len(thetas) >= 2:
            trend = thetas[-1] - thetas[0]
        return {
            'engagement_score': engagement,
            'performance_trend': trend,
            'session_consistency': self._calculate_learning_interval_consistency(user_id, weeks=4),
        }

    # ----- Persistence helpers -----
    def upsert_weekly_kpi(self, user_id: str, week_start: date, kpis: Dict[str, Any]) -> None:
        """Persist weekly KPIs using ORM upsert-like behavior."""
        existing: WeeklyKPI | None = (
            self.db.query(WeeklyKPI)
            .filter(WeeklyKPI.user_id == user_id, WeeklyKPI.week_start == week_start)
            .first()
        )
        if existing:
            existing.kpis = dict(kpis)
            existing.updated_at = datetime.now(timezone.utc)
        else:
            row = WeeklyKPI(user_id=user_id, week_start=week_start, kpis=dict(kpis))
            self.db.add(row)
        self.db.commit()
    
    def _adjust_risk_with_covariates(self, base_risk: float, covariates: Dict[str, Any]) -> float:
        """공변량 기반 위험도 조정"""
        # TODO: 실제 공변량 기반 조정 로직
        engagement_factor = covariates.get('engagement_score', 0.5)
        performance_factor = covariates.get('performance_trend', 0.0)
        
        # 참여도가 높으면 위험도 감소
        risk = base_risk * (1.0 - engagement_factor * 0.3)
        
        # 성과 트렌드가 하락하면 위험도 증가
        if performance_factor < 0:
            risk += abs(performance_factor) * 0.2
        
        return risk


def get_metrics_calculator() -> MetricsCalculator:
    """메트릭 계산기 인스턴스 생성"""
    db = next(get_db())
    return MetricsCalculator(db)
