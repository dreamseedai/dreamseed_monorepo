"""
Tests for Message Threading Service (Task 5.1)

Tests threading functionality including:
- Reply creation
- Thread retrieval
- Thread summaries
- Thread listing
- Thread deletion
- Thread participants
- WebSocket integration
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_models import (
    Conversation,
    ConversationParticipant,
    Message,
)
from app.messenger.threading import ThreadingService, get_threading_service


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def sample_conversation_id():
    """Sample conversation UUID."""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return 1


@pytest.fixture
def sample_parent_message(sample_conversation_id, sample_user_id):
    """Sample parent message."""
    return Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="This is the parent message",
        message_type="text",
        reply_count=0,
        last_reply_at=None,
        parent_id=None,
        thread_id=None,
    )


@pytest.fixture
def sample_participant(sample_conversation_id, sample_user_id):
    """Sample conversation participant."""
    return ConversationParticipant(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        user_id=sample_user_id,
        role="member",
    )


# ============================================================================
# Threading Service Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_reply_success(
    mock_db,
    sample_conversation_id,
    sample_user_id,
    sample_parent_message,
    sample_participant,
):
    """Test creating a reply to a message."""
    # Setup mocks
    mock_db.execute.side_effect = [
        # Parent message lookup
        AsyncMock(scalar_one_or_none=lambda: sample_parent_message),
        # Participant lookup
        AsyncMock(scalar_one_or_none=lambda: sample_participant),
    ]

    service = ThreadingService()

    # Create reply
    reply = await service.create_reply(
        db=mock_db,
        conversation_id=sample_conversation_id,
        parent_message_id=sample_parent_message.id,
        sender_id=sample_user_id,
        content="This is a reply",
        message_type="text",
    )

    # Verify reply was created
    assert reply.conversation_id == sample_conversation_id
    assert reply.sender_id == sample_user_id
    assert reply.content == "This is a reply"
    assert reply.parent_id == sample_parent_message.id
    assert reply.thread_id == sample_parent_message.id  # Parent is root

    # Verify parent message was updated
    assert sample_parent_message.reply_count == 1
    assert sample_parent_message.last_reply_at is not None

    # Verify DB operations
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_reply_nested(
    mock_db,
    sample_conversation_id,
    sample_user_id,
    sample_parent_message,
    sample_participant,
):
    """Test creating a nested reply (reply to a reply)."""
    # Create a first-level reply
    first_reply = Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="First reply",
        message_type="text",
        reply_count=0,
        parent_id=sample_parent_message.id,
        thread_id=sample_parent_message.id,
    )

    # Setup mocks
    mock_db.execute.side_effect = [
        # Parent (first reply) lookup
        AsyncMock(scalar_one_or_none=lambda: first_reply),
        # Participant lookup
        AsyncMock(scalar_one_or_none=lambda: sample_participant),
        # Root message lookup
        AsyncMock(scalar_one_or_none=lambda: sample_parent_message),
    ]

    service = ThreadingService()

    # Create nested reply
    nested_reply = await service.create_reply(
        db=mock_db,
        conversation_id=sample_conversation_id,
        parent_message_id=first_reply.id,
        sender_id=sample_user_id,
        content="Nested reply",
        message_type="text",
    )

    # Verify nested reply
    assert nested_reply.parent_id == first_reply.id
    assert nested_reply.thread_id == sample_parent_message.id  # Points to root

    # Verify both messages updated
    assert first_reply.reply_count == 1
    assert sample_parent_message.reply_count == 1


@pytest.mark.asyncio
async def test_create_reply_parent_not_found(
    mock_db,
    sample_conversation_id,
    sample_user_id,
):
    """Test creating reply when parent message doesn't exist."""
    # Setup mock - parent not found
    mock_db.execute.return_value = AsyncMock(scalar_one_or_none=lambda: None)

    service = ThreadingService()

    # Attempt to create reply
    with pytest.raises(ValueError, match="Parent message .* not found"):
        await service.create_reply(
            db=mock_db,
            conversation_id=sample_conversation_id,
            parent_message_id=uuid4(),
            sender_id=sample_user_id,
            content="Reply",
        )


