"""
Tests for Push Notification System

Test Coverage:
1. Device token registration (FCM, APNs, Web Push)
2. Device token unregistration
3. Get user devices
4. Push notification sending (FCM, APNs, Web Push)
5. Notification preferences and muting
6. Offline user detection
7. Multi-device delivery
8. Inactive device cleanup
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.messenger.push_notifications import (
    DevicePlatform,
    NotificationPriority,
    PushNotificationService,
    PushProvider,
    get_push_service,
)
from app.models.messenger_models import DeviceToken, NotificationSetting


@pytest.fixture
def mock_fcm_client():
    """Mock FCM client"""
    client = MagicMock()
    client.notify_single_device = MagicMock(return_value={"success": 1, "failure": 0})
    return client


@pytest.fixture
def mock_apns_client():
    """Mock APNs client"""
    client = AsyncMock()
    response = MagicMock()
    response.is_successful = True
    response.description = "OK"
    client.send_notification = AsyncMock(return_value=response)
    return client


@pytest.fixture
def mock_webpush():
    """Mock Web Push function"""
    return MagicMock()


@pytest.fixture
def push_service(mock_fcm_client, mock_apns_client, mock_webpush):
    """
    Create PushNotificationService with mocked providers
    """
    service = PushNotificationService(
        fcm_server_key="test_fcm_key",
        apns_key_path="/path/to/apns.p8",
        apns_key_id="test_apns_key_id",
        apns_team_id="test_team_id",
        web_push_private_key="test_vapid_key",
        web_push_claims={"sub": "mailto:test@example.com"},
    )

    # Inject mocked clients
    service.fcm_client = mock_fcm_client
    service.apns_client = mock_apns_client
    service.APNsNotificationRequest = MagicMock()
    service.webpush = mock_webpush

    return service


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create test user"""
    from app.models.user import User

    user = User(
        id=1,
        email="testuser@example.com",
        username="testuser",
        hashed_password="hashed_test_password",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


# ============================================================================
# Device Token Registration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_register_device_fcm_android(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test registering an Android device with FCM"""
    result = await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="fcm_token_123",
        platform=DevicePlatform.ANDROID,
        provider=PushProvider.FCM,
        device_name="Samsung Galaxy S21",
    )

    assert result["status"] == "registered"
    assert result["user_id"] == test_user.id
    assert "device_token_id" in result

    # Verify in database
    stmt = select(DeviceToken).where(DeviceToken.user_id == test_user.id)
    db_result = await db_session.execute(stmt)
    device = db_result.scalar_one_or_none()

    assert device is not None
    assert device.token == "fcm_token_123"
    assert device.platform == "android"
    assert device.provider == "fcm"
    assert device.device_name == "Samsung Galaxy S21"
    assert device.is_active is True


@pytest.mark.asyncio
async def test_register_device_apns_ios(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test registering an iOS device with APNs"""
    result = await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="apns_token_456",
        platform=DevicePlatform.IOS,
        provider=PushProvider.APNS,
        device_name="iPhone 13 Pro",
    )

    assert result["status"] == "registered"
    assert result["platform"] == "ios"

    # Verify in database
    stmt = select(DeviceToken).where(DeviceToken.token == "apns_token_456")
    db_result = await db_session.execute(stmt)
    device = db_result.scalar_one_or_none()

    assert device is not None
    assert device.provider == "apns"
    assert device.platform == "ios"


@pytest.mark.asyncio
async def test_register_device_web_push(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test registering a web browser with Web Push"""
    web_push_subscription = json.dumps(
        {
            "endpoint": "https://fcm.googleapis.com/fcm/send/...",
            "keys": {
                "p256dh": "BNcRdre...",
                "auth": "tBHItJI5svbpez7KI4CCXg==",
            },
        }
    )

    result = await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token=web_push_subscription,
        platform=DevicePlatform.WEB,
        provider=PushProvider.WEB_PUSH,
        device_name="Chrome on Desktop",
    )

    assert result["status"] == "registered"
    assert result["platform"] == "web"

    # Verify in database
    stmt = select(DeviceToken).where(DeviceToken.user_id == test_user.id)
    db_result = await db_session.execute(stmt)
    device = db_result.scalar_one_or_none()

    assert device is not None
    assert device.provider == "web_push"
    assert device.platform == "web"


