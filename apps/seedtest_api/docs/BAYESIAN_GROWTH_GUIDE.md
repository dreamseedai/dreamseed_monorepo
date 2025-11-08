# 베이지안 성장 모델 (Bayesian Growth Model) 가이드

**작성일**: 2025-11-02  
**상태**: ✅ Python 측 구현 완료, R 서비스 구현 필요

---

## 개요

베이지안 계층 모델(Bayesian Hierarchical Model)을 사용하여 목표 달성 확률 P(goal|state)를 불확실성과 함께 예측합니다. brms (Stan 백엔드)를 사용하여 posterior 샘플링을 수행합니다.

**목적**: 목표 달성 확률 및 불확실성 제공

**모델**: `score ~ week + (week|student_id)` (개인별 성장 기울기)

**소표본/잡음 안정화**: 사전 분포(Priors)를 통한 정규화로 소규모 데이터나 잡음이 많은 상황에서도 안정적인 추정이 가능합니다.

---

## 구현 상태

### ✅ 완료 (Python 측)

1. **Python 클라이언트**: `apps/seedtest_api/app/clients/r_brms.py`
   - `fit_growth()`: 베이지안 성장 모델 적합
   - `predict_goal_probability()`: 목표 달성 확률 예측
   - `prob_goal()`: 간단한 확률 계산 (fallback)

2. **Job**: `apps/seedtest_api/jobs/fit_bayesian_growth.py`
   - 데이터 로드 (mirt_ability, features_topic_daily)
   - R 서비스 호출
   - `growth_brms_meta` 저장
   - `weekly_kpi.P/sigma` 업데이트

3. **데이터베이스**: `growth_brms_meta` 테이블 (Alembic migration)
   - `run_id` (PK)
   - `formula` (Model formula)
   - `priors` (JSONB)
   - `posterior_summary` (JSONB)
   - `diagnostics` (JSONB)
   - `fitted_at` (timestamp)

4. **CronJob**: `portal_front/ops/k8s/cron/fit-bayesian-growth.yaml`
   - 매주 월요일 04:30 UTC 실행

5. **metrics.py 통합**: `compute_goal_attainment_probability()`에서 `METRICS_USE_BAYESIAN` 플래그 지원

---

## R 서비스 구현 필요

### r-brms-plumber 엔드포인트

#### `/growth/fit`

**입력**:
```json
{
  "data": [
    {
      "student_id": "uuid",
      "week": 0,
      "score": 0.5
    },
    {
      "student_id": "uuid",
      "week": 1,
      "score": 0.6
    }
  ],
  "formula": "score ~ week + (week|student_id)",
  "priors": {
    "intercept": {"dist": "normal", "mean": 0, "sd": 1},
    "week": {"dist": "normal", "mean": 0, "sd": 0.5},
    "sd": {"dist": "cauchy", "location": 0, "scale": 1}
  },
  "n_samples": 2000,
  "n_chains": 4,
  "n_warmup": 1000
}
```

**출력**:
```json
{
  "posterior_summary": {
    "intercept": {"mean": 0.3, "sd": 0.1, "q2.5": 0.1, "q97.5": 0.5},
    "week": {"mean": 0.05, "sd": 0.02, "q2.5": 0.01, "q97.5": 0.09},
    "sigma": {"mean": 0.2, "sd": 0.05}
  },
  "diagnostics": {
    "rhat": {"max": 1.01},
    "ess_bulk": {"min": 1500},
    "ess_tail": {"min": 1400}
  },
  "predictions": {
    "student-id-1": {
      "probability": 0.75,
      "uncertainty": 0.15,
      "lower": 0.60,
      "upper": 0.90
    }
  }
}
```

#### `/growth/predict` (선택)

**입력**:
```json
{
  "user_features": {
    "current_score": 0.6,
    "trend": 0.05,
    "weeks_remaining": 4
  },
  "target_score": 0.8,
  "credible_interval": 0.95
}
```

**출력**:
```json
{
  "probability": 0.75,
  "lower": 0.60,
  "upper": 0.90,
  "uncertainty": 0.15
}
```

---

## R 구현 예시

### R 코드 (Plumber)

