# Redis Quick Reference for Adaptive Testing

## 🚀 Quick Start (30 seconds)

```bash
# 1. Start Redis
docker-compose up -d redis  # or: redis-server

# 2. Set environment
export REDIS_URL=redis://localhost:6379/0

# 3. Test
python -c "import asyncio; from app.core.redis import ping_redis; print('✅ OK' if asyncio.run(ping_redis()) else '❌ FAILED')"
```

---

## 📝 Code Examples

### Basic Usage
```python
from app.core.redis import get_redis
from app.services.adaptive_state_store import AdaptiveEngineStateStore
from app.services.exam_engine import AdaptiveEngine

# Get dependencies
redis_client = get_redis()
store = AdaptiveEngineStateStore(redis_client)

# Save engine
engine = AdaptiveEngine(initial_theta=0.5)
await store.save_engine(exam_session_id=123, engine=engine)

# Load engine
engine = await store.load_engine(exam_session_id=123)

# Delete engine
await store.delete_engine(exam_session_id=123)
```

### In Router (FastAPI)
```python
from fastapi import Depends
from app.services.adaptive_state_store import AdaptiveEngineStateStore
from app.core.redis import get_redis

async def get_state_store(redis_client = Depends(get_redis)):
    return AdaptiveEngineStateStore(redis_client)

@router.post("/answer")
async def submit_answer(
    exam_session_id: int,
    state_store: AdaptiveEngineStateStore = Depends(get_state_store)
):
    # Load engine from Redis
    engine = await state_store.load_engine(exam_session_id)
    
    # Update engine
    engine.record_attempt(...)
    
    # Save back to Redis
    await state_store.save_engine(exam_session_id, engine)
```

---

## 🔧 Common Operations

### Check Connection
```bash
redis-cli ping  # Should return: PONG
```

### List All Engines
```bash
redis-cli KEYS "adaptive_engine:*"
```

### Get Engine State
```bash
redis-cli GET "adaptive_engine:123"
```

### Count Active Exams
```bash
redis-cli DBSIZE
```

### Delete Specific Engine
```bash
redis-cli DEL "adaptive_engine:123"
```

### Clear All Engines (DEV ONLY!)
```bash
redis-cli FLUSHDB
```

---

## 🐛 Troubleshooting

### Issue: Connection Refused
```bash
# Check if Redis is running
redis-cli ping

# If not running:
docker-compose up -d redis  # Docker
# or
redis-server  # Local
```

### Issue: Redis Not Found
```bash
# Install
pip install redis[hiredis]
```

### Issue: Can't Import get_redis
```python
# Check file exists
ls -la backend/app/core/redis.py

# If missing, copy from backup or git
git checkout HEAD -- backend/app/core/redis.py
```

### Issue: State Not Persisting
```python
# Check TTL
redis-cli TTL "adaptive_engine:123"
# If -2: Key doesn't exist
# If -1: Key has no TTL (permanent)
# If >0: TTL remaining in seconds

# Check save is being called
await state_store.save_engine(exam_session_id, engine, ttl_sec=7200)
```

---

## 📊 Monitoring

### Python
```python
# Get all active sessions
active = await store.get_all_active_sessions()
print(f"Active exams: {len(active)}")

# Get engine summary
summary = await store.get_engine_summary(exam_session_id=123)
print(f"θ={summary['theta']:.3f}, items={summary['items_completed']}")

# Check if engine exists
exists = await store.exists(exam_session_id=123)
```

### Redis CLI
```bash
# Real-time monitoring
redis-cli MONITOR

# Memory usage
redis-cli INFO memory

# Server stats
redis-cli INFO stats

# Slow queries (>10ms)
redis-cli SLOWLOG get 10
```

---

## ⚡ Performance Tips

### ✅ DO
```python
# Reuse client (singleton pattern)
redis_client = get_redis()  # Cached with @lru_cache

# Use pipeline for batch operations
pipe = redis_client.pipeline()
await pipe.get("key1")
await pipe.get("key2")
results = await pipe.execute()
```

### ❌ DON'T
```python
# Don't create new client each time
for i in range(100):
    client = get_redis()  # Wasteful!
    await client.set(f"key{i}", "value")

# Don't forget TTL
await store.save_engine(exam_id, engine)  # ❌ No TTL = memory leak
await store.save_engine(exam_id, engine, ttl_sec=7200)  # ✅
```

---

## 🧪 Testing

### Unit Test with Fake Redis
```python
import pytest
from fakeredis import aioredis as fakeredis

@pytest.fixture
async def fake_redis():
    client = fakeredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()

@pytest.mark.asyncio
async def test_my_feature(fake_redis):
    store = AdaptiveEngineStateStore(fake_redis)
    # Test without real Redis server
```

### E2E Test
```bash
pytest backend/tests/test_adaptive_exam_redis.py -v
```

