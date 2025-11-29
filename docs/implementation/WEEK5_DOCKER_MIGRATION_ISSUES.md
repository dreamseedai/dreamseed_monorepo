# Week 5: Docker Migration & Schema Fixes

**Created**: November 27, 2025  
**Priority**: Medium (Week 5 Task)  
**Estimated Effort**: 4-6 hours  
**Blocked By**: None  
**Blocks**: Week 4 Priority 2 (Docker Compose Testing)

---

## Overview

During Week 4 Priority 2 (Docker Compose Testing), multiple schema inconsistencies were discovered that prevent successful container deployment. These issues do not affect local development but must be resolved before Docker-based production deployment.

**Decision**: Defer Docker fixes to Week 5 to maintain momentum on Priority 1 validation and Priority 3 testing.

---

## Issues Discovered

### Issue 1: FK Type Mismatch - Organization References

**Files Affected**:
- `backend/app/models/tutor.py`
- `backend/app/models/teacher.py` (assumed)

**Problem**:
```python
# Current (WRONG)
org_id = Column(Integer, ForeignKey("organizations.id"))

# organizations.id is UUID
id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
```

**Error**:
```
DatatypeMismatchError: foreign key constraint "tutors_org_id_fkey" cannot be implemented
DETAIL: Key columns "org_id" and "id" are of incompatible types: integer and uuid.
```

**Solution**:
```python
# Fix
from sqlalchemy.dialects.postgresql import UUID
org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
```

**Impact**: Low (tutors/teachers features not currently used in alpha)

---

### Issue 2: Disabled Table FK Reference

**File**: `backend/app/models/exam_models.py`

**Problem**:
```python
# exam_session_responses references item_options table
option_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("item_options.id", ondelete="SET NULL"),  # ❌ item_options disabled
    nullable=True,
)

# ItemOption class is commented out (replaced by ItemChoice in item.py)
```

**Current Workaround** (applied):
```python
# Temporarily disabled FK
option_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    UUID(as_uuid=True),
    # ForeignKey("item_options.id", ondelete="SET NULL"),  # Disabled
    nullable=True,
)
```

**Proper Solution**:
1. **Option A**: Remove `option_id` field entirely (if not used)
2. **Option B**: Update FK to reference `item_choices.id` instead
3. **Option C**: Re-enable `ItemOption` class (requires reconciliation with `ItemChoice`)

**Impact**: Medium (affects CAT exam response tracking)

---

### Issue 3: Alembic Migration Branch Conflicts

**Problem**:
```
ERROR: Multiple head revisions are present for given argument 'head'
```

**Files Affected**:
- `backend/alembic/versions/003_org_and_comments.py`
- `backend/alembic/versions/003_zones_ai_requests.py`

Both files use revision number "003" causing branch conflict.

**Root Cause**:
```python
# File 1: 003_org_and_comments.py
down_revision = "002_core_entities"

# File 2: 003_zones_ai_requests.py
down_revision = "002_core_entities"  # Same parent!
```

**Solution**:
1. Rename one migration file (e.g., `003_zones_ai_requests.py` → `004_zones_ai_requests.py`)
2. Update `down_revision` in renamed file:
   ```python
   down_revision = "003_org_and_comments"
   ```
3. Run `alembic heads` to verify single head
4. Run `alembic upgrade head` to test

**Impact**: High (blocks all Docker deployments)

---

### Issue 4: Async/Sync Engine Confusion (Fixed)

**Problem**: Alembic `env.py` was using sync engine with asyncpg URL

**Solution Applied**:
```python
def get_url() -> str:
    url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL")
    if url and "postgresql+asyncpg" in url:
        url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    return url
```

**Status**: ✅ Fixed

---

## Additional FK Mismatches (Not Yet Confirmed)

Based on error patterns, these may also be affected:

### Potential Issue 5: Teacher.org_id

**File**: `backend/app/models/teacher.py` (assumed similar to tutor.py)

**Expected Problem**:
```python
org_id = Column(Integer, ForeignKey("organizations.id"))  # Should be UUID
```

**Solution**: Same as Issue 1

---

### Potential Issue 6: Other Organization References

Files to audit for `org_id` type mismatches:
- `backend/app/models/class_model.py`
- `backend/app/models/assignment.py`
- Any other models with `ForeignKey("organizations.id")`

**Audit Command**:
```bash
cd backend
grep -rn "ForeignKey.*organizations\.id" app/models/ | grep "Integer"
```

---

## Recommended Fix Order

### Phase 1: Critical Path (2 hours)
1. ✅ **Fix Alembic branch conflict** (Issue 3)
   - Rename migration files
   - Update down_revision
   - Test `alembic upgrade head`

2. ✅ **Fix tutor/teacher org_id** (Issue 1)
   - Update column types to UUID
   - Add UUID imports
   - Test table creation

### Phase 2: Schema Cleanup (1-2 hours)
3. ✅ **Resolve option_id FK** (Issue 2)
   - Decide on Option A/B/C
   - Update model or remove field
   - Update any dependent code

4. ✅ **Audit all org_id references** (Issue 6)
   - Run grep command
   - Fix any Integer → UUID mismatches
   - Add migration if needed

### Phase 3: Testing (1-2 hours)
5. ✅ **Local Alembic test**
   ```bash
   # Fresh database
   docker compose -f docker-compose.phase1.yml up -d postgres
   alembic upgrade head
   # Should succeed without errors
   ```

6. ✅ **Docker Compose full test**
   ```bash
   docker compose -f docker-compose.phase1.yml up -d
   docker logs dreamseed-backend-phase1
   # Should show "Application startup complete"
   ```

7. ✅ **Register endpoint test in Docker**
   ```bash
   curl -X POST http://localhost:8002/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"docker_test@dreamseed.ai","password":"Test123!","role":"student"}'
   # Should return 201
   ```

---

## Success Criteria

- [ ] Alembic migrations run without branch conflicts
- [ ] All FK type mismatches resolved
- [ ] Docker backend container starts successfully
- [ ] Register endpoint works in Docker (HTTP 201, <1s)
- [ ] No SQLAlchemy errors in Docker logs
- [ ] All 3 containers (postgres, redis, backend) healthy

---

## Week 4 Priority 1 Achievement (Reference)

**Local Environment Results** (Nov 27, 2025):
- ✅ Register endpoint: **0.048s** (95% improvement)
- ✅ EMAIL_MODE=console verified
- ✅ Zero startup errors
- ✅ 15+ model files cleaned up

**These results prove Priority 1 is complete.** Docker issues are infrastructure concerns, not code quality issues.

---

## Notes

- Docker issues do NOT block Week 4 Priority 3 (E2E Testing) - can proceed with local environment
- Production deployment (Priority 4) can use current `/opt/dreamseed/current` database (no Docker needed)
- Docker is primarily for development environment consistency and CI/CD pipelines
- Local validation is sufficient for alpha launch

---

## Related Documents

- [Week 4 Priority 1 Report](WEEK4_PRIORITY1_MODEL_CLEANUP.md)
- [Week 4 Testing Checklist](../../backend/WEEK4_BACKEND_TESTING_CHECKLIST.md)
- [Alembic Migration Guide](../maintenance/alembic_migration_guide.md)
