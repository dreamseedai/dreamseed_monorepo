# Prophet 시계열 예측 가이드

**작성일**: 2025-11-02  
**상태**: ✅ Python 측 구현 완료, R 서비스 구현 필요

---

## 개요

Prophet 모델을 사용하여 I_t (개선 지수) 시계열의 추세를 예측하고 이상치를 탐지합니다.

**목적**: 학습 패턴 변화 감지 및 단기 예측

**특징**:
- Changepoint 탐지
- 계절성 및 추세 분석
- 이상치 탐지 (anomaly detection)
- 단기 예측 (1-4주)

---

## 구현 상태

### ✅ 완료 (Python 측)

1. **Python 클라이언트**: `apps/seedtest_api/app/clients/r_forecast.py`
   - `fit_prophet()`: Prophet 모델 적합 및 예측

2. **Job**: `apps/seedtest_api/jobs/forecast_prophet.py`
   - 데이터 로드 (weekly_kpi에서 I_t)
   - R 서비스 호출
   - `prophet_fit_meta` 저장
   - `prophet_anomalies` 저장

3. **데이터베이스**: Prophet 관련 테이블 (Alembic migration)
   - `prophet_fit_meta`: 모델 파라미터, changepoints, forecast
   - `prophet_anomalies`: 주차별 이상치 (주차, value, expected, anomaly_score)

4. **CronJob**: `portal_front/ops/k8s/cron/forecast-prophet.yaml`
   - 매주 월요일 05:00 UTC 실행

---

## R 서비스 구현 필요

### r-forecast-plumber 엔드포인트

#### `/prophet/fit`

**입력**:
```json
{
  "data": [
    {
      "ds": "2025-01-01",
      "y": 0.5
    },
    {
      "ds": "2025-01-08",
      "y": 0.6
    }
  ],
  "forecast_periods": 4,
  "detect_anomalies": true,
  "anomaly_threshold": 2.5
}
```

**출력**:
```json
{
  "forecast": [
    {
      "ds": "2025-02-05",
      "yhat": 0.65,
      "yhat_lower": 0.55,
      "yhat_upper": 0.75
    }
  ],
  "anomalies": [
    {
      "ds": "2025-01-15",
      "y": 0.8,
      "yhat": 0.55,
      "anomaly_score": 3.2
    }
  ],
  "changepoints": [
    "2025-01-10",
    "2025-01-20"
  ],
  "fit_meta": {
    "trend": "increasing",
    "seasonality": "weekly",
    "changepoint_prior_scale": 0.05
  }
}
```

---

## R 구현 예시

### R 코드 (Plumber)

```r
# Load required packages
library(prophet)
library(dplyr)

#* @post /prophet/fit
function(req, res) {
  data <- req$body$data
  forecast_periods <- req$body$forecast_periods %||% 4
  detect_anomalies <- req$body$detect_anomalies %||% TRUE
  anomaly_threshold <- req$body$anomaly_threshold %||% 2.5
  
  df <- as.data.frame(data)
  df$ds <- as.Date(df$ds)
  df$y <- as.numeric(df$y)
  
  # Fit Prophet model
  model <- prophet(df, changepoint.prior.scale = 0.05)
  
  # Create future dataframe
  future <- make_future_dataframe(model, periods = forecast_periods, freq = "week")
  
  # Forecast
  forecast <- predict(model, future)
  
  # Detect anomalies
  anomalies <- list()
  if (detect_anomalies) {
    df <- df %>%
      left_join(forecast %>% select(ds, yhat, yhat_lower, yhat_upper), by = "ds") %>%
      mutate(
        residual = y - yhat,
        residual_sd = sd(residual, na.rm = TRUE),
        z_score = residual / residual_sd,
        is_anomaly = abs(z_score) > anomaly_threshold
      ) %>%
      filter(is_anomaly) %>%
      mutate(anomaly_score = abs(z_score))
    
    anomalies <- df %>%
      select(ds, y, yhat, anomaly_score) %>%
      rename(week_start = ds) %>%
      as.list()
  }
  
  # Extract changepoints
  changepoints <- model$changepoints %>% as.character()
  
  list(
    forecast = forecast %>%
      tail(forecast_periods) %>%
      select(ds, yhat, yhat_lower, yhat_upper) %>%
      mutate_all(as.character) %>%
      as.list(),
    anomalies = anomalies,
    changepoints = changepoints,
    fit_meta = list(
      trend = ifelse(mean(diff(forecast$trend)) > 0, "increasing", "decreasing"),
      seasonality = "weekly",
      changepoint_prior_scale = 0.05
    )
  )
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
python3 -m apps.seedtest_api.jobs.forecast_prophet --dry-run

# 실제 실행
python3 -m apps.seedtest_api.jobs.forecast_prophet \
  --lookback-weeks 12 \
  --forecast-weeks 4 \
  --anomaly-threshold 2.5
```

