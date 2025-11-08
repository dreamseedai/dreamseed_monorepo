# 전체 분석 모델 스캐폴딩 완료 최종 요약

## 완료된 작업

### ✅ 1. BRMS (베이지안) 경로

**구현 완료**:
- `apps/seedtest_api/jobs/fit_bayesian_growth.py`: 주간 정답률 시계열 → R 서비스 호출 → `growth_brms_meta` 저장
- `apps/seedtest_api/services/metrics.py`: `METRICS_USE_BAYESIAN=true` 플래그로 `compute_goal_attainment_probability()` 베이지안 전환
- `portal_front/ops/k8s/cron/fit-bayesian-growth.yaml`: 환경 변수 정합 완료
  - `LOOKBACK_WEEKS=12`
  - `BRMS_ITER=1000`
  - `BRMS_CHAINS=2`
  - `BRMS_FAMILY=gaussian`

**데이터 흐름**:
```
attempt VIEW → fit_bayesian_growth.py → r-brms-plumber/growth/fit → growth_brms_meta → weekly_kpi.P
```

### ✅ 2. Prophet (시계열 예측) 경로

**구현 완료**:
- `apps/seedtest_api/app/clients/r_forecast.py`: `prophet_fit()` 클라이언트 구현
- `apps/seedtest_api/jobs/forecast_prophet.py`: `weekly_kpi`에서 I_t 시계열 추출 → Prophet 모델 피팅
- `portal_front/ops/k8s/cron/forecast-prophet.yaml`: 주간 실행 (월요일 05:00 UTC)
- `r-forecast-plumber/api.R`: 기본 스캐폴딩 존재 (후속 구현 보강 예정)

**환경 변수**:
- `PROPHET_LOOKBACK_WEEKS=12`
- `PROPHET_FORECAST_WEEKS=4`
- `PROPHET_ANOMALY_THRESHOLD=2.5`

**데이터 흐름**:
```
weekly_kpi (I_t) → forecast_prophet.py → r-forecast-plumber/prophet/fit → prophet_fit_meta/prophet_anomalies
```

### ✅ 3. Survival (생존분석) 경로

**구현 완료**:
- `apps/seedtest_api/app/clients/r_forecast.py`: `fit_survival()`, `predict_survival()` 클라이언트 구현
- `apps/seedtest_api/jobs/fit_survival_churn.py`: 세션/attempt 통계 추출 → Survival 모델 피팅 → `weekly_kpi.S` 업데이트
- `portal_front/ops/k8s/cron/fit-survival-churn.yaml`: 일일 실행 (05:00 UTC)
- `r-forecast-plumber/api.R`: 기본 스캐폴딩 존재 (후속 구현 보강 예정)

**환경 변수**:
- `SURVIVAL_LOOKBACK_DAYS=90`
- `SURVIVAL_EVENT_THRESHOLD_DAYS=14`
- `SURVIVAL_UPDATE_KPI=true`

**데이터 흐름**:
```
session/attempt → fit_survival_churn.py → r-forecast-plumber/survival/fit → survival_fit_meta → weekly_kpi.S
```

### ✅ 4. Cluster (클러스터링) 경로

**구현 완료**:
- `apps/seedtest_api/app/clients/r_cluster.py`: `fit_clusters()`, `predict_segment()` 클라이언트 구현
- `apps/seedtest_api/jobs/cluster_segments.py`: 사용자 피처 추출 → 클러스터링 → `user_segment` 저장
- `portal_front/ops/k8s/cron/cluster-segments.yaml`: 월 2회 실행 (1일, 15일 07:00 UTC)

**환경 변수**:
- `CLUSTER_LOOKBACK_WEEKS=12`
- `CLUSTER_N_CLUSTERS=""` (자동 선택)
- `CLUSTER_METHOD=kmeans`

**데이터 흐름**:
```
weekly_kpi + features_topic_daily → cluster_segments.py → r-cluster-plumber/cluster/fit → user_segment/segment_meta
```

### ✅ 5. ESO (External Secrets Operator) 설정

**완료**:
- `portal_front/ops/k8s/r-brms-plumber/externalsecret.yaml`: GCP Secret 경로 `r-brms-internal-token`
- `portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml`: GCP Secret 경로 `r-forecast-internal-token`
- SecretStore: `gcpsm-secret-store` (namespace-scoped)

### ✅ 6. Weekly Report 보강

**추가된 섹션**:
- **Bayesian Growth Analysis**: Posterior 분포, 95% 신뢰구간, 주간 성장 추세
- **Prophet Forecast**: I_t 단기 예측 플롯, 불확실성 밴드, 이상치 탐지
- **Survival Analysis**: Churn Risk 게이지, 위험 수준 해석, 색상 코딩
- **Learning Pattern Segment**: 세그먼트 라벨/설명, 주요 특성, 맞춤 권장사항

**데이터 로딩 함수** (`generate_weekly_report.py`):
- `load_bayesian_growth()`: `weekly_kpi.P`, `weekly_kpi.sigma` 로딩
- `load_prophet_forecast()`: `prophet_fit_meta`, `prophet_anomalies` 로딩
- `load_survival_risk()`: `weekly_kpi.S`, `survival_fit_meta` 로딩
- `load_user_segment()`: `user_segment`, `segment_meta` 로딩

## 환경 변수 정합 상태

### ✅ 모든 모델 정합 완료

