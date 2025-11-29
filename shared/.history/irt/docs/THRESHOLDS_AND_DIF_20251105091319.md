# IRT Drift Detection Thresholds & DIF Guidelines

## Overview

This document defines thresholds for detecting item parameter drift and Differential Item Functioning (DIF) in the IRT calibration system.

## 1. Parameter Drift Thresholds

### 1.1 Basic Thresholds (Medium Alert)

Trigger alerts when parameter changes exceed:

| Parameter | Threshold | Interpretation |
|-----------|-----------|----------------|
| **b (difficulty)** | \|Δb\| > 0.25 | Shift of ~0.25 SD in difficulty |
| **a (discrimination)** | \|Δa\| > 0.2 | 20% change in discrimination |
| **c (guessing)** | Δc > 0.03 | 3 percentage points increase |

**Alert Severity: MEDIUM**

#### SQL Implementation
```sql
-- Detect parameter drift between consecutive windows
WITH drift_metrics AS (
  SELECT 
    curr.item_id,
    curr.window_id,
    ABS(curr.b_hat - prev.b_hat) AS delta_b,
    ABS(curr.a_hat - prev.a_hat) AS delta_a,
    (curr.c_hat - prev.c_hat) AS delta_c
  FROM shared_irt.item_calibration curr
  JOIN shared_irt.item_calibration prev 
    ON curr.item_id = prev.item_id 
    AND prev.window_id = (
      SELECT MAX(window_id) 
      FROM shared_irt.item_calibration 
      WHERE item_id = curr.item_id 
        AND window_id < curr.window_id
    )
  WHERE curr.converged = true AND prev.converged = true
)
INSERT INTO shared_irt.drift_alerts (item_id, window_id, metric, value, threshold, severity, message)
SELECT 
  item_id, 
  window_id,
  'delta_b' AS metric,
  delta_b AS value,
  0.25 AS threshold,
  'medium' AS severity,
  'Difficulty parameter drift: |Δb| = ' || ROUND(delta_b::numeric, 3) || ' exceeds 0.25'
FROM drift_metrics
WHERE delta_b > 0.25;
```

### 1.2 High-Risk Thresholds (High Alert)

Trigger high-priority alerts when changes are severe:

| Parameter | Threshold | Interpretation |
|-----------|-----------|----------------|
| **b (difficulty)** | \|Δb\| > 0.5 | Major difficulty shift (0.5 SD) |
| **a (discrimination)** | \|Δa\| > 0.4 | 40% change in discrimination |

**Alert Severity: HIGH**

#### Interpretation
- **|Δb| > 0.5**: Item became substantially easier or harder
  - Example: Item originally at θ=0 now discriminates best at θ=0.5
  - Action: Review item content for exposure, translation errors, curriculum changes
  
- **|Δa| > 0.4**: Item's ability to discriminate changed dramatically
  - Example: a=1.0 → a=1.4 or a=0.6
  - Action: Check for answer key errors, ambiguous wording, or guessing patterns

### 1.3 Guessing Parameter Increase

| Parameter | Threshold | Interpretation |
|-----------|-----------|----------------|
| **c (guessing)** | Δc > 0.03 | Guessing rate increased by 3+ percentage points |

**Alert Severity: MEDIUM**

#### Why Monitor c Increases?
- Increased guessing suggests:
  - Item became too difficult relative to test population
  - Answer choices became more obvious
  - Item exposure led to answer elimination strategies
  
#### SQL Implementation
```sql
-- Detect guessing parameter increase
INSERT INTO shared_irt.drift_alerts (item_id, window_id, metric, value, threshold, severity, message)
SELECT 
  curr.item_id,
  curr.window_id,
  'delta_c' AS metric,
  (curr.c_hat - prev.c_hat) AS value,
  0.03 AS threshold,
  'medium' AS severity,
  'Guessing parameter increased: Δc = +' || ROUND((curr.c_hat - prev.c_hat)::numeric, 3)
FROM shared_irt.item_calibration curr
JOIN shared_irt.item_calibration prev 
  ON curr.item_id = prev.item_id 
  AND prev.window_id = (
    SELECT MAX(window_id) 
    FROM shared_irt.item_calibration 
    WHERE item_id = curr.item_id 
      AND window_id < curr.window_id
  )
WHERE curr.c_hat - prev.c_hat > 0.03
  AND curr.converged = true 
  AND prev.converged = true;
```