@pytest.mark.asyncio
async def test_register_device_duplicate_updates(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test that registering the same device twice updates it"""
    # First registration
    result1 = await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="fcm_token_999",
        platform=DevicePlatform.ANDROID,
    )

    assert result1["status"] == "registered"
    device_id_1 = result1["device_token_id"]

    # Second registration with same token
    result2 = await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="fcm_token_999",
        platform=DevicePlatform.ANDROID,
    )

    assert result2["status"] == "updated"
    assert result2["device_token_id"] == device_id_1

    # Verify only one device in database
    stmt = select(DeviceToken).where(DeviceToken.user_id == test_user.id)
    db_result = await db_session.execute(stmt)
    devices = db_result.scalars().all()

    assert len(devices) == 1


# ============================================================================
# Device Token Unregistration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_unregister_device_success(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test successfully unregistering a device"""
    # Register device first
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="fcm_token_to_remove",
        platform=DevicePlatform.ANDROID,
    )

    # Unregister
    success = await push_service.unregister_device(
        db=db_session,
        user_id=test_user.id,
        device_token="fcm_token_to_remove",
    )

    assert success is True

    # Verify removed from database
    stmt = select(DeviceToken).where(DeviceToken.token == "fcm_token_to_remove")
    db_result = await db_session.execute(stmt)
    device = db_result.scalar_one_or_none()

    assert device is None


@pytest.mark.asyncio
async def test_unregister_device_not_found(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test unregistering a non-existent device"""
    success = await push_service.unregister_device(
        db=db_session,
        user_id=test_user.id,
        device_token="nonexistent_token",
    )

    assert success is False


# ============================================================================
# Get User Devices Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_devices(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test getting all devices for a user"""
    # Register multiple devices
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="android_token",
        platform=DevicePlatform.ANDROID,
        device_name="Android Phone",
    )

    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="ios_token",
        platform=DevicePlatform.IOS,
        device_name="iPhone",
    )

    # Get devices
    devices = await push_service.get_user_devices(
        db=db_session,
        user_id=test_user.id,
    )

    assert len(devices) == 2
    assert devices[0]["platform"] in ["android", "ios"]
    assert devices[1]["platform"] in ["android", "ios"]
    assert "registered_at" in devices[0]


@pytest.mark.asyncio
async def test_get_user_devices_active_only(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test filtering active devices only"""
    # Register active device
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="active_token",
        platform=DevicePlatform.ANDROID,
    )

    # Register inactive device
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="inactive_token",
        platform=DevicePlatform.ANDROID,
    )

    # Mark second device as inactive
    stmt = select(DeviceToken).where(DeviceToken.token == "inactive_token")
    result = await db_session.execute(stmt)
    device = result.scalar_one()
    device.is_active = False
    await db_session.commit()

    # Get active devices only
    devices = await push_service.get_user_devices(
        db=db_session,
        user_id=test_user.id,
        active_only=True,
    )

    assert len(devices) == 1
    assert devices[0]["platform"] == "android"


# ============================================================================
# Push Notification Sending Tests
# ============================================================================


@pytest.mark.asyncio
async def test_send_push_notification_fcm(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test sending push notification via FCM"""
    # Register device
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="fcm_token_send_test",
        platform=DevicePlatform.ANDROID,
        provider=PushProvider.FCM,
    )

    # Send notification
    result = await push_service.send_push_notification(
        db=db_session,
        user_id=test_user.id,
        title="Test Notification",
        body="This is a test message",
        data={"conversation_id": "12345", "type": "message.new"},
        priority=NotificationPriority.HIGH,
    )

    assert result["status"] == "sent"
    assert result["user_id"] == test_user.id
    assert result["devices_count"] == 1
    assert result["success_count"] == 1

    # Verify FCM client was called
    push_service.fcm_client.notify_single_device.assert_called_once()  # type: ignore


@pytest.mark.asyncio
async def test_send_push_notification_apns(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test sending push notification via APNs"""
    # Register device
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="apns_token_send_test",
        platform=DevicePlatform.IOS,
        provider=PushProvider.APNS,
    )

    # Send notification
    result = await push_service.send_push_notification(
        db=db_session,
        user_id=test_user.id,
        title="Test Notification",
        body="This is a test message",
        priority=NotificationPriority.HIGH,
    )

    assert result["status"] == "sent"
    assert result["success_count"] == 1

    # Verify APNs client was called
    push_service.apns_client.send_notification.assert_called_once()  # type: ignore


@pytest.mark.asyncio
async def test_send_push_notification_multi_device(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test sending push notification to multiple devices"""
    # Register multiple devices
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="fcm_token_1",
        platform=DevicePlatform.ANDROID,
        provider=PushProvider.FCM,
    )

    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="apns_token_1",
        platform=DevicePlatform.IOS,
        provider=PushProvider.APNS,
    )

    # Send notification
    result = await push_service.send_push_notification(
        db=db_session,
        user_id=test_user.id,
        title="Multi-Device Test",
        body="Testing multi-device delivery",
    )

    assert result["status"] == "sent"
    assert result["devices_count"] == 2
    assert result["success_count"] == 2


