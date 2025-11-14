# Detect Inactivity Job

비활성 사용자 감지 및 P/S 재계산 배치 작업

## Quick Start

### Local Development

```bash
# From monorepo root
source apps/.venv/bin/activate
export DATABASE_URL='postgresql+psycopg2://user:pass@localhost:5432/dreamseed_db'

# Run with defaults (7 days threshold)
python -m apps.seedtest_api.jobs.detect_inactivity

# Custom threshold
python -m apps.seedtest_api.jobs.detect_inactivity --threshold 14

# Dry-run (no DB commits)
python -m apps.seedtest_api.jobs.detect_inactivity --dry-run
```

### Inside Kubernetes Pod

```bash
NS=seedtest
POD=$(kubectl -n $NS get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')

# Run job
kubectl -n $NS exec -it $POD -- bash -lc '
  python3 -m apps.seedtest_api.jobs.detect_inactivity
'

# Dry-run
kubectl -n $NS exec -it $POD -- bash -lc '
  python3 -m apps.seedtest_api.jobs.detect_inactivity --dry-run
'
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INACTIVITY_THRESHOLD_DAYS` | `7` | Days without activity to trigger recalculation |
| `KPI_LOOKBACK_DAYS` | `30` | Days to look back for user activity |
| `METRICS_DEFAULT_TARGET` | `0.0` | Default target for P(goal) calculation |
| `METRICS_USE_BAYESIAN` | `false` | Use Bayesian mode for P(goal) |
| `METRICS_CHURN_HORIZON_DAYS` | `14` | Horizon for churn risk calculation |
| `DEBUG` | `false` | Enable debug logging per user |
| `DATABASE_URL` | (required) | PostgreSQL connection string |

### CLI Options

```
--threshold N   Inactivity threshold in days (default: 7)
--dry-run       Do not commit changes to database
```

## Data Flow

```
1. Find inactive users (no activity for N days)
   - Check: exam_results.updated_at
   - Check: features_topic_daily.last_seen_at
   - Check: attempt.completed_at
   - Check: session.ended_at (if exists)
2. For each inactive user:
   - Recalculate P(goal|state) using compute_goal_attainment_probability
   - Recalculate S(churn) using compute_churn_risk
3. Update weekly_kpi with new P and S values (preserve I_t, E_t, R_t, A_t)
```

## Database Tables

### Input
- **exam_results**: `user_id`, `updated_at`, `created_at`
- **features_topic_daily**: `user_id`, `last_seen_at`
- **attempt** VIEW: `student_id`, `completed_at`
- **session** (optional): `user_id`, `ended_at`

### Output
- **weekly_kpi**: `user_id`, `week_start`, `kpis` (JSONB with updated P, S)

## Output Format

### Success
```
[INFO] Found 12 inactive users (threshold=7 days); dry_run=False
[INFO] Summary: processed=12, failed=0, threshold=7 days, duration_ms=324
```

### No Inactive Users
```
[INFO] No inactive users found (threshold=7 days)
```

### Errors
```
[ERROR] user=user123 error=division by zero
[WARN] Could not calculate P/S for user=user456
[INFO] Summary: processed=11, failed=1, threshold=7 days, duration_ms=412
```

## Use Cases

### 1. Churn Prevention
7일 이상 미접속 사용자의 이탈 위험도(S)를 재계산하여 알림/개입 트리거

### 2. Goal Probability Update
장기 미접속 사용자의 목표 달성 확률(P)을 현재 상태 기반으로 업데이트

### 3. Event-Driven Recalculation
일일 배치(compute-daily-kpis) 외에 특정 조건 발생 시 즉시 재계산

## Deployment

### Deploy CronJob

```bash
# Apply manifest
kubectl apply -f portal_front/ops/k8s/cron/detect-inactivity.yaml

# Verify
kubectl -n seedtest get cronjob detect-inactivity
kubectl -n seedtest describe cronjob detect-inactivity
```

### Manual Job Run

```bash
# Create one-off job
kubectl -n seedtest create job \
  --from=cronjob/detect-inactivity \
  detect-inactivity-manual-$(date +%Y%m%d-%H%M%S)

# Watch logs
kubectl -n seedtest logs -f job/detect-inactivity-manual-<timestamp>
```

## Validation

### Check Updated KPIs

```sql
-- Check P/S updates for inactive users
SELECT user_id, week_start,
       kpis->>'P' AS goal_prob,
       kpis->>'S' AS churn_risk,
       updated_at
FROM weekly_kpi
WHERE updated_at >= NOW() - INTERVAL '1 hour'
ORDER BY updated_at DESC
LIMIT 20;

-- Find high churn risk users
SELECT user_id, week_start,
       kpis->>'S' AS churn_risk,
       kpis->>'A_t' AS engagement
FROM weekly_kpi
WHERE (kpis->>'S')::float > 0.7
ORDER BY (kpis->>'S')::float DESC
LIMIT 20;
```

### Verify Inactivity Detection

```sql
-- Check last activity for users
SELECT user_id, 
       MAX(COALESCE(updated_at, created_at)) AS last_activity
FROM exam_results
WHERE user_id IS NOT NULL
GROUP BY user_id
HAVING MAX(COALESCE(updated_at, created_at)) < NOW() - INTERVAL '7 days'
ORDER BY last_activity DESC
LIMIT 20;
```

## Troubleshooting

### No Inactive Users Found

```sql
-- Check if there are any users with old activity
SELECT COUNT(DISTINCT user_id) AS inactive_users
FROM exam_results
WHERE COALESCE(updated_at, created_at) < NOW() - INTERVAL '7 days';

-- Check if attempt VIEW has data
SELECT COUNT(DISTINCT student_id) AS inactive_users
FROM attempt
WHERE completed_at < NOW() - INTERVAL '7 days';
```

### P/S Calculation Failed

```bash
# Check metrics service dependencies
# - interest_goal table (for P calculation)
# - exam_results (for S calculation)

# Verify tables exist
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM interest_goal;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM exam_results;"
```

### Performance Issues

- Reduce `INACTIVITY_THRESHOLD_DAYS` to process fewer users
- Add indexes on activity timestamp columns:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_exam_results_updated_at ON exam_results(updated_at);
  CREATE INDEX IF NOT EXISTS idx_features_topic_daily_last_seen ON features_topic_daily(last_seen_at);
  ```

## Integration with Alerting

### Example: Send Alert for High Churn Risk

```python
# After detect_inactivity job completes, trigger alert
# (This would be a separate service/job)

import requests

def send_churn_alerts():
    high_risk_users = session.execute("""
        SELECT user_id, kpis->>'S' AS churn_risk
        FROM weekly_kpi
        WHERE (kpis->>'S')::float > 0.7
          AND updated_at >= NOW() - INTERVAL '1 hour'
    """).fetchall()
    
    for user_id, churn_risk in high_risk_users:
        # Send notification (email, push, etc.)
        requests.post("https://notification-service/send", json={
            "user_id": user_id,
            "type": "churn_warning",
            "message": f"High churn risk detected: {churn_risk}"
        })
```

## Related

- **Metrics Service**: `/apps/seedtest_api/services/metrics.py`
- **CronJob**: `/portal_front/ops/k8s/cron/detect-inactivity.yaml`
- **Deployment Guide**: `/portal_front/ops/k8s/cron/DEPLOYMENT_GUIDE.md`
