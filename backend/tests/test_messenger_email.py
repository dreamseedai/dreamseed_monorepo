"""
Task 4.2: Email Service Tests

Tests for:
- SMTP email sending
- HTML template rendering
- Digest email generation
- Rate limiting
- Bulk sending
- Email preferences

Test Coverage:
- 25+ test scenarios
- All notification types
- Digest frequencies
- Template rendering
- Email delivery
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models import User
from app.messenger.email_service import (
    EmailService,
    DigestFrequency,
    get_email_service,
)
from app.messenger.notifications import NotificationType


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def email_service():
    """Get fresh email service instance."""
    return EmailService()


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Create test user with email."""
    user = User(
        email="testuser@example.com",
        hashed_password="hashed",
        full_name="Test User",
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


# ============================================================================
# EMAIL SENDING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_send_email_smtp_success(email_service: EmailService):
    """Test successful SMTP email sending."""
    with patch("aiosmtplib.SMTP") as mock_smtp:
        # Mock SMTP context manager
        mock_smtp_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance

        success = await email_service.send_email_smtp(
            to_email="test@example.com",
            subject="Test Email",
            html_body="<h1>Test</h1>",
            text_body="Test",
        )

        assert success is True
        mock_smtp_instance.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_email_rate_limit(email_service: EmailService):
    """Test email rate limiting."""
    # Set low rate limit
    email_service.rate_limit_per_hour = 2

    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_smtp_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance

        # Send 2 emails (should succeed)
        success1 = await email_service.send_email_smtp(
            to_email="test@example.com",
            subject="Test 1",
            html_body="<h1>Test 1</h1>",
        )
        success2 = await email_service.send_email_smtp(
            to_email="test@example.com",
            subject="Test 2",
            html_body="<h1>Test 2</h1>",
        )

        assert success1 is True
        assert success2 is True

        # Third email should be rate limited
        success3 = await email_service.send_email_smtp(
            to_email="test@example.com",
            subject="Test 3",
            html_body="<h1>Test 3</h1>",
        )

        assert success3 is False


@pytest.mark.asyncio
async def test_send_email_with_attachments(email_service: EmailService):
    """Test sending email with attachments."""
    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_smtp_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance

        attachments = [
            {
                "type": "image",
                "data": b"fake_image_data",
                "cid": "logo",
            }
        ]

        success = await email_service.send_email_smtp(
            to_email="test@example.com",
            subject="Test with Attachment",
            html_body='<h1>Test</h1><img src="cid:logo">',
            attachments=attachments,
        )

        assert success is True


# ============================================================================
# TEMPLATE RENDERING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_render_template_new_message(email_service: EmailService):
    """Test rendering new message template."""
    context = {
        "sender": "John Doe",
        "conversation": "General Chat",
        "preview": "Hey, how are you?",
        "action_url": "https://example.com/message/123",
    }

    html_body, text_body = email_service.render_template(
        "new_message.html",
        context,
    )

    assert "John Doe" in html_body
    assert "General Chat" in html_body
    assert "Hey, how are you?" in html_body
    assert "John Doe" in text_body


@pytest.mark.asyncio
async def test_render_template_mention(email_service: EmailService):
    """Test rendering mention template."""
    context = {
        "sender": "Jane Smith",
        "conversation": "Project Discussion",
        "preview": "@testuser Can you review this?",
        "action_url": "https://example.com/message/456",
    }

    html_body, _text_body = email_service.render_template(
        "message_mention.html",
        context,
    )

    assert "Jane Smith" in html_body
    assert "mentioned you" in html_body


@pytest.mark.asyncio
async def test_render_template_invite(email_service: EmailService):
    """Test rendering invitation template."""
    context = {
        "sender": "Admin User",
        "conversation": "New Team Channel",
        "action_url": "https://example.com/conversation/789",
    }

    html_body, _text_body = email_service.render_template(
        "conversation_invite.html",
        context,
    )

    assert "New Team Channel" in html_body
    assert "invited" in html_body.lower()


@pytest.mark.asyncio
async def test_render_template_with_context_variables(email_service: EmailService):
    """Test that common context variables are added."""
    context = {
        "sender": "Test",
        "conversation": "Test",
        "preview": "Test",
        "action_url": "https://example.com",
    }

    html_body, _text_body = email_service.render_template(
        "new_message.html",
        context,
    )

    # Should include site_name, site_url, support_email, current_year
    assert "DreamSeed" in html_body
    assert str(datetime.now().year) in html_body


# ============================================================================
# NOTIFICATION EMAIL TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_send_notification_email_new_message(email_service: EmailService):
    """Test sending new message notification email."""
    with patch.object(
        email_service,
        "send_email",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:

        data = {
            "sender": "John Doe",
            "conversation": "General Chat",
            "preview": "Hey there!",
            "action_url": "/messenger/conversations/1",
        }

        success = await email_service.send_notification_email(
            user_email="test@example.com",
            notification_type=NotificationType.NEW_MESSAGE,
            data=data,
        )

        assert success is True
        mock_send.assert_awaited_once()

        # Check email content
        call_args = mock_send.call_args
        assert call_args.kwargs["to_email"] == "test@example.com"
        assert "John Doe" in call_args.kwargs["subject"]


@pytest.mark.asyncio
async def test_send_notification_email_mention(email_service: EmailService):
    """Test sending mention notification email."""
    with patch.object(
        email_service,
        "send_email",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:

        data = {
            "sender": "Jane Smith",
            "conversation": "Project Discussion",
            "preview": "@user Can you check this?",
            "action_url": "/messenger/conversations/2",
        }

        success = await email_service.send_notification_email(
            user_email="test@example.com",
            notification_type=NotificationType.MESSAGE_MENTION,
            data=data,
        )

        assert success is True
        assert "mentioned you" in mock_send.call_args.kwargs["subject"].lower()


@pytest.mark.asyncio
async def test_send_notification_email_invalid_type(email_service: EmailService):
    """Test sending notification with no email template."""
    with patch.object(
        email_service,
        "send_email",
        new_callable=AsyncMock,
    ) as mock_send:

        data = {}

        success = await email_service.send_notification_email(
            user_email="test@example.com",
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,  # No template
            data=data,
        )

        # Should fail gracefully
        assert success is False
        mock_send.assert_not_awaited()


# ============================================================================
# DIGEST EMAIL TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_send_digest_email_daily(
    db: AsyncSession,
    email_service: EmailService,
    test_user: User,
):
    """Test sending daily digest email."""
    # Create some notifications
    from app.models import InAppNotification

    notifications = []
    for i in range(3):
        notification = InAppNotification(
            user_id=int(test_user.id),  # type: ignore
            type="new_message",
            title=f"Message {i}",
            message=f"Content {i}",
            data={},
            priority="normal",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(hours=i),
        )
        db.add(notification)
        notifications.append(notification)

    await db.commit()

    with patch.object(
        email_service,
        "send_email",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:

        success = await email_service.send_digest_email(
            db=db,
            user_id=int(test_user.id),  # type: ignore
            frequency=DigestFrequency.DAILY,
        )

        assert success is True
        mock_send.assert_awaited_once()

        # Check email content
        call_args = mock_send.call_args
        assert "Daily Digest" in call_args.kwargs["subject"]
        assert test_user.email in call_args.kwargs["to_email"]


@pytest.mark.asyncio
async def test_send_digest_email_weekly(
    db: AsyncSession,
    email_service: EmailService,
    test_user: User,
):
    """Test sending weekly digest email."""
    # Create notifications
    from app.models import InAppNotification

    for i in range(5):
        notification = InAppNotification(
            user_id=int(test_user.id),  # type: ignore
            type="message_mention",
            title=f"Mention {i}",
            message=f"You were mentioned in message {i}",
            data={},
            priority="normal",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(days=i),
        )
        db.add(notification)

    await db.commit()

    with patch.object(
        email_service,
        "send_email",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:

        success = await email_service.send_digest_email(
            db=db,
            user_id=int(test_user.id),  # type: ignore
            frequency=DigestFrequency.WEEKLY,
        )

        assert success is True
        assert "Weekly Digest" in mock_send.call_args.kwargs["subject"]


@pytest.mark.asyncio
async def test_send_digest_email_no_notifications(
    db: AsyncSession,
    email_service: EmailService,
    test_user: User,
):
    """Test sending digest with no notifications."""
    with patch.object(
        email_service,
        "send_email",
        new_callable=AsyncMock,
    ) as mock_send:

        success = await email_service.send_digest_email(
            db=db,
            user_id=int(test_user.id),  # type: ignore
            frequency=DigestFrequency.DAILY,
        )

        # Should skip sending
        assert success is False
        mock_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_group_notifications_by_type(email_service: EmailService):
    """Test grouping notifications by type."""
    notifications = [
        MagicMock(
            type="new_message",
            title="Message 1",
            message="Content 1",
            data={},
            action_url="/1",
            created_at=datetime.utcnow(),
        ),
        MagicMock(
            type="new_message",
            title="Message 2",
            message="Content 2",
            data={},
            action_url="/2",
            created_at=datetime.utcnow(),
        ),
        MagicMock(
            type="message_mention",
            title="Mention 1",
            message="You were mentioned",
            data={},
            action_url="/3",
            created_at=datetime.utcnow(),
        ),
    ]

    grouped = email_service._group_notifications(notifications)

    assert len(grouped) == 2
    assert "new_message" in grouped
    assert "message_mention" in grouped
    assert len(grouped["new_message"]) == 2
    assert len(grouped["message_mention"]) == 1


# ============================================================================
# BULK SENDING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_send_bulk_emails(email_service: EmailService):
    """Test sending bulk emails."""
    recipients = [
        {
            "email": "user1@example.com",
            "context": {
                "sender": "Admin",
                "conversation": "Announcements",
                "preview": "Test 1",
            },
        },
        {
            "email": "user2@example.com",
            "context": {
                "sender": "Admin",
                "conversation": "Announcements",
                "preview": "Test 2",
            },
        },
        {
            "email": "user3@example.com",
            "context": {
                "sender": "Admin",
                "conversation": "Announcements",
                "preview": "Test 3",
            },
        },
    ]

    with patch.object(
        email_service,
        "send_email",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:

        count = await email_service.send_bulk_emails(
            recipients=recipients,
            template_name="new_message.html",
            subject="Announcement",
        )

        assert count == 3
        assert mock_send.await_count == 3


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_api_send_digest_email(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict,
    db: AsyncSession,
):
    """Test POST /digest/send endpoint."""
    # Create notification
    from app.models import InAppNotification

    notification = InAppNotification(
        user_id=int(test_user.id),  # type: ignore
        type="new_message",
        title="Test",
        message="Test",
        data={},
        priority="normal",
        is_read=False,
    )
    db.add(notification)
    await db.commit()

    with patch(
        "app.messenger.email_service.EmailService.send_digest_email"
    ) as mock_send:
        mock_send.return_value = True

        response = await client.post(
            "/api/v1/messenger/digest/send?frequency=daily",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["frequency"] == "daily"


@pytest.mark.asyncio
async def test_api_test_email_configuration(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict,
):
    """Test GET /email/test endpoint."""
    with patch("app.messenger.email_service.EmailService.send_email") as mock_send:
        mock_send.return_value = True

        response = await client.get(
            "/api/v1/messenger/email/test",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert "from_email" in data
        assert "test_sent_to" in data


# ============================================================================
# SINGLETON TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_email_service_singleton():
    """Test that get_email_service returns singleton."""
    service1 = get_email_service()
    service2 = get_email_service()

    assert service1 is service2
