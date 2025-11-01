# Staging Deployment Evidence Template

**PR**: #73 - attempt VIEW V1 스키마 잠금  
**Deployment Date**: YYYY-MM-DD  
**Deployment By**: @username  
**Environment**: Staging (seedtest-api staging DB)

---

## ✅ Pre-Deployment Checklist

- [ ] CI checks passing (K8s validate, Scope Guard, CodeQL)
- [ ] PR approved by required reviewers
- [ ] `DEPLOYMENT_GUIDE_attempt_view_lock.md` reviewed
- [ ] Staging DB connection verified
- [ ] Backup/snapshot captured (optional for view-only change)

---

## 📋 Deployment Evidence

### 1. Alembic History (Before)

```bash
# Command
cd /home/won/projects/dreamseed_monorepo/apps/seedtest_api
alembic history | head -10

# Output
```

<details>
<summary>Full alembic history output</summary>

```
(paste output here)
```

</details>

---

### 2. Alembic Upgrade Execution

```bash
# Command
alembic upgrade head

# Output (or screenshot)
```

**Key Observations**:
- [ ] Migration `20251101_0900_attempt_view_lock` executed
- [ ] No errors in SQL execution
- [ ] View `attempt` created/replaced successfully
- [ ] Duration: _____ seconds

---

### 3. Alembic History (After)

```bash
# Command
alembic history | head -10

# Output
```

**Verification**:
- [x] `20251101_0900` is now HEAD
- [x] `(head)` marker present

---

### 4. View Schema Validation

#### 4.1 Column Presence

```sql
-- Command
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'attempt' AND table_schema = 'public'
ORDER BY ordinal_position;

-- Output (or screenshot)
```

**Expected Columns** (13 total):
- [x] `id` (bigint, NOT NULL)
- [x] `exam_result_id` (uuid, NOT NULL)
- [x] `student_id` (uuid, NOT NULL)
- [x] `item_id` (integer, NOT NULL)
- [x] `question_id` (integer, NOT NULL)
- [x] `question_text` (text, YES)
- [x] `correct_answer` (text, YES)
- [x] `student_answer` (text, YES)
- [x] `is_correct` (integer, NOT NULL)
- [x] `response_time_ms` (integer, YES)
- [x] `completed_at` (timestamp, NOT NULL)
- [x] `attempt_no` (bigint, YES)
- [x] `tags` (jsonb, YES)

---

#### 4.2 Sample Data Query

```sql
-- Command
SELECT 
  id,
  student_id,
  item_id,
  question_id,
  is_correct,
  response_time_ms,
  attempt_no,
  completed_at
FROM attempt
ORDER BY completed_at DESC
LIMIT 5;

-- Output (or screenshot)
```

**Verification**:
- [ ] Deterministic `id` values (64-bit integer derived from exam_result_id + question_id)
- [ ] `student_id` is UUID or deterministic UUID
- [ ] `response_time_ms` is integer (not float)
- [ ] `attempt_no` is populated via ROW_NUMBER
- [ ] `completed_at` is timestamp without timezone

---

#### 4.3 Row Count

```sql
-- Command
SELECT COUNT(*) AS total_attempts FROM attempt;

-- Output
```

**Result**: _____ rows

**Status**:
- [ ] ✅ Matches expected volume (if known)
- [ ] ⚠️ Zero rows (empty DB - OK for smoke test)
- [ ] ❌ Mismatch - investigate

---

### 5. Determinism Validation

```sql
-- Command
WITH attempts_sample AS (
  SELECT 
    exam_result_id,
    question_id,
    id,
    student_id
  FROM attempt
  LIMIT 1000
)
SELECT 
  COUNT(*) AS total_sampled,
  COUNT(DISTINCT (exam_result_id, question_id)) AS unique_pairs,
  COUNT(DISTINCT id) AS unique_ids
FROM attempts_sample;

-- Output
```

**Expected**: `total_sampled = unique_ids` (1:1 mapping for deterministic ID)

**Verification**:
- [ ] ✅ `id` is unique and deterministic per (exam_result_id, question_id)
- [ ] ❌ Duplicates found - investigate VIEW SQL

---

### 6. Downstream Consumer Validation

#### 6.1 Metrics Pipeline Query

```sql
-- Example: Weekly KPI aggregation query
SELECT 
  student_id,
  COUNT(DISTINCT item_id) AS items_attempted,
  SUM(is_correct) AS correct_count,
  AVG(response_time_ms) AS avg_response_time_ms
FROM attempt
WHERE completed_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY student_id
LIMIT 10;

-- Output (or screenshot)
```

**Verification**:
- [ ] Query executes without errors
- [ ] Results are plausible (non-NULL student_id, reasonable counts)
- [ ] Performance acceptable (< 2s for sample query)

---

#### 6.2 IRT Calibration Query

