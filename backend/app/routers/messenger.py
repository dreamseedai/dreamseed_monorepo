"""
Messenger API endpoints

REST API for conversations, messages, and notification settings.
Supports direct messages, group chats, and announcements.

Authorization:
- get_current_user: All authenticated users can access messenger
- Conversation access: RLS policies enforce participant-based access
- Admin actions: Only conversation admins can add/remove participants

Endpoints:
- GET /conversations - List user's conversations
- POST /conversations - Create new conversation
- GET /conversations/{id} - Get conversation details
- DELETE /conversations/{id} - Leave conversation
- GET /conversations/{id}/messages - Get message history (paginated)
- POST /conversations/{id}/messages - Send message
- PUT /messages/{id} - Edit message
- DELETE /messages/{id} - Delete message (soft delete)
- POST /conversations/{id}/participants - Add participants (admin only)
- DELETE /conversations/{id}/participants/{user_id} - Remove participant (admin only)
- GET /conversations/{id}/settings - Get notification settings
- PUT /conversations/{id}/settings - Update notification settings
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi import status as status_lib
from sqlalchemy import and_, delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.messenger.pubsub import get_pubsub
from app.messenger.websocket import manager
from app.models.messenger_models import (
    Conversation,
    ConversationParticipant,
    Message,
    NotificationSetting,
)
from app.models.user import User
from app.schemas.messenger_schemas import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    MessageUpdate,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    ParticipantAdd,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/messenger", tags=["messenger"])


# ============================================================================
# Helper Functions
# ============================================================================


async def get_conversation_or_404(
    conversation_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> Conversation:
    """
    Get conversation and verify user is a participant.

    Args:
        conversation_id: Conversation UUID
        user: Current user
        db: Database session

    Returns:
        Conversation object

    Raises:
        HTTPException 404: If conversation not found or user not a participant
    """
    # Check if user is a participant
    stmt = select(ConversationParticipant).where(
        and_(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user.id,
        )
    )
    result = await db.execute(stmt)
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied",
        )

    # Fetch conversation
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return conversation


async def is_conversation_admin(
    conversation_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> bool:
    """Check if user is an admin of the conversation"""
    stmt = select(ConversationParticipant).where(
        and_(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user.id,
            ConversationParticipant.role == "admin",
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


# ============================================================================
# Conversation Endpoints
# ============================================================================


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    List all conversations for the current user.

    Returns conversations ordered by last activity (most recent first).
    Includes unread message count for each conversation.
    """
    # Get conversation IDs where user is a participant
    participant_stmt = select(ConversationParticipant.conversation_id).where(
        ConversationParticipant.user_id == user.id
    )

    # Count total conversations
    count_stmt = (
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.id.in_(participant_stmt))
    )
    result = await db.execute(count_stmt)
    total = result.scalar_one()

    # Fetch paginated conversations
    offset = (page - 1) * page_size
    stmt = (
        select(Conversation)
        .where(Conversation.id.in_(participant_stmt))
        .order_by(desc(Conversation.updated_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()

    # TODO: Add unread count, last message preview
    # This requires additional queries or CTE for optimization

    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status_lib.HTTP_201_CREATED,
)
async def create_conversation(
    data: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new conversation.

    The creator is automatically added as an admin participant.
    All specified participant_ids are added as members.

    For direct messages (type='direct'):
    - Must have exactly 2 participants (including creator)
    - Title is optional (auto-generated from participant names)

    For groups and announcements:
    - Title is required
    - Can have multiple participants
    """
    # Validate direct message rules
    if data.type == "direct":
        if len(data.participant_ids) != 1:  # +1 for creator = 2 total
            raise HTTPException(
                status_code=status_lib.HTTP_400_BAD_REQUEST,
                detail="Direct messages must have exactly 2 participants",
            )

    # Create conversation
    conversation = Conversation(
        type=data.type,
        title=data.title,
        zone_id=data.zone_id,
        org_id=data.org_id,
        created_by=user.id,
    )
    db.add(conversation)
    await db.flush()  # Get conversation.id

    # Add creator as admin
    creator_participant = ConversationParticipant(
        conversation_id=conversation.id,
        user_id=user.id,
        role="admin",
    )
    db.add(creator_participant)

    # Add other participants as members
    for participant_id in data.participant_ids:
        if participant_id != user.id:  # Skip if creator already added
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                user_id=participant_id,
                role="member",
            )
            db.add(participant)

    await db.commit()
    await db.refresh(conversation)

    return ConversationResponse.model_validate(conversation)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get conversation details"""
    conversation = await get_conversation_or_404(conversation_id, user, db)
    return ConversationResponse.model_validate(conversation)


@router.delete(
    "/conversations/{conversation_id}", status_code=status_lib.HTTP_204_NO_CONTENT
)
async def leave_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Leave a conversation (remove self as participant).

    If the last admin leaves, the conversation becomes inaccessible.
    TODO: Implement logic to promote another member to admin before leaving.
    """
    # Verify user is a participant
    await get_conversation_or_404(conversation_id, user, db)

    # Remove participant
    stmt = delete(ConversationParticipant).where(
        and_(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user.id,
        )
    )
    await db.execute(stmt)
    await db.commit()

    return None


# ============================================================================
# Message Endpoints
# ============================================================================


@router.get(
    "/conversations/{conversation_id}/messages", response_model=MessageListResponse
)
async def list_messages(
    conversation_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Messages per page"),
    before: Optional[uuid.UUID] = Query(
        None, description="Get messages before this message ID (for infinite scroll)"
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get message history for a conversation.

    Returns messages in reverse chronological order (newest first).
    Supports cursor-based pagination with 'before' parameter.
    Only returns non-deleted messages.
    """
    # Verify user is a participant
    await get_conversation_or_404(conversation_id, user, db)

    # Base query: non-deleted messages in this conversation
    base_stmt = select(Message).where(
        and_(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None),
        )
    )

    # Add cursor pagination if 'before' provided
    if before:
        # Get timestamp of the 'before' message
        before_stmt = select(Message.created_at).where(Message.id == before)
        result = await db.execute(before_stmt)
        before_time = result.scalar_one_or_none()
        if before_time:
            base_stmt = base_stmt.where(Message.created_at < before_time)

    # Count total (for pagination metadata)
    count_stmt = (
        select(func.count())
        .select_from(Message)
        .where(
            and_(
                Message.conversation_id == conversation_id,
                Message.deleted_at.is_(None),
            )
        )
    )
    result = await db.execute(count_stmt)
    total = result.scalar_one()

    # Fetch messages
    stmt = base_stmt.order_by(desc(Message.created_at)).limit(page_size)
    result = await db.execute(stmt)
    messages = result.scalars().all()

    return MessageListResponse(
        messages=[MessageResponse.model_validate(m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
        has_more=len(messages) == page_size,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status_lib.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: uuid.UUID,
    data: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Send a message to a conversation.

    This is a fallback REST endpoint. In production, messages should be sent
    via WebSocket for real-time delivery. This endpoint is useful for:
    - Testing
    - File uploads (send file URL after upload)
    - Fallback when WebSocket is unavailable
    """
    # Verify user is a participant
    await get_conversation_or_404(conversation_id, user, db)

    # Create message
    message = Message(
        conversation_id=conversation_id,
        sender_id=user.id,
        content=data.content,
        message_type=data.message_type,
        file_url=data.file_url,
        file_size=data.file_size,
        file_name=data.file_name,
    )
    db.add(message)

    # Update conversation updated_at
    stmt = (
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(updated_at=func.now())
    )
    await db.execute(stmt)

    await db.commit()
    await db.refresh(message)

    # Broadcast message via Redis Pub/Sub to all connected clients
    pubsub = get_pubsub()
    await pubsub.publish_message(
        conversation_id=conversation_id,
        message_data=MessageResponse.model_validate(message).model_dump(mode="json"),
    )

    return MessageResponse.model_validate(message)


@router.put("/messages/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: uuid.UUID,
    data: MessageUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Edit a message (sender only).

    Only the original sender can edit their messages.
    Edited messages are marked with edited_at timestamp.
    """
    # Fetch message
    stmt = select(Message).where(Message.id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    # Verify ownership
    if message.sender_id != user.id:
        raise HTTPException(
            status_code=status_lib.HTTP_403_FORBIDDEN,
            detail="You can only edit your own messages",
        )

    # Verify not deleted
    if message.deleted_at:
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail="Cannot edit deleted message",
        )

    # Update message
    message.content = data.content
    message.edited_at = func.now()
    await db.commit()
    await db.refresh(message)

    # Broadcast edit event via Redis Pub/Sub
    pubsub = get_pubsub()
    await pubsub.publish_message(
        conversation_id=message.conversation_id,
        message_data={
            "event": "message_edited",
            "message": MessageResponse.model_validate(message).model_dump(mode="json"),
        },
    )

    return MessageResponse.model_validate(message)


@router.delete("/messages/{message_id}", status_code=status_lib.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete a message (soft delete).

    Only the sender or conversation admin can delete messages.
    Soft delete: message.deleted_at is set, content remains in DB.
    """
    # Fetch message
    stmt = select(Message).where(Message.id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    # Check if user is sender or conversation admin
    is_sender = message.sender_id == user.id
    is_admin = await is_conversation_admin(message.conversation_id, user, db)

    if not (is_sender or is_admin):
        raise HTTPException(
            status_code=status_lib.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages or admin can delete any message",
        )

    # Soft delete
    message.deleted_at = func.now()
    await db.commit()

    # Broadcast delete event via Redis Pub/Sub
    pubsub = get_pubsub()
    await pubsub.publish_message(
        conversation_id=message.conversation_id,
        message_data={
            "event": "message_deleted",
            "message_id": str(message.id),
        },
    )

    return None


# ============================================================================
# Message Reactions Endpoints
# ============================================================================


@router.post("/messages/{message_id}/reactions")
async def add_reaction(
    message_id: uuid.UUID,
    emoji: str = Query(
        ..., description="Emoji shortcode or unicode (e.g., 'thumbs_up' or '👍')"
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Add an emoji reaction to a message.

    Args:
        message_id: ID of the message to react to
        emoji: Emoji shortcode (e.g., "thumbs_up") or unicode (e.g., "👍")

    Returns:
        Reaction details

    Raises:
        HTTPException 404: Message not found
        HTTPException 403: User not a participant
        HTTPException 409: Reaction already exists
    """
    from app.messenger.reactions import get_reactions_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_reactions_service()
        reaction = await service.add_reaction(
            db=db,
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
        )

        # Broadcast reaction event via Redis Pub/Sub
        from app.models.messenger_models import Message

        stmt = select(Message.conversation_id).where(Message.id == message_id)
        result = await db.execute(stmt)
        conversation_id = result.scalar_one_or_none()

        if conversation_id:
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=conversation_id,
                message_data={
                    "event": "reaction_added",
                    "message_id": str(message_id),
                    "user_id": user_id,
                    "emoji": emoji,
                    "emoji_unicode": reaction.emoji_unicode,
                    "reaction_id": reaction.id,
                },
            )

        return {
            "id": reaction.id,
            "message_id": str(reaction.message_id),
            "emoji": reaction.emoji,
            "emoji_unicode": reaction.emoji_unicode,
            "user_id": reaction.user_id,
            "created_at": reaction.created_at.isoformat(),
        }

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status_lib.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        elif "already reacted" in str(e):
            raise HTTPException(
                status_code=status_lib.HTTP_409_CONFLICT,
                detail=str(e),
            )
        elif "not a participant" in str(e):
            raise HTTPException(
                status_code=status_lib.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/messages/{message_id}/reactions/{emoji}",
    status_code=status_lib.HTTP_204_NO_CONTENT,
)
async def remove_reaction(
    message_id: uuid.UUID,
    emoji: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Remove an emoji reaction from a message.

    Args:
        message_id: ID of the message
        emoji: Emoji shortcode or unicode

    Returns:
        204 No Content on success

    Raises:
        HTTPException 404: Reaction not found
    """
    from app.messenger.reactions import get_reactions_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_reactions_service()
        removed = await service.remove_reaction(
            db=db,
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
        )

        if not removed:
            raise HTTPException(
                status_code=status_lib.HTTP_404_NOT_FOUND,
                detail="Reaction not found",
            )

        # Broadcast reaction event via Redis Pub/Sub
        from app.models.messenger_models import Message

        stmt = select(Message.conversation_id).where(Message.id == message_id)
        result = await db.execute(stmt)
        conversation_id = result.scalar_one_or_none()

        if conversation_id:
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=conversation_id,
                message_data={
                    "event": "reaction_removed",
                    "message_id": str(message_id),
                    "user_id": user_id,
                    "emoji": emoji,
                },
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove reaction error: {e}")
        raise HTTPException(
            status_code=status_lib.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove reaction",
        )


@router.post("/messages/{message_id}/reactions/toggle")
async def toggle_reaction(
    message_id: uuid.UUID,
    emoji: str = Query(..., description="Emoji shortcode or unicode"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Toggle a reaction (add if not exists, remove if exists).

    Convenience endpoint for single-click reactions in UI.

    Args:
        message_id: ID of the message
        emoji: Emoji shortcode or unicode

    Returns:
        Action taken and reaction details
    """
    from app.messenger.reactions import get_reactions_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_reactions_service()
        result = await service.toggle_reaction(
            db=db,
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
        )

        # Broadcast reaction event via Redis Pub/Sub
        from app.models.messenger_models import Message

        stmt = select(Message.conversation_id).where(Message.id == message_id)
        result_conv = await db.execute(stmt)
        conversation_id = result_conv.scalar_one_or_none()

        if conversation_id:
            pubsub = get_pubsub()
            event = (
                "reaction_added" if result["action"] == "added" else "reaction_removed"
            )
            await pubsub.publish_message(
                conversation_id=conversation_id,
                message_data={
                    "event": event,
                    "message_id": str(message_id),
                    "user_id": user_id,
                    "emoji": emoji,
                    **(
                        {
                            "emoji_unicode": result.get("emoji_unicode"),
                            "reaction_id": result.get("reaction_id"),
                        }
                        if result["action"] == "added"
                        else {}
                    ),
                },
            )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/messages/{message_id}/reactions")
async def get_message_reactions(
    message_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get all reactions on a message, grouped by emoji.

    Returns reaction counts, user lists, and whether current user has reacted.

    Args:
        message_id: ID of the message

    Returns:
        Grouped reaction data with counts and user lists

    Raises:
        HTTPException 404: Message not found
        HTTPException 403: User not a participant
    """
    from app.messenger.reactions import get_reactions_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_reactions_service()
        reactions = await service.get_message_reactions(
            db=db,
            message_id=message_id,
            user_id=user_id,
        )

        return reactions

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status_lib.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        elif "not a participant" in str(e):
            raise HTTPException(
                status_code=status_lib.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/messages/{message_id}/reactions/summary")
async def get_reaction_summary(
    message_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get quick summary of reactions on a message (counts only).

    Lightweight endpoint for displaying reaction badges without full data.

    Args:
        message_id: ID of the message

    Returns:
        Total reaction count and unique emoji count

    Raises:
        HTTPException 404: Message not found
    """
    from app.messenger.reactions import get_reactions_service

    try:
        service = get_reactions_service()
        summary = await service.get_reaction_summary(
            db=db,
            message_id=message_id,
        )

        return summary

    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/conversations/{conversation_id}/reactions/popular")
async def get_popular_reactions(
    conversation_id: uuid.UUID,
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of emoji to return"
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get most popular emoji reactions in a conversation.

    Useful for suggesting frequently-used reactions in UI.

    Args:
        conversation_id: ID of the conversation
        limit: Maximum number of emoji to return (1-50)

    Returns:
        List of popular emoji with usage counts

    Raises:
        HTTPException 403: User not a participant
    """
    from app.messenger.reactions import get_reactions_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_reactions_service()
        popular = await service.get_popular_reactions(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
        )

        return {"conversation_id": str(conversation_id), "popular_reactions": popular}

    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/reactions/emoji")
async def get_supported_emoji():
    """
    Get list of all supported emoji shortcodes.

    Returns emoji shortcodes with their unicode representations.
    Useful for emoji pickers in frontend.

    Returns:
        List of emoji with shortcode and unicode
    """
    from app.messenger.reactions import get_reactions_service

    service = get_reactions_service()
    emoji_list = service.get_supported_emoji()

    return {"emoji": emoji_list, "count": len(emoji_list)}


# ============================================================================
# Call Endpoints
# ============================================================================


@router.post("/conversations/{conversation_id}/calls")
async def initiate_call(
    conversation_id: uuid.UUID,
    call_type: str = Query(..., regex="^(audio|video)$"),
    invited_user_ids: list[int] = Query([]),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Initiate a voice or video call in a conversation.

    Args:
        conversation_id: ID of the conversation
        call_type: Type of call ('audio' or 'video')
        invited_user_ids: List of user IDs to invite

    Returns:
        Call details including call_id

    Raises:
        HTTPException 403: User not a participant
        HTTPException 409: Active call already exists
    """
    from app.messenger.calls import CallType, get_call_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_call_service()

        call = await service.initiate_call(
            db=db,
            conversation_id=conversation_id,
            initiator_id=user_id,
            call_type=CallType(call_type),
            invited_user_ids=invited_user_ids,
        )

        # Get participants
        participants = await service.get_call_participants(db, call.id)

        return {
            "call_id": str(call.id),
            "conversation_id": str(call.conversation_id),
            "call_type": call.call_type,
            "status": call.status,
            "started_at": call.started_at.isoformat(),
            "initiator_id": call.initiator_id,
            "participants": [
                {
                    "user_id": p.user_id,
                    "is_initiator": p.is_initiator,
                    "answered": p.answered,
                }
                for p in participants
            ],
        }

    except ValueError as e:
        if "active call" in str(e).lower():
            raise HTTPException(
                status_code=status_lib.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status_lib.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/calls/{call_id}")
async def get_call(
    call_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get call details.

    Args:
        call_id: ID of the call

    Returns:
        Complete call details with participants

    Raises:
        HTTPException 404: Call not found
        HTTPException 403: User not a participant
    """
    from app.messenger.calls import get_call_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_call_service()

        call = await service.get_call(db, call_id, user_id)

        if not call:
            raise HTTPException(
                status_code=status_lib.HTTP_404_NOT_FOUND,
                detail="Call not found",
            )

        # Get participants
        participants = await service.get_call_participants(db, call_id)

        return {
            "call_id": str(call.id),
            "conversation_id": str(call.conversation_id),
            "call_type": call.call_type,
            "status": call.status,
            "started_at": call.started_at.isoformat(),
            "answered_at": call.answered_at.isoformat() if call.answered_at else None,
            "ended_at": call.ended_at.isoformat() if call.ended_at else None,
            "duration_seconds": call.duration_seconds,
            "end_reason": call.end_reason,
            "initiator_id": call.initiator_id,
            "participants": [
                {
                    "user_id": p.user_id,
                    "is_initiator": p.is_initiator,
                    "answered": p.answered,
                    "joined_at": p.joined_at.isoformat() if p.joined_at else None,
                    "left_at": p.left_at.isoformat() if p.left_at else None,
                    "duration_seconds": p.duration_seconds,
                    "video_enabled": p.video_enabled,
                    "audio_enabled": p.audio_enabled,
                    "screen_share_enabled": p.screen_share_enabled,
                    "connection_quality": p.connection_quality,
                }
                for p in participants
            ],
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post("/calls/{call_id}/answer")
async def answer_call(
    call_id: uuid.UUID,
    video_enabled: bool = Query(False),
    peer_id: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Answer a call invitation.

    Args:
        call_id: ID of the call
        video_enabled: Whether to enable video
        peer_id: WebRTC peer identifier

    Returns:
        Participant details

    Raises:
        HTTPException 404: Call not found
        HTTPException 400: Call not active or already answered
    """
    from app.messenger.calls import get_call_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_call_service()

        participant = await service.answer_call(
            db=db,
            call_id=call_id,
            user_id=user_id,
            video_enabled=video_enabled,
            peer_id=peer_id,
        )

        return {
            "call_id": str(call_id),
            "user_id": participant.user_id,
            "answered": participant.answered,
            "joined_at": (
                participant.joined_at.isoformat() if participant.joined_at else None
            ),
            "video_enabled": participant.video_enabled,
            "audio_enabled": participant.audio_enabled,
            "peer_id": participant.peer_id,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/calls/{call_id}/reject")
async def reject_call(
    call_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Reject a call invitation.

    Args:
        call_id: ID of the call

    Returns:
        Updated call status

    Raises:
        HTTPException 404: Call not found
        HTTPException 403: User not invited
    """
    from app.messenger.calls import get_call_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_call_service()

        call = await service.reject_call(
            db=db,
            call_id=call_id,
            user_id=user_id,
        )

        return {
            "call_id": str(call.id),
            "status": call.status,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post("/calls/{call_id}/end")
async def end_call(
    call_id: uuid.UUID,
    end_reason: str = Query(
        "completed", regex="^(completed|declined|no_answer|failed|timeout)$"
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    End an active call.

    Args:
        call_id: ID of the call
        end_reason: Reason for ending

    Returns:
        Final call details with duration

    Raises:
        HTTPException 404: Call not found
    """
    from app.messenger.calls import EndReason, get_call_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_call_service()

        call = await service.end_call(
            db=db,
            call_id=call_id,
            user_id=user_id,
            end_reason=EndReason(end_reason),
        )

        return {
            "call_id": str(call.id),
            "status": call.status,
            "ended_at": call.ended_at.isoformat() if call.ended_at else None,
            "duration_seconds": call.duration_seconds,
            "end_reason": call.end_reason,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/calls/{call_id}/leave", status_code=status_lib.HTTP_204_NO_CONTENT)
async def leave_call(
    call_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Leave a call (participant leaves but call continues).

    Args:
        call_id: ID of the call

    Returns:
        204 No Content

    Raises:
        HTTPException 404: Call not found or user not in call
    """
    from app.messenger.calls import get_call_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_call_service()

        await service.leave_call(
            db=db,
            call_id=call_id,
            user_id=user_id,
        )

        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch("/calls/{call_id}/media")
async def update_call_media(
    call_id: uuid.UUID,
    video_enabled: bool | None = Query(None),
    audio_enabled: bool | None = Query(None),
    screen_share_enabled: bool | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update participant's media settings.

    Args:
        call_id: ID of the call
        video_enabled: Enable/disable video
        audio_enabled: Enable/disable audio
        screen_share_enabled: Enable/disable screen sharing

    Returns:
        Updated participant media settings

    Raises:
        HTTPException 404: Call not found or user not in call
    """
    from app.messenger.calls import get_call_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_call_service()

        participant = await service.update_participant_media(
            db=db,
            call_id=call_id,
            user_id=user_id,
            video_enabled=video_enabled,
            audio_enabled=audio_enabled,
            screen_share_enabled=screen_share_enabled,
        )

        return {
            "call_id": str(call_id),
            "user_id": participant.user_id,
            "video_enabled": participant.video_enabled,
            "audio_enabled": participant.audio_enabled,
            "screen_share_enabled": participant.screen_share_enabled,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/conversations/{conversation_id}/calls/active")
async def get_active_call(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get the active call in a conversation (if any).

    Args:
        conversation_id: ID of the conversation

    Returns:
        Active call details or null

    Raises:
        HTTPException 403: User not a participant
    """
    from app.messenger.calls import get_call_service

    user_id = int(user.id)  # type: ignore
    service = get_call_service()

    call = await service.get_active_call(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    if not call:
        return {"active_call": None}

    # Get participants
    participants = await service.get_call_participants(db, call.id)

    return {
        "active_call": {
            "call_id": str(call.id),
            "call_type": call.call_type,
            "status": call.status,
            "started_at": call.started_at.isoformat(),
            "initiator_id": call.initiator_id,
            "participants": [
                {
                    "user_id": p.user_id,
                    "answered": p.answered,
                    "video_enabled": p.video_enabled,
                    "audio_enabled": p.audio_enabled,
                }
                for p in participants
            ],
        }
    }


@router.get("/conversations/{conversation_id}/calls/history")
async def get_call_history(
    conversation_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get call history for a conversation.

    Args:
        conversation_id: ID of the conversation
        limit: Maximum number of calls to return
        offset: Offset for pagination

    Returns:
        List of past calls

    Raises:
        HTTPException 403: User not a participant
    """
    from app.messenger.calls import get_call_service

    try:
        user_id = int(user.id)  # type: ignore
        service = get_call_service()

        calls = await service.get_call_history(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        return {
            "conversation_id": str(conversation_id),
            "calls": [
                {
                    "call_id": str(call.id),
                    "call_type": call.call_type,
                    "status": call.status,
                    "started_at": call.started_at.isoformat(),
                    "ended_at": call.ended_at.isoformat() if call.ended_at else None,
                    "duration_seconds": call.duration_seconds,
                    "initiator_id": call.initiator_id,
                }
                for call in calls
            ],
            "limit": limit,
            "offset": offset,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


# ============================================================================
# Participant Management Endpoints
# ============================================================================


@router.post(
    "/conversations/{conversation_id}/participants",
    status_code=status_lib.HTTP_204_NO_CONTENT,
)
async def add_participants(
    conversation_id: uuid.UUID,
    data: ParticipantAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Add participants to a conversation (admin only).

    Only conversation admins can add new participants.
    Direct messages cannot have participants added.
    """
    # Verify user is a participant and get conversation
    conversation = await get_conversation_or_404(conversation_id, user, db)

    # Verify user is admin
    if not await is_conversation_admin(conversation_id, user, db):
        raise HTTPException(
            status_code=status_lib.HTTP_403_FORBIDDEN,
            detail="Only conversation admins can add participants",
        )

    # Verify not a direct message
    if conversation.type == "direct":
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail="Cannot add participants to direct messages",
        )

    # Add participants (skip if already exists)
    for user_id in data.user_ids:
        # Check if already a participant
        check_stmt = select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
        )
        result = await db.execute(check_stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            participant = ConversationParticipant(
                conversation_id=conversation_id,
                user_id=user_id,
                role=data.role,
            )
            db.add(participant)

    await db.commit()

    # TODO: Send notification to new participants

    return None


@router.delete(
    "/conversations/{conversation_id}/participants/{participant_user_id}",
    status_code=status_lib.HTTP_204_NO_CONTENT,
)
async def remove_participant(
    conversation_id: uuid.UUID,
    participant_user_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Remove a participant from a conversation (admin only).

    Only conversation admins can remove participants.
    Cannot remove the last admin.
    """
    # Verify user is admin
    if not await is_conversation_admin(conversation_id, user, db):
        raise HTTPException(
            status_code=status_lib.HTTP_403_FORBIDDEN,
            detail="Only conversation admins can remove participants",
        )

    # Check if target is the last admin
    admin_count_stmt = (
        select(func.count())
        .select_from(ConversationParticipant)
        .where(
            and_(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.role == "admin",
            )
        )
    )
    result = await db.execute(admin_count_stmt)
    admin_count = result.scalar_one()

    # Check if target is an admin
    target_stmt = select(ConversationParticipant).where(
        and_(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == participant_user_id,
        )
    )
    result = await db.execute(target_stmt)
    target_participant = result.scalar_one_or_none()

    if not target_participant:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )

    if target_participant.role == "admin" and admin_count <= 1:
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last admin",
        )

    # Remove participant
    stmt = delete(ConversationParticipant).where(
        and_(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == participant_user_id,
        )
    )
    await db.execute(stmt)
    await db.commit()

    # TODO: Send notification to removed participant

    return None


# ============================================================================
# Notification Settings Endpoints
# ============================================================================


@router.get(
    "/conversations/{conversation_id}/settings",
    response_model=NotificationSettingsResponse,
)
async def get_notification_settings(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Get notification settings for a conversation"""
    # Verify user is a participant
    await get_conversation_or_404(conversation_id, user, db)

    # Fetch or create default settings
    stmt = select(NotificationSetting).where(
        and_(
            NotificationSetting.user_id == user.id,
            NotificationSetting.conversation_id == conversation_id,
        )
    )
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = NotificationSetting(
            user_id=user.id,
            conversation_id=conversation_id,
            muted=False,
            push_enabled=True,
            email_enabled=True,
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return NotificationSettingsResponse.model_validate(settings)


@router.put(
    "/conversations/{conversation_id}/settings",
    response_model=NotificationSettingsResponse,
)
async def update_notification_settings(
    conversation_id: uuid.UUID,
    data: NotificationSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Update notification settings for a conversation"""
    # Verify user is a participant
    await get_conversation_or_404(conversation_id, user, db)

    # Fetch or create settings
    stmt = select(NotificationSetting).where(
        and_(
            NotificationSetting.user_id == user.id,
            NotificationSetting.conversation_id == conversation_id,
        )
    )
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()

    if not settings:
        settings = NotificationSetting(
            user_id=user.id,
            conversation_id=conversation_id,
        )
        db.add(settings)

    # Update fields
    if data.muted is not None:
        settings.muted = data.muted
    if data.push_enabled is not None:
        settings.push_enabled = data.push_enabled
    if data.email_enabled is not None:
        settings.email_enabled = data.email_enabled

    await db.commit()
    await db.refresh(settings)

    return NotificationSettingsResponse.model_validate(settings)


# ============================================================================
# Presence API Endpoints
# ============================================================================


@router.get("/presence/online")
async def get_online_users_api(
    zone_id: Optional[int] = Query(None, description="Filter by zone ID"),
    org_id: Optional[int] = Query(None, description="Filter by organization ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum users to return"),
    user: User = Depends(get_current_user),
):
    """
    Get list of currently online users.

    Filters:
    - zone_id: Show only users in specific zone
    - org_id: Show only users in specific organization
    - limit: Maximum number of users to return (default 100)

    Returns users sorted by last activity (most recent first).
    """
    from app.messenger.presence import get_presence_manager

    presence = get_presence_manager()
    online_users = await presence.get_online_users(
        zone_id=zone_id,
        org_id=org_id,
        limit=limit,
    )

    return {"online_users": online_users, "count": len(online_users)}


@router.get("/presence/count")
async def get_online_count_api(
    zone_id: Optional[int] = Query(None, description="Filter by zone ID"),
    org_id: Optional[int] = Query(None, description="Filter by organization ID"),
    user: User = Depends(get_current_user),
):
    """
    Get count of online users.

    Filters:
    - zone_id: Count only users in specific zone
    - org_id: Count only users in specific organization

    Returns aggregate counts for global, zone, and org levels.
    """
    from app.messenger.presence import get_presence_manager

    presence = get_presence_manager()
    counts = await presence.get_online_count(zone_id=zone_id, org_id=org_id)

    return counts


@router.get("/presence/status/{user_id}")
async def get_user_presence_status(
    user_id: int,
    user: User = Depends(get_current_user),
):
    """
    Get presence status for a specific user.

    Returns:
    - status: "online", "away", or "offline"
    - last_activity: ISO timestamp of last activity
    - last_seen: ISO timestamp when user went offline (if offline)
    - zone_id, org_id: User's current zone/org context
    """
    from app.messenger.presence import get_presence_manager

    presence = get_presence_manager()
    status = await presence.get_status(user_id)

    if not status:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="User presence not found",
        )

    return status


@router.post("/presence/away")
async def set_user_away(
    user: User = Depends(get_current_user),
):
    """
    Manually set user status to 'away'.

    This allows users to explicitly set their status to away
    (in addition to automatic away detection after 5 minutes of inactivity).
    """
    from app.messenger.presence import get_presence_manager

    presence = get_presence_manager()
    user_id = int(user.id)  # type: ignore
    await presence.set_away(user_id)

    return {"status": "away", "user_id": user_id}


# ============================================================================
# File Upload API Endpoints
# ============================================================================


@router.post("/upload")
async def upload_file(
    file: UploadFile,
    conversation_id: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    """
    Upload file to messenger storage.

    Supports:
    - Images: jpg, png, gif, webp (max 10 MB)
    - Videos: mp4, mov, webm (max 100 MB)
    - Audio: mp3, wav, ogg (max 20 MB)
    - Documents: pdf, docx, xlsx, pptx (max 50 MB)

    Features:
    - Virus scanning (ClamAV)
    - Thumbnail generation (images/videos)
    - CDN URL generation

    Returns file metadata for use in messages.
    """
    from app.messenger.storage import (
        FileSizeError,
        FileTypeError,
        VirusScanError,
        get_file_storage,
    )

    try:
        storage = get_file_storage()

        # Upload file
        file_metadata = await storage.upload_file(
            file=file.file,
            filename=file.filename or "unnamed",
            user_id=int(user.id),  # type: ignore
            conversation_id=conversation_id,
            scan_virus=True,
            generate_thumb=True,
        )

        return file_metadata

    except FileSizeError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        )
    except FileTypeError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e),
        )
    except VirusScanError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status_lib.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed",
        )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete uploaded file.

    Only the uploader or conversation admin can delete files.

    Args:
        file_id: File UUID

    Returns:
        {"deleted": true}
    """
    from app.messenger.storage import get_file_storage

    try:
        # Find message with this file
        stmt = select(Message).where(Message.file_url.contains(file_id))
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status_lib.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        # Check permissions (sender or admin)
        user_id = int(user.id)  # type: ignore
        is_sender = message.sender_id == user_id

        stmt_participant = select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == message.conversation_id,
                ConversationParticipant.user_id == user_id,
            )
        )
        result_participant = await db.execute(stmt_participant)
        participant = result_participant.scalar_one_or_none()
        is_admin = participant and participant.role == "admin"

        if not (is_sender or is_admin):
            raise HTTPException(
                status_code=status_lib.HTTP_403_FORBIDDEN,
                detail="Only sender or admin can delete files",
            )

        # Delete from storage
        storage = get_file_storage()
        if message.file_url:
            await storage.delete_file(message.file_url)

        # Delete thumbnail if exists
        if message.file_url:
            # Assuming thumbnail URL pattern
            thumb_url = message.file_url.replace(file_id, f"{file_id}_thumb")
            await storage.delete_file(thumb_url)

        # Mark message as deleted (soft delete)
        message.deleted_at = func.now()
        await db.commit()

        return {"deleted": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion error: {e}")
        raise HTTPException(
            status_code=status_lib.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File deletion failed",
        )


# ============================================================================
# WebSocket Event Handlers
# ============================================================================


async def update_user_activity(user_id: int):
    """
    Update user's last activity timestamp in presence system.

    Called when user performs any WebSocket action (send message, edit, etc.)
    to keep presence status accurate and prevent auto-away.
    """
    from app.messenger.presence import get_presence_manager

    try:
        presence = get_presence_manager()
        await presence.update_activity(user_id)
    except Exception as e:
        logger.warning(f"Failed to update presence for user {user_id}: {e}")


async def handle_message_send(
    websocket: WebSocket,
    user_id: int,
    conversation_id: uuid.UUID,
    message_data: dict,
):
    """
    Handle message.send event from WebSocket.

    Creates message in DB and broadcasts to conversation participants.
    """
    try:
        # Get database session (create new one for this handler)
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            # Verify user is participant
            stmt = select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
            result = await db.execute(stmt)
            participant = result.scalar_one_or_none()

            if not participant:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Not a participant of this conversation",
                    }
                )
                return

            # Create message
            new_message = Message(
                conversation_id=conversation_id,
                sender_id=user_id,
                content=message_data.get("content", ""),
                message_type=message_data.get("message_type", "text"),
                file_url=message_data.get("file_url"),
                file_size=message_data.get("file_size"),
                file_name=message_data.get("file_name"),
            )

            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)

            # Update user activity in presence system
            await update_user_activity(user_id)

            # Prepare response
            message_response = MessageResponse.model_validate(new_message)

            # Broadcast to conversation via Redis Pub/Sub
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=conversation_id,
                message_data={
                    "type": "message.new",
                    "data": message_response.model_dump(mode="json"),
                },
            )

            # Send acknowledgment to sender
            await websocket.send_json(
                {
                    "type": "message.sent",
                    "message_id": str(new_message.id),
                    "data": message_response.model_dump(mode="json"),
                }
            )

            logger.info(f"Message sent via WebSocket: {new_message.id}")

            # Track analytics event
            from app.messenger.analytics import (
                AnalyticsEventType,
                get_analytics_service,
            )

            analytics = get_analytics_service()
            await analytics.track_event(
                event_type=AnalyticsEventType.MESSAGE_SENT,
                user_id=user_id,
                conversation_id=str(conversation_id),
                metadata={
                    "message_id": str(new_message.id),
                    "message_type": new_message.message_type,
                },
            )

            # Send push notifications to offline participants (async)
            asyncio.create_task(
                send_push_notifications_for_message(
                    db_session=AsyncSessionLocal,
                    conversation_id=conversation_id,
                    sender_id=user_id,
                    message_content=message_data.get("content", ""),
                    message_id=new_message.id,
                )
            )

    except Exception as e:
        logger.error(f"Error in handle_message_send: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"Failed to send message: {str(e)}"}
        )


async def handle_message_reply(
    websocket: WebSocket,
    user_id: int,
    conversation_id: Optional[uuid.UUID],
    parent_message_id: uuid.UUID,
    message_data: dict,
):
    """
    Handle message.reply event from WebSocket.

    Creates a threaded reply to an existing message.
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.threading import get_threading_service

        async with AsyncSessionLocal() as db:
            # Get parent message to determine conversation_id if not provided
            if not conversation_id:
                parent_result = await db.execute(
                    select(Message.conversation_id).where(
                        Message.id == parent_message_id
                    )
                )
                conversation_id = parent_result.scalar_one_or_none()

                if not conversation_id:
                    await websocket.send_json(
                        {"type": "error", "message": "Parent message not found"}
                    )
                    return

            threading_service = get_threading_service()

            # Create reply using threading service
            reply = await threading_service.create_reply(
                db=db,
                conversation_id=conversation_id,
                parent_message_id=parent_message_id,
                sender_id=user_id,
                content=message_data.get("content"),
                message_type=message_data.get("message_type", "text"),
                file_url=message_data.get("file_url"),
                file_size=message_data.get("file_size"),
                file_name=message_data.get("file_name"),
            )

            # Update user activity
            await update_user_activity(user_id)

            # Prepare response
            message_response = MessageResponse.model_validate(reply)

            # Broadcast to conversation via Redis Pub/Sub
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=conversation_id,
                message_data={
                    "type": "message.reply",
                    "data": message_response.model_dump(mode="json"),
                    "parent_id": str(parent_message_id),
                    "thread_id": str(reply.thread_id),
                },
            )

            # Send acknowledgment to sender
            await websocket.send_json(
                {
                    "type": "message.replied",
                    "message_id": str(reply.id),
                    "parent_id": str(parent_message_id),
                    "thread_id": str(reply.thread_id),
                    "data": message_response.model_dump(mode="json"),
                }
            )

            logger.info(
                f"Reply created via WebSocket: {reply.id} "
                f"(parent: {parent_message_id}, thread: {reply.thread_id})"
            )

            # Track analytics event
            from app.messenger.analytics import (
                AnalyticsEventType,
                get_analytics_service,
            )

            analytics = get_analytics_service()
            await analytics.track_event(
                event_type=AnalyticsEventType.MESSAGE_SENT,
                user_id=user_id,
                conversation_id=str(conversation_id),
                metadata={
                    "message_id": str(reply.id),
                    "message_type": reply.message_type,
                    "parent_id": str(parent_message_id),
                    "thread_id": str(reply.thread_id),
                    "is_reply": True,
                },
            )

            # Send push notifications to thread participants (async)
            asyncio.create_task(
                send_push_notifications_for_message(
                    db_session=AsyncSessionLocal,
                    conversation_id=conversation_id,
                    sender_id=user_id,
                    message_content=message_data.get("content", ""),
                    message_id=reply.id,
                )
            )

    except ValueError as e:
        logger.error(f"Error in handle_message_reply: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})
    except Exception as e:
        logger.error(f"Error in handle_message_reply: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"Failed to create reply: {str(e)}"}
        )


async def handle_message_edit(
    websocket: WebSocket,
    user_id: int,
    message_id: uuid.UUID,
    message_data: dict,
):
    """
    Handle message.edit event from WebSocket.

    Updates message content and broadcasts update.
    """
    try:
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            # Fetch message
            stmt = select(Message).where(Message.id == message_id)
            result = await db.execute(stmt)
            msg = result.scalar_one_or_none()

            if not msg:
                await websocket.send_json(
                    {"type": "error", "message": "Message not found"}
                )
                return

            # Verify sender
            if msg.sender_id != user_id:
                await websocket.send_json(
                    {"type": "error", "message": "Only sender can edit message"}
                )
                return

            # Update content
            new_content = message_data.get("content")
            if new_content:
                msg.content = new_content
                msg.edited_at = func.now()

                await db.commit()
                await db.refresh(msg)

                # Update user activity in presence system
                await update_user_activity(user_id)

                # Broadcast update
                message_response = MessageResponse.model_validate(msg)
                pubsub = get_pubsub()
                await pubsub.publish_message(
                    conversation_id=msg.conversation_id,
                    message_data={
                        "type": "message.edited",
                        "data": message_response.model_dump(mode="json"),
                    },
                )

                # Send acknowledgment
                await websocket.send_json(
                    {
                        "type": "message.edited",
                        "message_id": str(message_id),
                        "data": message_response.model_dump(mode="json"),
                    }
                )

                logger.info(f"Message edited via WebSocket: {message_id}")

                # Track analytics event
                from app.messenger.analytics import (
                    AnalyticsEventType,
                    get_analytics_service,
                )

                analytics = get_analytics_service()
                await analytics.track_event(
                    event_type=AnalyticsEventType.MESSAGE_EDITED,
                    user_id=user_id,
                    conversation_id=str(msg.conversation_id),
                    metadata={"message_id": str(message_id)},
                )

    except Exception as e:
        logger.error(f"Error in handle_message_edit: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"Failed to edit message: {str(e)}"}
        )


async def handle_message_delete(
    websocket: WebSocket,
    user_id: int,
    message_id: uuid.UUID,
):
    """
    Handle message.delete event from WebSocket.

    Soft deletes message and broadcasts deletion.
    """
    try:
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            # Fetch message
            stmt = select(Message).where(Message.id == message_id)
            result = await db.execute(stmt)
            msg = result.scalar_one_or_none()

            if not msg:
                await websocket.send_json(
                    {"type": "error", "message": "Message not found"}
                )
                return

            # Verify sender or admin
            stmt_participant = select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == msg.conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
            result_participant = await db.execute(stmt_participant)
            participant = result_participant.scalar_one_or_none()

            is_admin = participant and participant.role == "admin"
            is_sender = msg.sender_id == user_id

            if not (is_sender or is_admin):
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Only sender or admin can delete message",
                    }
                )
                return

            # Soft delete
            msg.deleted_at = func.now()
            await db.commit()

            # Update user activity in presence system
            await update_user_activity(user_id)

            # Broadcast deletion
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=msg.conversation_id,
                message_data={
                    "type": "message.deleted",
                    "message_id": str(message_id),
                    "conversation_id": str(msg.conversation_id),
                },
            )

            # Send acknowledgment
            await websocket.send_json(
                {"type": "message.deleted", "message_id": str(message_id)}
            )

            logger.info(f"Message deleted via WebSocket: {message_id}")

            # Track analytics event
            from app.messenger.analytics import (
                AnalyticsEventType,
                get_analytics_service,
            )

            analytics = get_analytics_service()
            await analytics.track_event(
                event_type=AnalyticsEventType.MESSAGE_DELETED,
                user_id=user_id,
                conversation_id=str(msg.conversation_id),
                metadata={"message_id": str(message_id)},
            )

    except Exception as e:
        logger.error(f"Error in handle_message_delete: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"Failed to delete message: {str(e)}"}
        )


async def handle_read_receipt(
    websocket: WebSocket,
    user_id: int,
    message_id: uuid.UUID,
):
    """
    Handle message.read event from WebSocket.

    Creates read receipt and updates last_read_at.
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.messenger_models import ReadReceipt

        async with AsyncSessionLocal() as db:
            # Fetch message
            stmt = select(Message).where(Message.id == message_id)
            result = await db.execute(stmt)
            msg = result.scalar_one_or_none()

            if not msg:
                await websocket.send_json(
                    {"type": "error", "message": "Message not found"}
                )
                return

            # Verify participant
            stmt_participant = select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == msg.conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
            result_participant = await db.execute(stmt_participant)
            participant = result_participant.scalar_one_or_none()

            if not participant:
                await websocket.send_json(
                    {"type": "error", "message": "Not a participant"}
                )
                return

            # Create or update read receipt
            stmt_receipt = select(ReadReceipt).where(
                and_(
                    ReadReceipt.message_id == message_id,
                    ReadReceipt.user_id == user_id,
                )
            )
            result_receipt = await db.execute(stmt_receipt)
            receipt = result_receipt.scalar_one_or_none()

            if not receipt:
                receipt = ReadReceipt(
                    message_id=message_id,
                    user_id=user_id,
                    conversation_id=msg.conversation_id,
                )
                db.add(receipt)

            # Update last_read_at in participant
            participant.last_read_at = func.now()

            await db.commit()

            # Update user activity in presence system
            await update_user_activity(user_id)

            # Broadcast read receipt (optional - for read indicators)
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=msg.conversation_id,
                message_data={
                    "type": "message.read",
                    "message_id": str(message_id),
                    "user_id": user_id,
                    "conversation_id": str(msg.conversation_id),
                },
            )

            # Send acknowledgment
            await websocket.send_json(
                {"type": "read.confirmed", "message_id": str(message_id)}
            )

            logger.info(
                f"Read receipt created via WebSocket: message={message_id}, user={user_id}"
            )

            # Track analytics event
            from app.messenger.analytics import (
                AnalyticsEventType,
                get_analytics_service,
            )

            analytics = get_analytics_service()
            await analytics.track_event(
                event_type=AnalyticsEventType.MESSAGE_READ,
                user_id=user_id,
                conversation_id=str(msg.conversation_id),
                metadata={"message_id": str(message_id)},
            )

    except Exception as e:
        logger.error(f"Error in handle_read_receipt: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"Failed to create read receipt: {str(e)}"}
        )


async def handle_reaction_add(
    websocket: WebSocket,
    user_id: int,
    message_id: uuid.UUID,
    emoji: str,
):
    """
    Handle reaction.add event from WebSocket.

    Add emoji reaction to a message and broadcast to conversation.
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.reactions import get_reactions_service

        async with AsyncSessionLocal() as db:
            # Add reaction
            service = get_reactions_service()
            reaction = await service.add_reaction(
                db=db,
                message_id=message_id,
                user_id=user_id,
                emoji=emoji,
            )

            # Get conversation_id for broadcasting
            stmt = select(Message.conversation_id).where(Message.id == message_id)
            result = await db.execute(stmt)
            conversation_id = result.scalar_one_or_none()

            if not conversation_id:
                await websocket.send_json(
                    {"type": "error", "message": "Message not found"}
                )
                return

            # Update user activity
            await update_user_activity(user_id)

            # Broadcast via Redis Pub/Sub
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=conversation_id,
                message_data={
                    "type": "reaction.added",
                    "message_id": str(message_id),
                    "user_id": user_id,
                    "emoji": emoji,
                    "emoji_unicode": reaction.emoji_unicode,
                    "reaction_id": reaction.id,
                    "timestamp": reaction.created_at.isoformat(),
                },
            )

            # Send acknowledgment
            await websocket.send_json(
                {
                    "type": "reaction.confirmed",
                    "action": "added",
                    "reaction": {
                        "id": reaction.id,
                        "message_id": str(message_id),
                        "emoji": emoji,
                        "emoji_unicode": reaction.emoji_unicode,
                    },
                }
            )

            logger.info(
                f"Reaction added via WebSocket: emoji={emoji}, message={message_id}, user={user_id}"
            )

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        logger.warning(f"Reaction add failed: {e}")
    except Exception as e:
        logger.error(f"Error in handle_reaction_add: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"Failed to add reaction: {str(e)}"}
        )


async def handle_reaction_remove(
    websocket: WebSocket,
    user_id: int,
    message_id: uuid.UUID,
    emoji: str,
):
    """
    Handle reaction.remove event from WebSocket.

    Remove emoji reaction from a message and broadcast to conversation.
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.reactions import get_reactions_service

        async with AsyncSessionLocal() as db:
            # Get conversation_id before removing
            stmt = select(Message.conversation_id).where(Message.id == message_id)
            result = await db.execute(stmt)
            conversation_id = result.scalar_one_or_none()

            if not conversation_id:
                await websocket.send_json(
                    {"type": "error", "message": "Message not found"}
                )
                return

            # Remove reaction
            service = get_reactions_service()
            removed = await service.remove_reaction(
                db=db,
                message_id=message_id,
                user_id=user_id,
                emoji=emoji,
            )

            if not removed:
                await websocket.send_json(
                    {"type": "error", "message": "Reaction not found"}
                )
                return

            # Update user activity
            await update_user_activity(user_id)

            # Broadcast via Redis Pub/Sub
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=conversation_id,
                message_data={
                    "type": "reaction.removed",
                    "message_id": str(message_id),
                    "user_id": user_id,
                    "emoji": emoji,
                    "timestamp": func.now().isoformat(),
                },
            )

            # Send acknowledgment
            await websocket.send_json(
                {
                    "type": "reaction.confirmed",
                    "action": "removed",
                    "message_id": str(message_id),
                    "emoji": emoji,
                }
            )

            logger.info(
                f"Reaction removed via WebSocket: emoji={emoji}, message={message_id}, user={user_id}"
            )

    except Exception as e:
        logger.error(f"Error in handle_reaction_remove: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"Failed to remove reaction: {str(e)}"}
        )


async def handle_reaction_toggle(
    websocket: WebSocket,
    user_id: int,
    message_id: uuid.UUID,
    emoji: str,
):
    """
    Handle reaction.toggle event from WebSocket.

    Toggle emoji reaction (add if not exists, remove if exists).
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.reactions import get_reactions_service

        async with AsyncSessionLocal() as db:
            # Toggle reaction
            service = get_reactions_service()
            result = await service.toggle_reaction(
                db=db,
                message_id=message_id,
                user_id=user_id,
                emoji=emoji,
            )

            # Get conversation_id for broadcasting
            stmt = select(Message.conversation_id).where(Message.id == message_id)
            result_conv = await db.execute(stmt)
            conversation_id = result_conv.scalar_one_or_none()

            if not conversation_id:
                await websocket.send_json(
                    {"type": "error", "message": "Message not found"}
                )
                return

            # Update user activity
            await update_user_activity(user_id)

            # Broadcast via Redis Pub/Sub
            pubsub = get_pubsub()
            event_type = (
                "reaction.added" if result["action"] == "added" else "reaction.removed"
            )

            message_data = {
                "type": event_type,
                "message_id": str(message_id),
                "user_id": user_id,
                "emoji": emoji,
            }

            if result["action"] == "added":
                message_data["emoji_unicode"] = result.get("emoji_unicode")
                message_data["reaction_id"] = result.get("reaction_id")

            await pubsub.publish_message(
                conversation_id=conversation_id,
                message_data=message_data,
            )

            # Send acknowledgment
            await websocket.send_json(
                {
                    "type": "reaction.confirmed",
                    "action": result["action"],
                    "message_id": str(message_id),
                    "emoji": emoji,
                }
            )

            logger.info(
                f"Reaction toggled via WebSocket: action={result['action']}, emoji={emoji}, message={message_id}, user={user_id}"
            )

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        logger.warning(f"Reaction toggle failed: {e}")
    except Exception as e:
        logger.error(f"Error in handle_reaction_toggle: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"Failed to toggle reaction: {str(e)}"}
        )


# ============================================================================
# Call & WebRTC Event Handlers
# ============================================================================


async def handle_call_initiate(
    websocket: WebSocket,
    user_id: int,
    conversation_id: uuid.UUID,
    message: dict,
):
    """Handle call.initiate event from WebSocket."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.calls import CallType, get_call_service

        call_type = message.get("call_type", "audio")
        invited_user_ids = message.get("invited_user_ids", [])

        async with AsyncSessionLocal() as db:
            service = get_call_service()
            call = await service.initiate_call(
                db=db,
                conversation_id=conversation_id,
                initiator_id=user_id,
                call_type=CallType(call_type),
                invited_user_ids=invited_user_ids,
            )

            # Broadcast via Redis Pub/Sub
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=conversation_id,
                message_data={
                    "type": "call.initiated",
                    "call_id": str(call.id),
                    "call_type": call.call_type,
                    "initiator_id": user_id,
                    "invited_user_ids": invited_user_ids,
                    "timestamp": call.started_at.isoformat(),
                },
            )

            # Send confirmation
            await websocket.send_json(
                {
                    "type": "call.initiated",
                    "call_id": str(call.id),
                    "call_type": call.call_type,
                    "status": call.status,
                }
            )

            logger.info(f"Call initiated: {call.id}, type={call_type}")

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    except Exception as e:
        logger.error(f"Error in handle_call_initiate: {e}")
        await websocket.send_json(
            {"type": "error", "message": "Failed to initiate call"}
        )


async def handle_call_answer(
    websocket: WebSocket,
    user_id: int,
    call_id: uuid.UUID,
    message: dict,
):
    """Handle call.answer event from WebSocket."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.calls import get_call_service

        video_enabled = message.get("video_enabled", False)
        peer_id = message.get("peer_id")

        async with AsyncSessionLocal() as db:
            service = get_call_service()
            participant = await service.answer_call(
                db=db,
                call_id=call_id,
                user_id=user_id,
                video_enabled=video_enabled,
                peer_id=peer_id,
            )

            # Get call details for broadcasting
            call = await service.get_call(db, call_id, user_id)

            if not call:
                await websocket.send_json(
                    {"type": "error", "message": "Call not found"}
                )
                return

            # Broadcast via Redis Pub/Sub
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=call.conversation_id,
                message_data={
                    "type": "call.answered",
                    "call_id": str(call_id),
                    "user_id": user_id,
                    "video_enabled": video_enabled,
                    "peer_id": peer_id,
                    "timestamp": (
                        participant.joined_at.isoformat()
                        if participant.joined_at
                        else None
                    ),
                },
            )

            # Send confirmation
            await websocket.send_json(
                {
                    "type": "call.answered",
                    "call_id": str(call_id),
                    "peer_id": peer_id,
                }
            )

            logger.info(f"Call answered: {call_id}, user={user_id}")

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    except Exception as e:
        logger.error(f"Error in handle_call_answer: {e}")
        await websocket.send_json({"type": "error", "message": "Failed to answer call"})


async def handle_call_reject(
    websocket: WebSocket,
    user_id: int,
    call_id: uuid.UUID,
):
    """Handle call.reject event from WebSocket."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.calls import get_call_service

        async with AsyncSessionLocal() as db:
            service = get_call_service()
            call = await service.reject_call(
                db=db,
                call_id=call_id,
                user_id=user_id,
            )

            # Broadcast via Redis Pub/Sub
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=call.conversation_id,
                message_data={
                    "type": "call.rejected",
                    "call_id": str(call_id),
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Send confirmation
            await websocket.send_json(
                {
                    "type": "call.rejected",
                    "call_id": str(call_id),
                }
            )

            logger.info(f"Call rejected: {call_id}, user={user_id}")

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    except Exception as e:
        logger.error(f"Error in handle_call_reject: {e}")
        await websocket.send_json({"type": "error", "message": "Failed to reject call"})


async def handle_call_end(
    websocket: WebSocket,
    user_id: int,
    call_id: uuid.UUID,
    end_reason: str,
):
    """Handle call.end event from WebSocket."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.calls import EndReason, get_call_service

        async with AsyncSessionLocal() as db:
            service = get_call_service()
            call = await service.end_call(
                db=db,
                call_id=call_id,
                user_id=user_id,
                end_reason=EndReason(end_reason),
            )

            # Broadcast via Redis Pub/Sub
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=call.conversation_id,
                message_data={
                    "type": "call.ended",
                    "call_id": str(call_id),
                    "end_reason": call.end_reason,
                    "duration_seconds": call.duration_seconds,
                    "timestamp": call.ended_at.isoformat() if call.ended_at else None,
                },
            )

            # Send confirmation
            await websocket.send_json(
                {
                    "type": "call.ended",
                    "call_id": str(call_id),
                    "duration_seconds": call.duration_seconds,
                }
            )

            logger.info(f"Call ended: {call_id}, reason={end_reason}")

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    except Exception as e:
        logger.error(f"Error in handle_call_end: {e}")
        await websocket.send_json({"type": "error", "message": "Failed to end call"})


async def handle_call_leave(
    websocket: WebSocket,
    user_id: int,
    call_id: uuid.UUID,
):
    """Handle call.leave event from WebSocket."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.calls import get_call_service

        async with AsyncSessionLocal() as db:
            service = get_call_service()
            call = await service.get_call(db, call_id, user_id)

            if not call:
                await websocket.send_json(
                    {"type": "error", "message": "Call not found"}
                )
                return

            participant = await service.leave_call(
                db=db,
                call_id=call_id,
                user_id=user_id,
            )

            # Broadcast via Redis Pub/Sub
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=call.conversation_id,
                message_data={
                    "type": "call.participant_left",
                    "call_id": str(call_id),
                    "user_id": user_id,
                    "timestamp": (
                        participant.left_at.isoformat() if participant.left_at else None
                    ),
                },
            )

            # Send confirmation
            await websocket.send_json(
                {
                    "type": "call.left",
                    "call_id": str(call_id),
                }
            )

            logger.info(f"Participant left call: {call_id}, user={user_id}")

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    except Exception as e:
        logger.error(f"Error in handle_call_leave: {e}")
        await websocket.send_json({"type": "error", "message": "Failed to leave call"})


async def handle_call_media_update(
    websocket: WebSocket,
    user_id: int,
    call_id: uuid.UUID,
    message: dict,
):
    """Handle call.media event from WebSocket."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.calls import get_call_service

        video_enabled = message.get("video_enabled")
        audio_enabled = message.get("audio_enabled")
        screen_share_enabled = message.get("screen_share_enabled")

        async with AsyncSessionLocal() as db:
            service = get_call_service()
            call = await service.get_call(db, call_id, user_id)

            if not call:
                await websocket.send_json(
                    {"type": "error", "message": "Call not found"}
                )
                return

            participant = await service.update_participant_media(
                db=db,
                call_id=call_id,
                user_id=user_id,
                video_enabled=video_enabled,
                audio_enabled=audio_enabled,
                screen_share_enabled=screen_share_enabled,
            )

            # Broadcast via Redis Pub/Sub
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=call.conversation_id,
                message_data={
                    "type": "call.media_updated",
                    "call_id": str(call_id),
                    "user_id": user_id,
                    "video_enabled": participant.video_enabled,
                    "audio_enabled": participant.audio_enabled,
                    "screen_share_enabled": participant.screen_share_enabled,
                },
            )

            # Send confirmation
            await websocket.send_json(
                {
                    "type": "call.media_updated",
                    "call_id": str(call_id),
                }
            )

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    except Exception as e:
        logger.error(f"Error in handle_call_media_update: {e}")
        await websocket.send_json(
            {"type": "error", "message": "Failed to update media"}
        )


async def handle_webrtc_offer(
    websocket: WebSocket,
    user_id: int,
    call_id: uuid.UUID,
    message: dict,
):
    """Handle webrtc.offer event from WebSocket."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.calls import get_call_service

        target_user_id = message.get("target_user_id")
        sdp = message.get("sdp")

        if not target_user_id or not sdp:
            await websocket.send_json(
                {"type": "error", "message": "Missing target_user_id or sdp"}
            )
            return

        async with AsyncSessionLocal() as db:
            service = get_call_service()
            call = await service.get_call(db, call_id, user_id)

            if not call:
                await websocket.send_json(
                    {"type": "error", "message": "Call not found"}
                )
                return

            # Broadcast offer via Redis Pub/Sub to target user
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=call.conversation_id,
                message_data={
                    "type": "webrtc.offer",
                    "call_id": str(call_id),
                    "from_user_id": user_id,
                    "target_user_id": target_user_id,
                    "sdp": sdp,
                },
            )

            logger.info(
                f"WebRTC offer sent: {call_id}, from={user_id}, to={target_user_id}"
            )

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    except Exception as e:
        logger.error(f"Error in handle_webrtc_offer: {e}")
        await websocket.send_json({"type": "error", "message": "Failed to send offer"})


async def handle_webrtc_answer(
    websocket: WebSocket,
    user_id: int,
    call_id: uuid.UUID,
    message: dict,
):
    """Handle webrtc.answer event from WebSocket."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.calls import get_call_service

        target_user_id = message.get("target_user_id")
        sdp = message.get("sdp")

        if not target_user_id or not sdp:
            await websocket.send_json(
                {"type": "error", "message": "Missing target_user_id or sdp"}
            )
            return

        async with AsyncSessionLocal() as db:
            service = get_call_service()
            call = await service.get_call(db, call_id, user_id)

            if not call:
                await websocket.send_json(
                    {"type": "error", "message": "Call not found"}
                )
                return

            # Broadcast answer via Redis Pub/Sub to target user
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=call.conversation_id,
                message_data={
                    "type": "webrtc.answer",
                    "call_id": str(call_id),
                    "from_user_id": user_id,
                    "target_user_id": target_user_id,
                    "sdp": sdp,
                },
            )

            logger.info(
                f"WebRTC answer sent: {call_id}, from={user_id}, to={target_user_id}"
            )

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    except Exception as e:
        logger.error(f"Error in handle_webrtc_answer: {e}")
        await websocket.send_json({"type": "error", "message": "Failed to send answer"})


async def handle_webrtc_ice_candidate(
    websocket: WebSocket,
    user_id: int,
    call_id: uuid.UUID,
    message: dict,
):
    """Handle webrtc.ice_candidate event from WebSocket."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.messenger.calls import get_call_service

        target_user_id = message.get("target_user_id")
        candidate = message.get("candidate")

        if not target_user_id or not candidate:
            await websocket.send_json(
                {"type": "error", "message": "Missing target_user_id or candidate"}
            )
            return

        async with AsyncSessionLocal() as db:
            service = get_call_service()
            call = await service.get_call(db, call_id, user_id)

            if not call:
                await websocket.send_json(
                    {"type": "error", "message": "Call not found"}
                )
                return

            # Broadcast ICE candidate via Redis Pub/Sub to target user
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=call.conversation_id,
                message_data={
                    "type": "webrtc.ice_candidate",
                    "call_id": str(call_id),
                    "from_user_id": user_id,
                    "target_user_id": target_user_id,
                    "candidate": candidate,
                },
            )

    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    except Exception as e:
        logger.error(f"Error in handle_webrtc_ice_candidate: {e}")
        await websocket.send_json(
            {"type": "error", "message": "Failed to send ICE candidate"}
        )


async def send_push_notifications_for_message(
    db_session,
    conversation_id: uuid.UUID,
    sender_id: int,
    message_content: str,
    message_id: uuid.UUID,
):
    """
    Send push notifications to offline participants in a conversation.

    This runs as a background task and doesn't block the WebSocket handler.

    Args:
        db_session: AsyncSessionLocal class (not instance)
        conversation_id: Conversation UUID
        sender_id: User who sent the message
        message_content: Message text content
        message_id: Message UUID
    """
    try:
        from app.messenger.push_notifications import get_push_service
        from app.messenger.presence import get_presence_manager

        async with db_session() as db:
            # Get all participants except sender
            stmt = select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id != sender_id,
                )
            )
            result = await db.execute(stmt)
            participants = result.scalars().all()

            # Get sender info for notification
            sender_stmt = select(User).where(User.id == sender_id)
            sender_result = await db.execute(sender_stmt)
            sender = sender_result.scalar_one_or_none()
            sender_name = sender.username if sender else f"User {sender_id}"

            # Get conversation title
            conv_stmt = select(Conversation).where(Conversation.id == conversation_id)
            conv_result = await db.execute(conv_stmt)
            conversation = conv_result.scalar_one_or_none()
            conv_title = (
                conversation.title
                if conversation and conversation.title
                else "New message"
            )

            presence_manager = get_presence_manager()
            push_service = get_push_service()

            # Send push to each offline participant
            for participant in participants:
                try:
                    # Check if user is online
                    status = await presence_manager.get_status(participant.user_id)

                    # Only send push if user is offline
                    is_online = status and status.get("status") == "online"
                    if not is_online:
                        # Prepare notification
                        title = f"{sender_name} • {conv_title}"
                        body = message_content[:100]  # Truncate to 100 chars

                        # Send push notification
                        await push_service.send_push_notification(
                            db=db,
                            user_id=participant.user_id,
                            title=title,
                            body=body,
                            data={
                                "conversation_id": str(conversation_id),
                                "message_id": str(message_id),
                                "sender_id": sender_id,
                                "type": "message.new",
                            },
                            conversation_id=str(conversation_id),
                        )

                        logger.info(
                            f"Push notification sent: user={participant.user_id}, conv={conversation_id}"
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to send push to user {participant.user_id}: {e}"
                    )

    except Exception as e:
        logger.error(f"Error in send_push_notifications_for_message: {e}")


# ============================================================================
# WebSocket Endpoint
# ============================================================================
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    zone_id: Optional[int] = None,
    org_id: Optional[int] = None,
):
    """
    WebSocket endpoint for real-time messaging.

    Flow:
    1. Client connects with user_id, zone_id, org_id (query params)
    2. Server accepts connection and sets user online in presence system
    3. Server subscribes to user's conversations via Redis Pub/Sub
    4. Bidirectional message flow:
       - Client -> Server: JSON messages (type, conversation_id, content)
       - Server -> Client: Broadcasts from Redis Pub/Sub
    5. On disconnect: Cleanup and set user offline in presence system

    Query Parameters:
        - zone_id: Optional zone ID for presence tracking
        - org_id: Optional org ID for presence tracking

    Message Format (Client -> Server):
    {
        "type": "message.send" | "message.read" | "typing" | "subscribe",
        "conversation_id": "uuid",
        "content": "text",
        "message_id": "uuid" (for read receipts)
    }

    Message Format (Server -> Client):
    {
        "type": "message.new" | "message.edited" | "message.deleted" | "user.online" | "user.offline",
        "conversation_id": "uuid",
        "data": {...}
    }
    """
    await manager.connect(websocket, user_id, zone_id=zone_id, org_id=org_id)
    pubsub = get_pubsub()

    # Task for listening to Redis Pub/Sub
    async def listen_to_redis():
        """Background task to listen to Redis and forward to WebSocket"""
        try:
            async for message in pubsub.subscribe_user_notifications(user_id):
                try:
                    # Forward Redis message to WebSocket
                    await manager.send_personal_message(user_id, message)
                except Exception as e:
                    logger.error(
                        f"Failed to forward Redis message to user {user_id}: {e}"
                    )
                    break
        except asyncio.CancelledError:
            logger.info(f"Redis listener cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Redis listener error for user {user_id}: {e}")

    # Start Redis listener task
    redis_task = asyncio.create_task(listen_to_redis())

    try:
        # Main WebSocket receive loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")
                conversation_id = message.get("conversation_id")

                if message_type == "subscribe" and conversation_id:
                    # Subscribe to conversation updates
                    try:
                        conv_uuid = uuid.UUID(conversation_id)
                        await manager.subscribe_to_conversation(user_id, conv_uuid)
                        await websocket.send_json(
                            {"type": "subscribed", "conversation_id": conversation_id}
                        )
                    except ValueError:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "message": "Invalid conversation_id format",
                            }
                        )

                elif message_type == "message.send" and conversation_id:
                    # Handle real-time message sending via WebSocket
                    await handle_message_send(
                        websocket, user_id, uuid.UUID(conversation_id), message
                    )

                elif message_type == "message.reply" and message.get("parent_id"):
                    # Handle threaded reply via WebSocket
                    await handle_message_reply(
                        websocket,
                        user_id,
                        uuid.UUID(conversation_id) if conversation_id else None,
                        uuid.UUID(message["parent_id"]),
                        message,
                    )

                elif message_type == "message.edit" and message.get("message_id"):
                    # Handle message editing
                    await handle_message_edit(
                        websocket, user_id, uuid.UUID(message["message_id"]), message
                    )

                elif message_type == "message.delete" and message.get("message_id"):
                    # Handle message deletion
                    await handle_message_delete(
                        websocket, user_id, uuid.UUID(message["message_id"])
                    )

                elif message_type == "typing.start" and conversation_id:
                    # Update user activity
                    await update_user_activity(user_id)

                    # Broadcast typing indicator (start)
                    await pubsub.publish_message(
                        conversation_id=uuid.UUID(conversation_id),
                        message_data={
                            "type": "typing.start",
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                        },
                    )

                elif message_type == "typing.stop" and conversation_id:
                    # Broadcast typing indicator (stop)
                    await pubsub.publish_message(
                        conversation_id=uuid.UUID(conversation_id),
                        message_data={
                            "type": "typing.stop",
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                        },
                    )

                elif message_type == "message.read" and message.get("message_id"):
                    # Handle read receipt creation
                    await handle_read_receipt(
                        websocket, user_id, uuid.UUID(message["message_id"])
                    )

                elif (
                    message_type == "reaction.add"
                    and message.get("message_id")
                    and message.get("emoji")
                ):
                    # Handle adding emoji reaction
                    await handle_reaction_add(
                        websocket,
                        user_id,
                        uuid.UUID(message["message_id"]),
                        message["emoji"],
                    )

                elif (
                    message_type == "reaction.remove"
                    and message.get("message_id")
                    and message.get("emoji")
                ):
                    # Handle removing emoji reaction
                    await handle_reaction_remove(
                        websocket,
                        user_id,
                        uuid.UUID(message["message_id"]),
                        message["emoji"],
                    )

                elif (
                    message_type == "reaction.toggle"
                    and message.get("message_id")
                    and message.get("emoji")
                ):
                    # Handle toggling emoji reaction
                    await handle_reaction_toggle(
                        websocket,
                        user_id,
                        uuid.UUID(message["message_id"]),
                        message["emoji"],
                    )

                elif (
                    message_type == "call.initiate"
                    and conversation_id
                    and message.get("call_type")
                ):
                    # Handle call initiation
                    await handle_call_initiate(
                        websocket,
                        user_id,
                        uuid.UUID(conversation_id),
                        message,
                    )

                elif message_type == "call.answer" and message.get("call_id"):
                    # Handle call answer
                    await handle_call_answer(
                        websocket,
                        user_id,
                        uuid.UUID(message["call_id"]),
                        message,
                    )

                elif message_type == "call.reject" and message.get("call_id"):
                    # Handle call rejection
                    await handle_call_reject(
                        websocket,
                        user_id,
                        uuid.UUID(message["call_id"]),
                    )

                elif message_type == "call.end" and message.get("call_id"):
                    # Handle call end
                    await handle_call_end(
                        websocket,
                        user_id,
                        uuid.UUID(message["call_id"]),
                        message.get("end_reason", "completed"),
                    )

                elif message_type == "call.leave" and message.get("call_id"):
                    # Handle participant leaving
                    await handle_call_leave(
                        websocket,
                        user_id,
                        uuid.UUID(message["call_id"]),
                    )

                elif message_type == "call.media" and message.get("call_id"):
                    # Handle media toggle
                    await handle_call_media_update(
                        websocket,
                        user_id,
                        uuid.UUID(message["call_id"]),
                        message,
                    )

                elif message_type == "webrtc.offer" and message.get("call_id"):
                    # Handle WebRTC offer
                    await handle_webrtc_offer(
                        websocket,
                        user_id,
                        uuid.UUID(message["call_id"]),
                        message,
                    )

                elif message_type == "webrtc.answer" and message.get("call_id"):
                    # Handle WebRTC answer
                    await handle_webrtc_answer(
                        websocket,
                        user_id,
                        uuid.UUID(message["call_id"]),
                        message,
                    )

                elif message_type == "webrtc.ice_candidate" and message.get("call_id"):
                    # Handle ICE candidate
                    await handle_webrtc_ice_candidate(
                        websocket,
                        user_id,
                        uuid.UUID(message["call_id"]),
                        message,
                    )

                elif message_type == "webrtc.renegotiate" and message.get("call_id"):
                    # Handle WebRTC renegotiation (for screen sharing, etc.)
                    await handle_webrtc_renegotiate(
                        websocket,
                        user_id,
                        uuid.UUID(message["call_id"]),
                        message,
                    )

                elif message_type == "webrtc.connection_state" and message.get(
                    "call_id"
                ):
                    # Handle WebRTC connection state updates
                    await handle_webrtc_connection_state(
                        websocket,
                        user_id,
                        uuid.UUID(message["call_id"]),
                        message,
                    )

                elif message_type == "typing" and conversation_id:
                    # Legacy typing support (backward compatibility)
                    await pubsub.publish_message(
                        conversation_id=uuid.UUID(conversation_id),
                        message_data={
                            "type": "typing",
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                        },
                    )

                else:
                    # Unknown message type
                    logger.warning(f"Unknown WebSocket message type: {message_type}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from user {user_id}: {data}")
                await websocket.send_json(
                    {"type": "error", "message": "Invalid JSON format"}
                )
            except Exception as e:
                logger.error(
                    f"Error processing WebSocket message from user {user_id}: {e}"
                )
                await websocket.send_json(
                    {"type": "error", "message": "Internal server error"}
                )

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        # Cleanup
        redis_task.cancel()
        try:
            await redis_task
        except asyncio.CancelledError:
            pass
        await manager.disconnect(websocket, user_id)


# ============================================================================
# Push Notification Endpoints
# ============================================================================


@router.post("/devices/register")
async def register_device(
    device_token: str,
    platform: str,
    provider: str = "fcm",
    device_name: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Register a device token for push notifications.

    Supports:
    - FCM (Firebase Cloud Messaging) - Android, iOS, Web
    - APNs (Apple Push Notification Service) - iOS native
    - Web Push - Progressive Web Apps

    Request Body:
        - device_token: FCM registration token, APNs device token, or Web Push subscription JSON
        - platform: Device platform - 'ios', 'android', or 'web'
        - provider: Push provider - 'fcm' (default), 'apns', or 'web_push'
        - device_name: Optional user-friendly device name

    Returns:
        - status: 'registered' or 'updated'
        - device_token_id: ID of the registered device
        - user_id: User ID

    Example:
        POST /devices/register
        {
            "device_token": "ePXo7...",
            "platform": "android",
            "provider": "fcm",
            "device_name": "Samsung Galaxy S21"
        }
    """
    from app.messenger.push_notifications import (
        DevicePlatform,
        PushProvider,
        get_push_service,
    )

    # Validate platform
    if platform not in [p.value for p in DevicePlatform]:
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {platform}. Must be one of: ios, android, web",
        )

    # Validate provider
    if provider not in [p.value for p in PushProvider]:
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider: {provider}. Must be one of: fcm, apns, web_push",
        )

    push_service = get_push_service()

    result = await push_service.register_device(
        db=db,
        user_id=int(user.id),  # type: ignore
        device_token=device_token,
        platform=DevicePlatform(platform),
        provider=PushProvider(provider),
        device_name=device_name,
    )

    return result


@router.delete("/devices/{device_token}")
async def unregister_device(
    device_token: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Unregister a device token (e.g., on logout).

    Path Parameters:
        - device_token: Device token to remove

    Returns:
        - success: True if unregistered, False if not found

    Example:
        DELETE /devices/ePXo7...
    """
    from app.messenger.push_notifications import get_push_service

    push_service = get_push_service()

    success = await push_service.unregister_device(
        db=db,
        user_id=int(user.id),  # type: ignore
        device_token=device_token,
    )

    if not success:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Device token not found",
        )

    return {"success": True, "message": "Device unregistered"}


@router.get("/devices")
async def list_devices(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    List all registered devices for the current user.

    Returns:
        - devices: List of registered devices with platform, provider, and registration info

    Example:
        GET /devices
        Response:
        {
            "devices": [
                {
                    "id": 1,
                    "platform": "android",
                    "provider": "fcm",
                    "device_name": "Samsung Galaxy S21",
                    "registered_at": "2024-01-15T10:30:00Z",
                    "last_used_at": "2024-01-15T14:20:00Z"
                }
            ]
        }
    """
    from app.messenger.push_notifications import get_push_service

    push_service = get_push_service()

    devices = await push_service.get_user_devices(db=db, user_id=int(user.id))  # type: ignore

    return {"devices": devices}


# ============================================================================
# Analytics Endpoints
# ============================================================================


@router.get("/analytics/dashboard")
async def get_analytics_dashboard(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get comprehensive analytics dashboard summary.

    Query Parameters:
        - days: Number of days to look back (1-90, default: 7)

    Returns:
        Dashboard summary with:
        - message_stats: Total messages, types, senders
        - engagement_metrics: Active users, engagement rates
        - active_users_24h: Users active in last 24 hours
        - top_senders: Top 5 message senders
        - message_timeline: Daily message counts

    Example:
        GET /analytics/dashboard?days=30
    """
    from app.messenger.analytics import get_analytics_service

    analytics = get_analytics_service()
    summary = await analytics.get_dashboard_summary(db, days=days)

    return summary


@router.get("/analytics/messages")
async def get_message_analytics(
    conversation_id: Optional[str] = Query(None, description="Filter by conversation"),
    user_id_filter: Optional[int] = Query(None, description="Filter by user"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get detailed message statistics.

    Query Parameters:
        - conversation_id: Optional conversation UUID filter
        - user_id_filter: Optional user ID filter
        - days: Number of days to look back (1-365, default: 30)

    Returns:
        Message statistics including:
        - total_messages: Total message count
        - text_messages, image_messages, file_messages, system_messages: Counts by type
        - unique_senders: Number of unique message senders
        - avg_message_length: Average message length in characters
        - message_type_distribution: Percentage distribution by type

    Example:
        GET /analytics/messages?days=7
        GET /analytics/messages?conversation_id=f47ac10b-58cc-4372-a567-0e02b2c3d479
    """
    from datetime import datetime, timedelta
    from app.messenger.analytics import get_analytics_service

    analytics = get_analytics_service()

    start_date = datetime.utcnow() - timedelta(days=days)

    stats = await analytics.get_message_stats(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id_filter,
        start_date=start_date,
    )

    return stats


@router.get("/analytics/timeline")
async def get_message_timeline(
    interval: str = Query(
        "daily", regex="^(hourly|daily|weekly|monthly)$", description="Time interval"
    ),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation"),
    user_id_filter: Optional[int] = Query(None, description="Filter by user"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get message count timeline by time interval.

    Query Parameters:
        - interval: Time interval (hourly, daily, weekly, monthly)
        - conversation_id: Optional conversation UUID filter
        - user_id_filter: Optional user ID filter
        - days: Number of days to look back (1-365, default: 30)

    Returns:
        List of timestamp/count pairs showing message activity over time

    Example:
        GET /analytics/timeline?interval=daily&days=7
        Response:
        [
            {"timestamp": "2024-01-15T00:00:00Z", "count": 45},
            {"timestamp": "2024-01-16T00:00:00Z", "count": 52},
            ...
        ]
    """
    from app.messenger.analytics import TimeInterval, get_analytics_service

    analytics = get_analytics_service()

    timeline = await analytics.get_message_timeline(
        db=db,
        interval=TimeInterval(interval),
        conversation_id=conversation_id,
        user_id=user_id_filter,
        days=days,
    )

    return {"timeline": timeline}


@router.get("/analytics/top-senders")
async def get_top_senders(
    conversation_id: Optional[str] = Query(None, description="Filter by conversation"),
    limit: int = Query(10, ge=1, le=100, description="Number of top senders"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get top message senders.

    Query Parameters:
        - conversation_id: Optional conversation UUID filter
        - limit: Number of top senders to return (1-100, default: 10)
        - days: Number of days to look back (1-365, default: 30)

    Returns:
        List of top senders with user_id, username, and message_count

    Example:
        GET /analytics/top-senders?limit=5&days=7
        Response:
        [
            {"user_id": 123, "username": "alice", "message_count": 245},
            {"user_id": 456, "username": "bob", "message_count": 198},
            ...
        ]
    """
    from app.messenger.analytics import get_analytics_service

    analytics = get_analytics_service()

    top_senders = await analytics.get_top_senders(
        db=db,
        conversation_id=conversation_id,
        limit=limit,
        days=days,
    )

    return {"top_senders": top_senders}


@router.get("/analytics/user/{user_id}")
async def get_user_activity(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get activity statistics for a specific user.

    Path Parameters:
        - user_id: User ID to get stats for

    Query Parameters:
        - days: Number of days to look back (1-365, default: 30)

    Returns:
        User activity statistics including:
        - messages_sent: Number of messages sent
        - messages_read: Number of messages read
        - active_conversations: Number of active conversations
        - avg_messages_per_day: Average messages per day
        - first_message_date: Date of first message
        - last_activity_date: Date of last activity

    Example:
        GET /analytics/user/123?days=7
    """
    from app.messenger.analytics import get_analytics_service

    analytics = get_analytics_service()

    stats = await analytics.get_user_activity_stats(
        db=db,
        user_id=user_id,
        days=days,
    )

    return stats


@router.get("/analytics/engagement")
async def get_engagement_metrics(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user engagement metrics.

    Query Parameters:
        - days: Number of days to look back (1-90, default: 7)

    Returns:
        Engagement metrics including:
        - total_users: Total registered users
        - active_users: Users who sent at least 1 message
        - engaged_users: Users who sent 5+ messages
        - engagement_rate: Percentage of active users
        - deep_engagement_rate: Percentage of engaged users

    Example:
        GET /analytics/engagement?days=30
        Response:
        {
            "period_days": 30,
            "total_users": 1000,
            "active_users": 450,
            "engaged_users": 200,
            "engagement_rate": 45.0,
            "deep_engagement_rate": 20.0
        }
    """
    from app.messenger.analytics import get_analytics_service

    analytics = get_analytics_service()

    metrics = await analytics.get_user_engagement_metrics(db=db, days=days)

    return metrics


@router.get("/analytics/conversation/{conversation_id}")
async def get_conversation_analytics(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get detailed statistics for a specific conversation.

    Path Parameters:
        - conversation_id: Conversation UUID

    Returns:
        Conversation statistics including:
        - participant_count: Number of participants
        - active_participants: Participants who sent messages
        - message_count: Total messages
        - messages_per_day: Average messages per day
        - conversation_age_days: Age in days
        - first_message_date: Date of first message
        - last_message_date: Date of last message

    Example:
        GET /analytics/conversation/f47ac10b-58cc-4372-a567-0e02b2c3d479
    """
    from app.messenger.analytics import get_analytics_service

    # Verify user is participant
    await get_conversation_or_404(uuid.UUID(conversation_id), user, db)

    analytics = get_analytics_service()

    stats = await analytics.get_conversation_stats(
        db=db, conversation_id=conversation_id
    )

    return stats


@router.get("/analytics/top-conversations")
async def get_top_conversations(
    limit: int = Query(10, ge=1, le=50, description="Number of conversations"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    sort_by: str = Query(
        "messages", regex="^(messages|participants|activity)$", description="Sort by"
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get top conversations by activity.

    Query Parameters:
        - limit: Number of top conversations (1-50, default: 10)
        - days: Number of days to look back (1-365, default: 30)
        - sort_by: Sort criteria (messages, participants, activity)

    Returns:
        List of conversation statistics ordered by activity

    Example:
        GET /analytics/top-conversations?limit=5&days=7&sort_by=messages
    """
    from app.messenger.analytics import get_analytics_service

    analytics = get_analytics_service()

    conversations = await analytics.get_top_conversations(
        db=db,
        limit=limit,
        days=days,
        sort_by=sort_by,
    )

    return {"conversations": conversations}


# ============================================================================
# SEARCH & DISCOVERY ENDPOINTS (Task 3.2)
# ============================================================================


@router.get("/search/messages")
async def search_messages(
    query: str = Query(..., min_length=1, description="Search query"),
    conversation_id: Optional[str] = Query(
        None, description="Filter by conversation ID"
    ),
    sender_id: Optional[int] = Query(None, description="Filter by sender user ID"),
    message_type: Optional[str] = Query(
        None, description="Filter by message type (text, image, file, system)"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Filter messages after this date (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter messages before this date (ISO format)"
    ),
    sort_by: str = Query(
        "relevance",
        regex="^(relevance|date_desc|date_asc)$",
        description="Sort order: relevance, date_desc, date_asc",
    ),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Result offset for pagination"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Full-text search for messages with advanced filtering.

    Uses PostgreSQL full-text search with relevance ranking and fuzzy matching.

    Query Parameters:
        - query: Search query (required)
        - conversation_id: Filter by conversation (optional)
        - sender_id: Filter by sender (optional)
        - message_type: Filter by type (optional)
        - start_date: Filter messages after date (optional)
        - end_date: Filter messages before date (optional)
        - sort_by: Sort order (relevance/date_desc/date_asc, default: relevance)
        - limit: Results per page (1-100, default: 50)
        - offset: Pagination offset (default: 0)

    Returns:
        Search results with:
        - query: Original search query
        - total_count: Total matching results
        - results: List of message results with relevance ranking
        - limit: Results per page
        - offset: Current offset
        - has_more: Whether more results are available

    Features:
        - Full-text search with relevance ranking (ts_rank)
        - Search term highlighting in results
        - Permission checks (user must be conversation participant)
        - Advanced filtering by conversation, sender, type, date range
        - Pagination support

    Example:
        GET /search/messages?query=budget&conversation_id=conv_123&limit=20
    """
    from app.messenger.search import get_search_service, MessageType, SortOrder

    # Parse message_type enum
    parsed_type = None
    if message_type:
        try:
            parsed_type = MessageType(message_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid message_type. Must be one of: {', '.join([t.value for t in MessageType])}",
            )

    # Parse sort_by enum
    sort_order = SortOrder.RELEVANCE
    if sort_by == "date_desc":
        sort_order = SortOrder.DATE_DESC
    elif sort_by == "date_asc":
        sort_order = SortOrder.DATE_ASC

    search_service = get_search_service()

    results = await search_service.search_messages(
        db=db,
        query=query,
        user_id=int(user.id),  # type: ignore
        conversation_id=conversation_id,
        sender_id=sender_id,
        message_type=parsed_type,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_order,
        limit=limit,
        offset=offset,
    )

    return results


@router.get("/search/messages/simple")
async def search_messages_simple(
    query: str = Query(..., min_length=1, description="Search query"),
    conversation_id: str = Query(..., description="Conversation ID to search within"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Simple in-chat message search using ILIKE pattern matching.

    Faster than full-text search but less sophisticated. Good for quick
    in-conversation searches.

    Query Parameters:
        - query: Search query (required)
        - conversation_id: Conversation to search in (required)
        - limit: Maximum results (1-100, default: 50)

    Returns:
        List of matching messages with basic information

    Example:
        GET /search/messages/simple?query=budget&conversation_id=conv_123
    """
    from app.messenger.search import get_search_service

    search_service = get_search_service()

    results = await search_service.search_messages_simple(
        db=db,
        query=query,
        user_id=int(user.id),  # type: ignore
        conversation_id=conversation_id,
        limit=limit,
    )

    return {"results": results}


@router.get("/search/conversations")
async def search_conversations(
    query: str = Query(..., min_length=1, description="Search query"),
    conversation_type: Optional[str] = Query(
        None, description="Filter by type (direct, group, zone, org)"
    ),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Result offset for pagination"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Search conversations by title or participant usernames.

    Uses trigram similarity for fuzzy matching on conversation titles.

    Query Parameters:
        - query: Search query (required)
        - conversation_type: Filter by type (optional)
        - limit: Results per page (1-100, default: 20)
        - offset: Pagination offset (default: 0)

    Returns:
        Search results with:
        - query: Original search query
        - total_count: Total matching results
        - results: List of conversation results
        - limit: Results per page
        - offset: Current offset
        - has_more: Whether more results are available

    Example:
        GET /search/conversations?query=project&conversation_type=group
    """
    from app.messenger.search import get_search_service

    search_service = get_search_service()

    results = await search_service.search_conversations(
        db=db,
        query=query,
        user_id=int(user.id),  # type: ignore
        conversation_type=conversation_type,
        limit=limit,
        offset=offset,
    )

    return results


@router.get("/discover/conversations")
async def discover_conversations(
    zone_id: Optional[int] = Query(None, description="Filter by zone ID"),
    org_id: Optional[int] = Query(None, description="Filter by organization ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Discover public conversations that the user can join.

    Returns zone and org conversations that the user is not yet part of.

    Query Parameters:
        - zone_id: Filter by zone (optional)
        - org_id: Filter by organization (optional)
        - limit: Maximum results (1-100, default: 20)

    Returns:
        List of discoverable conversations with:
        - conversation_id: Unique conversation ID
        - title: Conversation title
        - type: Conversation type (zone/org)
        - participant_count: Number of participants
        - created_at: Creation timestamp

    Example:
        GET /discover/conversations?zone_id=1&limit=10
    """
    from app.messenger.search import get_search_service

    search_service = get_search_service()

    results = await search_service.discover_conversations(
        db=db,
        user_id=int(user.id),  # type: ignore
        zone_id=zone_id,
        org_id=org_id,
        limit=limit,
    )

    return {"results": results}


@router.get("/search/users")
async def search_users(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Result offset for pagination"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Search users by username or email for direct messages.

    Uses trigram similarity for fuzzy matching on usernames.

    Query Parameters:
        - query: Search query (required)
        - limit: Results per page (1-100, default: 20)
        - offset: Pagination offset (default: 0)

    Returns:
        Search results with:
        - query: Original search query
        - total_count: Total matching results
        - results: List of user results
        - limit: Results per page
        - offset: Current offset
        - has_more: Whether more results are available

    Example:
        GET /search/users?query=john&limit=10
    """
    from app.messenger.search import get_search_service

    search_service = get_search_service()

    results = await search_service.search_users(
        db=db,
        query=query,
        current_user_id=int(user.id),  # type: ignore
        limit=limit,
        offset=offset,
    )

    return results


@router.get("/autocomplete/users")
async def autocomplete_users(
    query: str = Query(..., min_length=1, description="Search query (username prefix)"),
    conversation_id: Optional[str] = Query(
        None, description="Prioritize users from this conversation"
    ),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Autocomplete user suggestions for mentions or direct message creation.

    If conversation_id is provided, prioritizes users from that conversation.

    Query Parameters:
        - query: Username prefix (required)
        - conversation_id: Prioritize users from conversation (optional)
        - limit: Maximum results (1-50, default: 10)

    Returns:
        List of user suggestions with:
        - user_id: User ID
        - username: Username
        - email: User email
        - is_participant: Whether user is in the specified conversation

    Example:
        GET /autocomplete/users?query=jo&conversation_id=conv_123&limit=5
    """
    from app.messenger.search import get_search_service

    search_service = get_search_service()

    results = await search_service.autocomplete_users(
        db=db,
        query=query,
        current_user_id=int(user.id),  # type: ignore
        conversation_id=conversation_id,
        limit=limit,
    )

    return {"results": results}


# ============================================================================
# ADMIN & MODERATION ENDPOINTS (Task 3.3)
# ============================================================================


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role."""
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )
    return user


@router.get("/admin/dashboard")
async def get_admin_dashboard(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get admin dashboard statistics.

    Returns comprehensive stats for admin overview.

    Requires: Admin role

    Returns:
        Dashboard statistics including:
        - total_users: Total users count
        - total_conversations: Total conversations count
        - total_messages: Total messages count
        - messages_today: Messages sent today
        - deleted_messages_30d: Messages deleted in last 30 days
        - pending_reports: Reports awaiting review
        - active_restrictions: Users with active restrictions

    Example:
        GET /admin/dashboard
    """
    from app.messenger.admin import get_admin_service

    admin_service = get_admin_service()

    stats = await admin_service.get_admin_dashboard_stats(db=db)

    return stats


@router.get("/admin/moderation/stats")
async def get_moderation_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get moderation statistics for specified period.

    Query Parameters:
        - days: Number of days to look back (1-90, default: 7)

    Requires: Admin role

    Returns:
        Moderation statistics including:
        - period_days: Days included in stats
        - deleted_messages: Messages deleted by moderators
        - active_bans: Currently banned users
        - active_mutes: Currently muted users
        - pending_reports: Reports awaiting review
        - resolved_reports: Reports resolved in period

    Example:
        GET /admin/moderation/stats?days=30
    """
    from app.messenger.admin import get_admin_service

    admin_service = get_admin_service()

    stats = await admin_service.get_moderation_stats(
        db=db,
        days=days,
    )

    return stats


@router.get("/admin/messages/flagged")
async def get_flagged_messages(
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get messages flagged for moderation review.

    Query Parameters:
        - limit: Results per page (1-100, default: 50)
        - offset: Pagination offset (default: 0)

    Requires: Admin role

    Returns:
        List of flagged messages with:
        - id: Message ID
        - conversation_id: Conversation ID
        - sender_id: Sender user ID
        - sender_email: Sender email
        - content: Message content
        - deleted_at: Deletion timestamp (if deleted)
        - created_at: Creation timestamp

    Example:
        GET /admin/messages/flagged?limit=20
    """
    from app.messenger.admin import get_admin_service

    admin_service = get_admin_service()

    messages = await admin_service.get_flagged_messages(
        db=db,
        limit=limit,
        offset=offset,
    )

    return {"flagged_messages": messages, "limit": limit, "offset": offset}


@router.delete("/admin/messages/{message_id}")
async def delete_message_by_admin(
    message_id: int,
    reason: str = Query(..., min_length=10, description="Reason for deletion"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete message by admin (moderation action).

    Soft deletes message and logs the action.

    Path Parameters:
        - message_id: Message ID to delete

    Query Parameters:
        - reason: Reason for deletion (required, min 10 chars)

    Requires: Admin role

    Returns:
        Deletion details including:
        - message_id: Deleted message ID
        - deleted: Success status
        - reason: Deletion reason
        - admin_id: Admin who performed action
        - log_id: Moderation log entry ID

    Example:
        DELETE /admin/messages/123?reason=Contains+spam+content
    """
    from app.messenger.admin import get_admin_service

    admin_service = get_admin_service()

    result = await admin_service.delete_message_by_admin(
        db=db,
        message_id=message_id,
        admin_id=int(admin.id),  # type: ignore
        reason=reason,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.delete("/admin/conversations/{conversation_id}")
async def delete_conversation_by_admin(
    conversation_id: str,
    reason: str = Query(..., min_length=10, description="Reason for deletion"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete conversation by admin (moderation action).

    Soft deletes all messages in conversation and logs the action.

    Path Parameters:
        - conversation_id: Conversation ID to delete

    Query Parameters:
        - reason: Reason for deletion (required, min 10 chars)

    Requires: Admin role

    Returns:
        Deletion details including:
        - conversation_id: Deleted conversation ID
        - deleted: Success status
        - reason: Deletion reason
        - admin_id: Admin who performed action
        - log_id: Moderation log entry ID

    Example:
        DELETE /admin/conversations/conv_123?reason=Violates+community+guidelines
    """
    from app.messenger.admin import get_admin_service

    admin_service = get_admin_service()

    result = await admin_service.delete_conversation_by_admin(
        db=db,
        conversation_id=conversation_id,
        admin_id=int(admin.id),  # type: ignore
        reason=reason,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/admin/users/{user_id}/restriction")
async def get_user_restriction(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user's current messenger restriction level.

    Path Parameters:
        - user_id: User ID to check

    Requires: Admin role

    Returns:
        User restriction details:
        - user_id: User ID
        - restriction: Restriction level (none/muted/restricted/banned)
        - reason: Reason for restriction (if any)
        - expires_at: Expiration timestamp (if temporary)

    Example:
        GET /admin/users/123/restriction
    """
    from app.messenger.admin import get_admin_service

    admin_service = get_admin_service()

    restriction = await admin_service.get_user_restriction(
        db=db,
        user_id=user_id,
    )

    # Get user details
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    expires_at_value = getattr(user, "messenger_restriction_expires_at", None)
    return {
        "user_id": user_id,
        "restriction": restriction.value,
        "reason": getattr(user, "messenger_restriction_reason", None),
        "expires_at": (expires_at_value.isoformat() if expires_at_value else None),
    }


@router.post("/admin/users/{user_id}/restriction")
async def set_user_restriction(
    user_id: int,
    restriction: str = Query(
        ..., regex="^(none|muted|restricted|banned)$", description="Restriction level"
    ),
    reason: str = Query(..., min_length=10, description="Reason for restriction"),
    duration_minutes: Optional[int] = Query(
        None, ge=1, le=525600, description="Duration in minutes (max 1 year)"
    ),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Set user's messenger restriction level.

    Path Parameters:
        - user_id: User ID to restrict

    Query Parameters:
        - restriction: Restriction level (none/muted/restricted/banned)
        - reason: Reason for restriction (required, min 10 chars)
        - duration_minutes: Optional duration (1-525600, None = permanent)

    Requires: Admin role

    Restriction Levels:
        - none: No restrictions
        - muted: Can't send messages
        - restricted: Can only message existing conversations
        - banned: Can't access messenger at all

    Returns:
        Restriction details including:
        - user_id: User ID
        - restriction: Restriction level
        - reason: Restriction reason
        - expires_at: Expiration timestamp (if temporary)
        - admin_id: Admin who set restriction
        - log_id: Moderation log entry ID

    Example:
        POST /admin/users/123/restriction?restriction=muted&reason=Spam+behavior&duration_minutes=1440
    """
    from app.messenger.admin import get_admin_service, UserRestriction

    admin_service = get_admin_service()

    restriction_enum = UserRestriction(restriction)

    result = await admin_service.set_user_restriction(
        db=db,
        user_id=user_id,
        restriction=restriction_enum,
        reason=reason,
        admin_id=int(admin.id),  # type: ignore
        duration_minutes=duration_minutes,
    )

    return result


@router.get("/admin/users/{user_id}/moderation-history")
async def get_user_moderation_history(
    user_id: int,
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get moderation history for a user.

    Path Parameters:
        - user_id: User ID to check

    Query Parameters:
        - limit: Max results (1-100, default: 20)

    Requires: Admin role

    Returns:
        List of moderation actions for user:
        - id: Log entry ID
        - action: Action type
        - admin_id: Admin who performed action
        - reason: Action reason
        - metadata: Additional action details
        - created_at: Action timestamp

    Example:
        GET /admin/users/123/moderation-history?limit=10
    """
    from app.messenger.admin import get_admin_service

    admin_service = get_admin_service()

    history = await admin_service.get_user_moderation_history(
        db=db,
        user_id=user_id,
        limit=limit,
    )

    return {"user_id": user_id, "history": history, "limit": limit}


@router.post("/reports")
async def create_report(
    reported_user_id: Optional[int] = Query(None, description="User being reported"),
    message_id: Optional[int] = Query(None, description="Message being reported"),
    conversation_id: Optional[str] = Query(
        None, description="Conversation being reported"
    ),
    reason: str = Query(
        ...,
        regex="^(spam|harassment|hate_speech|violence|inappropriate_content|impersonation|other)$",
        description="Report reason",
    ),
    description: Optional[str] = Query(
        None, max_length=1000, description="Detailed description"
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a report for admin review.

    Any user can create a report for content they find inappropriate.

    Query Parameters:
        - reported_user_id: Optional user being reported
        - message_id: Optional message being reported
        - conversation_id: Optional conversation being reported
        - reason: Report reason (required)
        - description: Optional detailed description (max 1000 chars)

    Reason Options:
        - spam: Unwanted spam content
        - harassment: Harassment or bullying
        - hate_speech: Hate speech or discrimination
        - violence: Violence or threats
        - inappropriate_content: Inappropriate or explicit content
        - impersonation: Impersonation or identity theft
        - other: Other reason (provide description)

    Returns:
        Report details including:
        - id: Report ID
        - reporter_id: User who created report
        - status: Report status (pending)
        - created_at: Creation timestamp

    Example:
        POST /reports?message_id=123&reason=spam&description=This+is+spam
    """
    from app.messenger.admin import get_admin_service, ReportReason

    # At least one target required
    if not any([reported_user_id, message_id, conversation_id]):
        raise HTTPException(
            status_code=400,
            detail="Must specify at least one: reported_user_id, message_id, or conversation_id",
        )

    admin_service = get_admin_service()

    report = await admin_service.create_report(
        db=db,
        reporter_id=int(user.id),  # type: ignore
        reported_user_id=reported_user_id,
        message_id=message_id,
        conversation_id=conversation_id,
        reason=ReportReason(reason),
        description=description,
    )

    return report


@router.get("/admin/reports")
async def get_pending_reports(
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get pending reports for admin review.

    Query Parameters:
        - limit: Results per page (1-100, default: 50)
        - offset: Pagination offset (default: 0)

    Requires: Admin role

    Returns:
        List of pending reports with:
        - id: Report ID
        - reporter_id: User who created report
        - reported_user_id: User being reported
        - message_id: Message being reported
        - conversation_id: Conversation being reported
        - reason: Report reason
        - description: Detailed description
        - status: Report status
        - created_at: Creation timestamp

    Example:
        GET /admin/reports?limit=20
    """
    from app.messenger.admin import get_admin_service

    admin_service = get_admin_service()

    reports = await admin_service.get_pending_reports(
        db=db,
        limit=limit,
        offset=offset,
    )

    return {"reports": reports, "limit": limit, "offset": offset}


@router.post("/admin/reports/{report_id}/resolve")
async def resolve_report(
    report_id: int,
    resolution: str = Query(..., min_length=10, description="Resolution description"),
    action_taken: Optional[str] = Query(
        None,
        regex="^(warn|mute|ban|delete_message|delete_conversation|restrict)$",
        description="Moderation action taken",
    ),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Resolve a report.

    Path Parameters:
        - report_id: Report ID to resolve

    Query Parameters:
        - resolution: Resolution description (required, min 10 chars)
        - action_taken: Optional moderation action taken

    Requires: Admin role

    Action Options:
        - warn: Issued warning to user
        - mute: Muted user
        - ban: Banned user
        - delete_message: Deleted reported message
        - delete_conversation: Deleted reported conversation
        - restrict: Restricted user access

    Returns:
        Resolution details including:
        - report_id: Report ID
        - status: New status (resolved)
        - admin_id: Admin who resolved report
        - resolution: Resolution description
        - action_taken: Action taken (if any)
        - resolved_at: Resolution timestamp

    Example:
        POST /admin/reports/123/resolve?resolution=Removed+spam+content&action_taken=delete_message
    """
    from app.messenger.admin import get_admin_service, ModerationAction

    admin_service = get_admin_service()

    action_enum = ModerationAction(action_taken) if action_taken else None

    result = await admin_service.resolve_report(
        db=db,
        report_id=report_id,
        admin_id=int(admin.id),  # type: ignore
        resolution=resolution,
        action_taken=action_enum,
    )

    return result


@router.post("/admin/keywords")
async def update_blocked_keywords(
    keywords: list[str] = Query(..., description="List of blocked keywords"),
    admin: User = Depends(require_admin),
):
    """
    Update blocked keywords list for content moderation.

    Query Parameters:
        - keywords: List of keywords to block (can be empty to clear)

    Requires: Admin role

    Returns:
        Updated keywords list:
        - keywords: Current blocked keywords
        - count: Number of keywords

    Example:
        POST /admin/keywords?keywords=spam&keywords=scam&keywords=phishing
    """
    from app.messenger.admin import get_admin_service

    admin_service = get_admin_service()

    admin_service.update_blocked_keywords(keywords)

    return {
        "keywords": admin_service.blocked_keywords,
        "count": len(admin_service.blocked_keywords),
    }


@router.get("/admin/keywords")
async def get_blocked_keywords(
    admin: User = Depends(require_admin),
):
    """
    Get current blocked keywords list.

    Requires: Admin role

    Returns:
        Current keywords list:
        - keywords: Current blocked keywords
        - count: Number of keywords

    Example:
        GET /admin/keywords
    """
    from app.messenger.admin import get_admin_service

    admin_service = get_admin_service()

    return {
        "keywords": admin_service.blocked_keywords,
        "count": len(admin_service.blocked_keywords),
    }


# ============================================================================
# ENHANCED NOTIFICATION ENDPOINTS (Task 4.1)
# ============================================================================


@router.get("/notifications")
async def get_notifications(
    unread_only: bool = Query(False, description="Show only unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user in-app notifications.

    Query Parameters:
        - unread_only: Show only unread notifications (default: false)
        - limit: Results per page (1-100, default: 50)
        - offset: Pagination offset (default: 0)

    Returns:
        List of notifications with:
        - id: Notification ID
        - type: Notification type
        - title: Notification title
        - message: Notification message
        - data: Additional data (JSON)
        - is_read: Read status
        - read_at: Read timestamp (if read)
        - action_url: Optional action URL
        - priority: Priority level
        - created_at: Creation timestamp

    Example:
        GET /notifications?unread_only=true&limit=20
    """
    from app.messenger.notifications import get_notification_service

    notification_service = get_notification_service()

    notifications = await notification_service.get_in_app_notifications(
        db=db,
        user_id=int(user.id),  # type: ignore
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )

    return {"notifications": notifications, "limit": limit, "offset": offset}


@router.get("/notifications/unread-count")
async def get_unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get count of unread notifications.

    Returns:
        Unread notification count:
        - count: Number of unread notifications

    Example:
        GET /notifications/unread-count
    """
    from app.messenger.notifications import get_notification_service

    notification_service = get_notification_service()

    count = await notification_service.get_unread_count(
        db=db,
        user_id=int(user.id),  # type: ignore
    )

    return {"count": count}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Mark notification as read.

    Path Parameters:
        - notification_id: Notification ID to mark as read

    Returns:
        Success status:
        - success: Whether operation succeeded
        - notification_id: Notification ID

    Example:
        POST /notifications/123/read
    """
    from app.messenger.notifications import get_notification_service

    notification_service = get_notification_service()

    success = await notification_service.mark_notification_read(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_id=notification_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"success": True, "notification_id": notification_id}


@router.post("/notifications/mark-all-read")
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Mark all notifications as read.

    Returns:
        Count of marked notifications:
        - marked_count: Number of notifications marked as read

    Example:
        POST /notifications/mark-all-read
    """
    from app.messenger.notifications import get_notification_service

    notification_service = get_notification_service()

    count = await notification_service.mark_all_read(
        db=db,
        user_id=int(user.id),  # type: ignore
    )

    return {"marked_count": count}


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete notification.

    Path Parameters:
        - notification_id: Notification ID to delete

    Returns:
        Success status:
        - success: Whether operation succeeded
        - notification_id: Notification ID

    Example:
        DELETE /notifications/123
    """
    from app.messenger.notifications import get_notification_service

    notification_service = get_notification_service()

    success = await notification_service.delete_notification(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_id=notification_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"success": True, "notification_id": notification_id}


@router.get("/notification-preferences")
async def get_notification_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get user's notification preferences.

    Returns:
        Notification preferences by channel and type:
        {
            "push": {
                "new_message": {"enabled": true, "quiet_hours_start": "22:00", ...},
                ...
            },
            "email": {...},
            "in_app": {...}
        }

    Example:
        GET /notification-preferences
    """
    from app.messenger.notifications import get_notification_service

    notification_service = get_notification_service()

    preferences = await notification_service.get_user_preferences(
        db=db,
        user_id=int(user.id),  # type: ignore
    )

    return {"preferences": preferences}


@router.put("/notification-preferences")
async def set_notification_preference(
    channel: str = Query(
        ..., regex="^(push|email|in_app)$", description="Notification channel"
    ),
    notification_type: str = Query(
        ...,
        regex="^(new_message|message_mention|message_reply|conversation_invite|"
        "participant_added|participant_removed|file_uploaded|system_announcement|"
        "moderation_warning|moderation_action)$",
        description="Notification type",
    ),
    enabled: bool = Query(..., description="Enable or disable notifications"),
    quiet_hours_start: Optional[str] = Query(
        None,
        regex="^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Quiet hours start (HH:MM)",
    ),
    quiet_hours_end: Optional[str] = Query(
        None,
        regex="^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Quiet hours end (HH:MM)",
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Set user notification preference.

    Query Parameters:
        - channel: Notification channel (push/email/in_app)
        - notification_type: Type of notification
        - enabled: Enable or disable (true/false)
        - quiet_hours_start: Optional quiet hours start time (HH:MM format)
        - quiet_hours_end: Optional quiet hours end time (HH:MM format)

    Returns:
        Success status:
        - success: Whether operation succeeded
        - channel: Channel name
        - notification_type: Notification type
        - enabled: Enabled status

    Example:
        PUT /notification-preferences?channel=push&notification_type=new_message&enabled=true&quiet_hours_start=22:00&quiet_hours_end=08:00
    """
    from app.messenger.notifications import (
        get_notification_service,
        NotificationChannel,
        NotificationType,
    )
    from datetime import time

    notification_service = get_notification_service()

    # Parse time strings
    start_time = None
    end_time = None

    if quiet_hours_start:
        hour, minute = map(int, quiet_hours_start.split(":"))
        start_time = time(hour, minute)

    if quiet_hours_end:
        hour, minute = map(int, quiet_hours_end.split(":"))
        end_time = time(hour, minute)

    await notification_service.set_user_preference(
        db=db,
        user_id=int(user.id),  # type: ignore
        channel=NotificationChannel(channel),
        notification_type=NotificationType(notification_type),
        enabled=enabled,
        quiet_hours_start=start_time,
        quiet_hours_end=end_time,
    )

    return {
        "success": True,
        "channel": channel,
        "notification_type": notification_type,
        "enabled": enabled,
    }


@router.post("/test-notification")
async def send_test_notification(
    notification_type: str = Query(
        "new_message",
        regex="^(new_message|message_mention|conversation_invite|system_announcement)$",
        description="Notification type to test",
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Send test notification (for testing purposes).

    Query Parameters:
        - notification_type: Type of notification to send (default: new_message)

    Returns:
        Send results:
        - results: Channel delivery results
        - notification_type: Type sent

    Example:
        POST /test-notification?notification_type=new_message
    """
    from app.messenger.notifications import (
        get_notification_service,
        NotificationType,
        NotificationPriority,
    )

    notification_service = get_notification_service()

    # Test data
    test_data = {
        "sender": "Test User",
        "recipient": user.email or "User",
        "preview": "This is a test notification",
        "conversation": "Test Conversation",
        "action_url": "/messenger/conversations/test",
    }

    results = await notification_service.send_notification(
        db=db,
        user_id=int(user.id),  # type: ignore
        notification_type=NotificationType(notification_type),
        data=test_data,
        priority=NotificationPriority.NORMAL,
    )

    return {
        "results": results,
        "notification_type": notification_type,
    }


# ============================================================================
# EMAIL NOTIFICATION ENDPOINTS (Task 4.2)
# ============================================================================


@router.post("/digest/send")
async def send_digest_email_now(
    frequency: str = Query(
        ..., regex="^(daily|weekly)$", description="Digest frequency"
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Send digest email immediately (for testing).

    Query Parameters:
        - frequency: Digest frequency (daily/weekly)

    Returns:
        Success status:
        - success: Whether operation succeeded
        - frequency: Digest frequency

    Example:
        POST /digest/send?frequency=daily
    """
    from app.messenger.email_service import get_email_service, DigestFrequency

    email_service = get_email_service()

    # Map frequency string to enum
    digest_freq = (
        DigestFrequency.DAILY if frequency == "daily" else DigestFrequency.WEEKLY
    )

    # Send digest
    success = await email_service.send_digest_email(
        db=db,
        user_id=int(user.id),  # type: ignore
        frequency=digest_freq,
    )

    return {
        "success": success,
        "frequency": frequency,
    }


@router.get("/email/test")
async def test_email_configuration(
    user: User = Depends(get_current_user),
):
    """
    Test email configuration (sends test email).

    Returns:
        Configuration status:
        - provider: Email provider
        - from_email: From email address
        - smtp_configured: Whether SMTP is configured

    Example:
        GET /email/test
    """
    from app.messenger.email_service import get_email_service

    email_service = get_email_service()

    # Send test email
    user_email = getattr(user, "email", None)
    if user_email and isinstance(user_email, str):
        try:
            html_body = """
            <h1>Test Email</h1>
            <p>This is a test email from DreamSeed Messenger.</p>
            <p>If you're seeing this, your email configuration is working correctly!</p>
            """

            success = await email_service.send_email(
                to_email=user_email,
                subject="Test Email - DreamSeed Messenger",
                html_body=html_body,
                text_body="This is a test email from DreamSeed Messenger.",
            )

            return {
                "success": success,
                "provider": email_service.provider.value,
                "from_email": email_service.from_email,
                "smtp_configured": bool(email_service.smtp_username),
                "test_sent_to": user.email,
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send test email: {str(e)}",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="User has no email address",
        )


# ============================================================================
# MESSAGE THREADING ENDPOINTS (Task 5.1)
# ============================================================================


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/reply",
    response_model=MessageResponse,
    status_code=status_lib.HTTP_201_CREATED,
)
async def create_reply(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    message: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Reply to a message (create a threaded reply).

    Path Parameters:
        - conversation_id: Conversation UUID
        - message_id: Parent message UUID (message being replied to)

    Request Body:
        - content: Reply text content
        - message_type: Type of message (text, image, file, system)
        - file_url: Optional file URL
        - file_size: Optional file size
        - file_name: Optional file name

    Returns:
        The created reply message with threading information

    Example:
        POST /conversations/{id}/messages/{msg_id}/reply
        {
            "content": "I agree with that!",
            "message_type": "text"
        }
    """
    from app.messenger.threading import get_threading_service

    threading_service = get_threading_service()

    try:
        reply = await threading_service.create_reply(
            db=db,
            conversation_id=conversation_id,
            parent_message_id=message_id,
            sender_id=int(user.id),  # type: ignore
            content=message.content,
            message_type=message.message_type,
            file_url=message.file_url,
            file_size=message.file_size,
            file_name=message.file_name,
        )

        # Broadcast via WebSocket
        pubsub = get_pubsub()
        await pubsub.publish_message(
            conversation_id=conversation_id,
            message_data={
                "type": "message.reply",
                "message_id": str(reply.id),
                "parent_id": str(message_id),
                "thread_id": str(reply.thread_id),
                "sender_id": user.id,
                "content": reply.content,
                "message_type": reply.message_type,
                "created_at": reply.created_at.isoformat(),
            },
        )

        return MessageResponse(
            id=reply.id,
            conversation_id=reply.conversation_id,
            sender_id=reply.sender_id,
            content=reply.content,
            message_type=reply.message_type,
            file_url=reply.file_url,
            file_size=reply.file_size,
            file_name=reply.file_name,
            created_at=reply.created_at,
            edited_at=reply.edited_at,
            deleted_at=reply.deleted_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/conversations/{conversation_id}/threads")
async def list_threads(
    conversation_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("recent", regex="^(recent|popular|oldest)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    List all threads in a conversation.

    Path Parameters:
        - conversation_id: Conversation UUID

    Query Parameters:
        - limit: Maximum number of threads (1-100, default: 20)
        - offset: Pagination offset (default: 0)
        - sort_by: Sort order - 'recent', 'popular', or 'oldest' (default: recent)

    Returns:
        List of thread summaries with metadata

    Example:
        GET /conversations/{id}/threads?sort_by=popular&limit=10
    """
    from app.messenger.threading import get_threading_service

    threading_service = get_threading_service()

    try:
        threads = await threading_service.list_threads(
            db=db,
            conversation_id=conversation_id,
            user_id=int(user.id),  # type: ignore
            limit=limit,
            offset=offset,
            sort_by=sort_by,
        )

        return {
            "threads": threads,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
        }

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: uuid.UUID,
    include_deleted: bool = Query(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get a complete thread with all replies (nested structure).

    Path Parameters:
        - thread_id: Root message UUID

    Query Parameters:
        - include_deleted: Include soft-deleted messages (default: false)

    Returns:
        Nested thread structure with all replies

    Example:
        GET /threads/{id}
        Response:
        {
            "id": "uuid",
            "content": "Root message",
            "reply_count": 5,
            "replies": [
                {
                    "id": "uuid",
                    "content": "Reply 1",
                    "replies": [...]
                }
            ]
        }
    """
    from app.messenger.threading import get_threading_service

    threading_service = get_threading_service()

    try:
        thread = await threading_service.get_thread(
            db=db,
            thread_root_id=thread_id,
            user_id=int(user.id),  # type: ignore
            include_deleted=include_deleted,
        )

        return thread

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/threads/{thread_id}/summary")
async def get_thread_summary(
    thread_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get thread summary (metadata without full reply tree).

    Path Parameters:
        - thread_id: Root message UUID

    Returns:
        Thread summary with reply count, participants, latest reply

    Example:
        GET /threads/{id}/summary
        Response:
        {
            "thread_id": "uuid",
            "content": "Root message",
            "reply_count": 15,
            "unique_participants": 5,
            "latest_reply": {...}
        }
    """
    from app.messenger.threading import get_threading_service

    threading_service = get_threading_service()

    try:
        summary = await threading_service.get_thread_summary(
            db=db,
            thread_root_id=thread_id,
            user_id=int(user.id),  # type: ignore
        )

        return summary

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/threads/{thread_id}/participants")
async def get_thread_participants(
    thread_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get list of users who have participated in a thread.

    Path Parameters:
        - thread_id: Root message UUID

    Returns:
        List of user IDs who have replied in the thread

    Example:
        GET /threads/{id}/participants
        Response:
        {
            "thread_id": "uuid",
            "participants": [1, 5, 12, 23]
        }
    """
    from app.messenger.threading import get_threading_service

    threading_service = get_threading_service()

    try:
        participants = await threading_service.get_thread_participants(
            db=db,
            thread_root_id=thread_id,
            user_id=int(user.id),  # type: ignore
        )

        return {
            "thread_id": str(thread_id),
            "participants": participants,
        }

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/threads/{thread_id}", status_code=status_lib.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Soft delete an entire thread (root message + all replies).

    Path Parameters:
        - thread_id: Root message UUID

    Returns:
        HTTP 204 No Content on success

    Note:
        - Only the thread creator or conversation admin can delete
        - This performs a soft delete (sets deleted_at timestamp)
        - All replies in the thread are also soft deleted

    Example:
        DELETE /threads/{id}
    """
    from app.messenger.threading import get_threading_service

    threading_service = get_threading_service()

    # Check if user is admin
    conversation_result = await db.execute(
        select(Message.conversation_id).where(Message.id == thread_id)
    )
    conversation_id = conversation_result.scalar_one_or_none()

    if not conversation_id:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Check admin status
    participant_result = await db.execute(
        select(ConversationParticipant).where(
            and_(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user.id,
            )
        )
    )
    participant = participant_result.scalar_one_or_none()
    is_admin = participant and participant.role == "admin"

    try:
        await threading_service.delete_thread(
            db=db,
            thread_root_id=thread_id,
            user_id=int(user.id),  # type: ignore
            is_admin=is_admin,
        )

        # Broadcast deletion
        pubsub = get_pubsub()
        await pubsub.publish_message(
            conversation_id=conversation_id,
            message_data={
                "type": "thread.deleted",
                "thread_id": str(thread_id),
                "deleted_by": int(user.id),  # type: ignore
            },
        )

        return None

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ============================================================================
# WebRTC Signaling Handlers
# ============================================================================


async def handle_webrtc_renegotiate(
    websocket: WebSocket,
    user_id: int,
    call_id: uuid.UUID,
    signaling_data: dict,
):
    """
    Handle WebRTC renegotiation request.

    Used when media tracks are added/removed (e.g., screen sharing starts/stops).

    Args:
        websocket: WebSocket connection
        user_id: User requesting renegotiation
        call_id: Call UUID
        signaling_data: Contains reason and optional new SDP offer
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.messenger_models import Call, CallParticipant

        async with AsyncSessionLocal() as db:
            # Verify user is participant
            stmt = select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id,
                )
            )
            result = await db.execute(stmt)
            participant = result.scalar_one_or_none()

            if not participant:
                await websocket.send_json(
                    {
                        "type": "error",
                        "event": "webrtc.renegotiate",
                        "message": "Not a participant of this call",
                    }
                )
                return

            # Get call info
            call_result = await db.execute(select(Call).where(Call.id == call_id))
            call = call_result.scalar_one_or_none()

            if not call:
                await websocket.send_json(
                    {
                        "type": "error",
                        "event": "webrtc.renegotiate",
                        "message": "Call not found",
                    }
                )
                return

            # Update user activity
            await update_user_activity(user_id)

            # Broadcast renegotiation request
            pubsub = get_pubsub()
            await pubsub.publish_message(
                conversation_id=call.conversation_id,
                message_data={
                    "type": "webrtc.renegotiate",
                    "call_id": str(call_id),
                    "from_user_id": user_id,
                    "reason": signaling_data.get("reason", "unknown"),
                    "sdp": signaling_data.get("sdp"),  # Optional new offer
                },
            )

            # Send acknowledgment
            await websocket.send_json(
                {
                    "type": "webrtc.renegotiate.sent",
                    "call_id": str(call_id),
                }
            )

            logger.info(
                f"WebRTC renegotiation requested for call {call_id} by user {user_id}"
            )

    except Exception as e:
        logger.error(f"Error in handle_webrtc_renegotiate: {e}")
        await websocket.send_json(
            {
                "type": "error",
                "event": "webrtc.renegotiate",
                "message": f"Failed to request renegotiation: {str(e)}",
            }
        )


async def handle_webrtc_connection_state(
    websocket: WebSocket,
    user_id: int,
    call_id: uuid.UUID,
    state_data: dict,
):
    """
    Handle WebRTC connection state updates.

    Tracks connection quality and status for monitoring and analytics.

    Args:
        websocket: WebSocket connection
        user_id: User reporting state
        call_id: Call UUID
        state_data: Contains 'state', 'quality', and optional metrics
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.messenger_models import CallParticipant
        from app.messenger.calls import ConnectionQuality

        async with AsyncSessionLocal() as db:
            # Get participant
            stmt = select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id,
                )
            )
            result = await db.execute(stmt)
            participant = result.scalar_one_or_none()

            if not participant:
                return  # Silently ignore for non-participants

            # Update connection quality if provided
            quality = state_data.get("quality")
            if quality in [q.value for q in ConnectionQuality]:
                participant.connection_quality = quality
                await db.commit()

            # Update user activity
            await update_user_activity(user_id)

            # Log connection state for monitoring
            logger.info(
                f"WebRTC connection state for call {call_id} user {user_id}: "
                f"state={state_data.get('state')}, quality={quality}"
            )

            # Track analytics event (CALL_QUALITY_UPDATE not yet implemented in AnalyticsEventType)
            # TODO: Add CALL_QUALITY_UPDATE to AnalyticsEventType enum
            # from app.messenger.analytics import (
            #     AnalyticsEventType,
            #     get_analytics_service,
            # )
            #
            # analytics = get_analytics_service()
            # await analytics.track_event(
            #     event_type=AnalyticsEventType.CALL_QUALITY_UPDATE,
            #     user_id=user_id,
            #     metadata={
            #         "call_id": str(call_id),
            #         "state": state_data.get("state"),
            #         "quality": quality,
            #         "metrics": state_data.get("metrics", {}),
            #     },
            # )

    except Exception as e:
        logger.error(f"Error in handle_webrtc_connection_state: {e}")
