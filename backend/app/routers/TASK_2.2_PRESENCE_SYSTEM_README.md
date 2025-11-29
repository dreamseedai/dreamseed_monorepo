# Task 2.2: Presence System - Implementation Complete ✅

## Overview

Implemented a distributed Redis-based presence tracking system for real-time user online/away/offline status across multiple FastAPI server instances.

**Implementation Date:** 2024-11-26  
**Total LOC:** ~850 lines (presence.py: 570, integrations: 150, tests: 320)

---

## Architecture

### Redis Data Structures

```
1. Hash Keys: presence:{user_id}
   Fields:
   - status: "online" | "away" | "offline"
   - last_activity: Unix timestamp
   - zone_id: User's current zone
   - org_id: User's current organization
   - updated_at: ISO timestamp
   - metadata: JSON string (optional)

2. Sorted Set Keys (score = last_activity timestamp):
   - online:global → All online users
   - online:zone:{zone_id} → Online users in zone
   - online:org:{org_id} → Online users in org

3. TTL:
   - Online presence: 5 minutes (auto-expire if not refreshed)
   - Offline last_seen: 30 days
```

### Presence States

```python
class PresenceStatus(str, Enum):
    ONLINE = "online"  # User actively connected
    AWAY = "away"      # Inactive for 5+ minutes OR manually set
    OFFLINE = "offline" # Disconnected
```

---

## Implementation Details

### 1. Core Module: `presence.py` (570 LOC)

**Location:** `backend/app/messenger/presence.py`

**Key Components:**

#### PresenceManager Class

```python
class PresenceManager:
    def __init__(self, redis, pubsub, away_threshold=300, ttl=300):
        """
        Args:
            redis: Redis client instance
            pubsub: PubSub manager for broadcasting
            away_threshold: Seconds of inactivity before auto-away (default: 5 min)
            ttl: Presence record TTL in seconds (default: 5 min)
        """
```

**Core Methods:**

1. **set_online(user_id, zone_id, org_id)**
   - Updates presence hash with online status
   - Adds user to sorted sets (global, zone, org)
   - Sets TTL for auto-cleanup
   - Broadcasts online status via Pub/Sub
   
2. **set_offline(user_id)**
   - Updates presence with offline status + last_seen timestamp
   - Removes from online sorted sets
   - Broadcasts offline status
   
3. **set_away(user_id)**
   - Updates status to "away" (keeps in sorted sets)
   - Broadcasts away status
   
4. **update_activity(user_id)**
   - Heartbeat mechanism: updates last_activity timestamp
   - Reverts "away" back to "online" on activity
   - Prevents auto-away during active use
   
5. **get_status(user_id) → dict | None**
   - Queries individual user presence
   - Returns full status dict or None if not found
   
6. **get_online_users(zone_id, org_id, limit) → list[dict]**
   - Lists online users with optional filters
   - Sorted by last_activity (most recent first)
   - Supports zone/org scoping
   
7. **get_online_count(zone_id, org_id) → dict**
   - Returns aggregate counts: global, zone, org
   - Efficient ZCARD operations on sorted sets
   
8. **check_and_set_away(user_id) → bool**
   - Auto-away detection: checks if inactive > 5 minutes
   - Automatically sets to "away" if threshold exceeded
   - Returns True if status changed, False otherwise
   
9. **cleanup_stale_presence() → int**
   - Background cleanup of disconnected users
   - Removes stale records from sorted sets
   - Returns count of cleaned records

**Singleton Pattern:**

```python
_presence_manager_instance: Optional[PresenceManager] = None

def get_presence_manager() -> PresenceManager:
    """Get or create singleton PresenceManager instance"""
    global _presence_manager_instance
    if _presence_manager_instance is None:
        _presence_manager_instance = PresenceManager(
            redis=get_redis(),
            pubsub=get_pubsub(),
        )
    return _presence_manager_instance
```

**Background Cleanup Task:**

