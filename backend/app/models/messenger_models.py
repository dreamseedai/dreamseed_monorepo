"""
SQLAlchemy models for Messenger system

This module defines the database schema for the real-time messaging system,
including conversations, participants, messages, read receipts, and notification settings.
"""

from __future__ import annotations

import uuid
import datetime as dt
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB as postgresql_JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Conversation(Base):
    """
    Conversation model representing a chat channel (direct, group, or announcement).

    Attributes:
        type: Type of conversation - 'direct' (1:1), 'group', or 'announcement'
        title: Optional title for group/announcement conversations
        zone_id: Associated zone (e.g., UnivPrepAI, CollegePrepAI)
        org_id: Associated organization (school, academy)
        created_by: User who created the conversation
    """

    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            "type IN ('direct', 'group', 'announcement')", name="ck_conversations_type"
        ),
        Index("idx_conversations_zone_org", "zone_id", "org_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    zone_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=True
    )
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    participants: Mapped[list["ConversationParticipant"]] = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
    calls: Mapped[list["Call"]] = relationship(
        "Call", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, type={self.type}, title={self.title!r})>"


class ConversationParticipant(Base):
    """
    Association model for participants in a conversation.

    Attributes:
        role: Participant role - 'admin', 'member', or 'observer'
        joined_at: When the participant joined the conversation
        last_read_at: Timestamp of last read message (for unread count)
    """

    __tablename__ = "conversation_participants"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'member', 'observer')", name="ck_participants_role"
        ),
        UniqueConstraint(
            "conversation_id", "user_id", name="uq_conversation_participant"
        ),
        Index("idx_participants_user", "user_id"),
        Index("idx_participants_conversation", "conversation_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    last_read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="participants"
    )
    # Note: relationship to User model will be added when User model is updated

    def __repr__(self) -> str:
        return f"<ConversationParticipant(conv_id={self.conversation_id}, user_id={self.user_id}, role={self.role})>"


class Message(Base):
    """
    Message model representing a chat message.

    Attributes:
        message_type: Type of message - 'text', 'image', 'file', or 'system'
        content: Text content of the message
        file_url: URL for attached files/images (Backblaze B2 or S3)
        file_size: Size of attached file in bytes
        file_name: Original filename of attached file
        edited_at: Timestamp of last edit (null if never edited)
        deleted_at: Soft delete timestamp (null if not deleted)
        parent_id: ID of the message this is replying to (null if not a reply)
        thread_id: ID of the root message in the thread (null if this IS the root)
        reply_count: Number of replies to this message
        last_reply_at: Timestamp of the most recent reply
    """

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "message_type IN ('text', 'image', 'file', 'system')",
            name="ck_messages_type",
        ),
        Index("idx_messages_conversation_created", "conversation_id", "created_at"),
        Index("idx_messages_sender", "sender_id"),
        # Note: Partial index on deleted_at (WHERE deleted_at IS NULL) is created via migration
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE")
    )
    sender_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Threading fields
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True
    )
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True
    )
    reply_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reply_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Reaction fields
    reaction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )
    read_receipts: Mapped[list["ReadReceipt"]] = relationship(
        "ReadReceipt", back_populates="message", cascade="all, delete-orphan"
    )
    reactions: Mapped[list["MessageReaction"]] = relationship(
        "MessageReaction", back_populates="message", cascade="all, delete-orphan"
    )

    # Threading relationships
    parent: Mapped[Optional["Message"]] = relationship(
        "Message",
        remote_side=[id],
        foreign_keys=[parent_id],
        back_populates="replies",
    )
    replies: Mapped[list["Message"]] = relationship(
        "Message",
        remote_side=[parent_id],
        foreign_keys=[parent_id],
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    thread_root: Mapped[Optional["Message"]] = relationship(
        "Message",
        remote_side=[id],
        foreign_keys=[thread_id],
        back_populates="thread_replies",
    )
    thread_replies: Mapped[list["Message"]] = relationship(
        "Message",
        remote_side=[thread_id],
        foreign_keys=[thread_id],
        back_populates="thread_root",
    )

    # Note: relationship to User model (sender) will be added when User model is updated

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conv_id={self.conversation_id}, sender={self.sender_id}, thread={self.thread_id})>"


