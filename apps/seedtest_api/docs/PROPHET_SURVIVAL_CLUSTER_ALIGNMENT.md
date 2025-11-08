# Prophet/Survival/Cluster 환경 변수 정합 가이드

## 개요

Prophet, Survival, Cluster 모델의 환경 변수 이름이 Job 파일과 CronJob 매니페스트 간에 정합되어 있는지 확인합니다.

## 환경 변수 정합 상태

### ✅ Prophet (forecast_prophet.py)

**Job 파일**: `apps/seedtest_api/jobs/forecast_prophet.py`
- `PROPHET_LOOKBACK_WEEKS` (기본값: 12)
- `PROPHET_FORECAST_WEEKS` (기본값: 4)
- `PROPHET_ANOMALY_THRESHOLD` (기본값: 2.5)

**CronJob**: `portal_front/ops/k8s/cron/forecast-prophet.yaml`
- `PROPHET_LOOKBACK_WEEKS=12`
- `PROPHET_FORECAST_WEEKS=4`
- `PROPHET_ANOMALY_THRESHOLD=2.5`

**상태**: ✅ 정합 완료

### ✅ Survival (fit_survival_churn.py)

**Job 파일**: `apps/seedtest_api/jobs/fit_survival_churn.py`
- `SURVIVAL_LOOKBACK_DAYS` (기본값: 90)
- `SURVIVAL_EVENT_THRESHOLD_DAYS` (기본값: 14)
- `SURVIVAL_UPDATE_KPI` (기본값: true)

**CronJob**: `portal_front/ops/k8s/cron/fit-survival-churn.yaml`
- `SURVIVAL_LOOKBACK_DAYS=90`
- `SURVIVAL_EVENT_THRESHOLD_DAYS=14`
- `SURVIVAL_UPDATE_KPI=true`

**상태**: ✅ 정합 완료

### ✅ Cluster (cluster_segments.py)

**Job 파일**: `apps/seedtest_api/jobs/cluster_segments.py`
- `CLUSTER_LOOKBACK_WEEKS` (기본값: 12)
- `CLUSTER_N_CLUSTERS` (기본값: None, 자동 선택)
- `CLUSTER_METHOD` (기본값: "kmeans")
- `CLUSTER_FEATURES` (기본값: 전체 피처 리스트)

**CronJob**: `portal_front/ops/k8s/cron/cluster-segments.yaml`
- `CLUSTER_LOOKBACK_WEEKS=12`
- `CLUSTER_N_CLUSTERS=""` (빈 값 = 자동 선택)
- `CLUSTER_METHOD=kmeans`
- `CLUSTER_FEATURES=engagement,improvement,efficiency,recovery,sessions,gap,avg_rt,avg_hints,total_attempts`

**상태**: ✅ 정합 완료

## R 서비스 클라이언트

### ✅ r_forecast.py (Prophet/Survival)

**파일**: `apps/seedtest_api/app/clients/r_forecast.py`

**구현 완료**:
- `fit_prophet()`: `/prophet/fit` 엔드포인트 호출
- `fit_survival()`: `/survival/fit` 엔드포인트 호출
- `predict_survival()`: `/survival/predict` 엔드포인트 호출

### ✅ r_cluster.py (Cluster)

**파일**: `apps/seedtest_api/app/clients/r_cluster.py`

**구현 완료**:
- `fit_clusters()`: `/cluster/fit` 엔드포인트 호출
- `predict_segment()`: `/cluster/predict` 엔드포인트 호출

## CronJob 스케줄

| 모델 | CronJob | 스케줄 | 상태 |
|------|---------|--------|------|
| Prophet | `forecast-prophet` | `0 5 * * 1` (매주 월요일 05:00 UTC) | ✅ 설정 완료 |
| Survival | `fit-survival-churn` | `0 5 * * *` (매일 05:00 UTC) | ✅ 설정 완료 |
| Cluster | `cluster-segments` | `0 7 1,15 * *` (매월 1일, 15일 07:00 UTC) | ✅ 설정 완료 |

## 검증 방법

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

## 다음 단계

### 완료된 작업
- [x] Prophet Job 및 CronJob 구현 및 정합
- [x] Survival Job 및 CronJob 구현 및 정합
- [x] Cluster Job 및 CronJob 구현 및 정합
- [x] R 서비스 클라이언트 구현

### 남은 작업
- [ ] r-forecast-plumber R 서비스 구현 (`/prophet/fit`, `/survival/fit` 등)
- [ ] r-cluster-plumber R 서비스 구현 (`/cluster/fit`) 또는 r-forecast-plumber에 포함
- [ ] Docker 이미지 빌드 및 배포
- [ ] E2E 테스트 및 검증

## 참고

모든 환경 변수는 Job 파일과 CronJob 매니페스트 간에 정합되어 있습니다. 추가 정합 작업이 필요하지 않습니다.