## 2. Differential Item Functioning (DIF) Detection

### 2.1 DIF Definition

**DIF occurs when an item performs differently for subgroups with the same ability level.**

Common grouping variables:
- **Language**: en, ko, zh-Hans, zh-Hant
- **Country**: KR, US, CN, TW, etc.
- **Subscription tier**: free, premium, enterprise
- **Demographics**: Age group, education level

### 2.2 Two-Group DIF Analysis

For each item, calibrate separately in two groups (focal vs. reference):

#### Step 1: Separate Calibration
```python
# Calibrate item in Group A (reference)
item_params_A = calibrate_2pl(
    responses_A,  # Reference group responses
    theta_A       # Reference group abilities
)

# Calibrate item in Group B (focal)
item_params_B = calibrate_2pl(
    responses_B,  # Focal group responses
    theta_B       # Focal group abilities
)
```

#### Step 2: Compute Parameter Differences
```python
delta_b = item_params_B['b'] - item_params_A['b']
delta_a = item_params_B['a'] - item_params_A['a']
```

### 2.3 Bayesian DIF Detection

Use Bayesian calibration (brms or PyMC) to get posterior distributions:

#### Threshold 1: Posterior Probability
```python
# Probability that difficulty differs by more than 0.3
P_delta_b = np.mean(np.abs(posterior_samples['delta_b']) > 0.3)

if P_delta_b > 0.9:
    alert("DIF detected: P(|Δb| > 0.3) = {:.2f}".format(P_delta_b))
```

**Alert Criteria:**
- P(|Δb| > 0.3) > 0.9 → **HIGH severity DIF alert**
- P(|Δa| > 0.2) > 0.9 → **MEDIUM severity DIF alert**

#### Threshold 2: Bayes Factor
```python
# Bayes Factor: evidence for H1 (DIF exists) vs H0 (no DIF)
BF_10 = compute_bayes_factor(
    model_with_dif,    # Model with group effect
    model_without_dif  # Null model
)

if BF_10 > 10:
    alert("DIF detected: Bayes Factor = {:.1f} (strong evidence)".format(BF_10))
```

**Bayes Factor Interpretation:**
| BF₁₀ | Evidence |
|------|----------|
| 1-3 | Anecdotal |
| 3-10 | Moderate |
| 10-30 | Strong |
| 30-100 | Very strong |
| >100 | Extreme |

**Alert Criteria:**
- BF₁₀ > 10 → **HIGH severity DIF alert**

### 2.4 DIF SQL Schema

```sql
-- Store DIF analysis results
CREATE TABLE IF NOT EXISTS shared_irt.dif_analysis (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES shared_irt.items(id),
    window_id INTEGER NOT NULL REFERENCES shared_irt.windows(id),
    
    -- Grouping variable
    grouping_var VARCHAR(50) NOT NULL,  -- 'language', 'country', 'subscription_tier'
    reference_group VARCHAR(50) NOT NULL,  -- e.g., 'en'
    focal_group VARCHAR(50) NOT NULL,      -- e.g., 'ko'
    
    -- Parameter estimates for each group
    ref_b_hat FLOAT,
    ref_a_hat FLOAT,
    focal_b_hat FLOAT,
    focal_a_hat FLOAT,
    
    -- DIF metrics
    delta_b FLOAT,  -- focal_b - ref_b
    delta_a FLOAT,  -- focal_a - ref_a
    
    -- Bayesian evidence
    prob_delta_b_gt_03 FLOAT,  -- P(|Δb| > 0.3)
    bayes_factor FLOAT,        -- BF for H1:DIF vs H0:no DIF
    
    -- Sample sizes
    n_responses_ref INTEGER,
    n_responses_focal INTEGER,
    
    -- Alert flag
    dif_detected BOOLEAN,
    severity VARCHAR(10),  -- 'low', 'medium', 'high'
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dif_item_window ON shared_irt.dif_analysis(item_id, window_id);
CREATE INDEX idx_dif_detected ON shared_irt.dif_analysis(dif_detected) WHERE dif_detected = true;
```