class ReadReceipt(Base):
    """
    ReadReceipt model indicating a user has read a message.

    Used to track read status and calculate unread message counts.
    """

    __tablename__ = "read_receipts"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_read_receipt"),
        Index("idx_read_receipts_message", "message_id"),
        Index("idx_read_receipts_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="read_receipts")
    # Note: relationship to User model will be added when User model is updated

    def __repr__(self) -> str:
        return f"<ReadReceipt(message_id={self.message_id}, user_id={self.user_id}, read_at={self.read_at})>"


class NotificationSetting(Base):
    """
    Notification settings for a user in a conversation.

    Attributes:
        muted: If true, user won't receive notifications from this conversation
        push_enabled: Enable push notifications (Firebase/APNs)
        email_enabled: Enable email notifications (SendGrid)
    """

    __tablename__ = "notification_settings"
    __table_args__ = (
        UniqueConstraint("user_id", "conversation_id", name="uq_notification_setting"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE")
    )
    muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    # Note: relationships to User and Conversation models will be available via foreign keys

    def __repr__(self) -> str:
        return f"<NotificationSetting(user_id={self.user_id}, conv_id={self.conversation_id}, muted={self.muted})>"


class DeviceToken(Base):
    """
    Device token model for push notifications.

    Stores FCM, APNs, or Web Push tokens for user devices.

    Attributes:
        user_id: Owner of the device
        token: FCM registration token, APNs device token, or Web Push subscription JSON
        platform: Device platform - 'ios', 'android', or 'web'
        provider: Push provider - 'fcm', 'apns', or 'web_push'
        device_name: Optional user-friendly device name
        is_active: Whether the token is still valid
        last_used_at: Last time a notification was sent to this device
    """

    __tablename__ = "device_tokens"
    __table_args__ = (
        CheckConstraint(
            "platform IN ('ios', 'android', 'web')", name="ck_device_tokens_platform"
        ),
        CheckConstraint(
            "provider IN ('fcm', 'apns', 'web_push')", name="ck_device_tokens_provider"
        ),
        UniqueConstraint("token", name="uq_device_token"),
        Index("idx_device_tokens_user", "user_id"),
        Index("idx_device_tokens_user_active", "user_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    token: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    # Note: relationship to User model will be added when User model is updated

    def __repr__(self) -> str:
        return f"<DeviceToken(id={self.id}, user_id={self.user_id}, platform={self.platform}, active={self.is_active})>"


class InAppNotification(Base):
    """
    In-app notification model for Task 4.1.

    Stores persistent notifications that users can browse, mark as read, and delete.
    Notifications automatically expire after 30 days.

    Attributes:
        user_id: Notification recipient
        type: Notification type (new_message, mention, etc.)
        title: Notification title
        message: Notification message
        data: Additional JSONB data
        is_read: Whether notification has been read
        read_at: When notification was read
        action_url: Deep link URL for notification action
        priority: Priority level (low, normal, high, urgent)
        created_at: When notification was created
        expires_at: When notification expires (auto-cleanup)
    """

    __tablename__ = "in_app_notifications"
    __table_args__ = (
        Index("idx_notifications_user", "user_id"),
        Index("idx_notifications_unread", "user_id", "is_read"),
        Index("idx_notifications_created", "created_at"),
        Index("idx_notifications_type", "type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Optional[dict]] = mapped_column(postgresql_JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<InAppNotification(id={self.id}, user_id={self.user_id}, type={self.type})>"


class NotificationPreference(Base):
    """
    Notification preference model for Task 4.1.

    Stores user preferences for notification channels and types.
    Users can enable/disable notifications per channel/type and set quiet hours.

    Attributes:
        user_id: User who owns the preference
        channel: Notification channel (push, email, in_app)
        notification_type: Type of notification
        enabled: Whether notifications are enabled
        quiet_hours_start: Quiet hours start time (do not disturb)
        quiet_hours_end: Quiet hours end time
        updated_at: Last update timestamp
    """

    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "channel", "notification_type"),
        Index("idx_preferences_user", "user_id"),
        Index("idx_preferences_lookup", "user_id", "channel", "notification_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    quiet_hours_start: Mapped[Optional[dt.time]] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[Optional[dt.time]] = mapped_column(Time, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<NotificationPreference(user_id={self.user_id}, channel={self.channel}, type={self.notification_type})>"


class MessageReaction(Base):
    """
    Message reaction model for emoji reactions (Task 5.2).

    Stores emoji reactions on messages. Each user can add multiple different
    emoji reactions to a message, but only one of each type.

    Attributes:
        message_id: Message being reacted to
        user_id: User who added the reaction
        emoji: Emoji shortcode (e.g., "thumbs_up", "heart", "smile")
        emoji_unicode: Unicode representation (e.g., "👍", "❤️", "😊")
        created_at: When the reaction was added
    """

    __tablename__ = "message_reactions"
    __table_args__ = (
        UniqueConstraint(
            "message_id", "user_id", "emoji", name="uq_message_user_emoji"
        ),
        Index("idx_message_reactions_message", "message_id"),
        Index("idx_message_reactions_user", "user_id"),
        Index("idx_message_reactions_emoji", "emoji"),
        Index("idx_message_reactions_message_emoji", "message_id", "emoji"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    emoji: Mapped[str] = mapped_column(String(50), nullable=False)
    emoji_unicode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="reactions")
    # Note: relationship to User model will be added when User model is updated

    def __repr__(self) -> str:
        return f"<MessageReaction(id={self.id}, message_id={self.message_id}, user_id={self.user_id}, emoji={self.emoji})>"


class Call(Base):
    """
    Call model for voice/video calls.

    Tracks call sessions with status, duration, and quality metrics.
    Supports both audio-only and video calls with recording capability.
    """

    __tablename__ = "calls"
    __table_args__ = (
        CheckConstraint("call_type IN ('audio', 'video')", name="valid_call_type"),
        CheckConstraint(
            "status IN ('initiated', 'ringing', 'active', 'ended', 'missed', 'rejected', 'failed')",
            name="valid_call_status",
        ),
        CheckConstraint(
            "quality_rating IS NULL OR (quality_rating >= 1 AND quality_rating <= 5)",
            name="valid_quality_rating",
        ),
        Index("idx_calls_conversation", "conversation_id"),
        Index("idx_calls_initiator", "initiator_id"),
        Index("idx_calls_status", "status"),
        Index("idx_calls_started", "started_at"),
        Index("idx_calls_type", "call_type"),
        Index(
            "idx_calls_active",
            "conversation_id",
            "status",
            postgresql_where="status IN ('initiated', 'ringing', 'active')",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    initiator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    call_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'audio' or 'video'
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="initiated"
    )  # initiated, ringing, active, ended, missed, rejected, failed
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    answered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_reason: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # completed, declined, no_answer, failed, timeout
    recording_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    quality_rating: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 1-5 stars
    call_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", postgresql_JSONB, nullable=True
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="calls"
    )
    participants: Mapped[list["CallParticipant"]] = relationship(
        "CallParticipant",
        back_populates="call",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Call(id={self.id}, type={self.call_type}, status={self.status})>"


class CallParticipant(Base):
    """
    CallParticipant model for tracking individual user participation in calls.

    Captures join/leave times, media settings, and connection quality per user.
    """

    __tablename__ = "call_participants"
    __table_args__ = (
        UniqueConstraint("call_id", "user_id", name="uq_call_participant"),
        Index("idx_call_participants_call", "call_id"),
        Index("idx_call_participants_user", "user_id"),
        Index("idx_call_participants_answered", "answered"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    joined_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    left_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_initiator: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    answered: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    video_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    audio_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    screen_share_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    connection_quality: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # excellent, good, fair, poor
    peer_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # WebRTC peer identifier

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="participants")

    def __repr__(self) -> str:
        return f"<CallParticipant(id={self.id}, call_id={self.call_id}, user_id={self.user_id}, answered={self.answered})>"
