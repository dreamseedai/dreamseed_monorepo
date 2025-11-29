"""문제 API 단위 테스트"""
import uuid
from fastapi import status


class TestProblemCreate:
    """문제 생성 API 테스트"""
    
    def test_create_success_as_teacher(self, client, teacher_auth_headers):
        """교사는 문제를 생성할 수 있음"""
        response = client.post(
            "/problems/",
            headers=teacher_auth_headers,
            json={
                "title": "Test Problem",
                "content": "This is a test problem",
                "difficulty": 5,
                "category": "algebra",
                "metadata": {"max_score": 100}
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Test Problem"
        assert data["category"] == "algebra"
        assert data["difficulty"] == 5
    
    def test_create_success_as_admin(self, client, test_admin):
        """관리자도 문제를 생성할 수 있음"""
        from app.routers.auth import create_access_token
        token = create_access_token(data={"sub": test_admin.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post(
            "/problems/",
            headers=headers,
            json={
                "title": "Admin Problem",
                "content": "Admin created problem",
                "difficulty": 7,
                "category": "geometry"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_forbidden_as_student(self, client, auth_headers):
        """학생은 문제를 생성할 수 없음"""
        response = client.post(
            "/problems/",
            headers=auth_headers,
            json={
                "title": "Student Problem",
                "content": "Should fail",
                "difficulty": 5,
                "category": "algebra"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_invalid_difficulty(self, client, teacher_auth_headers):
        """난이도는 1-10 범위여야 함"""
        response = client.post(
            "/problems/",
            headers=teacher_auth_headers,
            json={
                "title": "Invalid Problem",
                "content": "Invalid difficulty",
                "difficulty": 15,
                "category": "algebra"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestProblemList:
    """문제 목록 API 테스트"""
    
    def test_list_success(self, client, auth_headers, test_problem):
        """문제 목록 조회 성공"""
        response = client.get("/problems/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "problems" in data
        assert "total" in data
        assert len(data["problems"]) > 0
    
    def test_list_pagination(self, client, auth_headers, test_problem):
        """페이징 동작 확인"""
        response = client.get(
            "/problems/",
            headers=auth_headers,
            params={"skip": 0, "limit": 5}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["problems"]) <= 5
    
    def test_list_filter_by_difficulty(self, client, auth_headers, test_problem):
        """난이도 필터링"""
        response = client.get(
            "/problems/",
            headers=auth_headers,
            params={"difficulty": 5}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for item in data["items"]:
            assert item["difficulty"] == 5
    
    def test_list_requires_auth(self, client):
        """인증 없이는 조회 불가"""
        response = client.get("/problems/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProblemDetail:
    """문제 상세 조회 API 테스트"""
    
    def test_detail_success(self, client, auth_headers, test_problem):
        """문제 상세 조회 성공"""
        response = client.get(
            f"/problems/{test_problem.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_problem.id)
        assert data["title"] == test_problem.title
    
    def test_detail_not_found(self, client, auth_headers):
        """존재하지 않는 문제"""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/problems/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProblemUpdate:
    """문제 수정 API 테스트"""
    
    def test_update_success(self, client, teacher_auth_headers, test_problem):
        """문제 수정 성공"""
        response = client.put(
            f"/problems/{test_problem.id}",
            headers=teacher_auth_headers,
            json={
                "title": "Updated Title",
                "content": test_problem.content,
                "difficulty": test_problem.difficulty,
                "category": test_problem.category
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
    
    def test_update_forbidden_as_student(self, client, auth_headers, test_problem):
        """학생은 문제를 수정할 수 없음"""
        response = client.put(
            f"/problems/{test_problem.id}",
            headers=auth_headers,
            json={
                "title": "Hacked",
                "content": "Should fail",
                "difficulty": 1,
                "category": "algebra"
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_not_found(self, client, teacher_auth_headers):
        """존재하지 않는 문제 수정 시도"""
        fake_id = str(uuid.uuid4())
        response = client.put(
            f"/problems/{fake_id}",
            headers=teacher_auth_headers,
            json={
                "title": "New Title",
                "content": "Content",
                "difficulty": 5,
                "category": "algebra"
            }
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProblemDelete:
    """문제 삭제 API 테스트"""
    
    def test_delete_success_as_admin(self, client, test_admin, test_problem):
        """관리자는 문제를 삭제할 수 있음"""
        from app.routers.auth import create_access_token
        token = create_access_token(data={"sub": test_admin.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.delete(
            f"/problems/{test_problem.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_delete_forbidden_as_teacher(self, client, teacher_auth_headers, test_problem):
        """교사는 문제를 삭제할 수 없음"""
        response = client.delete(
            f"/problems/{test_problem.id}",
            headers=teacher_auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_not_found(self, client, test_admin):
        """존재하지 않는 문제 삭제 시도"""
        from app.routers.auth import create_access_token
        token = create_access_token(data={"sub": test_admin.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/problems/{fake_id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