@pytest.mark.asyncio
async def test_create_reply_not_participant(
    mock_db,
    sample_conversation_id,
    sample_user_id,
    sample_parent_message,
):
    """Test creating reply when user is not a participant."""
    # Setup mocks
    mock_db.execute.side_effect = [
        # Parent message lookup
        AsyncMock(scalar_one_or_none=lambda: sample_parent_message),
        # Participant lookup - not found
        AsyncMock(scalar_one_or_none=lambda: None),
    ]

    service = ThreadingService()

    # Attempt to create reply
    with pytest.raises(ValueError, match="not a participant"):
        await service.create_reply(
            db=mock_db,
            conversation_id=sample_conversation_id,
            parent_message_id=sample_parent_message.id,
            sender_id=sample_user_id,
            content="Reply",
        )


@pytest.mark.asyncio
async def test_get_thread(
    mock_db,
    sample_conversation_id,
    sample_user_id,
    sample_parent_message,
    sample_participant,
):
    """Test getting a complete thread."""
    # Create replies
    reply1 = Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="Reply 1",
        message_type="text",
        parent_id=sample_parent_message.id,
        thread_id=sample_parent_message.id,
        created_at=datetime.utcnow(),
    )

    reply2 = Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="Reply 2",
        message_type="text",
        parent_id=sample_parent_message.id,
        thread_id=sample_parent_message.id,
        created_at=datetime.utcnow(),
    )

    # Setup mocks
    mock_db.execute.side_effect = [
        # Root message lookup
        AsyncMock(scalar_one_or_none=lambda: sample_parent_message),
        # Participant lookup
        AsyncMock(scalar_one_or_none=lambda: sample_participant),
        # All messages in thread
        AsyncMock(
            scalars=lambda: AsyncMock(
                all=lambda: [sample_parent_message, reply1, reply2]
            )
        ),
    ]

    service = ThreadingService()

    # Get thread
    thread = await service.get_thread(
        db=mock_db,
        thread_root_id=sample_parent_message.id,
        user_id=sample_user_id,
    )

    # Verify thread structure
    assert thread["id"] == str(sample_parent_message.id)
    assert thread["content"] == sample_parent_message.content
    assert len(thread["replies"]) == 2


@pytest.mark.asyncio
async def test_get_thread_summary(
    mock_db,
    sample_conversation_id,
    sample_user_id,
    sample_parent_message,
    sample_participant,
):
    """Test getting thread summary."""
    # Create latest reply
    latest_reply = Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="Latest reply",
        message_type="text",
        parent_id=sample_parent_message.id,
        thread_id=sample_parent_message.id,
        created_at=datetime.utcnow(),
    )

    # Setup mocks
    sample_parent_message.reply_count = 5
    sample_parent_message.last_reply_at = datetime.utcnow()

    mock_db.execute.side_effect = [
        # Root message lookup
        AsyncMock(scalar_one_or_none=lambda: sample_parent_message),
        # Participant lookup
        AsyncMock(scalar_one_or_none=lambda: sample_participant),
        # Unique participants count
        AsyncMock(scalar=lambda: 3),
        # Latest reply
        AsyncMock(scalar_one_or_none=lambda: latest_reply),
    ]

    service = ThreadingService()

    # Get summary
    summary = await service.get_thread_summary(
        db=mock_db,
        thread_root_id=sample_parent_message.id,
        user_id=sample_user_id,
    )

    # Verify summary
    assert summary["thread_id"] == str(sample_parent_message.id)
    assert summary["reply_count"] == 5
    assert summary["unique_participants"] == 3
    assert summary["latest_reply"]["id"] == str(latest_reply.id)


