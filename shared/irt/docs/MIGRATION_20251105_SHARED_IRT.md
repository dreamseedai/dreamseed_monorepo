# IRT Database Schema Migration Guide

## Overview

This document describes the `shared_irt` schema migration for the comprehensive IRT (Item Response Theory) drift monitoring system.

## Migration File

**File**: `apps/seedtest_api/alembic/versions/20251105_1400_shared_irt_init.py`

**Revision ID**: `20251105_1400_shared_irt_init`

**Depends On**: `20251105_1000_irt_drift_tables`

**Date**: 2025-11-05 14:00:00

## Purpose

Initialize the `shared_irt` schema with comprehensive IRT tables for:
- Item bank management with rich content (JSONB)
- Operational IRT parameters for CAT and scoring
- Time-windowed calibration for drift monitoring
- Automated drift and DIF detection
- Historical calibration results with confidence intervals
- Response data collection for re-calibration

## Schema Structure

### Schema: `shared_irt`

Independent schema for IRT system isolation from main application tables.

**Benefits:**
- Clear separation of concerns
- Easier backup/restore of IRT data
- Permission management at schema level
- Namespace clarity

## Tables

### 1. `shared_irt.items` (Item Bank)

**Purpose**: Central repository for all test items with metadata.

**Columns:**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY | Auto-incrementing item ID |
| `id_str` | TEXT | UNIQUE, NOT NULL | Human-readable ID (e.g., "MATH-001") |
| `bank_id` | TEXT | NOT NULL | Item bank identifier |
| `lang` | TEXT | NOT NULL, CHECK | Language: en, ko, zh-Hans, zh-Hant |
| `stem_rich` | JSONB | | Item stem with HTML/LaTeX/images |
| `options_rich` | JSONB | | Answer choices with rich formatting |
| `answer_key` | JSONB | | Correct answer(s) |
| `topic_tags` | TEXT[] | DEFAULT '{}' | Topic classifications |
| `subtopic_tags` | TEXT[] | DEFAULT '{}' | Subtopic classifications |
| `curriculum_tags` | TEXT[] | DEFAULT '{}' | Curriculum alignments (CCSS, etc.) |
| `metadata` | JSONB | DEFAULT '{}' | Additional metadata |
| `is_anchor` | BOOLEAN | DEFAULT false | Anchor item for equating |
| `exposure_count` | INTEGER | DEFAULT 0 | Total exposures (CAT exposure control) |
| `created_at` | TIMESTAMP(tz) | DEFAULT now() | Creation timestamp |
| `updated_at` | TIMESTAMP(tz) | DEFAULT now() | Last update timestamp |

**Indexes:**
- `idx_items_bank_lang` on `(bank_id, lang)` - Fast filtering by bank and language
- `idx_items_id_str` on `(id_str)` UNIQUE - Lookup by human ID
- `idx_items_anchor` on `(is_anchor)` WHERE `is_anchor = true` - Partial index for anchor items

**Use Cases:**
- Item content management
- Multi-language item versions
- CAT item pool selection
- Exposure rate monitoring
- Equating anchor item identification

**Example Data:**
```json
{
  "id": 1234,
  "id_str": "MATH-ALG-001",
  "bank_id": "SAT_MATH",
  "lang": "en",
  "stem_rich": {
    "html": "<p>Solve for x: <math>2x + 3 = 11</math></p>",
    "images": []
  },
  "options_rich": [
    {"key": "A", "text": "x = 2"},
    {"key": "B", "text": "x = 4"},
    {"key": "C", "text": "x = 7"},
    {"key": "D", "text": "x = 14"}
  ],
  "answer_key": {"correct": ["B"]},
  "topic_tags": ["algebra", "linear_equations"],
  "is_anchor": false,
  "exposure_count": 1523
}
```

---

### 2. `shared_irt.item_parameters_current` (Operational Parameters)

**Purpose**: Current active IRT parameters for real-time CAT and scoring.

