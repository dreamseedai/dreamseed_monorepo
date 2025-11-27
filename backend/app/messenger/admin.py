"""
Admin and moderation service for messenger system (Task 3.3).

Provides:
- Content moderation with keyword filtering
- User management (ban, mute, restrict)
- Conversation moderation
- Audit logging
- Report handling
- Admin dashboard statistics
"""

import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.messenger_models import (
    Conversation,
    Message,
)


class ModerationAction(str, Enum):
    """Moderation action types."""

    WARN = "warn"
    MUTE = "mute"
    BAN = "ban"
    DELETE_MESSAGE = "delete_message"
    DELETE_CONVERSATION = "delete_conversation"
    RESTRICT = "restrict"


class ReportReason(str, Enum):
    """Report reason types."""

    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    IMPERSONATION = "impersonation"
    OTHER = "other"


class ReportStatus(str, Enum):
    """Report status types."""

    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class UserRestriction(str, Enum):
    """User restriction types."""

    NONE = "none"
    MUTED = "muted"  # Can't send messages
    RESTRICTED = "restricted"  # Can only send to existing conversations
    BANNED = "banned"  # Can't access messenger at all


# Default keyword blocklist (can be overridden via config)
DEFAULT_BLOCKED_KEYWORDS = [
    # Add actual blocked words in production
    "spam_word_1",
    "spam_word_2",
]


