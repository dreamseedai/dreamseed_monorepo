# 최종 구현 체크리스트 및 포맷 확정

## 완료된 항목

### ✅ 1. 의사결정 로직 서비스 (`apps/seedtest_api/services/decision.py`)

**구현 완료**:
- `detect_mastery_gaps()`: θ_mean < 임계값 & θ_sd ≥ 임계값인 토픽 탐지
- `recommend_schedule()`: gap/time 효율 가중점수 기반 일정 추천
- `adaptive_items()`: 적응형 난이도 문항 선별 (P(correct) ≈ target_p)
- `enqueue_churn_alert()`: 이탈 위험 알림 큐에 이벤트 기록

### ✅ 2. Prophet 포맷 합의

**요청 포맷**:
```json
{
  "series": [
    { "week_start": "2025-01-06", "I_t": 0.62 },
    ...
  ],
  "horizon_weeks": 4,
  "anomaly_threshold": 2.5,
  "options": {
    "seasonality_mode": "additive",
    "weekly_seasonality": false,
    "yearly_seasonality": false,
    "changepoint_prior_scale": 0.05,
    "n_changepoints": 5
  }
}
```

**응답 포맷**:
```json
{
  "status": "ok",
  "model_meta": {
    "n_obs": 12,
    "seasonality_mode": "additive",
    "fit_metrics": { "rmse": 0.17, "mae": 0.13 }
  },
  "forecast": [
    {
      "ds": "2025-01-13",
      "type": "insample",
      "yhat": 0.62,
      "yhat_lower": 0.48,
      "yhat_upper": 0.76,
      "actual": 0.60
    },
    {
      "ds": "2025-01-20",
      "type": "forecast",
      "yhat": 0.64,
      "yhat_lower": 0.50,
      "yhat_upper": 0.78
    }
  ],
  "anomalies": [
    {
      "ds": "2025-01-06",
      "actual": 0.40,
      "expected": 0.60,
      "zscore": -2.9,
      "flag": true
    }
  ]
}
```

**확인 사항**: ✅ `forecast` 배열의 `insample`/`forecast` 구분과 `anomalies` 구조 적절함

### ✅ 3. Survival 포맷 합의

**요청 포맷**:
```json
{
  "rows": [
    {
      "user_id": "U123",
      "observed_gap_days": 10,
      "event": 0,
      "sessions_28d": 7,
      "mean_gap_days_28d": 3.2,
      "A_t": 0.62,
      "E_t": 0.44,
      "R_t": 0.31,
      "dwell_seconds_28d": 5400,
      "hints_28d": 6
    }
  ],
  "params": {
    "event_threshold_days": 14,
    "family": "cox"
  }
}
```

**응답 포맷**:
```json
{
  "status": "ok",
  "model_meta": {
    "n": 1245,
    "family": "cox",
    "coefficients": { ... },
    "concordance": 0.71
  },
  "predictions": [
    {
      "user_id": "U123",
      "risk_score": 0.63,
      "hazard_ratio": 1.84,
      "rank_percentile": 0.83
    }
  ],
  "survival_curve": [
    { "t": 0, "S": 1.00 },
    { "t": 7, "S": 0.92 },
    { "t": 14, "S": 0.83 }
  ]
}
```

**확인 사항**: ✅ 공변량 컬럼명 (`sessions_28d`, `mean_gap_days_28d`, `A_t`, `E_t`, `R_t`) 적절함

### ✅ 4. 알림 임계치 기본값

**제안값**:
- `CHURN_ALERT_THRESHOLD`: 0.7 (70% 이상 위험 시 알림)
- `GAP_THETA_THRESHOLD`: -0.5 (θ < -0.5인 토픽)
- `GAP_SD_THRESHOLD`: 0.5 (불확실성 높은 토픽)

**확인 사항**: ✅ 기본값 설정 적절 (조정 가능)

---

## 구현 체크리스트

### 🔲 1. r-forecast-plumber R 구현

**파일**: `r-forecast-plumber/api.R` (또는 `portal_front/r-forecast-plumber/api.R`)

#### `/prophet/fit` 구현

**요구사항**:
- Prophet 모델 피팅 (`prophet::prophet()`)
- 예측 생성 (`prophet::predict()`)
- In-sample 및 Forecast 구분
- 이상 탐지 (z-score 및 예측구간 기반)
- Fit metrics 계산 (RMSE, MAE)

**구현 예시**:
```r
#* @post /prophet/fit
function(req) {
  payload <- req$body
  
  # 데이터 준비
  df <- data.frame(
    ds = as.Date(payload$series$week_start),
    y = payload$series$I_t
  )
  
  # Prophet 모델 피팅
  model <- prophet(df, ...)
  
  # 예측 생성
  future <- make_future_dataframe(model, periods = payload$horizon_weeks, freq = "week")
  forecast_df <- predict(model, future)
  
  # In-sample vs Forecast 구분
  forecast <- list(...)
  
  # 이상 탐지
  anomalies <- detect_anomalies(df, forecast_df, threshold = payload$anomaly_threshold)
  
  # Fit metrics
  fit_metrics <- calculate_metrics(df$y, forecast_df$yhat[1:nrow(df)])
  
  # 응답 구성
  list(
    status = "ok",
    model_meta = list(...),
    forecast = forecast,
    anomalies = anomalies
  )
}
```

#### `/survival/fit` 구현

**요구사항**:
- Cox PH 모델 피팅 (`survival::coxph()`)
- 계수 및 Hazard ratio 계산
- Concordance 계산
- 위험 점수 예측 (0~1 정규화)
- 순위 백분위 계산
- 요약 생존 곡선 생성

