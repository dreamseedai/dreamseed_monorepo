"""토픽별 숙련도 추정 서비스

이 모듈은 토픽 레벨에서의 IRT 기반 숙련도 추정을 제공합니다.
베이지안 사전분포를 사용하여 안정화된 θ 추정치를 계산합니다.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.metrics import StudentTopicTheta
from shared.irt import irf_3pl, item_information_3pl, map_theta_fisher


class TopicAbilityService:
    """토픽별 숙련도 추정 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def estimate_topic_ability(
        self,
        user_id: str,
        topic_id: str,
        responses: List[Dict[str, Any]],
        prior_mean: float = 0.0,
        prior_sd: float = 1.0,
    ) -> Tuple[float, float, str]:
        """토픽별 숙련도 θ 추정

        Args:
            user_id: 사용자 ID
            topic_id: 토픽 ID
            responses: 해당 토픽의 응답 데이터
            prior_mean: 베이지안 사전분포 평균
            prior_sd: 베이지안 사전분포 표준편차

        Returns:
            (theta, standard_error, method_name)
        """
        if not responses:
            return prior_mean, prior_sd, "prior_only"

        # 응답 데이터를 IRT 형식으로 변환
        items, response_values = self._prepare_irt_data(responses)

        if not items:
            return prior_mean, prior_sd, "no_valid_items"

        # MAP 추정 (베이지안)
        theta = map_theta_fisher(
            items=items,
            responses=response_values,
            prior_mean=prior_mean,
            prior_var=prior_sd**2,
            initial_theta=prior_mean,
            max_iter=25,
            tol=1e-4,
        )

        # 표준오차 계산
        se = self._calculate_standard_error(theta, items, prior_sd)

        # DB에 저장
        self._save_topic_theta(user_id, topic_id, theta, se)

        return theta, se, "map_estimation"

    def get_topic_abilities(
        self, user_id: str, topic_ids: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """사용자의 토픽별 숙련도 조회

        Args:
            user_id: 사용자 ID
            topic_ids: 조회할 토픽 ID 리스트 (None이면 전체)

        Returns:
            {topic_id: {theta: float, se: float, updated_at: datetime}}
        """
        query = self.db.query(StudentTopicTheta).filter(
            StudentTopicTheta.user_id == user_id
        )

        if topic_ids:
            query = query.filter(StudentTopicTheta.topic_id.in_(topic_ids))

        results = query.all()

        abilities = {}
        for result in results:
            abilities[result.topic_id] = {
                "theta": result.theta,
                "se": result.standard_error,
                "updated_at": result.updated_at,
            }

        return abilities

    def update_topic_abilities_batch(
        self,
        user_id: str,
        topic_responses: Dict[str, List[Dict[str, Any]]],
        prior_mean: float = 0.0,
        prior_sd: float = 1.0,
    ) -> Dict[str, Tuple[float, float, str]]:
        """여러 토픽의 숙련도를 일괄 업데이트

        Args:
            user_id: 사용자 ID
            topic_responses: {topic_id: [responses]} 형태의 데이터
            prior_mean: 베이지안 사전분포 평균
            prior_sd: 베이지안 사전분포 표준편차

        Returns:
            {topic_id: (theta, se, method)}
        """
        results = {}

        for topic_id, responses in topic_responses.items():
            theta, se, method = self.estimate_topic_ability(
                user_id, topic_id, responses, prior_mean, prior_sd
            )
            results[topic_id] = (theta, se, method)

        return results

    def get_ability_trend(
        self, user_id: str, topic_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """토픽별 숙련도 트렌드 조회

        Args:
            user_id: 사용자 ID
            topic_id: 토픽 ID
            days: 조회 기간 (일)

        Returns:
            [{'date': datetime, 'theta': float, 'se': float}]
        """
        # TODO: 실제 히스토리 데이터 조회
        # 현재는 더미 데이터 반환
        from datetime import timedelta

        trend = []
        base_date = datetime.now() - timedelta(days=days)

        for i in range(0, days, 7):  # 주간 단위
            date = base_date + timedelta(days=i)
            theta = 0.5 + 0.1 * (i / 7)  # 더미 트렌드
            se = 0.3

            trend.append({"date": date, "theta": theta, "se": se})

        return trend

    def identify_weak_topics(
        self, user_id: str, threshold: float = -0.5, min_responses: int = 5
    ) -> List[Dict[str, Any]]:
        """취약 토픽 식별

        Args:
            user_id: 사용자 ID
            threshold: 취약 토픽 판단 임계값 (θ < threshold)
            min_responses: 최소 응답 수

        Returns:
            [{'topic_id': str, 'theta': float, 'se': float, 'response_count': int}]
        """
        abilities = self.get_topic_abilities(user_id)
        weak_topics = []

        for topic_id, ability_data in abilities.items():
            theta = ability_data["theta"]
            se = ability_data["se"]

            # TODO: 실제 응답 수 조회
            response_count = 10  # 더미 데이터

            if theta < threshold and response_count >= min_responses:
                weak_topics.append(
                    {
                        "topic_id": topic_id,
                        "theta": theta,
                        "se": se,
                        "response_count": response_count,
                    }
                )

        return weak_topics

    def get_topic_difficulty_profile(
        self, user_id: str, topic_id: str
    ) -> Dict[str, Any]:
        """토픽별 난이도 프로파일 생성

        Args:
            user_id: 사용자 ID
            topic_id: 토픽 ID

        Returns:
            {'easy': int, 'medium': int, 'hard': int, 'total': int}
        """
        # TODO: 실제 난이도 분포 계산
        # 현재는 더미 데이터
        return {"easy": 3, "medium": 5, "hard": 2, "total": 10}

    # === 헬퍼 메서드들 ===

    def _prepare_irt_data(
        self, responses: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """응답 데이터를 IRT 형식으로 변환"""
        items = []
        response_values = []

        for response in responses:
            # IRT 파라미터 추출
            a = float(response.get("a", 1.0))  # discrimination
            b = float(response.get("b", 0.0))  # difficulty
            c = float(response.get("c", 0.2))  # guessing

            # 유효한 파라미터인지 확인
            if a <= 0 or c < 0 or c >= 1:
                continue

            items.append({"a": a, "b": b, "c": c})
            response_values.append(1 if response.get("correct", False) else 0)

        return items, response_values

    def _calculate_standard_error(
        self, theta: float, items: List[Dict[str, Any]], prior_sd: float
    ) -> float:
        """표준오차 계산"""
        # Fisher 정보 계산
        total_info = 0.0
        for item in items:
            a = item["a"]
            b = item["b"]
            c = item["c"]
            total_info += item_information_3pl(theta, a, b, c)

        # 사전분포 정보 추가
        prior_info = 1.0 / (prior_sd**2)
        total_info += prior_info

        # 표준오차 = 1 / sqrt(정보량)
        if total_info > 0:
            return 1.0 / math.sqrt(total_info)
        else:
            return prior_sd

    def _save_topic_theta(
        self, user_id: str, topic_id: str, theta: float, se: float
    ) -> None:
        """토픽별 θ를 DB에 저장"""
        # 기존 레코드 확인
        existing = (
            self.db.query(StudentTopicTheta)
            .filter(
                StudentTopicTheta.user_id == user_id,
                StudentTopicTheta.topic_id == topic_id,
            )
            .first()
        )

        if existing:
            # 업데이트
            existing.theta = theta
            existing.standard_error = se
            existing.updated_at = datetime.now()
        else:
            # 새로 생성
            new_theta = StudentTopicTheta(
                user_id=user_id, topic_id=topic_id, theta=theta, standard_error=se
            )
            self.db.add(new_theta)

        self.db.commit()


def get_topic_ability_service() -> TopicAbilityService:
    """토픽별 숙련도 서비스 인스턴스 생성"""
    db = next(get_db())
    return TopicAbilityService(db)
