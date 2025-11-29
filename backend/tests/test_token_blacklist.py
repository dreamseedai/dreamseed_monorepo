"""Token blacklist service 단위 테스트."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.token_blacklist import TokenBlacklistService


@pytest.fixture
def mock_redis():
    """Mock Redis 클라이언트."""
    redis = AsyncMock()
    redis.setex = AsyncMock(return_value=True)
    redis.exists = AsyncMock(return_value=0)
    redis.delete = AsyncMock(return_value=1)
    redis.scan = AsyncMock(return_value=(0, []))
    return redis


@pytest.fixture
def blacklist_service(mock_redis):
    """TokenBlacklistService 인스턴스."""
    return TokenBlacklistService(mock_redis)


@pytest.mark.asyncio
async def test_blacklist_token_success(blacklist_service, mock_redis):
    """토큰 블랙리스트 등록 성공."""
    jti = "test-jti-123"
    expires_at = datetime.utcnow() + timedelta(hours=1)

    result = await blacklist_service.blacklist_token(jti, expires_at)

    assert result is True
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == f"blacklist:token:{jti}"
    assert call_args[0][1] > 0  # TTL should be positive
    assert call_args[0][2] == "blacklisted"


@pytest.mark.asyncio
async def test_blacklist_token_already_expired(blacklist_service, mock_redis):
    """이미 만료된 토큰 블랙리스트 등록 시 즉시 성공."""
    jti = "test-jti-expired"
    expires_at = datetime.utcnow() - timedelta(hours=1)  # 이미 만료됨

    result = await blacklist_service.blacklist_token(jti, expires_at)

    assert result is True
    mock_redis.setex.assert_not_called()  # 이미 만료되어 Redis에 저장 안함


@pytest.mark.asyncio
async def test_is_blacklisted_true(blacklist_service, mock_redis):
    """블랙리스트된 토큰 확인."""
    jti = "test-jti-blacklisted"
    mock_redis.exists.return_value = 1  # 존재함

    result = await blacklist_service.is_blacklisted(jti)

    assert result is True
    mock_redis.exists.assert_called_once_with(f"blacklist:token:{jti}")


@pytest.mark.asyncio
async def test_is_blacklisted_false(blacklist_service, mock_redis):
    """블랙리스트되지 않은 토큰 확인."""
    jti = "test-jti-valid"
    mock_redis.exists.return_value = 0  # 존재하지 않음

    result = await blacklist_service.is_blacklisted(jti)

    assert result is False
    mock_redis.exists.assert_called_once_with(f"blacklist:token:{jti}")


@pytest.mark.asyncio
async def test_blacklist_user_tokens(blacklist_service, mock_redis):
    """사용자 전체 토큰 블랙리스트 등록."""
    user_id = 123
    expires_at = datetime.utcnow() + timedelta(minutes=30)

    result = await blacklist_service.blacklist_user_tokens(user_id, expires_at)

    assert result is True
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == f"blacklist:user:{user_id}"
    assert call_args[0][1] > 0


@pytest.mark.asyncio
async def test_blacklist_user_tokens_default_expiry(blacklist_service, mock_redis):
    """사용자 토큰 블랙리스트 - 기본 만료 시간 사용."""
    user_id = 456

    result = await blacklist_service.blacklist_user_tokens(user_id)

    assert result is True
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_is_user_blacklisted_true(blacklist_service, mock_redis):
    """사용자 블랙리스트 확인 - 블랙리스트됨."""
    user_id = 789
    mock_redis.exists.return_value = 1

    result = await blacklist_service.is_user_blacklisted(user_id)

    assert result is True
    mock_redis.exists.assert_called_once_with(f"blacklist:user:{user_id}")


@pytest.mark.asyncio
async def test_is_user_blacklisted_false(blacklist_service, mock_redis):
    """사용자 블랙리스트 확인 - 블랙리스트 안됨."""
    user_id = 999
    mock_redis.exists.return_value = 0

    result = await blacklist_service.is_user_blacklisted(user_id)

    assert result is False


@pytest.mark.asyncio
async def test_remove_from_blacklist(blacklist_service, mock_redis):
    """블랙리스트에서 토큰 제거."""
    jti = "test-jti-remove"

    result = await blacklist_service.remove_from_blacklist(jti)

    assert result is True
    mock_redis.delete.assert_called_once_with(f"blacklist:token:{jti}")


@pytest.mark.asyncio
async def test_get_blacklist_count_empty(blacklist_service, mock_redis):
    """블랙리스트 카운트 - 빈 경우."""
    mock_redis.scan.return_value = (0, [])

    count = await blacklist_service.get_blacklist_count()

    assert count == 0


@pytest.mark.asyncio
async def test_get_blacklist_count_with_tokens(blacklist_service, mock_redis):
    """블랙리스트 카운트 - 토큰이 있는 경우."""
    # 첫 번째 scan 호출: cursor 1 반환, 3개 키
    # 두 번째 scan 호출: cursor 0 반환 (종료), 2개 키
    mock_redis.scan.side_effect = [
        (1, ["blacklist:token:1", "blacklist:token:2", "blacklist:token:3"]),
        (0, ["blacklist:token:4", "blacklist:token:5"]),
    ]

    count = await blacklist_service.get_blacklist_count()

    assert count == 5
    assert mock_redis.scan.call_count == 2


@pytest.mark.asyncio
async def test_ttl_calculation(blacklist_service, mock_redis):
    """TTL 계산 정확성 확인."""
    jti = "test-jti-ttl"
    expires_at = datetime.utcnow() + timedelta(seconds=3600)

    await blacklist_service.blacklist_token(jti, expires_at)

    call_args = mock_redis.setex.call_args
    ttl = call_args[0][1]

    # TTL은 3600초에 가까워야 함 (약간의 오차 허용)
    assert 3595 <= ttl <= 3600


@pytest.mark.asyncio
async def test_concurrent_blacklist_operations(blacklist_service, mock_redis):
    """동시 블랙리스트 작업 처리."""
    import asyncio

    jti_list = [f"jti-{i}" for i in range(10)]
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # 10개 토큰 동시 블랙리스트 등록
    tasks = [blacklist_service.blacklist_token(jti, expires_at) for jti in jti_list]
    results = await asyncio.gather(*tasks)

    assert all(results)
    assert mock_redis.setex.call_count == 10