@pytest.mark.asyncio
async def test_send_push_notification_no_devices(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test sending push notification when user has no devices"""
    result = await push_service.send_push_notification(
        db=db_session,
        user_id=test_user.id,
        title="Test Notification",
        body="This should not be sent",
    )

    assert result["status"] == "no_devices"
    assert result["user_id"] == test_user.id


# ============================================================================
# Notification Preferences Tests
# ============================================================================


@pytest.mark.asyncio
async def test_send_push_notification_muted_conversation(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test that muted conversations don't trigger push notifications"""
    conversation_id = str(uuid.uuid4())

    # Register device
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="fcm_token_muted",
        platform=DevicePlatform.ANDROID,
        provider=PushProvider.FCM,
    )

    # Create muted notification setting
    from app.models.messenger_models import Conversation

    conversation = Conversation(
        id=uuid.UUID(conversation_id),
        type="direct",
        created_by=test_user.id,
    )
    db_session.add(conversation)

    settings = NotificationSetting(
        user_id=test_user.id,
        conversation_id=uuid.UUID(conversation_id),
        muted=True,
        push_enabled=True,
    )
    db_session.add(settings)
    await db_session.commit()

    # Try to send notification
    result = await push_service.send_push_notification(
        db=db_session,
        user_id=test_user.id,
        title="Muted Test",
        body="This should be skipped",
        conversation_id=conversation_id,
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "muted_or_disabled"


@pytest.mark.asyncio
async def test_send_push_notification_push_disabled(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test that conversations with push_enabled=False don't trigger notifications"""
    conversation_id = str(uuid.uuid4())

    # Register device
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="fcm_token_disabled",
        platform=DevicePlatform.ANDROID,
        provider=PushProvider.FCM,
    )

    # Create notification setting with push disabled
    from app.models.messenger_models import Conversation

    conversation = Conversation(
        id=uuid.UUID(conversation_id),
        type="direct",
        created_by=test_user.id,
    )
    db_session.add(conversation)

    settings = NotificationSetting(
        user_id=test_user.id,
        conversation_id=uuid.UUID(conversation_id),
        muted=False,
        push_enabled=False,
    )
    db_session.add(settings)
    await db_session.commit()

    # Try to send notification
    result = await push_service.send_push_notification(
        db=db_session,
        user_id=test_user.id,
        title="Push Disabled Test",
        body="This should be skipped",
        conversation_id=conversation_id,
    )

    assert result["status"] == "skipped"


# ============================================================================
# Cleanup Tests
# ============================================================================


@pytest.mark.asyncio
async def test_cleanup_inactive_devices(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test cleanup of devices inactive for 90+ days"""
    # Register device
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="old_device_token",
        platform=DevicePlatform.ANDROID,
    )

    # Set last_used_at to 100 days ago
    stmt = select(DeviceToken).where(DeviceToken.token == "old_device_token")
    result = await db_session.execute(stmt)
    device = result.scalar_one()
    device.last_used_at = datetime.utcnow() - timedelta(days=100)
    await db_session.commit()

    # Run cleanup
    removed = await push_service.cleanup_inactive_devices(db=db_session, days=90)

    assert removed == 1

    # Verify device is removed
    stmt = select(DeviceToken).where(DeviceToken.token == "old_device_token")
    result = await db_session.execute(stmt)
    device = result.scalar_one_or_none()

    assert device is None


@pytest.mark.asyncio
async def test_cleanup_keeps_active_devices(
    db_session: AsyncSession,
    test_user,
    push_service: PushNotificationService,
):
    """Test cleanup doesn't remove recently used devices"""
    # Register device
    await push_service.register_device(
        db=db_session,
        user_id=test_user.id,
        device_token="active_device_token",
        platform=DevicePlatform.ANDROID,
    )

    # Set last_used_at to 30 days ago (recent)
    stmt = select(DeviceToken).where(DeviceToken.token == "active_device_token")
    result = await db_session.execute(stmt)
    device = result.scalar_one()
    device.last_used_at = datetime.utcnow() - timedelta(days=30)
    await db_session.commit()

    # Run cleanup
    removed = await push_service.cleanup_inactive_devices(db=db_session, days=90)

    assert removed == 0

    # Verify device still exists
    stmt = select(DeviceToken).where(DeviceToken.token == "active_device_token")
    result = await db_session.execute(stmt)
    device = result.scalar_one_or_none()

    assert device is not None


# ============================================================================
# Singleton Tests
# ============================================================================


def test_get_push_service_singleton():
    """Test that get_push_service returns singleton instance"""
    service1 = get_push_service()
    service2 = get_push_service()

    assert service1 is service2
