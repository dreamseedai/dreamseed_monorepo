"""
Presence System for Real-Time User Status Tracking

Manages user online/offline status, last seen timestamps, and activity tracking.
Integrates with Redis for distributed presence management and WebSocket for real-time updates.

Features:
- Online/offline/away status tracking
- Last seen timestamp management
- Zone/org-wide presence broadcasts
- Activity-based auto-away detection
- Presence aggregation (online users count)

Architecture:
- Redis Hash: presence:{user_id} -> {status, last_activity, zone_id, org_id}
- Redis Sorted Set: online:zone:{zone_id} -> user_id (score = last_activity)
- Redis Sorted Set: online:org:{org_id} -> user_id (score = last_activity)
- TTL: 5 minutes (auto-cleanup for disconnected users)

Usage:
    from app.messenger.presence import get_presence_manager

    presence = get_presence_manager()
    await presence.set_online(user_id=1, zone_id=1, org_id=1)
    await presence.set_away(user_id=1)
    await presence.set_offline(user_id=1)

    status = await presence.get_status(user_id=1)
    online_users = await presence.get_online_users(zone_id=1)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.core.redis import get_redis
from app.messenger.pubsub import get_pubsub

logger = logging.getLogger(__name__)


class PresenceStatus(str, Enum):
    """User presence status"""

    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"


class PresenceManager:
    """
    Manages user presence and activity status.

    Redis Data Structures:
    - presence:{user_id} -> HASH {status, last_activity, zone_id, org_id, connections}
    - online:zone:{zone_id} -> ZSET {user_id: last_activity_timestamp}
    - online:org:{org_id} -> ZSET {user_id: last_activity_timestamp}
    - online:global -> ZSET {user_id: last_activity_timestamp}
    """

    def __init__(self):
        """Initialize presence manager"""
        self.redis = get_redis()
        self.pubsub = get_pubsub()

        # Auto-away threshold (5 minutes of inactivity)
        self.away_threshold_seconds = 300

        # Presence TTL (cleanup after 5 minutes)
        self.presence_ttl_seconds = 300

    # ========================================================================
    # Status Management
    # ========================================================================

    async def set_online(
        self,
        user_id: int,
        zone_id: Optional[int] = None,
        org_id: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Set user status to online.

        Args:
            user_id: User ID
            zone_id: Optional zone ID
            org_id: Optional org ID
            metadata: Optional metadata (device, client, etc.)

        Returns:
            True if status updated successfully
        """
        try:
            now = datetime.utcnow()
            timestamp = int(now.timestamp())

            presence_key = f"presence:{user_id}"
            presence_data = {
                "status": PresenceStatus.ONLINE.value,
                "last_activity": timestamp,
                "updated_at": now.isoformat(),
            }

            if zone_id is not None:
                presence_data["zone_id"] = zone_id
            if org_id is not None:
                presence_data["org_id"] = org_id
            if metadata:
                presence_data["metadata"] = str(metadata)

            # Update presence hash
            await self.redis.hset(presence_key, mapping=presence_data)  # type: ignore
            await self.redis.expire(presence_key, self.presence_ttl_seconds)

            # Add to online sorted sets
            await self.redis.zadd("online:global", {str(user_id): timestamp})

            if zone_id is not None:
                await self.redis.zadd(
                    f"online:zone:{zone_id}", {str(user_id): timestamp}
                )

            if org_id is not None:
                await self.redis.zadd(f"online:org:{org_id}", {str(user_id): timestamp})

            # Broadcast online status
            await self.pubsub.publish_online_status(
                user_id,
                PresenceStatus.ONLINE.value,
                metadata={
                    "zone_id": zone_id,
                    "org_id": org_id,
                    "timestamp": now.isoformat(),
                },
            )

            logger.info(f"User {user_id} set to online")
            return True

        except Exception as e:
            logger.error(f"Failed to set user {user_id} online: {e}")
            return False

    async def set_away(
        self,
        user_id: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Set user status to away (auto or manual).

        Args:
            user_id: User ID
            metadata: Optional metadata (reason, etc.)

        Returns:
            True if status updated successfully
        """
        try:
            presence_key = f"presence:{user_id}"

            # Check if user exists
            exists = await self.redis.exists(presence_key)
            if not exists:
                logger.warning(f"Cannot set away for non-existent user {user_id}")
                return False

            now = datetime.utcnow()

            # Update status only
            await self.redis.hset(  # type: ignore
                presence_key,
                mapping={
                    "status": PresenceStatus.AWAY.value,
                    "updated_at": now.isoformat(),
                },
            )

            # Broadcast away status
            await self.pubsub.publish_online_status(
                user_id,
                PresenceStatus.AWAY.value,
                metadata={"timestamp": now.isoformat(), **(metadata or {})},
            )

            logger.info(f"User {user_id} set to away")
            return True

        except Exception as e:
            logger.error(f"Failed to set user {user_id} away: {e}")
            return False

    async def set_offline(
        self,
        user_id: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Set user status to offline and cleanup.

        Args:
            user_id: User ID
            metadata: Optional metadata (reason, etc.)

        Returns:
            True if status updated successfully
        """
        try:
            presence_key = f"presence:{user_id}"

            # Get zone/org before deletion
            presence_data = await self.redis.hgetall(presence_key)  # type: ignore
            zone_id = presence_data.get(b"zone_id") if presence_data else None
            org_id = presence_data.get(b"org_id") if presence_data else None

            if zone_id:
                zone_id = int(zone_id)
            if org_id:
                org_id = int(org_id)

            now = datetime.utcnow()

            # Update status to offline (keep for last_seen)
            await self.redis.hset(  # type: ignore
                presence_key,
                mapping={
                    "status": PresenceStatus.OFFLINE.value,
                    "updated_at": now.isoformat(),
                    "last_seen": now.isoformat(),
                },
            )

            # Set shorter TTL for offline users (30 days for last_seen)
            await self.redis.expire(presence_key, 86400 * 30)

            # Remove from online sorted sets
            await self.redis.zrem("online:global", str(user_id))

            if zone_id:
                await self.redis.zrem(f"online:zone:{zone_id}", str(user_id))

            if org_id:
                await self.redis.zrem(f"online:org:{org_id}", str(user_id))

            # Broadcast offline status
            await self.pubsub.publish_online_status(
                user_id,
                PresenceStatus.OFFLINE.value,
                metadata={
                    "timestamp": now.isoformat(),
                    "last_seen": now.isoformat(),
                    **(metadata or {}),
                },
            )

            logger.info(f"User {user_id} set to offline")
            return True

        except Exception as e:
            logger.error(f"Failed to set user {user_id} offline: {e}")
            return False

    async def update_activity(
        self,
        user_id: int,
    ) -> bool:
        """
        Update user's last activity timestamp (heartbeat).

        Args:
            user_id: User ID

        Returns:
            True if activity updated successfully
        """
        try:
            presence_key = f"presence:{user_id}"

            # Check if user exists
            exists = await self.redis.exists(presence_key)
            if not exists:
                logger.warning(
                    f"Cannot update activity for non-existent user {user_id}"
                )
                return False

            now = datetime.utcnow()
            timestamp = int(now.timestamp())

            # Update last_activity
            await self.redis.hset(  # type: ignore
                presence_key,
                "last_activity",
                str(timestamp),
            )

            # Update TTL
            await self.redis.expire(presence_key, self.presence_ttl_seconds)

            # Update in sorted sets
            presence_data = await self.redis.hgetall(presence_key)  # type: ignore
            zone_id = presence_data.get(b"zone_id")
            org_id = presence_data.get(b"org_id")

            await self.redis.zadd("online:global", {str(user_id): timestamp})

            if zone_id:
                await self.redis.zadd(
                    f"online:zone:{zone_id.decode()}", {str(user_id): timestamp}
                )

            if org_id:
                await self.redis.zadd(
                    f"online:org:{org_id.decode()}", {str(user_id): timestamp}
                )

            # Check if user should be auto-away
            current_status = presence_data.get(b"status", b"").decode()
            if current_status == PresenceStatus.ONLINE.value:
                # No need to set away if we just updated activity
                pass

            return True

        except Exception as e:
            logger.error(f"Failed to update activity for user {user_id}: {e}")
            return False

    # ========================================================================
    # Status Queries
    # ========================================================================

    async def get_status(
        self,
        user_id: int,
    ) -> Optional[dict[str, Any]]:
        """
        Get user's current presence status.

        Args:
            user_id: User ID

        Returns:
            Dict with status, last_activity, zone_id, org_id, last_seen
            None if user not found
        """
        try:
            presence_key = f"presence:{user_id}"
            presence_data = await self.redis.hgetall(presence_key)  # type: ignore

            if not presence_data:
                return None

            result = {
                "user_id": user_id,
                "status": presence_data.get(b"status", b"").decode(),
                "last_activity": presence_data.get(b"last_activity", b"").decode(),
                "updated_at": presence_data.get(b"updated_at", b"").decode(),
            }

            if b"zone_id" in presence_data:
                result["zone_id"] = int(presence_data[b"zone_id"])

            if b"org_id" in presence_data:
                result["org_id"] = int(presence_data[b"org_id"])

            if b"last_seen" in presence_data:
                result["last_seen"] = presence_data[b"last_seen"].decode()

            return result

        except Exception as e:
            logger.error(f"Failed to get status for user {user_id}: {e}")
            return None

    async def get_online_users(
        self,
        zone_id: Optional[int] = None,
        org_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get list of online users.

        Args:
            zone_id: Filter by zone
            org_id: Filter by org
            limit: Maximum number of users

        Returns:
            List of user dicts with user_id, status, last_activity
        """
        try:
            # Determine which sorted set to query
            if zone_id is not None:
                key = f"online:zone:{zone_id}"
            elif org_id is not None:
                key = f"online:org:{org_id}"
            else:
                key = "online:global"

            # Get users sorted by last activity (most recent first)
            user_ids = await self.redis.zrevrange(key, 0, limit - 1, withscores=True)

            result = []
            for user_id_bytes, _score in user_ids:
                user_id = int(user_id_bytes.decode())
                status = await self.get_status(user_id)

                if status:
                    result.append(status)

            return result

        except Exception as e:
            logger.error(f"Failed to get online users: {e}")
            return []

    async def get_online_count(
        self,
        zone_id: Optional[int] = None,
        org_id: Optional[int] = None,
    ) -> int:
        """
        Get count of online users.

        Args:
            zone_id: Filter by zone
            org_id: Filter by org

        Returns:
            Number of online users
        """
        try:
            if zone_id is not None:
                key = f"online:zone:{zone_id}"
            elif org_id is not None:
                key = f"online:org:{org_id}"
            else:
                key = "online:global"

            count = await self.redis.zcard(key)
            return count

        except Exception as e:
            logger.error(f"Failed to get online count: {e}")
            return 0

    # ========================================================================
    # Auto-Away Detection
    # ========================================================================

    async def check_and_set_away(
        self,
        user_id: int,
    ) -> bool:
        """
        Check if user should be auto-away based on inactivity.

        Args:
            user_id: User ID

        Returns:
            True if user was set to away
        """
        try:
            status = await self.get_status(user_id)
            if not status:
                return False

            # Only auto-away online users
            if status["status"] != PresenceStatus.ONLINE.value:
                return False

            # Check last activity
            last_activity_ts = int(status["last_activity"])
            now_ts = int(datetime.utcnow().timestamp())

            if now_ts - last_activity_ts > self.away_threshold_seconds:
                await self.set_away(user_id, metadata={"reason": "auto-away"})
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to check away status for user {user_id}: {e}")
            return False

    async def cleanup_stale_presence(
        self,
        max_age_seconds: int = 600,
    ) -> int:
        """
        Cleanup stale presence records (users who disconnected without cleanup).

        Args:
            max_age_seconds: Maximum age before considering stale

        Returns:
            Number of cleaned up users
        """
        try:
            now_ts = int(datetime.utcnow().timestamp())
            cutoff_ts = now_ts - max_age_seconds

            # Get all users from global online set
            user_ids = await self.redis.zrangebyscore(
                "online:global", "-inf", cutoff_ts
            )

            cleaned = 0
            for user_id_bytes in user_ids:
                user_id = int(user_id_bytes.decode())
                await self.set_offline(user_id, metadata={"reason": "stale-cleanup"})
                cleaned += 1

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} stale presence records")

            return cleaned

        except Exception as e:
            logger.error(f"Failed to cleanup stale presence: {e}")
            return 0


# Singleton instance
_presence_manager: Optional[PresenceManager] = None


def get_presence_manager() -> PresenceManager:
    """Get singleton presence manager instance"""
    global _presence_manager
    if _presence_manager is None:
        _presence_manager = PresenceManager()
    return _presence_manager


# ============================================================================
# Background Tasks
# ============================================================================


async def presence_cleanup_task():
    """
    Background task to cleanup stale presence and check for auto-away.

    Should be run periodically (e.g., every minute).
    """
    presence = get_presence_manager()

    while True:
        try:
            # Cleanup stale presence (10 minutes old)
            await presence.cleanup_stale_presence(max_age_seconds=600)

            # Wait 1 minute before next cleanup
            await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info("Presence cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in presence cleanup task: {e}")
            await asyncio.sleep(60)
