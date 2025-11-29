"""
Analytics Service for Messenger

Tracks and aggregates:
- Message statistics (count, types, activity over time)
- User activity (active users, engagement metrics)
- Conversation metrics (size, activity, participant engagement)
- Real-time analytics events
- Historical trends and insights

Features:
- Redis caching for fast retrieval
- Time-based aggregations (hourly, daily, weekly, monthly)
- Per-user, per-conversation, and global analytics
- Event-driven tracking
- Background aggregation workers
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AnalyticsEventType(str, Enum):
    """Analytics event types"""

    MESSAGE_SENT = "message.sent"
    MESSAGE_EDITED = "message.edited"
    MESSAGE_DELETED = "message.deleted"
    MESSAGE_READ = "message.read"
    USER_ONLINE = "user.online"
    USER_OFFLINE = "user.offline"
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_JOINED = "conversation.joined"
    CONVERSATION_LEFT = "conversation.left"
    FILE_UPLOADED = "file.uploaded"


class TimeInterval(str, Enum):
    """Time interval for analytics aggregation"""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AnalyticsService:
    """
    Analytics service for tracking and aggregating messenger metrics.

    Provides:
    - Message statistics
    - User activity tracking
    - Conversation metrics
    - Real-time event tracking
    - Historical trends
    """

    def __init__(self, redis_client=None):
        """
        Initialize analytics service.

        Args:
            redis_client: Optional Redis client for caching
        """
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes default cache TTL

    # ========================================================================
    # Message Statistics
    # ========================================================================

    async def get_message_stats(
        self,
        db: AsyncSession,
        conversation_id: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get message statistics.

        Args:
            db: Database session
            conversation_id: Optional conversation filter
            user_id: Optional user filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            dict with message statistics
        """
        from app.models.messenger_models import Message
        import uuid

        # Build query
        query = select(
            func.count(Message.id).label("total_messages"),
            func.count(
                func.distinct(
                    func.case((Message.message_type == "text", Message.id), else_=None)
                )
            ).label("text_messages"),
            func.count(
                func.distinct(
                    func.case((Message.message_type == "image", Message.id), else_=None)
                )
            ).label("image_messages"),
            func.count(
                func.distinct(
                    func.case((Message.message_type == "file", Message.id), else_=None)
                )
            ).label("file_messages"),
            func.count(
                func.distinct(
                    func.case(
                        (Message.message_type == "system", Message.id), else_=None
                    )
                )
            ).label("system_messages"),
            func.count(func.distinct(Message.sender_id)).label("unique_senders"),
            func.avg(func.length(Message.content)).label("avg_message_length"),
        ).where(Message.deleted_at.is_(None))

        # Apply filters
        if conversation_id:
            query = query.where(Message.conversation_id == uuid.UUID(conversation_id))

        if user_id:
            query = query.where(Message.sender_id == user_id)

        if start_date:
            query = query.where(Message.created_at >= start_date)

        if end_date:
            query = query.where(Message.created_at <= end_date)

        result = await db.execute(query)
        row = result.first()

        if not row:
            return {
                "total_messages": 0,
                "text_messages": 0,
                "image_messages": 0,
                "file_messages": 0,
                "system_messages": 0,
                "unique_senders": 0,
                "avg_message_length": 0.0,
            }

        stats = {
            "total_messages": row.total_messages or 0,
            "text_messages": row.text_messages or 0,
            "image_messages": row.image_messages or 0,
            "file_messages": row.file_messages or 0,
            "system_messages": row.system_messages or 0,
            "unique_senders": row.unique_senders or 0,
            "avg_message_length": float(row.avg_message_length or 0),
        }

        # Calculate message type distribution
        if stats["total_messages"] > 0:
            stats["message_type_distribution"] = {
                "text": round(
                    stats["text_messages"] / stats["total_messages"] * 100, 2
                ),
                "image": round(
                    stats["image_messages"] / stats["total_messages"] * 100, 2
                ),
                "file": round(
                    stats["file_messages"] / stats["total_messages"] * 100, 2
                ),
                "system": round(
                    stats["system_messages"] / stats["total_messages"] * 100, 2
                ),
            }

        return stats

    async def get_message_timeline(
        self,
        db: AsyncSession,
        interval: TimeInterval = TimeInterval.DAILY,
        conversation_id: Optional[str] = None,
        user_id: Optional[int] = None,
        days: int = 30,
    ) -> list[dict]:
        """
        Get message count timeline by interval.

        Args:
            db: Database session
            interval: Time interval (hourly, daily, weekly, monthly)
            conversation_id: Optional conversation filter
            user_id: Optional user filter
            days: Number of days to look back

        Returns:
            List of {timestamp, count} dicts
        """
        from app.models.messenger_models import Message
        import uuid

        # Calculate start date
        start_date = datetime.utcnow() - timedelta(days=days)

        # Determine date truncation based on interval
        if interval == TimeInterval.HOURLY:
            date_trunc = func.date_trunc("hour", Message.created_at)
        elif interval == TimeInterval.DAILY:
            date_trunc = func.date_trunc("day", Message.created_at)
        elif interval == TimeInterval.WEEKLY:
            date_trunc = func.date_trunc("week", Message.created_at)
        else:  # MONTHLY
            date_trunc = func.date_trunc("month", Message.created_at)

        # Build query
        query = (
            select(date_trunc.label("timestamp"), func.count(Message.id).label("count"))
            .where(and_(Message.created_at >= start_date, Message.deleted_at.is_(None)))
            .group_by("timestamp")
            .order_by("timestamp")
        )

        # Apply filters
        if conversation_id:
            query = query.where(Message.conversation_id == uuid.UUID(conversation_id))

        if user_id:
            query = query.where(Message.sender_id == user_id)

        result = await db.execute(query)
        rows = result.all()

        return [
            {"timestamp": row.timestamp.isoformat(), "count": row.count} for row in rows
        ]

    async def get_top_senders(
        self,
        db: AsyncSession,
        conversation_id: Optional[str] = None,
        limit: int = 10,
        days: int = 30,
    ) -> list[dict]:
        """
        Get top message senders.

        Args:
            db: Database session
            conversation_id: Optional conversation filter
            limit: Number of top senders to return
            days: Number of days to look back

        Returns:
            List of {user_id, username, message_count} dicts
        """
        from app.models.messenger_models import Message
        from app.models.user import User
        import uuid

        start_date = datetime.utcnow() - timedelta(days=days)

        # Build query
        query = (
            select(
                Message.sender_id,
                User.username,
                func.count(Message.id).label("message_count"),
            )
            .join(User, Message.sender_id == User.id)
            .where(
                and_(
                    Message.created_at >= start_date,
                    Message.deleted_at.is_(None),
                    Message.sender_id.isnot(None),
                )
            )
            .group_by(Message.sender_id, User.username)
            .order_by(func.count(Message.id).desc())
            .limit(limit)
        )

        # Apply conversation filter
        if conversation_id:
            query = query.where(Message.conversation_id == uuid.UUID(conversation_id))

        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "user_id": row.sender_id,
                "username": row.username,
                "message_count": row.message_count,
            }
            for row in rows
        ]

    # ========================================================================
    # User Activity Tracking
    # ========================================================================

    async def get_user_activity_stats(
        self,
        db: AsyncSession,
        user_id: int,
        days: int = 30,
    ) -> dict:
        """
        Get activity statistics for a specific user.

        Args:
            db: Database session
            user_id: User ID
            days: Number of days to look back

        Returns:
            dict with user activity stats
        """
        from app.models.messenger_models import (
            ConversationParticipant,
            Message,
            ReadReceipt,
        )

        start_date = datetime.utcnow() - timedelta(days=days)

        # Messages sent
        messages_query = select(func.count(Message.id)).where(
            and_(
                Message.sender_id == user_id,
                Message.created_at >= start_date,
                Message.deleted_at.is_(None),
            )
        )
        messages_result = await db.execute(messages_query)
        messages_sent = messages_result.scalar() or 0

        # Messages read (read receipts)
        reads_query = select(func.count(ReadReceipt.id)).where(
            and_(ReadReceipt.user_id == user_id, ReadReceipt.read_at >= start_date)
        )
        reads_result = await db.execute(reads_query)
        messages_read = reads_result.scalar() or 0

        # Active conversations
        active_convs_query = select(
            func.count(func.distinct(ConversationParticipant.conversation_id))
        ).where(ConversationParticipant.user_id == user_id)
        active_convs_result = await db.execute(active_convs_query)
        active_conversations = active_convs_result.scalar() or 0

        # First message date
        first_message_query = select(func.min(Message.created_at)).where(
            Message.sender_id == user_id
        )
        first_message_result = await db.execute(first_message_query)
        first_message_date = first_message_result.scalar()

        # Last activity date
        last_activity_query = select(func.max(Message.created_at)).where(
            Message.sender_id == user_id
        )
        last_activity_result = await db.execute(last_activity_query)
        last_activity_date = last_activity_result.scalar()

        return {
            "user_id": user_id,
            "period_days": days,
            "messages_sent": messages_sent,
            "messages_read": messages_read,
            "active_conversations": active_conversations,
            "avg_messages_per_day": round(messages_sent / days, 2) if days > 0 else 0,
            "first_message_date": (
                first_message_date.isoformat() if first_message_date else None
            ),
            "last_activity_date": (
                last_activity_date.isoformat() if last_activity_date else None
            ),
        }

    async def get_active_users_count(
        self,
        db: AsyncSession,
        hours: int = 24,
    ) -> dict:
        """
        Get count of active users in the last N hours.

        Args:
            db: Database session
            hours: Number of hours to look back

        Returns:
            dict with active user counts
        """
        from app.models.messenger_models import Message

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Users who sent messages
        query = select(func.count(func.distinct(Message.sender_id))).where(
            and_(
                Message.created_at >= cutoff_time,
                Message.sender_id.isnot(None),
                Message.deleted_at.is_(None),
            )
        )
        result = await db.execute(query)
        active_users = result.scalar() or 0

        return {
            "period_hours": hours,
            "active_users": active_users,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_user_engagement_metrics(
        self,
        db: AsyncSession,
        days: int = 7,
    ) -> dict:
        """
        Get user engagement metrics.

        Args:
            db: Database session
            days: Number of days to look back

        Returns:
            dict with engagement metrics
        """
        from app.models.messenger_models import Message
        from app.models.user import User

        start_date = datetime.utcnow() - timedelta(days=days)

        # Total registered users
        total_users_query = select(func.count(User.id))
        total_users_result = await db.execute(total_users_query)
        total_users = total_users_result.scalar() or 0

        # Active users (sent at least 1 message)
        active_users_query = select(func.count(func.distinct(Message.sender_id))).where(
            and_(
                Message.created_at >= start_date,
                Message.sender_id.isnot(None),
                Message.deleted_at.is_(None),
            )
        )
        active_users_result = await db.execute(active_users_query)
        active_users = active_users_result.scalar() or 0

        # Engaged users (sent 5+ messages)
        engaged_users_query = (
            select(Message.sender_id)
            .where(
                and_(
                    Message.created_at >= start_date,
                    Message.sender_id.isnot(None),
                    Message.deleted_at.is_(None),
                )
            )
            .group_by(Message.sender_id)
            .having(func.count(Message.id) >= 5)
        )
        engaged_users_result = await db.execute(engaged_users_query)
        engaged_users = len(engaged_users_result.all())

        # Calculate engagement rates
        engagement_rate = (
            round(active_users / total_users * 100, 2) if total_users > 0 else 0
        )
        deep_engagement_rate = (
            round(engaged_users / total_users * 100, 2) if total_users > 0 else 0
        )

        return {
            "period_days": days,
            "total_users": total_users,
            "active_users": active_users,
            "engaged_users": engaged_users,
            "engagement_rate": engagement_rate,
            "deep_engagement_rate": deep_engagement_rate,
        }

    # ========================================================================
    # Conversation Metrics
    # ========================================================================

    async def get_conversation_stats(
        self,
        db: AsyncSession,
        conversation_id: str,
    ) -> dict:
        """
        Get statistics for a specific conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID

        Returns:
            dict with conversation statistics
        """
        from app.models.messenger_models import (
            Conversation,
            ConversationParticipant,
            Message,
        )
        import uuid

        conv_uuid = uuid.UUID(conversation_id)

        # Get conversation details
        conv_query = select(Conversation).where(Conversation.id == conv_uuid)
        conv_result = await db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            return {"error": "Conversation not found"}

        # Participant count
        participants_query = select(func.count(ConversationParticipant.id)).where(
            ConversationParticipant.conversation_id == conv_uuid
        )
        participants_result = await db.execute(participants_query)
        participant_count = participants_result.scalar() or 0

        # Message count
        messages_query = select(func.count(Message.id)).where(
            and_(
                Message.conversation_id == conv_uuid,
                Message.deleted_at.is_(None),
            )
        )
        messages_result = await db.execute(messages_query)
        message_count = messages_result.scalar() or 0

        # First and last message dates
        first_msg_query = select(func.min(Message.created_at)).where(
            Message.conversation_id == conv_uuid
        )
        first_msg_result = await db.execute(first_msg_query)
        first_message_date = first_msg_result.scalar()

        last_msg_query = select(func.max(Message.created_at)).where(
            Message.conversation_id == conv_uuid
        )
        last_msg_result = await db.execute(last_msg_query)
        last_message_date = last_msg_result.scalar()

        # Active participants (sent at least 1 message)
        active_participants_query = select(
            func.count(func.distinct(Message.sender_id))
        ).where(
            and_(
                Message.conversation_id == conv_uuid,
                Message.sender_id.isnot(None),
                Message.deleted_at.is_(None),
            )
        )
        active_participants_result = await db.execute(active_participants_query)
        active_participants = active_participants_result.scalar() or 0

        # Calculate activity metrics
        if first_message_date and last_message_date:
            conversation_age_days = (datetime.utcnow() - conversation.created_at).days
            messages_per_day = (
                round(message_count / conversation_age_days, 2)
                if conversation_age_days > 0
                else 0
            )
        else:
            conversation_age_days = 0
            messages_per_day = 0

        return {
            "conversation_id": conversation_id,
            "type": conversation.type,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "participant_count": participant_count,
            "active_participants": active_participants,
            "message_count": message_count,
            "messages_per_day": messages_per_day,
            "conversation_age_days": conversation_age_days,
            "first_message_date": (
                first_message_date.isoformat() if first_message_date else None
            ),
            "last_message_date": (
                last_message_date.isoformat() if last_message_date else None
            ),
        }

    async def get_top_conversations(
        self,
        db: AsyncSession,
        limit: int = 10,
        days: int = 30,
        sort_by: str = "messages",
    ) -> list[dict]:
        """
        Get top conversations by activity.

        Args:
            db: Database session
            limit: Number of top conversations to return
            days: Number of days to look back
            sort_by: Sort criteria ('messages', 'participants', 'activity')

        Returns:
            List of conversation stats dicts
        """
        from app.models.messenger_models import Message

        start_date = datetime.utcnow() - timedelta(days=days)

        # Build query based on sort criteria
        if sort_by == "messages":
            query = (
                select(
                    Message.conversation_id,
                    func.count(Message.id).label("message_count"),
                )
                .where(
                    and_(
                        Message.created_at >= start_date,
                        Message.deleted_at.is_(None),
                    )
                )
                .group_by(Message.conversation_id)
                .order_by(func.count(Message.id).desc())
                .limit(limit)
            )
        else:
            # Default to message count
            query = (
                select(
                    Message.conversation_id,
                    func.count(Message.id).label("message_count"),
                )
                .where(
                    and_(
                        Message.created_at >= start_date,
                        Message.deleted_at.is_(None),
                    )
                )
                .group_by(Message.conversation_id)
                .order_by(func.count(Message.id).desc())
                .limit(limit)
            )

        result = await db.execute(query)
        rows = result.all()

        # Get details for each conversation
        top_conversations = []
        for row in rows:
            conv_stats = await self.get_conversation_stats(db, str(row.conversation_id))
            top_conversations.append(conv_stats)

        return top_conversations

    # ========================================================================
    # Event Tracking
    # ========================================================================

    async def track_event(
        self,
        event_type: AnalyticsEventType,
        user_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Track an analytics event.

        Args:
            event_type: Type of event
            user_id: Optional user ID
            conversation_id: Optional conversation ID
            metadata: Optional event metadata
        """
        event_data = {
            "event_type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "conversation_id": conversation_id,
            "metadata": metadata or {},
        }

        # Store in Redis for real-time processing
        if self.redis:
            try:
                # Add to events stream
                await self.redis.lpush("analytics:events", json.dumps(event_data))
                # Trim to last 10000 events
                await self.redis.ltrim("analytics:events", 0, 9999)

                logger.debug(f"Tracked event: {event_type.value}")
            except Exception as e:
                logger.error(f"Failed to track event: {e}")

    # ========================================================================
    # Caching
    # ========================================================================

    async def get_cached_stats(self, cache_key: str) -> Optional[dict]:
        """
        Get cached statistics.

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None
        """
        if not self.redis:
            return None

        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache read error: {e}")

        return None

    async def set_cached_stats(
        self, cache_key: str, data: dict, ttl: Optional[int] = None
    ) -> None:
        """
        Cache statistics.

        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (default: self.cache_ttl)
        """
        if not self.redis:
            return

        try:
            ttl = ttl or self.cache_ttl
            await self.redis.setex(cache_key, ttl, json.dumps(data))
        except Exception as e:
            logger.error(f"Cache write error: {e}")

    # ========================================================================
    # Dashboard Summary
    # ========================================================================

    async def get_dashboard_summary(
        self,
        db: AsyncSession,
        days: int = 7,
    ) -> dict:
        """
        Get comprehensive dashboard summary.

        Args:
            db: Database session
            days: Number of days to look back

        Returns:
            dict with dashboard summary
        """
        # Check cache first
        cache_key = f"analytics:dashboard:{days}d"
        cached = await self.get_cached_stats(cache_key)
        if cached:
            return cached

        # Gather all metrics
        message_stats = await self.get_message_stats(
            db, start_date=datetime.utcnow() - timedelta(days=days)
        )

        engagement_metrics = await self.get_user_engagement_metrics(db, days=days)

        active_users_24h = await self.get_active_users_count(db, hours=24)

        top_senders = await self.get_top_senders(db, limit=5, days=days)

        message_timeline = await self.get_message_timeline(
            db, interval=TimeInterval.DAILY, days=days
        )

        summary = {
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "message_stats": message_stats,
            "engagement_metrics": engagement_metrics,
            "active_users_24h": active_users_24h,
            "top_senders": top_senders,
            "message_timeline": message_timeline,
        }

        # Cache for 5 minutes
        await self.set_cached_stats(cache_key, summary, ttl=300)

        return summary


# Singleton instance
_analytics_service_instance: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """
    Get or create singleton AnalyticsService instance.

    Returns:
        AnalyticsService singleton instance
    """
    from app.messenger.pubsub import get_pubsub

    global _analytics_service_instance

    if _analytics_service_instance is None:
        # Get Redis client from pubsub service
        try:
            pubsub = get_pubsub()
            redis_client = pubsub.redis_client if pubsub else None
        except Exception:
            redis_client = None

        _analytics_service_instance = AnalyticsService(redis_client=redis_client)

    return _analytics_service_instance


async def analytics_aggregation_task():
    """
    Background task to aggregate analytics data.

    Runs periodically to update cached statistics.
    """
    from app.core.database import AsyncSessionLocal

    analytics_service = get_analytics_service()

    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes

            async with AsyncSessionLocal() as db:
                # Pre-compute and cache dashboard summaries
                for days in [1, 7, 30]:
                    await analytics_service.get_dashboard_summary(db, days=days)

                logger.info("Analytics aggregation completed")

        except Exception as e:
            logger.error(f"Analytics aggregation task error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error