```python
async def presence_cleanup_task():
    """Background task to clean stale presence records (runs every 60s)"""
    presence = get_presence_manager()
    while True:
        try:
            await asyncio.sleep(60)
            cleaned = await presence.cleanup_stale_presence()
            if cleaned > 0:
                logger.info(f"Cleaned {cleaned} stale presence records")
        except Exception as e:
            logger.error(f"Error in presence cleanup: {e}")
```

---

### 2. WebSocket Integration: `websocket.py` (~50 LOC changes)

**Changes:**

1. Import PresenceManager:
   ```python
   from app.messenger.presence import get_presence_manager
   ```

2. Initialize in `__init__`:
   ```python
   self.presence = get_presence_manager()
   ```

3. **connect() method** - Set online on first connection:
   ```python
   async def connect(self, websocket, user_id, zone_id=None, org_id=None, conversations=None):
       await websocket.accept()
       self.active_connections[user_id].append(websocket)
       
       is_first_connection = len(self.active_connections[user_id]) == 1
       if is_first_connection:
           await self.presence.set_online(user_id, zone_id, org_id)
       else:
           await self.presence.update_activity(user_id)
   ```

4. **disconnect() method** - Set offline when last connection closes:
   ```python
   async def disconnect(self, websocket, user_id):
       if user_id in self.active_connections:
           self.active_connections[user_id].remove(websocket)
           
           if not self.active_connections[user_id]:
               await self.presence.set_offline(user_id)
           else:
               await self.presence.update_activity(user_id)
   ```

---

### 3. Event Handler Integration: `messenger.py` (~100 LOC)

**Added Helper Function:**

```python
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
```

**Integrated into Event Handlers:**

- `handle_message_send()` - After committing message
- `handle_message_edit()` - After updating content
- `handle_message_delete()` - After soft delete
- `handle_read_receipt()` - After creating receipt
- `typing.start` event - On typing indicator

**REST API Endpoints Added:**

```python
# GET /messenger/presence/online
# - List online users with zone/org filters
# - Returns: {"online_users": [...], "count": N}

# GET /messenger/presence/count
# - Get online user counts
# - Returns: {"global": N, "zone": N, "org": N}

# GET /messenger/presence/status/{user_id}
# - Get specific user's presence status
# - Returns: {user_id, status, last_activity, zone_id, org_id}

# POST /messenger/presence/away
# - Manually set current user to "away"
# - Returns: {"status": "away", "user_id": N}
```

---

### 4. Application Lifecycle: `main.py` (~15 LOC)

**Import:**
```python
from app.messenger.presence import presence_cleanup_task
```

**Startup Event:**
```python
@app.on_event("startup")
async def startup():
    import asyncio
    
    await start_broadcaster()
    
    # Start presence cleanup background task
    asyncio.create_task(presence_cleanup_task())
    logger.info("Presence cleanup task started successfully")
```

---

### 5. PubSub Enhancement: `pubsub.py` (~5 LOC)

**Updated publish_online_status():**

```python
async def publish_online_status(
    self,
    user_id: int,
    status: Literal["online", "offline", "away"],  # Added "away"
    metadata: Optional[dict] = None,
):
    """Publish user online status change"""
```

---

## Testing

### Test File: `test_messenger_presence.py` (320 LOC)

**Location:** `backend/tests/test_messenger_presence.py`

**Test Coverage:**

1. ✅ `test_set_online` - Verify online status, sorted set additions, broadcast
2. ✅ `test_set_offline` - Verify offline status, sorted set removals, last_seen
3. ✅ `test_set_away` - Verify away status update and broadcast
4. ✅ `test_update_activity` - Verify heartbeat updates last_activity
5. ✅ `test_get_status` - Verify status query returns correct data
6. ✅ `test_get_status_not_found` - Handle missing presence gracefully
7. ✅ `test_get_online_users_global` - List all online users
8. ✅ `test_get_online_users_with_zone` - Filter by zone_id
9. ✅ `test_get_online_count` - Aggregate counts
10. ✅ `test_check_and_set_away` - Auto-away after 5 minutes
11. ✅ `test_check_and_set_away_no_change` - No change for active users
12. ✅ `test_cleanup_stale_presence` - Background cleanup
13. ✅ `test_presence_manager_singleton` - Singleton pattern
14. ✅ `test_presence_status_enum` - Enum values

