# Runbook: attempt VIEW V1 Schema Lock

**Incident Response Guide**  
**Component**: `attempt` VIEW (PostgreSQL)  
**Owner**: Data Engineering Team  
**On-Call**: [PagerDuty rotation](link-to-pagerduty)  
**Last Updated**: 2025-10-31

---

## 🚨 Incident Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **P0 - Critical** | VIEW missing/broken, all queries fail | < 15 min |
| **P1 - High** | Queries timing out, data quality issues | < 1 hour |
| **P2 - Medium** | Performance degradation < 2x baseline | < 4 hours |
| **P3 - Low** | Minor warnings, no user impact | Next business day |

---

## 🔍 Symptom → Root Cause → Resolution

### 1. VIEW Missing (P0)

#### Symptoms
- Error: `relation "attempt" does not exist`
- ETL jobs failing with "ERROR: relation does not exist"
- Monitoring alerts: `attempt` query count drops to 0

#### Diagnosis
```sql
-- Check if VIEW exists
SELECT schemaname, viewname, viewowner
FROM pg_views
WHERE viewname = 'attempt';

-- Expected: 1 row (public, attempt, seedtest_user)
-- If empty: VIEW was dropped
```

#### Root Causes
1. **Accidental DROP**: Manual query or migration error
2. **Rollback Executed**: `alembic downgrade -1` called
3. **Schema Corruption**: Rare pg_catalog issue

#### Resolution

**Immediate (< 5 min)**:
```bash
# 1. SSH to DB host
ssh production-db-host

# 2. Navigate to seedtest_api
cd /opt/dreamseed/apps/seedtest_api
source venv/bin/activate

# 3. Check alembic state
alembic current
# If HEAD is 20251101_0900 but VIEW missing: database state mismatch

# 4. Re-create VIEW (idempotent)
alembic upgrade head --sql | psql -U seedtest_user -d seedtest

# OR direct SQL (emergency)
psql -U seedtest_user -d seedtest << 'EOF'
CREATE OR REPLACE VIEW attempt AS
SELECT 
  (('x' || LEFT(MD5(er.id::text || '-' || q.item_id::text), 16))::bit(64)::bigint) AS id,
  er.id AS exam_result_id,
  CASE 
    WHEN er.student_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' 
    THEN er.student_id::uuid
    ELSE ('00000000-0000-0000-0000-' || LPAD(LEFT(MD5(er.student_id), 12), 12, '0'))::uuid
  END AS student_id,
  q.item_id::int AS item_id,
  q.id::int AS question_id,
  q.question_text::text AS question_text,
  q.correct_answer::text AS correct_answer,
  NULLIF(er.result_json->>'studentAnswer', '')::text AS student_answer,
  CASE 
    WHEN (er.result_json->>'isCorrect')::text = 'true' THEN 1 
    ELSE 0 
  END AS is_correct,
  ROUND(COALESCE(NULLIF(er.result_json->>'responseTime', '')::numeric, 0))::int AS response_time_ms,
  er.completed_at AS completed_at,
  ROW_NUMBER() OVER (PARTITION BY student_id, q.item_id ORDER BY er.completed_at) AS attempt_no,
  q.tags
FROM exam_results er
JOIN questions q ON q.id = (er.result_json->>'questionId')::int
WHERE (er.result_json->>'questionId') IS NOT NULL;
EOF

# 5. Verify
psql -U seedtest_user -d seedtest -c "SELECT COUNT(*) FROM attempt;"
```

**Post-Incident**:
- [ ] Document how VIEW was dropped (audit logs)
- [ ] Review alembic migration history for gaps
- [ ] Update monitoring to alert on VIEW absence

---

### 2. Query Failure - Permission Denied (P1)

#### Symptoms
- Error: `permission denied for relation exam_results`
- Application logs: `SELECT FROM attempt failed with access denied`

#### Diagnosis
```sql
-- Check VIEW owner and dependencies
SELECT schemaname, viewname, viewowner
FROM pg_views
WHERE viewname = 'attempt';

-- Check table permissions
SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_name = 'exam_results' AND grantee = 'seedtest_user';

-- Expected: SELECT privilege present
```

#### Root Causes
1. **Role Mismatch**: VIEW created by user A, queried by user B
2. **Grant Revoked**: `REVOKE SELECT ON exam_results` executed
3. **Cascading Permission**: Base tables (`exam_results`, `questions`) access denied

