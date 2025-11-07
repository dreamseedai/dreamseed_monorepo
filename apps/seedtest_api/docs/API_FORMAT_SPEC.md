# Prophet/Survival API 포맷 명세서

## 1. Prophet 예측/이상 탐지 포맷

### 요청 (r-forecast-plumber `/prophet/fit`)

**Endpoint**: `POST /prophet/fit`

**Payload**:
```json
{
  "series": [
    { "week_start": "2025-01-06", "I_t": 0.62 },
    { "week_start": "2025-01-13", "I_t": 0.58 },
    { "week_start": "2025-01-20", "I_t": 0.65 },
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

**필수 필드**:
- `series`: 최소 4포인트 이상 권장
- `horizon_weeks`: 예측 기간 (기본값: 4)

**선택 필드**:
- `anomaly_threshold`: 이상치 탐지 임계값 (기본값: 2.5)
- `options`: Prophet 모델 파라미터

### 응답

```json
{
  "status": "ok",
  "model_meta": {
    "n_obs": 12,
    "seasonality_mode": "additive",
    "weekly_seasonality": false,
    "yearly_seasonality": false,
    "changepoint_prior_scale": 0.05,
    "n_changepoints": 5,
    "fit_metrics": {
      "rmse": 0.17,
      "mae": 0.13
    }
  },
  "horizon_weeks": 4,
  "last_observed_week": "2025-01-06",
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

### 이상 탐지 규칙

1. **기본**: 잔차(실제-예측)의 표준화 z-score 기준 `|z| >= anomaly_threshold`
2. **보완**: Prophet의 예측구간(`yhat_lower`, `yhat_upper`) 바깥에 위치하면 `flag=true`

### 저장 스키마

**`prophet_fit_meta` 테이블**:
- `run_id` (TEXT, PK): 실행 ID (예: `prophet-2025-01-06T00:00:00Z`)
- `metric` (TEXT): 메트릭 이름 (예: `"I_t"`)
- `changepoints` (JSONB): 변경점 정보
- `forecast` (JSONB): 예측 결과 (전체 forecast 배열)
- `fit_meta` (JSONB): 모델 메타데이터 (`model_meta` 전체)
- `fitted_at` (TIMESTAMPTZ): 피팅 시각

**`prophet_anomalies` 테이블**:
- `run_id` (TEXT): `prophet_fit_meta.run_id` 참조
- `week_start` (DATE): 주차 시작일
- `metric` (TEXT): 메트릭 이름
- `value` (FLOAT): 실제 값 (`actual`)
- `expected` (FLOAT): 예측 값 (`yhat`)
- `anomaly_score` (FLOAT): z-score
- `detected_at` (TIMESTAMPTZ): 탐지 시각
- PK: `(run_id, week_start, metric)`

---

## 2. Survival 입력/출력 스키마 (14일 미접속 이탈 위험)

### 요청 (r-forecast-plumber `/survival/fit`)

**Endpoint**: `POST /survival/fit`

**Payload**:
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
    },
    ...
  ],
  "params": {
    "event_threshold_days": 14,
    "family": "cox",
    "regularization": null
  }
}
```

**필수 필드**:
- `rows`: 사용자별 관측 데이터 배열
  - `user_id`: 사용자 ID
  - `observed_gap_days`: 마지막 접속 이후 경과일
  - `event`: 1이면 14일 이상 미접속 발생, 0이면 미발생
  - `sessions_28d`: 최근 28일간 세션 수
  - `mean_gap_days_28d`: 최근 28일간 평균 접속 간격
  - `A_t`: 최근 주간 Engagement 지수
  - `E_t`: 최근 주간 Efficiency 지수
  - `R_t`: 최근 주간 Recovery 지수

**선택 필드**:
- `dwell_seconds_28d`: 최근 28일간 총 체류 시간 (초)
- `hints_28d`: 최근 28일간 힌트 사용 횟수

### 응답

```json
{
  "status": "ok",
  "model_meta": {
    "n": 1245,
    "family": "cox",
    "event_threshold_days": 14,
    "coefficients": {
      "sessions_28d": -0.18,
      "mean_gap_days_28d": 0.35,
      "A_t": -0.22,
      "E_t": 0.05,
      "R_t": -0.04
    },
    "concordance": 0.71
  },
  "predictions": [
    {
      "user_id": "U123",
      "risk_score": 0.63,
      "hazard_ratio": 1.84,
      "rank_percentile": 0.83
    },
    {
      "user_id": "U456",
      "risk_score": 0.21,
      "hazard_ratio": 0.94,
      "rank_percentile": 0.18
    }
  ],
  "survival_curve": [
    { "t": 0, "S": 1.00 },
    { "t": 7, "S": 0.92 },
    { "t": 14, "S": 0.83 }
  ]
}
```

**응답 필드 설명**:
- `model_meta`: 모델 피팅 메타데이터
  - `n`: 관측치 수
  - `family`: 모델 패밀리 ("cox", "weibull" 등)
  - `event_threshold_days`: 이벤트 임계값
  - `coefficients`: 공변량 계수
  - `concordance`: 모델 성능 지표 (C-index)
- `predictions`: 사용자별 예측 결과
  - `risk_score`: 위험 점수 (0~1, 정규화됨)
  - `hazard_ratio`: 위험 비율
  - `rank_percentile`: 집단 내 위험 순위 백분위 (0~1)
- `survival_curve`: 요약 생존 곡선 (집단 평균)

### 모델/해석

- **기본 모델**: Cox Proportional Hazards (`survival::coxph`)
- **예측**: 공변량 X에 대한 hazard ratio 및 위험 점수
- **곡선**: 집단 평균 S(t) 제공 (리포팅용)

### 저장 스키마

**`survival_fit_meta` 테이블**:
- `run_id` (TEXT, PK): 실행 ID
- `formula` (TEXT): 모델 공식
- `coefficients` (JSONB): 계수 (`model_meta.coefficients`)
- `hazard_ratios` (JSONB): 위험 비율 (계수 기반 계산)
- `fitted_at` (TIMESTAMPTZ): 피팅 시각

**`survival_risk` 테이블** (신규 추가 필요):
- `user_id` (TEXT, PK): 사용자 ID
- `risk_score` (FLOAT): 위험 점수 (0~1)
- `hazard_ratio` (FLOAT): 위험 비율
- `rank_percentile` (FLOAT): 집단 내 순위 백분위 (0~1)
- `updated_at` (TIMESTAMPTZ): 업데이트 시각
- Index: `(user_id, updated_at DESC)`

**`weekly_kpi.S` 업데이트**:
- `weekly_kpi.kpis->>'S'`: 최신 `risk_score` 값 저장
- 일일 갱신 (0~1 범위)

---

## 3. Python 클라이언트 메서드 시그니처

### Prophet

```python
async def prophet_fit(
    self,
    series: List[Dict[str, Any]],  # [{week_start: str, I_t: float}, ...]
    *,
    horizon_weeks: int = 4,
    anomaly_threshold: float = 2.5,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Fit Prophet model and return forecast + anomalies.
    
    Args:
        series: List of {week_start: "YYYY-MM-DD", I_t: float}
        horizon_weeks: Forecast horizon (default: 4)
        anomaly_threshold: Z-score threshold (default: 2.5)
        options: Prophet options (seasonality_mode, weekly_seasonality, etc.)
    
    Returns:
        Dict with status, model_meta, forecast, anomalies
    """
```

### Survival

```python
async def survival_fit(
    self,
    rows: List[Dict[str, Any]],
    *,
    event_threshold_days: int = 14,
    family: str = "cox",
    regularization: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Fit survival model and return predictions + survival curve.
    
    Args:
        rows: List of user data dicts (user_id, observed_gap_days, event, ...)
        event_threshold_days: Event definition threshold (default: 14)
        family: Model family "cox" or "weibull" (default: "cox")
        regularization: Optional regularization params
    
    Returns:
        Dict with status, model_meta, predictions, survival_curve
    """
```

---

## 4. 저장 스키마 비교

### 현재 Alembic 마이그레이션 상태

**`prophet_fit_meta`**: ✅ 존재
- 현재 스키마: `run_id`, `metric`, `changepoints`, `forecast`, `fit_meta`, `fitted_at`
- 제안 포맷과 **호환 가능** (JSONB 필드로 저장)

**`prophet_anomalies`**: ✅ 존재
- 현재 스키마: `run_id`, `week_start`, `metric`, `value`, `expected`, `anomaly_score`, `detected_at`
- 제안 포맷과 **호환 가능**

**`survival_fit_meta`**: ✅ 존재
- 현재 스키마: `run_id`, `formula`, `coefficients`, `hazard_ratios`, `fitted_at`
- 제안 포맷과 **호환 가능** (JSONB 필드로 저장)

**`survival_risk`**: ❌ **추가 필요**
- Alembic 마이그레이션 생성 필요

---

## 5. 조정 사항

### 필요한 수정

1. **`survival_risk` 테이블 추가** (Alembic 마이그레이션)
2. **`r_forecast.py` 클라이언트 메서드 조정**:
   - `prophet_fit()`: 입력 포맷을 `series` (week_start, I_t)로 변경
   - `survival_fit()`: 입력 포맷 확인 및 출력 처리 개선
3. **`forecast_prophet.py` Job 수정**:
   - `prophet_fit()` 사용으로 변경 (현재는 `prophet_predict` 사용)
   - 입력 데이터를 `series` 포맷으로 변환
4. **`fit_survival_churn.py` Job 수정**:
   - 입력 데이터를 제안된 포맷(`observed_gap_days`, `sessions_28d`, 등)으로 변환
   - `survival_risk` 테이블에 예측 결과 저장
   - `weekly_kpi.S` 업데이트

### Weekly Report

✅ **이미 완료**: 베이지안/Prophet/Survival/Segment 블록 모두 추가됨

---

## 6. 구현 우선순위

1. **Alembic 마이그레이션**: `survival_risk` 테이블 추가
2. **R 서비스 구현**: `/prophet/fit`, `/survival/fit` 엔드포인트
3. **Python 클라이언트 수정**: 포맷 정합
4. **Python Job 수정**: 새로운 포맷으로 변환 및 저장
5. **테스트 및 검증**

---

## 7. 참고 사항

- Prophet 포맷에서 `week_start`는 `"YYYY-MM-DD"` 문자열 형식
- Survival 포맷에서 `observed_gap_days`는 실수값 가능 (예: 10.5일)
- `risk_score`는 0~1 범위로 정규화 필요
- `rank_percentile`은 집단 내 순위 백분위 (0~1)

