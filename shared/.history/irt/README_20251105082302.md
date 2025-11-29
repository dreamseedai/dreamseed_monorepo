# IRT Drift Monitoring System

Complete Item Response Theory (IRT) calibration and drift detection pipeline with PostgreSQL backend, Python/R analytics, FastAPI endpoints, and React dashboard.

## 📋 Overview

This system provides:
- **Multi-language item bank** (en/ko/zh-Hans/zh-Hant) with rich content support (TipTap + MathLive)
- **IRT parameter estimation** (1PL/2PL/3PL models using R mirt/ltm packages)
- **Automated drift detection** across calibration windows
- **Differential Item Functioning (DIF)** analysis
- **Monthly calibration pipeline** with CronJob automation
- **REST API** for parameter management and alert handling
- **React dashboard** for visualization and monitoring

---

## 🗂️ File Structure

```
shared/irt/
├── schema.sql              # PostgreSQL schema definition
├── etl_irt_responses.py    # Extract responses from DB, create calibration windows
├── calibrate_irt.R         # R script for IRT estimation (mirt/ltm)
├── calibrate_irt.py        # Python wrapper for R calibration + result storage
└── report_drift.py         # Generate HTML/PDF drift reports

apps/seedtest_api/
├── alembic/versions/
│   └── 20251105_0813_irt_drift.py  # Alembic migration
└── app/routers/
    └── irt.py              # FastAPI endpoints

portal_front/src/pages/
└── IrtDriftDashboard.tsx   # React monitoring dashboard

ops/k8s/jobs/
└── irt-calibration-monthly.yaml  # CronJob for monthly calibration
```

---

## 🚀 Quick Start

### 1. Database Setup

```bash
# Apply Alembic migration
cd apps/seedtest_api
alembic upgrade head

# Or apply SQL directly
psql $DATABASE_URL -f shared/irt/schema.sql
```

### 2. Seed Sample Data (Optional)

```sql
-- Insert sample items
INSERT INTO shared_irt.items (id_str, bank_id, lang, stem_rich, answer_key, topic_tags)
VALUES 
  ('MATH_001', 'math-algebra', 'en', '{"content": "Solve x+2=5"}', '{"correct": 3}', ARRAY['algebra']),
  ('MATH_002', 'math-algebra', 'en', '{"content": "Solve 2x=10"}', '{"correct": 5}', ARRAY['algebra']);

-- Insert sample responses
INSERT INTO shared_irt.item_responses (org_id, user_id_hash, item_id, is_correct, lang)
SELECT 
  'org-demo',
  md5(random()::text),
  (SELECT id FROM shared_irt.items ORDER BY random() LIMIT 1),
  random() > 0.3,
  'en'
FROM generate_series(1, 1000);
```

### 3. Run ETL + Calibration

```bash
# Step 1: ETL - Extract responses for a window
python -m shared.irt.etl_irt_responses \
  --database-url $DATABASE_URL \
  --window-label "2025-11 monthly" \
  --start-date 2025-11-01 \
  --end-date 2025-11-30 \
  --population-tags "lang:en" \
  --output /tmp/irt_responses.csv

# Step 2: Calibrate - Run IRT estimation
python -m shared.irt.calibrate_irt \
  --database-url $DATABASE_URL \
  --window-id 1 \
  --model 2PL

# Step 3: Generate drift report
python -m shared.irt.report_drift \
  --database-url $DATABASE_URL \
  --window-id 1 \
  --output /tmp/drift_report_2025_11.pdf
```

---

## 📊 API Endpoints

Base URL: `/api/v1/irt`

### Items & Parameters

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/items` | GET | List items with current IRT parameters |
| `/items/{item_id}/history` | GET | Calibration history for item (parameter trends) |

**Query Parameters:**
- `bank_id`: Filter by item bank
- `lang`: Filter by language (en/ko/zh-Hans/zh-Hant)
- `is_anchor`: Filter anchor items
- `limit`, `offset`: Pagination

**Example Response:**
```json
{
  "id": 123,
  "id_str": "MATH_001",
  "bank_id": "math-algebra",
  "lang": "en",
  "model": "2PL",
  "a": 1.234,
  "b": -0.456,
  "c": null,
  "param_version": 3,
  "effective_from": "2025-11-01T02:00:00Z"
}
```

### Windows

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/windows` | GET | List calibration windows |
| `/windows` | POST | Create new window |
| `/calibrations/{window_id}` | GET | Get calibration results for window |

**Create Window:**
```bash
curl -X POST /api/v1/irt/windows \
  -H "Content-Type: application/json" \
  -d '{
    "label": "2025-11 monthly",
    "start_at": "2025-11-01T00:00:00Z",
    "end_at": "2025-11-30T23:59:59Z",
    "population_tags": ["lang:en", "cohort:2025-Q4"]
  }'
```

### Drift Alerts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/drift-alerts` | GET | List drift alerts |
| `/drift-alerts/{alert_id}` | PATCH | Resolve/unresolve alert |

**Query Parameters:**
- `active_only`: Show only unresolved alerts (default: true)
- `severity`: Filter by severity (low/medium/high)
- `window_id`: Filter by window

