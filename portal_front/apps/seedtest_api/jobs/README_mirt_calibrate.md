# MIRT Calibration Job

IRT 모형 파라미터 추정 및 능력치 업데이트 배치 작업

## Quick Start

### Local Development

```bash
# From monorepo root
source apps/.venv/bin/activate
export DATABASE_URL='postgresql+psycopg2://user:pass@localhost:5432/dreamseed_db'
export R_IRT_BASE_URL='http://localhost:8000'
export R_IRT_INTERNAL_TOKEN='your-token'

# Run with defaults (30 days lookback, 2PL model)
python -m apps.seedtest_api.jobs.mirt_calibrate

# Custom lookback and model
export IRT_CALIB_LOOKBACK_DAYS=60
export IRT_MODEL=3PL
python -m apps.seedtest_api.jobs.mirt_calibrate
```

### Inside Kubernetes Pod

```bash
NS=seedtest
POD=$(kubectl -n $NS get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')

# Run job
kubectl -n $NS exec -it $POD -- bash -lc '
  python3 -m apps.seedtest_api.jobs.mirt_calibrate
'
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IRT_CALIB_LOOKBACK_DAYS` | `30` | Days to look back for observations |
| `IRT_MODEL` | `2PL` | IRT model type (1PL, 2PL, 3PL) |
| `R_IRT_BASE_URL` | (required) | R IRT Plumber service URL |
| `R_IRT_INTERNAL_TOKEN` | (required) | Authentication token for R IRT service |
| `R_IRT_TIMEOUT_SECS` | `300` | Timeout for R IRT service calls (seconds) |
| `DATABASE_URL` | (required) | PostgreSQL connection string |

## Data Flow

```
1. Extract observations from attempt VIEW (last N days)
   - Fallback: responses table → exam_results JSON
2. Call R IRT Plumber service (/calibrate endpoint)
   - Input: [{user_id, item_id, is_correct, responded_at}, ...]
   - Output: {item_params, abilities, fit_meta}
3. Upsert results to database:
   - mirt_item_params: item-level parameters (a, b, c)
   - mirt_ability: user-level ability estimates (θ, SE)
   - mirt_fit_meta: model fit statistics
```

## Database Tables

### Input
- **attempt** VIEW: `student_id`, `item_id`, `correct`, `completed_at`
- Fallback: **responses** or **exam_results**

### Output
- **mirt_item_params**: `item_id`, `model`, `params` (JSONB: {a, b, c}), `version`, `fitted_at`
- **mirt_ability**: `user_id`, `theta`, `se`, `model`, `version`, `fitted_at`
- **mirt_fit_meta**: `run_id`, `model_spec` (JSONB), `metrics` (JSONB), `fitted_at`

## Output Format

### Success
```
[INFO] Loaded 5000 observations from attempt VIEW
[INFO] Calling R IRT service...
Calibration upsert completed.
```

### Fallback to responses
```
[WARN] attempt VIEW not available: relation "attempt" does not exist; trying fallback...
[INFO] Loaded 3000 observations from responses table
Calibration upsert completed.
```

### No Data
```
No observations found; exiting.
```

### R Service Error
```
[ERROR] R IRT service call failed: Connection refused
```

## R IRT Plumber Service

### Prerequisites

R IRT Plumber 서비스가 배포되어 있어야 합니다.

#### Service Deployment (Example)

```yaml
# r-irt-plumber-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: r-irt-plumber
  namespace: seedtest
spec:
  replicas: 2
  selector:
    matchLabels:
      app: r-irt-plumber
  template:
    metadata:
      labels:
        app: r-irt-plumber
    spec:
      containers:
        - name: r-irt-plumber
          image: gcr.io/univprepai/r-irt-plumber:latest
          ports:
            - containerPort: 8000
          env:
            - name: PLUMBER_PORT
              value: "8000"
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: r-irt-plumber
  namespace: seedtest
spec:
  selector:
    app: r-irt-plumber
  ports:
    - protocol: TCP
      port: 8000
      targetPort: 8000
```

```bash
# Deploy R IRT service
kubectl -n seedtest apply -f r-irt-plumber-deployment.yaml

# Verify
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# Test health endpoint
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:8000/health
```

### API Contract

#### POST /calibrate

**Request**:
```json
{
  "observations": [
    {
      "user_id": "user123",
      "item_id": "item456",
      "is_correct": true,
      "responded_at": "2025-11-01T12:34:56Z"
    }
  ],
  "model": "2PL"
}
```