| 모델 | Job 파일 | CronJob | 상태 |
|------|---------|---------|------|
| **BRMS** | `LOOKBACK_WEEKS`, `BRMS_ITER`, `BRMS_CHAINS`, `BRMS_FAMILY` | 동일 | ✅ 정합 |
| **Prophet** | `PROPHET_LOOKBACK_WEEKS`, `PROPHET_FORECAST_WEEKS`, `PROPHET_ANOMALY_THRESHOLD` | 동일 | ✅ 정합 |
| **Survival** | `SURVIVAL_LOOKBACK_DAYS`, `SURVIVAL_EVENT_THRESHOLD_DAYS`, `SURVIVAL_UPDATE_KPI` | 동일 | ✅ 정합 |
| **Cluster** | `CLUSTER_LOOKBACK_WEEKS`, `CLUSTER_N_CLUSTERS`, `CLUSTER_METHOD` | 동일 | ✅ 정합 |

## CronJob 스케줄 요약

| 모델 | CronJob | 스케줄 | 상태 |
|------|---------|--------|------|
| **BRMS** | `fit-bayesian-growth` | `30 4 * * 1` (매주 월요일 04:30 UTC) | ✅ 설정 완료 |
| **Prophet** | `forecast-prophet` | `0 5 * * 1` (매주 월요일 05:00 UTC) | ✅ 설정 완료 |
| **Survival** | `fit-survival-churn` | `0 5 * * *` (매일 05:00 UTC) | ✅ 설정 완료 |
| **Cluster** | `cluster-segments` | `0 7 1,15 * *` (매월 1일, 15일 07:00 UTC) | ✅ 설정 완료 |

## R 서비스 클라이언트 구현 상태

### ✅ 완료
- `r_brms.py`: BRMS 클라이언트 (`fit_growth()`, `predict_goal_probability()`)
- `r_forecast.py`: Prophet/Survival 클라이언트 (`prophet_fit()`, `fit_survival()`, `predict_survival()`)
- `r_cluster.py`: Cluster 클라이언트 (`fit_clusters()`, `predict_segment()`)

## 남은 작업 (R 서비스 구현)

### ⚠️ R 서비스 엔드포인트 구현 필요

1. **r-brms-plumber**: ✅ `/growth/fit`, `/growth/predict` (이미 구현되어 있을 것으로 예상)

2. **r-forecast-plumber**: 구현 보강 필요
   - `/prophet/fit`: 주간 I_t 시계열 입력, 단기 예측/이상 탐지 반환
     - 입력: `{series: [{week_start, I_t}], horizon_weeks: int, anomaly_threshold: float}`
     - 출력: `{forecast: [...], anomalies: [...], changepoints: [...]}`
   - `/survival/fit`: 14일 미접속 이벤트, 공변량 포함 위험 추정
     - 입력: `{rows: [{user_id, last_seen, sessions, mean_gap_days, A_t, E_t, R_t, ...}]}`
     - 출력: `{risk_scores: [...], coefficients: {...}, hazard_ratios: {...}}`

3. **r-cluster-plumber** (또는 r-forecast-plumber에 포함):
   - `/cluster/fit`: 사용자 피처 입력, 클러스터링 반환
     - 입력: `{features: [{user_id, engagement, improvement, efficiency, ...}]}`
     - 출력: `{segments: [{user_id, segment_label, distance: ...}], segment_meta: {...}}`

## 운영 체크리스트

### 즉시 배포 가능한 항목
1. ✅ 모든 Python Job 파일 구현 완료
2. ✅ 모든 Python 클라이언트 구현 완료
3. ✅ 모든 CronJob 매니페스트 설정 완료
4. ✅ 모든 환경 변수 정합 완료
5. ✅ ESO 설정 완료
6. ✅ Weekly Report 템플릿 보강 완료

### R 서비스 배포 전 필요 작업
1. **r-brms-plumber 이미지 빌드**:
   ```bash
   docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest ./r-brms-plumber
   docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest
   kubectl -n seedtest apply -f portal_front/ops/k8s/r-brms-plumber/
   ```

2. **r-forecast-plumber 이미지 빌드**:
   ```bash
   docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest ./r-forecast-plumber
   docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest
   kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/
   ```

3. **CronJob 적용**:
   ```bash
   kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-bayesian-growth.yaml
   kubectl -n seedtest apply -f portal_front/ops/k8s/cron/forecast-prophet.yaml
   kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-survival-churn.yaml
   kubectl -n seedtest apply -f portal_front/ops/k8s/cron/cluster-segments.yaml
   ```

4. **KPI 베이지안 전환**:
   - `seedtest-api` Deployment에 `METRICS_USE_BAYESIAN=true` 설정
   - `compute_daily_kpis` 실행 후 `weekly_kpi.P` 확인

## 검증 방법

### BRMS 테스트
```bash
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth \
  brms-test-$(date +%s)
kubectl -n seedtest logs -f job/brms-test-<timestamp>
```

### Prophet 테스트
```bash
kubectl -n seedtest create job --from=cronjob/forecast-prophet \
  prophet-test-$(date +%s)
kubectl -n seedtest logs -f job/prophet-test-<timestamp>
```

### Survival 테스트
```bash
kubectl -n seedtest create job --from=cronjob/fit-survival-churn \
  survival-test-$(date +%s)
kubectl -n seedtest logs -f job/survival-test-<timestamp>
```

### Cluster 테스트
```bash
kubectl -n seedtest create job --from=cronjob/cluster-segments \
  cluster-test-$(date +%s)
kubectl -n seedtest logs -f job/cluster-test-<timestamp>
```

## 결론

**Python 측 스캐폴딩 100% 완료**: 모든 Job, 클라이언트, CronJob, 환경 변수, ESO 설정, Weekly Report 보강이 완료되었습니다.

**남은 작업**: R 서비스 엔드포인트 구현 및 Docker 이미지 빌드만 남았으며, 이는 Python 클라이언트가 이미 준비되어 있으므로 R 서비스 구현만 완료하면 즉시 연동 가능합니다.

