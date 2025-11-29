# Drift Detection Practical Guide

**Document**: 03_DRIFT_DETECTION_GUIDE.md  
**Part of**: IRT System Documentation Series  
**Created**: 2025-11-05  
**Status**: ✅ Production Ready  

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Drift Detection Overview](#drift-detection-overview)
3. [Detection Methods](#detection-methods)
4. [SQL Implementation](#sql-implementation)
5. [Alert Generation](#alert-generation)
6. [DIF Analysis](#dif-analysis)
7. [Practical Examples](#practical-examples)
8. [Troubleshooting](#troubleshooting)
9. [한글 가이드 (Korean Guide)](#한글-가이드-korean-guide)

---

## Quick Reference

### Drift Thresholds

| Metric | Medium Alert | High Alert | Critical Alert |
|--------|--------------|------------|----------------|
| **Difficulty (b)** | \|Δb\| > 0.25 | \|Δb\| > 0.5 | \|Δb\| > 0.75 |
| **Discrimination (a)** | \|Δa\| > 0.2 | \|Δa\| > 0.4 | \|Δa\| > 0.6 |
| **Guessing (c)** | Δc > 0.03 | Δc > 0.06 | Δc > 0.10 |
| **Information Drop** | 20-30% | 30-50% | > 50% |

### DIF Thresholds (Bayesian)

| Method | Threshold | Interpretation |
|--------|-----------|----------------|
| **Posterior Probability** | P(\|Δb\| > 0.3) > 0.9 | Strong evidence of DIF |
| **Bayes Factor** | BF > 10 | Strong evidence |
| **Credible Interval** | 95% CI excludes 0 | Significant difference |

---

## Drift Detection Overview

### What is Parameter Drift?

**Parameter drift** occurs when item parameters (a, b, c) change over time due to:
- **Item exposure**: Test-takers memorize answers
- **Curriculum changes**: Content becomes easier/harder
- **Population shift**: Student demographics change
- **Scoring errors**: Changes in rubrics or automation

### Why Monitor Drift?

- ⚠️ **Test fairness**: Ensure consistent measurement
- 📊 **Score validity**: Maintain comparability across time
- 🎯 **Item quality**: Identify problematic items early
- 🔒 **Security**: Detect compromised items

---

## Detection Methods

### 1. Parameter Comparison

**Method**: Compare current vs previous calibration

**Formula**:
```
Δb = b_current - b_previous
Δa = a_current - a_previous  
Δc = c_current - c_previous
```

**Pros**: Simple, fast, interpretable  
**Cons**: No uncertainty quantification

---

### 2. Bayesian Posterior Comparison

**Method**: Compare posterior distributions (brms/PyMC only)

**Formula**:
```
P(|Δb| > threshold) = mean(|b_current - b_previous| > 0.3)

Where:
  b_current, b_previous are posterior samples (e.g., 8000 samples)
```

**Pros**: Accounts for uncertainty, probabilistic interpretation  
**Cons**: Requires MCMC calibration (slower)

---

### 3. Information Function Degradation

**Method**: Compare test information curves

**Formula**:
```
Fisher Information (2PL):
  I(θ) = a² × P(θ) × [1 - P(θ)]

Fisher Information (3PL):
  I(θ) = a² × (P-c)² / [(1-c)² × P × (1-P)]

Information Drop:
  ΔI(θ) = [I_old(θ) - I_new(θ)] / I_old(θ) × 100%
```

**Alert if**: ΔI(θ) > 20% over ability range [-3, 3]

---

### 4. DIF Analysis (Group Comparison)

**Method**: Compare parameters across demographic groups

**Use Cases**:
- Gender (Male vs Female)
- Language (English vs Spanish vs Korean)
- Age groups (< 25 vs 25-35 vs > 35)
- Region (Urban vs Rural)

**Bayesian DIF**:
```
Δb_gender = b_male - b_female
P(|Δb_gender| > 0.3) = mean(|Δb_gender| > 0.3)
```

---

## SQL Implementation

### 1. Basic Parameter Drift Detection

```sql
-- Detect drift for all items in current vs previous window
WITH current_params AS (
    SELECT 
        item_id,
        a AS a_current,
        b AS b_current,
        c AS c_current
    FROM shared_irt.item_parameters_current
),
previous_params AS (
    SELECT 
        ic.item_id,
        ic.a AS a_previous,
        ic.b AS b_previous,
        ic.c AS c_previous
    FROM shared_irt.item_calibration ic
    INNER JOIN shared_irt.windows w ON ic.window_id = w.window_id
    WHERE w.window_end = (
        SELECT MAX(window_end) 
        FROM shared_irt.windows 
        WHERE window_end < CURRENT_DATE
    )
)
SELECT 
    c.item_id,
    c.b_current,
    p.b_previous,
    c.b_current - p.b_previous AS delta_b,
    ABS(c.b_current - p.b_previous) AS abs_delta_b,
    c.a_current - p.a_previous AS delta_a,
    c.c_current - p.c_previous AS delta_c,
    CASE 
        WHEN ABS(c.b_current - p.b_previous) > 0.75 THEN 'critical'
        WHEN ABS(c.b_current - p.b_previous) > 0.5 THEN 'high'
        WHEN ABS(c.b_current - p.b_previous) > 0.25 THEN 'medium'
        ELSE 'none'
    END AS severity
FROM current_params c
INNER JOIN previous_params p ON c.item_id = p.item_id
WHERE ABS(c.b_current - p.b_previous) > 0.25
ORDER BY abs_delta_b DESC;
```

---

### 2. Information Function Degradation

```sql
-- Calculate information drop across ability range
WITH theta_grid AS (
    SELECT generate_series(-3.0, 3.0, 0.5) AS theta
),
current_params AS (
    SELECT item_id, a, b, c
    FROM shared_irt.item_parameters_current
),
previous_params AS (
    SELECT ic.item_id, ic.a, ic.b, ic.c
    FROM shared_irt.item_calibration ic
    INNER JOIN shared_irt.windows w ON ic.window_id = w.window_id
    WHERE w.window_end = (
        SELECT MAX(window_end) 
        FROM shared_irt.windows 
        WHERE window_end < CURRENT_DATE
    )
),
info_comparison AS (
    SELECT 
        c.item_id,
        t.theta,
        -- Current information (3PL)
        POWER(c.a, 2) * POWER(
            (1.0 / (1 + EXP(-c.a * (t.theta - c.b))) - c.c), 2
        ) / (
            POWER(1 - c.c, 2) * 
            (1.0 / (1 + EXP(-c.a * (t.theta - c.b)))) * 
            (1 - 1.0 / (1 + EXP(-c.a * (t.theta - c.b))))
        ) AS info_current,
        -- Previous information
        POWER(p.a, 2) * POWER(
            (1.0 / (1 + EXP(-p.a * (t.theta - p.b))) - p.c), 2
        ) / (
            POWER(1 - p.c, 2) * 
            (1.0 / (1 + EXP(-p.a * (t.theta - p.b)))) * 
            (1 - 1.0 / (1 + EXP(-p.a * (t.theta - p.b))))
        ) AS info_previous
    FROM theta_grid t
    CROSS JOIN current_params c
    INNER JOIN previous_params p ON c.item_id = p.item_id
)
SELECT 
    item_id,
    AVG(info_current) AS avg_info_current,
    AVG(info_previous) AS avg_info_previous,
    AVG((info_previous - info_current) / NULLIF(info_previous, 0) * 100) AS avg_info_drop_pct,
    MAX((info_previous - info_current) / NULLIF(info_previous, 0) * 100) AS max_info_drop_pct
FROM info_comparison
GROUP BY item_id
HAVING AVG((info_previous - info_current) / NULLIF(info_previous, 0)) > 0.20
ORDER BY avg_info_drop_pct DESC;
```

---

### 3. Bayesian DIF Detection (from stored posteriors)

```sql
-- Assuming posterior samples stored in JSONB column
-- posterior_samples: {"b": [1.2, 1.3, 1.1, ...], "a": [...]}

WITH male_posteriors AS (
    SELECT 
        item_id,
        posterior_samples->'b' AS b_samples
    FROM shared_irt.item_calibration
    WHERE window_id = (SELECT MAX(window_id) FROM shared_irt.windows)
      AND calibration_metadata->>'group' = 'male'
),
female_posteriors AS (
    SELECT 
        item_id,
        posterior_samples->'b' AS b_samples
    FROM shared_irt.item_calibration
    WHERE window_id = (SELECT MAX(window_id) FROM shared_irt.windows)
      AND calibration_metadata->>'group' = 'female'
)
SELECT 
    m.item_id,
    -- Calculate DIF probability from posterior samples
    (
        SELECT COUNT(*)::FLOAT / jsonb_array_length(m.b_samples)
        FROM jsonb_array_elements_text(m.b_samples) WITH ORDINALITY AS m_val(val, idx)
        INNER JOIN jsonb_array_elements_text(f.b_samples) WITH ORDINALITY AS f_val(val, idx)
            ON m_val.idx = f_val.idx
        WHERE ABS(m_val.val::FLOAT - f_val.val::FLOAT) > 0.3
    ) AS prob_dif
FROM male_posteriors m
INNER JOIN female_posteriors f ON m.item_id = f.item_id
WHERE (
    SELECT COUNT(*)::FLOAT / jsonb_array_length(m.b_samples)
    FROM jsonb_array_elements_text(m.b_samples) WITH ORDINALITY AS m_val(val, idx)
    INNER JOIN jsonb_array_elements_text(f.b_samples) WITH ORDINALITY AS f_val(val, idx)
        ON m_val.idx = f_val.idx
    WHERE ABS(m_val.val::FLOAT - f_val.val::FLOAT) > 0.3
) > 0.9;
```

---

## Alert Generation

### Python Service Function

```python
# File: shared/irt/services.py

from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from shared.irt.models import (
    ItemParametersCurrent,
    ItemCalibration,
    DriftAlert,
    CalibrationWindow
)

def generate_drift_alerts(
    session: Session,
    window_id: int,
    thresholds: dict = None
) -> list[DriftAlert]:
    """
    Generate drift alerts by comparing current vs previous parameters.
    
    Args:
        session: Database session
        window_id: Current calibration window ID
        thresholds: Custom thresholds (optional)
            {
                'b_medium': 0.25, 'b_high': 0.5, 'b_critical': 0.75,
                'a_medium': 0.2, 'a_high': 0.4, 'a_critical': 0.6,
                'c_medium': 0.03, 'c_high': 0.06, 'c_critical': 0.10
            }
    
    Returns:
        List of DriftAlert objects
    """
    # Default thresholds
    if thresholds is None:
        thresholds = {
            'b_medium': 0.25, 'b_high': 0.5, 'b_critical': 0.75,
            'a_medium': 0.2, 'a_high': 0.4, 'a_critical': 0.6,
            'c_medium': 0.03, 'c_high': 0.06, 'c_critical': 0.10
        }
    
    # 1. Get current parameters
    current_params = {
        row.item_id: row
        for row in session.execute(
            select(ItemParametersCurrent)
        ).scalars()
    }
    
    # 2. Get previous window ID
    prev_window = session.execute(
        select(CalibrationWindow)
        .where(CalibrationWindow.window_id < window_id)
        .order_by(CalibrationWindow.window_id.desc())
        .limit(1)
    ).scalar_one_or_none()
    
    if not prev_window:
        return []  # No previous window to compare
    
    # 3. Get previous parameters
    previous_params = {
        row.item_id: row
        for row in session.execute(
            select(ItemCalibration)
            .where(ItemCalibration.window_id == prev_window.window_id)
        ).scalars()
    }
    
    # 4. Compare and generate alerts
    alerts = []
    
    for item_id, current in current_params.items():
        if item_id not in previous_params:
            continue  # New item, no baseline
        
        previous = previous_params[item_id]
        
        # Calculate deltas
        delta_b = abs(current.b - previous.b)
        delta_a = abs(current.a - previous.a)
        delta_c = abs(current.c - previous.c) if current.c else 0
        
        # Check difficulty drift
        if delta_b >= thresholds['b_medium']:
            severity = (
                'critical' if delta_b >= thresholds['b_critical']
                else 'high' if delta_b >= thresholds['b_high']
                else 'medium'
            )
            alerts.append(DriftAlert(
                window_id=window_id,
                item_id=item_id,
                metric='difficulty',
                old_value=previous.b,
                new_value=current.b,
                delta=current.b - previous.b,
                severity=severity,
                detected_at=datetime.utcnow()
            ))
        
        # Check discrimination drift
        if delta_a >= thresholds['a_medium']:
            severity = (
                'critical' if delta_a >= thresholds['a_critical']
                else 'high' if delta_a >= thresholds['a_high']
                else 'medium'
            )
            alerts.append(DriftAlert(
                window_id=window_id,
                item_id=item_id,
                metric='discrimination',
                old_value=previous.a,
                new_value=current.a,
                delta=current.a - previous.a,
                severity=severity,
                detected_at=datetime.utcnow()
            ))
        
        # Check guessing drift
        if delta_c >= thresholds['c_medium']:
            severity = (
                'critical' if delta_c >= thresholds['c_critical']
                else 'high' if delta_c >= thresholds['c_high']
                else 'medium'
            )
            alerts.append(DriftAlert(
                window_id=window_id,
                item_id=item_id,
                metric='guessing',
                old_value=previous.c,
                new_value=current.c,
                delta=current.c - previous.c,
                severity=severity,
                detected_at=datetime.utcnow()
            ))
    
    # 5. Bulk insert alerts
    if alerts:
        session.add_all(alerts)
        session.commit()
    
    return alerts
```

---

### Usage Example

```python
# In calibration script or API endpoint

from shared.irt.database import SessionLocal
from shared.irt.services import generate_drift_alerts

with SessionLocal() as session:
    # After calibration completes
    alerts = generate_drift_alerts(
        session=session,
        window_id=current_window_id
    )
    
    print(f"Generated {len(alerts)} drift alerts")
    
    # Critical alerts
    critical = [a for a in alerts if a.severity == 'critical']
    if critical:
        print(f"⚠️  {len(critical)} CRITICAL alerts!")
        for alert in critical:
            print(f"  - Item {alert.item_id}: {alert.metric} "
                  f"Δ={alert.delta:.3f}")
```

---

## DIF Analysis

### Python Implementation (Bayesian)

```python
# File: shared/irt/dif_analysis.py

import numpy as np
from scipy import stats
from typing import Tuple

def bayesian_dif(
    posterior_group1: np.ndarray,
    posterior_group2: np.ndarray,
    threshold: float = 0.3
) -> dict:
    """
    Compute Bayesian DIF metrics from posterior samples.
    
    Args:
        posterior_group1: Posterior samples for group 1 (e.g., male), shape (n_samples,)
        posterior_group2: Posterior samples for group 2 (e.g., female), shape (n_samples,)
        threshold: DIF threshold (default: 0.3 logits)
    
    Returns:
        {
            'delta_mean': Mean difference,
            'delta_median': Median difference,
            'prob_dif': P(|Δb| > threshold),
            'ci_95': 95% credible interval,
            'bayes_factor': Bayes factor (H1: Δb≠0 vs H0: Δb=0)
        }
    """
    # 1. Compute delta distribution
    delta = posterior_group1 - posterior_group2
    
    # 2. Summary statistics
    delta_mean = np.mean(delta)
    delta_median = np.median(delta)
    
    # 3. Probability of DIF
    prob_dif = np.mean(np.abs(delta) > threshold)
    
    # 4. Credible interval
    ci_95 = np.percentile(delta, [2.5, 97.5])
    
    # 5. Bayes Factor (Savage-Dickey ratio)
    # Approximate: BF = p(Δ=0|data) / p(Δ=0|prior)
    # Prior: Normal(0, 1)
    # Posterior density at 0
    from scipy.stats import gaussian_kde
    kde_posterior = gaussian_kde(delta)
    p_delta_zero_posterior = kde_posterior(0)[0]
    p_delta_zero_prior = stats.norm(0, 1).pdf(0)
    bayes_factor = p_delta_zero_posterior / p_delta_zero_prior
    
    return {
        'delta_mean': float(delta_mean),
        'delta_median': float(delta_median),
        'prob_dif': float(prob_dif),
        'ci_95': ci_95.tolist(),
        'bayes_factor': float(bayes_factor),
        'evidence': (
            'No DIF' if prob_dif < 0.5
            else 'Weak DIF' if prob_dif < 0.9
            else 'Strong DIF'
        )
    }


def compute_dif_for_item(
    session: Session,
    item_id: int,
    window_id: int,
    group_column: str = 'gender'
) -> dict:
    """
    Compute DIF for a single item across demographic groups.
    
    Args:
        session: Database session
        item_id: Item ID
        window_id: Calibration window ID
        group_column: Demographic column ('gender', 'language', 'age_group')
    
    Returns:
        {group_pair: dif_metrics}
    """
    # 1. Fetch posterior samples for each group
    stmt = select(ItemCalibration).where(
        and_(
            ItemCalibration.window_id == window_id,
            ItemCalibration.item_id == item_id
        )
    )
    calibrations = session.execute(stmt).scalars().all()
    
    # Group by demographic
    groups = {}
    for calib in calibrations:
        group = calib.calibration_metadata.get(group_column)
        if group and calib.posterior_samples:
            groups[group] = np.array(calib.posterior_samples['b'])
    
    # 2. Pairwise DIF comparisons
    results = {}
    group_names = list(groups.keys())
    
    for i, group1 in enumerate(group_names):
        for group2 in group_names[i+1:]:
            pair_key = f"{group1}_vs_{group2}"
            results[pair_key] = bayesian_dif(
                groups[group1],
                groups[group2]
            )
    
    return results
```

---

## Practical Examples

### Example 1: Monthly Drift Check

```python
# File: scripts/monthly_drift_check.py

from shared.irt.database import SessionLocal
from shared.irt.services import generate_drift_alerts
from shared.irt.models import CalibrationWindow

def monthly_drift_check():
    """Run monthly drift detection after calibration."""
    with SessionLocal() as session:
        # Get latest window
        latest_window = session.query(CalibrationWindow)\
            .order_by(CalibrationWindow.window_id.desc())\
            .first()
        
        if not latest_window:
            print("No calibration windows found")
            return
        
        # Generate alerts
        alerts = generate_drift_alerts(
            session,
            window_id=latest_window.window_id
        )
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Drift Detection Summary - Window {latest_window.window_id}")
        print(f"Period: {latest_window.window_start} to {latest_window.window_end}")
        print(f"{'='*60}\n")
        
        severity_counts = {}
        for alert in alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
        
        print(f"Total Alerts: {len(alerts)}")
        print(f"  - Critical: {severity_counts.get('critical', 0)}")
        print(f"  - High: {severity_counts.get('high', 0)}")
        print(f"  - Medium: {severity_counts.get('medium', 0)}")
        
        # Show critical alerts
        critical = [a for a in alerts if a.severity == 'critical']
        if critical:
            print(f"\n⚠️  CRITICAL ALERTS ({len(critical)}):")
            for alert in critical[:10]:  # Top 10
                print(f"  - Item {alert.item_id}: {alert.metric}")
                print(f"    Old: {alert.old_value:.3f}, New: {alert.new_value:.3f}, "
                      f"Δ: {alert.delta:+.3f}")

if __name__ == '__main__':
    monthly_drift_check()
```

**Run via SystemD**:
```bash
sudo systemctl start irt-drift-check.service
```

---

### Example 2: DIF Analysis by Gender

```python
# File: scripts/dif_gender_analysis.py

from shared.irt.database import SessionLocal
from shared.irt.dif_analysis import compute_dif_for_item
from shared.irt.models import Item

def analyze_gender_dif(window_id: int):
    """Analyze gender DIF for all items in a window."""
    with SessionLocal() as session:
        # Get all items
        items = session.query(Item).all()
        
        dif_results = []
        
        for item in items:
            try:
                dif = compute_dif_for_item(
                    session,
                    item_id=item.item_id,
                    window_id=window_id,
                    group_column='gender'
                )
                
                # Extract male vs female
                if 'male_vs_female' in dif:
                    result = dif['male_vs_female']
                    if result['prob_dif'] > 0.9:  # Strong DIF
                        dif_results.append({
                            'item_id': item.item_id,
                            'item_name': item.item_name,
                            'delta_mean': result['delta_mean'],
                            'prob_dif': result['prob_dif'],
                            'evidence': result['evidence']
                        })
            except Exception as e:
                print(f"Error analyzing item {item.item_id}: {e}")
        
        # Report
        print(f"\n{'='*60}")
        print(f"Gender DIF Analysis - Window {window_id}")
        print(f"{'='*60}\n")
        print(f"Items with Strong DIF: {len(dif_results)}")
        
        for item in sorted(dif_results, key=lambda x: x['prob_dif'], reverse=True):
            print(f"\nItem {item['item_id']}: {item['item_name']}")
            print(f"  Δb (Male - Female): {item['delta_mean']:+.3f}")
            print(f"  P(|Δb| > 0.3): {item['prob_dif']:.3f}")
            print(f"  Evidence: {item['evidence']}")

if __name__ == '__main__':
    analyze_gender_dif(window_id=12)  # Latest window
```

---

## Troubleshooting

### Issue 1: Too Many False Positives

**Symptom**: Hundreds of medium alerts for minor drift

**Solution**:
```python
# Increase thresholds
thresholds = {
    'b_medium': 0.35,  # instead of 0.25
    'b_high': 0.6,     # instead of 0.5
    'a_medium': 0.3,   # instead of 0.2
    'a_high': 0.5      # instead of 0.4
}

alerts = generate_drift_alerts(session, window_id, thresholds)
```

---

### Issue 2: No Alerts Generated

**Symptom**: `generate_drift_alerts()` returns empty list

**Debugging**:
```python
# Check if previous window exists
prev_window = session.query(CalibrationWindow)\
    .filter(CalibrationWindow.window_id < current_window_id)\
    .order_by(CalibrationWindow.window_id.desc())\
    .first()

if not prev_window:
    print("No previous window - this is the first calibration")

# Check parameter count
current_count = session.query(ItemParametersCurrent).count()
previous_count = session.query(ItemCalibration)\
    .filter(ItemCalibration.window_id == prev_window.window_id)\
    .count()

print(f"Current: {current_count}, Previous: {previous_count}")
```

---

### Issue 3: DIF Analysis Fails

**Symptom**: `KeyError: 'b'` in posterior_samples

**Solution**:
```python
# Check if posterior samples exist
calib = session.query(ItemCalibration)\
    .filter_by(window_id=window_id, item_id=item_id)\
    .first()

if not calib.posterior_samples:
    print("No posterior samples - calibration used mirt (EM)")
    print("DIF analysis requires brms or PyMC (MCMC)")
```

**Fix**: Re-calibrate with PyMC or brms to get posteriors.

---

## 한글 가이드 (Korean Guide)

### 드리프트 탐지란?

**파라미터 드리프트**는 문항 파라미터(a, b, c)가 시간에 따라 변하는 현상입니다.

**원인**:
- 문항 노출: 수험자가 답을 외움
- 교육과정 변경: 내용이 쉬워지거나 어려워짐
- 모집단 변화: 학생 구성이 달라짐
- 채점 오류: 채점 기준 변경

---

### 주요 임계값

| 지표 | 보통 | 높음 | 심각 |
|------|------|------|------|
| **난이도 (b)** | \|Δb\| > 0.25 | \|Δb\| > 0.5 | \|Δb\| > 0.75 |
| **변별도 (a)** | \|Δa\| > 0.2 | \|Δa\| > 0.4 | \|Δa\| > 0.6 |
| **추측도 (c)** | Δc > 0.03 | Δc > 0.06 | Δc > 0.10 |

---

### 탐지 방법

#### 1. 파라미터 비교 (간단)
```python
delta_b = b_현재 - b_이전
if abs(delta_b) > 0.25:
    print("드리프트 발견!")
```

#### 2. 베이지안 비교 (정확)
```python
# PyMC 또는 brms 사용 시
prob_dif = mean(abs(b_현재 - b_이전) > 0.3)
if prob_dif > 0.9:
    print("강한 드리프트 증거!")
```

---

### 실무 예제

#### 월간 드리프트 체크
```python
from shared.irt.services import generate_drift_alerts

with SessionLocal() as session:
    alerts = generate_drift_alerts(session, window_id=12)
    
    print(f"총 알림: {len(alerts)}개")
    critical = [a for a in alerts if a.severity == 'critical']
    print(f"심각: {len(critical)}개")
```

#### 성별 DIF 분석
```python
from shared.irt.dif_analysis import compute_dif_for_item

dif = compute_dif_for_item(
    session,
    item_id=101,
    window_id=12,
    group_column='gender'
)

result = dif['male_vs_female']
print(f"남녀 난이도 차이: {result['delta_mean']:.3f}")
print(f"DIF 확률: {result['prob_dif']:.1%}")
```

---

### 문제 해결

**문제**: 알림이 너무 많음 (수백 개)
- **해결**: 임계값을 높임 (0.25 → 0.35)

**문제**: 알림이 하나도 없음
- **원인**: 이전 캘리브레이션 없음 (첫 실행)
- **확인**: `SELECT COUNT(*) FROM shared_irt.windows`

**문제**: DIF 분석 실패 (`KeyError: 'b'`)
- **원인**: mirt 사용 시 posterior_samples 없음
- **해결**: PyMC 또는 brms로 재캘리브레이션

---

### 다음 단계

1. **알림 생성 테스트**:
   ```bash
   python scripts/monthly_drift_check.py
   ```

2. **DIF 분석 실행**:
   ```bash
   python scripts/dif_gender_analysis.py
   ```

3. **대시보드 확인**:
   - 프론트엔드: `MonthlyDriftReport` 컴포넌트
   - API: `GET /api/irt/drift/alerts`

---

**작성자**: DreamSeed AI Team  
**최종 업데이트**: 2025-11-05  
**관련 문서**: 02_CALIBRATION_METHODS_COMPARISON.md, THRESHOLDS_AND_DIF.md