**Response**:
```json
{
  "item_params": [
    {
      "item_id": "item456",
      "model": "2PL",
      "params": {"a": 1.2, "b": 0.5},
      "version": "v1"
    }
  ],
  "abilities": [
    {
      "user_id": "user123",
      "theta": 0.8,
      "se": 0.15,
      "model": "2PL",
      "version": "v1"
    }
  ],
  "fit_meta": {
    "run_id": "fit-2025-11-01T03:00:00Z",
    "model_spec": {"model": "2PL", "n_items": 100, "n_users": 50},
    "metrics": {"logLik": -1234.5, "AIC": 2500.0}
  }
}
```

## Deployment

### Create Secret

```bash
# Create R IRT credentials secret
kubectl -n seedtest create secret generic seedtest-irt-credentials \
  --from-literal=R_IRT_BASE_URL='http://r-irt-plumber.seedtest.svc.cluster.local:8000' \
  --from-literal=R_IRT_INTERNAL_TOKEN='<your-internal-token>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Deploy CronJob

```bash
# Apply manifest
kubectl apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml

# Verify
kubectl -n seedtest get cronjob mirt-calibrate
kubectl -n seedtest describe cronjob mirt-calibrate
```

### Manual Job Run

```bash
# Create one-off job
kubectl -n seedtest create job \
  --from=cronjob/mirt-calibrate \
  mirt-calibrate-manual-$(date +%Y%m%d-%H%M%S)

# Watch logs (may take 5-10 minutes)
kubectl -n seedtest logs -f job/mirt-calibrate-manual-<timestamp>
```

## Validation

### Check Output Data

```sql
-- Item parameters
SELECT item_id, model, 
       params->>'a' AS discrimination,
       params->>'b' AS difficulty,
       params->>'c' AS guessing,
       fitted_at
FROM mirt_item_params
ORDER BY fitted_at DESC
LIMIT 20;

-- User abilities
SELECT user_id, theta, se, model, fitted_at
FROM mirt_ability
ORDER BY fitted_at DESC
LIMIT 20;

-- Fit metadata
SELECT run_id, 
       model_spec->>'model' AS model,
       model_spec->>'n_items' AS n_items,
       model_spec->>'n_users' AS n_users,
       metrics->>'logLik' AS log_likelihood,
       fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 5;

-- Coverage check
SELECT 
  (SELECT COUNT(DISTINCT item_id) FROM mirt_item_params) AS items_calibrated,
  (SELECT COUNT(DISTINCT user_id) FROM mirt_ability) AS users_calibrated,
  (SELECT COUNT(*) FROM attempt WHERE completed_at >= NOW() - INTERVAL '30 days') AS total_observations;
```

## Troubleshooting

### R IRT Service Connection Failed

```bash
# Check service status
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# Check service endpoints
kubectl -n seedtest get endpoints r-irt-plumber

# Test connectivity from job pod
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:8000/health

# Check R IRT pod logs
kubectl -n seedtest logs -l app=r-irt-plumber --tail=50
```

### No Observations Found

```sql
-- Check attempt VIEW
SELECT COUNT(*) FROM attempt WHERE completed_at >= NOW() - INTERVAL '30 days';

-- Check if attempt VIEW exists
SELECT table_name FROM information_schema.views WHERE table_name = 'attempt';

-- If VIEW doesn't exist, check fallback tables
SELECT COUNT(*) FROM responses WHERE responded_at >= NOW() - INTERVAL '30 days';
SELECT COUNT(*) FROM exam_results WHERE updated_at >= NOW() - INTERVAL '30 days';
```

### Calibration Takes Too Long

- Reduce `IRT_CALIB_LOOKBACK_DAYS` (e.g., 14 instead of 30)
- Increase R IRT service resources (memory, CPU)
- Consider sampling observations (modify query LIMIT)

### Authentication Failed

```bash
# Verify secret exists
kubectl -n seedtest get secret seedtest-irt-credentials

# Check token value
kubectl -n seedtest get secret seedtest-irt-credentials -o jsonpath='{.data.R_IRT_INTERNAL_TOKEN}' | base64 -d
```

## Related

- **R IRT Client**: `/apps/seedtest_api/app/clients/r_irt.py`
- **CronJob**: `/portal_front/ops/k8s/cron/mirt-calibrate.yaml`
- **Tests**: `/apps/seedtest_api/tests/test_mirt_calibrate_job.py`
- **Deployment Guide**: `/portal_front/ops/k8s/cron/DEPLOYMENT_GUIDE.md`
