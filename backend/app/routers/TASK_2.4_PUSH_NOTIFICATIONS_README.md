# Task 2.4: Push Notifications

**Status**: ✅ Completed  
**LOC**: ~1,200  
**Dependencies**: Task 2.1 (Event Handlers), Task 2.2 (Presence System), Task 2.3 (File Upload)

## Overview

Push notification system for real-time message delivery to offline users across multiple platforms:
- **FCM** (Firebase Cloud Messaging) - Android, iOS, Web
- **APNs** (Apple Push Notification Service) - iOS native
- **Web Push** - Progressive Web Apps

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Push Notification Flow                     │
└──────────────────────────────────────────────────────────────┘

1. User sends message via WebSocket
2. Message handler creates message in DB
3. Background task checks offline participants
4. Push service sends notifications to registered devices
5. FCM/APNs/Web Push delivers to devices

Components:
┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
│ Message Handler │─────▶│ Push Service     │─────▶│ FCM Server  │
│ (WebSocket)     │      │ (Background Task)│      │ APNs Server │
└─────────────────┘      └──────────────────┘      │ Web Push    │
                                │                   └─────────────┘
                                ├── Device Token DB
                                ├── Notification Settings
                                └── Presence Check (online/offline)
```

## Database Schema

### `device_tokens` Table

Stores push notification device tokens for all platforms.

```sql
CREATE TABLE device_tokens (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('ios', 'android', 'web')),
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('fcm', 'apns', 'web_push')),
    device_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_device_tokens_user (user_id),
    INDEX idx_device_tokens_user_active (user_id, is_active)
);
```

**Columns:**
- `token`: FCM registration token, APNs device token, or Web Push subscription JSON
- `platform`: Device OS - 'ios', 'android', or 'web'
- `provider`: Push provider - 'fcm', 'apns', or 'web_push'
- `device_name`: User-friendly device name (e.g., "iPhone 13 Pro", "Chrome on Desktop")
- `is_active`: Whether the token is still valid (inactive tokens are ignored)
- `last_used_at`: Last time a notification was successfully sent to this device

## Implementation

### 1. Push Notification Service (`push_notifications.py`)

**Location**: `backend/app/messenger/push_notifications.py` (650 LOC)

#### Key Classes

##### `PushNotificationService`

Main service for managing push notifications across all platforms.

```python
class PushNotificationService:
    def __init__(
        self,
        fcm_server_key: Optional[str] = None,
        apns_key_path: Optional[str] = None,
        apns_key_id: Optional[str] = None,
        apns_team_id: Optional[str] = None,
        web_push_private_key: Optional[str] = None,
        web_push_claims: Optional[dict] = None,
    ):
        """Initialize push service with provider credentials"""
        
    async def register_device(
        self,
        db: AsyncSession,
        user_id: int,
        device_token: str,
        platform: DevicePlatform,
        provider: PushProvider = PushProvider.FCM,
        device_name: Optional[str] = None,
    ) -> dict:
        """Register device token for push notifications"""
        
    async def unregister_device(
        self,
        db: AsyncSession,
        user_id: int,
        device_token: str,
    ) -> bool:
        """Unregister device token (e.g., on logout)"""
        
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
        """Send push notification to all user devices"""
