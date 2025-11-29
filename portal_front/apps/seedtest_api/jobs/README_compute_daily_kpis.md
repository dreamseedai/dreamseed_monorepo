# Compute Daily KPIs Job

Computes weekly KPI metrics (I_t, E_t, R_t, A_t, P, S) for all active users.

## Quick Start

### Local Development

```bash
# From monorepo root
source apps/.venv/bin/activate
export DATABASE_URL='postgresql+psycopg2://user:pass@localhost:5432/dreamseed_db'

# Run with defaults (today's date)
PYTHONPATH=/home/won/projects/dreamseed_monorepo python -m portal_front.apps.seedtest_api.jobs.compute_daily_kpis

# Run for specific date
PYTHONPATH=/home/won/projects/dreamseed_monorepo python -m portal_front.apps.seedtest_api.jobs.compute_daily_kpis --date 2025-11-01

# Dry-run (no DB commits)
PYTHONPATH=/home/won/projects/dreamseed_monorepo python -m portal_front.apps.seedtest_api.jobs.compute_daily_kpis --dry-run
```

### Inside Kubernetes Pod

```bash
NS=seedtest
POD=$(kubectl -n $NS get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')

# Run job
kubectl -n $NS exec -it $POD -- bash -lc '
  python3 -m portal_front.apps.seedtest_api.jobs.compute_daily_kpis
'

# Dry-run
kubectl -n $NS exec -it $POD -- bash -lc '
  python3 -m portal_front.apps.seedtest_api.jobs.compute_daily_kpis --dry-run
'
```

## Testing

### Run Smoke Tests

```bash
# From monorepo root
source apps/.venv/bin/activate
pytest apps/seedtest_api/tests/test_compute_daily_kpis_smoke.py -v
```

Expected output:
```
✓ test_get_session_returns_session_type PASSED
✓ test_distinct_recent_users_accepts_session PASSED
✓ test_main_uses_session_not_connection PASSED
✓ test_calculate_and_store_weekly_kpi_signature PASSED
```

## Deployment

### Manual Job Run (Staging)

```bash
# Create one-off job from CronJob
kubectl -n seedtest create job \
  --from=cronjob/compute-daily-kpis \
  compute-daily-kpis-manual-$(date +%Y%m%d-%H%M%S)

# Watch logs
kubectl -n seedtest logs -f job/compute-daily-kpis-manual-<timestamp>
```

### Deploy CronJob

```bash
# Apply manifest
kubectl apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml

# Verify
kubectl -n seedtest get cronjob compute-daily-kpis
kubectl -n seedtest describe cronjob compute-daily-kpis
```

### Monitor

```bash
# List recent jobs
kubectl -n seedtest get jobs -l cronjob=compute-daily-kpis --sort-by=.metadata.creationTimestamp

# Check logs
kubectl -n seedtest logs -l job-name=compute-daily-kpis-<timestamp> --tail=50

# Check for failures
kubectl -n seedtest get jobs -l cronjob=compute-daily-kpis --field-selector status.successful!=1
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KPI_LOOKBACK_DAYS` | `30` | Days to look back for active users |
| `METRICS_DEFAULT_TARGET` | `0.0` | Default target for P(goal) calculation |
| `METRICS_USE_BAYESIAN` | `false` | Use Bayesian mode for P(goal) |
| `DEBUG` | `false` | Enable debug logging per-user |
| `DATABASE_URL` | (required) | PostgreSQL connection string |

### CLI Options

```
--date DATE     Anchor date (YYYY-MM-DD, defaults to today)
--dry-run       Do not commit changes to database
```

## Output Format

### Success
```
[INFO] Computing KPIs for 87 users; week_start=2025-10-27, dry_run=False
[INFO] Summary: processed_users=87, failed_users=0, week=2025-10-27, duration_ms=842
```

### No Users
```
[INFO] No recent users found (lookback=30 days); exiting.
```

### Errors
```
[ERROR] user=user123 error=division by zero
[INFO] Summary: processed_users=86, failed_users=1, week=2025-10-27, duration_ms=912
```

### Fatal Error
```
[FATAL] Unhandled exception: connection refused
<traceback>
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

### Type Errors
If you see `Connection cannot be assigned to Session`, ensure you're using the fixed version:
- ✅ Uses `get_session()` (returns `Session`)
- ❌ Old: `engine.begin()` (returns `Connection`)

## Architecture

### Data Flow
```
1. Query exam_results for active users (last N days)
2. For each user:
   - Compute I_t (improvement index)
   - Compute E_t (time efficiency)
   - Compute R_t (recovery rate)
   - Compute A_t (engagement)
   - Compute P (goal attainment probability)
   - Compute S (churn risk)
3. Upsert to weekly_kpi table
```

### Database Tables
- **Input**: `exam_results`, `ability_estimates`, `mirt_ability`, `student_topic_theta`
- **Output**: `weekly_kpi` (user_id, week_start, kpis JSONB)

### Idempotency
Uses `INSERT ... ON CONFLICT (user_id, week_start) DO UPDATE` for safe re-runs.

## Related

- **Metrics Service**: `/apps/seedtest_api/services/metrics.py`
- **Tests**: `/apps/seedtest_api/tests/test_metrics_compute.py`
- **CronJob**: `/portal_front/ops/k8s/cron/compute-daily-kpis.yaml`
