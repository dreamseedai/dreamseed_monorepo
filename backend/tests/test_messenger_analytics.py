"""
Tests for Analytics Service

Test Coverage:
1. Message statistics (total, by type, senders)
2. Message timeline (hourly, daily, weekly, monthly)
3. Top senders
4. User activity stats
5. Active users count
6. User engagement metrics
7. Conversation stats
8. Top conversations
9. Event tracking
10. Caching
11. Dashboard summary
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.messenger.analytics import (
    AnalyticsEventType,
    AnalyticsService,
    TimeInterval,
    get_analytics_service,
)


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.lpush = AsyncMock()
    redis.ltrim = AsyncMock()
    return redis


@pytest.fixture
def analytics_service(mock_redis):
    """Create AnalyticsService with mocked Redis"""
    return AnalyticsService(redis_client=mock_redis)


@pytest.fixture
async def test_users(db_session: AsyncSession):
    """Create test users"""
    from app.models.user import User

    users = [
        User(
            id=100,
            email="user1@example.com",
            username="user1",
            hashed_password="hashed_password",
        ),
        User(
            id=101,
            email="user2@example.com",
            username="user2",
            hashed_password="hashed_password",
        ),
        User(
            id=102,
            email="user3@example.com",
            username="user3",
            hashed_password="hashed_password",
        ),
    ]

    for user in users:
        db_session.add(user)

    await db_session.commit()

    return users


@pytest.fixture
async def test_conversation(db_session: AsyncSession, test_users):
    """Create test conversation"""
    from app.models.messenger_models import Conversation, ConversationParticipant

    conversation = Conversation(
        id=uuid.uuid4(),
        type="group",
        title="Test Group",
        created_by=test_users[0].id,
    )

    db_session.add(conversation)
    await db_session.commit()

    # Add participants
    for user in test_users:
        participant = ConversationParticipant(
            conversation_id=conversation.id,
            user_id=user.id,
            role="admin" if user.id == test_users[0].id else "member",
        )
        db_session.add(participant)

    await db_session.commit()

    return conversation


@pytest.fixture
async def test_messages(db_session: AsyncSession, test_conversation, test_users):
    """Create test messages"""
    from app.models.messenger_models import Message

    messages = []

    # User 1: 5 text messages
    for i in range(5):
        msg = Message(
            conversation_id=test_conversation.id,
            sender_id=test_users[0].id,
            content=f"Test message {i} from user1",
            message_type="text",
            created_at=datetime.utcnow() - timedelta(days=i),
        )
        db_session.add(msg)
        messages.append(msg)

    # User 2: 3 text messages, 1 image
    for i in range(3):
        msg = Message(
            conversation_id=test_conversation.id,
            sender_id=test_users[1].id,
            content=f"Test message {i} from user2",
            message_type="text",
            created_at=datetime.utcnow() - timedelta(days=i + 1),
        )
        db_session.add(msg)
        messages.append(msg)

    image_msg = Message(
        conversation_id=test_conversation.id,
        sender_id=test_users[1].id,
        content="",
        message_type="image",
        file_url="https://example.com/image.jpg",
        created_at=datetime.utcnow() - timedelta(days=2),
    )
    db_session.add(image_msg)
    messages.append(image_msg)

    # User 3: 2 text messages
    for i in range(2):
        msg = Message(
            conversation_id=test_conversation.id,
            sender_id=test_users[2].id,
            content=f"Test message {i} from user3",
            message_type="text",
            created_at=datetime.utcnow() - timedelta(days=i + 2),
        )
        db_session.add(msg)
        messages.append(msg)

    await db_session.commit()

    return messages


# ============================================================================
# Message Statistics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_message_stats(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_messages,
):
    """Test getting message statistics"""
    stats = await analytics_service.get_message_stats(db=db_session)

    assert stats["total_messages"] == 11
    assert stats["text_messages"] == 10
    assert stats["image_messages"] == 1
    assert stats["file_messages"] == 0
    assert stats["system_messages"] == 0
    assert stats["unique_senders"] == 3
    assert "message_type_distribution" in stats


@pytest.mark.asyncio
async def test_get_message_stats_filtered_by_conversation(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_conversation,
    test_messages,
):
    """Test filtering message stats by conversation"""
    stats = await analytics_service.get_message_stats(
        db=db_session, conversation_id=str(test_conversation.id)
    )

    assert stats["total_messages"] == 11
    assert stats["unique_senders"] == 3


@pytest.mark.asyncio
async def test_get_message_stats_filtered_by_user(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_users,
    test_messages,
):
    """Test filtering message stats by user"""
    stats = await analytics_service.get_message_stats(
        db=db_session, user_id=test_users[0].id
    )

    assert stats["total_messages"] == 5
    assert stats["unique_senders"] == 1


@pytest.mark.asyncio
async def test_get_message_stats_with_date_range(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_messages,
):
    """Test filtering message stats by date range"""
    start_date = datetime.utcnow() - timedelta(days=2)
    end_date = datetime.utcnow()

    stats = await analytics_service.get_message_stats(
        db=db_session, start_date=start_date, end_date=end_date
    )

    # Should include messages from last 2 days
    assert stats["total_messages"] > 0
    assert stats["total_messages"] <= 11


# ============================================================================
# Message Timeline Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_message_timeline_daily(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_messages,
):
    """Test getting daily message timeline"""
    timeline = await analytics_service.get_message_timeline(
        db=db_session, interval=TimeInterval.DAILY, days=7
    )

    assert isinstance(timeline, list)
    assert len(timeline) > 0
    assert "timestamp" in timeline[0]
    assert "count" in timeline[0]


@pytest.mark.asyncio
async def test_get_message_timeline_weekly(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_messages,
):
    """Test getting weekly message timeline"""
    timeline = await analytics_service.get_message_timeline(
        db=db_session, interval=TimeInterval.WEEKLY, days=30
    )

    assert isinstance(timeline, list)


@pytest.mark.asyncio
async def test_get_message_timeline_filtered(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_conversation,
    test_messages,
):
    """Test filtering timeline by conversation"""
    timeline = await analytics_service.get_message_timeline(
        db=db_session,
        interval=TimeInterval.DAILY,
        conversation_id=str(test_conversation.id),
        days=7,
    )

    assert isinstance(timeline, list)


# ============================================================================
# Top Senders Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_top_senders(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_users,
    test_messages,
):
    """Test getting top message senders"""
    top_senders = await analytics_service.get_top_senders(
        db=db_session, limit=3, days=30
    )

    assert len(top_senders) == 3
    assert top_senders[0]["user_id"] == test_users[0].id
    assert top_senders[0]["message_count"] == 5
    assert top_senders[1]["user_id"] == test_users[1].id
    assert top_senders[1]["message_count"] == 4


@pytest.mark.asyncio
async def test_get_top_senders_with_limit(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_messages,
):
    """Test limiting top senders results"""
    top_senders = await analytics_service.get_top_senders(
        db=db_session, limit=2, days=30
    )

    assert len(top_senders) == 2


@pytest.mark.asyncio
async def test_get_top_senders_filtered(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_conversation,
    test_messages,
):
    """Test filtering top senders by conversation"""
    top_senders = await analytics_service.get_top_senders(
        db=db_session, conversation_id=str(test_conversation.id), limit=3, days=30
    )

    assert len(top_senders) == 3


# ============================================================================
# User Activity Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_activity_stats(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_users,
    test_messages,
):
    """Test getting user activity statistics"""
    stats = await analytics_service.get_user_activity_stats(
        db=db_session, user_id=test_users[0].id, days=30
    )

    assert stats["user_id"] == test_users[0].id
    assert stats["messages_sent"] == 5
    assert stats["active_conversations"] == 1
    assert "avg_messages_per_day" in stats
    assert "first_message_date" in stats
    assert "last_activity_date" in stats


@pytest.mark.asyncio
async def test_get_user_activity_stats_no_activity(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
):
    """Test user stats with no activity"""
    stats = await analytics_service.get_user_activity_stats(
        db=db_session, user_id=999, days=30
    )

    assert stats["messages_sent"] == 0
    assert stats["active_conversations"] == 0


# ============================================================================
# Active Users Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_active_users_count(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_messages,
):
    """Test getting active users count"""
    result = await analytics_service.get_active_users_count(db=db_session, hours=24)

    assert "active_users" in result
    assert "period_hours" in result
    assert result["period_hours"] == 24
    assert result["active_users"] >= 0


# ============================================================================
# Engagement Metrics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_engagement_metrics(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_users,
    test_messages,
):
    """Test getting user engagement metrics"""
    metrics = await analytics_service.get_user_engagement_metrics(db=db_session, days=7)

    assert "total_users" in metrics
    assert "active_users" in metrics
    assert "engaged_users" in metrics
    assert "engagement_rate" in metrics
    assert "deep_engagement_rate" in metrics
    assert metrics["total_users"] >= 3


# ============================================================================
# Conversation Stats Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_conversation_stats(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_conversation,
    test_messages,
):
    """Test getting conversation statistics"""
    stats = await analytics_service.get_conversation_stats(
        db=db_session, conversation_id=str(test_conversation.id)
    )

    assert stats["conversation_id"] == str(test_conversation.id)
    assert stats["type"] == "group"
    assert stats["title"] == "Test Group"
    assert stats["participant_count"] == 3
    assert stats["active_participants"] == 3
    assert stats["message_count"] == 11
    assert "messages_per_day" in stats
    assert "conversation_age_days" in stats


@pytest.mark.asyncio
async def test_get_conversation_stats_not_found(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
):
    """Test getting stats for non-existent conversation"""
    stats = await analytics_service.get_conversation_stats(
        db=db_session, conversation_id=str(uuid.uuid4())
    )

    assert "error" in stats


# ============================================================================
# Top Conversations Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_top_conversations(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_conversation,
    test_messages,
):
    """Test getting top conversations"""
    conversations = await analytics_service.get_top_conversations(
        db=db_session, limit=10, days=30, sort_by="messages"
    )

    assert isinstance(conversations, list)
    assert len(conversations) >= 1
    if len(conversations) > 0:
        assert "conversation_id" in conversations[0]
        assert "message_count" in conversations[0]


# ============================================================================
# Event Tracking Tests
# ============================================================================


@pytest.mark.asyncio
async def test_track_event(
    analytics_service: AnalyticsService,
    mock_redis,
):
    """Test tracking analytics event"""
    await analytics_service.track_event(
        event_type=AnalyticsEventType.MESSAGE_SENT,
        user_id=123,
        conversation_id="test-conv-id",
        metadata={"message_type": "text"},
    )

    # Verify Redis was called
    mock_redis.lpush.assert_called_once()
    mock_redis.ltrim.assert_called_once()


@pytest.mark.asyncio
async def test_track_event_no_redis(
    db_session: AsyncSession,
):
    """Test event tracking without Redis (should not fail)"""
    service = AnalyticsService(redis_client=None)

    # Should not raise exception
    await service.track_event(
        event_type=AnalyticsEventType.MESSAGE_SENT,
        user_id=123,
    )


# ============================================================================
# Caching Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_cached_stats(
    analytics_service: AnalyticsService,
    mock_redis,
):
    """Test getting cached statistics"""
    import json

    mock_data = {"test": "data"}
    mock_redis.get = AsyncMock(return_value=json.dumps(mock_data))

    result = await analytics_service.get_cached_stats("test_key")

    assert result == mock_data
    mock_redis.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_set_cached_stats(
    analytics_service: AnalyticsService,
    mock_redis,
):
    """Test setting cached statistics"""
    test_data = {"test": "data"}

    await analytics_service.set_cached_stats("test_key", test_data, ttl=300)

    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_caching_no_redis(
    db_session: AsyncSession,
):
    """Test caching without Redis (should not fail)"""
    service = AnalyticsService(redis_client=None)

    # Should return None without error
    result = await service.get_cached_stats("test_key")
    assert result is None

    # Should not raise exception
    await service.set_cached_stats("test_key", {"data": "test"})


# ============================================================================
# Dashboard Summary Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_dashboard_summary(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    test_messages,
):
    """Test getting dashboard summary"""
    summary = await analytics_service.get_dashboard_summary(db=db_session, days=7)

    assert "period_days" in summary
    assert "generated_at" in summary
    assert "message_stats" in summary
    assert "engagement_metrics" in summary
    assert "active_users_24h" in summary
    assert "top_senders" in summary
    assert "message_timeline" in summary


@pytest.mark.asyncio
async def test_dashboard_summary_caching(
    db_session: AsyncSession,
    analytics_service: AnalyticsService,
    mock_redis,
    test_messages,
):
    """Test dashboard summary uses caching"""
    import json

    # First call - should compute and cache
    summary1 = await analytics_service.get_dashboard_summary(db=db_session, days=7)

    # Verify cache was set
    assert mock_redis.setex.called

    # Second call - should use cache
    mock_redis.get = AsyncMock(return_value=json.dumps(summary1))
    summary2 = await analytics_service.get_dashboard_summary(db=db_session, days=7)

    assert summary2 == summary1


# ============================================================================
# Singleton Tests
# ============================================================================


def test_get_analytics_service_singleton():
    """Test that get_analytics_service returns singleton instance"""
    service1 = get_analytics_service()
    service2 = get_analytics_service()

    assert service1 is service2