```

#### Provider Methods

- `_send_fcm()`: Send via Firebase Cloud Messaging
- `_send_apns()`: Send via Apple Push Notification Service
- `_send_web_push()`: Send via Web Push API

#### Enums

```python
class DevicePlatform(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"

class PushProvider(str, Enum):
    FCM = "fcm"
    APNS = "apns"
    WEB_PUSH = "web_push"

class NotificationPriority(str, Enum):
    HIGH = "high"      # Immediate delivery
    NORMAL = "normal"  # Standard delivery
    LOW = "low"        # Batched delivery
```

### 2. REST API Endpoints (`messenger.py`)

**Location**: `backend/app/routers/messenger.py` (+150 LOC)

#### Device Management

##### `POST /api/v1/messenger/devices/register`

Register a device token for push notifications.

**Request Body:**
```json
{
  "device_token": "ePXo7KwW9...",
  "platform": "android",
  "provider": "fcm",
  "device_name": "Samsung Galaxy S21"
}
```

**Response:**
```json
{
  "status": "registered",
  "device_token_id": 123,
  "user_id": 456,
  "platform": "android"
}
```

##### `DELETE /api/v1/messenger/devices/{device_token}`

Unregister a device token (e.g., on logout).

**Response:**
```json
{
  "success": true,
  "message": "Device unregistered"
}
```

##### `GET /api/v1/messenger/devices`

List all registered devices for the current user.

**Response:**
```json
{
  "devices": [
    {
      "id": 1,
      "platform": "android",
      "provider": "fcm",
      "device_name": "Samsung Galaxy S21",
      "registered_at": "2024-01-15T10:30:00Z",
      "last_used_at": "2024-01-15T14:20:00Z"
    },
    {
      "id": 2,
      "platform": "ios",
      "provider": "apns",
      "device_name": "iPhone 13 Pro",
      "registered_at": "2024-01-10T08:15:00Z",
      "last_used_at": "2024-01-15T13:45:00Z"
    }
  ]
}
```

### 3. Message Event Integration

Push notifications are automatically sent when:
1. New message arrives
2. User is offline (checked via presence system)
3. Conversation is not muted
4. Push notifications are enabled for the conversation

**Implementation** (`send_push_notifications_for_message()` in `messenger.py`, 80 LOC):

```python
async def send_push_notifications_for_message(
    db_session,
    conversation_id: uuid.UUID,
    sender_id: int,
    message_content: str,
    message_id: uuid.UUID,
):
    """
    Send push notifications to offline participants.
    
    1. Get all participants except sender
    2. Check if each participant is online (presence system)
    3. If offline, send push notification to all their devices
    4. Respect notification settings (muted, push_enabled)
    """
```

**Triggered from** `handle_message_send()`:

```python
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
```

### 4. Notification Preferences

Notification settings are checked before sending push notifications:

- **`muted`**: If true, no notifications are sent for this conversation
- **`push_enabled`**: If false, no push notifications are sent (email may still be sent)

**Check in** `send_push_notification()`:

```python
if settings and (settings.muted or not settings.push_enabled):
    logger.info(f"Push notification skipped: user={user_id} (muted or disabled)")
    return {"status": "skipped", "reason": "muted_or_disabled"}
```

### 5. Cleanup & Maintenance

#### Inactive Device Cleanup

Devices inactive for 90+ days are automatically removed.

```python
async def cleanup_inactive_devices(
    self,
    db: AsyncSession,
    days: int = 90,
) -> int:
    """Remove devices that haven't been used in X days"""
```

**Background Task** (`push_cleanup_task()` in `push_notifications.py`):

Runs every 24 hours and removes inactive devices.

```python
async def push_cleanup_task():
    """Background task to cleanup inactive devices"""
    while True:
        await asyncio.sleep(86400)  # 24 hours
        async with AsyncSessionLocal() as db:
            removed = await push_service.cleanup_inactive_devices(db, days=90)
```

## Configuration

### Environment Variables

```bash
# FCM (Firebase Cloud Messaging)
FCM_SERVER_KEY=AAAA...your-fcm-server-key

# APNs (Apple Push Notification Service)
APNS_KEY_PATH=/path/to/AuthKey_XXXXXXXXXX.p8
APNS_KEY_ID=XXXXXXXXXX
APNS_TEAM_ID=YYYYYYYYYY

# Web Push (VAPID)
WEB_PUSH_PRIVATE_KEY=your-vapid-private-key
WEB_PUSH_CLAIMS_EMAIL=admin@dreamseed.ai
```

### Python Dependencies

Add to `requirements.txt`:

```txt
# Push notifications
pyfcm==1.5.4                # Firebase Cloud Messaging
aioapns==3.2                # Apple Push Notification Service
pywebpush==1.14.0           # Web Push API
py-vapid==1.9.0             # VAPID for Web Push
```

Install:

```bash
pip install pyfcm aioapns pywebpush py-vapid
```

## Usage Examples

### 1. Register Device (Client Side)

#### Android (FCM)

```kotlin
// Get FCM token
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        
        // Register with backend
        api.registerDevice(
            deviceToken = token,
            platform = "android",
            provider = "fcm",
            deviceName = "Samsung Galaxy S21"
        )
    }
}
```

#### iOS (APNs)

```swift
// Get APNs token
func application(_ application: UIApplication, 
                didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
    
    // Register with backend
    api.registerDevice(
        deviceToken: token,
        platform: "ios",
        provider: "apns",
        deviceName: "iPhone 13 Pro"
    )
}
```

#### Web (Web Push)

```javascript
// Request notification permission
const permission = await Notification.requestPermission();