### 2.5 DIF Alert Examples

```sql
-- Insert DIF alert based on posterior probability
INSERT INTO shared_irt.drift_alerts (item_id, window_id, metric, value, threshold, severity, message)
SELECT 
    item_id,
    window_id,
    'dif_prob' AS metric,
    prob_delta_b_gt_03 AS value,
    0.9 AS threshold,
    'high' AS severity,
    format(
        'DIF detected between %s (ref) and %s (focal): P(|Δb| > 0.3) = %.2f, Δb = %.3f',
        reference_group,
        focal_group,
        prob_delta_b_gt_03,
        delta_b
    ) AS message
FROM shared_irt.dif_analysis
WHERE prob_delta_b_gt_03 > 0.9
  AND dif_detected = true;

-- Insert DIF alert based on Bayes Factor
INSERT INTO shared_irt.drift_alerts (item_id, window_id, metric, value, threshold, severity, message)
SELECT 
    item_id,
    window_id,
    'dif_bf' AS metric,
    bayes_factor AS value,
    10.0 AS threshold,
    'high' AS severity,
    format(
        'Strong DIF evidence between %s and %s: BF₁₀ = %.1f (Δb = %.3f)',
        reference_group,
        focal_group,
        bayes_factor,
        delta_b
    ) AS message
FROM shared_irt.dif_analysis
WHERE bayes_factor > 10
  AND dif_detected = true;
```

## 3. Information Function Degradation

### 3.1 θ-Range Information Drop

Monitor test information across ability ranges to detect localized degradation.

#### Threshold
- **Information drop > 20%** in any θ interval compared to previous window
- **Alert Severity: LOW (INFO)**

#### SQL Implementation

```sql
-- Compare test information across θ ranges
WITH theta_intervals AS (
  SELECT 
    window_id,
    CASE 
      WHEN theta_value < -2 THEN 'very_low'
      WHEN theta_value < -1 THEN 'low'
      WHEN theta_value < 0 THEN 'below_avg'
      WHEN theta_value < 1 THEN 'above_avg'
      WHEN theta_value < 2 THEN 'high'
      ELSE 'very_high'
    END AS theta_range,
    AVG(test_info) AS avg_info
  FROM shared_irt.test_info_curve
  GROUP BY window_id, 
    CASE 
      WHEN theta_value < -2 THEN 'very_low'
      WHEN theta_value < -1 THEN 'low'
      WHEN theta_value < 0 THEN 'below_avg'
      WHEN theta_value < 1 THEN 'above_avg'
      WHEN theta_value < 2 THEN 'high'
      ELSE 'very_high'
    END
),
info_changes AS (
  SELECT 
    curr.window_id,
    curr.theta_range,
    curr.avg_info AS current_info,
    prev.avg_info AS previous_info,
    (curr.avg_info - prev.avg_info) / prev.avg_info AS pct_change
  FROM theta_intervals curr
  JOIN theta_intervals prev 
    ON curr.theta_range = prev.theta_range
    AND prev.window_id = (
      SELECT MAX(window_id) 
      FROM shared_irt.windows 
      WHERE window_id < curr.window_id
    )
)
INSERT INTO shared_irt.drift_alerts (item_id, window_id, metric, value, threshold, severity, message)
SELECT 
    NULL AS item_id,  -- Test-level alert, not item-specific
    window_id,
    'info_drop_' || theta_range AS metric,
    pct_change AS value,
    -0.2 AS threshold,
    'low' AS severity,
    format(
        'Test information dropped %.1f%% in %s θ range (%.2f → %.2f)',
        pct_change * 100,
        theta_range,
        previous_info,
        current_info
    ) AS message
FROM info_changes
WHERE pct_change < -0.2;  -- 20% drop
```

### 3.2 Interpretation

**Why monitor θ-range information?**

- **Information drop at low θ**: Easy items became harder → students struggle more
- **Information drop at high θ**: Hard items became easier → ceiling effect
- **Information drop at mid θ**: Core items drifted → test less reliable for target population

**Action items:**
1. Identify which items contribute to that θ range
2. Review those items for content changes, translation issues
3. Consider adjusting item selection in CAT to maintain information

