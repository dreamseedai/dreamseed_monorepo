"""
Push Notification Service for Messenger

Supports multiple platforms:
- Firebase Cloud Messaging (FCM) - Android + iOS + Web
- Apple Push Notification Service (APNs) - iOS native
- Web Push - Progressive Web Apps

Features:
- Device token registration/management
- Multi-device push delivery
- Notification preferences (muting, do-not-disturb)
- Delivery tracking and analytics
- Background worker for async delivery
- Retry logic with exponential backoff
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DevicePlatform(str, Enum):
    """Device platform types"""

    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class NotificationPriority(str, Enum):
    """Notification delivery priority"""

    HIGH = "high"  # Immediate delivery (new message)
    NORMAL = "normal"  # Standard delivery
    LOW = "low"  # Batched delivery


class PushProvider(str, Enum):
    """Push notification provider"""

    FCM = "fcm"  # Firebase Cloud Messaging
    APNS = "apns"  # Apple Push Notification Service
    WEB_PUSH = "web_push"  # Web Push API


class PushNotificationService:
    """
    Push notification service for messenger.

    Handles:
    - Device token registration
    - Multi-platform push delivery (FCM, APNs, Web Push)
    - Notification preferences
    - Delivery tracking
    - Background async delivery
    """

    def __init__(
        self,
        fcm_server_key: Optional[str] = None,
        apns_key_path: Optional[str] = None,
        apns_key_id: Optional[str] = None,
        apns_team_id: Optional[str] = None,
        web_push_private_key: Optional[str] = None,
        web_push_claims: Optional[dict] = None,
    ):
        """
        Initialize push notification service.

        Args:
            fcm_server_key: Firebase Cloud Messaging server key
            apns_key_path: Path to APNs auth key (.p8 file)
            apns_key_id: APNs key ID
            apns_team_id: Apple Team ID
            web_push_private_key: VAPID private key for Web Push
            web_push_claims: VAPID claims (mailto: or https:)
        """
        self.fcm_server_key = fcm_server_key
        self.apns_key_path = apns_key_path
        self.apns_key_id = apns_key_id
        self.apns_team_id = apns_team_id
        self.web_push_private_key = web_push_private_key
        self.web_push_claims = web_push_claims

        # Initialize providers
        self._init_fcm()
        self._init_apns()
        self._init_web_push()

    def _init_fcm(self):
        """Initialize Firebase Cloud Messaging client"""
        if not self.fcm_server_key:
            logger.warning("FCM server key not provided - FCM push disabled")
            self.fcm_client = None
            return

        try:
            # Use pyfcm for FCM
            from pyfcm import FCMNotification  # type: ignore

            self.fcm_client = FCMNotification(api_key=self.fcm_server_key)
            logger.info("FCM client initialized successfully")
        except ImportError:
            logger.warning("pyfcm not installed - install with: pip install pyfcm")
            self.fcm_client = None
        except Exception as e:
            logger.error(f"FCM initialization error: {e}")
            self.fcm_client = None

    def _init_apns(self):
        """Initialize Apple Push Notification Service client"""
        if not all([self.apns_key_path, self.apns_key_id, self.apns_team_id]):
            logger.warning("APNs credentials not complete - APNs push disabled")
            self.apns_client = None
            return

        try:
            # Use aioapns for async APNs
            from aioapns import APNs, NotificationRequest  # type: ignore

            self.apns_client = APNs(
                key=self.apns_key_path,
                key_id=self.apns_key_id,
                team_id=self.apns_team_id,
                topic="ai.dreamseed.messenger",  # Bundle ID
                use_sandbox=False,  # Production
            )
            self.APNsNotificationRequest = NotificationRequest
            logger.info("APNs client initialized successfully")
        except ImportError:
            logger.warning("aioapns not installed - install with: pip install aioapns")
            self.apns_client = None
        except Exception as e:
            logger.error(f"APNs initialization error: {e}")
            self.apns_client = None

    def _init_web_push(self):
        """Initialize Web Push client"""
        if not all([self.web_push_private_key, self.web_push_claims]):
            logger.warning("Web Push credentials not complete - Web Push disabled")
            self.web_push_client = None
            return

        try:
            # Use pywebpush for Web Push
            from pywebpush import webpush  # type: ignore

            self.webpush = webpush
            logger.info("Web Push initialized successfully")
        except ImportError:
            logger.warning(
                "pywebpush not installed - install with: pip install pywebpush"
            )
            self.web_push_client = None
        except Exception as e:
            logger.error(f"Web Push initialization error: {e}")
            self.web_push_client = None

    async def register_device(
        self,
        db: AsyncSession,
        user_id: int,
        device_token: str,
        platform: DevicePlatform,
        provider: PushProvider = PushProvider.FCM,
        device_name: Optional[str] = None,
    ) -> dict:
        """
        Register device token for push notifications.

        Args:
            db: Database session
            user_id: User ID
            device_token: FCM/APNs/Web Push token
            platform: Device platform (ios/android/web)
            provider: Push provider (fcm/apns/web_push)
            device_name: Optional device name

        Returns:
            dict with registration info
        """
        from app.models.messenger_models import DeviceToken

        # Check if token already exists
        stmt = select(DeviceToken).where(
            and_(
                DeviceToken.user_id == user_id,
                DeviceToken.token == device_token,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update last_used
            existing.last_used_at = func.now()
            existing.is_active = True
            await db.commit()

            return {
                "status": "updated",
                "device_token_id": existing.id,
                "user_id": user_id,
            }

        # Create new token
        device_token_record = DeviceToken(
            user_id=user_id,
            token=device_token,
            platform=platform.value,
            provider=provider.value,
            device_name=device_name,
            is_active=True,
        )

        db.add(device_token_record)
        await db.commit()
        await db.refresh(device_token_record)

        logger.info(f"Device registered: user={user_id}, platform={platform}")

        return {
            "status": "registered",
            "device_token_id": device_token_record.id,
            "user_id": user_id,
            "platform": platform.value,
        }

    async def unregister_device(
        self,
        db: AsyncSession,
        user_id: int,
        device_token: str,
    ) -> bool:
        """
        Unregister device token (e.g., on logout).

        Args:
            db: Database session
            user_id: User ID
            device_token: Token to remove

        Returns:
            True if unregistered, False if not found
        """
        from app.models.messenger_models import DeviceToken

        stmt = delete(DeviceToken).where(
            and_(
                DeviceToken.user_id == user_id,
                DeviceToken.token == device_token,
            )
        )
        result = await db.execute(stmt)
        await db.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Device unregistered: user={user_id}")

        return deleted

    async def get_user_devices(
        self,
        db: AsyncSession,
        user_id: int,
        active_only: bool = True,
    ) -> list[dict]:
        """
        Get all registered devices for a user.

        Args:
            db: Database session
            user_id: User ID
            active_only: Only return active devices

        Returns:
            List of device info dicts
        """
        from app.models.messenger_models import DeviceToken

        stmt = select(DeviceToken).where(DeviceToken.user_id == user_id)

        if active_only:
            stmt = stmt.where(DeviceToken.is_active == True)  # noqa: E712

        stmt = stmt.order_by(DeviceToken.created_at.desc())

        result = await db.execute(stmt)
        devices = result.scalars().all()

        return [
            {
                "id": d.id,
                "platform": d.platform,
                "provider": d.provider,
                "device_name": d.device_name,
                "registered_at": d.created_at.isoformat(),
                "last_used_at": d.last_used_at.isoformat() if d.last_used_at else None,
            }
            for d in devices
        ]

    async def send_push_notification(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        body: str,
        data: Optional[dict] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        conversation_id: Optional[str] = None,
    ) -> dict:
        """
        Send push notification to all user devices.

        Args:
            db: Database session
            user_id: Target user ID
            title: Notification title
            body: Notification body text
            data: Additional data payload
            priority: Delivery priority
            conversation_id: Optional conversation ID (for muting check)

        Returns:
            dict with delivery results
        """
        # Check notification settings
        if conversation_id:
            from app.models.messenger_models import NotificationSetting

            stmt = select(NotificationSetting).where(
                and_(
                    NotificationSetting.user_id == user_id,
                    NotificationSetting.conversation_id == conversation_id,
                )
            )
            result = await db.execute(stmt)
            settings = result.scalar_one_or_none()

            if settings and (settings.muted or not settings.push_enabled):
                logger.info(
                    f"Push notification skipped: user={user_id} (muted or disabled)"
                )
                return {"status": "skipped", "reason": "muted_or_disabled"}

        # Get active devices
        devices = await self.get_user_devices(db, user_id, active_only=True)

        if not devices:
            logger.info(f"No devices registered for user {user_id}")
            return {"status": "no_devices", "user_id": user_id}

        # Get device tokens
        from app.models.messenger_models import DeviceToken

        stmt = select(DeviceToken).where(
            and_(
                DeviceToken.user_id == user_id,
                DeviceToken.is_active == True,  # noqa: E712
            )
        )
        result = await db.execute(stmt)
        device_records = result.scalars().all()

        # Send to each device
        results = []
        for device in device_records:
            try:
                if device.provider == PushProvider.FCM.value:
                    success = await self._send_fcm(
                        device.token,
                        title,
                        body,
                        data,
                        priority,
                    )
                elif device.provider == PushProvider.APNS.value:
                    success = await self._send_apns(
                        device.token,
                        title,
                        body,
                        data,
                        priority,
                    )
                elif device.provider == PushProvider.WEB_PUSH.value:
                    success = await self._send_web_push(
                        device.token,
                        title,
                        body,
                        data,
                    )
                else:
                    logger.warning(f"Unknown provider: {device.provider}")
                    success = False

                results.append(
                    {
                        "device_id": device.id,
                        "platform": device.platform,
                        "success": success,
                    }
                )

                # Update last_used_at on success
                if success:
                    device.last_used_at = func.now()

            except Exception as e:
                logger.error(f"Push delivery error (device={device.id}): {e}")
                results.append(
                    {
                        "device_id": device.id,
                        "platform": device.platform,
                        "success": False,
                        "error": str(e),
                    }
                )

        await db.commit()

        success_count = sum(1 for r in results if r.get("success"))

        return {
            "status": "sent",
            "user_id": user_id,
            "devices_count": len(results),
            "success_count": success_count,
            "results": results,
        }

    async def _send_fcm(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[dict],
        priority: NotificationPriority,
    ) -> bool:
        """Send via Firebase Cloud Messaging"""
        if not self.fcm_client:
            logger.warning("FCM client not initialized")
            return False

        try:
            # Prepare data payload
            data_message = data or {}
            data_message["timestamp"] = datetime.utcnow().isoformat()

            # Send
            result = self.fcm_client.notify_single_device(
                registration_id=token,
                message_title=title,
                message_body=body,
                data_message=data_message,
                time_to_live=86400,  # 24 hours
                priority="high" if priority == NotificationPriority.HIGH else "normal",
            )

            success = result.get("success") == 1
            if not success:
                logger.error(f"FCM send failed: {result}")

            return success

        except Exception as e:
            logger.error(f"FCM send error: {e}")
            return False

    async def _send_apns(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[dict],
        priority: NotificationPriority,
    ) -> bool:
        """Send via Apple Push Notification Service"""
        if not self.apns_client:
            logger.warning("APNs client not initialized")
            return False

        try:
            # Prepare notification request
            alert = {"title": title, "body": body}

            request = self.APNsNotificationRequest(
                device_token=token,
                message={
                    "aps": {
                        "alert": alert,
                        "sound": "default",
                        "badge": 1,
                    },
                    "data": data or {},
                },
                priority=10 if priority == NotificationPriority.HIGH else 5,
            )

            # Send
            response = await self.apns_client.send_notification(request)

            success = response.is_successful
            if not success:
                logger.error(f"APNs send failed: {response.description}")

            return success

        except Exception as e:
            logger.error(f"APNs send error: {e}")
            return False

    async def _send_web_push(
        self,
        subscription_info: str,
        title: str,
        body: str,
        data: Optional[dict],
    ) -> bool:
        """Send via Web Push API"""
        if not self.webpush:
            logger.warning("Web Push not initialized")
            return False

        try:
            # Parse subscription info (JSON string)
            subscription = json.loads(subscription_info)

            # Prepare notification payload
            payload = json.dumps(
                {
                    "title": title,
                    "body": body,
                    "icon": "/icon-192x192.png",
                    "badge": "/badge-72x72.png",
                    "data": data or {},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Send
            self.webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=self.web_push_private_key,
                vapid_claims=self.web_push_claims,
            )

            return True

        except Exception as e:
            logger.error(f"Web Push send error: {e}")
            return False

    async def cleanup_inactive_devices(
        self,
        db: AsyncSession,
        days: int = 90,
    ) -> int:
        """
        Remove devices that haven't been used in X days.

        Args:
            db: Database session
            days: Days of inactivity before cleanup

        Returns:
            Number of devices removed
        """
        from app.models.messenger_models import DeviceToken

        cutoff = datetime.utcnow() - timedelta(days=days)

        stmt = delete(DeviceToken).where(
            DeviceToken.last_used_at < cutoff,
        )

        result = await db.execute(stmt)
        await db.commit()

        removed = result.rowcount
        if removed > 0:
            logger.info(f"Cleaned up {removed} inactive devices (>{days} days)")

        return removed


# Singleton instance
_push_service_instance: Optional[PushNotificationService] = None


def get_push_service() -> PushNotificationService:
    """
    Get or create singleton PushNotificationService instance.

    Configuration from environment variables:
    - FCM_SERVER_KEY: Firebase Cloud Messaging server key
    - APNS_KEY_PATH: Path to APNs auth key (.p8 file)
    - APNS_KEY_ID: APNs key ID
    - APNS_TEAM_ID: Apple Team ID
    - WEB_PUSH_PRIVATE_KEY: VAPID private key for Web Push
    - WEB_PUSH_CLAIMS_EMAIL: VAPID email claim

    Returns:
        PushNotificationService singleton instance
    """
    import os

    global _push_service_instance

    if _push_service_instance is None:
        web_push_claims = None
        if os.getenv("WEB_PUSH_CLAIMS_EMAIL"):
            web_push_claims = {"sub": f"mailto:{os.getenv('WEB_PUSH_CLAIMS_EMAIL')}"}

        _push_service_instance = PushNotificationService(
            fcm_server_key=os.getenv("FCM_SERVER_KEY"),
            apns_key_path=os.getenv("APNS_KEY_PATH"),
            apns_key_id=os.getenv("APNS_KEY_ID"),
            apns_team_id=os.getenv("APNS_TEAM_ID"),
            web_push_private_key=os.getenv("WEB_PUSH_PRIVATE_KEY"),
            web_push_claims=web_push_claims,
        )

    return _push_service_instance


async def push_cleanup_task():
    """
    Background task to cleanup inactive devices.

    Runs every 24 hours and removes devices inactive for 90+ days.
    """
    from app.core.database import AsyncSessionLocal

    push_service = get_push_service()

    while True:
        try:
            await asyncio.sleep(86400)  # 24 hours

            async with AsyncSessionLocal() as db:
                removed = await push_service.cleanup_inactive_devices(db, days=90)
                if removed > 0:
                    logger.info(f"Push cleanup: removed {removed} inactive devices")

        except Exception as e:
            logger.error(f"Push cleanup task error: {e}")
            await asyncio.sleep(3600)  # Retry after 1 hour on error