**Columns:**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `item_id` | BIGINT | PRIMARY KEY, FK → items | Item reference |
| `model` | TEXT | NOT NULL, CHECK | IRT model: 1PL, 2PL, 3PL |
| `a` | FLOAT | | Discrimination parameter |
| `b` | FLOAT | NOT NULL | Difficulty parameter |
| `c` | FLOAT | | Guessing parameter |
| `a_se` | FLOAT | | Standard error of a |
| `b_se` | FLOAT | | Standard error of b |
| `c_se` | FLOAT | | Standard error of c |
| `theta_min` | FLOAT | DEFAULT -4.0 | Min theta for info curve |
| `theta_max` | FLOAT | DEFAULT 4.0 | Max theta for info curve |
| `version` | INTEGER | NOT NULL, DEFAULT 1 | Parameter version number |
| `effective_from` | TIMESTAMP(tz) | NOT NULL, DEFAULT now() | When parameters became active |
| `note` | TEXT | | Version change notes |
| `updated_at` | TIMESTAMP(tz) | DEFAULT now() | Last update |

**Constraints:**
- `CHECK (model IN ('1PL','2PL','3PL'))` - Valid IRT models
- `ON DELETE CASCADE` - Auto-delete when item deleted

**Use Cases:**
- CAT item selection (max Fisher information)
- Real-time ability estimation (EAP, MLE)
- Test scoring
- Information curve calculation
- Parameter versioning for A/B testing

**Example Data:**
```sql
INSERT INTO shared_irt.item_parameters_current VALUES
(1234, '2PL', 1.2, 0.5, NULL, 0.08, 0.06, NULL, -4.0, 4.0, 2, '2025-10-01', 'Recalibrated Q4 2025', now());
```

**Notes:**
- Only ONE row per item (PRIMARY KEY on item_id)
- Historical parameters stored in `item_calibration` table
- Update this table when promoting new calibration results

---

### 3. `shared_irt.windows` (Calibration Windows)

**Purpose**: Define time periods for windowed calibration and drift detection.

**Columns:**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY, AUTO | Window ID |
| `label` | TEXT | UNIQUE, NOT NULL | Human-readable label |
| `start_at` | TIMESTAMP(tz) | NOT NULL | Window start (inclusive) |
| `end_at` | TIMESTAMP(tz) | NOT NULL | Window end (exclusive) |
| `population_tags` | TEXT[] | DEFAULT '{}' | Population filters |
| `created_at` | TIMESTAMP(tz) | DEFAULT now() | Creation timestamp |

**Indexes:**
- `idx_windows_times` on `(start_at, end_at)` - Time range queries
- `idx_windows_label` on `(label)` UNIQUE - Lookup by label

**Use Cases:**
- Define calibration periods (monthly, quarterly)
- Filter responses by time range
- Track parameter drift over time
- Compare baseline vs. recent windows

**Example Data:**
```sql
INSERT INTO shared_irt.windows (label, start_at, end_at, population_tags) VALUES
('2025-Q1', '2025-01-01', '2025-04-01', ARRAY['grade_9', 'grade_10']),
('2025-Q2', '2025-04-01', '2025-07-01', ARRAY['grade_9', 'grade_10']),
('2025-10', '2025-10-01', '2025-11-01', ARRAY['all']);
```

**Best Practices:**
- Use consistent labeling scheme (YYYY-QN or YYYY-MM)
- Non-overlapping windows for drift detection
- Minimum 30 days per window (statistical stability)
- Minimum 30 responses per item per window

---

### 4. `shared_irt.item_calibration` (Historical Calibration)

**Purpose**: Store windowed IRT parameter estimates for drift monitoring.