```r
# Load required packages
library(brms)
library(dplyr)

#* @post /growth/fit
function(req, res) {
  data <- req$body$data
  formula <- as.formula(req$body$formula)
  priors <- req$body$priors %||% list()
  n_samples <- req$body$n_samples %||% 2000
  n_chains <- req$body$n_chains %||% 4
  n_warmup <- req$body$n_warmup %||% 1000
  
  df <- as.data.frame(data)
  
  # Set priors
  priors_list <- list()
  if (!is.null(priors$intercept)) {
    priors_list$Intercept <- prior_string(
      paste0("normal(", priors$intercept$mean, ", ", priors$intercept$sd, ")"),
      class = "Intercept"
    )
  }
  if (!is.null(priors$week)) {
    priors_list$b <- prior_string(
      paste0("normal(", priors$week$mean, ", ", priors$week$sd, ")"),
      class = "b", coef = "week"
    )
  }
  
  # Fit model
  model <- brm(
    formula,
    data = df,
    prior = priors_list,
    iter = n_samples + n_warmup,
    warmup = n_warmup,
    chains = n_chains,
    cores = n_chains,
    seed = 42
  )
  
  # Extract posterior summary
  posterior_summary <- as.list(fixef(model))
  
  # Diagnostics
  diagnostics <- list(
    rhat = list(max = max(rhat(model))),
    ess_bulk = list(min = min(ess_bulk(model))),
    ess_tail = list(min = min(ess_tail(model)))
  )
  
  # Predictions per student (goal probability)
  predictions <- predict(model, newdata = df) %>%
    as.data.frame() %>%
    group_by(student_id) %>%
    summarise(
      probability = mean(Q97.5 > target_score),  # Simplified
      uncertainty = sd(Q50),
      lower = quantile(Q50, 0.025),
      upper = quantile(Q50, 0.975)
    ) %>%
    as.list()
  
  list(
    posterior_summary = posterior_summary,
    diagnostics = diagnostics,
    predictions = predictions
  )
}

#* @post /growth/predict
function(req, res) {
  # Implementation for individual prediction
  # ...
}
```

---

## 사용 방법

### 로컬 테스트

```bash
# 환경 변수 설정
export DATABASE_URL="postgresql://..."
export R_BRMS_BASE_URL="http://localhost:8000"

# Dry-run
python3 -m apps.seedtest_api.jobs.fit_bayesian_growth --dry-run

# 실제 실행
python3 -m apps.seedtest_api.jobs.fit_bayesian_growth \
  --lookback-weeks 12 \
  --n-samples 2000 \
  --n-chains 4
```

### Kubernetes Job 실행

```bash
# CronJob으로부터 수동 Job 생성
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth \
  fit-bayesian-growth-test-$(date +%s)

# 직접 Job 실행
kubectl apply -f portal_front/ops/k8s/jobs/fit-bayesian-growth-now.yaml

# 로그 확인
kubectl -n seedtest logs job/fit-bayesian-growth-now -f
```

### CronJob 배포

```bash
# CronJob 생성
kubectl apply -f portal_front/ops/k8s/cron/fit-bayesian-growth.yaml

# CronJob 확인
kubectl -n seedtest get cronjob fit-bayesian-growth
```

---

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `R_BRMS_BASE_URL` | `http://r-brms-plumber.seedtest.svc.cluster.local:80` | R BRMS 서비스 URL |
| `R_BRMS_TIMEOUT_SECS` | `600` | 요청 타임아웃 (초, Stan MCMC는 느릴 수 있음) |
| `R_BRMS_INTERNAL_TOKEN` | (없음) | 내부 인증 토큰 (선택) |
| `BRMS_LOOKBACK_WEEKS` | `12` | 학습 데이터 lookback 기간 (주) |
| `BRMS_N_SAMPLES` | `2000` | Posterior 샘플 수 |
| `BRMS_N_CHAINS` | `4` | MCMC 체인 수 |
| `BRMS_UPDATE_KPI` | `true` | `weekly_kpi.P/sigma` 업데이트 여부 |
| `METRICS_USE_BAYESIAN` | `false` | `metrics.py`에서 베이지안 경로 사용 여부 |

---

## 소표본/잡음 안정화를 위한 Priors

베이지안 모델의 강점 중 하나는 사전 분포(Priors)를 통해 소규모 데이터셋이나 잡음이 많은 상황에서도 안정적인 추정이 가능하다는 점입니다.

### Priors 설정

```python
priors = {
    "intercept": {"dist": "normal", "mean": 0, "sd": 1},  # Regularize baseline ability
    "week": {"dist": "normal", "mean": 0, "sd": 0.5},  # Regularize growth slope
    "sd": {"dist": "cauchy", "location": 0, "scale": 1},  # Robust to outliers
}
```

### 각 Prior의 역할

