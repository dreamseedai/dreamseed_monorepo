"""
Tests for messenger search functionality (Task 3.2).

Tests cover:
- Message full-text search with PostgreSQL ts_rank
- Simple in-chat message search
- Conversation search and discovery
- User search and autocomplete
- Permission checks
- Search result ranking
- Pagination
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.messenger_models import (
    Conversation,
    ConversationParticipant,
    Message,
)
from app.messenger.search import (
    get_search_service,
    SortOrder,
    MessageType,
)


@pytest.fixture
async def test_users(db: AsyncSession):
    """Create test users."""
    users = []
    for i in range(5):
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
async def test_conversations(db: AsyncSession, test_users):
    """Create test conversations."""
    conversations = []

    # Direct conversation
    conv1 = Conversation(
        conversation_id="conv_001",
        type="direct",
        title="Direct Chat",
    )
    db.add(conv1)
    conversations.append(conv1)

    # Group conversation
    conv2 = Conversation(
        conversation_id="conv_002",
        type="group",
        title="Project Budget Discussion",
    )
    db.add(conv2)
    conversations.append(conv2)

    # Zone conversation
    conv3 = Conversation(
        conversation_id="conv_003",
        type="announcement",
        title="Zone Announcements",
        zone_id=1,
    )
    db.add(conv3)
    conversations.append(conv3)

    await db.commit()

    # Add participants
    for conv in conversations:
        for user in test_users[:3]:  # First 3 users
            participant = ConversationParticipant(
                conversation_id=conv.conversation_id,
                user_id=user.id,
            )
            db.add(participant)

    await db.commit()

    return conversations


@pytest.fixture
async def test_messages(db: AsyncSession, test_conversations, test_users):
    """Create test messages."""
    messages = []

    # Messages with various content
    contents = [
        "Let's discuss the budget for next quarter",
        "The budget needs to be approved by Friday",
        "Can we schedule a meeting about the project timeline?",
        "I've uploaded the quarterly report",
        "System message: User joined the conversation",
    ]

    for i, content in enumerate(contents):
        msg = Message(
            conversation_id=test_conversations[
                i % len(test_conversations)
            ].conversation_id,
            sender_id=test_users[i % len(test_users)].id,
            content=content,
            type=(
                MessageType.SYSTEM.value
                if "System" in content
                else MessageType.TEXT.value
            ),
            created_at=datetime.utcnow() - timedelta(days=i),
        )
        db.add(msg)
        messages.append(msg)

    await db.commit()

    for msg in messages:
        await db.refresh(msg)

    return messages


class TestSearchService:
    """Test SearchService methods."""

    async def test_search_messages_basic(
        self, db: AsyncSession, test_messages, test_users
    ):
        """Test basic message search."""
        service = get_search_service()

        result = await service.search_messages(
            db=db,
            query="budget",
            user_id=test_users[0].id,
        )

        assert result["query"] == "budget"
        assert result["total_count"] >= 2  # At least 2 messages contain "budget"
        assert len(result["results"]) >= 2
        assert result["has_more"] is False

    async def test_search_messages_with_conversation_filter(
        self, db: AsyncSession, test_messages, test_users, test_conversations
    ):
        """Test message search filtered by conversation."""
        service = get_search_service()

        result = await service.search_messages(
            db=db,
            query="budget",
            user_id=test_users[0].id,
            conversation_id=test_conversations[1].conversation_id,
        )

        assert result["total_count"] >= 1
        for msg in result["results"]:
            assert msg["conversation_id"] == test_conversations[1].conversation_id

    async def test_search_messages_with_sender_filter(
        self, db: AsyncSession, test_messages, test_users
    ):
        """Test message search filtered by sender."""
        service = get_search_service()

        result = await service.search_messages(
            db=db,
            query="budget",
            user_id=test_users[0].id,
            sender_id=test_users[1].id,
        )

        for msg in result["results"]:
            assert msg["sender_id"] == test_users[1].id

    async def test_search_messages_with_type_filter(
        self, db: AsyncSession, test_messages, test_users
    ):
        """Test message search filtered by message type."""
        service = get_search_service()

        result = await service.search_messages(
            db=db,
            query="System",
            user_id=test_users[0].id,
            message_type=MessageType.SYSTEM,
        )

        for msg in result["results"]:
            assert msg["type"] == MessageType.SYSTEM.value

    async def test_search_messages_with_date_range(
        self, db: AsyncSession, test_messages, test_users
    ):
        """Test message search with date range filter."""
        service = get_search_service()

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=2)

        result = await service.search_messages(
            db=db,
            query="budget",
            user_id=test_users[0].id,
            start_date=start_date,
            end_date=end_date,
        )

        for msg in result["results"]:
            msg_date = datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00"))
            assert start_date <= msg_date <= end_date

    async def test_search_messages_sorting(
        self, db: AsyncSession, test_messages, test_users
    ):
        """Test message search with different sort orders."""
        service = get_search_service()

        # Sort by date descending
        result_desc = await service.search_messages(
            db=db,
            query="budget",
            user_id=test_users[0].id,
            sort_by=SortOrder.DATE_DESC,
        )

        # Sort by date ascending
        result_asc = await service.search_messages(
            db=db,
            query="budget",
            user_id=test_users[0].id,
            sort_by=SortOrder.DATE_ASC,
        )

        if len(result_desc["results"]) > 1:
            # Check descending order
            dates_desc = [
                datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00"))
                for msg in result_desc["results"]
            ]
            assert dates_desc == sorted(dates_desc, reverse=True)

            # Check ascending order
            dates_asc = [
                datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00"))
                for msg in result_asc["results"]
            ]
            assert dates_asc == sorted(dates_asc)

    async def test_search_messages_pagination(
        self, db: AsyncSession, test_messages, test_users
    ):
        """Test message search pagination."""
        service = get_search_service()

        # First page
        page1 = await service.search_messages(
            db=db,
            query="the",  # Common word
            user_id=test_users[0].id,
            limit=2,
            offset=0,
        )

        # Second page
        page2 = await service.search_messages(
            db=db,
            query="the",
            user_id=test_users[0].id,
            limit=2,
            offset=2,
        )

        assert page1["limit"] == 2
        assert page2["offset"] == 2

        if page1["total_count"] > 2:
            assert page1["has_more"] is True

    async def test_search_messages_permission_check(
        self, db: AsyncSession, test_messages, test_users
    ):
        """Test that users can only search messages in their conversations."""
        service = get_search_service()

        # User 4 is not a participant in any conversation
        result = await service.search_messages(
            db=db,
            query="budget",
            user_id=test_users[4].id,
        )

        assert result["total_count"] == 0
        assert len(result["results"]) == 0

    async def test_search_messages_simple(
        self, db: AsyncSession, test_messages, test_users, test_conversations
    ):
        """Test simple in-chat message search."""
        service = get_search_service()

        result = await service.search_messages_simple(
            db=db,
            query="budget",
            user_id=test_users[0].id,
            conversation_id=test_conversations[1].conversation_id,
        )

        assert isinstance(result, list)
        for msg in result:
            assert msg["conversation_id"] == test_conversations[1].conversation_id
            assert "budget" in msg["content"].lower()

    async def test_search_conversations(
        self, db: AsyncSession, test_conversations, test_users
    ):
        """Test conversation search."""
        service = get_search_service()

        result = await service.search_conversations(
            db=db,
            query="Budget",
            user_id=test_users[0].id,
        )

        assert result["query"] == "Budget"
        assert result["total_count"] >= 1

        found = False
        for conv in result["results"]:
            if "budget" in conv["title"].lower():
                found = True
                break
        assert found

    async def test_search_conversations_with_type_filter(
        self, db: AsyncSession, test_conversations, test_users
    ):
        """Test conversation search filtered by type."""
        service = get_search_service()

        result = await service.search_conversations(
            db=db,
            query="",  # Empty query to get all
            user_id=test_users[0].id,
            conversation_type="group",
        )

        for conv in result["results"]:
            assert conv["type"] == "group"

    async def test_discover_conversations(
        self, db: AsyncSession, test_conversations, test_users
    ):
        """Test conversation discovery."""
        service = get_search_service()

        # User 4 is not a participant, should see zone conversations
        result = await service.discover_conversations(
            db=db,
            user_id=test_users[4].id,
        )

        assert isinstance(result, list)
        for conv in result:
            assert conv["type"] in ["zone", "org"]

    async def test_discover_conversations_with_zone_filter(
        self, db: AsyncSession, test_conversations, test_users
    ):
        """Test conversation discovery filtered by zone."""
        service = get_search_service()

        result = await service.discover_conversations(
            db=db,
            user_id=test_users[4].id,
            zone_id=1,
        )

        for conv in result:
            assert conv.get("zone_id") == 1

    async def test_search_users(self, db: AsyncSession, test_users):
        """Test user search."""
        service = get_search_service()

        result = await service.search_users(
            db=db,
            query="user1",
            current_user_id=test_users[0].id,
        )

        assert result["query"] == "user1"
        assert result["total_count"] >= 1

        found = False
        for user in result["results"]:
            if "user1" in user["email"].lower():
                found = True
                break
        assert found

    async def test_autocomplete_users(self, db: AsyncSession, test_users):
        """Test user autocomplete."""
        service = get_search_service()

        result = await service.autocomplete_users(
            db=db,
            query="user",
            current_user_id=test_users[0].id,
        )

        assert isinstance(result, list)
        assert len(result) > 0

        for user in result:
            assert "user" in user["email"].lower()

    async def test_autocomplete_users_with_conversation(
        self, db: AsyncSession, test_users, test_conversations
    ):
        """Test user autocomplete prioritizing conversation participants."""
        service = get_search_service()

        result = await service.autocomplete_users(
            db=db,
            query="user",
            current_user_id=test_users[0].id,
            conversation_id=test_conversations[0].conversation_id,
        )

        # Participants should come first
        if len(result) > 0:
            first_user = result[0]
            assert (
                first_user.get("is_participant") is True
                or first_user.get("is_participant") is None
            )

    async def test_highlight_terms(self):
        """Test search term highlighting."""
        service = get_search_service()

        text = "This is a test message about budget planning"
        query = "budget"

        highlighted = service._highlight_terms(text, query)

        assert "<mark>" in highlighted
        assert "</mark>" in highlighted
        assert "budget" in highlighted.lower()


class TestSearchAPIEndpoints:
    """Test search REST API endpoints."""

    @pytest.mark.asyncio
    async def test_search_messages_endpoint(
        self, async_client, test_messages, test_users
    ):
        """Test message search API endpoint."""
        # Mock authentication
        with patch(
            "app.routers.messenger.get_current_user", return_value=test_users[0]
        ):
            response = await async_client.get(
                "/api/v1/messenger/search/messages",
                params={"query": "budget"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "total_count" in data
        assert "results" in data

    @pytest.mark.asyncio
    async def test_search_messages_with_filters_endpoint(
        self, async_client, test_messages, test_users, test_conversations
    ):
        """Test message search with filters."""
        with patch(
            "app.routers.messenger.get_current_user", return_value=test_users[0]
        ):
            response = await async_client.get(
                "/api/v1/messenger/search/messages",
                params={
                    "query": "budget",
                    "conversation_id": test_conversations[1].conversation_id,
                    "sort_by": "date_desc",
                    "limit": 20,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 20

    @pytest.mark.asyncio
    async def test_search_messages_invalid_type(self, async_client, test_users):
        """Test message search with invalid message type."""
        with patch(
            "app.routers.messenger.get_current_user", return_value=test_users[0]
        ):
            response = await async_client.get(
                "/api/v1/messenger/search/messages",
                params={
                    "query": "test",
                    "message_type": "invalid_type",
                },
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_search_conversations_endpoint(
        self, async_client, test_conversations, test_users
    ):
        """Test conversation search API endpoint."""
        with patch(
            "app.routers.messenger.get_current_user", return_value=test_users[0]
        ):
            response = await async_client.get(
                "/api/v1/messenger/search/conversations",
                params={"query": "Budget"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    @pytest.mark.asyncio
    async def test_discover_conversations_endpoint(self, async_client, test_users):
        """Test conversation discovery API endpoint."""
        with patch(
            "app.routers.messenger.get_current_user", return_value=test_users[4]
        ):
            response = await async_client.get(
                "/api/v1/messenger/discover/conversations",
            )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    @pytest.mark.asyncio
    async def test_search_users_endpoint(self, async_client, test_users):
        """Test user search API endpoint."""
        with patch(
            "app.routers.messenger.get_current_user", return_value=test_users[0]
        ):
            response = await async_client.get(
                "/api/v1/messenger/search/users",
                params={"query": "user1"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    @pytest.mark.asyncio
    async def test_autocomplete_users_endpoint(self, async_client, test_users):
        """Test user autocomplete API endpoint."""
        with patch(
            "app.routers.messenger.get_current_user", return_value=test_users[0]
        ):
            response = await async_client.get(
                "/api/v1/messenger/autocomplete/users",
                params={"query": "user"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data


# Run tests with: pytest tests/test_messenger_search.py -v
