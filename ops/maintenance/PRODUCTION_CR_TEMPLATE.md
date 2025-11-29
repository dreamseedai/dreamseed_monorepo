# Production Change Request (CR) Template

**CR Number**: CR-YYYYMMDD-001  
**PR**: #73 - attempt VIEW V1 스키마 잠금  
**Submitted By**: @username  
**Submitted Date**: YYYY-MM-DD  
**Target Deployment Date**: YYYY-MM-DD (Maintenance Window: HH:MM-HH:MM UTC)

---

## 📋 Change Summary

### Purpose
Lock the `attempt` VIEW schema to V1 specification, guaranteeing deterministic IDs, explicit type casting, and null-handling semantics for downstream ETL, metrics, and IRT pipelines.

### Change Type
- [x] Database Schema (PostgreSQL VIEW)
- [ ] Application Code
- [ ] Infrastructure/Configuration
- [ ] Data Migration

### Urgency
- [ ] Emergency (P0)
- [ ] High (P1)
- [x] **Normal (P2)** - Scheduled maintenance
- [ ] Low (P3)

---

## 🎯 Business Justification

### Problem Statement
Current `attempt` VIEW lacks explicit schema guarantees:
- Type instability (float vs int for `response_time_ms`)
- Non-deterministic IDs break idempotent ETL pipelines
- NULL semantics unclear for required fields
- Downstream consumers (IRT calibration, weekly KPI jobs) fragile to schema drift

### Expected Benefits
1. **ETL Stability**: Deterministic `id` enables safe upsert patterns
2. **Type Safety**: Explicit casting prevents runtime errors in data pipelines
3. **IRT Accuracy**: Reliable `attempt_no` ordering for longitudinal analysis
4. **Metrics Consistency**: Guaranteed non-NULL fields for aggregations

### Risks if NOT Deployed
- ETL job failures accumulate as data volume grows
- IRT calibration produces inaccurate ability estimates
- Weekly KPI recompute jobs break during retake surge (Nov-Dec exam season)

---

## 🔧 Technical Details

### Components Affected
- **Database**: `seedtest` PostgreSQL (production)
- **Object**: `attempt` VIEW (read-only, no table changes)
- **Migration**: Alembic revision `20251101_0900_attempt_view_lock.py`

### Schema Changes

#### Before
```sql
-- Implicit types, non-deterministic ID
CREATE VIEW attempt AS
SELECT 
  gen_random_uuid() AS id,  -- ❌ Non-deterministic
  ...
```

#### After
```sql
-- Deterministic ID, explicit casting
CREATE OR REPLACE VIEW attempt AS
SELECT 
  (('x' || LEFT(MD5(er.id::text || '-' || q.item_id::text), 16))::bit(64)::bigint) AS id,
  er.student_id::uuid AS student_id,
  ROUND(COALESCE(NULLIF(er.result_json->>'responseTime', '')::numeric, 0))::int AS response_time_ms,
  ...
```

**Key Differences**:
| Field | Before | After |
|-------|--------|-------|
| `id` | uuid (random) | bigint (md5-based) |
| `response_time_ms` | float (implicit) | int (explicit ROUND) |
| `student_id` | text/uuid (mixed) | uuid (explicit cast) |
| `attempt_no` | absent | bigint (ROW_NUMBER) |

### SQL Statement
```sql
-- Executed by alembic upgrade head
DROP VIEW IF EXISTS attempt;

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
```

---

## 🎯 Impact Assessment

### Services Affected
- **Direct**: None (VIEW change only, no service restarts required)
- **Indirect**: 
  - ETL jobs querying `attempt` VIEW
  - IRT calibration Cron jobs (`mirt_calibrate.py`)
  - Weekly KPI recompute job (`recompute_weekly_kpi.py`)
  - Reporting dashboards (Redash/Looker)

### Downtime Required
**None** - VIEW replacement is atomic:
1. `DROP VIEW IF EXISTS attempt;` - instant
2. `CREATE OR REPLACE VIEW attempt AS ...` - instant
3. Total downtime: **< 1 second**

### Data Loss Risk
**None** - VIEWs are query-time projections; no data tables are modified.

### Performance Impact
- **Query Performance**: Negligible (same underlying JOIN logic)
- **MD5 Computation**: ~10μs per row overhead (acceptable for VIEW)
- **Index Opportunity**: Future PR can add covering index on `(student_id, completed_at)` if needed

