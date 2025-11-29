"""
Enhanced notification system for messenger (Task 4.1).

Provides:
- In-app notifications with read tracking
- Email notifications with templates
- Multi-channel notification delivery
- User notification preferences management
- Notification grouping and batching
- Quiet hours support
- Priority levels
"""

import logging
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    PUSH = "push"
    EMAIL = "email"
    IN_APP = "in_app"


class NotificationType(str, Enum):
    """Notification types."""

    NEW_MESSAGE = "new_message"
    MESSAGE_MENTION = "message_mention"
    MESSAGE_REPLY = "message_reply"
    CONVERSATION_INVITE = "conversation_invite"
    PARTICIPANT_ADDED = "participant_added"
    PARTICIPANT_REMOVED = "participant_removed"
    FILE_UPLOADED = "file_uploaded"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    MODERATION_WARNING = "moderation_warning"
    MODERATION_ACTION = "moderation_action"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EnhancedNotificationService:
    """
    Enhanced notification service supporting multiple channels.

    Features:
    - In-app notifications with read tracking
    - Email notifications with templates
    - Push notifications (existing system)
    - User preferences management
    - Quiet hours support
    - Notification batching
    - Priority handling
    """

    _instance: Optional["EnhancedNotificationService"] = None

    def __init__(self):
        """Initialize enhanced notification service."""
        self.email_enabled = True  # Configure via env var
        self.batch_interval_seconds = 300  # 5 minutes
        self.notification_templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load notification templates."""
        return {
            NotificationType.NEW_MESSAGE.value: {
                "title": "New message from {sender}",
                "message": "{sender}: {preview}",
                "email_subject": "New message from {sender} in {conversation}",
                "email_body": "Hi {recipient},\n\n{sender} sent you a message in {conversation}:\n\n{preview}\n\nView message: {action_url}",
            },
            NotificationType.MESSAGE_MENTION.value: {
                "title": "{sender} mentioned you",
                "message": "{sender} mentioned you: {preview}",
                "email_subject": "You were mentioned by {sender}",
                "email_body": "Hi {recipient},\n\n{sender} mentioned you in {conversation}:\n\n{preview}\n\nView message: {action_url}",
            },
            NotificationType.CONVERSATION_INVITE.value: {
                "title": "Invitation to {conversation}",
                "message": "{sender} invited you to join {conversation}",
                "email_subject": "Invitation to join {conversation}",
                "email_body": "Hi {recipient},\n\n{sender} has invited you to join the conversation '{conversation}'.\n\nJoin now: {action_url}",
            },
            NotificationType.MODERATION_WARNING.value: {
                "title": "Moderation Warning",
                "message": "Your message was flagged: {reason}",
                "email_subject": "Content Moderation Warning",
                "email_body": "Hi {recipient},\n\nYour recent message was flagged for moderation:\n\nReason: {reason}\n\nPlease review our community guidelines.",
            },
        }

    async def send_notification(
        self,
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> Dict[str, bool]:
        """
        Send notification through multiple channels.

        Args:
            db: Database session
            user_id: User to notify
            notification_type: Type of notification
            data: Notification data (sender, preview, etc.)
            priority: Priority level
            channels: Optional list of channels (default: all enabled)

        Returns:
            dict with channel success status
        """
        # Get user preferences
        preferences = await self.get_user_preferences(db, user_id, notification_type)

        # Check if in quiet hours
        if await self._is_quiet_hours(preferences):
            if priority not in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
                logger.info(f"User {user_id} in quiet hours, skipping notification")
                return {"skipped": True}

        # Determine channels to use
        if channels is None:
            channels = [
                NotificationChannel.IN_APP,
                NotificationChannel.PUSH,
                NotificationChannel.EMAIL,
            ]

        # Filter by user preferences
        enabled_channels = [
            ch for ch in channels if preferences.get(ch.value, {}).get("enabled", True)
        ]

        # Send to each channel
        results = {}

        for channel in enabled_channels:
            try:
                if channel == NotificationChannel.IN_APP:
                    success = await self._send_in_app_notification(
                        db, user_id, notification_type, data, priority
                    )
                    results["in_app"] = success

                elif channel == NotificationChannel.PUSH:
                    success = await self._send_push_notification(
                        db, user_id, notification_type, data, priority
                    )
                    results["push"] = success

                elif channel == NotificationChannel.EMAIL:
                    success = await self._send_email_notification(
                        db, user_id, notification_type, data, priority
                    )
                    results["email"] = success

            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {e}")
                results[channel.value] = False

        return results

    async def _send_in_app_notification(
        self,
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        data: Dict[str, Any],
        priority: NotificationPriority,
    ) -> bool:
        """Send in-app notification."""
        template = self.notification_templates.get(notification_type.value, {})

        title = template.get("title", "New notification").format(**data)
        message = template.get("message", "").format(**data)

        # Create notification record
        from sqlalchemy import text

        expires_at = datetime.utcnow() + timedelta(days=30)  # Expire after 30 days

        await db.execute(
            text(
                "INSERT INTO in_app_notifications "
                "(user_id, type, title, message, data, priority, action_url, expires_at) "
                "VALUES (:user_id, :type, :title, :message, :data, :priority, :action_url, :expires_at)"
            ).bindparams(
                user_id=user_id,
                type=notification_type.value,
                title=title,
                message=message,
                data=data,
                priority=priority.value,
                action_url=data.get("action_url"),
                expires_at=expires_at,
            )
        )

        await db.commit()

        # Broadcast to WebSocket if user is online
        await self._broadcast_notification(
            user_id,
            {
                "type": "notification",
                "notification_type": notification_type.value,
                "title": title,
                "message": message,
                "priority": priority.value,
                "data": data,
            },
        )

        return True

    async def _send_push_notification(
        self,
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        data: Dict[str, Any],
        priority: NotificationPriority,
    ) -> bool:
        """Send push notification using existing system."""
        from app.messenger.push_notifications import get_push_service

        template = self.notification_templates.get(notification_type.value, {})

        title = template.get("title", "New notification").format(**data)
        body = template.get("message", "").format(**data)

        push_service = get_push_service()

        # Map priority to push priority
        from app.messenger.push_notifications import (
            NotificationPriority as PushPriority,
        )

        push_priority = (
            PushPriority.HIGH
            if priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]
            else PushPriority.NORMAL
        )

        result = await push_service.send_push_notification(
            db=db,
            user_id=user_id,
            title=title,
            body=body,
            data=data,
            priority=push_priority,
        )

        return result.get("status") != "failed"

    async def _send_email_notification(
        self,
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        data: Dict[str, Any],
        priority: NotificationPriority,
    ) -> bool:
        """Send email notification."""
        if not self.email_enabled:
            return False

        # Get user email
        result = await db.execute(select(User.email).where(User.id == user_id))
        user_email = result.scalar_one_or_none()

        if not user_email:
            return False

        try:
            # Import email service
            from app.messenger.email_service import get_email_service

            # Get email service instance
            email_service = get_email_service()

            # Send notification email using templates
            success = await email_service.send_notification_email(
                user_email=user_email,
                notification_type=notification_type,
                data=data,
            )

            if success:
                logger.info(f"Email notification sent to {user_email}")
            else:
                logger.warning(f"Failed to send email to {user_email}")

            return success

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    async def _broadcast_notification(self, user_id: int, notification: Dict[str, Any]):
        """Broadcast notification to user's WebSocket connections."""
        try:
            from app.messenger.pubsub import get_pubsub

            pubsub = get_pubsub()
            await pubsub.publish_user_notification(
                user_id=user_id,
                notification_data=notification,
            )
        except Exception as e:
            logger.error(f"Failed to broadcast notification: {e}")

    async def get_user_preferences(
        self,
        db: AsyncSession,
        user_id: int,
        notification_type: Optional[NotificationType] = None,
    ) -> Dict[str, Any]:
        """Get user notification preferences."""
        from sqlalchemy import text

        query = text(
            "SELECT channel, notification_type, enabled, quiet_hours_start, quiet_hours_end "
            "FROM notification_preferences "
            "WHERE user_id = :user_id"
        )

        if notification_type:
            query = text(
                "SELECT channel, notification_type, enabled, quiet_hours_start, quiet_hours_end "
                "FROM notification_preferences "
                "WHERE user_id = :user_id AND notification_type = :notif_type"
            ).bindparams(user_id=user_id, notif_type=notification_type.value)
        else:
            query = query.bindparams(user_id=user_id)

        result = await db.execute(query)
        rows = result.fetchall()

        preferences = {}
        for row in rows:
            channel = row[0]
            if channel not in preferences:
                preferences[channel] = {}

            preferences[channel][row[1]] = {
                "enabled": row[2],
                "quiet_hours_start": row[3],
                "quiet_hours_end": row[4],
            }

        return preferences

    async def _is_quiet_hours(self, preferences: Dict[str, Any]) -> bool:
        """Check if current time is in user's quiet hours."""
        # Check any channel's quiet hours
        for channel_prefs in preferences.values():
            for notif_prefs in channel_prefs.values():
                start = notif_prefs.get("quiet_hours_start")
                end = notif_prefs.get("quiet_hours_end")

                if start and end:
                    now = datetime.utcnow().time()

                    if start < end:
                        # Normal range (e.g., 22:00 - 08:00)
                        if start <= now <= end:
                            return True
                    else:
                        # Overnight range (e.g., 22:00 - 08:00 next day)
                        if now >= start or now <= end:
                            return True

        return False

    async def set_user_preference(
        self,
        db: AsyncSession,
        user_id: int,
        channel: NotificationChannel,
        notification_type: NotificationType,
        enabled: bool,
        quiet_hours_start: Optional[time] = None,
        quiet_hours_end: Optional[time] = None,
    ):
        """Set user notification preference."""
        from sqlalchemy import text

        # Upsert preference
        await db.execute(
            text(
                "INSERT INTO notification_preferences "
                "(user_id, channel, notification_type, enabled, quiet_hours_start, quiet_hours_end, updated_at) "
                "VALUES (:user_id, :channel, :type, :enabled, :start, :end, :now) "
                "ON CONFLICT (user_id, channel, notification_type) "
                "DO UPDATE SET enabled = :enabled, quiet_hours_start = :start, "
                "quiet_hours_end = :end, updated_at = :now"
            ).bindparams(
                user_id=user_id,
                channel=channel.value,
                type=notification_type.value,
                enabled=enabled,
                start=quiet_hours_start,
                end=quiet_hours_end,
                now=datetime.utcnow(),
            )
        )

        await db.commit()

    async def get_in_app_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get user's in-app notifications."""
        from sqlalchemy import text

        query = """
            SELECT id, type, title, message, data, is_read, read_at, 
                   action_url, priority, created_at
            FROM in_app_notifications
            WHERE user_id = :user_id
              AND (expires_at IS NULL OR expires_at > :now)
        """

        if unread_only:
            query += " AND is_read = false"

        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"

        result = await db.execute(
            text(query).bindparams(
                user_id=user_id,
                now=datetime.utcnow(),
                limit=limit,
                offset=offset,
            )
        )

        notifications = []
        for row in result:
            notifications.append(
                {
                    "id": row[0],
                    "type": row[1],
                    "title": row[2],
                    "message": row[3],
                    "data": row[4],
                    "is_read": row[5],
                    "read_at": row[6].isoformat() if row[6] else None,
                    "action_url": row[7],
                    "priority": row[8],
                    "created_at": row[9].isoformat(),
                }
            )

        return notifications

    async def mark_notification_read(
        self,
        db: AsyncSession,
        user_id: int,
        notification_id: int,
    ) -> bool:
        """Mark notification as read."""
        from sqlalchemy import text

        result = await db.execute(
            text(
                "UPDATE in_app_notifications "
                "SET is_read = true, read_at = :now "
                "WHERE id = :notif_id AND user_id = :user_id"
            ).bindparams(
                notif_id=notification_id,
                user_id=user_id,
                now=datetime.utcnow(),
            )
        )

        await db.commit()

        return (result.rowcount or 0) > 0  # type: ignore

    async def mark_all_read(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> int:
        """Mark all notifications as read."""
        from sqlalchemy import text

        result = await db.execute(
            text(
                "UPDATE in_app_notifications "
                "SET is_read = true, read_at = :now "
                "WHERE user_id = :user_id AND is_read = false"
            ).bindparams(
                user_id=user_id,
                now=datetime.utcnow(),
            )
        )

        await db.commit()

        return result.rowcount or 0  # type: ignore

    async def get_unread_count(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> int:
        """Get count of unread notifications."""
        from sqlalchemy import text

        result = await db.execute(
            text(
                "SELECT COUNT(*) FROM in_app_notifications "
                "WHERE user_id = :user_id AND is_read = false "
                "AND (expires_at IS NULL OR expires_at > :now)"
            ).bindparams(
                user_id=user_id,
                now=datetime.utcnow(),
            )
        )

        return result.scalar() or 0

    async def delete_notification(
        self,
        db: AsyncSession,
        user_id: int,
        notification_id: int,
    ) -> bool:
        """Delete notification."""
        from sqlalchemy import text

        result = await db.execute(
            text(
                "DELETE FROM in_app_notifications "
                "WHERE id = :notif_id AND user_id = :user_id"
            ).bindparams(
                notif_id=notification_id,
                user_id=user_id,
            )
        )

        await db.commit()

        return (result.rowcount or 0) > 0  # type: ignore

    async def cleanup_old_notifications(
        self,
        db: AsyncSession,
        days_old: int = 30,
    ) -> int:
        """Delete expired or old read notifications."""
        from sqlalchemy import text

        cutoff = datetime.utcnow() - timedelta(days=days_old)

        result = await db.execute(
            text(
                "DELETE FROM in_app_notifications "
                "WHERE (expires_at IS NOT NULL AND expires_at < :now) "
                "OR (is_read = true AND read_at < :cutoff)"
            ).bindparams(
                now=datetime.utcnow(),
                cutoff=cutoff,
            )
        )

        await db.commit()

        return result.rowcount or 0  # type: ignore


# Singleton instance
_notification_service_instance: Optional[EnhancedNotificationService] = None


def get_notification_service() -> EnhancedNotificationService:
    """Get singleton notification service instance."""
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = EnhancedNotificationService()
    return _notification_service_instance
