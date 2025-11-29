"""
Tests for Message Reactions Feature

Test Coverage:
- ReactionsService methods
- REST API endpoints
- WebSocket event handlers
- Database constraints and triggers
- Edge cases and error handling
"""

import pytest
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.messenger.reactions import get_reactions_service
from app.models.messenger_models import (
    Conversation,
    ConversationParticipant,
    Message,
)
from app.models.user import User


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user2(db_session: AsyncSession) -> User:
    """Create second test user."""
    user = User(
        id=2,
        email="test2@example.com",
        username="testuser2",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_conversation(
    db_session: AsyncSession, test_user: User, test_user2: User
) -> Conversation:
    """Create test conversation with two participants."""
    conversation = Conversation(
        id=uuid.uuid4(),
        type="group",
        name="Test Conversation",
    )
    db_session.add(conversation)

    # Add participants
    participant1 = ConversationParticipant(
        conversation_id=conversation.id,
        user_id=test_user.id,
        role="admin",
    )
    participant2 = ConversationParticipant(
        conversation_id=conversation.id,
        user_id=test_user2.id,
        role="member",
    )

    db_session.add(participant1)
    db_session.add(participant2)

    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


@pytest.fixture
async def test_message(
    db_session: AsyncSession, test_conversation: Conversation, test_user: User
) -> Message:
    """Create test message."""
    message = Message(
        id=uuid.uuid4(),
        conversation_id=test_conversation.id,
        sender_id=test_user.id,
        content="Test message",
        reaction_count=0,
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    return message


# ============================================================================
# ReactionsService Tests
# ============================================================================


@pytest.mark.asyncio
class TestReactionsService:
    """Test ReactionsService methods."""

    async def test_add_reaction_success(
        self, db_session: AsyncSession, test_message: Message, test_user: User
    ):
        """Test successfully adding a reaction."""
        service = get_reactions_service()

        reaction = await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        assert reaction.id is not None
        assert reaction.message_id == test_message.id
        assert reaction.user_id == test_user.id
        assert reaction.emoji == "thumbs_up"
        assert reaction.emoji_unicode == "👍"
        assert reaction.created_at is not None

    async def test_add_reaction_with_unicode(
        self, db_session: AsyncSession, test_message: Message, test_user: User
    ):
        """Test adding reaction with unicode emoji."""
        service = get_reactions_service()

        reaction = await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="❤️",
        )

        assert reaction.emoji == "❤️"
        assert reaction.emoji_unicode == "❤️"

    async def test_add_duplicate_reaction_fails(
        self, db_session: AsyncSession, test_message: Message, test_user: User
    ):
        """Test that adding duplicate reaction raises error."""
        service = get_reactions_service()

        # Add first reaction
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        # Try to add duplicate
        with pytest.raises(ValueError, match="already reacted"):
            await service.add_reaction(
                db=db_session,
                message_id=test_message.id,
                user_id=int(test_user.id),  # type: ignore
                emoji="thumbs_up",
            )

    async def test_add_reaction_to_nonexistent_message(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test adding reaction to non-existent message."""
        service = get_reactions_service()
        fake_message_id = uuid.uuid4()

        with pytest.raises(ValueError, match="not found"):
            await service.add_reaction(
                db=db_session,
                message_id=fake_message_id,
                user_id=int(test_user.id),  # type: ignore
                emoji="thumbs_up",
            )

    async def test_add_reaction_by_non_participant(
        self, db_session: AsyncSession, test_message: Message
    ):
        """Test adding reaction by user who is not a participant."""
        service = get_reactions_service()
        non_participant_id = 999

        with pytest.raises(ValueError, match="not a participant"):
            await service.add_reaction(
                db=db_session,
                message_id=test_message.id,
                user_id=non_participant_id,
                emoji="thumbs_up",
            )

    async def test_remove_reaction_success(
        self, db_session: AsyncSession, test_message: Message, test_user: User
    ):
        """Test successfully removing a reaction."""
        service = get_reactions_service()

        # Add reaction first
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        # Remove it
        removed = await service.remove_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        assert removed is True

    async def test_remove_nonexistent_reaction(
        self, db_session: AsyncSession, test_message: Message, test_user: User
    ):
        """Test removing non-existent reaction returns False."""
        service = get_reactions_service()

        removed = await service.remove_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        assert removed is False

    async def test_toggle_reaction_add(
        self, db_session: AsyncSession, test_message: Message, test_user: User
    ):
        """Test toggling adds reaction when it doesn't exist."""
        service = get_reactions_service()

        result = await service.toggle_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="heart",
        )

        assert result["action"] == "added"
        assert result["emoji"] == "heart"
        assert "reaction_id" in result

    async def test_toggle_reaction_remove(
        self, db_session: AsyncSession, test_message: Message, test_user: User
    ):
        """Test toggling removes reaction when it exists."""
        service = get_reactions_service()

        # Add reaction first
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="heart",
        )

        # Toggle (should remove)
        result = await service.toggle_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="heart",
        )

        assert result["action"] == "removed"
        assert result["emoji"] == "heart"

    async def test_get_message_reactions_grouped(
        self,
        db_session: AsyncSession,
        test_message: Message,
        test_user: User,
        test_user2: User,
    ):
        """Test getting reactions grouped by emoji."""
        service = get_reactions_service()

        # Add multiple reactions
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user2.id),  # type: ignore
            emoji="thumbs_up",
        )
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="heart",
        )

        # Get reactions
        result = await service.get_message_reactions(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
        )

        assert result["total_reactions"] == 3
        assert len(result["reactions"]) == 2  # Two unique emojis

        # Find thumbs_up group
        thumbs_up = next(r for r in result["reactions"] if r["emoji"] == "thumbs_up")
        assert thumbs_up["count"] == 2
        assert test_user.id in thumbs_up["users"]
        assert test_user2.id in thumbs_up["users"]
        assert thumbs_up["user_reacted"] is True

    async def test_get_user_reactions(
        self,
        db_session: AsyncSession,
        test_message: Message,
        test_conversation: Conversation,
        test_user: User,
    ):
        """Test getting all reactions by a user."""
        service = get_reactions_service()

        # Add some reactions
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="heart",
        )

        # Get user reactions
        reactions = await service.get_user_reactions(
            db=db_session,
            user_id=int(test_user.id),  # type: ignore
            conversation_id=test_conversation.id,
        )

        assert len(reactions) == 2
        assert all(r["message_id"] == str(test_message.id) for r in reactions)

    async def test_get_popular_reactions(
        self,
        db_session: AsyncSession,
        test_message: Message,
        test_conversation: Conversation,
        test_user: User,
        test_user2: User,
    ):
        """Test getting popular reactions in conversation."""
        service = get_reactions_service()

        # Add reactions (thumbs_up more popular)
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user2.id),  # type: ignore
            emoji="thumbs_up",
        )
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="heart",
        )

        # Get popular reactions
        popular = await service.get_popular_reactions(
            db=db_session,
            conversation_id=test_conversation.id,
            user_id=int(test_user.id),  # type: ignore
            limit=10,
        )

        assert len(popular) == 2
        assert popular[0]["emoji"] == "thumbs_up"  # Most popular first
        assert popular[0]["count"] == 2
        assert popular[1]["emoji"] == "heart"
        assert popular[1]["count"] == 1

    async def test_get_reaction_summary(
        self, db_session: AsyncSession, test_message: Message, test_user: User
    ):
        """Test getting quick reaction summary."""
        service = get_reactions_service()

        # Add reactions
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="heart",
        )

        # Get summary
        summary = await service.get_reaction_summary(
            db=db_session,
            message_id=test_message.id,
        )

        assert summary["total_reactions"] == 2
        assert summary["unique_emoji"] == 2

    async def test_emoji_map_coverage(self):
        """Test that emoji map has good coverage."""
        service = get_reactions_service()
        supported = service.get_supported_emoji()

        # Should have at least 70 emoji
        assert len(supported) >= 70

        # Check common emoji exist
        shortcodes = [e["shortcode"] for e in supported]
        assert "thumbs_up" in shortcodes
        assert "heart" in shortcodes
        assert "smile" in shortcodes
        assert "fire" in shortcodes

    async def test_reaction_count_auto_updates(
        self, db_session: AsyncSession, test_message: Message, test_user: User
    ):
        """Test that message.reaction_count is automatically updated by trigger."""
        service = get_reactions_service()

        # Check initial count
        await db_session.refresh(test_message)
        assert test_message.reaction_count == 0

        # Add reaction
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        # Refresh and check count updated
        await db_session.refresh(test_message)
        assert test_message.reaction_count == 1

        # Remove reaction
        await service.remove_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        # Check count decremented
        await db_session.refresh(test_message)
        assert test_message.reaction_count == 0


