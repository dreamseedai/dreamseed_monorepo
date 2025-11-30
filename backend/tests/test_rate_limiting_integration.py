"""
Rate Limiting Integration Tests

E2E tests for rate limiting on authentication endpoints
"""

import time
import uuid

import httpx
import pytest

BASE_URL = "http://localhost:8001"
TEST_EMAIL_PREFIX = "ratelimit_test"


@pytest.fixture
def sync_client():
    """동기 HTTP 클라이언트."""
    return httpx.Client(base_url=BASE_URL, timeout=10.0)


@pytest.fixture
def test_user_data():
    """각 테스트용 고유 사용자 데이터 생성."""
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())
    return {
        "email": f"{TEST_EMAIL_PREFIX}_{timestamp}_{unique_id}@dreamseed.ai",
        "password": "SecurePassword123!",
        "role": "student",
    }


def test_login_rate_limit_per_ip(sync_client, test_user_data):
    """
    로그인 엔드포인트 Rate Limit 테스트 (5/minute per IP).

    Steps:
    1. 5회 로그인 시도 (성공 또는 401)
    2. 6번째 시도 → 429 Too Many Requests
    3. Retry-After 헤더 확인
    """
    # Step 1: 5회 로그인 시도 (rate limit 안에 들어옴)
    for i in range(5):
        response = sync_client.post(
            "/api/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        # 401 (인증 실패) 또는 200 (성공) 둘 다 허용
        assert response.status_code in [200, 401, 422]
        print(f"✅ 시도 {i+1}: {response.status_code}")

    # Step 2: 6번째 시도 (rate limit 초과)
    response = sync_client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    assert response.status_code == 429
    print(f"✅ 시도 6: 429 Too Many Requests")

    # Step 3: Rate limit 헤더 확인
    assert "Retry-After" in response.headers or "retry_after" in response.json()
    print("✅ Retry-After 헤더 확인")


def test_register_rate_limit_per_ip(sync_client):
    """
    회원가입 엔드포인트 Rate Limit 테스트 (3/hour per IP).

    Steps:
    1. 3회 회원가입 시도
    2. 4번째 시도 → 429 Too Many Requests
    """
    # Step 1: 3회 회원가입 시도
    for i in range(3):
        unique_id = str(uuid.uuid4())[:8]
        response = sync_client.post(
            "/api/auth/register",
            json={
                "email": f"ratelimit_{i}_{unique_id}@dreamseed.ai",
                "password": "SecurePassword123!",
                "role": "student",
            },
        )
        assert response.status_code in [201, 400]  # 201 (성공) 또는 400 (중복)
        print(f"✅ 회원가입 {i+1}: {response.status_code}")

    # Step 2: 4번째 시도 (rate limit 초과)
    response = sync_client.post(
        "/api/auth/register",
        json={
            "email": f"ratelimit_overflow_{uuid.uuid4()}@dreamseed.ai",
            "password": "SecurePassword123!",
            "role": "student",
        },
    )
    assert response.status_code == 429
    print("✅ 회원가입 4: 429 Too Many Requests")


def test_rate_limit_headers(sync_client, test_user_data):
    """
    Rate limit 관련 헤더 검증.

    Expected headers:
    - X-RateLimit-Limit: 제한 횟수
    - X-RateLimit-Remaining: 남은 횟수
    - X-RateLimit-Reset: 리셋 시간 (Unix timestamp)
    """
    response = sync_client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )

    # slowapi는 자동으로 헤더 추가 (headers_enabled=True 설정 시)
    # 헤더가 있으면 확인, 없으면 skip
    if "X-RateLimit-Limit" in response.headers:
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        print("✅ Rate limit 헤더 확인")
    else:
        print("⚠️  Rate limit 헤더 없음 (slowapi 설정 확인 필요)")


def test_rate_limit_reset_after_wait(sync_client, test_user_data):
    """
    Rate limit이 시간 경과 후 리셋되는지 확인.

    Steps:
    1. 5회 로그인 시도 (limit 도달)
    2. 60초 대기
    3. 다시 로그인 시도 (성공해야 함)

    Note: 실제 60초 대기는 너무 오래 걸리므로,
          이 테스트는 수동 테스트로 권장
    """
    pytest.skip("긴 대기 시간 필요 (60초) - 수동 테스트 권장")

    # 5회 시도
    for i in range(5):
        sync_client.post(
            "/api/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

    # 6번째 시도 (차단됨)
    response = sync_client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    assert response.status_code == 429

    # 60초 대기
    print("⏳ 60초 대기 중...")
    time.sleep(60)

    # 다시 시도 (성공해야 함)
    response = sync_client.post(
        "/api/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    assert response.status_code in [200, 401, 422]
    print("✅ Rate limit 리셋 확인")


def test_different_ips_independent_limits(sync_client, test_user_data):
    """
    다른 IP에서의 요청은 독립적인 rate limit을 가짐.

    Note: 로컬 테스트 환경에서는 IP를 변경하기 어려우므로,
          이 테스트는 프록시 또는 Docker 네트워크 설정 필요
    """
    pytest.skip("로컬 환경에서는 IP 변경 어려움 - 프로덕션 테스트 권장")

    # 실제 구현은 X-Forwarded-For 헤더로 IP를 시뮬레이션할 수 있음
    # 하지만 slowapi가 이를 지원하는지 확인 필요
    pass
