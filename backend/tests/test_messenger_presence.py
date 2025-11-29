"""
Tests for Presence System (Task 2.2)

Tests PresenceManager functionality:
- set_online / set_offline / set_away
- get_status
- get_online_users with zone/org filtering
- get_online_count
- update_activity (heartbeat)
- check_and_set_away (auto-away after 5 minutes)
- cleanup_stale_presence
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.messenger.presence import PresenceManager, PresenceStatus, get_presence_manager


@pytest.fixture
async def redis_mock():
    """Mock Redis client"""
    redis = MagicMock()

    # Mock Redis commands as async
    redis.hset = AsyncMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.zadd = AsyncMock()
    redis.zrem = AsyncMock()
    redis.zrevrange = AsyncMock(return_value=[])
    redis.zcard = AsyncMock(return_value=0)
    redis.delete = AsyncMock()
    redis.expire = AsyncMock()

    return redis


@pytest.fixture
async def pubsub_mock():
    """Mock PubSub manager"""
    pubsub = MagicMock()
    pubsub.publish_online_status = AsyncMock()
    return pubsub


@pytest.fixture
async def presence_manager(redis_mock, pubsub_mock):
    """Create PresenceManager with mocked dependencies"""
    manager = PresenceManager()
    # Replace internal redis and pubsub with mocks
    manager.redis = redis_mock
    manager.pubsub = pubsub_mock
    return manager


@pytest.mark.asyncio
async def test_set_online(presence_manager, redis_mock, pubsub_mock):
    """Test setting user online status"""
    user_id = 1
    zone_id = 10
    org_id = 100

    await presence_manager.set_online(user_id, zone_id, org_id)

    # Verify Redis hash update
    redis_mock.hset.assert_called_once()
    call_args = redis_mock.hset.call_args
    assert call_args[0][0] == f"presence:{user_id}"
    assert call_args[1]["mapping"]["status"] == "online"
    assert call_args[1]["mapping"]["zone_id"] == str(zone_id)
    assert call_args[1]["mapping"]["org_id"] == str(org_id)

    # Verify sorted set additions
    assert redis_mock.zadd.call_count == 3  # global, zone, org

    # Verify broadcast
    pubsub_mock.publish_online_status.assert_called_once_with(
        user_id, "online", metadata={"zone_id": zone_id, "org_id": org_id}
    )


@pytest.mark.asyncio
async def test_set_offline(presence_manager, redis_mock, pubsub_mock):
    """Test setting user offline status"""
    user_id = 1

    # Mock existing presence data
    redis_mock.hgetall.return_value = {
        b"status": b"online",
        b"zone_id": b"10",
        b"org_id": b"100",
    }

    await presence_manager.set_offline(user_id)

    # Verify sorted set removals
    assert redis_mock.zrem.call_count >= 1

    # Verify hash update with last_seen
    redis_mock.hset.assert_called()

    # Verify broadcast
    pubsub_mock.publish_online_status.assert_called_once()
    call_args = pubsub_mock.publish_online_status.call_args
    assert call_args[0][0] == user_id
    assert call_args[0][1] == "offline"


@pytest.mark.asyncio
async def test_set_away(presence_manager, redis_mock, pubsub_mock):
    """Test setting user away status"""
    user_id = 1

    await presence_manager.set_away(user_id)

    # Verify hash update
    redis_mock.hset.assert_called_once()
    call_args = redis_mock.hset.call_args
    assert call_args[0][0] == f"presence:{user_id}"
    assert call_args[1]["mapping"]["status"] == "away"

    # Verify broadcast
    pubsub_mock.publish_online_status.assert_called_once_with(
        user_id, "away", metadata={}
    )


@pytest.mark.asyncio
async def test_update_activity(presence_manager, redis_mock):
    """Test updating user activity timestamp (heartbeat)"""
    user_id = 1

    # Mock existing presence
    redis_mock.hgetall.return_value = {
        b"status": b"away",
        b"last_activity": b"1234567890",
    }

    await presence_manager.update_activity(user_id)

    # Verify hash update
    redis_mock.hset.assert_called_once()
    call_args = redis_mock.hset.call_args
    assert call_args[0][0] == f"presence:{user_id}"
    assert "last_activity" in call_args[1]["mapping"]
    assert call_args[1]["mapping"]["status"] == "online"  # Should revert to online


@pytest.mark.asyncio
async def test_get_status(presence_manager, redis_mock):
    """Test getting user presence status"""
    user_id = 1

    # Mock presence data
    now = datetime.utcnow()
    redis_mock.hgetall.return_value = {
        b"status": b"online",
        b"last_activity": str(int(now.timestamp())).encode(),
        b"zone_id": b"10",
        b"org_id": b"100",
    }

    status = await presence_manager.get_status(user_id)

    assert status is not None
    assert status["user_id"] == user_id
    assert status["status"] == "online"
    assert status["zone_id"] == 10
    assert status["org_id"] == 100


@pytest.mark.asyncio
async def test_get_status_not_found(presence_manager, redis_mock):
    """Test getting status for user with no presence data"""
    user_id = 999

    redis_mock.hgetall.return_value = {}

    status = await presence_manager.get_status(user_id)

    assert status is None


@pytest.mark.asyncio
async def test_get_online_users_global(presence_manager, redis_mock):
    """Test getting all online users"""
    # Mock sorted set response
    now = int(datetime.utcnow().timestamp())
    redis_mock.zrevrange.return_value = [
        (b"1", now),
        (b"2", now - 10),
        (b"3", now - 20),
    ]

    # Mock status for each user
    async def mock_get_status(user_id):
        return {
            "user_id": user_id,
            "status": "online",
            "last_activity": datetime.utcnow().isoformat(),
        }

    presence_manager.get_status = mock_get_status

    users = await presence_manager.get_online_users(limit=10)

    assert len(users) == 3
    assert users[0]["user_id"] == 1
    assert users[1]["user_id"] == 2
    assert users[2]["user_id"] == 3


@pytest.mark.asyncio
async def test_get_online_users_with_zone(presence_manager, redis_mock):
    """Test getting online users filtered by zone"""
    zone_id = 10

    redis_mock.zrevrange.return_value = [(b"1", 1234567890)]

    async def mock_get_status(user_id):
        return {"user_id": user_id, "status": "online", "zone_id": zone_id}

    presence_manager.get_status = mock_get_status

    users = await presence_manager.get_online_users(zone_id=zone_id, limit=10)

    # Verify correct key was used
    call_args = redis_mock.zrevrange.call_args
    assert call_args[0][0] == f"online:zone:{zone_id}"
    assert len(users) == 1  # Use the users variable


@pytest.mark.asyncio
async def test_get_online_count(presence_manager, redis_mock):
    """Test getting online user counts"""
    redis_mock.zcard.return_value = 42

    counts = await presence_manager.get_online_count()

    assert counts["global"] == 42


@pytest.mark.asyncio
async def test_check_and_set_away(presence_manager, redis_mock, pubsub_mock):
    """Test auto-away detection after 5 minutes of inactivity"""
    user_id = 1

    # Mock user who has been inactive for 6 minutes
    old_timestamp = int((datetime.utcnow() - timedelta(minutes=6)).timestamp())
    redis_mock.hgetall.return_value = {
        b"status": b"online",
        b"last_activity": str(old_timestamp).encode(),
    }

    result = await presence_manager.check_and_set_away(user_id)

    assert result is True

    # Verify status was updated to away
    redis_mock.hset.assert_called()
    pubsub_mock.publish_online_status.assert_called_once()


@pytest.mark.asyncio
async def test_check_and_set_away_no_change(presence_manager, redis_mock, pubsub_mock):
    """Test auto-away detection for recently active user"""
    user_id = 1

    # Mock user who was active 2 minutes ago
    recent_timestamp = int((datetime.utcnow() - timedelta(minutes=2)).timestamp())
    redis_mock.hgetall.return_value = {
        b"status": b"online",
        b"last_activity": str(recent_timestamp).encode(),
    }

    result = await presence_manager.check_and_set_away(user_id)

    assert result is False

    # Verify no status update
    pubsub_mock.publish_online_status.assert_not_called()


@pytest.mark.asyncio
async def test_cleanup_stale_presence(presence_manager, redis_mock):
    """Test cleanup of stale presence records"""
    # Mock stale users (last activity > 5 minutes ago)
    old_timestamp = int((datetime.utcnow() - timedelta(minutes=10)).timestamp())
    redis_mock.zrevrange.return_value = [
        (b"1", old_timestamp),
        (b"2", old_timestamp - 100),
    ]

    redis_mock.hgetall.return_value = {
        b"status": b"online",
        b"last_activity": str(old_timestamp).encode(),
    }

    cleanup_count = await presence_manager.cleanup_stale_presence()

    assert cleanup_count == 2

    # Verify removals from sorted sets
    assert redis_mock.zrem.call_count >= 2


@pytest.mark.asyncio
async def test_presence_manager_singleton():
    """Test that get_presence_manager returns singleton"""
    manager1 = get_presence_manager()
    manager2 = get_presence_manager()

    assert manager1 is manager2


@pytest.mark.asyncio
async def test_presence_status_enum():
    """Test PresenceStatus enum values"""
    assert PresenceStatus.ONLINE.value == "online"
    assert PresenceStatus.AWAY.value == "away"
    assert PresenceStatus.OFFLINE.value == "offline"
