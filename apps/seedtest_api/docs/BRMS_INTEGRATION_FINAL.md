# 베이지안(BRMS) 통합 최종 완료 상태

## 완료된 작업

### 1. ✅ fit_bayesian_growth.py 구현

**파일**: `apps/seedtest_api/jobs/fit_bayesian_growth.py`

**기능**:
- 최근 `LOOKBACK_WEEKS` (기본 8주) 동안 `attempt` VIEW에서 주간 정답률 추출
- 입력 스키마: `[{student: str, week: int, score: float}]`
- `r-brms-plumber` `/growth/fit` 호출
- `growth_brms_meta` 테이블에 posterior JSON 저장

**환경 변수** (기본값):
- `LOOKBACK_WEEKS=8` (또는 `BRMS_LOOKBACK_WEEKS`)
- `BRMS_ITER=1000` (또는 `BRMS_N_SAMPLES`)
- `BRMS_CHAINS=2` (또는 `BRMS_N_CHAINS`)
- `BRMS_FAMILY=gaussian`

### 2. ✅ metrics 통합

**파일**: `apps/seedtest_api/services/metrics.py`

**기능**:
- `compute_goal_attainment_probability()`: `METRICS_USE_BAYESIAN=true` 시 베이지안 경로
- `r-brms-plumber.predict_prob()` 호출로 posterior 기반 확률 계산
- 폴백: Normal approximation
- `calculate_and_store_weekly_kpi()`: P를 위 함수로 계산

### 3. ✅ CronJob 연결

**파일**: `portal_front/ops/k8s/cron/fit-bayesian-growth.yaml`

**설정**:
- 스케줄: 매주 월요일 04:30 UTC
- 실행: `python -m apps.seedtest_api.jobs.fit_bayesian_growth`
- 환경 변수:
  - `BRMS_LOOKBACK_WEEKS=12` (Cron에서는 12주 사용)
  - `BRMS_N_SAMPLES=1000`
  - `BRMS_N_CHAINS=2`
  - `BRMS_FAMILY=gaussian`

### 4. ✅ 환경 변수 정합

**호환성**:
- `BRMS_LOOKBACK_WEEKS` 또는 `LOOKBACK_WEEKS` 지원
- `BRMS_N_SAMPLES` 또는 `BRMS_ITER` 지원
- `BRMS_N_CHAINS` 또는 `BRMS_CHAINS` 지원
- `BRMS_FAMILY` 지원 (기본값: `gaussian`)

## 데이터 흐름

```
attempt VIEW (주간 정답률)
  ↓
fit_bayesian_growth.py
  ↓
r-brms-plumber /growth/fit
  ↓
growth_brms_meta (posterior 저장)
  ↓
weekly_kpi.P (predictions 기반 업데이트)
  ↓
metrics.py compute_goal_attainment_probability()
  ↓
METRICS_USE_BAYESIAN=true 시 베이지안 확률 사용
```

## 기본값 설정

### Job 기본값 (fit_bayesian_growth.py)
- `LOOKBACK_WEEKS=8`
- `BRMS_ITER=1000`
- `BRMS_CHAINS=2`
- `BRMS_FAMILY=gaussian`

### CronJob 기본값 (fit-bayesian-growth.yaml)
- `BRMS_LOOKBACK_WEEKS=12` (더 긴 기간)
- `BRMS_N_SAMPLES=1000`
- `BRMS_N_CHAINS=2`
- `BRMS_FAMILY=gaussian`

## 운영 체크리스트

### ✅ 완료
- [x] fit_bayesian_growth.py 생성
- [x] metrics 통합 (METRICS_USE_BAYESIAN 플래그)
- [x] CronJob 매니페스트 설정
- [x] 환경 변수 정합 (양쪽 이름 지원)

### 🔄 다음 단계
- [ ] r-brms-plumber 이미지 빌드 및 푸시
- [ ] seedtest-api Deployment에 `METRICS_USE_BAYESIAN=true` 추가 (이미 완료됨)
- [ ] 테스트 및 검증

## 테스트 방법

### 수동 실행
```bash
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth \
  fit-brms-test-$(date +%s)

kubectl -n seedtest logs -f job/fit-brms-test-<timestamp>
```

### 데이터 확인
```sql
-- growth_brms_meta 확인
SELECT run_id, fitted_at, posterior_summary->'week' AS week_effect
FROM growth_brms_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- weekly_kpi.P 확인
SELECT user_id, week_start, kpis->>'P' AS goal_probability
FROM weekly_kpi
WHERE kpis ? 'P'
ORDER BY week_start DESC
LIMIT 10;
```

## 참고 자료

- [BRMS_ENV_VARS_ALIGNMENT.md](./BRMS_ENV_VARS_ALIGNMENT.md): 환경 변수 정합 가이드
- [BRMS_METRICS_INTEGRATION.md](./BRMS_METRICS_INTEGRATION.md): Metrics 통합 가이드
- [BAYESIAN_METRICS_INTEGRATION_COMPLETE.md](./BAYESIAN_METRICS_INTEGRATION_COMPLETE.md): 통합 완료 상태

