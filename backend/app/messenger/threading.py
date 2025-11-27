"""
Message Threading Service

This module handles message threading and reply management for the messenger system.
Supports nested replies, thread summaries, and efficient thread queries.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_models import (
    ConversationParticipant,
    Message,
)

logger = logging.getLogger(__name__)


class ThreadingService:
    """
    Service for managing message threads and replies.

    Features:
    - Create replies to messages
    - Get thread with all replies
    - Get thread summary (metadata only)
    - List all threads in a conversation
    - Update thread statistics (reply counts)
    - Thread notifications
    """

    @staticmethod
    async def create_reply(
        db: AsyncSession,
        conversation_id: UUID,
        parent_message_id: UUID,
        sender_id: int,
        content: Optional[str] = None,
        message_type: str = "text",
        file_url: Optional[str] = None,
        file_size: Optional[int] = None,
        file_name: Optional[str] = None,
    ) -> Message:
        """
        Create a reply to an existing message.

        Args:
            db: Database session
            conversation_id: ID of the conversation
            parent_message_id: ID of the message being replied to
            sender_id: ID of the user sending the reply
            content: Text content of the reply
            message_type: Type of message (text, image, file, system)
            file_url: URL of attached file (optional)
            file_size: Size of attached file (optional)
            file_name: Name of attached file (optional)

        Returns:
            The created reply message

        Raises:
            ValueError: If parent message doesn't exist or user not in conversation
        """
        # Verify parent message exists
        parent_result = await db.execute(
            select(Message).where(Message.id == parent_message_id)
        )
        parent_message = parent_result.scalar_one_or_none()

        if not parent_message:
            raise ValueError(f"Parent message {parent_message_id} not found")

        if parent_message.conversation_id != conversation_id:
            raise ValueError("Parent message not in specified conversation")

        # Verify user is participant
        participant_result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == sender_id,
                )
            )
        )
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise ValueError("User is not a participant in this conversation")

        # Determine thread_id (root message of the thread)
        # If parent has thread_id, use it; otherwise parent IS the root
        thread_id = parent_message.thread_id or parent_message.id

        # Create the reply
        reply = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            file_url=file_url,
            file_size=file_size,
            file_name=file_name,
            parent_id=parent_message_id,
            thread_id=thread_id,
        )

        db.add(reply)

        # Update parent message reply count
        parent_message.reply_count += 1
        parent_message.last_reply_at = datetime.utcnow()

        # If parent is not the root, also update the root
        if parent_message.thread_id:
            root_result = await db.execute(
                select(Message).where(Message.id == parent_message.thread_id)
            )
            root_message = root_result.scalar_one_or_none()
            if root_message:
                root_message.reply_count += 1
                root_message.last_reply_at = datetime.utcnow()

        await db.commit()
        await db.refresh(reply)

        logger.info(
            f"Created reply {reply.id} to message {parent_message_id} "
            f"in thread {thread_id}"
        )

        return reply

    @staticmethod
    async def get_thread(
        db: AsyncSession,
        thread_root_id: UUID,
        user_id: int,
        include_deleted: bool = False,
    ) -> Dict:
        """
        Get a thread with all its replies.

        Args:
            db: Database session
            thread_root_id: ID of the root message
            user_id: ID of the user requesting (for permission check)
            include_deleted: Whether to include soft-deleted messages

        Returns:
            Dictionary with root message and nested replies

        Raises:
            ValueError: If thread not found or user lacks permission
        """
        # Get root message
        root_result = await db.execute(
            select(Message).where(Message.id == thread_root_id)
        )
        root_message = root_result.scalar_one_or_none()

        if not root_message:
            raise ValueError(f"Thread root {thread_root_id} not found")

        # Verify user is participant
        participant_result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id
                    == root_message.conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
        )
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise ValueError("User is not a participant in this conversation")

        # Get all replies in the thread
        query = select(Message).where(
            or_(
                Message.id == thread_root_id,
                Message.thread_id == thread_root_id,
            )
        )

        if not include_deleted:
            query = query.where(Message.deleted_at.is_(None))

        query = query.order_by(Message.created_at)

        result = await db.execute(query)
        messages = result.scalars().all()

        # Build nested structure
        messages_dict = {msg.id: msg for msg in messages}

        def build_reply_tree(message_id: UUID) -> Dict:
            """Recursively build reply tree."""
            message = messages_dict[message_id]

            # Find direct replies
            direct_replies = [msg for msg in messages if msg.parent_id == message_id]

            return {
                "id": str(message.id),
                "conversation_id": str(message.conversation_id),
                "sender_id": message.sender_id,
                "content": message.content,
                "message_type": message.message_type,
                "file_url": message.file_url,
                "file_size": message.file_size,
                "file_name": message.file_name,
                "created_at": message.created_at.isoformat(),
                "edited_at": (
                    message.edited_at.isoformat() if message.edited_at else None
                ),
                "deleted_at": (
                    message.deleted_at.isoformat() if message.deleted_at else None
                ),
                "reply_count": message.reply_count,
                "last_reply_at": (
                    message.last_reply_at.isoformat() if message.last_reply_at else None
                ),
                "replies": [build_reply_tree(reply.id) for reply in direct_replies],
            }

        thread_tree = build_reply_tree(thread_root_id)

        return thread_tree

    @staticmethod
    async def get_thread_summary(
        db: AsyncSession,
        thread_root_id: UUID,
        user_id: int,
    ) -> Dict:
        """
        Get thread summary (metadata without full reply tree).

        Args:
            db: Database session
            thread_root_id: ID of the root message
            user_id: ID of the user requesting

        Returns:
            Dictionary with thread metadata
        """
        # Get root message
        root_result = await db.execute(
            select(Message).where(Message.id == thread_root_id)
        )
        root_message = root_result.scalar_one_or_none()

        if not root_message:
            raise ValueError(f"Thread root {thread_root_id} not found")

        # Verify participant
        participant_result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id
                    == root_message.conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
        )
        if not participant_result.scalar_one_or_none():
            raise ValueError("User is not a participant")

        # Count unique participants in thread
        participants_result = await db.execute(
            select(func.count(func.distinct(Message.sender_id))).where(
                or_(
                    Message.id == thread_root_id,
                    Message.thread_id == thread_root_id,
                )
            )
        )
        unique_participants = participants_result.scalar() or 0

        # Get latest reply
        latest_reply_result = await db.execute(
            select(Message)
            .where(Message.thread_id == thread_root_id)
            .where(Message.deleted_at.is_(None))
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        latest_reply = latest_reply_result.scalar_one_or_none()

        return {
            "thread_id": str(root_message.id),
            "conversation_id": str(root_message.conversation_id),
            "sender_id": root_message.sender_id,
            "content": root_message.content,
            "message_type": root_message.message_type,
            "created_at": root_message.created_at.isoformat(),
            "reply_count": root_message.reply_count,
            "last_reply_at": (
                root_message.last_reply_at.isoformat()
                if root_message.last_reply_at
                else None
            ),
            "unique_participants": unique_participants,
            "latest_reply": (
                {
                    "id": str(latest_reply.id),
                    "sender_id": latest_reply.sender_id,
                    "content": latest_reply.content,
                    "created_at": latest_reply.created_at.isoformat(),
                }
                if latest_reply
                else None
            ),
        }

    @staticmethod
    async def list_threads(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "recent",  # 'recent', 'popular', 'oldest'
    ) -> List[Dict]:
        """
        List all threads in a conversation.

        Args:
            db: Database session
            conversation_id: ID of the conversation
            user_id: ID of the user requesting
            limit: Maximum number of threads to return
            offset: Offset for pagination
            sort_by: Sorting method - 'recent', 'popular', or 'oldest'

        Returns:
            List of thread summaries
        """
        # Verify participant
        participant_result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
        )
        if not participant_result.scalar_one_or_none():
            raise ValueError("User is not a participant")

        # Get root messages (messages with no parent)
        query = select(Message).where(
            and_(
                Message.conversation_id == conversation_id,
                Message.parent_id.is_(None),
                Message.deleted_at.is_(None),
            )
        )

        # Apply sorting
        if sort_by == "recent":
            query = query.order_by(
                desc(Message.last_reply_at), desc(Message.created_at)
            )
        elif sort_by == "popular":
            query = query.order_by(desc(Message.reply_count), desc(Message.created_at))
        elif sort_by == "oldest":
            query = query.order_by(Message.created_at)

        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        root_messages = result.scalars().all()

        # Build summaries
        threads = []
        for root in root_messages:
            # Get latest reply
            latest_reply_result = await db.execute(
                select(Message)
                .where(Message.thread_id == root.id)
                .where(Message.deleted_at.is_(None))
                .order_by(desc(Message.created_at))
                .limit(1)
            )
            latest_reply = latest_reply_result.scalar_one_or_none()

            threads.append(
                {
                    "thread_id": str(root.id),
                    "conversation_id": str(root.conversation_id),
                    "sender_id": root.sender_id,
                    "content": root.content,
                    "message_type": root.message_type,
                    "created_at": root.created_at.isoformat(),
                    "reply_count": root.reply_count,
                    "last_reply_at": (
                        root.last_reply_at.isoformat() if root.last_reply_at else None
                    ),
                    "latest_reply": (
                        {
                            "id": str(latest_reply.id),
                            "sender_id": latest_reply.sender_id,
                            "content": (
                                (latest_reply.content or "")[:100] + "..."
                                if len(latest_reply.content or "") > 100
                                else latest_reply.content
                            ),
                            "created_at": latest_reply.created_at.isoformat(),
                        }
                        if latest_reply
                        else None
                    ),
                }
            )

        return threads

    @staticmethod
    async def delete_thread(
        db: AsyncSession,
        thread_root_id: UUID,
        user_id: int,
        is_admin: bool = False,
    ) -> int:
        """
        Soft delete an entire thread (root + all replies).

        Args:
            db: Database session
            thread_root_id: ID of the root message
            user_id: ID of the user deleting
            is_admin: Whether the user is an admin

        Returns:
            Number of messages deleted

        Raises:
            ValueError: If thread not found or permission denied
        """
        # Get root message
        root_result = await db.execute(
            select(Message).where(Message.id == thread_root_id)
        )
        root_message = root_result.scalar_one_or_none()

        if not root_message:
            raise ValueError(f"Thread root {thread_root_id} not found")

        # Check permission (must be sender or admin)
        if root_message.sender_id != user_id and not is_admin:
            raise ValueError(
                "Permission denied: only sender or admin can delete thread"
            )

        # Get all messages in thread
        messages_result = await db.execute(
            select(Message).where(
                or_(
                    Message.id == thread_root_id,
                    Message.thread_id == thread_root_id,
                )
            )
        )
        messages = messages_result.scalars().all()

        # Soft delete all
        deleted_count = 0
        now = datetime.utcnow()

        for message in messages:
            if not message.deleted_at:
                message.deleted_at = now
                deleted_count += 1

        await db.commit()

        logger.info(f"Soft deleted thread {thread_root_id} ({deleted_count} messages)")

        return deleted_count

    @staticmethod
    async def get_thread_participants(
        db: AsyncSession,
        thread_root_id: UUID,
        user_id: int,
    ) -> List[int]:
        """
        Get list of unique user IDs who have replied in a thread.

        Args:
            db: Database session
            thread_root_id: ID of the root message
            user_id: ID of the user requesting

        Returns:
            List of user IDs
        """
        # Verify thread exists and user is participant
        root_result = await db.execute(
            select(Message).where(Message.id == thread_root_id)
        )
        root_message = root_result.scalar_one_or_none()

        if not root_message:
            raise ValueError(f"Thread root {thread_root_id} not found")

        participant_result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id
                    == root_message.conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
        )
        if not participant_result.scalar_one_or_none():
            raise ValueError("User is not a participant")

        # Get unique sender IDs
        result = await db.execute(
            select(func.distinct(Message.sender_id)).where(
                or_(
                    Message.id == thread_root_id,
                    Message.thread_id == thread_root_id,
                )
            )
        )

        participant_ids = [row[0] for row in result.fetchall() if row[0]]

        return participant_ids


# Singleton instance
_threading_service: Optional[ThreadingService] = None


def get_threading_service() -> ThreadingService:
    """Get singleton instance of ThreadingService."""
    global _threading_service
    if _threading_service is None:
        _threading_service = ThreadingService()
    return _threading_service
