"""핵심 API 통합 테스트 - HTTP로 검증된 API만 포함"""
import uuid
from fastapi import status


class TestSubmissionFlow:
    """제출 플로우 테스트 (학생 → 문제 조회 → 답안 제출)"""
    
    def test_submit_answer_success(self, client, auth_headers, test_problem):
        """학생이 답안을 제출할 수 있음"""
        response = client.post(
            "/submissions/",
            headers=auth_headers,
            json={
                "problem_id": str(test_problem.id),
                "answer": "x = 2 또는 x = 3"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["problem_id"] == str(test_problem.id)
        assert "answer" in data
    
    def test_get_my_submissions(self, client, auth_headers, test_problem):
        """내 제출 내역 조회"""
        # 먼저 답안 제출
        client.post(
            "/submissions/",
            headers=auth_headers,
            json={
                "problem_id": str(test_problem.id),
                "answer": "Test answer"
            }
        )
        
        # 내 제출 내역 조회
        response = client.get("/submissions/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "submissions" in data
        assert len(data["submissions"]) > 0


class TestProgressTracking:
    """진행도 추적 테스트"""
    
    def test_get_my_progress(self, client, auth_headers):
        """내 진행도 조회"""
        response = client.get("/progress/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "progresses" in data
    
    def test_get_statistics(self, client, auth_headers):
        """학습 통계 조회"""
        response = client.get("/progress/statistics", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_problems_attempted" in data


class TestProblemWorkflow:
    """문제 관련 워크플로우 테스트"""
    
    def test_list_and_detail(self, client, auth_headers, test_problem):
        """문제 목록 조회 후 상세 조회"""
        # 목록 조회
        list_response = client.get("/problems/", headers=auth_headers)
        assert list_response.status_code == status.HTTP_200_OK
        problems = list_response.json()["problems"]
        assert len(problems) > 0
        
        # 첫 번째 문제 상세 조회
        problem_id = problems[0]["id"]
        detail_response = client.get(
            f"/problems/{problem_id}",
            headers=auth_headers
        )
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.json()["id"] == problem_id
