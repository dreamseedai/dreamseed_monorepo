# IRT Bayesian Drift Monitoring - Operations Guide

## Overview

The IRT drift monitoring system detects parameter changes in item bank using Bayesian re-estimation with anchor-based equating. This guide covers deployment, configuration, monitoring, and troubleshooting.

---

## Quick Start

### 1. Database Setup

Run the migration:

```bash
cd apps/seedtest_api
alembic upgrade head
```

This creates:
- `items` (item bank with anchor flags)
- `drift_windows` (time-period definitions)
- `item_calibration` (windowed estimation results)
- `drift_alerts` (automated alerts)

### 2. Initial Configuration

Set environment variables:

```bash
export DATABASE_URL="postgresql://user:pass@localhost/seedtest"
export PYMC_BACKEND="pymc"  # or "brms", "stan"
export DRIFT_MIN_SAMPLE=200
export DRIFT_THRESHOLD_DELTA_B=0.25
export DRIFT_THRESHOLD_DELTA_A=0.2
export DRIFT_THRESHOLD_DELTA_C=0.03
```

### 3. Populate Item Bank

Load initial item parameters and designate anchors:

```sql
INSERT INTO items (id, a, b, c, is_anchor, tags)
VALUES
  ('item_001', 1.2, 0.0, 0.2, TRUE, '{"topic": "algebra", "language": "ko"}'),
  ('item_002', 1.0, 0.5, 0.2, FALSE, '{"topic": "geometry", "language": "en"}'),
  ...;
```

**Anchor Selection Criteria:**
- High discrimination (a > 1.0)
- Central difficulty (-1.0 < b < 1.0)
- Stable performance history
- Representative of test blueprint
- Recommend: 20-30% of item pool

### 4. Run First Detection

```bash
python -m apps.seedtest_api.jobs.irt_drift \
  --recent-days 30 \
  --backend pymc \
  --dif-groups gender grade \
  --run-id drift_baseline_20251104
```

Expected output:
```
Run drift_baseline_20251104: 150 items, 12 alerts
```

### 5. Review Results

Check Shiny dashboard:
- Navigate to "IRT Drift Monitor" tab
- Select run ID
- Review alerts by severity
- Inspect anchor stability

---

## Configuration

### Prior Specifications

**Anchor Items (Strong Prior):**
```python
# apps/seedtest_api/jobs/irt_drift.py
DEFAULT_ANCHOR_PRIOR_SD = 0.05  # σ² = 0.0025
```
- Mean: Baseline parameter value
- SD: 0.05 → narrow prior (forces stability)

**Non-Anchor Items (Weak Prior):**
```python
DEFAULT_NON_ANCHOR_PRIOR_SD = 0.25  # σ² = 0.0625
```
- Mean: Baseline parameter value
- SD: 0.25 → wide prior (allows drift detection)

**Guessing Parameter (c):**
```python
# Beta prior: α = baseline_c * 10 + 1, β = (1 - baseline_c) * 10 + 1
# For c=0.2: Beta(3, 9) centered at 0.25
```

### Drift Thresholds

| Metric | Threshold | Severity | Action |
|--------|-----------|----------|--------|
| \|Δb\| | > 0.25 | Moderate | Adjust exposure weight |
| \|Δb\| | > 0.50 | Severe | Exclude from CAT |
| \|Δa\| | > 0.20 | Moderate | Monitor closely |
| \|Δa\| | > 0.40 | Severe | Recalibrate |
| Δc | > 0.03 | Moderate | Review item quality |
| 95% CI separation | Any | Severe | Immediate review |
| DIF BF | > 3.0 | Moderate | Group-specific review |

### Window Configuration

**Recent Window (default: 30 days):**
```python
recent_start = now - timedelta(days=30)
recent_end = now
```

**Baseline Window (quarterly update):**
```sql
-- Create baseline window (example: Q3 2025)
INSERT INTO drift_windows (start_at, end_at, population_tags)
VALUES ('2025-07-01', '2025-10-01', NULL);
```

**Recommendation:**
- Recent: 30 days (monthly), 7 days (weekly for high deployment)
- Baseline: Re-compute quarterly or after major content changes

### DIF Analysis Groups

Specify demographic groups for DIF analysis:

```bash
--dif-groups gender grade school language
```

Available columns (from response data):
- `gender`: M/F/Other
- `grade`: 7, 8, 9, 10, 11, 12
- `school`: School ID
- `language`: ko, en, zh

---

## Operational Procedures

### Monthly Drift Detection Workflow

**Schedule:** 1st of each month, 2 AM

1. **Run Detection Job:**
   ```bash
   python -m apps.seedtest_api.jobs.irt_drift \
     --recent-days 30 \
     --backend pymc \
     --run-id drift_$(date +%Y%m%d)
   ```

2. **Generate Report:**
   ```bash
   cd apps/reports
   quarto render irt_drift_report.qmd \
     --execute-params run_id=drift_$(date +%Y%m%d) \
     --output-dir /app/data/reports/drift
   ```

