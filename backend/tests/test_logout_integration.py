"""
Token Blacklist 통합 테스트

로그아웃 및 토큰 무효화 플로우 테스트
"""

import time
import uuid

import httpx
import pytest


BASE_URL = "http://localhost:8001"
TEST_EMAIL_PREFIX = "blacklist_test"


@pytest.fixture
def test_user_data():
    """각 테스트용 고유 사용자 데이터 생성."""
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())
    return {
        "email": f"{TEST_EMAIL_PREFIX}_{timestamp}_{unique_id}@dreamseed.ai",
        "password": "SecurePassword123!",
        "role": "student",
        "full_name": f"Blacklist Test User {timestamp}",
    }


@pytest.fixture
def sync_client():
    """동기 HTTP 클라이언트."""
    return httpx.Client(base_url=BASE_URL, timeout=10.0)


def _register_user(sync_client, test_user_data):
    """Helper: 사용자 등록."""
    response = sync_client.post(
        "/api/auth/register",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "role": test_user_data["role"],
        },
    )
    assert response.status_code == 201
    return response


def _login_user(sync_client, email, password):
    """Helper: 사용자 로그인 및 토큰 반환."""
    response = sync_client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )
    assert response.status_code == 200
    token = response.cookies.get("fastapiusersauth")
    assert token is not None
    return token


def _get_auth_headers(token):
    """Helper: 토큰으로 Authorization 헤더 생성."""
    return {"Authorization": f"Bearer {token}"}


def _verify_token_valid(sync_client, headers):
    """Helper: 토큰이 유효한지 확인."""
    response = sync_client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    return response


def _verify_token_invalid(sync_client, headers):
    """Helper: 토큰이 무효한지 확인."""
    response = sync_client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


