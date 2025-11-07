# 생존분석 (Survival Analysis) 가이드

**작성일**: 2025-11-02  
**상태**: ✅ Python 측 구현 완료, R 서비스 구현 필요

---

## 개요

생존분석을 사용하여 사용자 이탈 위험을 예측합니다. Cox 비례 위험 모델(Cox Proportional Hazards)을 사용하여 14일 미접속 이벤트를 예측합니다.

**목적**: 사용자 이탈 방지 및 고위험군 조기 식별

---

## 구현 상태

### ✅ 완료 (Python 측)

1. **Python 클라이언트**: `apps/seedtest_api/app/clients/r_forecast.py`
   - `fit_survival()`: Cox PH 모델 적합
   - `predict_survival()`: 생존 확률 예측

2. **Job**: `apps/seedtest_api/jobs/fit_survival_churn.py`
   - 데이터 로드 (attempt VIEW, weekly_kpi)
   - R 서비스 호출
   - `survival_fit_meta` 저장
   - `weekly_kpi.S` 업데이트

3. **데이터베이스**: `survival_fit_meta` 테이블 (Alembic migration)
   - `run_id` (PK)
   - `formula` (Survival formula)
   - `coefficients` (JSONB)
   - `hazard_ratios` (JSONB)
   - `fitted_at` (timestamp)

4. **CronJob**: `portal_front/ops/k8s/cron/fit-survival-churn.yaml`
   - 매일 05:00 UTC 실행

---

## R 서비스 구현 필요

### r-forecast-plumber 엔드포인트

#### `/survival/fit`

**입력**:
```json
{
  "data": [
    {
      "user_id": "uuid",
      "time": 10.5,
      "event": 1,
      "engagement": 0.8,
      "efficiency": 0.7,
      "recovery": 0.6,
      "mean_gap": 5.2,
      "sessions": 15
    }
  ],
  "formula": "Surv(time, event) ~ engagement + efficiency + recovery + mean_gap + sessions",
  "model_type": "coxph"
}
```

**출력**:
```json
{
  "coefficients": {
    "engagement": -0.5,
    "efficiency": -0.3,
    "recovery": -0.4,
    "mean_gap": 0.2,
    "sessions": -0.1
  },
  "hazard_ratios": {
    "engagement": 0.606,
    "efficiency": 0.741,
    "recovery": 0.670,
    "mean_gap": 1.221,
    "sessions": 0.905
  },
  "risk_scores": {
    "user-id-1": 0.85,
    "user-id-2": 0.42
  }
}
```

#### `/survival/predict` (선택)

**입력**:
```json
{
  "user_features": [
    {
      "user_id": "uuid",
      "engagement": 0.8,
      "efficiency": 0.7,
      "recovery": 0.6,
      "mean_gap": 5.2,
      "sessions": 15
    }
  ],
  "time_points": [7, 14, 21, 30]
}
```

**출력**:
```json
{
  "survival_curves": {
    "user-id-1": {
      "7": 0.95,
      "14": 0.85,
      "21": 0.72,
      "30": 0.60
    }
  },
  "risk_rankings": [
    {"user_id": "user-id-1", "risk_score": 0.85, "rank": 1},
    {"user_id": "user-id-2", "risk_score": 0.42, "rank": 2}
  ]
}
```

---

## R 구현 예시

### R 코드 (Plumber)

```r
# Load required packages
library(survival)
library(dplyr)

#* @post /survival/fit
function(req, res) {
  data <- req$body$data
  formula <- as.formula(req$body$formula)
  model_type <- req$body$model_type %||% "coxph"
  
  df <- as.data.frame(data)
  
  # Fit Cox PH model
  model <- coxph(formula, data = df)
  
  # Extract coefficients and hazard ratios
  coefs <- coef(model)
  hr <- exp(coefs)
  
  # Compute risk scores (linear predictor)
  df$risk_score <- predict(model, type = "risk")
  
  # Normalize risk scores to [0, 1]
  risk_scores <- (df$risk_score - min(df$risk_score)) / 
                 (max(df$risk_score) - min(df$risk_score))
  names(risk_scores) <- df$user_id
  
  list(
    coefficients = as.list(coefs),
    hazard_ratios = as.list(hr),
    risk_scores = as.list(risk_scores)
  )
}

#* @post /survival/predict
function(req, res) {
  # Implementation for prediction
  # ...
}
```

---

## 사용 방법

### 로컬 테스트

```bash
# 환경 변수 설정
export DATABASE_URL="postgresql://..."
export R_FORECAST_BASE_URL="http://localhost:8000"

# Dry-run
python3 -m apps.seedtest_api.jobs.fit_survival_churn --dry-run

# 실제 실행
python3 -m apps.seedtest_api.jobs.fit_survival_churn \
  --lookback-days 90 \
  --event-threshold-days 14
```

### Kubernetes Job 실행

