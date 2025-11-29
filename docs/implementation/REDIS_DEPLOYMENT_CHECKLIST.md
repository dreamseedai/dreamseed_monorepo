# Redis Upgrade Deployment Checklist

## 🎯 Objective
Upgrade adaptive testing system from in-memory ENGINE_CACHE to Redis-based persistent state storage.

## ✅ Completed (by this upgrade)

- [x] Created `backend/app/core/redis.py` - Redis client singleton
- [x] Created `backend/app/services/adaptive_state_store.py` - Engine state persistence layer
- [x] Updated `backend/app/api/routers/adaptive_exam.py` - Redis integration
- [x] Created `docs/implementation/REDIS_SETUP_GUIDE.md` - Complete setup documentation
- [x] Created `backend/tests/test_adaptive_exam_redis.py` - Redis E2E tests

## 📋 Deployment Steps

### Step 1: Install Redis Dependencies

```bash
cd backend
pip install redis[hiredis] fakeredis[aioredis]
pip freeze > requirements.txt  # Update requirements
```

### Step 2: Set Up Redis (Choose One)

**Option A: Docker Compose (Recommended for Dev)**
```bash
# Add to docker-compose.yml:
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

# Start
docker-compose up -d redis

# Verify
docker-compose ps
redis-cli ping  # Should return PONG
```

**Option B: Local Redis**
```bash
# Install
sudo apt-get install redis-server  # Ubuntu
brew install redis                 # macOS

# Start
redis-server

# Verify
redis-cli ping
```

**Option C: Cloud Memorystore (Production)**
```bash
gcloud redis instances create dreamseed-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_7_0 \
    --tier=basic
```

### Step 3: Configure Environment Variables

Add to `.env` file:
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Or for production:
# REDIS_URL=redis://10.0.0.3:6379/0  # Cloud Memorystore IP
```

### Step 4: Test Redis Connection

```bash
cd backend
python -c "
import asyncio
from app.core.redis import ping_redis

async def test():
    if await ping_redis():
        print('✅ Redis connection successful')
    else:
        print('❌ Redis connection failed')

asyncio.run(test())
"
```

### Step 5: Run Tests

```bash
# Run Redis-specific tests
pytest backend/tests/test_adaptive_exam_redis.py -v

# Expected output:
# ✅ test_redis_engine_persistence PASSED
# ✅ test_redis_state_recovery_from_db PASSED
# ✅ test_redis_ttl_extension PASSED
# ✅ test_concurrent_exams_redis PASSED
# ✅ test_redis_cleanup_on_completion PASSED
# ✅ test_theta_consistency_redis_vs_db PASSED
# ✅ test_redis_performance_100_concurrent_saves PASSED
# ✅ test_redis_performance_load_speed PASSED

# Run all adaptive exam tests
pytest backend/tests/test_adaptive_exam*.py -v
```

### Step 6: Interactive Demo

```bash
cd backend
python -m pytest backend/tests/test_adaptive_exam_redis.py::run_interactive_redis_exam -s

# Should display:
# 📝 Exam Started (ID: 1)
# 📊 Item 1/5: θ: +0.234
# 📊 Item 2/5: θ: +0.456
# ...
# ✅ Exam Completed
```

### Step 7: Verify Migration Success

Check that old ENGINE_CACHE code is removed:
```bash
cd backend
grep -r "ENGINE_CACHE" app/

# Should return: No matches (or only in comments)
```

Check that Redis is used:
```bash
grep -r "state_store" app/api/routers/adaptive_exam.py

# Should show multiple matches in /start, /answer, /next, /complete
```

### Step 8: Manual E2E Test

```bash
# Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# In another terminal, test API:
# 1. Start exam
curl -X POST http://localhost:8000/api/adaptive/start \
  -H "Content-Type: application/json" \
  -d '{"exam_type": "placement", "max_items": 10}'

# Response: {"exam_session_id": 1, ...}

# 2. Get next item
curl http://localhost:8000/api/adaptive/next?exam_session_id=1

# Response: {"item": {"id": 5, ...}, "current_theta": 0.0}

# 3. Submit answer
curl -X POST http://localhost:8000/api/adaptive/answer \
  -H "Content-Type: application/json" \
  -d '{"exam_session_id": 1, "item_id": 5, "correct": true}'

# Response: {"theta": 0.234, "standard_error": 0.45, ...}

