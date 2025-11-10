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

---

## 한글 요약 (Korean Summary)

## 개요

IRT 캘리브레이션 시스템에서 문항 파라미터 드리프트 및 차별기능문항(DIF)을 탐지하기 위한 임계값과 가이드라인입니다.

## 1. 파라미터 드리프트 임계값

### 1.1 기본 임계값 (중간 경보)

연속된 캘리브레이션 윈도우 간 파라미터 변화가 다음을 초과하면 경보 발생:

| 파라미터 | 임계값 | 해석 |
|---------|--------|------|
| **b (난이도)** | \|Δb\| > 0.25 | 난이도가 표준편차 0.25만큼 변화 |
| **a (변별도)** | \|Δa\| > 0.2 | 변별도가 20% 변화 |
| **c (추측도)** | Δc > 0.03 | 추측 확률이 3%p 증가 |

**경보 심각도: 중간(MEDIUM)**

#### 해석
- **|Δb| > 0.25**: 문항이 이전보다 쉬워지거나 어려워짐
  - 예: 이전에는 θ=0에서 50% 정답률 → 현재는 θ=0.25에서 50% 정답률
  - 조치: 문항 내용 검토, 노출 효과 확인, 번역 오류 점검
  
- **|Δa| > 0.2**: 문항의 변별력 변화
  - 예: a=1.0 → a=1.2 (더 잘 변별) 또는 a=0.8 (덜 변별)
  - 조치: 답안 키 오류 확인, 모호한 문구 검토
  
- **Δc > 0.03**: 추측 확률 증가
  - 예: c=0.15 → c=0.18 (추측으로 맞힐 확률 3%p 증가)
  - 조치: 문항 난이도 재검토, 선택지 명료성 확인

### 1.2 고위험 임계값 (높은 경보)

파라미터 변화가 심각한 경우:

| 파라미터 | 임계값 | 해석 |
|---------|--------|------|
| **b (난이도)** | \|Δb\| > 0.5 | 난이도가 크게 변화 (0.5 SD) |
| **a (변별도)** | \|Δa\| > 0.4 | 변별도가 40% 변화 |

**경보 심각도: 높음(HIGH)**

#### 조치 방안
- **|Δb| > 0.5**: 
  - 즉시 문항 검토 필요
  - 문항 노출, 번역 오류, 교육과정 변경 가능성 조사
  - 필요 시 문항 플래깅 또는 교체 고려
  
- **|Δa| > 0.4**:
  - 심각한 문제 가능성
  - 답안 키 오류, 문항 의도와 다른 해석 가능성
  - 즉각적인 검토 및 수정 필요

### 1.3 추측도 파라미터 증가 감시

**왜 c 증가를 모니터링하는가?**
- 추측도 증가는 다음을 시사:
  - 문항이 수험자 집단에 비해 너무 어려워짐
  - 선택지가 너무 명확해짐
  - 문항 노출로 인한 답안 소거 전략 사용

## 2. 차별기능문항(DIF) 탐지

### 2.1 DIF 정의

**DIF는 동일한 능력 수준의 수험자 집단 간 문항 성능이 다르게 나타나는 현象입니다.**

일반적인 그룹 변수:
- **언어**: en(영어), ko(한국어), zh-Hans(중국어 간체), zh-Hant(중국어 번체)
- **국가**: KR(한국), US(미국), CN(중국), TW(대만) 등
- **구독 티어**: free(무료), premium(프리미엄), enterprise(엔터프라이즈)
- **인구통계**: 연령대, 교육 수준

### 2.2 2-그룹 DIF 분석

각 문항에 대해 두 그룹(참조 vs. 초점)으로 나누어 별도 캘리브레이션:

#### 단계 1: 그룹별 캘리브레이션
```python
# 그룹 A (참조 그룹) 캘리브레이션
item_params_A = calibrate_2pl(
    responses_A,  # 참조 그룹 응답
    theta_A       # 참조 그룹 능력
)

# 그룹 B (초점 그룹) 캘리브레이션
item_params_B = calibrate_2pl(
    responses_B,  # 초점 그룹 응답
    theta_B       # 초점 그룹 능력
)
```