```bash
# CronJob으로부터 수동 Job 생성
kubectl -n seedtest create job --from=cronjob/fit-survival-churn \
  fit-survival-churn-test-$(date +%s)

# 직접 Job 실행
kubectl apply -f portal_front/ops/k8s/jobs/fit-survival-churn-now.yaml

# 로그 확인
kubectl -n seedtest logs job/fit-survival-churn-now -f
```

### CronJob 배포

```bash
# CronJob 생성
kubectl apply -f portal_front/ops/k8s/cron/fit-survival-churn.yaml

# CronJob 확인
kubectl -n seedtest get cronjob fit-survival-churn

# 다음 실행 시간 확인
kubectl -n seedtest get cronjob fit-survival-churn -o jsonpath='{.status.lastScheduleTime}'
```

---

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `R_FORECAST_BASE_URL` | `http://r-forecast-plumber.seedtest.svc.cluster.local:80` | R Forecast 서비스 URL |
| `R_FORECAST_TIMEOUT_SECS` | `300` | 요청 타임아웃 (초) |
| `R_FORECAST_INTERNAL_TOKEN` | (없음) | 내부 인증 토큰 (선택) |
| `SURVIVAL_LOOKBACK_DAYS` | `90` | 학습 데이터 lookback 기간 (일) |
| `SURVIVAL_EVENT_THRESHOLD_DAYS` | `14` | 이탈 이벤트 정의 기준 (일) |
| `SURVIVAL_UPDATE_KPI` | `true` | `weekly_kpi.S` 업데이트 여부 |

---

## 데이터 흐름

1. **데이터 로드**:
   - `attempt VIEW`: 최근 활동 추적
   - `weekly_kpi`: A_t, E_t, R_t, mean_gap, sessions
   - Event 정의: `days_since_last >= 14`

2. **모델 적합**:
   - Cox PH 모델: `Surv(time, event) ~ engagement + efficiency + recovery + mean_gap + sessions`
   - R 서비스 호출: `/survival/fit`

3. **결과 저장**:
   - `survival_fit_meta`: 모델 계수, 위험비
   - `weekly_kpi.S`: 개별 사용자 위험 점수 (0-1)

4. **활용**:
   - 고위험군 식별: `S > 0.7`
   - 리포트 반영: 주간 리포트에 S 값 표시
   - 조기 개입: 7일 미접속 시 즉시 갱신 (`detect_inactivity.py` 통합)

---

## `detect_inactivity.py` 통합

`detect_inactivity.py`는 이미 구현되어 있으며, 7일 미접속 사용자를 찾아 P/S를 재계산합니다.

**통합 방안**:
1. `detect_inactivity.py`에서 발견된 사용자에 대해 즉시 생존분석 예측 호출
2. 또는 생존분석 Job에서 위험 점수가 높은 사용자 목록 반환하여 조기 개입

---

## 검증

### 데이터베이스 검증

```sql
-- 최근 적합 결과 확인
SELECT 
    run_id,
    formula,
    coefficients,
    hazard_ratios,
    fitted_at
FROM survival_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- 위험 점수 확인
SELECT 
    user_id,
    week_start,
    kpis->>'S' AS risk_score,
    updated_at
FROM weekly_kpi
WHERE kpis ? 'S'
  AND (kpis->>'S')::float > 0.7
ORDER BY (kpis->>'S')::float DESC
LIMIT 10;
```

### 로그 확인

```bash
# Job 로그에서 확인할 내용:
# - Loaded N user records
# - Coefficients: {...}
# - Hazard ratios: {...}
# - Risk scores computed for N users
# - Updated weekly_kpi.S for N users
```

---

## 문제 해결

### R 서비스 연결 실패

```
[ERROR] R Survival service call failed: ...
```

**해결**:
1. `R_FORECAST_BASE_URL` 확인
2. r-forecast-plumber 서비스 상태 확인: `kubectl -n seedtest get pods | grep forecast`
3. 네트워크 정책 확인

### 데이터 부족

```
[WARN] No user activity data found for survival fitting
```

**해결**:
1. `SURVIVAL_LOOKBACK_DAYS` 증가
2. `attempt VIEW` 데이터 확인
3. `weekly_kpi` 데이터 확인

### 위험 점수 업데이트 실패

```
[WARN] Failed to update KPI for user-id: ...
```

**해결**:
1. 사용자별 `weekly_kpi` 레코드 존재 확인
2. 데이터 타입 확인 (float)
3. 로그에서 상세 에러 확인

---

## 다음 단계

1. **R 서비스 구현**: r-forecast-plumber `/survival/fit` 엔드포인트
2. **테스트**: 실제 데이터로 검증
3. **모니터링**: 위험 점수 분포 및 모델 성능 추적
4. **리포트 통합**: 주간 리포트에 S 값 반영

---

**생존분석 구현 준비 완료!** 🎯

