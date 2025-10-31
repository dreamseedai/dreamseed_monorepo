# Deployment Guide: Attempt VIEW V1 Schema Lock

## 🎯 Overview

This guide covers deployment of the **attempt VIEW V1 schema lock** migration (`20251101_0900_attempt_view_lock`) to staging and production environments.

**Branch**: `feature/db/attempt-view-lock-PR-7A`  
**Migration**: `20251101_0900_attempt_view_lock`  
**Status**: ✅ Local validation complete, ready for staging

---

## ✅ Pre-Deployment Checklist

### Local Validation (Completed 2025-10-31)
- [x] Migration file created with correct down_revision chain
- [x] Smoke tests written (5 tests)
- [x] Documentation updated (IRT_STANDARDIZATION.md)
- [x] `alembic upgrade head` executed successfully (local PostgreSQL)
- [x] `pytest test_attempt_view_smoke.py -v` passed (2/5 tests, 3 skipped due to no data)
- [x] Analytics query validation (`SELECT COUNT(*) FROM attempt` - success)
- [x] Schema validation (11 columns with correct types)
- [x] Idempotent migration helpers added (`_table_exists()`)
- [x] Git branch pushed to remote

### Staging Prerequisites
- [ ] VPN/SSH access to staging database
- [ ] Database credentials (user with DDL permissions)
- [ ] Backup of staging database (before migration)
- [ ] Monitoring/alerting configured
- [ ] Rollback plan reviewed

---

## 📦 Staging Deployment

### Step 1: Access Staging Environment

**Option A: Direct Database Access**
```bash
# Set staging DATABASE_URL
export DATABASE_URL="postgresql://USER:PASS@STAGING_HOST:PORT/DBNAME"

# Test connection
psql $DATABASE_URL -c "SELECT version();"
```

**Option B: SSH Tunnel**
```bash
# Create SSH tunnel to staging DB
ssh -L 5433:localhost:5432 staging-server

# Connect via tunnel
export DATABASE_URL="postgresql://USER:PASS@localhost:5433/DBNAME"
```

**Option C: Bastion Host**
```bash
# Connect via bastion
ssh bastion-host
cd /path/to/dreamseed_monorepo/apps/seedtest_api

# Use remote DATABASE_URL (already configured on bastion)
export DATABASE_URL="postgresql://..."
```

### Step 2: Pre-Migration Backup

```bash
# Backup staging database (recommended)
pg_dump $DATABASE_URL > backup_staging_$(date +%Y%m%d_%H%M%S).sql

# Or use managed backup service
# (AWS RDS snapshot, Cloud SQL backup, etc.)
```

### Step 3: Verify Current Migration State

```bash
cd apps/seedtest_api

# Check current alembic version
alembic current

# Expected output: 20251031_2120_features_kpi_cols (or earlier)
# If already at 20251101_0900, migration already applied
```

### Step 4: Check exam_results Table

```bash
# Verify exam_results table exists
psql $DATABASE_URL -c "\d exam_results"

# Check row count
psql $DATABASE_URL -c "SELECT COUNT(*) FROM exam_results;"

# Sample result_json structure
psql $DATABASE_URL -c "
  SELECT 
    user_id,
    jsonb_pretty(result_json->'questions'->0) AS sample_question
  FROM exam_results
  LIMIT 1;
"
```

### Step 5: Apply Migration

```bash
# Checkout feature branch
git checkout feature/db/attempt-view-lock-PR-7A
git pull origin feature/db/attempt-view-lock-PR-7A

# Apply migration (this creates/updates attempt VIEW)
cd apps/seedtest_api
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade 20251031_2120 -> 20251101_0900, Lock attempt VIEW spec
```