#### Resolution

```sql
-- Grant SELECT on base tables to application user
GRANT SELECT ON exam_results TO seedtest_user;
GRANT SELECT ON questions TO seedtest_user;

-- Grant SELECT on VIEW itself (usually implicit)
GRANT SELECT ON attempt TO seedtest_user;

-- Verify
SET ROLE seedtest_user;
SELECT COUNT(*) FROM attempt;
RESET ROLE;
```

**Prevention**:
- Add permission checks to Alembic migration:
  ```python
  op.execute("GRANT SELECT ON exam_results TO seedtest_user;")
  op.execute("GRANT SELECT ON questions TO seedtest_user;")
  op.execute("GRANT SELECT ON attempt TO seedtest_user;")
  ```

---

### 3. Query Timeout / Slow Performance (P1/P2)

#### Symptoms
- Queries take > 5 seconds (baseline: < 200ms)
- CloudWatch alerts: `attempt` query p99 latency > 2000ms
- ETL jobs timing out

#### Diagnosis

```sql
-- 1. Check query execution plan
EXPLAIN ANALYZE
SELECT *
FROM attempt
WHERE student_id = '123e4567-e89b-12d3-a456-426614174000'
  AND completed_at >= CURRENT_DATE - INTERVAL '30 days';

-- Look for:
-- - Seq Scan on exam_results (BAD - should use index)
-- - Hash Join cost > 10000 (slow)
-- - Planning Time > 10ms (excessive)

-- 2. Check table stats
SELECT 
  schemaname, 
  tablename, 
  n_live_tup, 
  n_dead_tup, 
  last_vacuum, 
  last_analyze
FROM pg_stat_user_tables
WHERE tablename IN ('exam_results', 'questions');

-- If last_analyze is old (> 7 days) or n_dead_tup high (> 10%):
ANALYZE exam_results;
ANALYZE questions;

-- 3. Check for locks
SELECT 
  pid, 
  usename, 
  query, 
  state, 
  wait_event_type,
  query_start
FROM pg_stat_activity
WHERE query ILIKE '%attempt%'
  AND state != 'idle';
```

#### Root Causes
1. **Missing Index**: No covering index on `(student_id, completed_at)`
2. **Stale Statistics**: ANALYZE not run after bulk inserts
3. **Table Bloat**: Dead tuples accumulating in `exam_results`
4. **MD5 Overhead**: Deterministic ID computation expensive at scale

#### Resolution

**Short-Term (< 30 min)**:
```sql
-- Update statistics
ANALYZE exam_results;
ANALYZE questions;

-- Check for blocking queries
SELECT pg_cancel_backend(pid)
FROM pg_stat_activity
WHERE query ILIKE '%attempt%'
  AND state = 'active'
  AND query_start < NOW() - INTERVAL '5 minutes';
```

**Medium-Term (< 4 hours)**:
```sql
-- Add index on base table (exam_results)
CREATE INDEX CONCURRENTLY idx_exam_results_student_completed
ON exam_results (student_id, completed_at)
WHERE (result_json->>'questionId') IS NOT NULL;

-- Add index for JOIN condition
CREATE INDEX CONCURRENTLY idx_questions_item_id
ON questions (item_id);
```

**Long-Term (Next Sprint)**:
- **Materialized VIEW**: Convert `attempt` to MV for pre-computed results
  ```sql
  CREATE MATERIALIZED VIEW attempt_mv AS
  SELECT ... FROM exam_results JOIN questions ...;
  
  CREATE UNIQUE INDEX ON attempt_mv (id);
  CREATE INDEX ON attempt_mv (student_id, completed_at);
  
  -- Refresh hourly via cron
  REFRESH MATERIALIZED VIEW CONCURRENTLY attempt_mv;
  ```
- **Composite Index**: Add covering index for common query patterns
  ```sql
  CREATE INDEX idx_attempt_student_time
  ON attempt (student_id, completed_at) INCLUDE (is_correct, response_time_ms);
  ```

---

### 4. Data Quality Issues (P1)

#### Symptoms
- ETL job reports unexpected NULL values
- IRT calibration fails: "student_id cannot be NULL"
- Smoke tests fail: `test_attempt_view_no_nulls_in_required_fields`

#### Diagnosis