**Run Tests:**
```bash
cd backend
pytest tests/test_messenger_presence.py -v
```

---

## API Usage Examples

### REST API

**1. Get Online Users:**
```bash
curl -X GET "http://localhost:8000/messenger/presence/online?zone_id=10&limit=50" \
  -H "Authorization: Bearer $TOKEN"

Response:
{
  "online_users": [
    {
      "user_id": 1,
      "status": "online",
      "last_activity": "2024-11-26T10:30:00Z",
      "zone_id": 10,
      "org_id": 100
    },
    ...
  ],
  "count": 42
}
```

**2. Get Online Counts:**
```bash
curl -X GET "http://localhost:8000/messenger/presence/count?zone_id=10" \
  -H "Authorization: Bearer $TOKEN"

Response:
{
  "global": 1523,
  "zone": 42,
  "org": null
}
```

**3. Get User Status:**
```bash
curl -X GET "http://localhost:8000/messenger/presence/status/123" \
  -H "Authorization: Bearer $TOKEN"

Response:
{
  "user_id": 123,
  "status": "away",
  "last_activity": "2024-11-26T10:25:00Z",
  "zone_id": 10,
  "org_id": 100
}
```

**4. Set Away Manually:**
```bash
curl -X POST "http://localhost:8000/messenger/presence/away" \
  -H "Authorization: Bearer $TOKEN"

Response:
{
  "status": "away",
  "user_id": 1
}
```

### WebSocket Integration

**Presence is automatically tracked:**

1. **On Connect:** User set to "online" (with zone_id/org_id if provided)
2. **On Activity:** Any message/edit/typing updates last_activity
3. **Auto-Away:** After 5 minutes of inactivity → "away"
4. **On Disconnect:** When last connection closes → "offline"

**WebSocket Connect with Presence:**
```javascript
const ws = new WebSocket(
  `ws://localhost:8000/messenger/ws?token=${token}&zone_id=10&org_id=100`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "system" && data.event === "connected") {
    console.log("Connected with presence:", data.presence);
  }
};
```

---

## Performance Characteristics

### Redis Operations Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| set_online | O(log N) per sorted set | 3 ZADD operations (global, zone, org) |
| set_offline | O(log N) per sorted set | 3 ZREM operations |
| set_away | O(1) | HSET only, no sorted set changes |
| update_activity | O(1) | HSET only |
| get_status | O(1) | HGETALL single key |
| get_online_users | O(log N + M) | ZREVRANGE + M * HGETALL |
| get_online_count | O(1) | ZCARD per set |

### Memory Usage

**Per User:**
- Hash: ~200 bytes (status, timestamps, IDs)
- Sorted Sets: ~80 bytes per set (member + score)
- **Total: ~440 bytes per online user**

**Scale Estimate:**
- 1,000 users: ~440 KB
- 10,000 users: ~4.4 MB
- 100,000 users: ~44 MB
- **1,000,000 users: ~440 MB** ✅ (MegaCity target)

### Network Efficiency

- Presence updates: Fire-and-forget (no blocking)
- Pub/Sub broadcasts: O(N) to all subscribers
- Background cleanup: Every 60 seconds (low overhead)

---

## Deployment Considerations

### 1. Multi-Server Setup

✅ **Redis-based = Distributed State**
- No single server memory bottleneck
- Presence survives server restarts
- Load balancer can route to any instance

### 2. Redis Persistence

```redis
# Recommended redis.conf settings:
save 900 1        # Save after 15 min if ≥1 key changed
save 300 10       # Save after 5 min if ≥10 keys changed
save 60 10000     # Save after 1 min if ≥10K keys changed

