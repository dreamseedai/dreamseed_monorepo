# Prophet/Survival 포맷 최종 확인

## 확인 포인트 검토

### ✅ 1. Prophet 응답 구조

**제안된 포맷**:
```json
{
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

**확인 사항**:
- ✅ `forecast` 배열의 `insample`/`forecast` 구분: 명확함
- ✅ `yhat_lower`, `yhat_upper`: 불확실성 밴드 제공 적절
- ✅ `anomalies` 배열의 구조: `actual`, `expected`, `zscore`, `flag` 필드 충분함
- ✅ `last_observed_week`: 최근 관측 주차 표시 적절

**결론**: ✅ **포맷 적절, 그대로 구현 진행 가능**

---

### ✅ 2. Survival 입력 공변량 컬럼명/정의

**제안된 포맷**:
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
  ]
}
```

**컬럼명 및 정의 검토**:

| 컬럼명 | 정의 | 타입 | 적절성 |
|--------|------|------|--------|
| `user_id` | 사용자 식별자 | string | ✅ 적절 |
| `observed_gap_days` | 마지막 접속 이후 경과일 | float | ✅ 적절 (소수점 가능) |
| `event` | 14일 이상 미접속 발생 여부 (1/0) | int | ✅ 적절 |
| `sessions_28d` | 최근 28일간 세션 수 | int | ✅ 적절 |
| `mean_gap_days_28d` | 최근 28일간 평균 접속 간격 (일) | float | ✅ 적절 |
| `A_t` | 최근 주간 Engagement 지수 | float | ✅ 적절 (0~1) |
| `E_t` | 최근 주간 Efficiency 지수 | float | ✅ 적절 (0~1) |
| `R_t` | 최근 주간 Recovery 지수 | float | ✅ 적절 (0~1) |
| `dwell_seconds_28d` | 최근 28일간 총 체류 시간 (초) | int | ✅ 적절 (선택) |
| `hints_28d` | 최근 28일간 힌트 사용 횟수 | int | ✅ 적절 (선택) |

**현재 Python Job 매핑** (`fit_survival_churn.py`):
```python
{
    "user_id": r["user_id"],
    "observed_gap_days": r["time"],  # days_since_last
    "event": r["event"],
    "sessions_28d": r["sessions"],
    "mean_gap_days_28d": r["mean_gap"],
    "A_t": r["engagement"],
    "E_t": r["efficiency"],
    "R_t": r["recovery"],
}
```

**확인 사항**:
- ✅ 컬럼명 일관성: `sessions_28d`, `mean_gap_days_28d` 형식 일관
- ✅ 정의 명확성: 각 컬럼의 의미와 단위 명확
- ✅ 선택적 필드: `dwell_seconds_28d`, `hints_28d`는 선택사항으로 적절
- ✅ Python Job 매핑: 현재 구현과 제안 포맷 간 변환 가능

**결론**: ✅ **컬럼명 및 정의 적절, 그대로 구현 진행 가능**

---

### ✅ 3. 알림 임계치 기본값

**제안된 임계치**:

| 임계치 | 기본값 | 설명 | 검토 |
|--------|--------|------|------|
| `CHURN_ALERT_THRESHOLD` | **0.7** | 이탈 위험 알림 임계값 (0~1) | ✅ 상위 30% 위험군 알림 적절 |
| `GAP_THETA_THRESHOLD` | **-0.5** | 마스터리 갭 탐지 θ 임계값 | ✅ 평균 이하 토픽 탐지 적절 |
| `GAP_SD_THRESHOLD` | **0.5** | 마스터리 갭 탐지 불확실성 임계값 | ✅ 불확실성 높은 토픽 탐지 적절 |

**의사결정 로직에서의 사용**:
- `detect_mastery_gaps()`: θ_mean < `GAP_THETA_THRESHOLD` & θ_sd ≥ `GAP_SD_THRESHOLD`
- `enqueue_churn_alert()`: S(t) ≥ `CHURN_ALERT_THRESHOLD` 시 알림 큐에 기록

**제안 사항**:
- 환경 변수로 조정 가능하도록 구현 (예: `DECISION_CHURN_ALERT_THRESHOLD`)
- 운영 데이터에 따라 조정 가능 (초기값: 0.7)

**결론**: ✅ **임계치 기본값 적절, 환경 변수로 조정 가능하도록 구현 권장**

---

## 최종 합의

### ✅ 모든 포맷 및 임계치 확정

1. **Prophet 응답 구조**: ✅ 적절, 그대로 구현
2. **Survival 입력 공변량**: ✅ 컬럼명/정의 적절, 그대로 구현
3. **알림 임계치**: ✅ 기본값 적절, 환경 변수 지원 권장

---

## 구현 진행 가능 항목

다음 항목들을 바로 구현할 수 있습니다:

### 1. r-forecast-plumber R 구현

**파일**: `r-forecast-plumber/api.R` 또는 `portal_front/r-forecast-plumber/api.R`

**구현 내용**:
- `/prophet/fit`: 제안된 포맷대로 구현
  - Prophet 모델 피팅
  - 예측 생성 (insample + forecast 구분)
  - 이상 탐지 (z-score + 예측구간)
  - Fit metrics 계산 (RMSE, MAE)
- `/survival/fit`: 제안된 포맷대로 구현
  - Cox PH 모델 피팅
  - 계수 및 Hazard ratio 계산
  - 위험 점수 예측 (0~1 정규화)
  - 순위 백분위 계산
  - 요약 생존 곡선

### 2. fit_survival_churn.py 완성

**파일**: `apps/seedtest_api/jobs/fit_survival_churn.py`

**구현 내용**:
- 공변량 집계 (현재 구현 → 제안 포맷 변환)
- R 서비스 호출 (`RForecastClient.survival_fit()`)
- `survival_fit_meta` 저장
- `survival_risk` 테이블 업데이트
- `weekly_kpi.S` 갱신

### 3. weekly_report.qmd 보강

**파일**: `reports/quarto/weekly_report.qmd`

**구현 내용**:
- 베이지안 신뢰대역/게이지 (이미 추가됨)
- Prophet 예측/이상치 플롯 (이미 추가됨)
- Survival 위험 게이지/백분위 (이미 추가됨)
- 세그먼트 박스 (이미 추가됨)

---

## 다음 단계

**즉시 구현 가능**:
1. r-forecast-plumber R 구현 (Prophet/Survival)
2. fit_survival_churn.py 완성 (입력 변환 + 저장 로직)
3. 테스트 및 검증

**환경 변수 추가 (선택)**:
- `DECISION_CHURN_ALERT_THRESHOLD=0.7`
- `DECISION_GAP_THETA_THRESHOLD=-0.5`
- `DECISION_GAP_SD_THRESHOLD=0.5`

---

## 결론

**✅ 모든 포맷 및 임계치 확정 완료**

- Prophet 응답 구조: 적절
- Survival 입력 공변량: 적절
- 알림 임계치 기본값: 적절

**바로 구현 진행 가능합니다.**

