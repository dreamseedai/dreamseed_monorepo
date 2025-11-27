"""
Pydantic schemas for Messenger API

Schemas for conversations, messages, participants, and notification settings.
Used for request/response validation in FastAPI endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Conversation Schemas
# ============================================================================


class ConversationParticipantBase(BaseModel):
    """Base participant info"""

    user_id: int = Field(..., description="User ID")
    role: Literal["admin", "member", "observer"] = Field(
        "member", description="Participant role"
    )


class ConversationParticipantResponse(ConversationParticipantBase):
    """Participant response with metadata"""

    id: uuid.UUID
    conversation_id: uuid.UUID
    joined_at: datetime
    last_read_at: Optional[datetime] = None
    # Optional: Include user details if needed
    # user_email: Optional[str] = None
    # user_name: Optional[str] = None

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Request to create a new conversation"""

    type: Literal["direct", "group", "announcement"] = Field(
        ..., description="Conversation type"
    )
    title: Optional[str] = Field(
        None,
        max_length=255,
        description="Conversation title (required for group/announcement)",
    )
    zone_id: Optional[int] = Field(None, description="Zone ID")
    org_id: Optional[int] = Field(None, description="Organization ID")
    participant_ids: list[int] = Field(
        ..., min_length=1, max_length=100, description="Initial participant user IDs"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str], info) -> Optional[str]:
        # Get conversation type from values if available
        conv_type = info.data.get("type")
        if conv_type in ("group", "announcement") and not v:
            raise ValueError(
                "Title is required for group and announcement conversations"
            )
        return v

    @field_validator("participant_ids")
    @classmethod
    def validate_participants(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("Duplicate participant IDs not allowed")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "type": "group",
                "title": "수학 1반 - 2025 봄학기",
                "zone_id": 1,
                "org_id": 1,
                "participant_ids": [1, 2, 3, 4, 5],
            }
        }


class ConversationResponse(BaseModel):
    """Conversation response with metadata"""

    id: uuid.UUID
    type: str
    title: Optional[str] = None
    zone_id: Optional[int] = None
    org_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    # Optional: Include participant count, last message preview
    participant_count: Optional[int] = None
    last_message_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: Optional[int] = None

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Paginated conversation list"""

    conversations: list[ConversationResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Message Schemas
# ============================================================================


class MessageCreate(BaseModel):
    """Request to send a new message"""

    content: Optional[str] = Field(
        None, max_length=10000, description="Message text content"
    )
    message_type: Literal["text", "image", "file", "system"] = Field(
        "text", description="Message type"
    )
    file_url: Optional[str] = Field(None, description="Uploaded file URL (S3/B2)")
    file_size: Optional[int] = Field(
        None, ge=0, le=10485760, description="File size in bytes (max 10MB)"
    )
    file_name: Optional[str] = Field(
        None, max_length=255, description="Original filename"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str], info) -> Optional[str]:
        msg_type = info.data.get("message_type")
        if msg_type == "text" and not v:
            raise ValueError("Content is required for text messages")
        if v and not v.strip():
            raise ValueError("Content cannot be empty or whitespace-only")
        return v

    @field_validator("file_url")
    @classmethod
    def validate_file_url(cls, v: Optional[str], info) -> Optional[str]:
        msg_type = info.data.get("message_type")
        if msg_type in ("image", "file") and not v:
            raise ValueError(f"file_url is required for {msg_type} messages")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "content": "내일 시험 범위가 변경되었습니다. 3장까지만 출제됩니다.",
                "message_type": "text",
            }
        }


class MessageUpdate(BaseModel):
    """Request to edit an existing message"""

    content: str = Field(
        ..., min_length=1, max_length=10000, description="Updated message content"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace-only")
        return v


class MessageResponse(BaseModel):
    """Message response with metadata"""

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: Optional[int] = None
    content: Optional[str] = None
    message_type: str
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None
    created_at: datetime
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    # Optional: Include sender details
    # sender_name: Optional[str] = None
    # sender_email: Optional[str] = None
    # read_by_count: Optional[int] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Paginated message list"""

    messages: list[MessageResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# Notification Settings Schemas
# ============================================================================


class NotificationSettingsUpdate(BaseModel):
    """Request to update notification settings"""

    muted: Optional[bool] = Field(None, description="Mute all notifications")
    push_enabled: Optional[bool] = Field(None, description="Enable push notifications")
    email_enabled: Optional[bool] = Field(
        None, description="Enable email notifications"
    )


class NotificationSettingsResponse(BaseModel):
    """Notification settings response"""

    id: uuid.UUID
    user_id: int
    conversation_id: uuid.UUID
    muted: bool
    push_enabled: bool
    email_enabled: bool

    class Config:
        from_attributes = True


# ============================================================================
# Participant Management Schemas
# ============================================================================


class ParticipantAdd(BaseModel):
    """Request to add participants to a conversation"""

    user_ids: list[int] = Field(
        ..., min_length=1, max_length=50, description="User IDs to add"
    )
    role: Literal["admin", "member", "observer"] = Field(
        "member", description="Role for new participants"
    )

    @field_validator("user_ids")
    @classmethod
    def validate_user_ids(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("Duplicate user IDs not allowed")
        return v


class ParticipantRemove(BaseModel):
    """Request to remove a participant from a conversation"""

    user_id: int = Field(..., description="User ID to remove")


# ============================================================================
# Read Receipt Schemas
# ============================================================================


class ReadReceiptCreate(BaseModel):
    """Request to mark messages as read"""

    message_ids: list[uuid.UUID] = Field(
        ..., min_length=1, max_length=100, description="Message IDs to mark as read"
    )


class ReadReceiptResponse(BaseModel):
    """Read receipt response"""

    id: uuid.UUID
    message_id: uuid.UUID
    user_id: int
    read_at: datetime

    class Config:
        from_attributes = True