### Interactive Demo
```bash
python -m pytest backend/tests/test_adaptive_exam_redis.py::run_interactive_redis_exam -s
```

---

## 🔐 Security

### Production Configuration
```bash
# Use password
REDIS_URL=redis://:yourpassword@host:6379/0

# Use TLS
REDIS_URL=rediss://:password@host:6380/0

# Use private network (GCP)
REDIS_URL=redis://10.0.0.3:6379/0  # Internal IP only
```

### Redis Config
```bash
# redis.conf
requirepass yourpassword
bind 127.0.0.1  # Local only
maxmemory 256mb
maxmemory-policy allkeys-lru
```

---

## 💰 Cost Estimates

| Environment | Solution | Cost/Month |
|-------------|----------|------------|
| **Local Dev** | Docker Redis | $0 |
| **Staging** | Redis Cloud 250MB | $10 |
| **Production** | GCP Memorystore 1GB Basic | $50 |
| **Production HA** | GCP Memorystore 1GB Standard | $100 |

**Usage estimate**: 1GB = ~10,000 concurrent exams

---

## 📚 API Reference

### AdaptiveEngineStateStore

#### `load_engine(exam_session_id, initial_theta=0.0, max_items=20)`
Load engine from Redis or create new.

**Returns**: `AdaptiveEngine` instance

**Example**:
```python
engine = await store.load_engine(123, initial_theta=0.5)
```

#### `save_engine(exam_session_id, engine, ttl_sec=3600)`
Save engine to Redis with TTL.

**Returns**: `bool` (True if success)

**Example**:
```python
success = await store.save_engine(123, engine, ttl_sec=7200)
```

#### `delete_engine(exam_session_id)`
Delete engine from Redis.

**Returns**: `bool` (True if deleted)

**Example**:
```python
await store.delete_engine(123)
```

#### `exists(exam_session_id)`
Check if engine exists.

**Returns**: `bool`

**Example**:
```python
if await store.exists(123):
    print("Engine exists")
```

#### `get_ttl(exam_session_id)`
Get remaining TTL.

**Returns**: `int` (seconds, -2 if not exists, -1 if no TTL)

**Example**:
```python
ttl = await store.get_ttl(123)
print(f"Expires in {ttl}s")
```

#### `extend_ttl(exam_session_id, additional_seconds)`
Extend TTL.

**Returns**: `bool`

**Example**:
```python
await store.extend_ttl(123, additional_seconds=3600)  # +1 hour
```

#### `get_all_active_sessions()`
Get all active exam session IDs.

**Returns**: `List[int]`

**Example**:
```python
active = await store.get_all_active_sessions()
print(f"Active: {len(active)} exams")
```

#### `get_engine_summary(exam_session_id)`
Get summary without loading full engine.

**Returns**: `Dict` or `None`

**Example**:
```python
summary = await store.get_engine_summary(123)
print(f"θ={summary['theta']}, items={summary['items_completed']}")
```

---

## 🎯 Redis Key Format

```
adaptive_engine:{exam_session_id}
```

**Value (JSON)**:
```json
{
  "theta": 0.523,
  "standard_error": 0.245,
  "item_params_list": [
    {"a": 1.5, "b": 0.2, "c": 0.2}
  ],
  "responses": [true, false, true],
  "max_items": 20,
  "items_completed": 3
}
```

---

## 🔄 Recovery Flow

```
┌─────────────┐
│ Load Engine │
└──────┬──────┘
       │
       ▼
┌──────────────┐      ┌─────────────┐
│ Redis Exists?│─Yes─▶│ Use Redis   │
└──────┬───────┘      └─────────────┘
       │ No
       ▼
┌──────────────┐
│ Load from DB │ ← Automatic fallback
│ (Attempts)   │
└──────────────┘
```

**Transparent**: No error thrown if Redis is down!

---

## 📞 Support

- **Setup Guide**: `docs/implementation/REDIS_SETUP_GUIDE.md`
- **Deployment**: `docs/implementation/REDIS_DEPLOYMENT_CHECKLIST.md`
- **Migration**: `docs/implementation/REDIS_MIGRATION_SUMMARY.md`
- **Tests**: `backend/tests/test_adaptive_exam_redis.py`

---

## ✅ Pre-Flight Checklist

Before deploying:

- [ ] Redis server running (`redis-cli ping`)
- [ ] `REDIS_URL` environment variable set
- [ ] Dependencies installed (`pip install redis[hiredis]`)
- [ ] Tests passing (`pytest test_adaptive_exam_redis.py`)
- [ ] Connection test OK (`ping_redis()` returns True)
- [ ] Manual E2E test successful (start → answer → check Redis)

---

**Quick Links**:
- Redis Docs: https://redis.io/docs/
- redis-py: https://redis-py.readthedocs.io/
- GCP Memorystore: https://cloud.google.com/memorystore

**Status**: 🟢 Production Ready  
**Last Updated**: November 20, 2025