**Resolve Alert:**
```bash
curl -X PATCH /api/v1/irt/drift-alerts/42 \
  -H "Content-Type: application/json" \
  -d '{"resolved": true}'
```

### Statistics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stats/summary` | GET | System-wide statistics |

**Example Response:**
```json
{
  "total_items": 5432,
  "items_with_params": 5120,
  "anchor_items": 150,
  "total_windows": 12,
  "active_alerts": {
    "high": 3,
    "medium": 12,
    "low": 25,
    "total": 40
  }
}
```

---

## 🤖 Automated Calibration

### Monthly CronJob

The system includes a Kubernetes CronJob that runs monthly calibration automatically.

**Schedule:** 2 AM UTC on the 1st of every month

```bash
# View CronJob status
kubectl -n seedtest get cronjobs

# View job history
kubectl -n seedtest get jobs -l app=irt-calibration

# View logs
kubectl -n seedtest logs -l app=irt-calibration --tail=100
```

### Manual Calibration

```bash
# Customize the manual job template
cat ops/k8s/jobs/irt-calibration-monthly.yaml | \
  sed 's/WINDOW_LABEL:-[^}]*/WINDOW_LABEL:-2025-11 manual/' | \
  kubectl create -f -

# Monitor progress
kubectl -n seedtest logs -f job/irt-calibration-manual-$(date +%Y%m%d)
```

---

## 📈 React Dashboard

### Setup

1. **Add route:**

```tsx
// portal_front/src/App.tsx
import { IrtDriftDashboard } from '@/pages/IrtDriftDashboard';

// In routes:
<Route path="/admin/irt-drift" element={<IrtDriftDashboard />} />
```

2. **Install dependencies** (if not already present):

```bash
cd portal_front
npm install recharts lucide-react
```

3. **Access:** Navigate to `/admin/irt-drift`

### Features

- **Overview Tab:** System health, alert summary, key metrics
- **Alerts Tab:** All active drift alerts with severity badges, resolve actions
- **Trends Tab:** Parameter stability charts for selected items

---

## 🔧 Configuration

### Environment Variables

```bash
# ETL Settings
IRT_ETL_MIN_RESPONSES_PER_ITEM=30       # Minimum responses for calibration
IRT_ETL_MIN_VARIANCE=0.05               # Minimum response variance

# R Script Settings
IRT_DRIFT_THRESHOLD_B=0.3               # Difficulty drift threshold (Δb)
IRT_DRIFT_THRESHOLD_A=0.5               # Discrimination drift threshold (Δa)
```

### Drift Detection Thresholds

Adjust in `shared/irt/calibrate_irt.R`:

```r
--drift-threshold-b 0.3  # Flag if |Δb| > 0.3
--drift-threshold-a 0.5  # Flag if |Δa| > 0.5
```

### Alert Severity Rules

In `shared/irt/calibrate_irt.py`:

```python
# Determine severity
abs_drift = abs(drift_value)
if abs_drift > 0.5:
    severity = 'high'
elif abs_drift > 0.3:
    severity = 'medium'
else:
    severity = 'low'
```

---

## 📦 Dependencies

### Python

```txt
asyncpg
click
pydantic
jinja2
```

### R

```r
install.packages(c("mirt", "ltm", "jsonlite", "dplyr", "tidyr", "optparse"))
```

### Optional (PDF Reports)

```bash
# For PDF generation from HTML
sudo apt-get install wkhtmltopdf

# Or use weasyprint
pip install weasyprint
```

---

## 🔍 Troubleshooting

### Issue: "No responses found for window"

**Cause:** Date range or population filters too restrictive

**Solution:**
```sql
-- Check available responses
SELECT COUNT(*), MIN(answered_at), MAX(answered_at)
FROM shared_irt.item_responses;

-- Verify window dates
SELECT * FROM shared_irt.windows WHERE label = '2025-11 monthly';
```

### Issue: "Insufficient items for calibration"

**Cause:** Items don't meet minimum response threshold

**Solution:**
```bash
# Lower threshold
python -m shared.irt.etl_irt_responses \
  --min-responses 20 \
  --min-variance 0.03 \
  ...
```

### Issue: R script fails with "package not found"

**Solution:**
```r
# Install missing packages
install.packages(c("mirt", "ltm"))
```

### Issue: CronJob not running

**Check:**
```bash
# Verify CronJob exists
kubectl -n seedtest get cronjobs irt-calibration-monthly

# Check schedule syntax
kubectl -n seedtest describe cronjob irt-calibration-monthly

# Manually trigger
kubectl -n seedtest create job --from=cronjob/irt-calibration-monthly irt-test-$(date +%s)
```

---

## 📚 Additional Resources

- **IRT Theory:** [van der Linden & Hambleton (1997)](https://www.springer.com/gp/book/9780387946306)
- **mirt Package:** https://CRAN.R-project.org/package=mirt
- **Drift Detection:** [Glas & Jehangir (2014)](https://www.tandfonline.com/doi/abs/10.1080/15366367.2014.968145)
- **DIF Analysis:** [Chalmers et al. (2016)](https://www.jstatsoft.org/article/view/v048i06)

---

## 📝 License

Internal use only. DreamSeed AI © 2025
