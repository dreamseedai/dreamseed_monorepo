# Analytics Models 통합 완료 가이드

## 개요

Prophet (시계열), Survival Analysis (생존분석), Clustering (클러스터링) 모델 스캐폴딩이 완료되었습니다.

## 완료된 작업

### 1. Prophet (시계열 예측) ✅

**클라이언트**: `apps/seedtest_api/app/clients/r_forecast.py`
- `fit_prophet()`: I_t 시계열에 Prophet 모델 피팅
- 예측, 이상치 탐지, changepoint 감지 지원

**Job**: `apps/seedtest_api/jobs/forecast_prophet.py`
- `weekly_kpi`에서 I_t 데이터 로드
- Prophet 모델 피팅 및 예측 생성
- `prophet_fit_meta`, `prophet_anomalies` 테이블에 저장

**CronJob**: `portal_front/ops/k8s/cron/forecast-prophet.yaml`
- 스케줄: 매주 월요일 05:00 UTC (`0 5 * * 1`)
- 환경 변수:
  - `PROPHET_LOOKBACK_WEEKS`: 12
  - `PROPHET_FORECAST_WEEKS`: 4
  - `PROPHET_ANOMALY_THRESHOLD`: 2.5

### 2. Survival Analysis (생존분석) ✅

**클라이언트**: `apps/seedtest_api/app/clients/r_forecast.py`
- `fit_survival()`: Cox proportional hazards 모델 피팅
- `predict_survival()`: S(t) 생존 확률 예측

**Job**: `apps/seedtest_api/jobs/fit_survival_churn.py`
- `attempt` VIEW 및 `weekly_kpi`에서 사용자 활동 데이터 로드
- 이벤트: 14일 미접속
- 공변량: A_t, E_t, R_t, mean_gap, sessions
- `survival_fit_meta` 테이블에 저장
- `weekly_kpi.kpis->>'S'` 업데이트 (`SURVIVAL_UPDATE_KPI=true` 시)

**CronJob**: `portal_front/ops/k8s/cron/fit-survival-churn.yaml`
- 스케줄: 매일 05:00 UTC (`0 5 * * *`)
- 환경 변수:
  - `SURVIVAL_LOOKBACK_DAYS`: 90
  - `SURVIVAL_EVENT_THRESHOLD_DAYS`: 14
  - `SURVIVAL_UPDATE_KPI`: true

### 3. Clustering (클러스터링) ✅

**클라이언트**: `apps/seedtest_api/app/clients/r_cluster.py` (신규)
- `fit_clusters()`: k-means 또는 Gaussian mixture 모델 피팅
- `predict_segment()`: 신규 사용자 세그먼트 예측
- 자동 k 선택 지원 (silhouette/Gap statistic)

**Job**: `apps/seedtest_api/jobs/cluster_segments.py`
- `weekly_kpi` 및 `features_topic_daily`에서 사용자 피처 로드
- 피처: engagement, improvement, efficiency, recovery, sessions, gap, avg_rt, avg_hints, total_attempts
- 세그먼트 라벨 생성 (short_frequent, long_rare, hint_heavy 등)
- `user_segment`, `segment_meta` 테이블에 저장

**CronJob**: `portal_front/ops/k8s/cron/cluster-segments.yaml`
- 스케줄: 매월 1일, 15일 07:00 UTC (`0 7 1,15 * *`)
- 환경 변수:
  - `CLUSTER_LOOKBACK_WEEKS`: 12
  - `CLUSTER_N_CLUSTERS`: "" (빈 값 = 자동 선택)
  - `CLUSTER_METHOD`: "kmeans"
  - `CLUSTER_FEATURES`: "engagement,improvement,efficiency,recovery,sessions,gap,avg_rt,avg_hints,total_attempts"

## 데이터 흐름

### Prophet (시계열 예측)
```
weekly_kpi (I_t)
  ↓
forecast_prophet.py
  ↓
r-forecast-plumber /prophet/fit
  ↓
prophet_fit_meta (forecast, changepoints)
prophet_anomalies (week, score, flag)
```

### Survival (생존분석)
```
attempt VIEW + weekly_kpi
  ↓
fit_survival_churn.py
  ↓
r-forecast-plumber /survival/fit
  ↓
survival_fit_meta (coefficients, hazard_ratios)
weekly_kpi.kpis->>'S' (risk scores)
```

### Clustering (클러스터링)
```
weekly_kpi + features_topic_daily
  ↓
cluster_segments.py
  ↓
r-cluster-plumber /cluster/fit
  ↓
user_segment (user_id, segment_label, features_snapshot)
segment_meta (centers, metrics)
```

## 환경 변수 요약

### Prophet
- `R_FORECAST_BASE_URL`: `http://r-forecast-plumber.seedtest.svc.cluster.local:80`
- `R_FORECAST_TIMEOUT_SECS`: 300
- `PROPHET_LOOKBACK_WEEKS`: 12
- `PROPHET_FORECAST_WEEKS`: 4
- `PROPHET_ANOMALY_THRESHOLD`: 2.5