**Columns:**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY, AUTO | Calibration record ID |
| `item_id` | BIGINT | FK → items, NOT NULL | Item reference |
| `window_id` | BIGINT | FK → windows, NOT NULL | Window reference |
| `model` | TEXT | NOT NULL, CHECK | IRT model used |
| `a_hat` | FLOAT | | Discrimination estimate |
| `b_hat` | FLOAT | NOT NULL | Difficulty estimate |
| `c_hat` | FLOAT | | Guessing estimate |
| `a_ci_low` | FLOAT | | Lower 95% CI for a |
| `a_ci_high` | FLOAT | | Upper 95% CI for a |
| `b_ci_low` | FLOAT | | Lower 95% CI for b |
| `b_ci_high` | FLOAT | | Upper 95% CI for b |
| `c_ci_low` | FLOAT | | Lower 95% CI for c |
| `c_ci_high` | FLOAT | | Upper 95% CI for c |
| `n_responses` | INTEGER | NOT NULL | Sample size |
| `loglik` | FLOAT | | Log-likelihood |
| `converged` | BOOLEAN | DEFAULT true | Convergence flag |
| `drift_flag` | TEXT | | Drift severity: low, medium, high |
| `dif_metadata` | JSONB | DEFAULT '{}' | DIF analysis results |
| `created_at` | TIMESTAMP(tz) | DEFAULT now() | Calibration timestamp |

**Indexes:**
- `idx_item_calibration_item_window` on `(item_id, window_id)` UNIQUE - One calibration per item per window
- `idx_item_calibration_window` on `(window_id)` - Window-level queries
- `idx_item_calibration_drift` on `(drift_flag)` WHERE `drift_flag IS NOT NULL` - Partial index for drifted items

**Constraints:**
- `CHECK (model IN ('1PL','2PL','3PL'))`
- `ON DELETE CASCADE` for both FKs
- `UNIQUE (item_id, window_id)` - Prevent duplicate calibrations

**Use Cases:**
- Historical parameter tracking
- Drift detection (compare consecutive windows)
- Confidence interval overlap analysis
- DIF detection across groups
- Convergence diagnostics

**Example Data:**
```sql
INSERT INTO shared_irt.item_calibration 
(item_id, window_id, model, a_hat, b_hat, c_hat, a_ci_low, a_ci_high, b_ci_low, b_ci_high, n_responses, loglik, converged, drift_flag, dif_metadata)
VALUES
(1234, 1, '2PL', 1.15, 0.48, NULL, 1.05, 1.25, 0.42, 0.54, 523, -345.2, true, NULL, '{}'),
(1234, 2, '2PL', 1.18, 0.73, NULL, 1.08, 1.28, 0.67, 0.79, 489, -332.1, true, 'medium', 
 '{"delta_b": 0.25, "delta_a": 0.03}'::jsonb);
```

**DIF Metadata Example:**
```json
{
  "dif_analysis": {
    "language": {
      "reference_group": "en",
      "focal_group": "ko",
      "delta_b": 0.35,
      "prob_delta_b_gt_03": 0.92,
      "bayes_factor": 12.3
    }
  }
}
```

---

### 5. `shared_irt.drift_alerts` (Drift Detection Alerts)

**Purpose**: Automated alerts for parameter drift and DIF detection.

**Columns:**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY, AUTO | Alert ID |
| `item_id` | BIGINT | FK → items, NULLABLE | Item ID (NULL for test-level alerts) |
| `window_id` | BIGINT | FK → windows, NOT NULL | Window where drift detected |
| `metric` | TEXT | NOT NULL | Metric name |
| `value` | FLOAT | | Observed metric value |
| `threshold` | FLOAT | | Threshold exceeded |
| `severity` | TEXT | NOT NULL, CHECK | Alert severity: low, medium, high |
| `message` | TEXT | | Human-readable message |
| `resolved_at` | TIMESTAMP(tz) | | Resolution timestamp |
| `created_at` | TIMESTAMP(tz) | DEFAULT now() | Alert creation time |

**Indexes:**
- `idx_drift_alerts_item_window` on `(item_id, window_id)` - Item-window queries
- `idx_drift_alerts_severity_unresolved` on `(severity, created_at)` WHERE `resolved_at IS NULL` - Active alerts
- `idx_drift_alerts_window` on `(window_id)` - Window summary queries

**Constraints:**
- `CHECK (severity IN ('low','medium','high'))`
- `ON DELETE CASCADE` for both FKs

**Metric Types:**
- `delta_b`, `delta_a`, `delta_c` - Parameter changes
- `dif_prob`, `dif_bf` - DIF detection (Bayesian)
- `info_drop_low`, `info_drop_high`, etc. - Information function drops
- `max_info_drop` - Item max information drop

