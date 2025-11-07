# BRMS Metrics Integration Guide

## 개요

베이지안 성장 모델(Bayesian Growth Model, BRMS)을 `metrics.py`의 `compute_goal_attainment_probability` 함수에 통합하여 목표 달성 확률 P(goal|state)를 계산합니다.

## 아키텍처

### 데이터 흐름

```
fit_bayesian_growth.py (CronJob)
  ↓
  growth_brms_meta 테이블에 posterior_summary 저장
  ↓
  weekly_kpi.kpis->>'P' 업데이트 (BRMS_UPDATE_KPI=true 시)
  ↓
  metrics.py compute_goal_attainment_probability()
  ↓
  METRICS_USE_BAYESIAN=true:
    - weekly_kpi에서 P 직접 사용 (우선순위 1)
    - 또는 growth_brms_meta에서 posterior 로드 후 R client로 계산 (우선순위 2)
    - 폴백: Normal approximation
```

## 환경 변수

### fit-bayesian-growth CronJob
- `BRMS_LOOKBACK_WEEKS`: 12 (기본값)
- `BRMS_N_SAMPLES`: 2000 (기본값)
- `BRMS_N_CHAINS`: 4 (기본값)
- `BRMS_UPDATE_KPI`: true (weekly_kpi에 P/σ 업데이트)

### metrics.py 전환
- `METRICS_USE_BAYESIAN`: true/false (기본: false)
  - `true`: 베이지안 경로 사용 (weekly_kpi 또는 growth_brms_meta 기반)
  - `false`: Normal approximation만 사용

## 구현 세부사항

### 1. `compute_goal_attainment_probability()` 전략

```python
if METRICS_USE_BAYESIAN=true:
    1. weekly_kpi.kpis->>'P' 확인 (fit_bayesian_growth가 이미 계산한 값)
    2. 없으면 growth_brms_meta에서 최신 posterior 로드
    3. R BRMS client로 P(goal|state) 계산
    4. 폴백: Normal approximation
else:
    Normal approximation만 사용
```

### 2. `fit_bayesian_growth.py` 저장 로직

- `growth_brms_meta` 테이블:
  - `run_id`: 실행 ID
  - `posterior_summary`: JSONB (후驗 분포 요약)
  - `diagnostics`: JSONB (수렴 진단)
  
- `weekly_kpi` 업데이트 (`BRMS_UPDATE_KPI=true`):
  - `kpis->>'P'`: 목표 달성 확률
  - `kpis->>'sigma'`: 불확실성 (σ)

## 사용법

### CronJob 활성화

```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-bayesian-growth.yaml
```

### 베이지안 모드 활성화

`compute-daily-kpis` CronJob 또는 관련 서비스에 환경 변수 추가:

```yaml
env:
  - name: METRICS_USE_BAYESIAN
    value: "true"
```

### 수동 테스트

```bash
# 1. Bayesian growth model fitting
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth \
  fit-bayesian-growth-test-$(date +%s)

# 2. KPI 계산 시 베이지안 모드 사용
export METRICS_USE_BAYESIAN=true
python3 -m apps.seedtest_api.jobs.compute_daily_kpis
```

## 검증

### 1. `growth_brms_meta` 확인

```sql
SELECT run_id, fitted_at, posterior_summary->'week' AS week_effect
FROM growth_brms_meta
ORDER BY fitted_at DESC
LIMIT 1;
```

### 2. `weekly_kpi.P` 확인

```sql
SELECT user_id, week_start, kpis->>'P' AS goal_probability, kpis->>'sigma' AS uncertainty
FROM weekly_kpi
WHERE kpis ? 'P'
ORDER BY week_start DESC
LIMIT 10;
```

### 3. 로그 확인

```bash
# fit-bayesian-growth 로그
kubectl -n seedtest logs -l job-name=fit-bayesian-growth --tail=50

# compute-daily-kpis 로그 (METRICS_USE_BAYESIAN=true 시)
kubectl -n seedtest logs -l job-name=compute-daily-kpis --tail=50
```

## 트러블슈팅

### 1. R BRMS 서비스 미사용 가능

- `metrics.py`는 자동으로 Normal approximation으로 폴백합니다.
- 로그에 `"Bayesian path failed, using Normal fallback"` 메시지 확인.

### 2. `growth_brms_meta` 테이블 비어있음

- `fit-bayesian-growth` CronJob이 실행되지 않았을 수 있습니다.
- 수동 실행: `kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth ...`

### 3. `weekly_kpi.P` 값이 없음

- `BRMS_UPDATE_KPI=false`이거나 predictions가 없을 수 있습니다.
- `fit_bayesian_growth.py` 로그에서 `"Updated weekly_kpi.P/sigma for N users"` 확인.

## 참고 자료

- [BAYESIAN_GROWTH_GUIDE.md](./BAYESIAN_GROWTH_GUIDE.md): BRMS 모델 상세 가이드
- [ANALYTICS_MODELS_ROADMAP.md](./ANALYTICS_MODELS_ROADMAP.md): 전체 분석 모델 로드맵