3. **Upload to S3:**
   ```bash
   aws s3 cp /app/data/reports/drift/irt_drift_report.pdf \
     s3://dreamseed-reports/irt-drift/$(date +%Y-%m)/
   ```

4. **Review Alerts:**
   - Open Shiny dashboard → IRT Drift Monitor
   - Filter: Severity = Severe
   - For each alert:
     - Review item parameters and CI
     - Check DIF results
     - Decide action (below)

5. **Take Action:**

   **Severe Drift (Δb > 0.5 or CI separation):**
   ```bash
   # Exclude from CAT immediately
   curl -X POST http://localhost:8000/api/v1/irt/alerts/resolve \
     -H "Content-Type: application/json" \
     -d '{"alert_ids": [123, 456], "action_taken": "Excluded from CAT; scheduled recalibration"}'
   ```
   
   **Moderate Drift (0.25 < Δb < 0.5):**
   - Adjust exposure weight to 0.5 (reduce selection)
   - Monitor for 2 weeks
   - If drift persists, recalibrate

   **Minor Drift (Δb < 0.25):**
   - Log for next review
   - No immediate action

6. **Export CAT Rules:**
   ```bash
   curl http://localhost:8000/api/v1/irt/exposure/rules?run_id=drift_20251104 \
     > /app/config/cat_exposure_rules.json
   ```

7. **Notify Stakeholders:**
   - Send report PDF to content team
   - Slack alert for severe items
   - Update item bank documentation

### Quarterly Baseline Update

**Schedule:** 1st of Jan/Apr/Jul/Oct, 1 AM

1. **Create New Baseline Window:**
   ```sql
   INSERT INTO drift_windows (start_at, end_at, population_tags)
   VALUES ('2025-10-01', '2026-01-01', NULL);
   ```

2. **Re-estimate All Items:**
   ```bash
   python -m apps.seedtest_api.jobs.irt_drift \
     --recent-days 90 \
     --baseline-window-id $(last_baseline_id) \
     --run-id baseline_Q4_2025
   ```

3. **Update Item Bank:**
   ```sql
   -- Copy recent estimates to baseline
   UPDATE items i
   SET a = c.a_hat,
       b = c.b_hat,
       c = c.c_hat,
       version = 'Q4_2025',
       effective_from = NOW()
   FROM item_calibration c
   WHERE c.item_id = i.id
     AND c.run_id = 'baseline_Q4_2025';
   ```

### Anchor Quality Check

**Schedule:** Bi-weekly (every 2nd Monday)

1. **Query Anchor Stability:**
   ```sql
   SELECT i.id, i.a, i.b, c.a_hat, c.b_hat,
          ABS(c.b_hat - i.b) AS delta_b
   FROM items i
   JOIN item_calibration c ON c.item_id = i.id
   WHERE i.is_anchor = TRUE
     AND c.run_id = (SELECT run_id FROM drift_alerts ORDER BY created_at DESC LIMIT 1)
   ORDER BY delta_b DESC;
   ```

2. **Review Top Unstable Anchors:**
   - If Δb > 0.15 for any anchor:
     - Investigate cause (content change? population shift?)
     - Consider replacing with stable candidate
     - Update anchor set

3. **Candidate Selection:**
   ```sql
   -- Find stable non-anchor items as replacement candidates
   SELECT c.item_id,
          AVG(ABS(c.b_hat - i.b)) AS mean_drift,
          COUNT(*) AS n_windows
   FROM item_calibration c
   JOIN items i ON i.id = c.item_id
   WHERE i.is_anchor = FALSE
     AND i.a > 1.0  -- High discrimination
     AND i.b BETWEEN -1.0 AND 1.0  -- Central difficulty
   GROUP BY c.item_id
   HAVING COUNT(*) >= 5
   ORDER BY mean_drift ASC
   LIMIT 10;
   ```

---

## CAT Integration

### Apply Drift-Based Exposure Weights

In `apps/seedtest_api/app_adaptive_demo.py`:

```python
from apps.seedtest_api.routers.irt_drift_api import load_drift_exposure_weights

# Load drift weights (cached)
drift_weights = load_drift_exposure_weights(run_id="drift_latest")

# Apply to CAT selector
item_next, info_next, _ = select_next_with_constraints(
    theta_new,
    DEMO_POOL,
    used_ids=used_ids,
    keymap=km,
    prefilter=pre,
    top_n=max(int(settings.CAT_TOP_N), 1),
    acceptance_probs=drift_weights,  # Override with drift-based weights
    ...
)
```

### Exclude Items Immediately

```python
# Get excluded items (severe drift)
excluded_ids = requests.get(
    "http://localhost:8000/api/v1/irt/exposure/excluded"
).json()

# Filter pool
DEMO_POOL = [item for item in DEMO_POOL if item["question_id"] not in excluded_ids]
```

---

## Monitoring & Alerts

### Health Checks

**Daily:**
- Cron job logs: `/var/log/irt_drift.log`
- Report generation status: `/var/log/drift_report.log`
- Database table sizes

