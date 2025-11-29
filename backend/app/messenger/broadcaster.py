"""
Message broadcaster - integrates Redis Pub/Sub with WebSocket manager

Listens to Redis Pub/Sub channels and forwards messages to connected WebSocket clients.
Runs as background task in FastAPI application lifecycle.

Usage:
    from app.messenger.broadcaster import start_broadcaster, stop_broadcaster

    @app.on_event("startup")
    async def startup():
        await start_broadcaster()

    @app.on_event("shutdown")
    async def shutdown():
        await stop_broadcaster()
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional
from uuid import UUID

from app.messenger.pubsub import get_pubsub
from app.messenger.websocket import manager

logger = logging.getLogger(__name__)


class MessageBroadcaster:
    """
    Bridges Redis Pub/Sub and WebSocket manager.

    Subscribes to Redis channels and forwards messages to WebSocket clients.
    Runs as background asyncio task.
    """

    def __init__(self):
        """Initialize broadcaster"""
        self.pubsub = get_pubsub()
        self.tasks: list[asyncio.Task] = []
        self.running = False

    async def start(self):
        """
        Start broadcaster background tasks.

        Subscribes to:
        - Online status channel (broadcasts presence updates)
        """
        if self.running:
            logger.warning("Broadcaster already running")
            return

        self.running = True
        logger.info("Starting message broadcaster...")

        # Start online status listener
        task = asyncio.create_task(self._listen_online_status())
        self.tasks.append(task)

        logger.info("Message broadcaster started")

    async def stop(self):
        """Stop broadcaster and cancel all tasks"""
        if not self.running:
            return

        self.running = False
        logger.info("Stopping message broadcaster...")

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to finish
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

        logger.info("Message broadcaster stopped")

    # ========================================================================
    # Background Listeners
    # ========================================================================

    async def _listen_online_status(self):
        """
        Listen to online status updates and broadcast to all connected clients.

        This allows users to see who's online in real-time.
        """
        try:
            logger.info("Started listening to online status updates")
            async for status_update in self.pubsub.subscribe_online_status():
                # Broadcast status update to all connected users
                await manager.broadcast_to_all(
                    {
                        "type": "presence",
                        "event": "user_status",
                        "data": status_update,
                    }
                )
        except asyncio.CancelledError:
            logger.info("Online status listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in online status listener: {e}")
            raise

    async def listen_conversation(self, conversation_id: UUID):
        """
        Listen to a specific conversation and forward messages to participants.

        This should be called for each active conversation.
        Not used in global broadcaster - instead, handled per-connection.

        Args:
            conversation_id: Conversation UUID to listen to
        """
        try:
            logger.info(f"Started listening to conversation {conversation_id}")
            async for message in self.pubsub.subscribe_conversation(conversation_id):
                # Forward message to all participants
                await manager.broadcast_to_conversation(
                    conversation_id,
                    {
                        "type": "message",
                        "event": "new_message",
                        "data": message,
                    },
                    exclude_user=message.get("sender_id"),  # Don't echo to sender
                )
        except asyncio.CancelledError:
            logger.info(f"Conversation listener cancelled: {conversation_id}")
            raise
        except Exception as e:
            logger.error(f"Error in conversation listener {conversation_id}: {e}")
            raise


# Global broadcaster instance
_broadcaster: Optional[MessageBroadcaster] = None


async def start_broadcaster():
    """
    Start global message broadcaster.

    Call this in FastAPI startup event.
    """
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = MessageBroadcaster()
    await _broadcaster.start()


async def stop_broadcaster():
    """
    Stop global message broadcaster.

    Call this in FastAPI shutdown event.
    """
    global _broadcaster
    if _broadcaster is not None:
        await _broadcaster.stop()


def get_broadcaster() -> MessageBroadcaster:
    """Get global broadcaster instance"""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = MessageBroadcaster()
    return _broadcaster