# ============================================================================
# REST API Tests
# ============================================================================


@pytest.mark.asyncio
class TestReactionsAPI:
    """Test REST API endpoints for reactions."""

    async def test_add_reaction_endpoint(
        self, client, test_message: Message, test_user: User, auth_headers
    ):
        """Test POST /messages/{id}/reactions endpoint."""
        response = await client.post(
            f"/api/v1/messenger/messages/{test_message.id}/reactions?emoji=thumbs_up",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["emoji"] == "thumbs_up"
        assert data["emoji_unicode"] == "👍"
        assert data["message_id"] == str(test_message.id)

    async def test_remove_reaction_endpoint(
        self, client, test_message: Message, test_user: User, auth_headers, db_session
    ):
        """Test DELETE /messages/{id}/reactions/{emoji} endpoint."""
        # Add reaction first
        service = get_reactions_service()
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        # Remove via API
        response = await client.delete(
            f"/api/v1/messenger/messages/{test_message.id}/reactions/thumbs_up",
            headers=auth_headers,
        )

        assert response.status_code == 204

    async def test_toggle_reaction_endpoint(
        self, client, test_message: Message, auth_headers
    ):
        """Test POST /messages/{id}/reactions/toggle endpoint."""
        # Toggle on (add)
        response = await client.post(
            f"/api/v1/messenger/messages/{test_message.id}/reactions/toggle?emoji=heart",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "added"

        # Toggle off (remove)
        response = await client.post(
            f"/api/v1/messenger/messages/{test_message.id}/reactions/toggle?emoji=heart",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "removed"

    async def test_get_message_reactions_endpoint(
        self, client, test_message: Message, test_user: User, auth_headers, db_session
    ):
        """Test GET /messages/{id}/reactions endpoint."""
        # Add reactions
        service = get_reactions_service()
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        # Get via API
        response = await client.get(
            f"/api/v1/messenger/messages/{test_message.id}/reactions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_reactions"] == 1
        assert len(data["reactions"]) == 1

    async def test_get_reaction_summary_endpoint(
        self, client, test_message: Message, test_user: User, auth_headers, db_session
    ):
        """Test GET /messages/{id}/reactions/summary endpoint."""
        # Add reactions
        service = get_reactions_service()
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        # Get summary
        response = await client.get(
            f"/api/v1/messenger/messages/{test_message.id}/reactions/summary",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_reactions"] == 1
        assert data["unique_emoji"] == 1

    async def test_get_popular_reactions_endpoint(
        self,
        client,
        test_conversation: Conversation,
        test_message: Message,
        test_user: User,
        auth_headers,
        db_session,
    ):
        """Test GET /conversations/{id}/reactions/popular endpoint."""
        # Add reactions
        service = get_reactions_service()
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="fire",
        )

        # Get popular
        response = await client.get(
            f"/api/v1/messenger/conversations/{test_conversation.id}/reactions/popular",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "popular_reactions" in data
        assert len(data["popular_reactions"]) >= 1

    async def test_get_supported_emoji_endpoint(self, client):
        """Test GET /reactions/emoji endpoint."""
        response = await client.get("/api/v1/messenger/reactions/emoji")

        assert response.status_code == 200
        data = response.json()
        assert "emoji" in data
        assert "count" in data
        assert data["count"] >= 70


# ============================================================================
# WebSocket Tests
# ============================================================================


@pytest.mark.asyncio
class TestReactionsWebSocket:
    """Test WebSocket events for reactions."""

    async def test_reaction_add_websocket(
        self, websocket_client, test_message: Message, test_user: User
    ):
        """Test reaction.add WebSocket event."""
        # Send reaction.add event
        await websocket_client.send_json(
            {
                "type": "reaction.add",
                "message_id": str(test_message.id),
                "emoji": "thumbs_up",
            }
        )

        # Should receive confirmation
        response = await websocket_client.receive_json()
        assert response["type"] == "reaction.confirmed"
        assert response["action"] == "added"

    async def test_reaction_remove_websocket(
        self,
        websocket_client,
        test_message: Message,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Test reaction.remove WebSocket event."""
        # Add reaction first
        service = get_reactions_service()
        await service.add_reaction(
            db=db_session,
            message_id=test_message.id,
            user_id=int(test_user.id),  # type: ignore
            emoji="thumbs_up",
        )

        # Send reaction.remove event
        await websocket_client.send_json(
            {
                "type": "reaction.remove",
                "message_id": str(test_message.id),
                "emoji": "thumbs_up",
            }
        )

        # Should receive confirmation
        response = await websocket_client.receive_json()
        assert response["type"] == "reaction.confirmed"
        assert response["action"] == "removed"

    async def test_reaction_toggle_websocket(
        self, websocket_client, test_message: Message
    ):
        """Test reaction.toggle WebSocket event."""
        # Send reaction.toggle event
        await websocket_client.send_json(
            {
                "type": "reaction.toggle",
                "message_id": str(test_message.id),
                "emoji": "heart",
            }
        )

        # Should receive confirmation
        response = await websocket_client.receive_json()
        assert response["type"] == "reaction.confirmed"
        assert response["action"] in ["added", "removed"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
