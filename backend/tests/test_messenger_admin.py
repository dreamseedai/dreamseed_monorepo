"""
Tests for messenger admin and moderation functionality (Task 3.3).

Tests cover:
- Content moderation with keyword filtering
- User restrictions (mute, ban, restrict)
- Message/conversation deletion by admin
- Report creation and resolution
- Moderation logs and audit trail
- Admin dashboard statistics
- Permission checks
"""

import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.messenger_models import (
    Conversation,
    ConversationParticipant,
    Message,
)
from app.messenger.admin import (
    get_admin_service,
    ModerationAction,
    ReportReason,
    UserRestriction,
)


@pytest.fixture
async def admin_user(db: AsyncSession):
    """Create admin user for testing."""
    admin = User(
        email="admin@test.com",
        hashed_password="hashed",
        role="admin",
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


@pytest.fixture
async def regular_users(db: AsyncSession):
    """Create regular users for testing."""
    users = []
    for i in range(3):
        user = User(
            email=f"user{i}@test.com",
            hashed_password="hashed",
            role="student",
        )
        db.add(user)
        users.append(user)

    await db.commit()
    for user in users:
        await db.refresh(user)

    return users


@pytest.fixture
async def test_conversation(db: AsyncSession, regular_users):
    """Create test conversation with messages."""
    conv = Conversation(
        type="group",
        title="Test Conversation",
    )
    db.add(conv)
    await db.commit()

    # Add participants
    for user in regular_users:
        participant = ConversationParticipant(
            conversation_id=conv.id,
            user_id=user.id,
        )
        db.add(participant)

    # Add messages
    messages = []
    for i, user in enumerate(regular_users):
        msg = Message(
            conversation_id=conv.id,
            sender_id=user.id,
            content=f"Test message {i}",
            message_type="text",
        )
        db.add(msg)
        messages.append(msg)

    await db.commit()

    for msg in messages:
        await db.refresh(msg)

    return {"conversation": conv, "messages": messages}


class TestAdminService:
    """Test AdminService methods."""

    def test_singleton_pattern(self):
        """Test that AdminService uses singleton pattern."""
        service1 = get_admin_service()
        service2 = get_admin_service()

        assert service1 is service2

    def test_keyword_blocking(self):
        """Test keyword blocking functionality."""
        service = get_admin_service()

        # Update blocked keywords
        service.update_blocked_keywords(["spam", "scam", "phishing"])

        # Test blocked content
        result1 = service.check_content_moderation("This is a spam message")
        assert result1["is_allowed"] is False
        assert "spam" in result1["matched_keywords"]

        # Test allowed content
        result2 = service.check_content_moderation("This is a normal message")
        assert result2["is_allowed"] is True
        assert result2["matched_keywords"] == []

    def test_keyword_case_insensitive(self):
        """Test keyword blocking is case-insensitive."""
        service = get_admin_service()

        service.update_blocked_keywords(["spam"])

        # Test different cases
        result1 = service.check_content_moderation("SPAM message")
        assert result1["is_allowed"] is False

        result2 = service.check_content_moderation("Spam message")
        assert result2["is_allowed"] is False

    def test_keyword_word_boundaries(self):
        """Test keyword blocking respects word boundaries."""
        service = get_admin_service()

        service.update_blocked_keywords(["spam"])

        # Should match
        result1 = service.check_content_moderation("This is spam")
        assert result1["is_allowed"] is False

        # Should not match (part of another word)
        result2 = service.check_content_moderation("This is spammer")
        assert result2["is_allowed"] is True

    async def test_get_user_restriction_default(self, db: AsyncSession, regular_users):
        """Test getting user restriction returns NONE by default."""
        service = get_admin_service()

        restriction = await service.get_user_restriction(
            db=db,
            user_id=regular_users[0].id,
        )

        assert restriction == UserRestriction.NONE

    async def test_set_user_restriction(
        self, db: AsyncSession, regular_users, admin_user
    ):
        """Test setting user restriction."""
        service = get_admin_service()

        result = await service.set_user_restriction(
            db=db,
            user_id=regular_users[0].id,
            restriction=UserRestriction.MUTED,
            reason="Spam behavior",
            admin_id=admin_user.id,
            duration_minutes=60,
        )

        assert result["user_id"] == regular_users[0].id
        assert result["restriction"] == "muted"
        assert result["reason"] == "Spam behavior"
        assert result["expires_at"] is not None

    async def test_set_permanent_restriction(
        self, db: AsyncSession, regular_users, admin_user
    ):
        """Test setting permanent restriction."""
        service = get_admin_service()

        result = await service.set_user_restriction(
            db=db,
            user_id=regular_users[0].id,
            restriction=UserRestriction.BANNED,
            reason="Severe violation",
            admin_id=admin_user.id,
            duration_minutes=None,  # Permanent
        )

        assert result["restriction"] == "banned"
        assert result["expires_at"] is None

    async def test_delete_message_by_admin(
        self, db: AsyncSession, test_conversation, admin_user
    ):
        """Test admin deleting a message."""
        service = get_admin_service()

        message = test_conversation["messages"][0]

        result = await service.delete_message_by_admin(
            db=db,
            message_id=message.id,
            admin_id=admin_user.id,
            reason="Inappropriate content",
        )

        assert result["message_id"] == message.id
        assert result["deleted"] is True

        # Verify message was soft deleted
        await db.refresh(message)
        assert message.deleted_at is not None
        assert "[Content removed by moderator]" in message.content

    async def test_delete_message_not_found(self, db: AsyncSession, admin_user):
        """Test deleting non-existent message."""
        service = get_admin_service()

        result = await service.delete_message_by_admin(
            db=db,
            message_id=99999,
            admin_id=admin_user.id,
            reason="Test",
        )

        assert "error" in result

    async def test_delete_conversation_by_admin(
        self, db: AsyncSession, test_conversation, admin_user
    ):
        """Test admin deleting a conversation."""
        service = get_admin_service()

        conv = test_conversation["conversation"]

        result = await service.delete_conversation_by_admin(
            db=db,
            conversation_id=str(conv.id),
            admin_id=admin_user.id,
            reason="Violates guidelines",
        )

        assert result["conversation_id"] == str(conv.id)
        assert result["deleted"] is True

        # Verify all messages were soft deleted
        for msg in test_conversation["messages"]:
            await db.refresh(msg)
            assert msg.deleted_at is not None

    async def test_get_moderation_stats(
        self, db: AsyncSession, test_conversation, admin_user
    ):
        """Test getting moderation statistics."""
        service = get_admin_service()

        # Delete a message first
        await service.delete_message_by_admin(
            db=db,
            message_id=test_conversation["messages"][0].id,
            admin_id=admin_user.id,
            reason="Test",
        )

        stats = await service.get_moderation_stats(db=db, days=7)

        assert "period_days" in stats
        assert "deleted_messages" in stats
        assert stats["deleted_messages"] >= 1

    async def test_get_flagged_messages(
        self, db: AsyncSession, test_conversation, admin_user
    ):
        """Test getting flagged messages."""
        service = get_admin_service()

        # Delete a message to flag it
        await service.delete_message_by_admin(
            db=db,
            message_id=test_conversation["messages"][0].id,
            admin_id=admin_user.id,
            reason="Test",
        )

        flagged = await service.get_flagged_messages(db=db, limit=10, offset=0)

        assert isinstance(flagged, list)
        assert len(flagged) >= 1
        assert flagged[0]["id"] == test_conversation["messages"][0].id

    async def test_create_report(self, db: AsyncSession, regular_users):
        """Test creating a report."""
        service = get_admin_service()

        report = await service.create_report(
            db=db,
            reporter_id=regular_users[0].id,
            reported_user_id=regular_users[1].id,
            reason=ReportReason.SPAM,
            description="User is sending spam",
        )

        assert report["reporter_id"] == regular_users[0].id
        assert report["reported_user_id"] == regular_users[1].id
        assert report["reason"] == "spam"
        assert report["status"] == "pending"

    async def test_create_message_report(
        self, db: AsyncSession, test_conversation, regular_users
    ):
        """Test creating a message report."""
        service = get_admin_service()

        message = test_conversation["messages"][0]

        report = await service.create_report(
            db=db,
            reporter_id=regular_users[1].id,
            message_id=message.id,
            reason=ReportReason.HARASSMENT,
            description="Harassing message",
        )

        assert report["message_id"] == message.id
        assert report["reason"] == "harassment"

    async def test_resolve_report(self, db: AsyncSession, regular_users, admin_user):
        """Test resolving a report."""
        service = get_admin_service()

        # Create report first
        report = await service.create_report(
            db=db,
            reporter_id=regular_users[0].id,
            reported_user_id=regular_users[1].id,
            reason=ReportReason.SPAM,
        )

        # Resolve it
        resolution = await service.resolve_report(
            db=db,
            report_id=report["id"] or 1,
            admin_id=admin_user.id,
            resolution="Warned user, no further action needed",
            action_taken=ModerationAction.WARN,
        )

        assert resolution["status"] == "resolved"
        assert resolution["admin_id"] == admin_user.id
        assert resolution["action_taken"] == "warn"

    async def test_get_admin_dashboard_stats(
        self, db: AsyncSession, test_conversation, regular_users
    ):
        """Test getting admin dashboard statistics."""
        service = get_admin_service()

        stats = await service.get_admin_dashboard_stats(db=db)

        assert "total_users" in stats
        assert "total_conversations" in stats
        assert "total_messages" in stats
        assert "messages_today" in stats
        assert stats["total_users"] >= len(regular_users)
        assert stats["total_conversations"] >= 1
        assert stats["total_messages"] >= len(test_conversation["messages"])


class TestAdminAPIEndpoints:
    """Test admin REST API endpoints."""

    @pytest.mark.asyncio
    async def test_admin_dashboard_requires_admin(self, async_client, regular_users):
        """Test that dashboard requires admin role."""
        with patch(
            "app.routers.messenger.get_current_user", return_value=regular_users[0]
        ):
            response = await async_client.get("/api/v1/messenger/admin/dashboard")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_dashboard_success(self, async_client, admin_user):
        """Test admin dashboard endpoint."""
        with patch("app.routers.messenger.get_current_user", return_value=admin_user):
            response = await async_client.get("/api/v1/messenger/admin/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_messages" in data

    @pytest.mark.asyncio
    async def test_get_moderation_stats(self, async_client, admin_user):
        """Test moderation stats endpoint."""
        with patch("app.routers.messenger.get_current_user", return_value=admin_user):
            response = await async_client.get(
                "/api/v1/messenger/admin/moderation/stats",
                params={"days": 30},
            )

        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "deleted_messages" in data

    @pytest.mark.asyncio
    async def test_delete_message_by_admin(
        self, async_client, admin_user, test_conversation
    ):
        """Test admin message deletion endpoint."""
        message = test_conversation["messages"][0]

        with patch("app.routers.messenger.get_current_user", return_value=admin_user):
            response = await async_client.delete(
                f"/api/v1/messenger/admin/messages/{message.id}",
                params={"reason": "Test deletion for inappropriate content"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True

    @pytest.mark.asyncio
    async def test_set_user_restriction(self, async_client, admin_user, regular_users):
        """Test setting user restriction endpoint."""
        with patch("app.routers.messenger.get_current_user", return_value=admin_user):
            response = await async_client.post(
                f"/api/v1/messenger/admin/users/{regular_users[0].id}/restriction",
                params={
                    "restriction": "muted",
                    "reason": "Spam behavior detected",
                    "duration_minutes": 60,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["restriction"] == "muted"

    @pytest.mark.asyncio
    async def test_create_report(self, async_client, regular_users, test_conversation):
        """Test creating a report (any user can do this)."""
        message = test_conversation["messages"][0]

        with patch(
            "app.routers.messenger.get_current_user", return_value=regular_users[1]
        ):
            response = await async_client.post(
                "/api/v1/messenger/reports",
                params={
                    "message_id": message.id,
                    "reason": "spam",
                    "description": "This message contains spam",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["reason"] == "spam"

    @pytest.mark.asyncio
    async def test_create_report_no_target(self, async_client, regular_users):
        """Test creating report without target fails."""
        with patch(
            "app.routers.messenger.get_current_user", return_value=regular_users[0]
        ):
            response = await async_client.post(
                "/api/v1/messenger/reports",
                params={"reason": "spam"},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_blocked_keywords(self, async_client, admin_user):
        """Test updating blocked keywords."""
        with patch("app.routers.messenger.get_current_user", return_value=admin_user):
            response = await async_client.post(
                "/api/v1/messenger/admin/keywords",
                params={"keywords": ["spam", "scam", "phishing"]},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["keywords"]) == 3
        assert "spam" in data["keywords"]

    @pytest.mark.asyncio
    async def test_get_blocked_keywords(self, async_client, admin_user):
        """Test getting blocked keywords."""
        with patch("app.routers.messenger.get_current_user", return_value=admin_user):
            response = await async_client.get("/api/v1/messenger/admin/keywords")

        assert response.status_code == 200
        data = response.json()
        assert "keywords" in data
        assert "count" in data


# Run tests with: pytest tests/test_messenger_admin.py -v