**Use Cases:**
- Daily drift monitoring dashboard
- Email notifications for HIGH severity
- Weekly review reports
- Item flagging workflow
- Audit trail

**Example Data:**
```sql
INSERT INTO shared_irt.drift_alerts 
(item_id, window_id, metric, value, threshold, severity, message, resolved_at)
VALUES
(1234, 2, 'delta_b', 0.55, 0.5, 'high', 
 'Difficulty parameter drift: |Δb| = 0.550 exceeds 0.5 (high risk threshold)', 
 NULL),
(1234, 2, 'dif_prob', 0.93, 0.9, 'high',
 'DIF detected between en (ref) and ko (focal): P(|Δb| > 0.3) = 0.93, Δb = 0.352',
 NULL);
```

---

### 6. `shared_irt.item_responses` (Response Data)

**Purpose**: Store item response data for IRT calibration.

**Columns:**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY, AUTO | Response ID |
| `org_id` | TEXT | NOT NULL | Organization identifier |
| `user_id_hash` | TEXT | NOT NULL | Hashed user ID (privacy) |
| `session_id` | TEXT | | Test session identifier |
| `item_id` | BIGINT | FK → items, NOT NULL | Item reference |
| `started_at` | TIMESTAMP(tz) | | When item presented |
| `answered_at` | TIMESTAMP(tz) | NOT NULL, DEFAULT now() | When response submitted |
| `is_correct` | BOOLEAN | | Correctness (dichotomous) |
| `score` | FLOAT | | Score (polytomous/partial credit) |
| `response_payload` | JSONB | DEFAULT '{}' | Full response data |
| `lang` | TEXT | NOT NULL, CHECK | Response language |
| `extra` | JSONB | DEFAULT '{}' | Additional metadata |

**Indexes:**
- `idx_item_responses_item` on `(item_id)` - Item-level aggregation
- `idx_item_responses_answered_at` on `(answered_at)` - Time-based windowing
- `idx_item_responses_session` on `(session_id)` - Session analysis
- `idx_item_responses_user_hash` on `(user_id_hash)` - User history

**Constraints:**
- `CHECK (lang IN ('en','ko','zh-Hans','zh-Hant'))`
- `ON DELETE CASCADE` for item_id FK

**Use Cases:**
- Windowed calibration (filter by answered_at)
- Sample size calculation (n_responses)
- DIF analysis (group by lang, org_id)
- Response time analysis
- Guessing detection

**Example Data:**
```sql
INSERT INTO shared_irt.item_responses
(org_id, user_id_hash, session_id, item_id, started_at, answered_at, is_correct, score, response_payload, lang, extra)
VALUES
('org_123', 'hash_abc123', 'session_xyz', 1234, '2025-11-05 10:00:00+00', '2025-11-05 10:02:15+00', 
 true, 1.0, '{"selected": "B", "response_time_ms": 135000}'::jsonb, 'en', 
 '{"device": "mobile", "country": "US"}'::jsonb);
```

**Privacy Notes:**
- `user_id_hash`: SHA-256 hash of user_id (irreversible)
- No PII stored in this table
- GDPR-compliant (pseudonymized data)

---

## Relationships

### Entity Relationship Diagram

```
┌─────────────────┐
│     items       │
│  (item bank)    │
└────────┬────────┘
         │ 1
         │
         ├──────────────┐
         │              │
         │ *            │ 1
┌────────▼────────┐    │
│item_parameters_ │    │
│    current      │    │
│  (operational)  │    │
└─────────────────┘    │
                       │
         ┌─────────────┤
         │             │
         │ *           │ *
┌────────▼────────┐   │
│item_calibration │◄──┤
│  (historical)   │   │
└────────┬────────┘   │
         │            │
         │ *          │
┌────────▼────────┐   │
│ drift_alerts    │   │
└────────┬────────┘   │
         │            │
         │            │ 1
         │       ┌────▼────────┐
         │       │   windows   │
         │       │(time periods)│
         │       └─────────────┘
         │
         │ *
┌────────▼────────┐
│ item_responses  │
│ (response data) │
└─────────────────┘
```

### Foreign Key Relationships

