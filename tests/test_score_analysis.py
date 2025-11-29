"""Tests for Score Analysis Service

성적 분석 서비스 테스트
====================

이 테스트는 성적 분석 서비스의 다음 기능을 검증합니다:
1. IRT 기반 능력 추정
2. 혼합효과 모형 기반 능력 추정
3. 토픽별 분석
4. 학습 추천 생성
5. 성장 예측
6. 비교 기준 계산
"""

import pytest
from adaptive_engine.services.score_analysis import (
    ScoreAnalysisService,
    AnalysisEngine,
    TopicInsight,
    Recommendation,
)


class TestScoreAnalysisService:
    """성적 분석 서비스 테스트"""
    
    def test_irt_estimation(self):
        """IRT 기반 능력 추정"""
        service = ScoreAnalysisService(engine="irt")
        
        responses = [
            {"item_id": "q1", "correct": True, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"},
            {"item_id": "q2", "correct": True, "a": 1.0, "b": 0.5, "c": 0.0, "topic": "대수"},
            {"item_id": "q3", "correct": False, "a": 1.0, "b": 1.5, "c": 0.0, "topic": "기하"},
        ]
        
        report = service.generate_report(
            student_id="s1",
            session_id="session1",
            responses=responses,
        )
        
        assert report.student_id == "s1"
        assert report.session_id == "session1"
        assert report.engine_used == "irt"
        assert report.n_items == 3
        assert report.n_correct == 2
        assert abs(report.overall_accuracy - 2/3) < 0.01
        assert report.theta > 0  # 3문항 중 2개 정답이므로 양수
        
    def test_mixed_effects_estimation(self):
        """혼합효과 모형 기반 능력 추정"""
        service = ScoreAnalysisService(engine="mixed_effects", min_responses_for_mixed=4)
        
        # 여러 학생의 응답 (혼합효과 모형용)
        all_responses = [
            {"student_id": "s1", "item_id": "q1", "correct": True, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"},
            {"student_id": "s1", "item_id": "q2", "correct": False, "a": 1.0, "b": 1.0, "c": 0.0, "topic": "기하"},
            {"student_id": "s2", "item_id": "q1", "correct": True, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"},
            {"student_id": "s2", "item_id": "q2", "correct": True, "a": 1.0, "b": 1.0, "c": 0.0, "topic": "기하"},
        ]
        
        s1_responses = [r for r in all_responses if r["student_id"] == "s1"]
        
        report = service.generate_report(
            student_id="s1",
            session_id="session1",
            responses=s1_responses,
            all_responses=all_responses,
        )
        
        assert report.student_id == "s1"
        assert report.engine_used in ["mixed_effects", "irt_fallback"]
        assert report.theta is not None
        
    def test_hybrid_engine_selection(self):
        """Hybrid 엔진 자동 선택"""
        service = ScoreAnalysisService(engine="hybrid", min_responses_for_mixed=10)
        
        # 적은 응답: IRT 사용
        few_responses = [
            {"item_id": f"q{i}", "correct": True, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"}
            for i in range(5)
        ]
        
        engine = service._decide_engine(len(few_responses))
        assert engine == AnalysisEngine.IRT
        
        # 많은 응답: 혼합효과 모형 사용
        many_responses = [
            {"item_id": f"q{i}", "correct": True, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"}
            for i in range(15)
        ]
        
        engine = service._decide_engine(len(many_responses))
        assert engine == AnalysisEngine.MIXED_EFFECTS
        
    def test_topic_analysis(self):
        """토픽별 분석"""
        service = ScoreAnalysisService(engine="irt")
        
        responses = [
            {"item_id": "q1", "correct": True, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"},
            {"item_id": "q2", "correct": True, "a": 1.0, "b": 0.5, "c": 0.0, "topic": "대수"},
            {"item_id": "q3", "correct": False, "a": 1.0, "b": 1.0, "c": 0.0, "topic": "기하"},
            {"item_id": "q4", "correct": False, "a": 1.0, "b": 1.2, "c": 0.0, "topic": "기하"},
        ]
        
        report = service.generate_report(
            student_id="s1",
            session_id="session1",
            responses=responses,
        )
        
        # 토픽 인사이트 확인
        assert len(report.topic_insights) == 2
        
        topic_map = {t.topic: t for t in report.topic_insights}
        assert "대수" in topic_map
        assert "기하" in topic_map
        
        # 대수: 2/2 = 100%
        assert topic_map["대수"].n_items == 2
        assert topic_map["대수"].n_correct == 2
        assert topic_map["대수"].accuracy == 1.0
        assert topic_map["대수"].strength_level == "strong"
        
        # 기하: 0/2 = 0%
        assert topic_map["기하"].n_items == 2
        assert topic_map["기하"].n_correct == 0
        assert topic_map["기하"].accuracy == 0.0
        assert topic_map["기하"].strength_level == "weak"
        
    def test_recommendations(self):
        """학습 추천 생성"""
        service = ScoreAnalysisService(engine="irt")
        
        responses = [
            {"item_id": "q1", "correct": False, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"},
            {"item_id": "q2", "correct": False, "a": 1.0, "b": 0.5, "c": 0.0, "topic": "대수"},
            {"item_id": "q3", "correct": True, "a": 1.0, "b": 1.0, "c": 0.0, "topic": "기하"},
            {"item_id": "q4", "correct": True, "a": 1.0, "b": 1.2, "c": 0.0, "topic": "기하"},
        ]
        
        report = service.generate_report(
            student_id="s1",
            session_id="session1",
            responses=responses,
        )
        
        # 추천 확인
        assert len(report.recommendations) > 0
        
        # 약점 토픽(대수)에 대한 추천이 있어야 함
        topics_recommended = [r.topic for r in report.recommendations]
        assert "대수" in topics_recommended
        
        # 개념 복습 또는 연습 추천이 있어야 함
        rec_types = [r.type for r in report.recommendations]
        assert "concept" in rec_types or "practice" in rec_types
        
    def test_growth_forecast(self):
        """성장 예측"""
        service = ScoreAnalysisService(engine="irt", scale_A=100.0, scale_B=500.0)
        
        responses = [
            {"item_id": f"q{i}", "correct": i % 2 == 0, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"}
            for i in range(10)
        ]
        
        report = service.generate_report(
            student_id="s1",
            session_id="session1",
            responses=responses,
            include_forecast=True,
        )
        
        assert report.growth_forecast is not None
        assert report.growth_forecast.current_score is not None
        assert len(report.growth_forecast.forecast_steps) == 5
        
        # 예측 점수가 증가 추세여야 함
        scores = [step["score"] for step in report.growth_forecast.forecast_steps]
        assert scores[0] < scores[-1] or abs(scores[0] - scores[-1]) < 10
        
    def test_benchmark(self):
        """비교 기준 계산"""
        service = ScoreAnalysisService(engine="irt")
        
        responses = [
            {"item_id": f"q{i}", "correct": True, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"}
            for i in range(5)
        ]
        
        report = service.generate_report(
            student_id="s1",
            session_id="session1",
            responses=responses,
            include_benchmark=True,
        )
        
        assert report.benchmark is not None
        assert 0.0 <= report.benchmark.percentile <= 1.0
        assert report.benchmark.rank_description is not None
        assert report.benchmark.next_goal is not None
        
        # 모든 문항을 맞혔으므로 백분위가 높아야 함
        assert report.benchmark.percentile > 0.5
        
    def test_scaled_score(self):
        """척도 점수 변환"""
        service = ScoreAnalysisService(engine="irt", scale_A=100.0, scale_B=500.0)
        
        responses = [
            {"item_id": "q1", "correct": True, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"},
        ]
        
        report = service.generate_report(
            student_id="s1",
            session_id="session1",
            responses=responses,
        )
        
        assert report.scaled_score is not None
        # theta ≈ 2.0, scaled = 100 * 2.0 + 500 = 700
        assert 400 <= report.scaled_score <= 800
        
    def test_empty_responses_error(self):
        """빈 응답 에러 처리"""
        service = ScoreAnalysisService(engine="irt")
        
        with pytest.raises(ValueError, match="No responses provided"):
            service.generate_report(
                student_id="s1",
                session_id="session1",
                responses=[],
            )
            
    def test_report_serialization(self):
        """리포트 직렬화"""
        service = ScoreAnalysisService(engine="irt")
        
        responses = [
            {"item_id": "q1", "correct": True, "a": 1.0, "b": 0.0, "c": 0.0, "topic": "대수"},
        ]
        
        report = service.generate_report(
            student_id="s1",
            session_id="session1",
            responses=responses,
        )
        
        # 딕셔너리 변환
        data = report.to_dict()
        
        assert data["student_id"] == "s1"
        assert data["session_id"] == "session1"
        assert "ability" in data
        assert "topic_insights" in data
        assert "recommendations" in data
        assert "summary" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