```sql
-- Check for NULLs in required fields
SELECT 
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE id IS NULL) AS null_id,
  COUNT(*) FILTER (WHERE student_id IS NULL) AS null_student_id,
  COUNT(*) FILTER (WHERE item_id IS NULL) AS null_item_id,
  COUNT(*) FILTER (WHERE question_id IS NULL) AS null_question_id,
  COUNT(*) FILTER (WHERE is_correct IS NULL) AS null_is_correct
FROM attempt;

-- If any NULL counts > 0, investigate source data
SELECT 
  er.id AS exam_result_id,
  er.student_id AS raw_student_id,
  er.result_json->>'questionId' AS question_id_from_json,
  q.id AS question_id_joined
FROM exam_results er
LEFT JOIN questions q ON q.id = (er.result_json->>'questionId')::int
WHERE er.student_id IS NULL
   OR (er.result_json->>'questionId') IS NULL
LIMIT 10;
```

#### Root Causes
1. **Bad Source Data**: `exam_results.student_id` is NULL or empty string
2. **JOIN Failure**: `questions` table missing rows for `questionId` in JSON
3. **Type Casting Error**: `student_id` regex fails to match, fallback UUID broken

#### Resolution

**Immediate**:
```sql
-- Find and fix NULL student_id in source table
UPDATE exam_results
SET student_id = 'default-student-uuid'  -- Replace with actual default
WHERE student_id IS NULL;

-- Recreate questions that are referenced but missing
INSERT INTO questions (id, item_id, question_text, correct_answer)
SELECT DISTINCT
  (result_json->>'questionId')::int,
  (result_json->>'questionId')::int,  -- Use question_id as item_id if unknown
  'Migrated question',
  'N/A'
FROM exam_results er
WHERE NOT EXISTS (
  SELECT 1 FROM questions q WHERE q.id = (er.result_json->>'questionId')::int
)
  AND (result_json->>'questionId') IS NOT NULL;
```

**Prevention**:
- Add CHECK constraints on `exam_results`:
  ```sql
  ALTER TABLE exam_results
  ADD CONSTRAINT check_student_id_not_null
  CHECK (student_id IS NOT NULL AND student_id != '');
  
  ALTER TABLE exam_results
  ADD CONSTRAINT check_question_id_exists
  CHECK (
    (result_json->>'questionId') IS NULL
    OR EXISTS (SELECT 1 FROM questions WHERE id = (result_json->>'questionId')::int)
  );
  ```

---

### 5. Determinism Violation (P2)

#### Symptoms
- ETL upsert conflicts: "duplicate key value violates unique constraint"
- IRT pipeline sees duplicate `(student_id, item_id, attempt_no)` tuples

#### Diagnosis

```sql
-- Check for duplicate IDs
WITH id_counts AS (
  SELECT id, COUNT(*) AS cnt
  FROM attempt
  GROUP BY id
  HAVING COUNT(*) > 1
)
SELECT a.*
FROM attempt a
JOIN id_counts ic ON a.id = ic.id
ORDER BY a.id, a.completed_at
LIMIT 20;

-- Check if exam_result_id + question_id pairs are unique in source
SELECT 
  er.id AS exam_result_id,
  (er.result_json->>'questionId')::int AS question_id,
  COUNT(*) AS occurrences
FROM exam_results er
WHERE (er.result_json->>'questionId') IS NOT NULL
GROUP BY er.id, (er.result_json->>'questionId')::int
HAVING COUNT(*) > 1;
```

#### Root Causes
1. **Duplicate Source Rows**: `exam_results` has multiple rows with same `id` and `questionId`
2. **MD5 Collision**: Extremely rare (1 in 2^64 for 64-bit truncation)

#### Resolution

**Deduplicate Source**:
```sql
-- Identify duplicates
CREATE TEMP TABLE duplicate_exam_results AS
SELECT id, result_json->>'questionId' AS question_id, MIN(ctid) AS keep_ctid
FROM exam_results
GROUP BY id, result_json->>'questionId'
HAVING COUNT(*) > 1;

-- Delete duplicates (keep oldest)
DELETE FROM exam_results
WHERE ctid NOT IN (SELECT keep_ctid FROM duplicate_exam_results);

-- Verify
SELECT COUNT(*) FROM duplicate_exam_results;  -- Should be 0
```