1. **item_parameters_current.item_id → items.id** (1:1)
   - Each item has one current parameter set
   - CASCADE DELETE

2. **item_calibration.item_id → items.id** (1:N)
   - Each item has multiple historical calibrations
   - CASCADE DELETE

3. **item_calibration.window_id → windows.id** (N:1)
   - Each window has many item calibrations
   - CASCADE DELETE

4. **drift_alerts.item_id → items.id** (N:1, NULLABLE)
   - Each item can have multiple alerts
   - NULL for test-level alerts
   - CASCADE DELETE

5. **drift_alerts.window_id → windows.id** (N:1)
   - Each window can have multiple alerts
   - CASCADE DELETE

6. **item_responses.item_id → items.id** (N:1)
   - Each item has many responses
   - CASCADE DELETE

---

## Migration Execution

### Prerequisites

```bash
# Ensure PostgreSQL 12+ (for JSONB improvements)
psql --version

# Check alembic is installed
cd apps/seedtest_api
pip install alembic psycopg2-binary

# Verify database connection
export DATABASE_URL="postgresql://user:pass@host:5432/dreamseed"
psql $DATABASE_URL -c "SELECT version();"
```

### Run Migration

```bash
# Check current revision
alembic current

# Preview SQL (dry run)
alembic upgrade 20251105_1400_shared_irt_init --sql

# Apply migration
alembic upgrade 20251105_1400_shared_irt_init

# Or upgrade to latest
alembic upgrade head
```

### Verify Migration

```sql
-- Check schema exists
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'shared_irt';

-- List all tables
\dt shared_irt.*

-- Count tables (should be 6)
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'shared_irt';

-- Check indexes
SELECT tablename, indexname FROM pg_indexes 
WHERE schemaname = 'shared_irt' ORDER BY tablename, indexname;

-- Check constraints
SELECT conname, contype FROM pg_constraint 
WHERE connamespace = 'shared_irt'::regnamespace;
```

### Rollback (if needed)

```bash
# Rollback to previous revision
alembic downgrade 20251105_1000_irt_drift_tables

# Check current state
alembic current
```

---

## Post-Migration Tasks

### 1. Grant Permissions

```sql
-- Create roles if not exist
CREATE ROLE irt_admin;
CREATE ROLE irt_readonly;

-- Grant schema permissions
GRANT USAGE ON SCHEMA shared_irt TO irt_admin, irt_readonly;

-- Admin permissions (full access)
GRANT ALL ON ALL TABLES IN SCHEMA shared_irt TO irt_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA shared_irt TO irt_admin;

-- Read-only permissions
GRANT SELECT ON ALL TABLES IN SCHEMA shared_irt TO irt_readonly;

-- Future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA shared_irt 
  GRANT ALL ON TABLES TO irt_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA shared_irt 
  GRANT SELECT ON TABLES TO irt_readonly;
```

### 2. Initial Data Seeding

See: `shared/irt/docs/SEEDING_GUIDE.md` (to be created)

```sql
-- Example: Create first window
INSERT INTO shared_irt.windows (label, start_at, end_at) VALUES
('2025-11-baseline', '2025-11-01', '2025-12-01');
```

### 3. Setup Monitoring

```sql
-- Monitor table sizes
SELECT 
  schemaname, 
  tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'shared_irt'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Monitor response data growth
SELECT 
  DATE_TRUNC('day', answered_at) AS day,
  COUNT(*) AS responses
FROM shared_irt.item_responses
GROUP BY day
ORDER BY day DESC
LIMIT 30;
```

---

## Performance Considerations

### Expected Data Volumes

| Table | Rows (Year 1) | Growth Rate | Index Size |
|-------|---------------|-------------|------------|
| items | 5,000-10,000 | Low (manual) | ~5 MB |
| item_parameters_current | 5,000-10,000 | Low | ~2 MB |
| windows | 12-50 | Low | <1 MB |
| item_calibration | 50K-500K | Medium | ~50 MB |
| drift_alerts | 1K-10K | Medium | ~5 MB |
| item_responses | 10M-100M | **HIGH** | ~10 GB |

### Partitioning Recommendations

**item_responses** should be partitioned by `answered_at` (monthly):