# 4. Check Redis
redis-cli GET "adaptive_engine:1"
# Should show JSON with theta, responses, etc.
```

## 🔍 Verification Checklist

- [ ] Redis server is running (`redis-cli ping` returns PONG)
- [ ] Environment variable `REDIS_URL` is set
- [ ] Python can import `redis` and `fakeredis`
- [ ] `ping_redis()` returns True
- [ ] All tests pass (8/8 in test_adaptive_exam_redis.py)
- [ ] Interactive demo runs successfully
- [ ] Manual E2E test works (start → next → answer)
- [ ] Redis keys appear (`redis-cli KEYS "adaptive_engine:*"`)
- [ ] Engine state persists across API calls
- [ ] Engine state deleted after exam completion

## 📊 Monitoring (Post-Deployment)

### Check Active Sessions
```python
from app.services.adaptive_state_store import AdaptiveEngineStateStore
from app.core.redis import get_redis

redis_client = get_redis()
store = AdaptiveEngineStateStore(redis_client)

# Count active exams
active = await store.get_all_active_sessions()
print(f"Active exams: {len(active)}")
```

### Redis CLI Monitoring
```bash
# Count keys
redis-cli DBSIZE

# List all engine keys
redis-cli KEYS "adaptive_engine:*"

# Monitor memory
redis-cli INFO memory | grep used_memory_human

# Watch commands in real-time
redis-cli MONITOR
```

### Health Check Endpoint (Optional)
Add to `adaptive_exam.py`:
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

Test:
```bash
curl http://localhost:8000/api/adaptive/health/redis
# Response: {"redis": "up", "timestamp": "2024-11-20T..."}
```

## 🚨 Rollback Plan (If Issues Occur)

If Redis causes problems, you can temporarily revert:

1. **Quick Fix**: Comment out Redis dependency override in tests
   ```python
   # app.dependency_overrides[get_redis] = override_get_redis  # Comment this
   ```

2. **Restore ENGINE_CACHE**: Revert to previous commit
   ```bash
   git log --oneline | grep "adaptive"  # Find pre-Redis commit
   git checkout <commit-hash> -- backend/app/api/routers/adaptive_exam.py
   ```

3. **Disable Redis**: Set fallback in `adaptive_state_store.py`
   ```python
   # In load_engine(): Always return new engine if Redis unavailable
   try:
       raw = await self.redis.get(key)
   except Exception as e:
       logger.warning(f"Redis unavailable, using DB fallback: {e}")
       return AdaptiveEngine(initial_theta=initial_theta)
   ```

## 📈 Performance Expectations

| Metric | Before (ENGINE_CACHE) | After (Redis) |
|--------|----------------------|---------------|
| Load time | ~0.001ms (in-memory) | ~1-5ms (Redis) |
| Save time | ~0.001ms (in-memory) | ~1-5ms (Redis) |
| State persistence | ❌ Lost on restart | ✅ Survives restart |
| Horizontal scaling | ❌ Single instance | ✅ Multi-instance |
| Concurrent exams | ⚠️ Memory leak risk | ✅ TTL auto-cleanup |

**Verdict**: Slight performance trade-off (~5ms latency) for production-grade persistence and scalability.

## 🎓 Next Steps (Optional Enhancements)

1. **Add Redis Sentinel** (High Availability)
   - Auto-failover if Redis master fails
   - Cost: +$50/month for Cloud Memorystore Standard tier

2. **Add Prometheus Metrics**
   ```python
   from prometheus_client import Counter, Histogram
   
   redis_ops = Counter('redis_operations_total', 'Redis ops', ['operation'])
   redis_latency = Histogram('redis_operation_seconds', 'Redis latency')
   
   @redis_latency.time()
   async def save_engine(...):
       redis_ops.labels(operation='save').inc()
       # ... existing code
   ```

3. **Add Redis Cluster** (Sharding)
   - For >10,000 concurrent exams
   - Horizontal scaling of Redis itself

4. **Add Background State Sync**
   - Periodic sync from DB to Redis
   - Recover from Redis data loss automatically

## 📚 References

- **Redis Setup Guide**: `docs/implementation/REDIS_SETUP_GUIDE.md`
- **Test Suite**: `backend/tests/test_adaptive_exam_redis.py`
- **Router Code**: `backend/app/api/routers/adaptive_exam.py`
- **State Store**: `backend/app/services/adaptive_state_store.py`
- **Redis Client**: `backend/app/core/redis.py`

## ✅ Sign-Off

- [ ] Developer: Tested locally and all checks pass
- [ ] DevOps: Redis deployed and monitored
- [ ] QA: E2E tests executed successfully
- [ ] PM: Performance metrics acceptable

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Redis Version**: _______________  
**Environment**: [ ] Dev [ ] Staging [ ] Production  

---

**Status**: 🟢 Ready to Deploy  
**Risk Level**: 🟡 Low (fallback to DB available)  
**Estimated Time**: 30 minutes  
**Rollback Time**: 5 minutes
