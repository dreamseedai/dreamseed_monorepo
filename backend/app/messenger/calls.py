"""
Call Service for Voice/Video Calling

This module handles call lifecycle management, participant tracking,
and WebRTC signaling for voice and video calls.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_models import Call, CallParticipant, ConversationParticipant

logger = logging.getLogger(__name__)


class CallType(str, Enum):
    """Call type enumeration."""

    AUDIO = "audio"
    VIDEO = "video"


class CallStatus(str, Enum):
    """Call status enumeration."""

    INITIATED = "initiated"
    RINGING = "ringing"
    ACTIVE = "active"
    ENDED = "ended"
    MISSED = "missed"
    REJECTED = "rejected"
    FAILED = "failed"


class EndReason(str, Enum):
    """Call end reason enumeration."""

    COMPLETED = "completed"
    DECLINED = "declined"
    NO_ANSWER = "no_answer"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ConnectionQuality(str, Enum):
    """Connection quality enumeration."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class CallService:
    """
    Service for managing voice/video calls.

    Features:
    - Initiate audio/video calls
    - Manage call participants
    - Track call status and duration
    - Handle call ending/rejection
    - Call history and statistics
    """

    @staticmethod
    async def initiate_call(
        db: AsyncSession,
        conversation_id: UUID,
        initiator_id: int,
        call_type: CallType,
        invited_user_ids: List[int],
    ) -> Call:
        """
        Initiate a new call.

        Args:
            db: Database session
            conversation_id: ID of the conversation
            initiator_id: ID of the user initiating the call
            call_type: Type of call (audio/video)
            invited_user_ids: List of user IDs to invite

        Returns:
            Created call object

        Raises:
            ValueError: If conversation not found or user not a participant
        """
        # Verify initiator is a participant
        participant_check = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == initiator_id,
                )
            )
        )
        if not participant_check.scalar_one_or_none():
            raise ValueError("Initiator is not a participant in this conversation")

        # Check for active call in this conversation
        active_call_check = await db.execute(
            select(Call).where(
                and_(
                    Call.conversation_id == conversation_id,
                    Call.status.in_(
                        [
                            CallStatus.INITIATED.value,
                            CallStatus.RINGING.value,
                            CallStatus.ACTIVE.value,
                        ]
                    ),
                )
            )
        )
        if active_call_check.scalar_one_or_none():
            raise ValueError("There is already an active call in this conversation")

        # Create call
        call = Call(
            conversation_id=conversation_id,
            initiator_id=initiator_id,
            call_type=call_type.value,
            status=CallStatus.INITIATED.value,
        )
        db.add(call)
        await db.flush()  # Get call ID

        # Add initiator as participant
        initiator_participant = CallParticipant(
            call_id=call.id,
            user_id=initiator_id,
            is_initiator=True,
            answered=True,  # Initiator automatically joins
            video_enabled=(call_type == CallType.VIDEO),
            audio_enabled=True,
            joined_at=datetime.utcnow(),
        )
        db.add(initiator_participant)

        # Add invited participants
        for user_id in invited_user_ids:
            if user_id == initiator_id:
                continue  # Skip initiator

            # Verify they're conversation participants
            participant_check = await db.execute(
                select(ConversationParticipant).where(
                    and_(
                        ConversationParticipant.conversation_id == conversation_id,
                        ConversationParticipant.user_id == user_id,
                    )
                )
            )
            if not participant_check.scalar_one_or_none():
                logger.warning(
                    f"User {user_id} is not a conversation participant, skipping"
                )
                continue

            participant = CallParticipant(
                call_id=call.id,
                user_id=user_id,
                is_initiator=False,
                answered=False,
                video_enabled=False,
                audio_enabled=False,
            )
            db.add(participant)

        # Update call status to ringing
        call.status = CallStatus.RINGING.value

        await db.commit()
        await db.refresh(call)

        logger.info(
            f"Call initiated: {call.id}, type={call_type.value}, "
            f"conversation={conversation_id}, initiator={initiator_id}"
        )

        return call

    @staticmethod
    async def answer_call(
        db: AsyncSession,
        call_id: UUID,
        user_id: int,
        video_enabled: bool = False,
        peer_id: Optional[str] = None,
    ) -> CallParticipant:
        """
        Answer a call.

        Args:
            db: Database session
            call_id: ID of the call
            user_id: ID of the user answering
            video_enabled: Whether user has video enabled
            peer_id: WebRTC peer identifier

        Returns:
            Updated call participant

        Raises:
            ValueError: If call not found or user not invited
        """
        # Get call
        call_result = await db.execute(select(Call).where(Call.id == call_id))
        call = call_result.scalar_one_or_none()

        if not call:
            raise ValueError(f"Call {call_id} not found")

        if call.status not in [
            CallStatus.INITIATED.value,
            CallStatus.RINGING.value,
            CallStatus.ACTIVE.value,
        ]:
            raise ValueError(f"Call is not active (status: {call.status})")

        # Get participant
        participant_result = await db.execute(
            select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id,
                )
            )
        )
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise ValueError(f"User {user_id} is not invited to this call")

        if participant.answered:
            raise ValueError("User has already answered this call")

        # Update participant
        participant.answered = True
        participant.joined_at = datetime.utcnow()
        participant.video_enabled = video_enabled
        participant.audio_enabled = True
        participant.peer_id = peer_id

        # Update call status to active if this is the first answer
        if call.status != CallStatus.ACTIVE.value:
            call.status = CallStatus.ACTIVE.value
            call.answered_at = datetime.utcnow()

        await db.commit()
        await db.refresh(participant)

        logger.info(f"Call answered: {call_id}, user={user_id}, video={video_enabled}")

        return participant

    @staticmethod
    async def reject_call(
        db: AsyncSession,
        call_id: UUID,
        user_id: int,
    ) -> Call:
        """
        Reject a call invitation.

        Args:
            db: Database session
            call_id: ID of the call
            user_id: ID of the user rejecting

        Returns:
            Updated call object

        Raises:
            ValueError: If call not found or user not invited
        """
        # Get call
        call_result = await db.execute(select(Call).where(Call.id == call_id))
        call = call_result.scalar_one_or_none()

        if not call:
            raise ValueError(f"Call {call_id} not found")

        # Get participant
        participant_result = await db.execute(
            select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id,
                )
            )
        )
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise ValueError(f"User {user_id} is not invited to this call")

        if participant.is_initiator:
            # If initiator rejects, end the call
            return await CallService.end_call(
                db=db,
                call_id=call_id,
                user_id=user_id,
                end_reason=EndReason.DECLINED,
            )

        # Check if all non-initiator participants have rejected
        all_participants_result = await db.execute(
            select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.is_initiator == False,
                )
            )
        )
        all_participants = all_participants_result.scalars().all()

        # If everyone rejected, end call
        if all(p.user_id == user_id or not p.answered for p in all_participants):
            call.status = CallStatus.REJECTED.value
            call.ended_at = datetime.utcnow()
            call.end_reason = EndReason.DECLINED.value

            await db.commit()
            await db.refresh(call)

            logger.info(f"Call rejected by all participants: {call_id}")

        return call

    @staticmethod
    async def end_call(
        db: AsyncSession,
        call_id: UUID,
        user_id: int,
        end_reason: EndReason = EndReason.COMPLETED,
    ) -> Call:
        """
        End an active call.

        Args:
            db: Database session
            call_id: ID of the call
            user_id: ID of the user ending the call
            end_reason: Reason for ending

        Returns:
            Updated call object

        Raises:
            ValueError: If call not found
        """
        # Get call
        call_result = await db.execute(select(Call).where(Call.id == call_id))
        call = call_result.scalar_one_or_none()

        if not call:
            raise ValueError(f"Call {call_id} not found")

        if call.status == CallStatus.ENDED.value:
            return call  # Already ended

        # Update call
        call.status = CallStatus.ENDED.value
        call.ended_at = datetime.utcnow()
        call.end_reason = end_reason.value

        # Calculate duration
        answered_at = call.answered_at
        ended_at = call.ended_at
        if answered_at is not None and ended_at is not None:
            duration = (ended_at - answered_at).total_seconds()
            call.duration_seconds = int(duration)

        # Update all participants' left_at and duration
        participants_result = await db.execute(
            select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.answered == True,
                    CallParticipant.left_at == None,
                )
            )
        )
        participants = participants_result.scalars().all()

        for participant in participants:
            participant.left_at = call.ended_at
            joined_at = participant.joined_at
            left_at = participant.left_at
            if joined_at is not None and left_at is not None:
                duration = (left_at - joined_at).total_seconds()
                participant.duration_seconds = int(duration)

        await db.commit()
        await db.refresh(call)

        logger.info(
            f"Call ended: {call_id}, reason={end_reason.value}, duration={call.duration_seconds}s"
        )

        return call

    @staticmethod
    async def leave_call(
        db: AsyncSession,
        call_id: UUID,
        user_id: int,
    ) -> CallParticipant:
        """
        Leave a call (participant leaves but call continues).

        Args:
            db: Database session
            call_id: ID of the call
            user_id: ID of the user leaving

        Returns:
            Updated call participant

        Raises:
            ValueError: If call not found or user not in call
        """
        # Get participant
        participant_result = await db.execute(
            select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id,
                )
            )
        )
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise ValueError(f"User {user_id} is not in call {call_id}")

        if participant.left_at:
            return participant  # Already left

        # Update participant
        participant.left_at = datetime.utcnow()

        joined_at = participant.joined_at
        left_at = participant.left_at
        if joined_at is not None and left_at is not None:
            duration = (left_at - joined_at).total_seconds()
            participant.duration_seconds = int(duration)

        # Check if all participants have left
        all_participants_result = await db.execute(
            select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.answered == True,
                )
            )
        )
        all_participants = all_participants_result.scalars().all()

        if all(p.left_at is not None for p in all_participants):
            # Everyone left, end the call
            await CallService.end_call(
                db=db,
                call_id=call_id,
                user_id=user_id,
                end_reason=EndReason.COMPLETED,
            )

        await db.commit()
        await db.refresh(participant)

        logger.info(f"User left call: {call_id}, user={user_id}")

        return participant

    @staticmethod
    async def update_participant_media(
        db: AsyncSession,
        call_id: UUID,
        user_id: int,
        video_enabled: Optional[bool] = None,
        audio_enabled: Optional[bool] = None,
        screen_share_enabled: Optional[bool] = None,
    ) -> CallParticipant:
        """
        Update participant's media settings (video/audio/screen share).

        Args:
            db: Database session
            call_id: ID of the call
            user_id: ID of the user
            video_enabled: Whether video is enabled
            audio_enabled: Whether audio is enabled
            screen_share_enabled: Whether screen sharing is enabled

        Returns:
            Updated call participant

        Raises:
            ValueError: If call not found or user not in call
        """
        # Get participant
        participant_result = await db.execute(
            select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id,
                )
            )
        )
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise ValueError(f"User {user_id} is not in call {call_id}")

        # Update media settings
        if video_enabled is not None:
            participant.video_enabled = video_enabled
        if audio_enabled is not None:
            participant.audio_enabled = audio_enabled
        if screen_share_enabled is not None:
            participant.screen_share_enabled = screen_share_enabled

        await db.commit()
        await db.refresh(participant)

        return participant

    @staticmethod
    async def update_connection_quality(
        db: AsyncSession,
        call_id: UUID,
        user_id: int,
        quality: ConnectionQuality,
    ) -> CallParticipant:
        """
        Update participant's connection quality.

        Args:
            db: Database session
            call_id: ID of the call
            user_id: ID of the user
            quality: Connection quality

        Returns:
            Updated call participant
        """
        # Get participant
        participant_result = await db.execute(
            select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id,
                )
            )
        )
        participant = participant_result.scalar_one_or_none()

        if participant:
            participant.connection_quality = quality.value
            await db.commit()
            await db.refresh(participant)

        return participant

    @staticmethod
    async def get_call(
        db: AsyncSession,
        call_id: UUID,
        user_id: int,
    ) -> Optional[Call]:
        """
        Get call details.

        Args:
            db: Database session
            call_id: ID of the call
            user_id: ID of the requesting user

        Returns:
            Call object or None

        Raises:
            ValueError: If user is not a participant
        """
        # Get call with participants
        call_result = await db.execute(select(Call).where(Call.id == call_id))
        call = call_result.scalar_one_or_none()

        if not call:
            return None

        # Verify user is a participant
        participant_check = await db.execute(
            select(CallParticipant).where(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id,
                )
            )
        )
        if not participant_check.scalar_one_or_none():
            raise ValueError("User is not a participant in this call")

        return call

    @staticmethod
    async def get_active_call(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: int,
    ) -> Optional[Call]:
        """
        Get active call in a conversation.

        Args:
            db: Database session
            conversation_id: ID of the conversation
            user_id: ID of the requesting user

        Returns:
            Active call or None
        """
        call_result = await db.execute(
            select(Call).where(
                and_(
                    Call.conversation_id == conversation_id,
                    Call.status.in_(
                        [
                            CallStatus.INITIATED.value,
                            CallStatus.RINGING.value,
                            CallStatus.ACTIVE.value,
                        ]
                    ),
                )
            )
        )
        return call_result.scalar_one_or_none()

    @staticmethod
    async def get_call_history(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Call]:
        """
        Get call history for a conversation.

        Args:
            db: Database session
            conversation_id: ID of the conversation
            user_id: ID of the requesting user
            limit: Maximum number of calls to return
            offset: Offset for pagination

        Returns:
            List of calls
        """
        # Verify user is a conversation participant
        participant_check = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
        )
        if not participant_check.scalar_one_or_none():
            raise ValueError("User is not a participant in this conversation")

        # Get call history
        calls_result = await db.execute(
            select(Call)
            .where(Call.conversation_id == conversation_id)
            .order_by(desc(Call.started_at))
            .limit(limit)
            .offset(offset)
        )
        return list(calls_result.scalars().all())

    @staticmethod
    async def get_call_participants(
        db: AsyncSession,
        call_id: UUID,
    ) -> List[CallParticipant]:
        """
        Get all participants in a call.

        Args:
            db: Database session
            call_id: ID of the call

        Returns:
            List of call participants
        """
        participants_result = await db.execute(
            select(CallParticipant).where(CallParticipant.call_id == call_id)
        )
        return list(participants_result.scalars().all())


# Singleton instance
_call_service: Optional[CallService] = None


def get_call_service() -> CallService:
    """Get singleton instance of CallService."""
    global _call_service
    if _call_service is None:
        _call_service = CallService()
    return _call_service
