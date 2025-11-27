"""
Redis Pub/Sub manager for real-time messaging

Handles message broadcasting across multiple server instances.
Uses Redis Pub/Sub for horizontal scaling.

Channel naming convention:
- conversation:{conversation_id} - Messages for specific conversation
- user:{user_id} - Personal notifications for user
- zone:{zone_id} - Zone-wide announcements
- online:status - User online/offline status updates

Usage:
    from app.messenger.pubsub import MessengerPubSub

    pubsub = MessengerPubSub()

    # Publish message to conversation
    await pubsub.publish_message(conversation_id, message_data)

    # Subscribe to conversation (in WebSocket handler)
    async for message in pubsub.subscribe_conversation(conversation_id):
        await websocket.send_json(message)
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Literal, Optional
from uuid import UUID

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class MessengerPubSub:
    """
    Redis Pub/Sub manager for messenger system.

    Handles:
    - Message broadcasting to conversation participants
    - User-specific notifications
    - Zone-wide announcements
    - Online status updates
    """

    def __init__(self):
        """Initialize Pub/Sub manager"""
        self.redis_client = get_redis()

    # ========================================================================
    # Channel Name Helpers
    # ========================================================================

    @staticmethod
    def conversation_channel(conversation_id: UUID | str) -> str:
        """Get channel name for a conversation"""
        return f"conversation:{conversation_id}"

    @staticmethod
    def user_channel(user_id: int) -> str:
        """Get channel name for user notifications"""
        return f"user:{user_id}"

    @staticmethod
    def zone_channel(zone_id: int) -> str:
        """Get channel name for zone announcements"""
        return f"zone:{zone_id}"

    @staticmethod
    def online_status_channel() -> str:
        """Get channel name for online status updates"""
        return "online:status"

    # ========================================================================
    # Publishing Methods
    # ========================================================================

    async def publish_message(
        self,
        conversation_id: UUID | str,
        message_data: dict[str, Any],
    ) -> int:
        """
        Publish a new message to conversation channel.

        Args:
            conversation_id: Conversation UUID
            message_data: Message payload (will be JSON serialized)

        Returns:
            int: Number of subscribers who received the message

        Example:
            await pubsub.publish_message(
                conversation_id="123e4567-...",
                message_data={
                    "id": "msg-uuid",
                    "sender_id": 1,
                    "content": "Hello!",
                    "created_at": "2025-11-26T10:00:00Z",
                }
            )
        """
        channel = self.conversation_channel(conversation_id)
        payload = json.dumps(message_data, default=str)

        try:
            num_subscribers = await self.redis_client.publish(channel, payload)
            logger.info(
                f"Published message to {channel} " f"({num_subscribers} subscribers)"
            )
            return num_subscribers
        except Exception as e:
            logger.error(f"Failed to publish message to {channel}: {e}")
            raise

    async def publish_user_notification(
        self,
        user_id: int,
        notification_data: dict[str, Any],
    ) -> int:
        """
        Publish notification to user's personal channel.

        Args:
            user_id: User ID
            notification_data: Notification payload

        Returns:
            int: Number of subscribers

        Example:
            await pubsub.publish_user_notification(
                user_id=1,
                notification_data={
                    "type": "new_message",
                    "conversation_id": "123e4567-...",
                    "sender_name": "선생님",
                    "preview": "새 메시지가 도착했습니다",
                }
            )
        """
        channel = self.user_channel(user_id)
        payload = json.dumps(notification_data, default=str)

        try:
            num_subscribers = await self.redis_client.publish(channel, payload)
            logger.debug(
                f"Published notification to {channel} "
                f"({num_subscribers} subscribers)"
            )
            return num_subscribers
        except Exception as e:
            logger.error(f"Failed to publish notification to {channel}: {e}")
            raise

    async def publish_zone_announcement(
        self,
        zone_id: int,
        announcement_data: dict[str, Any],
    ) -> int:
        """
        Publish announcement to all users in a zone.

        Args:
            zone_id: Zone ID
            announcement_data: Announcement payload

        Returns:
            int: Number of subscribers
        """
        channel = self.zone_channel(zone_id)
        payload = json.dumps(announcement_data, default=str)

        try:
            num_subscribers = await self.redis_client.publish(channel, payload)
            logger.info(
                f"Published announcement to {channel} "
                f"({num_subscribers} subscribers)"
            )
            return num_subscribers
        except Exception as e:
            logger.error(f"Failed to publish announcement to {channel}: {e}")
            raise

    async def publish_online_status(
        self,
        user_id: int,
        status: Literal["online", "offline", "away"],
        metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        """
        Publish user online/offline/away status update.

        Args:
            user_id: User ID
            status: "online", "offline", or "away"
            metadata: Optional additional data (e.g., last_seen)

        Returns:
            int: Number of subscribers

        Example:
            await pubsub.publish_online_status(
                user_id=1,
                status="online",
                metadata={"device": "web"}
            )
        """
        channel = self.online_status_channel()
        payload = json.dumps(
            {
                "user_id": user_id,
                "status": status,
                "timestamp": None,  # Will be serialized as ISO string
                **(metadata or {}),
            },
            default=str,
        )

        try:
            num_subscribers = await self.redis_client.publish(channel, payload)
            logger.debug(
                f"Published status update for user {user_id}: {status} "
                f"({num_subscribers} subscribers)"
            )
            return num_subscribers
        except Exception as e:
            logger.error(f"Failed to publish status update: {e}")
            raise

    # ========================================================================
    # Subscribing Methods
    # ========================================================================

    async def subscribe_conversation(
        self,
        conversation_id: UUID | str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Subscribe to conversation messages.

        Yields message dictionaries as they arrive.
        Automatically handles JSON deserialization.

        Args:
            conversation_id: Conversation UUID

        Yields:
            dict: Message data

        Example:
            async for message in pubsub.subscribe_conversation(conv_id):
                print(f"New message: {message['content']}")
                await websocket.send_json(message)
        """
        channel = self.conversation_channel(conversation_id)
        pubsub = self.redis_client.pubsub()

        try:
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to {channel}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")
                        continue
        except asyncio.CancelledError:
            logger.info(f"Subscription to {channel} cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in subscription to {channel}: {e}")
            raise
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info(f"Unsubscribed from {channel}")

    async def subscribe_user_notifications(
        self,
        user_id: int,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Subscribe to user's personal notification channel.

        Args:
            user_id: User ID

        Yields:
            dict: Notification data
        """
        channel = self.user_channel(user_id)
        pubsub = self.redis_client.pubsub()

        try:
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to {channel}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode notification: {e}")
                        continue
        except asyncio.CancelledError:
            logger.info(f"Subscription to {channel} cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in subscription to {channel}: {e}")
            raise
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info(f"Unsubscribed from {channel}")

    async def subscribe_zone_announcements(
        self,
        zone_id: int,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Subscribe to zone announcement channel.

        Args:
            zone_id: Zone ID

        Yields:
            dict: Announcement data
        """
        channel = self.zone_channel(zone_id)
        pubsub = self.redis_client.pubsub()

        try:
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to {channel}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode announcement: {e}")
                        continue
        except asyncio.CancelledError:
            logger.info(f"Subscription to {channel} cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in subscription to {channel}: {e}")
            raise
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info(f"Unsubscribed from {channel}")

    async def subscribe_online_status(
        self,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Subscribe to global online status updates.

        Yields:
            dict: Status update data with user_id, status, timestamp
        """
        channel = self.online_status_channel()
        pubsub = self.redis_client.pubsub()

        try:
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to {channel}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode status update: {e}")
                        continue
        except asyncio.CancelledError:
            logger.info(f"Subscription to {channel} cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in subscription to {channel}: {e}")
            raise
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info(f"Unsubscribed from {channel}")

    # ========================================================================
    # Utility Methods
    # ========================================================================

    async def get_channel_subscribers(self, channel: str) -> int:
        """
        Get number of active subscribers to a channel.

        Args:
            channel: Channel name

        Returns:
            int: Number of subscribers
        """
        try:
            info = await self.redis_client.execute_command("PUBSUB", "NUMSUB", channel)
            # Redis returns [channel_name, subscriber_count, ...]
            if info and len(info) > 1:
                return int(info[1])
            return 0
        except Exception as e:
            logger.error(f"Failed to get subscriber count for {channel}: {e}")
            return 0

    async def list_active_channels(self, pattern: str = "*") -> list[str]:
        """
        List active channels matching pattern.

        Args:
            pattern: Channel name pattern (default: "*")

        Returns:
            list[str]: List of active channel names
        """
        try:
            channels = await self.redis_client.execute_command(
                "PUBSUB", "CHANNELS", pattern
            )
            return list(channels) if channels else []
        except Exception as e:
            logger.error(f"Failed to list channels: {e}")
            return []


# Singleton instance
_pubsub_instance: Optional[MessengerPubSub] = None


def get_pubsub() -> MessengerPubSub:
    """
    Get singleton MessengerPubSub instance.

    Returns:
        MessengerPubSub: Global Pub/Sub manager

    Example:
        from app.messenger.pubsub import get_pubsub

        pubsub = get_pubsub()
        await pubsub.publish_message(...)
    """
    global _pubsub_instance
    if _pubsub_instance is None:
        _pubsub_instance = MessengerPubSub()
    return _pubsub_instance