```sql
-- Convert to partitioned table (future enhancement)
CREATE TABLE shared_irt.item_responses_new (LIKE shared_irt.item_responses)
PARTITION BY RANGE (answered_at);

-- Create monthly partitions
CREATE TABLE shared_irt.item_responses_2025_11 
PARTITION OF shared_irt.item_responses_new
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

### Index Maintenance

```sql
-- Rebuild indexes quarterly
REINDEX TABLE shared_irt.item_responses;

-- Analyze for query optimization
ANALYZE shared_irt.item_responses;
ANALYZE shared_irt.item_calibration;

-- Vacuum to reclaim space
VACUUM ANALYZE shared_irt.item_responses;
```

---

## Backup Strategy

### Full Schema Backup

```bash
# Backup shared_irt schema only
pg_dump $DATABASE_URL --schema=shared_irt --file=shared_irt_backup_$(date +%Y%m%d).sql

# Backup with compression
pg_dump $DATABASE_URL --schema=shared_irt --format=custom --file=shared_irt_$(date +%Y%m%d).dump
```

### Selective Backups

```bash
# Backup without large response table
pg_dump $DATABASE_URL --schema=shared_irt \
  --exclude-table=shared_irt.item_responses \
  --file=shared_irt_no_responses_$(date +%Y%m%d).sql

# Backup only metadata tables
pg_dump $DATABASE_URL \
  --table=shared_irt.items \
  --table=shared_irt.item_parameters_current \
  --table=shared_irt.windows \
  --file=shared_irt_metadata_$(date +%Y%m%d).sql
```

### Restore

```bash
# Restore from SQL dump
psql $DATABASE_URL < shared_irt_backup_20251105.sql

# Restore from custom format
pg_restore --dbname=$DATABASE_URL shared_irt_20251105.dump
```

---

## Troubleshooting

### Migration Fails

**Issue**: `relation "shared_irt.items" already exists`

**Solution**:
```bash
# Check if partially applied
psql $DATABASE_URL -c "\dt shared_irt.*"

# Drop and retry (CAUTION: destroys data)
psql $DATABASE_URL -c "DROP SCHEMA shared_irt CASCADE;"
alembic upgrade 20251105_1400_shared_irt_init
```

### Performance Issues

**Issue**: Slow queries on `item_responses`

**Solution**:
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'shared_irt' AND tablename = 'item_responses';

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_item_responses_org_item 
ON shared_irt.item_responses(org_id, item_id);
```

### Foreign Key Violations

**Issue**: Cannot insert into `item_calibration` - FK violation

**Solution**:
```sql
-- Verify referenced records exist
SELECT id FROM shared_irt.items WHERE id = 1234;
SELECT id FROM shared_irt.windows WHERE id = 1;

-- Insert missing records first
INSERT INTO shared_irt.windows (label, start_at, end_at) 
VALUES ('2025-11', '2025-11-01', '2025-12-01');
```

---

## Related Documentation

- **Schema Design**: `shared/irt/docs/SCHEMA_DESIGN.md`
- **Calibration Guide**: `shared/irt/docs/CALIBRATION_GUIDE.md`
- **Drift Thresholds**: `shared/irt/docs/THRESHOLDS_AND_DIF.md`
- **API Reference**: `apps/seedtest_api/app/routers/analytics_irt.py`
- **Report Templates**: `shared/irt/reports/templates/`

---

## Changelog

### Version 1.0.0 (2025-11-05)

**Initial Release**
- Created `shared_irt` schema
- 6 tables: items, item_parameters_current, windows, item_calibration, drift_alerts, item_responses
- 14 indexes for query optimization
- CHECK constraints for data validation
- Foreign key CASCADE DELETE for referential integrity
- JSONB columns for flexible metadata storage
- Array columns for tag storage
- Timestamp columns with timezone support

**Migration File**: `20251105_1400_shared_irt_init.py`

---

## Contributors

- **Author**: AI Assistant
- **Reviewer**: Engineering Team
- **Date**: 2025-11-05
- **Repository**: dreamseed_monorepo
- **Branch**: staging/attempt-view-lock-v1
