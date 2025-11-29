# 베이지안(BRMS) Metrics 통합 완료 상태

## 개요

베이지안(brms) 모델을 metrics 시스템에 통합하여 목표 달성 확률 P(goal|state)를 posterior 기반으로 계산합니다.

## 완료된 통합

### 1. 데이터 흐름

```
┌─────────────────────────────────┐
│ fit-bayesian-growth (CronJob)  │
│ 매주 월요일 04:30 UTC           │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ fit_bayesian_growth.py          │
│ - 데이터 로드 (mirt_ability 등) │
│ - R BRMS 서비스 호출            │
│ - predictions 생성              │
└────────────┬────────────────────┘
             │
             ▼ (BRMS_UPDATE_KPI=true)
┌─────────────────────────────────┐
│ weekly_kpi.kpis->>'P'           │
│ weekly_kpi.kpis->>'sigma'       │
└────────────┬────────────────────┘
             │
             ▼ (실시간 계산 시)
┌─────────────────────────────────┐
│ metrics.py                      │
│ compute_goal_attainment_prob() │
│ - weekly_kpi.P 우선 확인        │
│ - 없으면 growth_brms_meta 기반  │
│ - 폴백: Normal approximation    │
└─────────────────────────────────┘
```

### 2. 구현 세부사항

#### A. `fit_bayesian_growth.py` (주기적 실행)

**역할**: 주기적으로 베이지안 모델을 피팅하고 `weekly_kpi.P`를 업데이트

**프로세스**:
1. 12주 데이터 로드 (mirt_ability → student_topic_theta → features_topic_daily → weekly_kpi)
2. R BRMS 서비스 호출: `POST /growth/fit`
   - 모델: `score ~ week + (week|student_id)`
   - Priors: Normal(intercept/week), Cauchy(sd) - 소표본/잡음 안정화
   - MCMC: 2000 samples, 4 chains
3. 결과 저장:
   - `growth_brms_meta`: posterior_summary, diagnostics
   - `weekly_kpi.P`: predictions에서 각 사용자별 목표 달성 확률
   - `weekly_kpi.sigma`: 불확실성 (σ)

**환경 변수**:
- `BRMS_LOOKBACK_WEEKS`: 12 (기본값)
- `BRMS_N_SAMPLES`: 2000
- `BRMS_N_CHAINS`: 4
- `BRMS_UPDATE_KPI`: true (weekly_kpi 업데이트 여부)

#### B. `metrics.py` `compute_goal_attainment_probability()` (실시간 계산)

**역할**: 주간 KPI 계산 시 목표 달성 확률을 계산

**전략** (`METRICS_USE_BAYESIAN=true` 시):
1. **우선순위 1**: `weekly_kpi.kpis->>'P'` 확인 (fit_bayesian_growth가 이미 계산)
2. **우선순위 2**: `growth_brms_meta`에서 최신 posterior 로드 → R BRMS client로 계산
3. **폴백**: Normal approximation (R 서비스 미사용 가능 시)

**폴백** (`METRICS_USE_BAYESIAN=false` 또는 베이지안 경로 실패 시):
- Normal approximation: `P = 1 - Φ((target - μ) / σ)`

#### C. `calculate_and_store_weekly_kpi()` (주간 KPI 계산)

**현재 구조**:
- `compute_goal_attainment_probability()` 호출
- `METRICS_USE_BAYESIAN=true`면 자동으로 베이지안 경로 사용
- 이미 `weekly_kpi.P`가 있으면 재사용 (fit_bayesian_growth가 계산한 값)

## 환경 변수 설정

### fit-bayesian-growth CronJob
```yaml
env:
  - name: R_BRMS_BASE_URL
    value: "http://r-brms-plumber.seedtest.svc.cluster.local:80"
  - name: BRMS_LOOKBACK_WEEKS
    value: "12"
  - name: BRMS_N_SAMPLES
    value: "2000"
  - name: BRMS_N_CHAINS
    value: "4"
  - name: BRMS_UPDATE_KPI
    value: "true"  # weekly_kpi.P 업데이트
```

### compute-daily-kpis / metrics 계산
```yaml
env:
  - name: METRICS_USE_BAYESIAN
    value: "true"  # 베이지안 경로 활성화
  - name: METRICS_DEFAULT_TARGET
    value: "0.0"  # 기본 목표 점수
```

## 사용 시나리오

### 시나리오 1: 주기적 업데이트 (권장)

