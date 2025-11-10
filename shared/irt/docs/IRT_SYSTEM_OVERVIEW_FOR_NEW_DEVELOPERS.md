# IRT System Overview for New Developers

## Welcome! 👋

This guide will help you understand the **IRT (Item Response Theory) Drift Monitoring System** in the DreamSeed platform. Whether you're new to IRT or just joining the team, this document will get you up to speed.

---

## Table of Contents

1. [What is IRT?](#what-is-irt)
2. [System Architecture](#system-architecture)
3. [Key Concepts](#key-concepts)
4. [Directory Structure](#directory-structure)
5. [Getting Started](#getting-started)
6. [Common Workflows](#common-workflows)
7. [API Usage](#api-usage)
8. [Troubleshooting](#troubleshooting)
9. [Further Reading](#further-reading)

---

## What is IRT?

**Item Response Theory (IRT)** is a statistical framework for analyzing test items and test-taker abilities. Unlike classical test theory, IRT models the probability of a correct response based on:

- **θ (theta)**: Test-taker ability
- **a (discrimination)**: How well the item differentiates between high/low ability
- **b (difficulty)**: The ability level where 50% probability of correct response
- **c (guessing)**: Probability of guessing correctly (for multiple choice)

### Why IRT?

✅ **Item-level analysis**: Understand each question's performance  
✅ **Ability estimation**: Measure student ability independently of test form  
✅ **Adaptive testing (CAT)**: Select optimal items based on current ability estimate  
✅ **Equating**: Compare scores across different test forms  
✅ **Drift detection**: Monitor if items become easier/harder over time

### IRT Models

| Model | Parameters | Formula | Use Case |
|-------|-----------|---------|----------|
| **1PL (Rasch)** | b only (a=1, c=0) | P(θ) = 1 / (1 + e^(-(θ-b))) | Simple, assumes equal discrimination |
| **2PL** | a, b (c=0) | P(θ) = 1 / (1 + e^(-a(θ-b))) | Standard model, variable discrimination |
| **3PL** | a, b, c | P(θ) = c + (1-c) / (1 + e^(-a(θ-b))) | Multiple choice with guessing |

**Our system uses 2PL as default** for most items, with 3PL for multiple-choice questions with significant guessing.

---

## System Architecture

### High-Level Flow

```
┌─────────────────┐
│  Test Sessions  │
│   (students)    │
└────────┬────────┘
         │ responses
         ▼
┌─────────────────────────────────┐
│   shared_irt.item_responses     │ ◄── Raw response data
└────────┬────────────────────────┘
         │
         │ ETL (monthly)
         ▼
┌─────────────────────────────────┐
│   shared_irt.windows            │ ◄── Time periods
│   (e.g., 2025-Q1, 2025-Q2)      │
└────────┬────────────────────────┘
         │
         │ Calibration Jobs
         │ (mirt / brms / PyMC)
         ▼
┌─────────────────────────────────┐
│   shared_irt.item_calibration   │ ◄── Parameter estimates
│   (a_hat, b_hat, c_hat + CIs)   │
└────────┬────────────────────────┘
         │
         │ Drift Detection
         ▼
┌─────────────────────────────────┐
│   shared_irt.drift_alerts       │ ◄── Automated alerts
│   (delta_b > 0.5, DIF, etc.)    │
└────────┬────────────────────────┘
         │
         │ Reporting
         ▼
┌─────────────────────────────────┐
│   Monthly PDF Reports           │ ◄── Stakeholder review
│   + Dashboard (React)           │
└─────────────────────────────────┘
```

### Components

1. **Database Schema** (`shared_irt`)
   - 6 tables for items, parameters, windows, calibrations, alerts, responses
   - PostgreSQL with JSONB for flexible metadata

2. **Calibration Engine** (Python/R)
   - `mirt` (Python): Fast baseline calibration
   - `brms` (R/Stan): Bayesian calibration with MCMC
   - `PyMC` (Python): Bayesian calibration with NUTS

3. **API Layer** (FastAPI)
   - 12 REST endpoints for drift monitoring, statistics, reports
   - JWT authentication
   - OpenAPI docs at `/docs`

4. **Frontend** (React)
   - `MonthlyDriftReport` component (shared across projects)
   - Interactive charts with SVG rendering
   - PDF download integration

5. **Automation**
   - **K8s CronJobs**: Monthly calibration in cloud
   - **SystemD timers**: Monthly calibration on-premise
   - **Alembic migrations**: Database schema versioning

---

## Key Concepts

### 1. Calibration Windows

**Windows** are time periods for grouping responses:

```sql
-- Example: Q1 2025
INSERT INTO shared_irt.windows (label, start_at, end_at) VALUES
('2025-Q1', '2025-01-01', '2025-04-01');
```

**Why windows?**
- Compare parameter stability over time (drift detection)
- Ensure sufficient sample size per item (≥30 responses)
- Track seasonal effects (e.g., summer vs. school year)

### 2. Parameter Drift

**Drift** occurs when item parameters change between windows:

| Metric | Formula | Threshold | Meaning |
|--------|---------|-----------|---------|
| Δb | \|b_current - b_previous\| | >0.25 (medium), >0.5 (high) | Difficulty changed |
| Δa | \|a_current - a_previous\| | >0.2 (medium), >0.4 (high) | Discrimination changed |
| Δc | c_current - c_previous | >0.03 | Guessing increased |

**Causes of drift:**
- Item exposure (students share answers)
- Translation errors (for multi-language tests)
- Curriculum changes
- Population shifts

### 3. DIF (Differential Item Functioning)

**DIF** means an item performs differently for subgroups with the same ability:

```python
# Example: Language DIF
# English speakers: b = 0.0
# Korean speakers: b = 0.4  ← Item harder for Korean speakers
# Δb = 0.4 → DIF detected!
```

**DIF Detection:**
- **Bayesian approach**: P(|Δb| > 0.3) > 0.9 → alert
- **Bayes Factor**: BF₁₀ > 10 → strong evidence

**Common DIF grouping variables:**
- Language (en, ko, zh-Hans, zh-Hant)
- Country
- Subscription tier
- Age/grade level

### 4. Information Functions

**Information I(θ)** measures how much the item tells us about ability at level θ:

```
For 2PL: I(θ) = a² × P(θ) × [1 - P(θ)]
```

**Test Information** = sum of item information curves:

```
Test_Info(θ) = Σ Item_Info_i(θ)
```

**SEM (Standard Error of Measurement)**:

```
SEM(θ) = 1 / √Test_Info(θ)
```

**Why monitor information?**
- Detect if test became less reliable in certain θ ranges
- Optimize CAT item selection (maximize information at current θ estimate)

---

## Directory Structure

```
dreamseed_monorepo/
├── shared/
│   └── irt/                          ← Core IRT system
│       ├── __init__.py
│       ├── README.md                 ← System overview
│       ├── models.py                 ← Pydantic models (30+ classes)
│       ├── service.py                ← Business logic (info curves, CAT)
│       ├── calibrate_irt.py          ← mirt calibration (CLI)
│       ├── calibrate_monthly_pymc.py ← PyMC Bayesian calibration
│       ├── calibrate_monthly_brms.R  ← brms Bayesian calibration
│       ├── etl_mpc_legacy_to_pg.py   ← Legacy data migration
│       ├── docs/
│       │   ├── MIGRATION_20251105_SHARED_IRT.md ← DB schema docs
│       │   ├── THRESHOLDS_AND_DIF.md            ← Drift thresholds
│       │   ├── IRT_SYSTEM_OVERVIEW.md           ← This file!
│       │   └── ...
│       └── reports/
│           ├── drift_monthly.py      ← Report generator (CLI)
│           ├── templates/
│           │   └── drift_monthly.html ← Jinja2 template
│           └── __init__.py
├── apps/
│   └── seedtest_api/
│       ├── alembic/
│       │   └── versions/
│       │       └── 20251105_1400_shared_irt_init.py ← DB migration
│       └── app/
│           ├── main.py               ← FastAPI app (router registration)
│           └── routers/
│               └── analytics_irt.py  ← 12 REST endpoints
├── infra/
│   ├── k8s/
│   │   └── jobs/
│   │       ├── irt-calibration-monthly.yaml  ← mirt CronJob
│   │       ├── irt-calibration-brms-monthly.yaml ← brms CronJob
│   │       └── irt-calibration-pymc-monthly.yaml ← PyMC CronJob
│   └── systemd/
│       ├── irt-calibration.service.example   ← SystemD services
│       ├── irt-calibration.timer
│       └── README.md
└── portal_front/
    └── src/
        └── pages/
            └── admin/
                └── IrtDriftPage.tsx  ← React dashboard
```

---

## Getting Started

### Prerequisites

```bash
# Python 3.10+
python --version

# PostgreSQL 12+
psql --version

# R 4.0+ (for brms)
R --version

# Node.js 18+ (for frontend)
node --version
```

### 1. Database Setup

```bash
# Run migration
cd apps/seedtest_api
export DATABASE_URL="postgresql://user:pass@localhost:5432/dreamseed"
alembic upgrade head

# Verify
psql $DATABASE_URL -c "\dt shared_irt.*"
```

### 2. Install Python Dependencies

```bash
# Core IRT packages
pip install numpy scipy pandas sqlalchemy pydantic

# Calibration engines
pip install mirt pymc arviz

# Reports
pip install jinja2 weasyprint click

# API
pip install fastapi uvicorn python-jose[cryptography]
```

### 3. Install R Dependencies (optional)

```R
install.packages(c("brms", "RPostgres", "dplyr", "jsonlite"))
```

### 4. Seed Initial Data

```sql
-- Create first calibration window
INSERT INTO shared_irt.windows (label, start_at, end_at) VALUES
('2025-11-baseline', '2025-11-01', '2025-12-01');

-- Add test items (example)
INSERT INTO shared_irt.items (id_str, bank_id, lang, is_anchor) VALUES
('MATH-001', 'SAT_MATH', 'en', false),
('MATH-002', 'SAT_MATH', 'en', true);  -- anchor item
```

### 5. Run Test Calibration

```bash
# Dry run (no database writes)
python -m shared.irt.calibrate_irt \
  --database-url $DATABASE_URL \
  --window-id 1 \
  --model 2PL \
  --dry-run

# Live calibration
python -m shared.irt.calibrate_irt \
  --database-url $DATABASE_URL \
  --window-id 1 \
  --model 2PL
```

### 6. Start API Server

```bash
cd apps/seedtest_api
uvicorn app.main:app --reload --port 8000

# Test endpoint
curl http://localhost:8000/api/analytics/irt/health
```

### 7. Generate First Report

```bash
python -m shared.irt.reports.drift_monthly \
  --window-id 1 \
  --output /tmp/first_report.pdf

# Open PDF
open /tmp/first_report.pdf
```

---

## Common Workflows

### Workflow 1: Monthly Calibration

**Goal**: Update item parameters based on last month's responses.

**Steps:**

1. **Create window**
   ```sql
   INSERT INTO shared_irt.windows (label, start_at, end_at) VALUES
   ('2025-11', '2025-11-01', '2025-12-01');
   ```

2. **Run calibration**
   ```bash
   python -m shared.irt.calibrate_monthly_pymc \
     --database-url $DATABASE_URL \
     --samples 1000 --tune 500 --chains 4
   ```

3. **Check for alerts**
   ```sql
   SELECT * FROM shared_irt.drift_alerts 
   WHERE window_id = (SELECT MAX(id) FROM shared_irt.windows)
     AND severity = 'high'
     AND resolved_at IS NULL;
   ```

4. **Review high-severity items**
   - Check `drift_alerts` table for Δb > 0.5
   - Investigate item content, translation
   - Consult with subject matter experts

5. **Update operational parameters** (if approved)
   ```sql
   UPDATE shared_irt.item_parameters_current
   SET a = 1.25, b = 0.55, version = version + 1, 
       effective_from = now(), note = 'Updated from 2025-11 calibration'
   WHERE item_id = 1234;
   ```

6. **Generate report**
   ```bash
   python -m shared.irt.reports.drift_monthly \
     --window-id $(psql $DATABASE_URL -t -c "SELECT MAX(id) FROM shared_irt.windows") \
     --output /tmp/monthly_report_$(date +%Y%m).pdf
   ```

---

### Workflow 2: DIF Analysis

**Goal**: Detect if items are biased against certain groups.

**Steps:**

1. **Identify grouping variable** (e.g., language)

2. **Run 2-group calibration** (in Python script)
   ```python
   # Calibrate for English speakers
   params_en = calibrate_2pl(responses_en, theta_en)
   
   # Calibrate for Korean speakers
   params_ko = calibrate_2pl(responses_ko, theta_ko)
   
   # Compute difference
   delta_b = params_ko['b'] - params_en['b']
   ```

3. **Bayesian DIF detection** (brms or PyMC)
   ```python
   # Posterior probability
   P_dif = np.mean(np.abs(posterior_samples['delta_b']) > 0.3)
   
   if P_dif > 0.9:
       # Insert alert
       insert_drift_alert(item_id, window_id, 'dif_prob', P_dif, 0.9, 'high', ...)
   ```

4. **Store results**
   ```sql
   UPDATE shared_irt.item_calibration
   SET dif_metadata = '{"language": {"ref": "en", "focal": "ko", "delta_b": 0.42, "prob": 0.93}}'::jsonb
   WHERE item_id = 1234 AND window_id = 1;
   ```

5. **Review flagged items**
   - Compare translations
   - Check for cultural bias
   - Consult with test development team

---

### Workflow 3: CAT Item Selection

**Goal**: Select optimal next item for adaptive test.

**Steps:**

1. **Estimate current ability** (after N items)
   ```python
   from shared.irt.service import estimate_theta_eap
   
   theta_current = estimate_theta_eap(
       responses=[1, 0, 1, 1, 0],  # correct/incorrect
       item_params=[(1.2, 0.5), (0.9, -0.2), ...]
   )
   # θ ≈ 0.35
   ```

2. **Get remaining item pool**
   ```sql
   SELECT id, a, b FROM shared_irt.item_parameters_current
   WHERE item_id NOT IN (1, 5, 12, 18, 23)  -- already administered
     AND exposure_count < 1000;  -- exposure control
   ```

3. **Select max information item**
   ```python
   from shared.irt.service import select_next_item_mfi
   
   next_item = select_next_item_mfi(
       remaining_items=[(1.3, 0.4), (0.8, 0.3), ...],
       theta_current=0.35
   )
   # Returns item with max I(θ=0.35)
   ```

4. **Update exposure count**
   ```sql
   UPDATE shared_irt.items
   SET exposure_count = exposure_count + 1
   WHERE id = <next_item_id>;
   ```

5. **Administer item** and repeat

---

## API Usage

### Authentication

```bash
# Get JWT token (example)
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"***"}' \
  | jq -r '.access_token')
```

### Common Endpoints

#### 1. Get Drift Summary

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analytics/irt/drift/summary?limit=5
```

**Response:**
```json
{
  "windows": [
    {
      "window_id": 2,
      "label": "2025-Q2",
      "start_at": "2025-04-01T00:00:00Z",
      "end_at": "2025-07-01T00:00:00Z",
      "n_items": 523,
      "n_alerts": 12,
      "alerts_by_metric": {
        "delta_b": 8,
        "delta_a": 3,
        "dif_prob": 1
      }
    }
  ]
}
```

#### 2. Get Alerts for Window

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/analytics/irt/drift/alerts/2?severity=high"
```

**Response:**
```json
{
  "alerts": [
    {
      "id": 45,
      "item_id": 1234,
      "window_id": 2,
      "metric": "delta_b",
      "value": 0.55,
      "threshold": 0.5,
      "severity": "high",
      "message": "Difficulty parameter drift: |Δb| = 0.550 exceeds 0.5",
      "created_at": "2025-11-05T10:30:00Z",
      "resolved_at": null
    }
  ]
}
```

#### 3. Get Item Info Curves

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/analytics/irt/info/curves/items \
  -d '{"item_ids": [1234, 1235], "theta_min": -3, "theta_max": 3, "steps": 61}'
```

**Response:**
```json
{
  "curves": [
    {
      "item_id": 1234,
      "model": "2PL",
      "points": [
        {"theta": -3.0, "info": 0.02},
        {"theta": -2.9, "info": 0.03},
        ...
        {"theta": 0.5, "info": 0.36},  // max_info
        ...
      ],
      "max_info": 0.36,
      "max_info_theta": 0.5
    }
  ]
}
```

#### 4. Download Monthly Report

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/analytics/irt/report/monthly?window_id=2" \
  -o report.pdf

# Or get file path only
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/analytics/irt/report/monthly?window_id=2&download=false"
```

**Response (download=false):**
```json
{
  "success": true,
  "file_path": "/tmp/irt_reports/drift_window_2_20251105_143025.pdf",
  "file_size_bytes": 524288,
  "file_size_kb": 512.0
}
```

### Full API Reference

See: `http://localhost:8000/docs` (OpenAPI/Swagger UI)

---

## Troubleshooting

### Issue 1: Calibration Fails with "Insufficient Data"

**Error:**
```
ValueError: Item 1234 has only 15 responses in window 2 (minimum 30 required)
```

**Solution:**
- Increase window duration (e.g., monthly → quarterly)
- Filter items with `n_responses >= 30` before calibration
- Use larger population (remove population_tags filters)

---

### Issue 2: MCMC Not Converging (brms/PyMC)

**Error:**
```
Warning: R-hat > 1.01 for parameter b[12]
Warning: 234 divergences detected
```

**Solution:**
```python
# Increase samples and tuning
python -m shared.irt.calibrate_monthly_pymc \
  --samples 2000 \        # was 1000
  --tune 1000 \           # was 500
  --chains 4
```

Or use informative priors:
```python
# In PyMC model
a ~ Normal(1.0, 0.5)  # instead of flat prior
b ~ Normal(0.0, 2.0)
```

---

### Issue 3: Reports Missing WeasyPrint

**Error:**
```
ImportError: WeasyPrint is not installed. Cannot generate PDF reports.
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
pip install weasyprint

# macOS
brew install pango
pip install weasyprint

# Generate HTML instead
python -m shared.irt.reports.drift_monthly \
  --window-id 1 --output report.html --format html
```

---

### Issue 4: API Returns 401 Unauthorized

**Error:**
```json
{"detail": "Not authenticated"}
```

**Solution:**
- Verify JWT token is valid: `jwt.io`
- Check token expiration
- Include `Authorization: Bearer <token>` header
- Verify user has `irt_admin` or `irt_readonly` role

---

### Issue 5: Slow Queries on item_responses

**Symptom:** Calibration takes >10 minutes

**Solution:**
```sql
-- Check if indexes exist
\d shared_irt.item_responses

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_item_responses_window 
ON shared_irt.item_responses(item_id, answered_at);

-- Analyze table
ANALYZE shared_irt.item_responses;

-- Consider partitioning (see MIGRATION_20251105_SHARED_IRT.md)
```

---

## Further Reading

### Internal Documentation

1. **[MIGRATION_20251105_SHARED_IRT.md](./MIGRATION_20251105_SHARED_IRT.md)** - Database schema (650 lines)
   - Table structures, indexes, constraints
   - Migration guide, rollback procedures
   - Performance tuning, backup strategies

2. **[THRESHOLDS_AND_DIF.md](./THRESHOLDS_AND_DIF.md)** - Drift detection thresholds
   - Parameter drift: |Δb| > 0.25, |Δa| > 0.2
   - DIF detection: P > 0.9, BF > 10
   - Information drop: >20% threshold

3. **[shared/irt/README.md](../README.md)** - IRT system overview
   - Architecture, components
   - Quick start guide
   - CLI usage examples

4. **[apps/seedtest_api/app/routers/analytics_irt.py](../../../apps/seedtest_api/app/routers/analytics_irt.py)** - API implementation
   - 12 REST endpoints
   - Query patterns, error handling
   - OpenAPI schema

5. **K8s Manifests** (`infra/k8s/jobs/`)
   - CronJob schedules, resource limits
   - Docker image references
   - Secrets management

### External Resources

#### IRT Theory
- **Lord, F. M. (1980)**. *Applications of Item Response Theory to Practical Testing Problems*. Lawrence Erlbaum Associates.
- **Embretson, S. E., & Reise, S. P. (2000)**. *Item Response Theory for Psychologists*. Psychology Press.
- **van der Linden, W. J., & Hambleton, R. K. (1997)**. *Handbook of Modern Item Response Theory*. Springer.

#### Bayesian IRT
- **Gelman, A., et al. (2013)**. *Bayesian Data Analysis* (3rd ed.). CRC Press.
- **brms documentation**: https://paul-buerkner.github.io/brms/
- **PyMC documentation**: https://www.pymc.io/

#### DIF Detection
- **Zwick, R. (2012)**. *A Review of ETS Differential Item Functioning Assessment Procedures*. ETS Research Report Series.
- **Raju, N. S., et al. (1995)**. DIF in polytomous items. *Applied Psychological Measurement*, 19(1), 3-22.

#### Standards
- **AERA/APA/NCME (2014)**. *Standards for Educational and Psychological Testing*. American Educational Research Association.

### Python/R Packages

- **mirt** (Python): Fast EM algorithm, large sample sizes
- **pymc**: Bayesian MCMC with NUTS sampler
- **brms** (R): Bayesian via Stan, rich formula syntax
- **numpy/scipy**: Numerical computing, optimization
- **pandas**: Data manipulation
- **sqlalchemy**: Database ORM

### Video Tutorials (External)

- **"Item Response Theory Basics"** - YouTube (search for academic lectures)
- **"Bayesian Data Analysis with PyMC"** - PyMC official channel
- **"brms Tutorial"** - Paul Bürkner's workshops

---

## Getting Help

### Internal Support

1. **Slack Channels**
   - `#data-science` - IRT theory, modeling questions
   - `#backend` - API, database questions
   - `#devops` - K8s, deployment issues

2. **Documentation Issues**
   - Open GitHub issue: `dreamseedai/dreamseed_monorepo`
   - Tag: `documentation`, `irt-system`

3. **Code Reviews**
   - All IRT changes require review from data science team
   - Tag reviewers: `@data-science-team`

### External Resources

- **IRT Mailing List**: https://lists.psu.edu/cgi-bin/wa?A0=RASCH
- **Stack Overflow**: Tag `item-response-theory`, `pymc`, `brms`
- **Cross Validated**: https://stats.stackexchange.com/ (for statistical questions)

---

## Quick Reference Card

### Key Commands

```bash
# Calibration
python -m shared.irt.calibrate_monthly_pymc --database-url $DATABASE_URL

# Report generation
python -m shared.irt.reports.drift_monthly --window-id 1 --output report.pdf

# API server
uvicorn app.main:app --reload --port 8000

# Database migration
alembic upgrade head

# Check alerts
psql $DATABASE_URL -c "SELECT * FROM shared_irt.drift_alerts WHERE severity='high'"
```

### Key Thresholds

| Metric | Medium | High |
|--------|--------|------|
| Δb | >0.25 | >0.5 |
| Δa | >0.2 | >0.4 |
| Δc | >0.03 | - |
| P(DIF) | - | >0.9 |
| BF | - | >10 |
| Info drop | >20% | - |

### Key Tables

- `shared_irt.items` - Item bank (id_str, bank_id, lang)
- `shared_irt.item_parameters_current` - Operational params (a, b, c)
- `shared_irt.windows` - Time periods (label, start_at, end_at)
- `shared_irt.item_calibration` - Historical params (a_hat, b_hat, CIs)
- `shared_irt.drift_alerts` - Alerts (metric, value, threshold, severity)
- `shared_irt.item_responses` - Raw data (item_id, is_correct, answered_at)

### Key Files

- `shared/irt/models.py` - Pydantic models (30+ classes)
- `shared/irt/service.py` - Business logic (10 functions)
- `apps/seedtest_api/app/routers/analytics_irt.py` - API (12 endpoints)
- `shared/irt/reports/drift_monthly.py` - Report generator

---

## Next Steps

Now that you understand the IRT system, here are some suggested learning paths:

### For Backend Engineers:
1. ✅ Read `MIGRATION_20251105_SHARED_IRT.md` - Understand database schema
2. ✅ Study `apps/seedtest_api/app/routers/analytics_irt.py` - Learn API patterns
3. ✅ Run test calibration with synthetic data
4. ✅ Implement new API endpoint (e.g., GET /items/{id}/drift-history)

### For Data Scientists:
1. ✅ Read `THRESHOLDS_AND_DIF.md` - Learn drift detection logic
2. ✅ Study `shared/irt/service.py` - Understand Fisher information calculations
3. ✅ Run PyMC calibration and inspect MCMC diagnostics
4. ✅ Experiment with different priors and compare results

### For Frontend Engineers:
1. ✅ Study `shared/frontend/irt/MonthlyDriftReport.tsx` - Component structure
2. ✅ Test API endpoints via Postman/Insomnia
3. ✅ Integrate component into new project (Univ/Parent/School)
4. ✅ Add new visualization (e.g., time series drift chart)

### For DevOps:
1. ✅ Review K8s manifests in `infra/k8s/jobs/`
2. ✅ Deploy CronJob to staging cluster
3. ✅ Set up monitoring (Prometheus + Grafana)
4. ✅ Configure alerts for job failures

---

## Conclusion

You now have a comprehensive understanding of the IRT Drift Monitoring System. Key takeaways:

✅ **IRT models** estimate ability (θ) and item parameters (a, b, c)  
✅ **Drift detection** monitors parameter stability over time windows  
✅ **DIF analysis** ensures fairness across demographic groups  
✅ **Information functions** optimize adaptive testing and measure reliability  
✅ **Full stack** from database → calibration → API → frontend  

**Remember:** IRT is powerful but complex. Don't hesitate to ask questions, consult documentation, and collaborate with the data science team. Welcome to the team! 🎉

---

## Document Metadata

- **Author**: AI Assistant
- **Date**: 2025-11-05
- **Version**: 1.0.0
- **Repository**: dreamseed_monorepo
- **Branch**: staging/attempt-view-lock-v1
- **Last Updated**: 2025-11-05
