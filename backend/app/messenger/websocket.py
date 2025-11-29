"""
WebSocket connection manager for messenger

Manages active WebSocket connections, handles reconnection,
and coordinates with Redis Pub/Sub for message broadcasting.

Features:
- Connection lifecycle management (connect, disconnect, heartbeat)
- User presence tracking (online/offline status)
- Message delivery to connected clients
- Automatic cleanup on disconnect

Usage:
    from app.messenger.websocket import manager

    @router.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: int):
        await manager.connect(websocket, user_id)
        try:
            while True:
                data = await websocket.receive_json()
                await manager.handle_message(user_id, data)
        except WebSocketDisconnect:
            await manager.disconnect(user_id)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from app.messenger.pubsub import get_pubsub
from app.messenger.presence import get_presence_manager

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for messenger system.

    Tracks:
    - Active connections per user
    - User online status
    - Conversation subscriptions

    Supports multiple connections per user (web + mobile).
    """

    def __init__(self):
        """Initialize connection manager"""
        # Map user_id -> list of WebSocket connections
        self.active_connections: dict[int, list[WebSocket]] = defaultdict(list)

        # Map user_id -> set of conversation_ids they're subscribed to
        self.user_subscriptions: dict[int, set[UUID]] = defaultdict(set)

        # Map user_id -> last seen timestamp
        self.user_last_seen: dict[int, datetime] = {}

        # Pub/Sub manager
        self.pubsub = get_pubsub()

        # Presence manager
        self.presence = get_presence_manager()

    # ========================================================================
    # Connection Lifecycle
    # ========================================================================

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        zone_id: Optional[int] = None,
        org_id: Optional[int] = None,
        conversations: Optional[list[UUID]] = None,
    ):
        """
        Accept WebSocket connection and register user.

        Args:
            websocket: FastAPI WebSocket instance
            user_id: User ID
            zone_id: Optional zone ID for presence tracking
            org_id: Optional org ID for presence tracking
            conversations: Optional list of conversation IDs to subscribe to

        Example:
            await manager.connect(websocket, user_id=1, zone_id=1, org_id=1)
        """
        await websocket.accept()

        # Add connection to active list
        self.active_connections[user_id].append(websocket)

        # Subscribe to conversations if provided
        if conversations:
            self.user_subscriptions[user_id].update(conversations)

        # Update online status
        is_first_connection = len(self.active_connections[user_id]) == 1
        if is_first_connection:
            # Set online in presence system
            await self.presence.set_online(
                user_id=user_id,
                zone_id=zone_id,
                org_id=org_id,
            )

            # Publish to Redis Pub/Sub (for backward compatibility)
            await self.pubsub.publish_online_status(user_id, "online")
            logger.info(f"User {user_id} is now online")
        else:
            # Update activity for existing connection
            await self.presence.update_activity(user_id)
            logger.info(
                f"User {user_id} connected "
                f"({len(self.active_connections[user_id])} active connections)"
            )

        # Send welcome message with presence info
        presence_status = await self.presence.get_status(user_id)
        await self.send_personal_message(
            user_id,
            {
                "type": "system",
                "event": "connected",
                "message": "Connected to messenger",
                "timestamp": datetime.utcnow().isoformat(),
                "presence": presence_status,
            },
        )

    async def disconnect(self, websocket: WebSocket, user_id: int):
        """
        Remove WebSocket connection and update user status.

        Args:
            websocket: FastAPI WebSocket instance to remove
            user_id: User ID

        Example:
            await manager.disconnect(websocket, user_id=1)
        """
        # Remove connection from active list
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                # Connection not in list (already removed or never added)
                pass

            # Clean up if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

                # Update last seen
                self.user_last_seen[user_id] = datetime.utcnow()

                # Set offline in presence system
                await self.presence.set_offline(user_id)

                # Publish offline status (for backward compatibility)
                await self.pubsub.publish_online_status(
                    user_id,
                    "offline",
                    metadata={"last_seen": self.user_last_seen[user_id].isoformat()},
                )
                logger.info(f"User {user_id} is now offline")
            else:
                # Update activity for remaining connections
                await self.presence.update_activity(user_id)
                logger.info(
                    f"User {user_id} disconnected "
                    f"({len(self.active_connections[user_id])} remaining connections)"
                )

    # ========================================================================
    # Message Sending
    # ========================================================================

    async def send_personal_message(
        self,
        user_id: int,
        message: dict[str, Any],
    ):
        """
        Send message to all connections of a specific user.

        Args:
            user_id: User ID
            message: Message data (will be JSON serialized)

        Example:
            await manager.send_personal_message(
                user_id=1,
                message={"type": "notification", "content": "New message!"}
            )
        """
        if user_id not in self.active_connections:
            logger.debug(f"User {user_id} not connected, skipping message")
            return

        # Send to all connections for this user
        disconnected: list[WebSocket] = []
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection, user_id)

    async def broadcast_to_conversation(
        self,
        conversation_id: UUID,
        message: dict[str, Any],
        exclude_user: Optional[int] = None,
    ):
        """
        Broadcast message to all participants of a conversation.

        Args:
            conversation_id: Conversation UUID
            message: Message data
            exclude_user: Optional user ID to exclude (e.g., sender)

        Example:
            await manager.broadcast_to_conversation(
                conversation_id=UUID("..."),
                message={"type": "message", "content": "Hello!"},
                exclude_user=1  # Don't send back to sender
            )
        """
        # Find all users subscribed to this conversation
        for user_id, conversations in self.user_subscriptions.items():
            if conversation_id in conversations and user_id != exclude_user:
                await self.send_personal_message(user_id, message)

    async def broadcast_to_all(self, message: dict[str, Any]):
        """
        Broadcast message to all connected users.

        Args:
            message: Message data

        Example:
            await manager.broadcast_to_all({
                "type": "system",
                "message": "Server maintenance in 5 minutes"
            })
        """
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(user_id, message)

    # ========================================================================
    # Subscription Management
    # ========================================================================

    async def subscribe_to_conversation(
        self,
        user_id: int,
        conversation_id: UUID,
    ):
        """
        Subscribe user to conversation messages.

        Args:
            user_id: User ID
            conversation_id: Conversation UUID
        """
        self.user_subscriptions[user_id].add(conversation_id)
        logger.debug(f"User {user_id} subscribed to conversation {conversation_id}")

    async def unsubscribe_from_conversation(
        self,
        user_id: int,
        conversation_id: UUID,
    ):
        """
        Unsubscribe user from conversation messages.

        Args:
            user_id: User ID
            conversation_id: Conversation UUID
        """
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(conversation_id)
            logger.debug(
                f"User {user_id} unsubscribed from conversation {conversation_id}"
            )

    # ========================================================================
    # Status & Monitoring
    # ========================================================================

    def is_user_online(self, user_id: int) -> bool:
        """Check if user has any active connections"""
        return user_id in self.active_connections

    def get_online_users(self) -> list[int]:
        """Get list of all online user IDs"""
        return list(self.active_connections.keys())

    def get_connection_count(self, user_id: int) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, []))

    def get_total_connections(self) -> int:
        """Get total number of active WebSocket connections"""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_user_last_seen(self, user_id: int) -> Optional[datetime]:
        """Get user's last seen timestamp"""
        return self.user_last_seen.get(user_id)

    async def get_stats(self) -> dict[str, Any]:
        """
        Get connection manager statistics.

        Returns:
            dict: Statistics including online users, connections, etc.
        """
        return {
            "online_users": len(self.active_connections),
            "total_connections": self.get_total_connections(),
            "active_conversations": sum(
                len(subs) for subs in self.user_subscriptions.values()
            ),
        }


# Global singleton instance
manager = WebSocketConnectionManager()