1. **매주 월요일 04:30**: `fit-bayesian-growth` CronJob 실행
   - 최근 12주 데이터로 모델 피팅
   - 모든 사용자에 대해 `weekly_kpi.P` 업데이트

2. **평일 02:10**: `compute-daily-kpis` 실행
   - `METRICS_USE_BAYESIAN=true`면 이미 저장된 `weekly_kpi.P` 사용
   - 추가 계산 없이 빠른 응답

**장점**: 효율적, 일관된 확률 계산

### 시나리오 2: 실시간 계산

1. **주간 KPI 계산 시**: `calculate_and_store_weekly_kpi()` 호출
   - `METRICS_USE_BAYESIAN=true`면:
     - `weekly_kpi.P` 확인 → 없으면 `growth_brms_meta` 기반 계산
   - R 서비스 미사용 가능 시 Normal approximation 폴백

**장점**: 최신 모델 기반 실시간 계산

## 검증 방법

### 1. 베이지안 모델 피팅 확인
```bash
# CronJob 수동 실행
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth \
  fit-bayesian-growth-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/fit-bayesian-growth-test-<timestamp>
```

### 2. weekly_kpi.P 확인
```sql
-- 베이지안 확률이 저장된 사용자 확인
SELECT user_id, week_start, kpis->>'P' AS goal_probability, kpis->>'sigma' AS uncertainty
FROM weekly_kpi
WHERE kpis ? 'P'
ORDER BY week_start DESC
LIMIT 10;

-- 최신 주간 피팅 결과
SELECT run_id, fitted_at, posterior_summary->'week' AS week_effect
FROM growth_brms_meta
ORDER BY fitted_at DESC
LIMIT 1;
```

### 3. 실시간 계산 테스트
```python
from apps.seedtest_api.services.metrics import compute_goal_attainment_probability
from apps.seedtest_api.services.db import get_session

# 베이지안 모드로 확률 계산
import os
os.environ["METRICS_USE_BAYESIAN"] = "true"

with get_session() as s:
    prob = compute_goal_attainment_probability(s, "user-123", target=150.0)
    print(f"Goal probability: {prob}")
```

## 트러블슈팅

### 문제 1: weekly_kpi.P가 업데이트되지 않음

**원인**:
- `BRMS_UPDATE_KPI=false`로 설정
- `predictions`가 비어있음 (R 서비스가 반환하지 않음)

**해결**:
```bash
# CronJob 환경 변수 확인
kubectl -n seedtest get cronjob fit-bayesian-growth -o yaml | grep BRMS_UPDATE_KPI

# 로그에서 predictions 확인
kubectl -n seedtest logs <pod-name> | grep "Predictions computed"
```

### 문제 2: 베이지안 경로가 작동하지 않음

**원인**:
- `METRICS_USE_BAYESIAN=false` 또는 미설정
- R BRMS 서비스 미사용 가능
- `growth_brms_meta` 테이블이 비어있음

**해결**:
```bash
# 환경 변수 확인
echo $METRICS_USE_BAYESIAN

# R 서비스 상태 확인
kubectl -n seedtest get svc r-brms-plumber

# growth_brms_meta 확인
psql $DATABASE_URL -c "SELECT COUNT(*) FROM growth_brms_meta;"
```

### 문제 3: Normal approximation으로 폴백됨

**원인**: R BRMS 서비스 호출 실패 (네트워크, 타임아웃 등)

**해결**:
- 로그 확인: `logger.debug(f"Bayesian path failed, using Normal fallback: {e}")`
- R 서비스 로그 확인: `kubectl -n seedtest logs -l app=r-brms-plumber`

**정상 동작**: 베이지안 경로 실패 시 자동으로 Normal approximation 사용

## 다음 단계

1. **R 서비스 배포**: `r-brms-plumber` 이미지 빌드 및 배포
2. **모니터링**: CronJob 실행 모니터링 및 에러 알림 설정
3. **성능 최적화**: 필요한 경우 모델 피팅 주기 조정 (현재: 주 1회)

## 참고 자료

- [BRMS_METRICS_INTEGRATION.md](./BRMS_METRICS_INTEGRATION.md): 통합 가이드
- [BAYESIAN_GROWTH_GUIDE.md](./BAYESIAN_GROWTH_GUIDE.md): BRMS 모델 상세 가이드
- [BRMS_INTEGRATION_COMPLETE.md](./BRMS_INTEGRATION_COMPLETE.md): 완료 요약