@pytest.mark.asyncio
async def test_list_threads_recent(
    mock_db,
    sample_conversation_id,
    sample_user_id,
    sample_participant,
):
    """Test listing threads sorted by recent activity."""
    # Create thread roots
    thread1 = Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="Thread 1",
        message_type="text",
        parent_id=None,
        thread_id=None,
        reply_count=5,
        last_reply_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )

    thread2 = Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="Thread 2",
        message_type="text",
        parent_id=None,
        thread_id=None,
        reply_count=2,
        last_reply_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )

    # Setup mocks
    mock_db.execute.side_effect = [
        # Participant lookup
        AsyncMock(scalar_one_or_none=lambda: sample_participant),
        # Thread roots
        AsyncMock(scalars=lambda: AsyncMock(all=lambda: [thread1, thread2])),
        # Latest replies (2 queries)
        AsyncMock(scalar_one_or_none=lambda: None),
        AsyncMock(scalar_one_or_none=lambda: None),
    ]

    service = ThreadingService()

    # List threads
    threads = await service.list_threads(
        db=mock_db,
        conversation_id=sample_conversation_id,
        user_id=sample_user_id,
        sort_by="recent",
    )

    # Verify threads
    assert len(threads) == 2
    assert threads[0]["thread_id"] == str(thread1.id)
    assert threads[0]["reply_count"] == 5


@pytest.mark.asyncio
async def test_list_threads_popular(
    mock_db,
    sample_conversation_id,
    sample_user_id,
    sample_participant,
):
    """Test listing threads sorted by popularity."""
    # Create thread roots
    hot_thread = Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="Hot thread",
        message_type="text",
        parent_id=None,
        thread_id=None,
        reply_count=50,
        created_at=datetime.utcnow(),
    )

    cold_thread = Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="Cold thread",
        message_type="text",
        parent_id=None,
        thread_id=None,
        reply_count=2,
        created_at=datetime.utcnow(),
    )

    # Setup mocks
    mock_db.execute.side_effect = [
        # Participant lookup
        AsyncMock(scalar_one_or_none=lambda: sample_participant),
        # Thread roots (sorted by reply_count DESC)
        AsyncMock(scalars=lambda: AsyncMock(all=lambda: [hot_thread, cold_thread])),
        # Latest replies
        AsyncMock(scalar_one_or_none=lambda: None),
        AsyncMock(scalar_one_or_none=lambda: None),
    ]

    service = ThreadingService()

    # List threads
    threads = await service.list_threads(
        db=mock_db,
        conversation_id=sample_conversation_id,
        user_id=sample_user_id,
        sort_by="popular",
    )

    # Verify sorting
    assert len(threads) == 2
    assert threads[0]["thread_id"] == str(hot_thread.id)
    assert threads[0]["reply_count"] == 50


@pytest.mark.asyncio
async def test_delete_thread(
    mock_db,
    sample_conversation_id,
    sample_user_id,
    sample_parent_message,
):
    """Test deleting an entire thread."""
    # Create replies
    reply1 = Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="Reply 1",
        message_type="text",
        parent_id=sample_parent_message.id,
        thread_id=sample_parent_message.id,
        deleted_at=None,
    )

    reply2 = Message(
        id=uuid4(),
        conversation_id=sample_conversation_id,
        sender_id=sample_user_id,
        content="Reply 2",
        message_type="text",
        parent_id=sample_parent_message.id,
        thread_id=sample_parent_message.id,
        deleted_at=None,
    )

    sample_parent_message.deleted_at = None

    # Setup mocks
    mock_db.execute.side_effect = [
        # Root message lookup
        AsyncMock(scalar_one_or_none=lambda: sample_parent_message),
        # All messages in thread
        AsyncMock(
            scalars=lambda: AsyncMock(
                all=lambda: [sample_parent_message, reply1, reply2]
            )
        ),
    ]

    service = ThreadingService()

    # Delete thread
    deleted_count = await service.delete_thread(
        db=mock_db,
        thread_root_id=sample_parent_message.id,
        user_id=sample_user_id,
    )

    # Verify deletion
    assert deleted_count == 3
    assert sample_parent_message.deleted_at is not None
    assert reply1.deleted_at is not None
    assert reply2.deleted_at is not None