appendonly yes    # AOF for durability
appendfsync everysec
```

### 3. Monitoring

**Key Metrics:**
```python
# Total online users
redis-cli ZCARD online:global

# Zone-specific counts
redis-cli ZCARD online:zone:10

# Memory usage
redis-cli INFO memory
```

### 4. Cleanup Job

Background task runs every 60 seconds:
- Checks global sorted set for stale entries
- Removes records with last_activity > 5 minutes ago
- Auto-cleanup prevents memory leaks

---

## Future Enhancements

### Short-Term (Optional)

1. **Custom Statuses:**
   ```python
   # "Do Not Disturb", "In Meeting", "On Break"
   await presence.set_custom_status(user_id, "in_meeting")
   ```

2. **Presence Webhooks:**
   ```python
   # Trigger external notifications on status changes
   @app.on_event("presence_changed")
   async def on_presence_changed(user_id, old_status, new_status):
       await notify_external_service(user_id, new_status)
   ```

3. **Typing Indicator Persistence:**
   ```python
   # Store active typing state in Redis
   await presence.set_typing(user_id, conversation_id, typing=True)
   ```

### Long-Term

1. **Presence History:**
   - Track daily online time per user
   - Generate activity reports
   - Identify inactive users

2. **Geo-Location:**
   - Add `location` field to presence hash
   - Filter online users by proximity

3. **Device Tracking:**
   - Track which devices user is connected from
   - "Online on Mobile" vs "Online on Desktop"

---

## Troubleshooting

### Issue: Users stuck in "online" state after disconnect

**Cause:** WebSocket disconnect not handled properly

**Solution:**
1. Check `websocket.py disconnect()` called on all exit paths
2. Verify background cleanup task is running
3. Reduce TTL if needed: `PresenceManager(ttl=300)`

### Issue: Auto-away not working

**Cause:** `update_activity()` called too frequently

**Solution:**
1. Only call on significant actions (message send, not every typing)
2. Check `away_threshold` setting (default: 300 seconds)
3. Verify `check_and_set_away()` logic

### Issue: High Redis memory usage

**Cause:** Stale presence records not cleaned

**Solution:**
1. Ensure `presence_cleanup_task()` running in main.py
2. Check cleanup logs: `grep "Cleaned" logs/backend.log`
3. Manually cleanup: `await presence.cleanup_stale_presence()`

### Issue: Incorrect online counts

**Cause:** Sorted set and hash out of sync

**Solution:**
1. Rebuild sorted sets from hashes:
   ```python
   # Manual rebuild script
   async def rebuild_sorted_sets():
       presence = get_presence_manager()
       # Scan all presence:* keys
       # Re-add to sorted sets if status=online
   ```

---

## LOC Summary

| Component | LOC | Description |
|-----------|-----|-------------|
| `presence.py` | 570 | Core PresenceManager class |
| `websocket.py` | 50 | Integration in connect/disconnect |
| `messenger.py` | 100 | Event handlers + REST API |
| `main.py` | 15 | Lifecycle management |
| `pubsub.py` | 5 | "away" status support |
| `test_messenger_presence.py` | 320 | Unit tests (14 scenarios) |
| **Total** | **1,060** | Task 2.2 complete |

**Cumulative Project LOC:** 5,110 (1.2 → 1.4 → 1.1 → 2.1 → 2.2)

---

## ✅ Task 2.2 Complete

**Status:** PRODUCTION READY

**Tested:** Unit tests pass (14/14)  
**Integrated:** WebSocket, REST API, Background tasks  
**Documented:** Complete API reference, examples, troubleshooting  

**Next Steps:**
- Task 2.3: File Upload & Storage (CDN, thumbnails, virus scan)
- Task 2.4: Push Notifications (FCM, APNs, web push)
- Task 2.5: Search & Discovery (full-text search, filters)

---

**Implementation by:** GitHub Copilot (Claude Sonnet 4.5)  
**Date:** November 26, 2024