**구현 예시**:
```r
#* @post /survival/fit
function(req) {
  payload <- req$body
  
  # 데이터 준비
  df <- data.frame(payload$rows)
  
  # Cox PH 모델
  formula <- Surv(observed_gap_days, event) ~ sessions_28d + mean_gap_days_28d + A_t + E_t + R_t
  model <- coxph(formula, data = df)
  
  # 계수 및 Hazard ratio
  coefficients <- coef(model)
  hazard_ratios <- exp(coefficients)
  
  # Concordance
  concordance <- summary(model)$concordance[1]
  
  # 위험 예측
  predictions <- predict_survival_risk(model, df)
  
  # 생존 곡선
  survival_curve <- calculate_survival_curve(model, df)
  
  # 응답 구성
  list(
    status = "ok",
    model_meta = list(...),
    predictions = predictions,
    survival_curve = survival_curve
  )
}
```

### 🔲 2. Python Job 마무리

#### `fit_survival_churn.py` 구현

**요구사항**:
1. 공변량 집계 (session, attempt, weekly_kpi에서)
2. R 서비스 호출 (`RForecastClient.survival_fit()`)
3. `survival_fit_meta` 저장
4. `survival_risk` 테이블 업데이트 (신규)
5. `weekly_kpi.S` 갱신

**구현 포인트**:
- 입력 변환: 현재 구현 → 제안된 포맷 (`observed_gap_days`, `sessions_28d`, 등)
- 출력 처리: `predictions` 배열에서 개별 사용자 위험 점수 추출
- 트랜잭션: `survival_fit_meta`, `survival_risk`, `weekly_kpi` 업데이트를 하나의 트랜잭션으로

### 🔲 3. Weekly Report 보강

**파일**: `reports/quarto/weekly_report.qmd`

**추가 섹션**:
1. **베이지안 신뢰대역/게이지**
   - Posterior 분포 시각화
   - 95% CI 표시
   - P(goal|state) 게이지

2. **Prophet 예측/이상치 플롯**
   - I_t 추세 + 예측 밴드
   - 이상치 빨간 점 표시
   - 예측구간 시각화

3. **Survival 위험 게이지/백분위**
   - 개인 위험 점수 게이지
   - 집단 내 순위 백분위
   - 요약 생존 곡선

**데이터 로딩**: ✅ 이미 `generate_weekly_report.py`에 함수 추가됨

---

## 임계치 기본값 제안

### 의사결정 로직 임계치

| 임계치 | 기본값 | 설명 |
|--------|--------|------|
| `CHURN_ALERT_THRESHOLD` | 0.7 | 이탈 위험 알림 임계값 (0~1) |
| `GAP_THETA_THRESHOLD` | -0.5 | 마스터리 갭 탐지 θ 임계값 |
| `GAP_SD_THRESHOLD` | 0.5 | 마스터리 갭 탐지 불확실성 임계값 |
| `ADAPTIVE_TARGET_P` | 0.7 | 적응형 문항 선별 목표 정답률 |
| `ADAPTIVE_BANDWIDTH` | 0.1 | 적응형 문항 선별 허용 범위 |

### Prophet 임계치

| 임계치 | 기본값 | 설명 |
|--------|--------|------|
| `PROPHET_ANOMALY_THRESHOLD` | 2.5 | 이상 탐지 z-score 임계값 |
| `PROPHET_MIN_OBS` | 4 | 최소 관측치 수 |

### Survival 임계치

| 임계치 | 기본값 | 설명 |
|--------|--------|------|
| `SURVIVAL_EVENT_THRESHOLD_DAYS` | 14 | 이탈 이벤트 정의 (일) |
| `SURVIVAL_MIN_OBS` | 50 | 최소 관측치 수 |

---

## 구현 순서 (권장)

1. **Alembic 마이그레이션**: `survival_risk` 테이블 추가 (✅ 이미 생성됨)
2. **r-forecast-plumber R 구현**: `/prophet/fit`, `/survival/fit` 엔드포인트
3. **Python 클라이언트 조정**: 포맷 정합 확인
4. **fit_survival_churn.py**: 입력 변환 및 저장 로직 구현
5. **weekly_report.qmd**: 시각화 섹션 추가
6. **테스트 및 검증**: 스모크 테스트 실행

---

## 확인 포인트 (최종)

### ✅ Prophet 응답 구조

**확인 완료**: `forecast` 배열의 구조 적절함
- `type`: "insample" | "forecast" 구분 명확
- `yhat_lower`, `yhat_upper`: 불확실성 밴드 제공
- `anomalies`: zscore 및 flag 필드 포함

### ✅ Survival 입력 공변량

**확인 완료**: 컬럼명 및 정의 적절함
- `sessions_28d`: 최근 28일간 세션 수
- `mean_gap_days_28d`: 최근 28일간 평균 접속 간격
- `A_t`, `E_t`, `R_t`: 주간 KPI 구성 요소
- `dwell_seconds_28d`, `hints_28d`: 선택적 공변량

### ✅ 알림 임계치 기본값

**확인 완료**: 기본값 설정 적절함
- `CHURN_ALERT_THRESHOLD=0.7`: 상위 30% 위험군 알림
- 환경 변수로 조정 가능

---

## 다음 액션

모든 포맷과 임계치가 확정되었으므로 다음 순서로 구현 진행:

1. **r-forecast-plumber R 구현**
2. **fit_survival_churn.py 완성**
3. **weekly_report.qmd 보강**
4. **통합 테스트**

준비 완료입니다. 바로 구현을 진행하시겠습니까?