@pytest.mark.asyncio
async def test_delete_thread_permission_denied(
    mock_db,
    sample_conversation_id,
    sample_parent_message,
):
    """Test deleting thread without permission."""
    # Setup mock
    sample_parent_message.sender_id = 999  # Different user
    mock_db.execute.return_value = AsyncMock(
        scalar_one_or_none=lambda: sample_parent_message
    )

    service = ThreadingService()

    # Attempt to delete
    with pytest.raises(ValueError, match="Permission denied"):
        await service.delete_thread(
            db=mock_db,
            thread_root_id=sample_parent_message.id,
            user_id=1,  # Different from sender
            is_admin=False,
        )


@pytest.mark.asyncio
async def test_delete_thread_admin(
    mock_db,
    sample_conversation_id,
    sample_parent_message,
):
    """Test admin can delete any thread."""
    # Setup mocks
    sample_parent_message.sender_id = 999  # Different user
    sample_parent_message.deleted_at = None

    mock_db.execute.side_effect = [
        # Root message lookup
        AsyncMock(scalar_one_or_none=lambda: sample_parent_message),
        # All messages in thread
        AsyncMock(scalars=lambda: AsyncMock(all=lambda: [sample_parent_message])),
    ]

    service = ThreadingService()

    # Admin delete
    deleted_count = await service.delete_thread(
        db=mock_db,
        thread_root_id=sample_parent_message.id,
        user_id=1,  # Different from sender
        is_admin=True,
    )

    # Verify deletion
    assert deleted_count == 1
    assert sample_parent_message.deleted_at is not None


@pytest.mark.asyncio
async def test_get_thread_participants(
    mock_db,
    sample_conversation_id,
    sample_user_id,
    sample_parent_message,
    sample_participant,
):
    """Test getting thread participants."""
    # Setup mocks
    mock_db.execute.side_effect = [
        # Root message lookup
        AsyncMock(scalar_one_or_none=lambda: sample_parent_message),
        # Participant lookup
        AsyncMock(scalar_one_or_none=lambda: sample_participant),
        # Unique sender IDs
        AsyncMock(fetchall=lambda: [(1,), (5,), (12,)]),
    ]

    service = ThreadingService()

    # Get participants
    participants = await service.get_thread_participants(
        db=mock_db,
        thread_root_id=sample_parent_message.id,
        user_id=sample_user_id,
    )

    # Verify participants
    assert len(participants) == 3
    assert 1 in participants
    assert 5 in participants
    assert 12 in participants


@pytest.mark.asyncio
async def test_singleton():
    """Test ThreadingService singleton pattern."""
    service1 = get_threading_service()
    service2 = get_threading_service()

    assert service1 is service2


# ============================================================================
# Integration Tests (with real DB) - Skipped by default
# ============================================================================


@pytest.mark.skip(reason="Requires real database connection")
@pytest.mark.asyncio
async def test_threading_integration():
    """
    Integration test with real database.

    To run:
    1. Ensure PostgreSQL is running
    2. Run: pytest test_messenger_threading.py::test_threading_integration -v
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Create conversation
        conversation = Conversation(
            type="group",
            title="Test Thread Conversation",
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        # Create participant
        participant = ConversationParticipant(
            conversation_id=conversation.id,
            user_id=1,
            role="member",
        )
        db.add(participant)
        await db.commit()

        # Create root message
        root_message = Message(
            conversation_id=conversation.id,
            sender_id=1,
            content="Root message for thread test",
            message_type="text",
        )
        db.add(root_message)
        await db.commit()
        await db.refresh(root_message)

        # Create replies using service
        service = get_threading_service()

        await service.create_reply(
            db=db,
            conversation_id=conversation.id,
            parent_message_id=root_message.id,
            sender_id=1,
            content="First reply",
        )

        await service.create_reply(
            db=db,
            conversation_id=conversation.id,
            parent_message_id=root_message.id,
            sender_id=1,
            content="Second reply",
        )

        # Verify thread
        thread = await service.get_thread(
            db=db,
            thread_root_id=root_message.id,
            user_id=1,
        )

        assert thread["reply_count"] == 2
        assert len(thread["replies"]) == 2

        # Cleanup
        await service.delete_thread(
            db=db,
            thread_root_id=root_message.id,
            user_id=1,
        )

        await db.delete(participant)
        await db.delete(conversation)
        await db.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