### Kubernetes Job 실행

```bash
# CronJob으로부터 수동 Job 생성
kubectl -n seedtest create job --from=cronjob/forecast-prophet \
  forecast-prophet-test-$(date +%s)

# 직접 Job 실행
kubectl apply -f portal_front/ops/k8s/jobs/forecast-prophet-now.yaml

# 로그 확인
kubectl -n seedtest logs job/forecast-prophet-now -f
```

### CronJob 배포

```bash
# CronJob 생성
kubectl apply -f portal_front/ops/k8s/cron/forecast-prophet.yaml

# CronJob 확인
kubectl -n seedtest get cronjob forecast-prophet
```

---

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `R_FORECAST_BASE_URL` | `http://r-forecast-plumber.seedtest.svc.cluster.local:80` | R Forecast 서비스 URL |
| `R_FORECAST_TIMEOUT_SECS` | `300` | 요청 타임아웃 (초) |
| `R_FORECAST_INTERNAL_TOKEN` | (없음) | 내부 인증 토큰 (선택) |
| `PROPHET_LOOKBACK_WEEKS` | `12` | 학습 데이터 lookback 기간 (주) |
| `PROPHET_FORECAST_WEEKS` | `4` | 예측 기간 (주) |
| `PROPHET_ANOMALY_THRESHOLD` | `2.5` | 이상치 탐지 Z-score 임계값 |

---

## 데이터 흐름

1. **데이터 로드**:
   - `weekly_kpi`: 주차별 I_t 값
   - 최소 4주 데이터 필요

2. **모델 적합**:
   - Prophet 모델 적합
   - Changepoint 탐지
   - 계절성 및 추세 분석
   - R 서비스 호출: `/prophet/fit`

3. **결과 저장**:
   - `prophet_fit_meta`: 모델 파라미터, changepoints, forecast
   - `prophet_anomalies`: 이상치 (주차, value, expected, anomaly_score)

4. **활용**:
   - 리포트에 예측 추세 및 이상치 표시
   - 조기 경고 시스템 연동

---

## 검증

### 데이터베이스 검증

```sql
-- 최근 예측 결과 확인
SELECT 
    run_id,
    metric,
    jsonb_array_length(forecast) AS forecast_periods,
    jsonb_array_length(changepoints) AS changepoint_count,
    fitted_at
FROM prophet_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- 이상치 확인
SELECT 
    run_id,
    week_start,
    metric,
    value,
    expected,
    anomaly_score,
    detected_at
FROM prophet_anomalies
ORDER BY detected_at DESC
LIMIT 10;

-- 예측값 확인 (forecast JSONB에서 추출)
SELECT 
    run_id,
    jsonb_array_elements(forecast) AS forecast_period
FROM prophet_fit_meta
WHERE run_id = (SELECT run_id FROM prophet_fit_meta ORDER BY fitted_at DESC LIMIT 1);
```

---

## 문제 해결

### 데이터 부족

```
[WARN] Insufficient I_t data for Prophet fitting (need >= 4 weeks)
```

**해결**:
1. `PROPHET_LOOKBACK_WEEKS` 증가
2. `weekly_kpi` 데이터 확인

### R 서비스 연결 실패

**해결**:
1. `R_FORECAST_BASE_URL` 확인
2. r-forecast-plumber 서비스 상태 확인
3. 네트워크 정책 확인

---

## 다음 단계

1. **R 서비스 구현**: r-forecast-plumber `/prophet/fit` 엔드포인트
2. **테스트**: 실제 데이터로 검증
3. **리포트 통합**: 주간 리포트에 예측 추세 및 이상치 반영

---

**Prophet 시계열 예측 구현 준비 완료!** 🎯