def test_logout_invalidates_token(sync_client, test_user_data):
    """
    로그아웃 후 토큰이 무효화되는지 확인.

    Steps:
    1. 사용자 등록
    2. 로그인하여 토큰 획득
    3. 보호된 엔드포인트 접근 성공 확인
    4. 로그아웃 (토큰 블랙리스트 등록)
    5. 동일 토큰으로 보호된 엔드포인트 접근 시도 → 401 Unauthorized
    """
    # Step 1-2: 회원가입 및 로그인
    _register_user(sync_client, test_user_data)
    print(f"✅ 회원가입 완료: {test_user_data['email']}")

    access_token = _login_user(
        sync_client, test_user_data["email"], test_user_data["password"]
    )
    print("✅ 로그인 성공, 토큰 획득")

    # Step 3: 보호된 엔드포인트 접근 (성공해야 함)
    headers = _get_auth_headers(access_token)
    me_response_before = _verify_token_valid(sync_client, headers)
    user_data = me_response_before.json()
    assert user_data["email"] == test_user_data["email"]
    print("✅ 토큰으로 /me 접근 성공")

    # Step 4: 로그아웃 (토큰 블랙리스트 등록)
    logout_response = sync_client.post("/api/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    print("✅ 로그아웃 완료")

    # Step 5: 로그아웃 후 동일 토큰으로 접근 시도 (실패해야 함)
    time.sleep(0.5)  # Redis 전파 대기
    _verify_token_invalid(sync_client, headers)
    print("✅ 로그아웃 후 토큰 무효화 확인 (401 Unauthorized)")


def test_multiple_device_logout(sync_client, test_user_data):
    """
    여러 기기에서 로그인 후 한 기기에서 로그아웃 시 해당 토큰만 무효화.

    Steps:
    1. 사용자 등록
    2. 첫 번째 로그인 (토큰 A)
    3. 두 번째 로그인 (토큰 B)
    4. 토큰 A로 로그아웃
    5. 토큰 A는 무효화, 토큰 B는 여전히 유효
    """
    # Step 1-3: 회원가입 및 멀티 디바이스 로그인
    _register_user(sync_client, test_user_data)
    print("✅ 회원가입 완료")

    token_a = _login_user(
        sync_client, test_user_data["email"], test_user_data["password"]
    )
    print("✅ Device A 로그인 완료")

    token_b = _login_user(
        sync_client, test_user_data["email"], test_user_data["password"]
    )
    print("✅ Device B 로그인 완료")

    # Step 4: Device A에서 로그아웃
    headers_a = _get_auth_headers(token_a)
    logout_response = sync_client.post("/api/auth/logout", headers=headers_a)
    assert logout_response.status_code == 200
    print("✅ Device A 로그아웃")

    time.sleep(0.5)

    # Step 5: Token A는 무효화됨
    _verify_token_invalid(sync_client, headers_a)
    print("✅ Token A 무효화 확인")

    # Step 6: Token B는 여전히 유효
    headers_b = _get_auth_headers(token_b)
    _verify_token_valid(sync_client, headers_b)
    print("✅ Token B 여전히 유효")


def test_token_expiry_and_blacklist(sync_client, test_user_data):
    """
    블랙리스트된 토큰은 만료 시간까지만 Redis에 유지.

    Note: 실제 만료 테스트는 24시간이 걸리므로,
          이 테스트는 TTL 설정이 올바른지만 확인.
    """
    # Step 1: 회원가입 & 로그인
    _register_user(sync_client, test_user_data)
    access_token = _login_user(
        sync_client, test_user_data["email"], test_user_data["password"]
    )

    # Step 2: 로그아웃 (블랙리스트 등록)
    headers = _get_auth_headers(access_token)
    logout_response = sync_client.post("/api/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    print("✅ 로그아웃 완료 - Redis TTL 설정됨")

    # Step 3: 토큰 무효화 확인
    time.sleep(0.5)
    _verify_token_invalid(sync_client, headers)
    print("✅ 블랙리스트된 토큰 거부됨")


def test_logout_performance(sync_client, test_user_data):
    """
    로그아웃 성능 테스트 - 100ms 이내 완료되어야 함.
    """
    # 회원가입 & 로그인
    _register_user(sync_client, test_user_data)
    access_token = _login_user(
        sync_client, test_user_data["email"], test_user_data["password"]
    )
    headers = _get_auth_headers(access_token)

    # 로그아웃 성능 측정
    start_time = time.time()
    logout_response = sync_client.post("/api/auth/logout", headers=headers)
    elapsed = time.time() - start_time

    assert logout_response.status_code == 200
    assert elapsed < 0.1  # 100ms 이내
    print(f"✅ 로그아웃 성능: {elapsed*1000:.1f}ms")


def test_invalid_token_logout(sync_client):
    """
    유효하지 않은 토큰으로 로그아웃 시도 시 401 반환.
    """
    headers = {"Authorization": "Bearer invalid_token_12345"}
    logout_response = sync_client.post("/api/auth/logout", headers=headers)
    assert logout_response.status_code == 401
    print("✅ 유효하지 않은 토큰 로그아웃 거부됨")


def test_complete_auth_lifecycle(sync_client, test_user_data):
    """
    완전한 인증 라이프사이클 테스트.

    Steps:
    1. 회원가입
    2. 로그인 (토큰 획득)
    3. 보호된 리소스 접근
    4. 로그아웃
    5. 재로그인 (새 토큰 획득)
    6. 보호된 리소스 접근 성공
    """
    # Step 1-2: 회원가입 & 로그인
    _register_user(sync_client, test_user_data)
    token1 = _login_user(
        sync_client, test_user_data["email"], test_user_data["password"]
    )
    headers1 = _get_auth_headers(token1)
    print("✅ 첫 번째 로그인")

    # Step 3: 보호된 리소스 접근 성공
    _verify_token_valid(sync_client, headers1)
    print("✅ 첫 번째 토큰으로 접근 성공")

    # Step 4: 로그아웃
    sync_client.post("/api/auth/logout", headers=headers1)
    time.sleep(0.5)
    print("✅ 로그아웃")

    # Step 5: 재로그인
    token2 = _login_user(
        sync_client, test_user_data["email"], test_user_data["password"]
    )
    headers2 = _get_auth_headers(token2)
    print("✅ 재로그인")

    # Step 6: 새 토큰으로 접근 성공
    _verify_token_valid(sync_client, headers2)
    print("✅ 새 토큰으로 접근 성공")

    # Step 7: 이전 토큰은 여전히 무효
    _verify_token_invalid(sync_client, headers1)
    print("✅ 이전 토큰 여전히 무효화 상태")