### Compatibility
- **Backward Compatible**: ✅ (all existing queries continue to work)
- **Breaking Changes**: ❌ None (column names and types remain compatible)
- **Exception**: Applications assuming `id` is UUID will need to adapt (none known in V1)

---

## 🛡️ Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| VIEW creation fails | Low | High | Test in staging first; alembic transaction rollback automatic |
| Downstream query breaks | Low | Medium | Staging validation includes sample queries from ETL/IRT jobs |
| Performance degradation | Low | Low | EXPLAIN ANALYZE in staging; no index changes in this PR |
| Rollback fails | Very Low | High | Downgrade tested; VIEW drop is instant and safe |

### Blast Radius
- **Scope**: Read-only VIEW in `seedtest` schema
- **Users Affected**: 0 (internal pipelines only)
- **Services**: Background jobs (no user-facing API changes)

---

## ✅ Pre-Deployment Checklist

### Code Review
- [ ] PR #73 approved by 2+ reviewers
- [ ] CI checks passing (K8s validate, Scope Guard, CodeQL)
- [ ] Alembic migration syntax validated

### Testing
- [ ] Staging deployment completed successfully
- [ ] Staging evidence captured (see `STAGING_EVIDENCE_TEMPLATE.md`)
- [ ] Smoke tests passed (5/5 in `test_attempt_view_smoke.py`)
- [ ] Downstream query validation (ETL, IRT, metrics)

### Documentation
- [ ] `IRT_STANDARDIZATION.md` updated with V1 spec
- [ ] `DEPLOYMENT_GUIDE_attempt_view_lock.md` reviewed
- [ ] `RUNBOOK_attempt_view_lock.md` prepared for incident response

### Stakeholder Communication
- [ ] ETL team notified of VIEW schema lock
- [ ] IRT pipeline owner aware of deterministic IDs
- [ ] BI/Reporting team informed (no action required)

---

## 📅 Deployment Plan

### Timeline

| Phase | Start | End | Duration | Owner |
|-------|-------|-----|----------|-------|
| 1. Pre-flight checks | HH:MM | HH:MM | 5 min | @deployer |
| 2. Alembic upgrade | HH:MM | HH:MM | 1 min | @deployer |
| 3. Smoke tests | HH:MM | HH:MM | 2 min | @deployer |
| 4. Validation queries | HH:MM | HH:MM | 5 min | @deployer |
| 5. Evidence capture | HH:MM | HH:MM | 5 min | @deployer |
| 6. Monitoring (24h) | HH:MM | +24h | 1 day | @oncall |

**Total Active Deployment**: ~15 minutes  
**Post-Deployment Monitoring**: 24 hours

### Maintenance Window
- **Scheduled**: YYYY-MM-DD HH:MM-HH:MM UTC (1 hour reserved)
- **Actual Downtime**: < 1 second (VIEW replacement)
- **User Impact**: None (background pipelines only)

### Deployment Steps

```bash
# 1. SSH to production DB host (or use CI/CD pipeline)
ssh production-db-host

# 2. Navigate to seedtest_api directory
cd /opt/dreamseed/apps/seedtest_api

# 3. Activate Python environment
source venv/bin/activate

# 4. Verify Alembic current state
alembic history | head -5
alembic current

# 5. Preview migration SQL (optional)
alembic upgrade head --sql > /tmp/attempt_view_lock_preview.sql
less /tmp/attempt_view_lock_preview.sql

# 6. Execute migration
alembic upgrade head

# 7. Verify new VIEW
psql -U seedtest_user -d seedtest -c "\d+ attempt"

# 8. Run smoke tests
pytest tests/test_attempt_view_smoke.py -v

# 9. Validation queries (see STAGING_EVIDENCE_TEMPLATE.md)
psql -U seedtest_user -d seedtest -f validation_queries.sql
```

---

## 🔄 Rollback Plan

### Conditions for Rollback
- [ ] VIEW creation fails (automatic alembic rollback)
- [ ] Smoke tests fail after deployment
- [ ] Critical downstream job breaks (ETL/IRT)
- [ ] Performance degradation > 2x baseline

### Rollback Procedure

```bash
# 1. Immediate rollback (< 30 seconds)
alembic downgrade -1

# 2. Verify VIEW dropped
psql -U seedtest_user -d seedtest -c "\d attempt"

# Expected output: "Did not find any relation named 'attempt'"

# 3. Restart dependent jobs (if needed)
# IRT calibration: (manual restart via cron or supervisord)
# Weekly KPI: (will resume on next schedule)

# 4. Notify stakeholders
# Post incident in #eng-alerts Slack channel
```