#### 단계 2: 파라미터 차이 계산
```python
delta_b = item_params_B['b'] - item_params_A['b']
delta_a = item_params_B['a'] - item_params_A['a']
```

### 2.3 베이지안 DIF 탐지

베이지안 캘리브레이션(brms 또는 PyMC)을 사용하여 사후분포 획득:

#### 임계값 1: 사후 확률
```python
# 난이도가 0.3 이상 차이날 확률
P_delta_b = np.mean(np.abs(posterior_samples['delta_b']) > 0.3)

if P_delta_b > 0.9:
    alert("DIF 탐지: P(|Δb| > 0.3) = {:.2f}".format(P_delta_b))
```

**경보 기준:**
- P(|Δb| > 0.3) > 0.9 → **높음(HIGH)** 심각도 DIF 경보
- P(|Δa| > 0.2) > 0.9 → **중간(MEDIUM)** 심각도 DIF 경보

#### 임계값 2: 베이즈 팩터
```python
# 베이즈 팩터: H1(DIF 존재) vs H0(DIF 없음)
BF_10 = compute_bayes_factor(
    model_with_dif,    # 그룹 효과 있는 모델
    model_without_dif  # 귀무 모델
)

if BF_10 > 10:
    alert("DIF 탐지: 베이즈 팩터 = {:.1f} (강력한 증거)".format(BF_10))
```

**베이즈 팩터 해석:**
| BF₁₀ | 증거 수준 |
|------|-----------|
| 1-3 | 일화적 |
| 3-10 | 중간 |
| 10-30 | 강력 |
| 30-100 | 매우 강력 |
| >100 | 극단적 |

**경보 기준:**
- BF₁₀ > 10 → **높음(HIGH)** 심각도 DIF 경보

### 2.4 DIF 예시

**언어별 DIF 사례:**
- 영어(참조 그룹): b = 0.0, a = 1.2
- 한국어(초점 그룹): b = 0.4, a = 1.2
- **Δb = 0.4**: 한국어 수험자에게 더 어려움
- 원인: 번역 오류, 문화적 맥락 차이, 교육과정 차이

**조치 방안:**
1. 번역 전문가와 문항 검토
2. 해당 언어 수험자 인터뷰
3. 문항 개정 또는 해당 언어 버전 교체
4. 심각한 경우 문항 폐기

## 3. 정보량 함수 하락

### 3.1 θ-구간별 정보량 하락

능력 구간별 검사 정보량을 모니터링하여 국소적 하락 탐지.

#### 임계값
- **정보량이 이전 윈도우 대비 20% 이상 하락**한 θ 구간
- **경보 심각도: 낮음(LOW) - INFO**

#### θ 구간 분류
| θ 범위 | 구간 이름 | 수험자 수준 |
|--------|----------|-----------|
| θ < -2 | very_low | 매우 낮은 능력 |
| -2 ≤ θ < -1 | low | 낮은 능력 |
| -1 ≤ θ < 0 | below_avg | 평균 이하 |
| 0 ≤ θ < 1 | above_avg | 평균 이상 |
| 1 ≤ θ < 2 | high | 높은 능력 |
| θ ≥ 2 | very_high | 매우 높은 능력 |

### 3.2 해석

**θ 구간별 정보량 하락의 의미:**

- **낮은 θ 구간 정보량 하락**: 쉬운 문항이 어려워짐 → 하위권 학생 측정 정확도 감소
- **높은 θ 구간 정보량 하락**: 어려운 문항이 쉬워짐 → 천장효과, 상위권 변별 불가
- **중간 θ 구간 정보량 하락**: 핵심 문항 드리프트 → 목표 집단 측정 신뢰도 저하

**조치 방안:**
1. 해당 θ 구간에 기여하는 문항 식별
2. 문항 내용 변경, 번역 문제 검토
3. CAT 문항 선택 알고리즘 조정하여 정보량 유지

### 3.3 문항별 최대 정보량 하락

개별 문항의 최대 정보량(max I(θ))이 20% 이상 하락한 경우 경보:

```sql
-- 문항별 최대 정보량 20% 이상 하락 탐지
WHERE pct_change < -0.2;  -- 20% 하락
```