**Weekly:**
- Shiny dashboard uptime
- S3 report uploads
- Alert resolution rate

### Key Metrics

| Metric | Target | Action if Exceeded |
|--------|--------|--------------------|
| Severe alerts | < 5 per month | Content review |
| Moderate alerts | < 20 per month | Monitor trends |
| Anchor drift (mean Δb) | < 0.10 | Anchor set review |
| Job runtime | < 2 hours | Optimize backend |
| Report generation time | < 5 minutes | Check Quarto setup |

### Slack Alerts

Configure webhook in cron job:

```bash
# After drift detection
python -m apps.seedtest_api.jobs.irt_drift --recent-days 30 && \
  python -m apps.seedtest_api.jobs.send_drift_slack_alert --run-id $LATEST_RUN
```

Example payload:
```json
{
  "text": "IRT Drift Alert",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Run:* drift_20251104\n*Severe:* 3\n*Moderate:* 12\n*Items Flagged:* item_123, item_456, item_789"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "View Dashboard"},
          "url": "https://admin.dreamseed.ai/shiny/irt-drift"
        }
      ]
    }
  ]
}
```

---

## Troubleshooting

### Issue: PyMC Installation Fails

**Symptom:** ImportError: No module named 'pymc'

**Solution:**
```bash
pip install pymc arviz
# Or use conda:
conda install -c conda-forge pymc arviz
```

### Issue: Job Runs Too Long (> 4 hours)

**Causes:**
- Too many items (> 500)
- Complex DIF analysis
- Insufficient compute resources

**Solutions:**
1. Reduce item set:
   ```python
   # Filter by exposure or importance
   item_ids = load_high_priority_items()
   ```

2. Switch to Stan (faster):
   ```bash
   --backend stan
   ```

3. Increase workers (if using multiprocessing):
   ```python
   with Pool(processes=8) as pool:
       results = pool.map(estimate_item, item_list)
   ```

### Issue: Anchor Items Show Drift

**Symptom:** Mean anchor Δb > 0.15

**Diagnosis:**
1. Check response data quality:
   ```sql
   SELECT item_id, COUNT(*), AVG(correct::int)
   FROM attempts
   WHERE item_id IN (SELECT id FROM items WHERE is_anchor=TRUE)
   GROUP BY item_id;
   ```

2. Review population shifts:
   ```sql
   SELECT grade, COUNT(DISTINCT user_id)
   FROM attempts
   WHERE created_at >= NOW() - INTERVAL '30 days'
   GROUP BY grade;
   ```

**Actions:**
- If data quality issue: Fix upstream
- If population shift: Update baseline window
- If anchor truly drifted: Replace anchor

### Issue: DIF Analysis Fails

**Symptom:** dif jsonb column is NULL

**Causes:**
- Missing demographic columns in response data
- Insufficient sample size per group
- compute_dif() not implemented fully

**Solutions:**
1. Verify demographic columns exist:
   ```sql
   SELECT * FROM attempts LIMIT 1;
   ```

2. Check sample sizes:
   ```sql
   SELECT gender, COUNT(*) FROM attempts WHERE item_id = 'item_123' GROUP BY gender;
   ```

3. Implement DIF analysis or disable:
   ```bash
   # Run without DIF
   python -m apps.seedtest_api.jobs.irt_drift --recent-days 30  # omit --dif-groups
   ```

---

## Performance Optimization

### Backend Selection

| Backend | Speed | Accuracy | Use Case |
|---------|-------|----------|----------|
| PyMC | Moderate | High | Production (default) |
| Stan | Fast | High | Large item banks (> 300 items) |
| brms | Slow | High | R-native workflows |

### Caching

Cache baseline calibrations:

```python
# In irt_drift.py
@lru_cache(maxsize=1)
def load_baseline_calibrations(baseline_window_id):
    # Query DB once, cache result
    ...
```

### Database Indexes

Ensure indexes exist:

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_item_calibration_run_item
ON item_calibration(run_id, item_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_drift_alerts_unresolved
ON drift_alerts(severity, resolved_at) WHERE resolved_at IS NULL;
```

---

## Rollback Procedures

### Revert to Previous Baseline

If recent calibration is faulty:

```sql
-- Restore previous baseline
UPDATE items i
SET a = prev.a,
    b = prev.b,
    c = prev.c,
    version = prev.version,
    effective_from = NOW()
FROM items_backup_Q3_2025 prev
WHERE prev.id = i.id;
```

### Disable Drift-Based Exposure

Temporarily disable CAT integration:

```python
# In app_adaptive_demo.py
# Comment out drift weights
# drift_weights = load_drift_exposure_weights(run_id="drift_latest")
drift_weights = None  # Use default
```

---

## Contact & Support

- **Analytics Team:** analytics@dreamseed.ai
- **Slack:** #irt-drift-monitoring
- **Dashboard:** https://admin.dreamseed.ai/shiny/irt-drift
- **Documentation:** https://docs.dreamseed.ai/irt-drift

---

**Last Updated:** 2025-11-04  
**Version:** 1.0.0