### Rollback SQL
```sql
-- Executed by alembic downgrade -1
DROP VIEW IF EXISTS attempt;
```

**Rollback Risk**: Minimal (VIEW drop is instant and safe)

### Post-Rollback Actions
- [ ] Investigate root cause (query logs, error messages)
- [ ] Fix migration script if needed
- [ ] Re-test in staging
- [ ] Re-schedule production deployment

---

## 📊 Success Criteria

### Immediate (Deployment Complete)
- [x] Alembic upgrade executes without errors
- [x] `attempt` VIEW exists with 13 columns
- [x] Smoke tests pass (5/5)
- [x] Sample queries return expected results

### Short-Term (24 hours)
- [ ] No errors in application logs mentioning `attempt` VIEW
- [ ] ETL jobs complete successfully (check cron logs)
- [ ] IRT calibration job runs without errors
- [ ] Weekly KPI recompute completes (if scheduled)

### Medium-Term (7 days)
- [ ] No performance degradation in metrics queries
- [ ] No schema-related incidents reported by downstream teams
- [ ] Deterministic ID behavior validated in production data

---

## 📈 Monitoring Plan

### Metrics to Watch (24h)

| Metric | Baseline | Alert Threshold | Dashboard |
|--------|----------|-----------------|-----------|
| `attempt` query latency | < 200ms | > 500ms | CloudWatch/Grafana |
| ETL job success rate | 100% | < 95% | Airflow/Cron logs |
| IRT calibration errors | 0 | > 0 | Application logs |
| DB connection count | ~50 | > 100 | pg_stat_activity |

### Log Queries

```sql
-- Check for VIEW-related errors in PostgreSQL logs
SELECT * FROM pg_stat_statements
WHERE query ILIKE '%attempt%'
  AND calls > 0
ORDER BY total_exec_time DESC
LIMIT 10;

-- Verify no broken queries
SELECT COUNT(*) FROM attempt;  -- Should return row count
```

### Alert Channels
- **Critical**: PagerDuty → On-call engineer
- **Warning**: Slack #eng-alerts
- **Info**: Email to data-eng@dreamseedai.com

---

## 👥 Roles & Responsibilities

| Role | Name | Responsibilities |
|------|------|------------------|
| **Change Owner** | @username | Overall CR coordination, PR merge, deployment execution |
| **Deployer** | @username | Execute alembic upgrade, capture evidence |
| **Validator** | @username | Run smoke tests, downstream query validation |
| **Approver (Tech Lead)** | @username | Final go/no-go decision |
| **Approver (DBA)** | @username | Review SQL, approve production access |
| **On-Call Engineer** | @username | Monitor 24h post-deployment, incident response |

---

## 📎 Supporting Documents

1. **PR #73**: https://github.com/dreamseedai/dreamseed_monorepo/pull/73
2. **Staging Evidence**: [Link to PR comment with staging deployment results]
3. **Deployment Guide**: `DEPLOYMENT_GUIDE_attempt_view_lock.md`
4. **Runbook**: `RUNBOOK_attempt_view_lock.md`
5. **IRT Spec**: `apps/seedtest_api/docs/IRT_STANDARDIZATION.md`

---

## ✍️ Approval Signatures

| Approver | Role | Decision | Date | Comments |
|----------|------|----------|------|----------|
| @tech-lead | Tech Lead | ⬜ Approve / ⬜ Reject | YYYY-MM-DD |  |
| @dba-lead | DBA | ⬜ Approve / ⬜ Reject | YYYY-MM-DD |  |
| @product-owner | Product | ⬜ Approve / ⬜ Reject | YYYY-MM-DD |  |

---

## 📝 Post-Deployment Notes

*(To be filled after deployment)*

### Actual Deployment

- **Date/Time**: YYYY-MM-DD HH:MM UTC
- **Duration**: ___ minutes
- **Issues Encountered**: None / [Describe issues]
- **Deviations from Plan**: None / [Describe deviations]

### Evidence Links
- Alembic upgrade log: [Link or attachment]
- Smoke test results: [Link or attachment]
- Validation queries: [Link or attachment]

### Lessons Learned
- What went well:
- What could be improved:
- Action items for next CR:

---

**CR Version**: 1.0  
**Last Updated**: YYYY-MM-DD  
**Status**: ⬜ Draft | ⬜ Pending Approval | ⬜ Approved | ⬜ Deployed | ⬜ Verified | ⬜ Closed
