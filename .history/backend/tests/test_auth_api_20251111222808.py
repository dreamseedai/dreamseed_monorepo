"""
인증 API 단위 테스트
회원가입, 로그인, 토큰 검증, 사용자 정보 조회
"""
from fastapi import status
from faker import Faker

fake = Faker()


class TestAuthRegistration:
    """회원가입 테스트"""
    
    def test_register_success(self, client):
        """정상 회원가입"""
        unique_email = fake.email()
        response = client.post(
            "/auth/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
                "full_name": "New User",
                "role": "student"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == unique_email
        assert data["full_name"] == "New User"
        assert data["role"] == "student"
        assert data["is_active"] is True
        assert "id" in data
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client, test_student):
        """중복 이메일 회원가입 실패"""
        response = client.post(
            "/auth/register",
            json={
                "email": "student@test.com",
                "password": "password123",
                "full_name": "Duplicate User",
                "role": "student"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"]
    
    def test_register_invalid_email(self, client):
        """잘못된 이메일 형식"""
        response = client.post(
            "/auth/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "full_name": "Invalid Email User",
                "role": "student"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_short_password(self, client):
        """짧은 비밀번호 (8자 미만)"""
        response = client.post(
            "/auth/register",
            json={
                "email": "shortpass@test.com",
                "password": "short",
                "full_name": "Short Pass User",
                "role": "student"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_invalid_role(self, client):
        """잘못된 역할"""
        response = client.post(
            "/auth/register",
            json={
                "email": "invalidrole@test.com",
                "password": "password123",
                "full_name": "Invalid Role User",
                "role": "invalid_role"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthLogin:
    """로그인 테스트"""
    
    def test_login_success(self, client, test_student):
        """정상 로그인"""
        response = client.post(
            "/auth/login",
            json={
                "email": "student@test.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20
    
    def test_login_wrong_password(self, client, test_student):
        """잘못된 비밀번호"""
        response = client.post(
            "/auth/login",
            json={
                "email": "student@test.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """존재하지 않는 사용자"""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthMe:
    """사용자 정보 조회 테스트"""
    
    def test_get_me_success(self, client, auth_headers):
        """인증된 사용자 정보 조회"""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "student@test.com"
        assert data["role"] == "student"
        assert "id" in data
    
    def test_get_me_no_token(self, client):
        """토큰 없이 요청"""
        response = client.get("/auth/me")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_me_invalid_token(self, client):
        """잘못된 토큰"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthRefresh:
    """토큰 갱신 테스트"""
    
    def test_refresh_token_success(self, client, auth_headers):
        """토큰 갱신 성공"""
        response = client.post("/auth/refresh", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_unauthorized(self, client):
        """인증 없이 토큰 갱신"""
        response = client.post("/auth/refresh")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
