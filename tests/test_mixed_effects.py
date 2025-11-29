"""Tests for Mixed-Effects Model

혼합효과 모형 테스트
==================

이 테스트는 혼합효과 모형의 다음 기능을 검증합니다:
1. 학생 능력 추정
2. 문항 난이도 추정
3. 상호 보정 효과
4. 공정한 측정
"""

import pytest
from shared.mixed_effects import (
    fit_mixed_effects,
    estimate_single_student_with_calibrated_items,
    ResponseData,
    StudentAbility,
    ItemDifficulty,
)


class TestMixedEffects:
    """혼합효과 모형 테스트"""

    def test_basic_estimation(self):
        """기본 능력 추정 테스트"""
        responses = [
            {
                "student_id": "s1",
                "item_id": "q1",
                "correct": True,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s1",
                "item_id": "q2",
                "correct": False,
                "a": 1.0,
                "b": 1.0,
                "c": 0.0,
            },
            {
                "student_id": "s2",
                "item_id": "q1",
                "correct": True,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s2",
                "item_id": "q2",
                "correct": True,
                "a": 1.0,
                "b": 1.0,
                "c": 0.0,
            },
        ]

        abilities, difficulties = fit_mixed_effects(responses, verbose=False)

        # 결과 확인
        assert "s1" in abilities
        assert "s2" in abilities
        assert "q1" in difficulties
        assert "q2" in difficulties

        # s2가 s1보다 능력이 높아야 함
        assert abilities["s2"].theta > abilities["s1"].theta

        # q2가 q1보다 어려워야 함 (모든 학생이 q1은 맞히고 q2는 일부만 맞힘)
        assert difficulties["q2"].b > difficulties["q1"].b

    def test_ability_bounds(self):
        """능력 추정치가 합리적 범위 내에 있는지 확인"""
        responses = [
            {
                "student_id": "s1",
                "item_id": "q1",
                "correct": True,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s1",
                "item_id": "q2",
                "correct": True,
                "a": 1.0,
                "b": 0.5,
                "c": 0.0,
            },
            {
                "student_id": "s1",
                "item_id": "q3",
                "correct": True,
                "a": 1.0,
                "b": 1.0,
                "c": 0.0,
            },
        ]

        abilities, _ = fit_mixed_effects(responses, verbose=False)

        # 모든 문항을 맞힌 학생의 능력은 양수여야 함
        assert abilities["s1"].theta > 0
        assert -4.0 <= abilities["s1"].theta <= 4.0

    def test_difficulty_bias_correction(self):
        """난이도 편차 보정 테스트"""
        # 시나리오: q1은 모든 학생이 맞힘 (쉬움)
        #          q2는 모든 학생이 틀림 (어려움)
        responses = [
            {
                "student_id": "s1",
                "item_id": "q1",
                "correct": True,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s1",
                "item_id": "q2",
                "correct": False,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s2",
                "item_id": "q1",
                "correct": True,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s2",
                "item_id": "q2",
                "correct": False,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s3",
                "item_id": "q1",
                "correct": True,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s3",
                "item_id": "q2",
                "correct": False,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
        ]

        abilities, difficulties = fit_mixed_effects(responses, verbose=False)

        # q1은 쉬워야 함 (b < 0)
        # q2는 어려워야 함 (b > 0)
        assert difficulties["q1"].b < difficulties["q2"].b

        # 모든 학생의 능력은 비슷해야 함 (같은 패턴)
        thetas = [a.theta for a in abilities.values()]
        theta_std = (
            sum((t - sum(thetas) / len(thetas)) ** 2 for t in thetas) / len(thetas)
        ) ** 0.5
        assert theta_std < 1.0  # 표준편차가 작아야 함

    def test_empty_responses(self):
        """빈 응답 처리 테스트"""
        responses = []
        abilities, difficulties = fit_mixed_effects(responses, verbose=False)

        assert len(abilities) == 0
        assert len(difficulties) == 0

    def test_single_student_calibration(self):
        """보정된 문항으로 단일 학생 능력 추정"""
        # Step 1: 전체 데이터로 문항 보정
        all_responses = [
            {
                "student_id": "s1",
                "item_id": "q1",
                "correct": True,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s1",
                "item_id": "q2",
                "correct": False,
                "a": 1.0,
                "b": 1.0,
                "c": 0.0,
            },
            {
                "student_id": "s2",
                "item_id": "q1",
                "correct": True,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s2",
                "item_id": "q2",
                "correct": True,
                "a": 1.0,
                "b": 1.0,
                "c": 0.0,
            },
        ]

        _, difficulties = fit_mixed_effects(all_responses, verbose=False)

        # Step 2: 새 학생의 능력 추정
        new_student_responses = [
            {
                "student_id": "s3",
                "item_id": "q1",
                "correct": True,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            },
            {
                "student_id": "s3",
                "item_id": "q2",
                "correct": True,
                "a": 1.0,
                "b": 1.0,
                "c": 0.0,
            },
        ]

        ability = estimate_single_student_with_calibrated_items(
            new_student_responses,
            difficulties,
        )

        assert ability.student_id == "s3"
        assert ability.theta > 0  # 모든 문항 정답이므로 양수
        assert ability.n_responses == 2

    def test_convergence(self):
        """EM 알고리즘 수렴 테스트"""
        responses = [
            {
                "student_id": f"s{i}",
                "item_id": "q1",
                "correct": i % 2 == 0,
                "a": 1.0,
                "b": 0.0,
                "c": 0.0,
            }
            for i in range(10)
        ] + [
            {
                "student_id": f"s{i}",
                "item_id": "q2",
                "correct": i % 3 == 0,
                "a": 1.0,
                "b": 0.5,
                "c": 0.0,
            }
            for i in range(10)
        ]

        abilities, difficulties = fit_mixed_effects(
            responses,
            max_em_iter=50,
            em_tol=1e-4,
            verbose=False,
        )

        # 수렴했으면 결과가 있어야 함
        assert len(abilities) > 0
        assert len(difficulties) == 2

        # SE가 유한해야 함
        for ability in abilities.values():
            assert ability.se < float("inf")

        for difficulty in difficulties.values():
            assert difficulty.se < float("inf")


class TestResponseData:
    """ResponseData 클래스 테스트"""

    def test_from_dict(self):
        """딕셔너리에서 생성"""
        data = {
            "student_id": "s1",
            "item_id": "q1",
            "correct": True,
            "a": 1.2,
            "b": 0.5,
            "c": 0.2,
        }

        resp = ResponseData.from_dict(data)

        assert resp.student_id == "s1"
        assert resp.item_id == "q1"
        assert resp.correct is True
        assert resp.a == 1.2
        assert resp.b == 0.5
        assert resp.c == 0.2


class TestStudentAbility:
    """StudentAbility 클래스 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        ability = StudentAbility(
            student_id="s1",
            theta=1.5,
            se=0.3,
            n_responses=10,
        )

        result = ability.to_dict()

        assert result["student_id"] == "s1"
        assert result["theta"] == 1.5
        assert result["se"] == 0.3
        assert result["n_responses"] == 10
        assert result["method"] == "mixed_effects"


class TestItemDifficulty:
    """ItemDifficulty 클래스 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        difficulty = ItemDifficulty(
            item_id="q1",
            b=0.8,
            se=0.2,
            n_responses=20,
            a=1.2,
            c=0.2,
        )

        result = difficulty.to_dict()

        assert result["item_id"] == "q1"
        assert result["b"] == 0.8
        assert result["se"] == 0.2
        assert result["n_responses"] == 20
        assert result["a"] == 1.2
        assert result["c"] == 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