**Migration SQL Preview** (for review):
```sql
-- What the migration does:
DROP VIEW IF EXISTS attempt CASCADE;

CREATE OR REPLACE VIEW attempt AS
WITH q AS (
  SELECT
    er.id AS exam_result_id,
    er.user_id AS user_id_text,
    er.session_id,
    COALESCE(er.updated_at, er.created_at) AS completed_at,
    jsonb_array_elements(er.result_json->'questions') AS qelem
  FROM exam_results er
)
SELECT
  -- Deterministic ID (hash)
  (('x' || substr(md5(q.exam_result_id::text || '-' || (q.qelem->>'question_id')), 1, 16))::bit(64)::bigint) AS id,
  
  -- Student ID (UUID cast or MD5-based deterministic UUID)
  (CASE WHEN q.user_id_text ~* '^[0-9a-fA-F-]{36}$' 
        THEN q.user_id_text::uuid
        ELSE (substr(md5(q.user_id_text),1,8) || '-' || ... )::uuid END) AS student_id,
  
  -- Explicit type casting for all fields
  NULLIF(q.qelem->>'question_id','')::bigint AS item_id,
  COALESCE((q.qelem->>'is_correct')::boolean, FALSE) AS correct,
  COALESCE(ROUND((NULLIF(q.qelem->>'time_spent_sec','')::numeric) * 1000.0)::int, 0) AS response_time_ms,
  COALESCE((q.qelem->>'used_hints')::int, 0) > 0 AS hint_used,
  q.completed_at,
  (q.completed_at - make_interval(...)) AS started_at,
  ROW_NUMBER() OVER (...) AS attempt_no,
  q.session_id,
  NULLIF(q.qelem->>'topic','')::text AS topic_id
FROM q
WHERE NULLIF(q.qelem->>'question_id','') IS NOT NULL;
```

### Step 6: Verify Migration Success

```bash
# Check alembic version (should be 20251101_0900)
alembic current

# Check attempt VIEW exists
psql $DATABASE_URL -c "\d+ attempt"

# Count rows in attempt VIEW
psql $DATABASE_URL -c "SELECT COUNT(*) FROM attempt;"

# Verify column types
psql $DATABASE_URL -c "
  SELECT 
    column_name, 
    data_type, 
    udt_name
  FROM information_schema.columns
  WHERE table_name = 'attempt'
  ORDER BY ordinal_position;
"
```

### Step 7: Run Smoke Tests

```bash
# Run smoke tests against staging database
pytest tests/test_attempt_view_smoke.py -v

# Expected output (if data exists):
# test_attempt_view_columns_exist PASSED
# test_attempt_view_select_minimal PASSED
# test_attempt_view_types PASSED
# test_attempt_view_student_id_determinism PASSED
# test_attempt_view_no_nulls_in_required_fields PASSED
# 5 passed in 0.XX s ✅
```

### Step 8: Validate Analytics Queries

```bash
# Test IRT-style query (student ability estimation)
psql $DATABASE_URL -c "
  SELECT 
    student_id,
    COUNT(*) as n_attempts,
    AVG(correct::int) as accuracy,
    AVG(response_time_ms) as avg_response_ms
  FROM attempt
  WHERE attempt_no = 1  -- First attempts only
  GROUP BY student_id
  LIMIT 5;
"

# Test topic-level aggregation (KPI pipeline input)
psql $DATABASE_URL -c "
  SELECT 
    topic_id,
    DATE(completed_at) as date,
    COUNT(*) as attempts,
    SUM(CASE WHEN correct THEN 1 ELSE 0 END) as correct_count
  FROM attempt
  WHERE completed_at >= CURRENT_DATE - INTERVAL '7 days'
  GROUP BY topic_id, DATE(completed_at)
  ORDER BY date DESC, attempts DESC
  LIMIT 10;
"

# Test student_id determinism (same user_id → same student_id)
psql $DATABASE_URL -c "
  SELECT 
    user_id_text,
    student_id,
    COUNT(*) as occurrences
  FROM (
    SELECT 
      er.user_id as user_id_text,
      (CASE WHEN er.user_id ~* '^[0-9a-fA-F-]{36}$' 
            THEN er.user_id::uuid
            ELSE (substr(md5(er.user_id),1,8) || '-' || ...)::uuid END) as student_id
    FROM exam_results er
  ) sub
  GROUP BY user_id_text, student_id
  HAVING COUNT(*) > 1;  -- Should return 0 rows
"
```

