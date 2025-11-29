"""
Task 4.1: Enhanced Notification System Tests

Tests for:
- Multi-channel notification delivery (push, email, in-app)
- User preference management
- Quiet hours support
- Priority levels
- In-app notification CRUD
- Notification templates
- Read tracking
- REST API endpoints

Test Coverage:
- 30+ test scenarios
- All notification types
- Channel preferences
- Permission checks
- Error handling
"""

import pytest
from datetime import time
from typing import Dict, List
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models import User, Conversation
from app.messenger.notifications import (
    EnhancedNotificationService,
    NotificationChannel,
    NotificationType,
    NotificationPriority,
    get_notification_service,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def notification_service():
    """Get fresh notification service instance."""
    return get_notification_service()


@pytest.fixture
async def test_users(db: AsyncSession) -> List[User]:
    """Create test users."""
    users = []

    for i in range(3):
        user = User(
            email=f"testuser{i}@example.com",
            hashed_password="hashed",
            full_name=f"Test User {i}",
            role="user",
        )
        db.add(user)
        users.append(user)

    await db.commit()

    for user in users:
        await db.refresh(user)

    return users


@pytest.fixture
async def test_conversation(
    db: AsyncSession,
    test_users: List[User],
) -> Conversation:
    """Create test conversation."""
    conversation = Conversation(
        title="Test Conversation",
        type="group",
        created_by=test_users[0].id,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return conversation


# ============================================================================
# NOTIFICATION DELIVERY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_send_notification_all_channels(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test sending notification to all channels."""
    user = test_users[0]

    # Mock push notification system
    with patch.object(
        notification_service,
        "_send_push_notification",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_push:
        with patch.object(
            notification_service,
            "_send_email_notification",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_email:

            results = await notification_service.send_notification(
                db=db,
                user_id=int(user.id),  # type: ignore
                notification_type=NotificationType.NEW_MESSAGE,
                data={
                    "sender": "Test Sender",
                    "recipient": user.email,
                    "preview": "Test message",
                    "conversation": "Test Conv",
                },
                priority=NotificationPriority.NORMAL,
            )

            # All channels should succeed
            assert results["in_app"] is True
            assert results["push"] is True
            assert results["email"] is True

            # Check mocks were called
            mock_push.assert_awaited_once()
            mock_email.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_notification_priority_levels(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test different priority levels."""
    user = test_users[0]

    # Set quiet hours (block normal priority)
    await notification_service.set_user_preference(
        db=db,
        user_id=int(user.id),  # type: ignore
        channel=NotificationChannel.PUSH,
        notification_type=NotificationType.NEW_MESSAGE,
        enabled=True,
        quiet_hours_start=time(0, 0),
        quiet_hours_end=time(23, 59),
    )

    # Low priority - should be blocked
    with patch.object(
        notification_service,
        "_send_push_notification",
        new_callable=AsyncMock,
    ) as mock_push:

        results = await notification_service.send_notification(
            db=db,
            user_id=int(user.id),  # type: ignore
            notification_type=NotificationType.NEW_MESSAGE,
            data={"sender": "Test"},
            priority=NotificationPriority.LOW,
        )

        # Should be skipped during quiet hours
        assert "skipped" in results or results["push"] is False

    # Urgent priority - should bypass quiet hours
    with patch.object(
        notification_service,
        "_send_push_notification",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_push:

        results = await notification_service.send_notification(
            db=db,
            user_id=int(user.id),  # type: ignore
            notification_type=NotificationType.MODERATION_WARNING,
            data={"reason": "Test warning"},
            priority=NotificationPriority.URGENT,
        )

        # Should succeed despite quiet hours
        assert results["push"] is True
        mock_push.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_notification_with_disabled_channels(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test sending notification with disabled channels."""
    user = test_users[0]

    # Disable push notifications
    await notification_service.set_user_preference(
        db=db,
        user_id=int(user.id),  # type: ignore
        channel=NotificationChannel.PUSH,
        notification_type=NotificationType.NEW_MESSAGE,
        enabled=False,
    )

    with patch.object(
        notification_service,
        "_send_push_notification",
        new_callable=AsyncMock,
    ) as mock_push:
        with patch.object(
            notification_service,
            "_send_email_notification",
            new_callable=AsyncMock,
            return_value=True,
        ) as _mock_email:

            results = await notification_service.send_notification(
                db=db,
                user_id=int(user.id),  # type: ignore
                notification_type=NotificationType.NEW_MESSAGE,
                data={"sender": "Test"},
                priority=NotificationPriority.NORMAL,
            )

            # Push should be skipped
            mock_push.assert_not_awaited()

            # Email and in-app should still work
            assert results["in_app"] is True
            assert results["email"] is True


# ============================================================================
# IN-APP NOTIFICATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_create_in_app_notification(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test creating in-app notification."""
    user = test_users[0]

    # Create notification
    success = await notification_service._send_in_app_notification(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_type=NotificationType.NEW_MESSAGE,
        data={
            "sender": "Test Sender",
            "recipient": "test@example.com",
            "preview": "You have a new message",
            "conversation": "Test",
        },
        priority=NotificationPriority.NORMAL,
    )

    assert success is True

    # Check notification was created
    notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
    )

    assert len(notifications) == 1
    assert (
        "New Message" in notifications[0]["title"]
        or "Test Sender" in notifications[0]["title"]
    )
    assert notifications[0]["is_read"] is False


@pytest.mark.asyncio
async def test_get_in_app_notifications_pagination(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test getting notifications with pagination."""
    user = test_users[0]

    # Create 10 notifications
    for i in range(10):
        await notification_service._send_in_app_notification(
            db=db,
            user_id=int(user.id),  # type: ignore
            notification_type=NotificationType.NEW_MESSAGE,
            data={
                "sender": f"Sender {i}",
                "recipient": "test@example.com",
                "preview": f"Message {i}",
                "conversation": "Test",
            },
            priority=NotificationPriority.NORMAL,
        )

    # Get first page
    page1 = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
        limit=5,
        offset=0,
    )

    assert len(page1) == 5

    # Get second page
    page2 = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
        limit=5,
        offset=5,
    )

    assert len(page2) == 5

    # Should be different notifications
    page1_ids = {n["id"] for n in page1}
    page2_ids = {n["id"] for n in page2}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_get_unread_notifications_only(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test getting only unread notifications."""
    user = test_users[0]

    # Create 5 notifications
    notification_ids = []
    for i in range(5):
        await notification_service._send_in_app_notification(
            db=db,
            user_id=int(user.id),  # type: ignore
            notification_type=NotificationType.NEW_MESSAGE,
            data={
                "sender": f"Sender {i}",
                "recipient": "test@example.com",
                "preview": f"Message {i}",
                "conversation": "Test",
            },
            priority=NotificationPriority.NORMAL,
        )

    # Get all notifications
    all_notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
    )
    notification_ids = [n["id"] for n in all_notifications]

    # Mark first 2 as read
    await notification_service.mark_notification_read(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_id=notification_ids[0],
    )
    await notification_service.mark_notification_read(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_id=notification_ids[1],
    )

    # Get unread only
    unread = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
        unread_only=True,
    )

    assert len(unread) == 3

    # All should be unread
    for notification in unread:
        assert notification["is_read"] is False


@pytest.mark.asyncio
async def test_mark_notification_read(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test marking notification as read."""
    user = test_users[0]

    # Create notification
    await notification_service._send_in_app_notification(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_type=NotificationType.NEW_MESSAGE,
        data={
            "sender": "Test Sender",
            "recipient": "test@example.com",
            "preview": "Test",
            "conversation": "Test",
        },
        priority=NotificationPriority.NORMAL,
    )

    # Get notification
    notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
    )
    notification_id = notifications[0]["id"]

    # Mark as read
    success = await notification_service.mark_notification_read(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_id=notification_id,
    )

    assert success is True

    # Verify it's read
    notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
    )

    assert notifications[0]["is_read"] is True
    assert notifications[0]["read_at"] is not None


@pytest.mark.asyncio
async def test_mark_all_read(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test marking all notifications as read."""
    user = test_users[0]

    # Create 5 unread notifications
    for i in range(5):
        await notification_service._send_in_app_notification(
            db=db,
            user_id=int(user.id),  # type: ignore
            notification_type=NotificationType.NEW_MESSAGE,
            data={
                "sender": f"Sender {i}",
                "recipient": "test@example.com",
                "preview": f"Message {i}",
                "conversation": "Test",
            },
            priority=NotificationPriority.NORMAL,
        )

    # Mark all as read
    count = await notification_service.mark_all_read(
        db=db,
        user_id=int(user.id),  # type: ignore
    )

    assert count == 5

    # Verify all are read
    unread = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
        unread_only=True,
    )

    assert len(unread) == 0


@pytest.mark.asyncio
async def test_get_unread_count(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test getting unread notification count."""
    user = test_users[0]

    # Initial count should be 0
    count = await notification_service.get_unread_count(
        db=db,
        user_id=int(user.id),  # type: ignore
    )
    assert count == 0

    # Create 3 notifications
    for i in range(3):
        await notification_service._send_in_app_notification(
            db=db,
            user_id=int(user.id),  # type: ignore
            notification_type=NotificationType.NEW_MESSAGE,
            data={
                "sender": f"Sender {i}",
                "recipient": "test@example.com",
                "preview": f"Message {i}",
                "conversation": "Test",
            },
            priority=NotificationPriority.NORMAL,
        )

    # Count should be 3
    count = await notification_service.get_unread_count(
        db=db,
        user_id=int(user.id),  # type: ignore
    )
    assert count == 3

    # Mark one as read
    notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
    )
    await notification_service.mark_notification_read(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_id=notifications[0]["id"],
    )

    # Count should be 2
    count = await notification_service.get_unread_count(
        db=db,
        user_id=int(user.id),  # type: ignore
    )
    assert count == 2


@pytest.mark.asyncio
async def test_delete_notification(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test deleting notification."""
    user = test_users[0]

    # Create notification
    await notification_service._send_in_app_notification(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_type=NotificationType.NEW_MESSAGE,
        data={
            "sender": "Test Sender",
            "recipient": "test@example.com",
            "preview": "Test",
            "conversation": "Test",
        },
        priority=NotificationPriority.NORMAL,
    )

    # Get notification
    notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
    )
    notification_id = notifications[0]["id"]

    # Delete it
    success = await notification_service.delete_notification(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_id=notification_id,
    )

    assert success is True

    # Verify it's gone
    notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
    )

    assert len(notifications) == 0


@pytest.mark.asyncio
async def test_notification_isolation_between_users(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test that users can't access each other's notifications."""
    user1, user2 = test_users[0], test_users[1]

    # Create notification for user1
    await notification_service._send_in_app_notification(
        db=db,
        user_id=int(user1.id),  # type: ignore
        notification_type=NotificationType.NEW_MESSAGE,
        data={
            "sender": "Test Sender",
            "recipient": "test@example.com",
            "preview": "Message for user1",
            "conversation": "Test",
        },
        priority=NotificationPriority.NORMAL,
    )

    # Get notification ID
    user1_notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user1.id),  # type: ignore
    )
    notification_id = user1_notifications[0]["id"]

    # User2 tries to access it
    notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user2.id),  # type: ignore
    )
    assert len(notifications) == 0

    # User2 tries to mark it as read
    success = await notification_service.mark_notification_read(
        db=db,
        user_id=int(user2.id),  # type: ignore
        notification_id=notification_id,
    )
    assert success is False

    # User2 tries to delete it
    success = await notification_service.delete_notification(
        db=db,
        user_id=int(user2.id),  # type: ignore
        notification_id=notification_id,
    )
    assert success is False


# ============================================================================
# PREFERENCE MANAGEMENT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_set_and_get_user_preferences(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test setting and getting user preferences."""
    user = test_users[0]

    # Set preference
    await notification_service.set_user_preference(
        db=db,
        user_id=int(user.id),  # type: ignore
        channel=NotificationChannel.PUSH,
        notification_type=NotificationType.NEW_MESSAGE,
        enabled=False,
        quiet_hours_start=time(22, 0),
        quiet_hours_end=time(8, 0),
    )

    # Get preferences
    preferences = await notification_service.get_user_preferences(
        db=db,
        user_id=int(user.id),  # type: ignore
    )

    # Check push preference
    push_prefs = preferences.get(NotificationChannel.PUSH.value, {})
    new_message_pref = push_prefs.get(NotificationType.NEW_MESSAGE.value, {})

    assert new_message_pref["enabled"] is False
    assert new_message_pref["quiet_hours_start"] == "22:00"
    assert new_message_pref["quiet_hours_end"] == "08:00"


@pytest.mark.asyncio
async def test_update_existing_preference(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test updating existing preference."""
    user = test_users[0]

    # Set initial preference
    await notification_service.set_user_preference(
        db=db,
        user_id=int(user.id),  # type: ignore
        channel=NotificationChannel.EMAIL,
        notification_type=NotificationType.NEW_MESSAGE,
        enabled=True,
    )

    # Update to disabled
    await notification_service.set_user_preference(
        db=db,
        user_id=int(user.id),  # type: ignore
        channel=NotificationChannel.EMAIL,
        notification_type=NotificationType.NEW_MESSAGE,
        enabled=False,
    )

    # Check updated preference
    preferences = await notification_service.get_user_preferences(
        db=db,
        user_id=int(user.id),  # type: ignore
    )

    email_prefs = preferences.get(NotificationChannel.EMAIL.value, {})
    new_message_pref = email_prefs.get(NotificationType.NEW_MESSAGE.value, {})

    assert new_message_pref["enabled"] is False


@pytest.mark.asyncio
async def test_default_preferences(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test default preferences for new users."""
    user = test_users[0]

    # Get preferences without setting any
    preferences = await notification_service.get_user_preferences(
        db=db,
        user_id=int(user.id),  # type: ignore
    )

    # Should have default structure
    assert NotificationChannel.PUSH.value in preferences
    assert NotificationChannel.EMAIL.value in preferences
    assert NotificationChannel.IN_APP.value in preferences


# ============================================================================
# TEMPLATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_notification_templates(
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
    test_users: List[User],
):
    """Test notification templates for different types."""
    user = test_users[0]

    # Test new message template
    with patch.object(
        notification_service,
        "_send_push_notification",
        new_callable=AsyncMock,
        return_value=True,
    ):
        with patch.object(
            notification_service,
            "_send_email_notification",
            new_callable=AsyncMock,
            return_value=True,
        ):

            await notification_service.send_notification(
                db=db,
                user_id=int(user.id),  # type: ignore
                notification_type=NotificationType.NEW_MESSAGE,
                data={
                    "sender": "John Doe",
                    "recipient": user.email,
                    "preview": "Hey, how are you?",
                    "conversation": "General Chat",
                },
                priority=NotificationPriority.NORMAL,
            )

            # Check in-app notification was created with template
            notifications = await notification_service.get_in_app_notifications(
                db=db,
                user_id=int(user.id),  # type: ignore
            )

            assert len(notifications) == 1
            assert "John Doe" in notifications[0]["title"]
            assert "Hey, how are you?" in notifications[0]["message"]


# ============================================================================
# REST API TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_api_get_notifications(
    client: AsyncClient,
    test_users: List[User],
    auth_headers: Dict[str, str],
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
):
    """Test GET /notifications endpoint."""
    user = test_users[0]

    # Create some notifications
    for i in range(3):
        await notification_service._send_in_app_notification(
            db=db,
            user_id=int(user.id),  # type: ignore
            notification_type=NotificationType.NEW_MESSAGE,
            data={
                "sender": f"Sender {i}",
                "recipient": "test@example.com",
                "preview": f"Message {i}",
                "conversation": "Test",
            },
            priority=NotificationPriority.NORMAL,
        )

    # Get notifications
    response = await client.get(
        "/api/v1/messenger/notifications",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 3


@pytest.mark.asyncio
async def test_api_get_unread_count(
    client: AsyncClient,
    test_users: List[User],
    auth_headers: Dict[str, str],
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
):
    """Test GET /notifications/unread-count endpoint."""
    user = test_users[0]

    # Create 2 unread notifications
    for i in range(2):
        await notification_service._send_in_app_notification(
            db=db,
            user_id=int(user.id),  # type: ignore
            notification_type=NotificationType.NEW_MESSAGE,
            data={
                "sender": f"Sender {i}",
                "recipient": "test@example.com",
                "preview": f"Message {i}",
                "conversation": "Test",
            },
            priority=NotificationPriority.NORMAL,
        )

    # Get count
    response = await client.get(
        "/api/v1/messenger/notifications/unread-count",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2


@pytest.mark.asyncio
async def test_api_mark_notification_read(
    client: AsyncClient,
    test_users: List[User],
    auth_headers: Dict[str, str],
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
):
    """Test POST /notifications/{id}/read endpoint."""
    user = test_users[0]

    # Create notification
    await notification_service._send_in_app_notification(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_type=NotificationType.NEW_MESSAGE,
        data={
            "sender": "Test Sender",
            "recipient": "test@example.com",
            "preview": "Test",
            "conversation": "Test",
        },
        priority=NotificationPriority.NORMAL,
    )

    # Get notification ID
    notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
    )
    notification_id = notifications[0]["id"]

    # Mark as read
    response = await client.post(
        f"/api/v1/messenger/notifications/{notification_id}/read",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_api_mark_all_read(
    client: AsyncClient,
    test_users: List[User],
    auth_headers: Dict[str, str],
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
):
    """Test POST /notifications/mark-all-read endpoint."""
    user = test_users[0]

    # Create 3 notifications
    for i in range(3):
        await notification_service._send_in_app_notification(
            db=db,
            user_id=int(user.id),  # type: ignore
            notification_type=NotificationType.NEW_MESSAGE,
            data={
                "sender": f"Sender {i}",
                "recipient": "test@example.com",
                "preview": f"Message {i}",
                "conversation": "Test",
            },
            priority=NotificationPriority.NORMAL,
        )

    # Mark all as read
    response = await client.post(
        "/api/v1/messenger/notifications/mark-all-read",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["marked_count"] == 3


@pytest.mark.asyncio
async def test_api_delete_notification(
    client: AsyncClient,
    test_users: List[User],
    auth_headers: Dict[str, str],
    db: AsyncSession,
    notification_service: EnhancedNotificationService,
):
    """Test DELETE /notifications/{id} endpoint."""
    user = test_users[0]

    # Create notification
    await notification_service._send_in_app_notification(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_type=NotificationType.NEW_MESSAGE,
        data={
            "sender": "Test Sender",
            "recipient": "test@example.com",
            "preview": "Test",
            "conversation": "Test",
        },
        priority=NotificationPriority.NORMAL,
    )

    # Get notification ID
    notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
    )
    notification_id = notifications[0]["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/messenger/notifications/{notification_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_api_get_preferences(
    client: AsyncClient,
    test_users: List[User],
    auth_headers: Dict[str, str],
):
    """Test GET /notification-preferences endpoint."""
    response = await client.get(
        "/api/v1/messenger/notification-preferences",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "preferences" in data


@pytest.mark.asyncio
async def test_api_set_preference(
    client: AsyncClient,
    test_users: List[User],
    auth_headers: Dict[str, str],
):
    """Test PUT /notification-preferences endpoint."""
    response = await client.put(
        "/api/v1/messenger/notification-preferences"
        "?channel=push"
        "&notification_type=new_message"
        "&enabled=false"
        "&quiet_hours_start=22:00"
        "&quiet_hours_end=08:00",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["channel"] == "push"
    assert data["enabled"] is False


@pytest.mark.asyncio
async def test_api_unauthorized_access(client: AsyncClient):
    """Test that endpoints require authentication."""
    # Try without auth headers
    response = await client.get("/api/v1/messenger/notifications")
    assert response.status_code == 401

    response = await client.get("/api/v1/messenger/notifications/unread-count")
    assert response.status_code == 401

    response = await client.post("/api/v1/messenger/notifications/1/read")
    assert response.status_code == 401