**Add Unique Constraint**:
```sql
CREATE UNIQUE INDEX idx_exam_results_unique_attempt
ON exam_results (id, ((result_json->>'questionId')::int));
```

---

## 🛠️ Common Operations

### Check VIEW Health

```bash
# Quick health check script
psql -U seedtest_user -d seedtest << 'EOF'
-- 1. VIEW exists
SELECT COUNT(*) AS view_exists
FROM pg_views
WHERE viewname = 'attempt';

-- 2. Row count
SELECT COUNT(*) AS total_attempts FROM attempt;

-- 3. Recent data
SELECT MAX(completed_at) AS latest_attempt FROM attempt;

-- 4. No NULLs in required fields
SELECT 
  COUNT(*) FILTER (WHERE id IS NULL) AS null_ids,
  COUNT(*) FILTER (WHERE student_id IS NULL) AS null_student_ids
FROM attempt;

-- 5. Sample query performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM attempt WHERE student_id = (SELECT student_id FROM attempt LIMIT 1)
LIMIT 10;
EOF
```

### Manual VIEW Refresh (if MV in future)

```sql
-- If converted to Materialized VIEW
REFRESH MATERIALIZED VIEW CONCURRENTLY attempt_mv;

-- Monitor progress
SELECT 
  pid, 
  query, 
  state, 
  query_start,
  NOW() - query_start AS duration
FROM pg_stat_activity
WHERE query ILIKE '%REFRESH MATERIALIZED VIEW%';
```

### Emergency Rollback

```bash
# Revert to pre-lock VIEW schema (if deployed)
alembic downgrade -1

# Verify VIEW dropped
psql -U seedtest_user -d seedtest -c "\d attempt"
# Expected: Did not find any relation named "attempt"

# If previous VIEW version needed, restore from backup or re-deploy old migration
```

---

## 📞 Escalation Path

### L1 - On-Call Engineer (You)
- **Actions**: Run diagnostics (above queries), restart jobs, clear locks
- **Escalate if**: Cannot resolve in 1 hour OR data loss suspected

### L2 - Data Engineering Lead (@data-eng-lead)
- **Contact**: Slack DM + PagerDuty page
- **Actions**: Schema changes, index creation, alembic migrations
- **Escalate if**: Performance requires infra changes OR schema corruption

### L3 - DBA / Platform Engineering (@dba-team)
- **Contact**: Emergency hotline (xxx-xxx-xxxx)
- **Actions**: DB failover, replication issues, pg_catalog repairs
- **Escalate if**: Database-wide outage OR data corruption

---

## 📊 Monitoring & Alerts

### CloudWatch Metrics
- `DatabaseConnections` - Alert if > 100 (baseline: 50)
- `CPUUtilization` - Alert if > 80% for 5min
- Custom: `attempt_query_p99_latency` - Alert if > 2000ms

### Query Patterns to Watch

```sql
-- Slowest queries referencing attempt
SELECT 
  query,
  calls,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
WHERE query ILIKE '%attempt%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Blocked queries
SELECT 
  blocked_locks.pid AS blocked_pid,
  blocking_locks.pid AS blocking_pid,
  blocked_activity.query AS blocked_query
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
WHERE NOT blocked_locks.granted;
```

---

## 🔮 Future Enhancements (Roadmap)

1. **Materialized VIEW** (Q1 2026)
   - Pre-compute `attempt` to MV, refresh hourly
   - Estimated speedup: 10x for aggregation queries

2. **Composite Index** (Q1 2026)
   - `CREATE INDEX idx_attempt_student_time ON attempt (student_id, completed_at);`
   - Estimated impact: 5x faster time-series queries

3. **Partitioning** (Q2 2026)
   - Partition `exam_results` by `completed_at` (monthly)
   - Estimated impact: 50% reduction in query scan size

4. **Caching Layer** (Q2 2026)
   - Redis cache for common aggregations
   - Estimated impact: Sub-100ms response for dashboards

---

## 📚 Related Documentation
- `IRT_STANDARDIZATION.md` - VIEW schema specification
- `DEPLOYMENT_GUIDE_attempt_view_lock.md` - Deployment procedures
- `PRODUCTION_CR_TEMPLATE.md` - Change request template
- `STAGING_EVIDENCE_TEMPLATE.md` - Validation checklist

---

**Runbook Version**: 1.0  
**Last Tested**: YYYY-MM-DD  
**Next Review**: 2026-01-31