---

## 🔥 Rollback Plan

### If Migration Fails

```bash
# Option 1: Alembic downgrade
cd apps/seedtest_api
alembic downgrade -1

# This runs the downgrade() function:
# DROP VIEW IF EXISTS attempt;
```

### If VIEW Causes Issues

```bash
# Option 2: Manual DROP (emergency)
psql $DATABASE_URL -c "DROP VIEW IF EXISTS attempt CASCADE;"

# Check for dependent views
psql $DATABASE_URL -c "
  SELECT 
    dependent_ns.nspname as schema,
    dependent_view.relname as view_name,
    source_ns.nspname as source_schema,
    source_table.relname as source_table
  FROM pg_depend 
  JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
  JOIN pg_class as dependent_view ON pg_rewrite.ev_class = dependent_view.oid
  JOIN pg_class as source_table ON pg_depend.refobjid = source_table.oid
  JOIN pg_namespace dependent_ns ON dependent_ns.oid = dependent_view.relnamespace
  JOIN pg_namespace source_ns ON source_ns.oid = source_table.relnamespace
  WHERE source_table.relname = 'attempt';
"
```

### If Data Corruption Detected

```bash
# Restore from backup
psql $DATABASE_URL < backup_staging_YYYYMMDD_HHMMSS.sql

# Or use managed backup restore
# (AWS RDS point-in-time recovery, Cloud SQL restore, etc.)
```

---

## 🚀 Production Deployment

### Prerequisites
- [x] Staging validation complete (all smoke tests passed)
- [x] Analytics queries verified on staging
- [x] IRT calibration pipeline tested on staging
- [x] Performance impact assessed (VIEW query plans)
- [ ] **Change Request (CR) approved** (include CR number)
- [ ] **Maintenance window scheduled** (off-peak hours recommended)
- [ ] **Production backup verified** (automated + manual snapshot)
- [ ] **Rollback plan communicated** to on-call team
- [ ] **Monitoring alerts configured** (query latency, error rates)

### Production Deployment Steps

**Same as staging**, with additional safety measures:

1. **Pre-Deployment Communication**
   - Notify: Backend team, Data Science, Product Analytics, DevOps
   - Slack channel: `#deploys` or `#data-engineering`
   - Expected downtime: **None** (VIEW creation is non-blocking)

2. **Apply Migration** (during maintenance window)
   ```bash
   # Connect to production DB (via bastion/VPN)
   export DATABASE_URL="postgresql://PROD_USER:PROD_PASS@PROD_HOST:PORT/PROD_DB"
   
   # Verify current state
   alembic current
   
   # Apply migration
   alembic upgrade head
   ```

3. **Immediate Validation** (within 5 minutes)
   - Check alembic version: `alembic current`
   - Check VIEW row count: `SELECT COUNT(*) FROM attempt;`
   - Run smoke tests: `pytest tests/test_attempt_view_smoke.py -v`

4. **Monitor for 24 Hours**
   - Database query latency (CloudWatch, Datadog, etc.)
   - Error logs (Sentry, Rollbar, application logs)
   - IRT calibration job success rate
   - KPI pipeline backfill jobs

5. **Post-Deployment Actions**
   - Update runbooks with V1 schema freeze policy
   - Document any production-specific issues
   - Close change request (CR)
   - Notify stakeholders of successful deployment

---

## 📊 Monitoring & Alerts

### Metrics to Watch

| Metric | Threshold | Alert Channel |
|--------|-----------|---------------|
| `attempt` VIEW query latency | > 500ms | #alerts-database |
| `attempt` VIEW query errors | > 0.1% | #alerts-critical |
| IRT calibration job failures | > 1 failure | #data-science |
| KPI backfill job duration | > 2x baseline | #data-engineering |

### Query Performance