```sql
-- Example: Item response data for IRT model
SELECT 
  item_id,
  student_id,
  is_correct,
  attempt_no
FROM attempt
WHERE item_id IN (1001, 1002, 1003)  -- Sample items
ORDER BY item_id, attempt_no
LIMIT 20;

-- Output (or screenshot)
```

**Verification**:
- [ ] `attempt_no` correctly ordered for each (student_id, item_id)
- [ ] No NULL values in required fields (student_id, item_id, is_correct)

---

#### 6.3 ETL/Reporting Tool Integration

**Tool**: _____ (e.g., Redash, Looker, Jupyter, R Plumber)

**Test Query**:
```sql
(paste test query used by downstream tool)
```

**Outcome**:
- [ ] ✅ Query executes successfully
- [ ] ✅ Dashboard/report renders correctly
- [ ] ❌ Error encountered: _____ (attach error message)

---

### 7. Smoke Test Execution

```bash
# Command
cd /home/won/projects/dreamseed_monorepo/apps/seedtest_api
pytest tests/test_attempt_view_smoke.py -v

# Output (or screenshot)
```

**Expected**: 5 tests passed

**Verification**:
- [ ] `test_attempt_view_columns_exist` ✅
- [ ] `test_attempt_view_select_minimal` ✅
- [ ] `test_attempt_view_types` ✅
- [ ] `test_attempt_view_student_id_determinism` ✅
- [ ] `test_attempt_view_no_nulls_in_required_fields` ✅

---

### 8. Performance Baseline

```sql
-- Query execution time (no index yet)
EXPLAIN ANALYZE
SELECT *
FROM attempt
WHERE student_id = '<sample-uuid>'
  AND completed_at >= CURRENT_DATE - INTERVAL '30 days';

-- Output (or screenshot)
```

**Metrics**:
- Execution Time: _____ ms
- Planning Time: _____ ms
- Rows Scanned: _____

**Assessment**:
- [ ] ✅ Performance acceptable for V1 (<500ms for typical query)
- [ ] ⚠️ Slow (>500ms) - Note for future index PR (see RUNBOOK)
- [ ] ❌ Timeout/error - investigate immediately

---

### 9. Rollback Readiness

```bash
# Downgrade command (dry-run only)
alembic downgrade -1 --sql

# Output (SQL preview)
```

**Verification**:
- [ ] SQL contains `DROP VIEW IF EXISTS attempt;`
- [ ] No dependent objects would break (VIEW has no dependents in V1)

---

## 🎯 Deployment Decision

### Go/No-Go Criteria

| Criterion | Status | Notes |
|-----------|--------|-------|
| Alembic upgrade succeeded | ⬜ ✅ / ❌ |  |
| All 13 columns present | ⬜ ✅ / ❌ |  |
| Sample data query works | ⬜ ✅ / ❌ |  |
| Determinism verified | ⬜ ✅ / ❌ |  |
| Smoke tests pass (5/5) | ⬜ ✅ / ❌ |  |
| Downstream queries work | ⬜ ✅ / ❌ |  |
| Performance acceptable | ⬜ ✅ / ❌ |  |

### Final Decision

- [ ] ✅ **APPROVED** for Production - All criteria met
- [ ] ⚠️ **APPROVED WITH NOTES** - Minor issues documented below
- [ ] ❌ **BLOCKED** - Critical issues require fixes before production

**Notes/Issues**:
```
(Document any warnings, slowness, or edge cases discovered)
```

---

## 📸 Screenshots/Artifacts

- [ ] Alembic upgrade terminal output
- [ ] Sample query results from staging DB
- [ ] Smoke test run screenshot
- [ ] EXPLAIN ANALYZE output

*Attach screenshots or logs as PR comment attachments*

---

## ⏱️ Deployment Timeline

| Event | Time | Duration |
|-------|------|----------|
| Pre-flight checks | HH:MM | - |
| Alembic upgrade start | HH:MM | - |
| Alembic upgrade complete | HH:MM | ___s |
| Smoke tests | HH:MM | ___s |
| Downstream validation | HH:MM | ___m |
| Evidence capture | HH:MM | ___m |
| **Total deployment time** | - | **___m** |

---

## 👥 Sign-Off

- **Deployed by**: @username (Date: YYYY-MM-DD HH:MM UTC)
- **Validated by**: @username (Date: YYYY-MM-DD HH:MM UTC)
- **Approved for Production**: @username (Date: YYYY-MM-DD HH:MM UTC)

---

## 📝 Post-Deployment Actions

- [ ] Update PR #73 with staging evidence (this template filled)
- [ ] Create Production CR using `PRODUCTION_CR_TEMPLATE.md`
- [ ] Schedule production deployment window
- [ ] Notify downstream teams (ETL, BI, IRT pipeline owners)
- [ ] Monitor staging for 24-48h before production rollout

---

**Template Version**: 1.0  
**Related Documents**: 
- `DEPLOYMENT_GUIDE_attempt_view_lock.md`
- `PRODUCTION_CR_TEMPLATE.md`
- `RUNBOOK_attempt_view_lock.md`
