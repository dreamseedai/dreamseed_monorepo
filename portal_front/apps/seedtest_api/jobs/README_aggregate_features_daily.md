# Aggregate Features Daily Job

일일 토픽별 피처 집계 배치 작업 - `features_topic_daily` 테이블 업데이트

## Quick Start

### Local Development

```bash
# From monorepo root
source apps/.venv/bin/activate
export DATABASE_URL='postgresql+psycopg2://user:pass@localhost:5432/dreamseed_db'

# Run with defaults (yesterday's data)
python -m apps.seedtest_api.jobs.aggregate_features_daily

# Run for specific date
python -m apps.seedtest_api.jobs.aggregate_features_daily --date 2025-11-01

# Dry-run (no DB commits)
python -m apps.seedtest_api.jobs.aggregate_features_daily --dry-run

# Enable IRT theta estimates
export AGG_INCLUDE_THETA=true
python -m apps.seedtest_api.jobs.aggregate_features_daily
```

### Inside Kubernetes Pod

```bash
NS=seedtest
POD=$(kubectl -n $NS get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')

# Run job
kubectl -n $NS exec -it $POD -- bash -lc '
  python3 -m apps.seedtest_api.jobs.aggregate_features_daily
'

# Dry-run
kubectl -n $NS exec -it $POD -- bash -lc '
  python3 -m apps.seedtest_api.jobs.aggregate_features_daily --dry-run
'
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGG_LOOKBACK_DAYS` | `7` | Days to look back for aggregation |
| `AGG_INCLUDE_THETA` | `false` | Include IRT theta estimates from student_topic_theta |
| `DEBUG` | `false` | Enable debug logging per user/topic/date |
| `DATABASE_URL` | (required) | PostgreSQL connection string |

### CLI Options

```
--date DATE     Anchor date (YYYY-MM-DD, defaults to yesterday)
--dry-run       Do not commit changes to database
```

## Output Format

### Success
```
[INFO] Aggregating features for 1234 (user, topic, date) combinations; since=2025-10-25, anchor=2025-11-01, dry_run=False
[INFO] Summary: processed=1234, failed=0, duration_ms=8420
```

### No Data
```
[INFO] No (user_id, topic_id, date) combinations found (lookback=7 days); exiting.
```

### Errors
```
[ERROR] user=user123 topic=algebra date=2025-11-01 error=division by zero
[INFO] Summary: processed=1233, failed=1, duration_ms=8512
```

## Data Flow

```
1. Query attempt VIEW for distinct (user_id, topic_id, date) in last N days
2. For each combination:
   - Aggregate: attempts, correct, avg_time_ms, rt_median, hints
   - Load theta estimate (if AGG_INCLUDE_THETA=true)
   - Calculate improvement index (14-day window)
3. Upsert to features_topic_daily table
```

## Database Tables

### Input
- **attempt** VIEW: `student_id`, `topic_id`, `completed_at`, `correct`, `response_time_ms`, `hint_used`
- **student_topic_theta** (optional): `user_id`, `topic_id`, `theta`, `se`, `updated_at`

### Output
- **features_topic_daily**: `user_id`, `topic_id`, `date`, `attempts`, `correct`, `avg_time_ms`, `hints`, `theta_estimate`, `theta_sd`, `rt_median`, `improvement`, `last_seen_at`, `computed_at`

## Deployment

### Manual Job Run (Staging)

```bash
# Create one-off job from CronJob
kubectl -n seedtest create job \
  --from=cronjob/aggregate-features-daily \
  aggregate-features-manual-$(date +%Y%m%d-%H%M%S)

# Watch logs
kubectl -n seedtest logs -f job/aggregate-features-manual-<timestamp>
```

### Deploy CronJob

```bash
# Apply manifest
kubectl apply -f portal_front/ops/k8s/cron/aggregate-features-daily.yaml

# Verify
kubectl -n seedtest get cronjob aggregate-features-daily
kubectl -n seedtest describe cronjob aggregate-features-daily
```

### Monitor

```bash
# List recent jobs
kubectl -n seedtest get jobs -l cronjob=aggregate-features-daily --sort-by=.metadata.creationTimestamp

# Check logs
kubectl -n seedtest logs -l job-name=aggregate-features-daily-<timestamp> --tail=50

# Check for failures
kubectl -n seedtest get jobs -l cronjob=aggregate-features-daily --field-selector status.successful!=1
```

## Validation

### Check Output Data

```sql
-- Recent aggregations
SELECT user_id, topic_id, date, attempts, correct, rt_median, improvement
FROM features_topic_daily
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC, user_id, topic_id
LIMIT 20;

-- Aggregation coverage
SELECT date, COUNT(DISTINCT user_id) AS users, COUNT(*) AS records
FROM features_topic_daily
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY date
ORDER BY date DESC;

-- Check theta estimates (if AGG_INCLUDE_THETA=true)
SELECT user_id, topic_id, date, theta_estimate, theta_sd
FROM features_topic_daily
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
  AND theta_estimate IS NOT NULL
ORDER BY date DESC
LIMIT 20;
```

## Troubleshooting

### Import Errors
Ensure `PYTHONPATH` includes monorepo root:
```bash
export PYTHONPATH=/home/won/projects/dreamseed_monorepo
```

### Database Connection
Verify `DATABASE_URL` is set and accessible:
```bash
psql "$DATABASE_URL" -c "SELECT 1"
```

### No Data Found
Check if `attempt` VIEW exists and has data:
```sql
SELECT COUNT(*) FROM attempt WHERE completed_at >= NOW() - INTERVAL '7 days';
```

### Slow Performance
- Reduce `AGG_LOOKBACK_DAYS` (default: 7)
- Add index on `attempt(student_id, topic_id, completed_at)`
- Consider batching by date

## Related

- **Metrics Service**: `/apps/seedtest_api/services/metrics.py`
- **Model**: `/apps/seedtest_api/models/features_topic_daily.py`
- **CronJob**: `/portal_front/ops/k8s/cron/aggregate-features-daily.yaml`
- **Deployment Guide**: `/portal_front/ops/k8s/cron/DEPLOYMENT_GUIDE.md`