### 3.3 Item-Specific Information Drop

```sql
-- Detect items whose max information dropped significantly
WITH item_max_info AS (
  SELECT 
    item_id,
    window_id,
    MAX(item_info) AS max_info
  FROM shared_irt.item_info_curve
  GROUP BY item_id, window_id
),
info_drop AS (
  SELECT 
    curr.item_id,
    curr.window_id,
    curr.max_info AS current_max,
    prev.max_info AS previous_max,
    (curr.max_info - prev.max_info) / prev.max_info AS pct_change
  FROM item_max_info curr
  JOIN item_max_info prev 
    ON curr.item_id = prev.item_id
    AND prev.window_id = (
      SELECT MAX(window_id) 
      FROM item_max_info 
      WHERE item_id = curr.item_id 
        AND window_id < curr.window_id
    )
)
INSERT INTO shared_irt.drift_alerts (item_id, window_id, metric, value, threshold, severity, message)
SELECT 
    item_id,
    window_id,
    'max_info_drop' AS metric,
    pct_change AS value,
    -0.2 AS threshold,
    'low' AS severity,
    format(
        'Item max information dropped %.1f%% (%.3f → %.3f)',
        pct_change * 100,
        previous_max,
        current_max
    ) AS message
FROM info_drop
WHERE pct_change < -0.2;
```

## 4. Summary of Alert Thresholds

| Metric | Threshold | Severity | Action Required |
|--------|-----------|----------|-----------------|
| \|Δb\| | > 0.25 | MEDIUM | Review item, investigate causes |
| \|Δb\| | > 0.5 | HIGH | Immediate review, consider flagging |
| \|Δa\| | > 0.2 | MEDIUM | Check discrimination changes |
| \|Δa\| | > 0.4 | HIGH | Major issue, review answer key |
| Δc | > 0.03 | MEDIUM | Guessing increased, check difficulty |
| P(\|Δb\| > 0.3) | > 0.9 | HIGH | DIF detected (Bayesian) |
| Bayes Factor | > 10 | HIGH | Strong DIF evidence |
| Info drop | > 20% | LOW | Monitor test reliability in θ range |

## 5. Implementation Checklist

### For Calibration Jobs (Python/R)

- [ ] Compute parameter changes (Δb, Δa, Δc) between consecutive windows
- [ ] Insert alerts into `shared_irt.drift_alerts` table
- [ ] Flag items with severity='high' for immediate review
- [ ] Generate DIF analysis for language/country/tier groups
- [ ] Compute posterior probabilities and Bayes Factors (Bayesian methods)
- [ ] Store DIF results in `shared_irt.dif_analysis` table
- [ ] Compute test information curves and detect drops
- [ ] Send notifications for HIGH severity alerts

### For API Endpoints

- [ ] GET /api/analytics/irt/drift/alerts - Filter by severity
- [ ] GET /api/analytics/irt/drift/summary - Count alerts by metric
- [ ] GET /api/analytics/irt/dif/{item_id} - Show DIF analysis results
- [ ] PATCH /api/analytics/irt/drift/alerts/{id}/resolve - Mark alerts as reviewed

### For Reports

- [ ] Include alert summary table (grouped by severity)
- [ ] Show items exceeding high-risk thresholds
- [ ] Display DIF analysis for flagged items
- [ ] Plot θ-range information curves (current vs. previous)
- [ ] Highlight items with >20% max_info drop

## 6. References

### Academic Standards
- **Δb threshold**: AERA/APA/NCME Standards (2014) - difficulty changes >0.5 SD warrant investigation
- **DIF detection**: Zwick, R. (2012). *A Review of ETS Differential Item Functioning Assessment Procedures* - recommends BF>10 for strong evidence
- **Information criteria**: Lord, F. M. (1980). *Applications of Item Response Theory* - 20% information drop affects SEM significantly

### Industry Practice
- **ETS**: Uses |Δb| > 0.5 as flagging threshold for operational items
- **Pearson**: Monitors guessing parameter increases >0.05 for security concerns
- **NWEA MAP**: DIF detection with P(|Δb| > 0.3) > 0.8 for language groups
