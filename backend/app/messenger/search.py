"""
Search Service for Messenger

Provides full-text search and filtering capabilities:
- Message search with content, sender, date filters
- Conversation search and discovery
- User search by username, email
- Advanced filtering (date range, message type, participants)
- Search result ranking and relevance scoring
- PostgreSQL full-text search with tsvector

Features:
- Full-text search with stemming and ranking
- Filter by conversation, user, date range, message type
- Search result pagination
- Highlight search terms in results
- Sort by relevance or date
- Autocomplete suggestions
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SearchType(str, Enum):
    """Search type"""

    MESSAGES = "messages"
    CONVERSATIONS = "conversations"
    USERS = "users"


class SortOrder(str, Enum):
    """Sort order for search results"""

    RELEVANCE = "relevance"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"


class MessageType(str, Enum):
    """Message type filter"""

    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class SearchService:
    """
    Search service for messenger.

    Provides:
    - Full-text message search
    - Conversation search and discovery
    - User search
    - Advanced filtering
    - Search result ranking
    """

    def __init__(self):
        """Initialize search service"""
        pass

    # ========================================================================
    # Message Search
    # ========================================================================

    async def search_messages(
        self,
        db: AsyncSession,
        query: str,
        user_id: int,
        conversation_id: Optional[str] = None,
        sender_id: Optional[int] = None,
        message_type: Optional[MessageType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: SortOrder = SortOrder.RELEVANCE,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """
        Search messages with full-text search and filters.

        Args:
            db: Database session
            query: Search query string
            user_id: User performing search (for permission check)
            conversation_id: Optional conversation filter
            sender_id: Optional sender filter
            message_type: Optional message type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            sort_by: Sort order (relevance, date_desc, date_asc)
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            dict with search results and metadata
        """
        from app.models.messenger_models import (
            Conversation,
            ConversationParticipant,
            Message,
        )
        from app.models.user import User
        import uuid

        # Build base query
        # Use PostgreSQL full-text search with ts_rank for relevance
        search_query = func.to_tsquery(
            "english", func.plainto_tsquery("english", query)
        )
        search_vector = func.to_tsvector("english", Message.content)

        base_query = (
            select(
                Message,
                User.username.label("sender_username"),
                Conversation.title.label("conversation_title"),
                func.ts_rank(search_vector, search_query).label("rank"),
            )
            .join(User, Message.sender_id == User.id, isouter=True)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .join(
                ConversationParticipant,
                and_(
                    ConversationParticipant.conversation_id == Message.conversation_id,
                    ConversationParticipant.user_id == user_id,
                ),
            )
            .where(
                and_(
                    search_vector.op("@@")(search_query),
                    Message.deleted_at.is_(None),
                )
            )
        )

        # Apply filters
        if conversation_id:
            base_query = base_query.where(
                Message.conversation_id == uuid.UUID(conversation_id)
            )

        if sender_id:
            base_query = base_query.where(Message.sender_id == sender_id)

        if message_type:
            base_query = base_query.where(Message.message_type == message_type.value)

        if start_date:
            base_query = base_query.where(Message.created_at >= start_date)

        if end_date:
            base_query = base_query.where(Message.created_at <= end_date)

        # Apply sorting
        if sort_by == SortOrder.RELEVANCE:
            base_query = base_query.order_by(
                func.ts_rank(search_vector, search_query).desc()
            )
        elif sort_by == SortOrder.DATE_DESC:
            base_query = base_query.order_by(Message.created_at.desc())
        else:  # DATE_ASC
            base_query = base_query.order_by(Message.created_at.asc())

        # Get total count (without pagination)
        count_query = select(func.count()).select_from(
            base_query.with_only_columns(Message.id).subquery()
        )
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply pagination
        paginated_query = base_query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(paginated_query)
        rows = result.all()

        # Format results
        messages = []
        for row in rows:
            message = row.Message
            messages.append(
                {
                    "id": str(message.id),
                    "conversation_id": str(message.conversation_id),
                    "conversation_title": row.conversation_title,
                    "sender_id": message.sender_id,
                    "sender_username": row.sender_username,
                    "content": message.content,
                    "message_type": message.message_type,
                    "file_url": message.file_url,
                    "file_name": message.file_name,
                    "created_at": message.created_at.isoformat(),
                    "edited_at": (
                        message.edited_at.isoformat() if message.edited_at else None
                    ),
                    "relevance": (
                        float(row.rank) if sort_by == SortOrder.RELEVANCE else None
                    ),
                    "highlighted_content": self._highlight_terms(
                        message.content, query
                    ),
                }
            )

        return {
            "query": query,
            "total_count": total_count,
            "results": messages,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(messages) < total_count,
        }

    async def search_messages_simple(
        self,
        db: AsyncSession,
        query: str,
        user_id: int,
        conversation_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """
        Simple message search within a conversation (for in-chat search).

        Args:
            db: Database session
            query: Search query string
            user_id: User performing search
            conversation_id: Conversation UUID
            limit: Maximum results

        Returns:
            List of matching messages
        """
        from app.models.messenger_models import ConversationParticipant, Message
        import uuid

        conv_uuid = uuid.UUID(conversation_id)

        # Verify user is participant
        participant_check = select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == conv_uuid,
                ConversationParticipant.user_id == user_id,
            )
        )
        participant_result = await db.execute(participant_check)
        if not participant_result.scalar_one_or_none():
            return []

        # Search messages with ILIKE (case-insensitive pattern match)
        search_pattern = f"%{query}%"
        messages_query = (
            select(Message)
            .where(
                and_(
                    Message.conversation_id == conv_uuid,
                    Message.content.ilike(search_pattern),
                    Message.deleted_at.is_(None),
                )
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(messages_query)
        messages = result.scalars().all()

        return [
            {
                "id": str(msg.id),
                "content": msg.content,
                "sender_id": msg.sender_id,
                "created_at": msg.created_at.isoformat(),
                "highlighted_content": self._highlight_terms(msg.content or "", query),
            }
            for msg in messages
        ]

    # ========================================================================
    # Conversation Search
    # ========================================================================

    async def search_conversations(
        self,
        db: AsyncSession,
        query: str,
        user_id: int,
        conversation_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """
        Search conversations by title or participants.

        Args:
            db: Database session
            query: Search query string
            user_id: User performing search
            conversation_type: Optional type filter (direct, group, announcement)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            dict with search results and metadata
        """
        from app.models.messenger_models import Conversation, ConversationParticipant
        from app.models.user import User

        # Search in conversation titles and participant usernames
        search_pattern = f"%{query}%"

        # Build query
        base_query = (
            select(
                Conversation,
                func.count(ConversationParticipant.id).label("participant_count"),
                func.max(func.coalesce(Conversation.title, User.username)).label(
                    "display_name"
                ),
            )
            .join(
                ConversationParticipant,
                ConversationParticipant.conversation_id == Conversation.id,
            )
            .join(User, User.id == ConversationParticipant.user_id, isouter=True)
            .where(
                and_(
                    # User must be a participant
                    Conversation.id.in_(
                        select(ConversationParticipant.conversation_id).where(
                            ConversationParticipant.user_id == user_id
                        )
                    ),
                    # Search in title or participant username
                    or_(
                        Conversation.title.ilike(search_pattern),
                        User.username.ilike(search_pattern),
                    ),
                )
            )
            .group_by(Conversation.id)
        )

        # Apply type filter
        if conversation_type:
            base_query = base_query.where(Conversation.type == conversation_type)

        # Get total count
        count_query = select(func.count()).select_from(
            base_query.with_only_columns(Conversation.id).subquery()
        )
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply pagination and execute
        paginated_query = (
            base_query.order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(paginated_query)
        rows = result.all()

        # Format results
        conversations = []
        for row in rows:
            conv = row.Conversation
            conversations.append(
                {
                    "id": str(conv.id),
                    "type": conv.type,
                    "title": conv.title,
                    "display_name": row.display_name,
                    "participant_count": row.participant_count,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                }
            )

        return {
            "query": query,
            "total_count": total_count,
            "results": conversations,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(conversations) < total_count,
        }

    async def discover_conversations(
        self,
        db: AsyncSession,
        user_id: int,
        zone_id: Optional[int] = None,
        org_id: Optional[int] = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        Discover public conversations user can join.

        Args:
            db: Database session
            user_id: User performing discovery
            zone_id: Optional zone filter
            org_id: Optional organization filter
            limit: Maximum results

        Returns:
            List of discoverable conversations
        """
        from app.models.messenger_models import (
            Conversation,
            ConversationParticipant,
            Message,
        )

        # Find conversations user is not part of
        query = (
            select(
                Conversation,
                func.count(ConversationParticipant.id).label("participant_count"),
                func.count(Message.id).label("message_count"),
            )
            .join(
                ConversationParticipant,
                ConversationParticipant.conversation_id == Conversation.id,
                isouter=True,
            )
            .join(
                Message,
                Message.conversation_id == Conversation.id,
                isouter=True,
            )
            .where(
                and_(
                    # User is not already a participant
                    Conversation.id.not_in(
                        select(ConversationParticipant.conversation_id).where(
                            ConversationParticipant.user_id == user_id
                        )
                    ),
                    # Only group and announcement types (not direct)
                    Conversation.type.in_(["group", "announcement"]),
                )
            )
            .group_by(Conversation.id)
        )

        # Apply filters
        if zone_id:
            query = query.where(Conversation.zone_id == zone_id)

        if org_id:
            query = query.where(Conversation.org_id == org_id)

        # Order by activity (message count desc)
        query = query.order_by(func.count(Message.id).desc()).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        # Format results
        conversations = []
        for row in rows:
            conv = row.Conversation
            conversations.append(
                {
                    "id": str(conv.id),
                    "type": conv.type,
                    "title": conv.title,
                    "participant_count": row.participant_count,
                    "message_count": row.message_count,
                    "created_at": conv.created_at.isoformat(),
                }
            )

        return conversations

    # ========================================================================
    # User Search
    # ========================================================================

    async def search_users(
        self,
        db: AsyncSession,
        query: str,
        current_user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """
        Search users by username or email.

        Args:
            db: Database session
            query: Search query string
            current_user_id: User performing search
            limit: Maximum results
            offset: Pagination offset

        Returns:
            dict with search results and metadata
        """
        from app.models.user import User

        search_pattern = f"%{query}%"

        # Build query (exclude current user)
        base_query = select(User).where(
            and_(
                User.id != current_user_id,
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                ),
            )
        )

        # Get total count
        count_query = select(func.count()).select_from(
            base_query.with_only_columns(User.id).subquery()
        )
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply pagination
        paginated_query = base_query.order_by(User.username).limit(limit).offset(offset)

        result = await db.execute(paginated_query)
        users = result.scalars().all()

        # Format results
        user_results = []
        for user in users:
            user_results.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    # Add highlighted fields
                    "highlighted_username": self._highlight_terms(user.username, query),
                }
            )

        return {
            "query": query,
            "total_count": total_count,
            "results": user_results,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(user_results) < total_count,
        }

    # ========================================================================
    # Autocomplete
    # ========================================================================

    async def autocomplete_users(
        self,
        db: AsyncSession,
        query: str,
        current_user_id: int,
        conversation_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Autocomplete user suggestions for mentions or direct messages.

        Args:
            db: Database session
            query: Partial username
            current_user_id: User performing search
            conversation_id: Optional conversation (suggest participants first)
            limit: Maximum suggestions

        Returns:
            List of user suggestions
        """
        from app.models.messenger_models import ConversationParticipant
        from app.models.user import User
        import uuid

        search_pattern = f"{query}%"  # Prefix match for autocomplete

        # If conversation provided, prioritize participants
        if conversation_id:
            conv_uuid = uuid.UUID(conversation_id)

            # Get conversation participants first
            participant_query = (
                select(User)
                .join(
                    ConversationParticipant,
                    ConversationParticipant.user_id == User.id,
                )
                .where(
                    and_(
                        ConversationParticipant.conversation_id == conv_uuid,
                        User.id != current_user_id,
                        User.username.ilike(search_pattern),
                    )
                )
                .order_by(User.username)
                .limit(limit)
            )

            result = await db.execute(participant_query)
            users = list(result.scalars().all())

            # If not enough participants, add other users
            if len(users) < limit:
                other_query = (
                    select(User)
                    .where(
                        and_(
                            User.id != current_user_id,
                            User.username.ilike(search_pattern),
                            User.id.not_in([u.id for u in users]),
                        )
                    )
                    .order_by(User.username)
                    .limit(limit - len(users))
                )

                other_result = await db.execute(other_query)
                users.extend(other_result.scalars().all())
        else:
            # No conversation context, search all users
            query_obj = (
                select(User)
                .where(
                    and_(
                        User.id != current_user_id,
                        User.username.ilike(search_pattern),
                    )
                )
                .order_by(User.username)
                .limit(limit)
            )

            result = await db.execute(query_obj)
            users = result.scalars().all()

        # Format results
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
            for user in users
        ]

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _highlight_terms(self, text: str, query: str) -> str:
        """
        Highlight search terms in text.

        Args:
            text: Original text
            query: Search query

        Returns:
            Text with highlighted terms (using <mark> tags)
        """
        if not text or not query:
            return text

        # Simple case-insensitive highlighting
        # Split query into words
        words = query.lower().split()

        highlighted = text
        for word in words:
            if len(word) < 2:  # Skip very short words
                continue

            # Find and replace (case-insensitive)
            import re

            pattern = re.compile(re.escape(word), re.IGNORECASE)
            highlighted = pattern.sub(
                lambda m: f"<mark>{m.group()}</mark>", highlighted
            )

        return highlighted


# Singleton instance
_search_service_instance: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """
    Get or create singleton SearchService instance.

    Returns:
        SearchService singleton instance
    """
    global _search_service_instance

    if _search_service_instance is None:
        _search_service_instance = SearchService()

    return _search_service_instance