**해석:**
- 문항의 변별력 저하
- 추측도 증가로 인한 정보량 감소
- 문항 파라미터 드리프트의 부수 효과

## 4. 경보 임계값 요약

| 지표 | 임계값 | 심각도 | 필요 조치 |
|------|--------|--------|-----------|
| \|Δb\| | > 0.25 | 중간 | 문항 검토, 원인 조사 |
| \|Δb\| | > 0.5 | 높음 | 즉시 검토, 플래깅 고려 |
| \|Δa\| | > 0.2 | 중간 | 변별도 변화 확인 |
| \|Δa\| | > 0.4 | 높음 | 심각한 문제, 답안 키 검토 |
| Δc | > 0.03 | 중간 | 추측도 증가, 난이도 확인 |
| P(\|Δb\| > 0.3) | > 0.9 | 높음 | DIF 탐지 (베이지안) |
| 베이즈 팩터 | > 10 | 높음 | 강력한 DIF 증거 |
| 정보량 하락 | > 20% | 낮음 | θ 구간 신뢰도 모니터링 |

## 5. 구현 체크리스트

### 캘리브레이션 작업 (Python/R)

- [ ] 연속 윈도우 간 파라미터 변화(Δb, Δa, Δc) 계산
- [ ] `shared_irt.drift_alerts` 테이블에 경보 삽입
- [ ] severity='high' 문항 즉시 검토 플래깅
- [ ] 언어/국가/티어별 DIF 분석 수행
- [ ] 사후 확률 및 베이즈 팩터 계산 (베이지안 방법)
- [ ] `shared_irt.dif_analysis` 테이블에 DIF 결과 저장
- [ ] 검사 정보 곡선 계산 및 하락 탐지
- [ ] HIGH 심각도 경보에 대한 알림 발송

### API 엔드포인트

- [ ] GET /api/analytics/irt/drift/alerts - 심각도별 필터링
- [ ] GET /api/analytics/irt/drift/summary - 지표별 경보 집계
- [ ] GET /api/analytics/irt/dif/{item_id} - DIF 분석 결과 표시
- [ ] PATCH /api/analytics/irt/drift/alerts/{id}/resolve - 경보 검토 완료 표시

### 보고서

- [ ] 경보 요약 테이블 포함 (심각도별 그룹화)
- [ ] 고위험 임계값 초과 문항 표시
- [ ] 플래그된 문항의 DIF 분석 표시
- [ ] θ 구간 정보 곡선 플롯 (현재 vs. 이전)
- [ ] 최대 정보량 20% 이상 하락 문항 강조

## 6. 실무 적용 가이드

### 6.1 일일 모니터링

```sql
-- 높은 심각도 경보 조회
SELECT * FROM shared_irt.drift_alerts 
WHERE severity = 'high' 
  AND resolved_at IS NULL
ORDER BY created_at DESC;
```

### 6.2 주간 리뷰

1. **모든 중간 심각도 경보 검토**
2. **DIF 분석 결과 확인** (언어/국가별)
3. **정보량 하락 추세 분석**
4. **플래그된 문항 전문가 리뷰 일정 수립**

### 6.3 월간 보고

1. **월별 드리프트 리포트 생성** (PDF)
2. **경보 통계 요약** (심각도별, 지표별)
3. **조치 완료된 문항 목록**
4. **다음 달 모니터링 계획**

## 7. 참고 문헌

### 학술 표준
- **Δb 임계값**: AERA/APA/NCME Standards (2014) - 난이도 변화 >0.5 SD는 조사 필요
- **DIF 탐지**: Zwick, R. (2012). *A Review of ETS Differential Item Functioning Assessment Procedures* - BF>10을 강력한 증거로 권장
- **정보량 기준**: Lord, F. M. (1980). *Applications of Item Response Theory* - 20% 정보량 하락은 SEM에 유의미한 영향

### 산업 실무
- **ETS**: 운영 중인 문항에 대해 |Δb| > 0.5를 플래깅 임계값으로 사용
- **Pearson**: 보안 우려로 추측도 >0.05 증가 모니터링
- **NWEA MAP**: 언어 그룹에 대해 P(|Δb| > 0.3) > 0.8로 DIF 탐지
