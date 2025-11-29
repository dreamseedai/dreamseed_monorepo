"""
Message Reactions Service

This module handles emoji reactions on messages for the messenger system.
Supports adding, removing, and querying emoji reactions with Unicode support.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.messenger_models import (
    ConversationParticipant,
    Message,
    MessageReaction,
)

logger = logging.getLogger(__name__)


# Popular emoji mappings (shortcode -> unicode)
EMOJI_MAP = {
    # Smileys & Emotion
    "smile": "😊",
    "grin": "😀",
    "joy": "😂",
    "heart_eyes": "😍",
    "wink": "😉",
    "blush": "😊",
    "thinking": "🤔",
    "laughing": "😆",
    "rofl": "🤣",
    "sweat_smile": "😅",
    "cry": "😢",
    "sob": "😭",
    "angry": "😠",
    "rage": "😡",
    "triumph": "😤",
    "confused": "😕",
    "worried": "😟",
    "disappointed": "😞",
    "expressionless": "😑",
    "neutral_face": "😐",
    "rolling_eyes": "🙄",
    "smirk": "😏",
    "persevere": "😣",
    "relieved": "😌",
    "pensive": "😔",
    "sleepy": "😪",
    "sleeping": "😴",
    "mask": "😷",
    "sunglasses": "😎",
    "nerd": "🤓",
    "partying": "🥳",
    "star_struck": "🤩",
    # Hearts
    "heart": "❤️",
    "orange_heart": "🧡",
    "yellow_heart": "💛",
    "green_heart": "💚",
    "blue_heart": "💙",
    "purple_heart": "💜",
    "black_heart": "🖤",
    "broken_heart": "💔",
    "two_hearts": "💕",
    "sparkling_heart": "💖",
    "heartpulse": "💗",
    "cupid": "💘",
    "revolving_hearts": "💞",
    "heart_decoration": "💟",
    # Hands
    "thumbs_up": "👍",
    "thumbs_down": "👎",
    "clap": "👏",
    "raised_hands": "🙌",
    "ok_hand": "👌",
    "victory": "✌️",
    "crossed_fingers": "🤞",
    "love_you": "🤟",
    "metal": "🤘",
    "pray": "🙏",
    "handshake": "🤝",
    "muscle": "💪",
    "raised_hand": "✋",
    "wave": "👋",
    "call_me": "🤙",
    "point_left": "👈",
    "point_right": "👉",
    "point_up": "☝️",
    "point_down": "👇",
    # Nature
    "fire": "🔥",
    "star": "⭐",
    "sparkles": "✨",
    "zap": "⚡",
    "boom": "💥",
    "tada": "🎉",
    "confetti": "🎊",
    "balloon": "🎈",
    "rocket": "🚀",
    "100": "💯",
    "medal": "🏅",
    "trophy": "🏆",
    "crown": "👑",
    # Objects
    "bulb": "💡",
    "bell": "🔔",
    "mega": "📣",
    "loudspeaker": "📢",
    "speech_balloon": "💬",
    "thought_balloon": "💭",
    "zzz": "💤",
    "eyes": "👀",
    "brain": "🧠",
    # Symbols
    "check": "✅",
    "x": "❌",
    "warning": "⚠️",
    "no_entry": "⛔",
    "question": "❓",
    "grey_question": "❔",
    "exclamation": "❗",
    "grey_exclamation": "❕",
    "heavy_plus_sign": "➕",
    "heavy_minus_sign": "➖",
    "infinity": "♾️",
}


class ReactionsService:
    """
    Service for managing message reactions.

    Features:
    - Add emoji reactions to messages
    - Remove reactions
    - Get reaction counts and lists
    - Get popular reactions
    - Reaction summaries
    """

    @staticmethod
    async def add_reaction(
        db: AsyncSession,
        message_id: UUID,
        user_id: int,
        emoji: str,
    ) -> MessageReaction:
        """
        Add an emoji reaction to a message.

        Args:
            db: Database session
            message_id: ID of the message to react to
            user_id: ID of the user adding the reaction
            emoji: Emoji shortcode (e.g., "thumbs_up") or unicode (e.g., "👍")

        Returns:
            The created reaction

        Raises:
            ValueError: If message not found, user not participant, or reaction already exists
        """
        # Verify message exists
        message_result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        message = message_result.scalar_one_or_none()

        if not message:
            raise ValueError(f"Message {message_id} not found")

        # Verify user is participant in conversation
        participant_result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == message.conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
        )
        participant = participant_result.scalar_one_or_none()

        if not participant:
            raise ValueError("User is not a participant in this conversation")

        # Convert emoji shortcode to unicode if in map
        emoji_unicode = EMOJI_MAP.get(emoji, emoji)

        # Check if reaction already exists
        existing_result = await db.execute(
            select(MessageReaction).where(
                and_(
                    MessageReaction.message_id == message_id,
                    MessageReaction.user_id == user_id,
                    MessageReaction.emoji == emoji,
                )
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise ValueError(f"User has already reacted with {emoji}")

        # Create reaction
        reaction = MessageReaction(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
            emoji_unicode=emoji_unicode,
        )

        db.add(reaction)
        await db.commit()
        await db.refresh(reaction)

        logger.info(f"Added reaction {emoji} to message {message_id} by user {user_id}")

        return reaction

    @staticmethod
    async def remove_reaction(
        db: AsyncSession,
        message_id: UUID,
        user_id: int,
        emoji: str,
    ) -> bool:
        """
        Remove an emoji reaction from a message.

        Args:
            db: Database session
            message_id: ID of the message
            user_id: ID of the user removing the reaction
            emoji: Emoji shortcode or unicode

        Returns:
            True if reaction was removed, False if not found
        """
        # Find and delete reaction
        result = await db.execute(
            select(MessageReaction).where(
                and_(
                    MessageReaction.message_id == message_id,
                    MessageReaction.user_id == user_id,
                    MessageReaction.emoji == emoji,
                )
            )
        )
        reaction = result.scalar_one_or_none()

        if not reaction:
            return False

        await db.delete(reaction)
        await db.commit()

        logger.info(
            f"Removed reaction {emoji} from message {message_id} by user {user_id}"
        )

        return True

    @staticmethod
    async def toggle_reaction(
        db: AsyncSession,
        message_id: UUID,
        user_id: int,
        emoji: str,
    ) -> Dict:
        """
        Toggle a reaction (add if not exists, remove if exists).

        Args:
            db: Database session
            message_id: ID of the message
            user_id: ID of the user
            emoji: Emoji shortcode or unicode

        Returns:
            Dictionary with action taken and reaction data
        """
        # Check if reaction exists
        result = await db.execute(
            select(MessageReaction).where(
                and_(
                    MessageReaction.message_id == message_id,
                    MessageReaction.user_id == user_id,
                    MessageReaction.emoji == emoji,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Remove
            await db.delete(existing)
            await db.commit()

            return {
                "action": "removed",
                "message_id": str(message_id),
                "emoji": emoji,
            }
        else:
            # Add
            try:
                reaction = await ReactionsService.add_reaction(
                    db=db,
                    message_id=message_id,
                    user_id=user_id,
                    emoji=emoji,
                )

                return {
                    "action": "added",
                    "message_id": str(message_id),
                    "emoji": emoji,
                    "emoji_unicode": reaction.emoji_unicode,
                    "reaction_id": reaction.id,
                }
            except ValueError as e:
                raise e

    @staticmethod
    async def get_message_reactions(
        db: AsyncSession,
        message_id: UUID,
        user_id: int,
    ) -> Dict:
        """
        Get all reactions on a message grouped by emoji.

        Args:
            db: Database session
            message_id: ID of the message
            user_id: ID of the requesting user (for permission check)

        Returns:
            Dictionary with reactions grouped by emoji

        Raises:
            ValueError: If user is not a participant
        """
        # Verify message exists
        message_result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        message = message_result.scalar_one_or_none()

        if not message:
            raise ValueError(f"Message {message_id} not found")

        # Verify user is participant
        participant_result = await db.execute(
            select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == message.conversation_id,
                    ConversationParticipant.user_id == user_id,
                )
            )
        )
        if not participant_result.scalar_one_or_none():
            raise ValueError("User is not a participant")

        # Get all reactions
        reactions_result = await db.execute(
            select(MessageReaction)
            .where(MessageReaction.message_id == message_id)
            .order_by(MessageReaction.created_at)
        )
        reactions = reactions_result.scalars().all()

        # Group by emoji
        grouped: Dict[str, Dict] = {}

        for reaction in reactions:
            if reaction.emoji not in grouped:
                grouped[reaction.emoji] = {
                    "emoji": reaction.emoji,
                    "emoji_unicode": reaction.emoji_unicode,
                    "count": 0,
                    "users": [],
                    "user_reacted": False,
                }

            grouped[reaction.emoji]["count"] += 1
            grouped[reaction.emoji]["users"].append(reaction.user_id)

            if reaction.user_id == user_id:
                grouped[reaction.emoji]["user_reacted"] = True

        return {
            "message_id": str(message_id),
            "total_reactions": len(reactions),
            "reactions": list(grouped.values()),
        }

    @staticmethod
    async def get_user_reactions(
        db: AsyncSession,
        user_id: int,
        conversation_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Get reactions by a specific user.

        Args:
            db: Database session
            user_id: ID of the user
            conversation_id: Optional conversation filter
            limit: Maximum number of reactions to return

        Returns:
            List of user's reactions
        """
        query = select(MessageReaction).where(MessageReaction.user_id == user_id)

        # Filter by conversation if provided
        if conversation_id:
            query = query.join(Message).where(
                Message.conversation_id == conversation_id
            )

        query = query.order_by(desc(MessageReaction.created_at)).limit(limit)

        result = await db.execute(query)
        reactions = result.scalars().all()

        return [
            {
                "id": reaction.id,
                "message_id": str(reaction.message_id),
                "emoji": reaction.emoji,
                "emoji_unicode": reaction.emoji_unicode,
                "created_at": reaction.created_at.isoformat(),
            }
            for reaction in reactions
        ]

    @staticmethod
    async def get_popular_reactions(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: int,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get most popular emoji reactions in a conversation.

        Args:
            db: Database session
            conversation_id: ID of the conversation
            user_id: ID of the requesting user
            limit: Maximum number of emoji to return

        Returns:
            List of popular reactions with counts
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

        # Query for popular reactions
        result = await db.execute(
            select(
                MessageReaction.emoji,
                MessageReaction.emoji_unicode,
                func.count(MessageReaction.id).label("count"),
            )
            .join(Message)
            .where(Message.conversation_id == conversation_id)
            .group_by(MessageReaction.emoji, MessageReaction.emoji_unicode)
            .order_by(desc("count"))
            .limit(limit)
        )

        popular = result.fetchall()

        return [
            {
                "emoji": row[0],
                "emoji_unicode": row[1],
                "count": row[2],
            }
            for row in popular
        ]

    @staticmethod
    async def get_reaction_summary(
        db: AsyncSession,
        message_id: UUID,
    ) -> Dict:
        """
        Get quick summary of reactions on a message (count only).

        Args:
            db: Database session
            message_id: ID of the message

        Returns:
            Reaction count summary
        """
        # Get message with reaction_count
        result = await db.execute(
            select(Message.reaction_count).where(Message.id == message_id)
        )
        reaction_count = result.scalar_one_or_none()

        if reaction_count is None:
            raise ValueError(f"Message {message_id} not found")

        # Get unique emoji count
        emoji_result = await db.execute(
            select(func.count(func.distinct(MessageReaction.emoji))).where(
                MessageReaction.message_id == message_id
            )
        )
        unique_emoji_count = emoji_result.scalar() or 0

        return {
            "message_id": str(message_id),
            "total_reactions": reaction_count,
            "unique_emoji": unique_emoji_count,
        }

    @staticmethod
    def get_emoji_unicode(emoji: str) -> str:
        """
        Convert emoji shortcode to unicode.

        Args:
            emoji: Emoji shortcode or unicode

        Returns:
            Unicode representation
        """
        return EMOJI_MAP.get(emoji, emoji)

    @staticmethod
    def get_supported_emoji() -> List[Dict]:
        """
        Get list of all supported emoji shortcodes.

        Returns:
            List of emoji with shortcode and unicode
        """
        return [
            {"shortcode": shortcode, "unicode": unicode_char}
            for shortcode, unicode_char in sorted(EMOJI_MAP.items())
        ]


# Singleton instance
_reactions_service: Optional[ReactionsService] = None


def get_reactions_service() -> ReactionsService:
    """Get singleton instance of ReactionsService."""
    global _reactions_service
    if _reactions_service is None:
        _reactions_service = ReactionsService()
    return _reactions_service