class AdminService:
    """
    Admin and moderation service for messenger.

    Provides content moderation, user management, and audit logging.
    Singleton pattern for consistent state across requests.
    """

    _instance: Optional["AdminService"] = None

    def __init__(self):
        """Initialize admin service."""
        self.blocked_keywords = DEFAULT_BLOCKED_KEYWORDS
        self.blocked_pattern = self._compile_keyword_pattern()

    def _compile_keyword_pattern(self) -> re.Pattern:
        """Compile blocked keywords into regex pattern."""
        if not self.blocked_keywords:
            return re.compile(r"(?!.*)")  # Never matches

        # Escape special regex characters
        escaped = [re.escape(word) for word in self.blocked_keywords]
        pattern = r"\b(" + "|".join(escaped) + r")\b"
        return re.compile(pattern, re.IGNORECASE)

    def update_blocked_keywords(self, keywords: List[str]):
        """Update blocked keywords list."""
        self.blocked_keywords = keywords
        self.blocked_pattern = self._compile_keyword_pattern()

    def check_content_moderation(self, content: str) -> Dict[str, Any]:
        """
        Check if content violates moderation rules.

        Args:
            content: Message content to check

        Returns:
            dict with:
            - is_allowed: bool
            - reason: Optional[str]
            - matched_keywords: List[str]
        """
        matched = self.blocked_pattern.findall(content)

        if matched:
            return {
                "is_allowed": False,
                "reason": "Content contains blocked keywords",
                "matched_keywords": list(set(matched)),
            }

        return {
            "is_allowed": True,
            "reason": None,
            "matched_keywords": [],
        }

    async def get_user_restriction(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> UserRestriction:
        """
        Get user's current restriction level.

        Args:
            db: Database session
            user_id: User ID to check

        Returns:
            UserRestriction enum value
        """
        # Query user's restriction status from user table or separate table
        # For now, return NONE (implement based on your user model)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return UserRestriction.BANNED

        # Check if user has restriction field
        restriction = getattr(user, "messenger_restriction", None)
        if restriction:
            return UserRestriction(restriction)

        return UserRestriction.NONE

    async def set_user_restriction(
        self,
        db: AsyncSession,
        user_id: int,
        restriction: UserRestriction,
        reason: str,
        admin_id: int,
        duration_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Set user restriction level.

        Args:
            db: Database session
            user_id: User to restrict
            restriction: Restriction level
            reason: Reason for restriction
            admin_id: Admin performing action
            duration_minutes: Optional duration (None = permanent)

        Returns:
            dict with restriction details
        """
        # Update user restriction
        # Note: This requires adding messenger_restriction field to User model
        # For now, we'll create a moderation log entry

        expires_at = None
        if duration_minutes:
            expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)

        # Log the action
        log_entry = await self.log_moderation_action(
            db=db,
            action=(
                ModerationAction.RESTRICT
                if restriction != UserRestriction.BANNED
                else ModerationAction.BAN
            ),
            target_user_id=user_id,
            admin_id=admin_id,
            reason=reason,
            metadata={
                "restriction": restriction.value,
                "duration_minutes": duration_minutes,
                "expires_at": expires_at.isoformat() if expires_at else None,
            },
        )

        return {
            "user_id": user_id,
            "restriction": restriction.value,
            "reason": reason,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "admin_id": admin_id,
            "log_id": log_entry.get("id"),
        }

    async def delete_message_by_admin(
        self,
        db: AsyncSession,
        message_id: int,
        admin_id: int,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Delete message by admin (moderation).

        Args:
            db: Database session
            message_id: Message to delete
            admin_id: Admin performing action
            reason: Reason for deletion

        Returns:
            dict with deletion details
        """
        # Get message
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one_or_none()

        if not message:
            return {"error": "Message not found"}

        # Save original content before modifying
        original_content = message.content or ""

        # Soft delete message
        message.deleted_at = datetime.utcnow()
        message.content = "[Content removed by moderator]"

        # Log the action
        log_entry = await self.log_moderation_action(
            db=db,
            action=ModerationAction.DELETE_MESSAGE,
            target_user_id=message.sender_id,
            admin_id=admin_id,
            reason=reason,
            metadata={
                "message_id": message_id,
                "conversation_id": message.conversation_id,
                "original_content": original_content[:100],  # First 100 chars
            },
        )

        await db.commit()

        return {
            "message_id": message_id,
            "deleted": True,
            "reason": reason,
            "admin_id": admin_id,
            "log_id": log_entry.get("id"),
        }

    async def delete_conversation_by_admin(
        self,
        db: AsyncSession,
        conversation_id: str,
        admin_id: int,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Delete conversation by admin (moderation).

        Args:
            db: Database session
            conversation_id: Conversation to delete
            admin_id: Admin performing action
            reason: Reason for deletion

        Returns:
            dict with deletion details
        """
        # Get conversation
        result = await db.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return {"error": "Conversation not found"}

        # Delete all messages in conversation (soft delete)
        await db.execute(
            text(
                "UPDATE messages SET deleted_at = :now, content = '[Conversation removed by moderator]' "
                "WHERE conversation_id = :conv_id AND deleted_at IS NULL"
            ).bindparams(now=datetime.utcnow(), conv_id=conversation_id)
        )

        # Log the action
        log_entry = await self.log_moderation_action(
            db=db,
            action=ModerationAction.DELETE_CONVERSATION,
            target_user_id=None,
            admin_id=admin_id,
            reason=reason,
            metadata={
                "conversation_id": conversation_id,
                "conversation_title": conversation.title,
                "conversation_type": conversation.type,
            },
        )

        await db.commit()

        return {
            "conversation_id": conversation_id,
            "deleted": True,
            "reason": reason,
            "admin_id": admin_id,
            "log_id": log_entry.get("id"),
        }

    async def log_moderation_action(
        self,
        db: AsyncSession,
        action: ModerationAction,
        admin_id: int,
        reason: str,
        target_user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log moderation action to audit trail.

        Args:
            db: Database session
            action: Type of moderation action
            admin_id: Admin performing action
            reason: Reason for action
            target_user_id: Optional user affected
            metadata: Optional additional data

        Returns:
            dict with log entry details
        """
        # In production, insert into moderation_logs table
        # For now, return a dict

        log_entry = {
            "id": None,  # Would be auto-generated
            "action": action.value,
            "admin_id": admin_id,
            "target_user_id": target_user_id,
            "reason": reason,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }

        # TODO: Insert into database when moderation_logs table exists
        # await db.execute(insert(ModerationLog).values(**log_entry))
        # await db.commit()

        return log_entry

    async def get_moderation_stats(
        self,
        db: AsyncSession,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get moderation statistics.

        Args:
            db: Database session
            days: Number of days to look back

        Returns:
            dict with moderation stats
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Deleted messages count
        deleted_messages = await db.execute(
            select(func.count(Message.id)).where(
                and_(
                    Message.deleted_at.isnot(None),
                    Message.deleted_at >= cutoff,
                )
            )
        )
        deleted_count = deleted_messages.scalar() or 0

        # Active restrictions (would need moderation_logs table)
        # For now, return mock data

        return {
            "period_days": days,
            "deleted_messages": deleted_count,
            "active_bans": 0,  # TODO: Query from moderation_logs
            "active_mutes": 0,  # TODO: Query from moderation_logs
            "pending_reports": 0,  # TODO: Query from reports table
            "resolved_reports": 0,  # TODO: Query from reports table
        }

    async def get_flagged_messages(
        self,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get messages flagged for review.

        Args:
            db: Database session
            limit: Max results
            offset: Pagination offset

        Returns:
            List of flagged messages
        """
        # In production, query messages with reports or keyword matches
        # For now, return messages that were deleted

        result = await db.execute(
            select(Message, User.email)
            .join(User, User.id == Message.sender_id)
            .where(Message.deleted_at.isnot(None))
            .order_by(desc(Message.deleted_at))
            .limit(limit)
            .offset(offset)
        )

        messages = []
        for msg, sender_email in result:
            messages.append(
                {
                    "id": msg.id,
                    "conversation_id": msg.conversation_id,
                    "sender_id": msg.sender_id,
                    "sender_email": sender_email,
                    "content": msg.content,
                    "deleted_at": (
                        msg.deleted_at.isoformat() if msg.deleted_at else None
                    ),
                    "created_at": msg.created_at.isoformat(),
                }
            )

        return messages

    async def get_user_moderation_history(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get moderation history for a user.

        Args:
            db: Database session
            user_id: User to check
            limit: Max results

        Returns:
            List of moderation actions
        """
        # TODO: Query moderation_logs table when it exists
        # For now, return empty list

        return []

    async def create_report(
        self,
        db: AsyncSession,
        reporter_id: int,
        reported_user_id: Optional[int] = None,
        message_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
        reason: ReportReason = ReportReason.OTHER,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a report for admin review.

        Args:
            db: Database session
            reporter_id: User creating report
            reported_user_id: Optional user being reported
            message_id: Optional message being reported
            conversation_id: Optional conversation being reported
            reason: Report reason
            description: Optional detailed description

        Returns:
            dict with report details
        """
        # TODO: Insert into reports table when it exists

        report = {
            "id": None,  # Would be auto-generated
            "reporter_id": reporter_id,
            "reported_user_id": reported_user_id,
            "message_id": message_id,
            "conversation_id": conversation_id,
            "reason": reason.value,
            "description": description,
            "status": ReportStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
        }

        return report

    async def get_pending_reports(
        self,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get pending reports for admin review.

        Args:
            db: Database session
            limit: Max results
            offset: Pagination offset

        Returns:
            List of pending reports
        """
        # TODO: Query reports table when it exists

        return []

    async def resolve_report(
        self,
        db: AsyncSession,
        report_id: int,
        admin_id: int,
        resolution: str,
        action_taken: Optional[ModerationAction] = None,
    ) -> Dict[str, Any]:
        """
        Resolve a report.

        Args:
            db: Database session
            report_id: Report to resolve
            admin_id: Admin resolving report
            resolution: Resolution description
            action_taken: Optional moderation action taken

        Returns:
            dict with resolution details
        """
        # TODO: Update reports table when it exists

        return {
            "report_id": report_id,
            "status": ReportStatus.RESOLVED.value,
            "admin_id": admin_id,
            "resolution": resolution,
            "action_taken": action_taken.value if action_taken else None,
            "resolved_at": datetime.utcnow().isoformat(),
        }

    async def get_admin_dashboard_stats(
        self,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Get comprehensive admin dashboard statistics.

        Returns:
            dict with dashboard stats
        """
        # Total users
        total_users = await db.execute(select(func.count(User.id)))
        user_count = total_users.scalar() or 0

        # Total conversations
        total_convs = await db.execute(select(func.count(Conversation.conversation_id)))
        conv_count = total_convs.scalar() or 0

        # Total messages
        total_msgs = await db.execute(select(func.count(Message.id)))
        msg_count = total_msgs.scalar() or 0

        # Messages today
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        msgs_today = await db.execute(
            select(func.count(Message.id)).where(Message.created_at >= today_start)
        )
        today_count = msgs_today.scalar() or 0

        # Deleted messages (last 30 days)
        cutoff_30d = datetime.utcnow() - timedelta(days=30)
        deleted_msgs = await db.execute(
            select(func.count(Message.id)).where(
                and_(
                    Message.deleted_at.isnot(None),
                    Message.deleted_at >= cutoff_30d,
                )
            )
        )
        deleted_count = deleted_msgs.scalar() or 0

        return {
            "total_users": user_count,
            "total_conversations": conv_count,
            "total_messages": msg_count,
            "messages_today": today_count,
            "deleted_messages_30d": deleted_count,
            "pending_reports": 0,  # TODO: Query reports table
            "active_restrictions": 0,  # TODO: Query moderation_logs
        }


# Singleton instance
_admin_service_instance: Optional[AdminService] = None


def get_admin_service() -> AdminService:
    """Get singleton admin service instance."""
    global _admin_service_instance
    if _admin_service_instance is None:
        _admin_service_instance = AdminService()
    return _admin_service_instance