1. **Intercept Prior (Normal, mean=0, sd=1)**:
   - 목적: 기준 능력(θ=0 주변)으로 정규화
   - 효과: 극단적인 절편값 방지, 소표본에서 안정성 제공
   - 적용: 모든 학생의 기준 능력을 0 근처로 제한

2. **Week Slope Prior (Normal, mean=0, sd=0.5)**:
   - 목적: 성장 기울기를 0 주변으로 정규화
   - 효과: 과도한 성장/퇴보 추정 방지
   - 적용: 개인별 성장 기울기를 합리적 범위로 제한

3. **SD Prior (Cauchy, location=0, scale=1)**:
   - 목적: 잔차 표준편차의 로버스트 추정
   - 효과: 이상치에 강건, 무거운 꼬리 허용
   - 적용: 잡음이 많은 데이터에서 안정적인 불확실성 추정

### 안정화 효과

**소표본 상황**:
- 데이터가 적을 때 (예: 학생당 3-5주 데이터)
- Priors가 극단적인 추정을 방지
- 합리적 범위 내에서 posterior 추정

**잡음이 많은 상황**:
- 측정 오류, 외부 요인으로 인한 변동
- Cauchy prior가 이상치에 덜 민감
- 더 안정적인 불확실성 추정 (σ)

**MCMC 수렴**:
- Bounded priors가 샘플링 공간 제한
- 더 빠른 수렴 및 안정적인 체인

---

## 데이터 흐름

1. **데이터 로드**:
   - `mirt_ability`: 사용자별 θ (우선)
   - `features_topic_daily`: 토픽별 θ_mean (폴백)
   - 주차 인덱스 변환 (0-based)

2. **모델 적합**:
   - 계층 모델: `score ~ week + (week|student_id)`
   - Priors: intercept, week slope, sigma
   - R 서비스 호출: `/growth/fit`

3. **결과 저장**:
   - `growth_brms_meta`: 모델 계수, diagnostics
   - `weekly_kpi.P`: 목표 달성 확률 (0-1)
   - `weekly_kpi.sigma`: 불확실성

4. **활용**:
   - `compute_goal_attainment_probability()`에서 `METRICS_USE_BAYESIAN=true` 시 사용
   - 리포트에 P 및 신뢰구간 표시

---

## metrics.py 통합

`compute_goal_attainment_probability()` 함수에서 `METRICS_USE_BAYESIAN=true`로 설정하면 베이지안 경로를 사용합니다:

```python
# In compute_goal_attainment_probability()
use_bayes = os.getenv("METRICS_USE_BAYESIAN", "false").lower() == "true"
if use_bayes:
    from ..app.clients import r_brms as rbrms
    mu_sd = load_user_ability_summary(session, user_id)
    if mu_sd:
        mu, sd = mu_sd
        prob = rbrms.RBrmsClient().prob_goal(mu=mu, sd=sd, target=target)
        return prob
```

---

## 검증

### 데이터베이스 검증

```sql
-- 최근 적합 결과 확인
SELECT 
    run_id,
    formula,
    posterior_summary,
    diagnostics,
    fitted_at
FROM growth_brms_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- 목표 달성 확률 확인
SELECT 
    user_id,
    week_start,
    kpis->>'P' AS goal_probability,
    kpis->>'sigma' AS uncertainty,
    updated_at
FROM weekly_kpi
WHERE kpis ? 'P'
  AND (kpis->>'P')::float > 0.5
ORDER BY (kpis->>'P')::float DESC
LIMIT 10;
```

---

## 문제 해결

### R 서비스 연결 실패

```
[ERROR] R BRMS service call failed: ...
```

**해결**:
1. `R_BRMS_BASE_URL` 확인
2. r-brms-plumber 서비스 상태 확인
3. 타임아웃 증가 (Stan MCMC는 오래 걸릴 수 있음)

### MCMC 수렴 문제

**해결**:
1. `n_warmup` 증가
2. `n_samples` 증가
3. Priors 조정
4. Diagnostics 확인 (Rhat, ESS)

### 메모리 부족

**해결**:
1. `n_samples` 감소
2. `n_chains` 감소
3. Pod 리소스 증가

---

## 다음 단계

1. **R 서비스 구현**: r-brms-plumber `/growth/fit` 엔드포인트
2. **테스트**: 실제 데이터로 검증
3. **모니터링**: MCMC diagnostics 추적
4. **리포트 통합**: 주간 리포트에 P 및 신뢰구간 반영

---

**베이지안 성장 모델 구현 준비 완료!** 🎯