if (permission === 'granted') {
  // Subscribe to push notifications
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
  });
  
  // Register with backend
  await fetch('/api/v1/messenger/devices/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      device_token: JSON.stringify(subscription),
      platform: 'web',
      provider: 'web_push',
      device_name: 'Chrome on Desktop'
    })
  });
}
```

### 2. Send Push Notification (Server Side)

#### From Message Handler

```python
from app.messenger.push_notifications import get_push_service

push_service = get_push_service()

await push_service.send_push_notification(
    db=db,
    user_id=recipient_id,
    title="John Doe • General Chat",
    body="Hey, are you available for a call?",
    data={
        "conversation_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "message_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "sender_id": 123,
        "type": "message.new"
    },
    priority=NotificationPriority.HIGH,
    conversation_id="f47ac10b-58cc-4372-a567-0e02b2c3d479"
)
```

#### Manual Push

```python
# Send custom push notification
await push_service.send_push_notification(
    db=db,
    user_id=user_id,
    title="System Notification",
    body="Your subscription expires in 3 days",
    data={"type": "subscription.expiring", "days_left": 3},
    priority=NotificationPriority.NORMAL
)
```

### 3. Unregister Device (On Logout)

```javascript
// Client-side
await fetch(`/api/v1/messenger/devices/${deviceToken}`, {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${authToken}` }
});
```

## Testing

### Test Suite (`test_messenger_push_notifications.py`)

**Location**: `backend/tests/test_messenger_push_notifications.py` (650 LOC)

**Test Coverage**:
- ✅ Device registration (FCM, APNs, Web Push)
- ✅ Device unregistration
- ✅ Duplicate device handling (updates instead of duplicates)
- ✅ Multi-device delivery
- ✅ Push notification sending (FCM, APNs, Web Push)
- ✅ Notification preferences (muted conversations, push_enabled=false)
- ✅ Offline user detection
- ✅ Inactive device cleanup (90+ days)
- ✅ No devices handling
- ✅ Singleton pattern

### Run Tests

```bash
cd backend

# Run all push notification tests
pytest tests/test_messenger_push_notifications.py -v

# Run with coverage
pytest tests/test_messenger_push_notifications.py --cov=app.messenger.push_notifications --cov-report=html

# Run specific test
pytest tests/test_messenger_push_notifications.py::test_register_device_fcm_android -v
```

### Mock Providers

Tests use mocked FCM, APNs, and Web Push clients to avoid hitting real services:

```python
@pytest.fixture
def push_service(mock_fcm_client, mock_apns_client, mock_webpush):
    service = PushNotificationService(...)
    service.fcm_client = mock_fcm_client
    service.apns_client = mock_apns_client
    service.webpush = mock_webpush
    return service
```

## Security Considerations

### 1. Token Validation

- Device tokens are unique (enforced by database constraint)
- Tokens are associated with specific users (cannot be hijacked)
- Inactive tokens are automatically cleaned up

### 2. Credential Management

- FCM server keys, APNs certificates, and VAPID keys stored securely in environment variables
- Never expose credentials in client-side code
- Use Google Secret Manager or AWS Secrets Manager in production

### 3. Authorization

- Only authenticated users can register/unregister devices
- Users can only manage their own devices
- Push notifications respect conversation permissions (participant-based access)

### 4. Rate Limiting

- Implement rate limiting on device registration endpoint (prevent spam)
- Batch push notifications where possible (reduce API calls)
- Use priority levels to control delivery urgency

### 5. Data Privacy

- Push notification payloads should not contain sensitive data (only IDs and metadata)
- Actual message content fetched after user opens app
- Follow GDPR/CCPA guidelines for notification data retention

## Performance Optimization

### 1. Background Task Pattern

Push notifications are sent asynchronously to avoid blocking WebSocket handlers:

```python
asyncio.create_task(
    send_push_notifications_for_message(...)
)
```

**Benefits**:
- WebSocket message delivery is not delayed
- Push notification failures don't affect message sending
- Concurrent delivery to multiple devices

### 2. Batch Delivery

For high-volume scenarios, batch push notifications:

```python
# Instead of sending one-by-one
for user_id in user_ids:
    await send_push_notification(user_id, ...)

# Batch send
await send_batch_push_notifications(user_ids, ...)
```

### 3. Caching

- Cache presence status (online/offline) to reduce Redis lookups
- Cache notification settings per conversation
- Use TTL (time-to-live) of 60 seconds for presence cache

### 4. Database Indexes

- `idx_device_tokens_user_active`: Fast lookup of active devices per user
- `idx_device_tokens_user`: Quick device count queries
- Unique constraint on `token`: Prevents duplicates

### 5. Connection Pooling

- Reuse FCM/APNs/Web Push client connections (singleton pattern)
- Don't create new clients for each notification
- Connection pooling handled by underlying libraries

## Monitoring & Analytics

### Metrics to Track

1. **Delivery Success Rate**
   - Percentage of notifications successfully delivered
   - Track per provider (FCM, APNs, Web Push)

2. **Latency**
   - Time from message send to push notification delivery
   - Target: <2 seconds for high-priority notifications

3. **Device Registration Rate**
   - New devices registered per day
   - Churn rate (unregistered devices)

4. **Inactive Device Count**
   - Devices not used in 30/60/90 days
   - Cleanup efficiency

5. **Error Rate**
   - Invalid tokens (device uninstalled app, token expired)
   - Provider API errors (FCM 500, APNs certificate issues)

### Logging

```python
# Success
logger.info(f"Push notification sent: user={user_id}, conv={conversation_id}")

# Failure
logger.error(f"Push delivery error (device={device_id}): {error}")

# Skipped
logger.info(f"Push notification skipped: user={user_id} (muted or disabled)")
```

### Alerting

Set up alerts for:
- Push notification error rate > 5%
- FCM/APNs API errors
- Device registration failures
- Cleanup task failures

## Troubleshooting

### Common Issues

#### 1. FCM "Invalid Registration Token"

**Cause**: Device token expired or app uninstalled

**Solution**:
- Mark device as inactive in database
- Client should re-register token on next app launch

#### 2. APNs Certificate Expired

**Cause**: APNs auth key expired or revoked

**Solution**:
- Generate new APNs auth key from Apple Developer Portal
- Update `APNS_KEY_PATH`, `APNS_KEY_ID`, `APNS_TEAM_ID` environment variables
- Restart push service

#### 3. Web Push Subscription Invalid

**Cause**: User revoked notification permission or cleared browser data

**Solution**:
- Remove subscription from database
- Client should request permission again and re-subscribe

#### 4. Push Notifications Not Received

**Checklist**:
- ✅ Device token registered in database?
- ✅ Device `is_active = true`?
- ✅ User is offline (checked via presence system)?
- ✅ Conversation not muted?
- ✅ `push_enabled = true` in notification settings?
- ✅ FCM/APNs/Web Push credentials configured correctly?
- ✅ Provider API responding (check logs)?

#### 5. Duplicate Notifications

**Cause**: Multiple devices registered with same token

**Solution**:
- Database unique constraint on `token` should prevent this
- If issue persists, check client-side registration logic

## Future Enhancements

### Phase 1 (Next Sprint)

1. **Rich Notifications**
   - Image previews in push notifications
   - Action buttons (Reply, Mark as Read)
   - Notification grouping by conversation

2. **Notification History**
   - Track all sent notifications (delivery log)
   - User can view notification history in app
   - Analytics dashboard for admins

3. **Smart Delivery**
   - Do-not-disturb hours (respect user timezone)
   - Quiet hours (8 PM - 8 AM, no push)
   - Notification batching (group multiple messages)

### Phase 2 (Future)

4. **Advanced Targeting**
   - Send push to specific device (not all user devices)
   - Priority-based device selection (send to most recently used device first)
   - Platform-specific payloads (iOS badge count, Android LED color)

5. **Push Notification Templates**
   - Predefined templates for different event types
   - Localization support (push in user's language)
   - Dynamic content (unread count, sender name with avatar)

6. **Analytics Integration**
   - Track notification open rate
   - A/B testing for notification content
   - User engagement metrics (time to open, click-through rate)

## Migration Guide

### From No Push Notifications to Task 2.4

1. **Run Database Migration**

```bash
cd backend
alembic upgrade head  # Applies 006_device_tokens migration
```

2. **Install Dependencies**

```bash
pip install pyfcm aioapns pywebpush py-vapid
```

3. **Configure Environment Variables**

```bash
# .env
FCM_SERVER_KEY=your_fcm_server_key
APNS_KEY_PATH=/path/to/AuthKey.p8
APNS_KEY_ID=your_apns_key_id
APNS_TEAM_ID=your_team_id
WEB_PUSH_PRIVATE_KEY=your_vapid_key
WEB_PUSH_CLAIMS_EMAIL=admin@dreamseed.ai
```

4. **Update Client Apps**

- Android: Integrate FCM SDK, register device token on login
- iOS: Enable push notifications capability, register APNs token
- Web: Request notification permission, subscribe to Web Push

5. **Test Push Notifications**

```bash
# Run tests
pytest tests/test_messenger_push_notifications.py -v

# Manual test via API
curl -X POST http://localhost:8000/api/v1/messenger/devices/register \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "test_fcm_token",
    "platform": "android",
    "provider": "fcm",
    "device_name": "Test Device"
  }'
```

6. **Start Cleanup Task** (Optional)

```python
# In main.py or startup script
import asyncio
from app.messenger.push_notifications import push_cleanup_task

# Start background task
asyncio.create_task(push_cleanup_task())
```

## Summary

Task 2.4 implements a complete push notification system with:

✅ **Multi-platform support**: FCM (Android/iOS/Web), APNs (iOS), Web Push (PWA)  
✅ **Device management**: Register, unregister, list devices via REST API  
✅ **Smart delivery**: Only send to offline users (checked via presence system)  
✅ **Notification preferences**: Respect muted conversations and user settings  
✅ **Background processing**: Async push delivery doesn't block message handlers  
✅ **Cleanup & maintenance**: Auto-remove inactive devices (90+ days)  
✅ **Comprehensive tests**: 20+ test scenarios covering all functionality  
✅ **Production-ready**: Singleton pattern, error handling, logging, monitoring

**Total LOC**: ~1,200  
**Files Modified**: 4 (push_notifications.py, messenger_models.py, messenger.py, migration)  
**Files Created**: 3 (push_notifications.py, test_messenger_push_notifications.py, 006_device_tokens.py)

**Cumulative LOC**: 7,630 / 40,000-50,000 target

---

**Next Steps**: Task 3.1 (Analytics & Insights) or Task 3.2 (Search & Discovery)