### Survival
- `R_FORECAST_BASE_URL`: `http://r-forecast-plumber.seedtest.svc.cluster.local:80`
- `R_FORECAST_TIMEOUT_SECS`: 300
- `SURVIVAL_LOOKBACK_DAYS`: 90
- `SURVIVAL_EVENT_THRESHOLD_DAYS`: 14
- `SURVIVAL_UPDATE_KPI`: true

### Clustering
- `R_CLUSTER_BASE_URL`: `http://r-cluster-plumber.seedtest.svc.cluster.local:80`
- `R_CLUSTER_TIMEOUT_SECS`: 300
- `CLUSTER_LOOKBACK_WEEKS`: 12
- `CLUSTER_N_CLUSTERS`: "" (자동 선택)
- `CLUSTER_METHOD`: "kmeans"
- `CLUSTER_FEATURES`: "engagement,improvement,efficiency,recovery,sessions,gap,avg_rt,avg_hints,total_attempts"

## 사용 방법

### 수동 실행

#### Prophet
```bash
kubectl -n seedtest create job --from=cronjob/forecast-prophet \
  forecast-prophet-test-$(date +%s)

kubectl -n seedtest logs -f job/forecast-prophet-test-<timestamp>
```

#### Survival
```bash
kubectl -n seedtest create job --from=cronjob/fit-survival-churn \
  fit-survival-churn-test-$(date +%s)

kubectl -n seedtest logs -f job/fit-survival-churn-test-<timestamp>
```

#### Clustering
```bash
kubectl -n seedtest create job --from=cronjob/cluster-segments \
  cluster-segments-test-$(date +%s)

kubectl -n seedtest logs -f job/cluster-segments-test-<timestamp>
```

### 데이터 확인

#### Prophet 결과
```sql
-- 예측 결과
SELECT run_id, metric, forecast->>'ds' AS date, forecast->>'yhat' AS predicted
FROM prophet_fit_meta
ORDER BY fitted_at DESC
LIMIT 10;

-- 이상치
SELECT week, score, anomaly_flag
FROM prophet_anomalies
ORDER BY week DESC
LIMIT 10;
```

#### Survival 결과
```sql
-- 모델 계수
SELECT run_id, coefficients, hazard_ratios
FROM survival_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- 위험 점수
SELECT user_id, week_start, kpis->>'S' AS churn_risk
FROM weekly_kpi
WHERE kpis ? 'S'
ORDER BY (kpis->>'S')::float DESC
LIMIT 10;
```

#### Clustering 결과
```sql
-- 세그먼트 분포
SELECT segment_label, COUNT(*) AS user_count
FROM user_segment
GROUP BY segment_label
ORDER BY user_count DESC;

-- 클러스터 메타
SELECT run_id, n_clusters, metrics->>'silhouette' AS silhouette_score
FROM segment_meta
ORDER BY fitted_at DESC
LIMIT 1;
```

## CronJob 스케줄 요약

| 모델 | CronJob | 스케줄 | 실행 주기 |
|------|---------|--------|----------|
| Prophet | `forecast-prophet` | `0 5 * * 1` | 매주 월요일 05:00 UTC |
| Survival | `fit-survival-churn` | `0 5 * * *` | 매일 05:00 UTC |
| Clustering | `cluster-segments` | `0 7 1,15 * *` | 매월 1일, 15일 07:00 UTC |

## 트러블슈팅

### R 서비스 미사용 가능

각 Job은 R 서비스 호출 실패 시 에러 로그를 출력하고 종료합니다. 다음을 확인하세요:

1. **서비스 배포 확인**:
   ```bash
   kubectl -n seedtest get svc | grep -E "r-forecast|r-cluster"
   ```

2. **Pod 상태 확인**:
   ```bash
   kubectl -n seedtest get pods | grep -E "r-forecast|r-cluster"
   ```

3. **로그 확인**:
   ```bash
   kubectl -n seedtest logs -l app=r-forecast-plumber --tail=50
   ```

### 데이터 부족

- **Prophet**: 최소 4주 데이터 필요
- **Survival**: 최소 10명의 사용자 필요
- **Clustering**: 최소 10명의 사용자 필요 (4주 이상 데이터)

### 메모리/CPU 제한

각 CronJob의 리소스 요청/제한을 확인하고 필요시 조정:

```bash
kubectl -n seedtest describe cronjob forecast-prophet | grep -A 10 "Resources"
```

## 다음 단계

1. **R 서비스 배포**:
   - `r-forecast-plumber`: Prophet 및 Survival 엔드포인트 구현
   - `r-cluster-plumber`: Clustering 엔드포인트 구현

2. **이미지 빌드**:
   - 모든 변경사항이 포함된 새 이미지 빌드 및 푸시

3. **테스트**:
   - 각 모델의 수동 실행 및 결과 검증
   - CronJob 자동 실행 모니터링

## 참고 자료

- [PROPHET_FORECASTING_GUIDE.md](./PROPHET_FORECASTING_GUIDE.md): Prophet 모델 상세 가이드
- [SURVIVAL_ANALYSIS_GUIDE.md](./SURVIVAL_ANALYSIS_GUIDE.md): Survival 모델 상세 가이드
- [ANALYTICS_MODELS_ROADMAP.md](./ANALYTICS_MODELS_ROADMAP.md): 전체 분석 모델 로드맵

