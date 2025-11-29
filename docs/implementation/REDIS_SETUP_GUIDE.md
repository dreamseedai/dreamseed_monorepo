"""
Redis Configuration and Setup Guide for Adaptive Testing

This guide explains how to set up Redis for production-ready adaptive testing.

## Why Redis?

The adaptive testing system uses Redis to store engine state (theta, item history, responses)
across API requests. Benefits:

1. **Persistence**: Engine state survives server restarts
2. **Scalability**: Works across multiple app instances (Cloud Run)
3. **Performance**: Fast in-memory storage
4. **TTL**: Automatic cleanup of abandoned exams

## Architecture

```
┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Student    │────▶│  FastAPI    │────▶│  PostgreSQL  │
│   (Client)   │     │   Router    │     │  (Database)  │
└──────────────┘     └─────────────┘     └──────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │    Redis    │
                     │ (Engine     │
                     │  State)     │
                     └─────────────┘
```

- **PostgreSQL**: Source of truth (Items, ExamSessions, Attempts)
- **Redis**: Fast cache for engine state (theta, responses, item history)
- **Recovery**: If Redis fails, engine reconstructs state from PostgreSQL Attempts table

## Setup Instructions

### 1. Local Development (Docker Compose)

Add Redis service to `docker-compose.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: dreamseed_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  backend:
    # ... existing backend config ...
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

volumes:
  redis_data:
```

Start services:
```bash
docker-compose up -d redis
docker-compose ps  # Verify redis is running
```

### 2. Local Development (Standalone Redis)

Install Redis:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server

# Test connection
redis-cli ping  # Should return PONG
```

### 3. Production (Google Cloud Platform)

Use Cloud Memorystore (managed Redis):

```bash
# Create Redis instance
gcloud redis instances create dreamseed-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_7_0 \
    --tier=basic

# Get connection info
gcloud redis instances describe dreamseed-redis \
    --region=us-central1 \
    --format="get(host,port)"

# Connect from Cloud Run
# Set REDIS_URL in Cloud Run environment:
# redis://<REDIS_HOST>:6379/0
```

Cost estimate: ~$50/month for 1GB Basic tier

### 4. Production (Alternative: Redis Cloud)

Free tier available at https://redis.com/try-free/

1. Create account and instance
2. Get connection URL
3. Set as environment variable:
   ```
   REDIS_URL=redis://default:<password>@<host>:6379/0
   ```

## Environment Variables

Set in `.env` file:

```bash
# Option 1: Full Redis URL (recommended)
REDIS_URL=redis://localhost:6379/0

# Option 2: Individual settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional

# Production settings
REDIS_URL=redis://10.0.0.3:6379/0  # Cloud Memorystore internal IP
```

## Testing Redis Connection

Run health check:

```python
from app.core.redis import ping_redis

# In async context
if await ping_redis():
    print("✅ Redis is ready")
else:
    print("❌ Redis connection failed")
```

Command line test:
```bash
cd backend
python -c "
import asyncio
from app.core.redis import ping_redis

async def test():
    result = await ping_redis()
    print('Redis OK' if result else 'Redis FAILED')

asyncio.run(test())
"
```

## Key Format and Data Structure

### Redis Key Format
```
adaptive_engine:{exam_session_id}
```

Example: `adaptive_engine:123`

### Value Structure (JSON)
```json
{
  "theta": 0.523,
  "standard_error": 0.245,
  "item_params_list": [
    {"a": 1.5, "b": 0.2, "c": 0.2},
    {"a": 1.2, "b": -0.5, "c": 0.15}
  ],
  "responses": [true, false, true],
  "max_items": 20,
  "items_completed": 3
}
```

### TTL (Time To Live)
- Default: 3600 seconds (1 hour)
- For longer exams: 7200 seconds (2 hours)
- Prevents memory leaks from abandoned exams
- Auto-deleted when exam completes

## Monitoring Redis

### Check Active Sessions
```python
from app.services.adaptive_state_store import AdaptiveEngineStateStore
from app.core.redis import get_redis

redis_client = get_redis()
store = AdaptiveEngineStateStore(redis_client)

# Get all active exam session IDs
active = await store.get_all_active_sessions()
print(f"Active exams: {len(active)}")

# Get summary for specific session
summary = await store.get_engine_summary(exam_session_id=123)
print(f"Theta: {summary['theta']}, Items: {summary['items_completed']}")
```

### Redis CLI Commands
```bash
# Connect to Redis
redis-cli

# List all engine keys
KEYS adaptive_engine:*

# Get specific engine state
GET adaptive_engine:123

# Check TTL
TTL adaptive_engine:123

# Count active sessions
DBSIZE

# Clear all engine states (dev only!)
FLUSHDB
```

### Memory Usage
```bash
redis-cli INFO memory
```

Look for:
- `used_memory_human`: Total memory used
- `maxmemory`: Memory limit
- `eviction_policy`: What happens when full (should be "noeviction")

## Performance Optimization

### Connection Pooling
The `get_redis()` function uses `@lru_cache` to maintain a single connection pool:

```python
# ✅ Good - reuses connection
redis_client = get_redis()
await redis_client.set("key", "value")

# ❌ Bad - creates new pool each time
for i in range(100):
    client = get_redis()  # Wasteful
    await client.set(f"key{i}", "value")
```

### Batch Operations
For multiple operations, use pipeline:

```python
redis_client = get_redis()
pipe = redis_client.pipeline()

for session_id in [1, 2, 3, 4, 5]:
    await pipe.get(f"adaptive_engine:{session_id}")

results = await pipe.execute()
```

### TTL Extension
For long exams (>1 hour), extend TTL:

```python
# After 30 minutes, add 1 hour
await store.extend_ttl(exam_session_id=123, additional_seconds=3600)
```

## Error Handling

### Redis Down - Automatic Fallback
If Redis is unavailable, the system automatically:

1. Creates new engine from DB session state
2. Reconstructs history from Attempts table
3. Continues operation (with slight performance penalty)

Example:
```python
# This always works, even if Redis is down
engine = await state_store.load_engine(
    exam_session_id=123,
    initial_theta=0.5
)

# If Redis has no state, it rebuilds from DB
# No exception thrown - transparent recovery
```

### Monitoring Redis Health
Add health check endpoint:

```python
@router.get("/health/redis")
async def redis_health():
    from app.core.redis import ping_redis
    
    is_healthy = await ping_redis()
    
    return {
        "redis": "up" if is_healthy else "down",
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Troubleshooting

### Issue: Connection Refused
```
redis.exceptions.ConnectionError: Error connecting to localhost:6379
```

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# If not, start Redis
redis-server

# Or with Docker
docker-compose up -d redis
```

### Issue: Authentication Failed
```
redis.exceptions.AuthenticationError: Authentication required
```

**Solution**: Set password in environment:
```bash
REDIS_URL=redis://:yourpassword@localhost:6379/0
```

### Issue: Out of Memory
```
redis.exceptions.ResponseError: OOM command not allowed
```

**Solution**: Increase Redis memory or set TTL:
```bash
# In redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru

# Or restart with limit
redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Issue: Stale Engine States
Old exam sessions cluttering Redis?

**Solution**: Run cleanup script:
```python
from app.core.redis import clear_redis_cache

# Clear all engine states older than 2 hours
await clear_redis_cache("adaptive_engine:*")
```

## Testing with Fake Redis

For unit tests, use fake Redis (no server needed):

```python
import pytest
from fakeredis import aioredis as fakeredis

@pytest.fixture
async def fake_redis():
    client = fakeredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()

@pytest.fixture
async def fake_state_store(fake_redis):
    from app.services.adaptive_state_store import AdaptiveEngineStateStore
    return AdaptiveEngineStateStore(fake_redis)

# Override dependency in tests
app.dependency_overrides[get_redis] = lambda: fake_redis
```

Install fake Redis:
```bash
pip install fakeredis[aioredis]
```

## Migration from ENGINE_CACHE

Old code (in-memory dict):
```python
# ❌ Old - doesn't scale, lost on restart
ENGINE_CACHE[exam_sess.id] = engine
engine = ENGINE_CACHE.get(exam_sess.id)
ENGINE_CACHE.pop(exam_sess.id)
```

New code (Redis):
```python
# ✅ New - persistent, scalable
await state_store.save_engine(exam_sess.id, engine)
engine = await state_store.load_engine(exam_sess.id)
await state_store.delete_engine(exam_sess.id)
```

No other code changes needed!

## Cost Analysis

### Development
- Local Redis: **Free** (self-hosted)
- Docker Redis: **Free** (included in compose)

### Production (Google Cloud)
- Cloud Memorystore Basic 1GB: **~$50/month**
- Cloud Memorystore Standard 1GB (HA): **~$100/month**

### Production (Redis Cloud)
- Free tier: **$0** (30MB, limited ops)
- Essential 250MB: **$10/month**
- Production 1GB: **$35/month**

### Estimate Usage
- Each engine state: ~500 bytes
- 100 concurrent exams: ~50KB
- 1000 concurrent exams: ~500KB
- ✅ 1GB Redis handles 10,000+ concurrent exams

## Security Considerations

1. **Network Isolation**: Keep Redis on private network (VPC)
2. **Authentication**: Use password for Redis (`requirepass` in redis.conf)
3. **TLS**: Enable for production (Cloud Memorystore supports TLS)
4. **Firewall**: Only allow app servers to access Redis port

Example production URL:
```bash
# With TLS and auth
REDIS_URL=rediss://:password@host:6380/0
```

## Next Steps

1. ✅ Add Redis to docker-compose.yml
2. ✅ Set REDIS_URL environment variable
3. ✅ Test connection with `ping_redis()`
4. ✅ Run adaptive exam E2E test
5. ✅ Monitor Redis memory usage
6. 🔄 Deploy to Cloud Run with Cloud Memorystore
7. 🔄 Set up Redis monitoring alerts

## References

- Redis Documentation: https://redis.io/docs/
- Google Cloud Memorystore: https://cloud.google.com/memorystore
- Redis Cloud: https://redis.com/
- redis-py async: https://redis-py.readthedocs.io/en/stable/