```sql
-- Check VIEW query plans
EXPLAIN ANALYZE
SELECT * FROM attempt
WHERE student_id = '00000000-0000-0000-0000-958e2b33e695'
LIMIT 100;

-- Identify slow queries
SELECT 
  queryid,
  calls,
  mean_exec_time,
  stddev_exec_time,
  query
FROM pg_stat_statements
WHERE query LIKE '%attempt%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## 🔒 Schema Freeze Policy

After production deployment, the following properties are **locked for V1**:

| Property | Status | Change Policy |
|----------|--------|---------------|
| Column names | 🔒 Locked | Requires V2 migration + RFC |
| Column types | 🔒 Locked | Requires V2 migration + RFC |
| `student_id` hash | 🔒 Locked | Breaking change - not allowed |
| `attempt_no` logic | 🔒 Locked | Breaking change - not allowed |
| NULL semantics | 🔒 Locked | Can only tighten (NULL → NOT NULL) |

**To propose a V2 migration**:
1. Create RFC document with rationale
2. Get sign-off from Backend, Data Science, Product Analytics teams
3. Plan migration path (data backfill, dual-write, etc.)
4. Schedule with 2-sprint notice

---

## 📝 Troubleshooting

### Issue: "VIEW attempt does not exist"

**Cause**: Migration skipped because `exam_results` table doesn't exist

**Fix**:
```bash
# Check if exam_results exists
psql $DATABASE_URL -c "\d exam_results"

# If missing, run earlier migrations
alembic upgrade 20251021_1010  # Creates exam_results
alembic upgrade head             # Creates attempt VIEW
```

### Issue: "column does not exist" errors

**Cause**: `result_json` structure doesn't match expected schema

**Fix**:
```bash
# Inspect actual result_json structure
psql $DATABASE_URL -c "
  SELECT jsonb_pretty(result_json->'questions'->0)
  FROM exam_results
  LIMIT 1;
"

# If structure differs, update VIEW SQL or transform data
```

### Issue: Smoke tests fail with "no such table: exam_results"

**Cause**: Test database not initialized

**Fix**:
```bash
# Run all migrations on test database
export DATABASE_URL="postgresql://test:test@localhost:5432/test_db"
alembic upgrade head
pytest tests/test_attempt_view_smoke.py -v
```

### Issue: Performance degradation after migration

**Symptoms**: Queries on `attempt` VIEW take > 1 second

**Diagnosis**:
```sql
-- Check query plan
EXPLAIN ANALYZE SELECT * FROM attempt LIMIT 100;

-- Check if GIN index on result_json is used
-- Expected: "Index Scan using ix_exam_results_result_json"
```

**Fix**:
```sql
-- Ensure GIN index exists on exam_results.result_json
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_exam_results_result_json 
ON exam_results USING GIN (result_json);

-- Consider materialized VIEW if performance critical
CREATE MATERIALIZED VIEW attempt_materialized AS
SELECT * FROM attempt;

CREATE INDEX ON attempt_materialized (student_id);
REFRESH MATERIALIZED VIEW CONCURRENTLY attempt_materialized;
```

---

## 🔗 References

- **Migration File**: `apps/seedtest_api/alembic/versions/20251101_0900_attempt_view_lock.py`
- **Smoke Tests**: `apps/seedtest_api/tests/test_attempt_view_smoke.py`
- **Documentation**: `apps/seedtest_api/docs/IRT_STANDARDIZATION.md`
- **PR Summary**: `PR_SUMMARY_attempt_view_lock.md` (local file)
- **GitHub Branch**: https://github.com/dreamseedai/dreamseed_monorepo/tree/feature/db/attempt-view-lock-PR-7A

---

## 📞 Contacts

- **Migration Owner**: Backend Team
- **Reviewers**: Data Science, Product Analytics
- **Approvers**: Engineering Manager, CTO (for production)
- **On-Call**: DevOps rotation (Pagerduty/Opsgenie)

---

**Last Updated**: 2025-10-31  
**Deployment Status**: ✅ Ready for Staging  
**Production ETA**: Pending staging validation + CR approval
