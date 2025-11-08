# 전체 고급 모델 배포 계획

**최종 업데이트**: 2025-11-02 01:13 KST  
**상태**: 🚀 전체 배포 시작  
**예상 소요 시간**: 8.5시간

---

## 📋 배포 계획 개요

모든 옵션을 순차적으로 배포합니다:

1. ✅ **Clustering CronJob** (30분) - 즉시 배포 가능
2. ⏳ **R Forecast 서비스** (4시간) - Survival + Prophet
3. ⏳ **R BRMS 서비스** (4시간) - Bayesian Growth
4. ⏳ **ESO/Secret 연결** (추가)

---

## 🎯 Phase 1: Clustering CronJob (30분)

### 1.1 CronJob 매니페스트 생성

**파일**: `portal_front/ops/k8s/cron/cluster-segments.yaml`

**스케줄**: 매월 1일, 15일 07:00 UTC

**환경 변수**:
- `CLUSTER_LOOKBACK_WEEKS`: 12
- `CLUSTER_N_CLUSTERS`: 5
- `CLUSTER_METHOD`: kmeans

### 1.2 One-off Job 매니페스트

**파일**: `portal_front/ops/k8s/jobs/cluster-segments-now.yaml`

### 1.3 배포 및 검증

```bash
# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/cluster-segments.yaml

# 테스트 실행
kubectl -n seedtest create job --from=cronjob/cluster-segments \
  cluster-segments-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/cluster-segments-test-*
```

**예상 로그**:
```
[INFO] Loading user features from weekly_kpi (lookback=12 weeks)
[INFO] Loaded 500 users with 6 features
[INFO] Fitting K-means clustering (k=5)
[INFO] Cluster centers computed
[INFO] Generating segment labels
[INFO] Stored cluster_fit_meta: run_id=cluster-20251102-071523
[INFO] Updated user_segments for 500 users
✅ Clustering completed successfully
```

**검증 SQL**:
```sql
-- Cluster fit meta 확인
SELECT run_id, n_clusters, features, metrics, fitted_at
FROM cluster_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- User segments 확인
SELECT 
    segment_label,
    COUNT(*) AS user_count,
    AVG((features->>'engagement')::float) AS avg_engagement,
    AVG((features->>'efficiency')::float) AS avg_efficiency
FROM user_segments
WHERE updated_at >= NOW() - INTERVAL '1 hour'
GROUP BY segment_label
ORDER BY user_count DESC;
```

---

## 🎯 Phase 2: R Forecast 서비스 (4시간)

### 2.1 R Forecast Plumber 서비스 구현 (2시간)

**파일**: `r-forecast-plumber/api.R`

**엔드포인트**:
1. `/survival/fit` - Cox PH 생존분석
2. `/prophet/fit` - Prophet 시계열 예측
3. `/healthz` - 헬스체크

**주요 기능**:
- Survival: `survival::coxph()`, 위험 비율 계산
- Prophet: `prophet::prophet()`, 이상 탐지, changepoints

### 2.2 Dockerfile 생성

**파일**: `r-forecast-plumber/Dockerfile`

**베이스 이미지**: `rocker/r-ver:4.3`

**패키지**:
- plumber
- survival
- prophet
- jsonlite
- dplyr

### 2.3 Kubernetes 배포 (30분)

**파일**:
- `portal_front/ops/k8s/r-forecast-plumber/deployment.yaml`
- `portal_front/ops/k8s/r-forecast-plumber/service.yaml`
- `portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml`

**리소스**:
```yaml
resources:
  requests:
    cpu: "1000m"
    memory: "2Gi"
  limits:
    cpu: "4000m"
    memory: "8Gi"
```

### 2.4 Python Client 구현 (30분)

**파일**: `apps/seedtest_api/app/clients/r_forecast.py`

**클래스**: `RForecastClient`

**메서드**:
- `fit_survival(data, formula, model_type)`
- `fit_prophet(data, forecast_periods, detect_anomalies, anomaly_threshold)`

### 2.5 CronJob 배포 (30분)

**파일**:
- `portal_front/ops/k8s/cron/fit-survival-churn.yaml` (04:00 UTC 매일)
- `portal_front/ops/k8s/cron/forecast-prophet.yaml` (05:00 UTC 매주 일요일)

### 2.6 검증 (30분)

```bash
# R Forecast 서비스 Health check
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS http://r-forecast-plumber.seedtest.svc.cluster.local:80/healthz

# Survival Job 테스트
kubectl -n seedtest create job --from=cronjob/fit-survival-churn \
  fit-survival-test-$(date +%s)

# Prophet Job 테스트
kubectl -n seedtest create job --from=cronjob/forecast-prophet \
  forecast-prophet-test-$(date +%s)
```

**검증 SQL**:
```sql
-- Survival fit meta
SELECT run_id, formula, coefficients, hazard_ratios, fitted_at
FROM survival_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- weekly_kpi.S 확인
SELECT COUNT(*) AS users_with_survival_score
FROM weekly_kpi
WHERE kpis ? 'S'
  AND week_start >= NOW() - INTERVAL '1 week';

-- Prophet fit meta
SELECT run_id, metric, changepoints, forecast, fitted_at
FROM prophet_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- Anomalies 확인
SELECT COUNT(*) AS anomaly_count
FROM anomalies
WHERE detected_at >= NOW() - INTERVAL '1 week';
```

---

## 🎯 Phase 3: R BRMS 서비스 (4시간)

### 3.1 R BRMS Plumber 서비스 구현 (2.5시간)

**파일**: `r-brms-plumber/api.R`

**엔드포인트**:
1. `/growth/fit` - Bayesian 성장 모델
2. `/growth/predict` - 목표 달성 확률 예측
3. `/healthz` - 헬스체크

**주요 기능**:
- BRMS: `brms::brm()`, Stan 컴파일
- Priors: Normal, Cauchy
- Diagnostics: Rhat, ESS

**주의사항**:
- Stan 컴파일 시간 고려 (첫 실행 시 5-10분)
- 높은 메모리 요구 (4-16GB)

### 3.2 Dockerfile 생성

**파일**: `r-brms-plumber/Dockerfile`

**베이스 이미지**: `rocker/r-ver:4.3`

**패키지**:
- plumber
- brms
- rstan
- jsonlite
- dplyr

**빌드 시간**: 30-60분 (Stan 컴파일)

### 3.3 Kubernetes 배포 (30분)

**파일**:
- `portal_front/ops/k8s/r-brms-plumber/deployment.yaml`
- `portal_front/ops/k8s/r-brms-plumber/service.yaml`
- `portal_front/ops/k8s/r-brms-plumber/externalsecret.yaml`

**리소스** (높음):
```yaml
resources:
  requests:
    cpu: "2000m"
    memory: "4Gi"
  limits:
    cpu: "8000m"
    memory: "16Gi"
```

### 3.4 Python Client 구현 (30분)

**파일**: `apps/seedtest_api/app/clients/r_brms.py`

**클래스**: `RBrmsClient`

**메서드**:
- `fit_growth(data, formula, priors, n_samples, n_chains)`
- `predict_goal(data, goal_threshold)`

### 3.5 CronJob 배포 (30분)

**파일**:
- `portal_front/ops/k8s/cron/fit-bayesian-growth.yaml` (06:00 UTC 매주 일요일)

**타임아웃**: 600초 (10분)

### 3.6 검증 (30분)

```bash
# R BRMS 서비스 Health check
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS http://r-brms-plumber.seedtest.svc.cluster.local:80/healthz

# Bayesian Growth Job 테스트
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth \
  fit-bayesian-test-$(date +%s)

# 로그 확인 (Stan 컴파일 메시지 포함)
kubectl -n seedtest logs -f job/fit-bayesian-test-*
```

**예상 로그**:
```
[INFO] Fitting Bayesian growth model (lookback=12 weeks, n_samples=2000, n_chains=4)
[INFO] Loaded 500 users with theta observations
[INFO] Calling R BRMS service...
Compiling Stan model... (this may take a few minutes)
Chain 1: Iteration: 1 / 2000 [ 0%]
Chain 1: Iteration: 500 / 2000 [ 25%]
Chain 1: Iteration: 1000 / 2000 [ 50%]
Chain 1: Iteration: 1500 / 2000 [ 75%]
Chain 1: Iteration: 2000 / 2000 [100%]
[INFO] Posterior summary: {"intercept": {"mean": 0.05, "sd": 0.12}, ...}
[INFO] Diagnostics: {"rhat": {"intercept": 1.01, ...}, "ess": {...}}
[INFO] Updated weekly_kpi.P/sigma for 500 users
✅ Bayesian growth model fitting completed
```

**검증 SQL**:
```sql
-- BRMS fit meta
SELECT run_id, formula, priors, posterior_summary, diagnostics, fitted_at
FROM brms_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- weekly_kpi.P, sigma 확인
SELECT 
    COUNT(*) AS users_with_probability,
    AVG((kpis->>'P')::float) AS avg_probability,
    AVG((kpis->>'sigma')::float) AS avg_uncertainty
FROM weekly_kpi
WHERE kpis ? 'P'
  AND week_start >= NOW() - INTERVAL '1 week';
```

---

## 🎯 Phase 4: ESO/Secret 연결 (추가)

### 4.1 ExternalSecret 매니페스트 생성

**파일**: `portal_front/ops/k8s/secrets/externalsecret-r-services.yaml`

**포함 Secret**:
- `R_FORECAST_INTERNAL_TOKEN`
- `R_BRMS_INTERNAL_TOKEN`

### 4.2 CronJob 업데이트

**파일 업데이트**:
- `calibrate-irt.yaml` → `calibrate-irt-with-externalsecret.yaml` (이미 존재)
- `fit-survival-churn.yaml` → ExternalSecret 참조 추가
- `forecast-prophet.yaml` → ExternalSecret 참조 추가
- `fit-bayesian-growth.yaml` → ExternalSecret 참조 추가

---

## 📊 전체 배포 타임라인

| Phase | 작업 | 소요 시간 | 누적 시간 |
|-------|------|----------|----------|
| **Phase 1** | Clustering CronJob | 30분 | 0.5시간 |
| **Phase 2** | R Forecast 서비스 구현 | 2시간 | 2.5시간 |
| | R Forecast Dockerfile | 30분 | 3시간 |
| | R Forecast K8s 배포 | 30분 | 3.5시간 |
| | Python RForecastClient | 30분 | 4시간 |
| | Survival/Prophet CronJobs | 30분 | 4.5시간 |
| **Phase 3** | R BRMS 서비스 구현 | 2.5시간 | 7시간 |
| | R BRMS Dockerfile | 30분 | 7.5시간 |
| | R BRMS K8s 배포 | 30분 | 8시간 |
| | Python RBrmsClient | 30분 | 8.5시간 |
| **Phase 4** | ESO/Secret 연결 | 30분 | 9시간 |

**총 예상 시간**: 9시간

---

## ✅ 배포 체크리스트

### Phase 1: Clustering (30분)
- [ ] CronJob 매니페스트 생성
- [ ] One-off Job 매니페스트 생성
- [ ] CronJob 배포
- [ ] 테스트 실행
- [ ] 로그 확인
- [ ] 데이터베이스 검증

### Phase 2: R Forecast (4시간)
- [ ] api.R 구현 (/survival/fit, /prophet/fit)
- [ ] Dockerfile 작성
- [ ] 이미지 빌드 및 푸시
- [ ] Deployment 매니페스트 생성
- [ ] Service 매니페스트 생성
- [ ] ExternalSecret 매니페스트 생성
- [ ] K8s 배포
- [ ] Health check 확인
- [ ] RForecastClient 구현
- [ ] Survival CronJob 매니페스트 생성
- [ ] Prophet CronJob 매니페스트 생성
- [ ] CronJob 배포
- [ ] 테스트 실행 (Survival)
- [ ] 테스트 실행 (Prophet)
- [ ] 데이터베이스 검증

### Phase 3: R BRMS (4시간)
- [ ] api.R 구현 (/growth/fit)
- [ ] Dockerfile 작성
- [ ] 이미지 빌드 및 푸시 (Stan 컴파일)
- [ ] Deployment 매니페스트 생성 (높은 리소스)
- [ ] Service 매니페스트 생성
- [ ] ExternalSecret 매니페스트 생성
- [ ] K8s 배포
- [ ] Health check 확인
- [ ] RBrmsClient 구현
- [ ] Bayesian Growth CronJob 매니페스트 생성
- [ ] CronJob 배포
- [ ] 테스트 실행
- [ ] 데이터베이스 검증

### Phase 4: ESO/Secret (30분)
- [ ] ExternalSecret 매니페스트 생성
- [ ] GCP Secret Manager에 토큰 생성
- [ ] ExternalSecret 배포
- [ ] Secret 생성 확인
- [ ] CronJob 업데이트 (ExternalSecret 참조)
- [ ] 재배포 및 검증

---

## 🚀 배포 시작 순서

### 1단계: 즉시 배포 (Clustering)
```bash
# Phase 1 파일 생성
# - ops/k8s/cron/cluster-segments.yaml
# - ops/k8s/jobs/cluster-segments-now.yaml

# 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/cluster-segments.yaml

# 테스트
kubectl -n seedtest create job --from=cronjob/cluster-segments \
  cluster-segments-test-$(date +%s)
```

### 2단계: R Forecast 서비스
```bash
# Phase 2 파일 생성
# - r-forecast-plumber/api.R
# - r-forecast-plumber/Dockerfile
# - r-forecast-plumber/plumber.R
# - ops/k8s/r-forecast-plumber/deployment.yaml
# - ops/k8s/r-forecast-plumber/service.yaml
# - ops/k8s/r-forecast-plumber/externalsecret.yaml
# - apps/seedtest_api/app/clients/r_forecast.py
# - ops/k8s/cron/fit-survival-churn.yaml
# - ops/k8s/cron/forecast-prophet.yaml

# 빌드 및 배포
cd r-forecast-plumber
docker build -t gcr.io/univprepai/r-forecast-plumber:latest .
docker push gcr.io/univprepai/r-forecast-plumber:latest

kubectl -n seedtest apply -f ops/k8s/r-forecast-plumber/
kubectl -n seedtest apply -f ops/k8s/cron/fit-survival-churn.yaml
kubectl -n seedtest apply -f ops/k8s/cron/forecast-prophet.yaml
```

### 3단계: R BRMS 서비스
```bash
# Phase 3 파일 생성
# - r-brms-plumber/api.R
# - r-brms-plumber/Dockerfile
# - r-brms-plumber/plumber.R
# - ops/k8s/r-brms-plumber/deployment.yaml
# - ops/k8s/r-brms-plumber/service.yaml
# - ops/k8s/r-brms-plumber/externalsecret.yaml
# - apps/seedtest_api/app/clients/r_brms.py
# - ops/k8s/cron/fit-bayesian-growth.yaml

# 빌드 및 배포
cd r-brms-plumber
docker build -t gcr.io/univprepai/r-brms-plumber:latest .
docker push gcr.io/univprepai/r-brms-plumber:latest

kubectl -n seedtest apply -f ops/k8s/r-brms-plumber/
kubectl -n seedtest apply -f ops/k8s/cron/fit-bayesian-growth.yaml
```

### 4단계: ESO/Secret 연결
```bash
# Phase 4 파일 생성
# - ops/k8s/secrets/externalsecret-r-services.yaml

# GCP Secret Manager에 토큰 생성
gcloud secrets create r-forecast-internal-token \
  --data-file=- \
  --project=univprepai <<EOF
your-forecast-token
EOF

gcloud secrets create r-brms-internal-token \
  --data-file=- \
  --project=univprepai <<EOF
your-brms-token
EOF

# ExternalSecret 배포
kubectl apply -f ops/k8s/secrets/externalsecret-r-services.yaml

# Secret 확인
kubectl -n seedtest get secret r-forecast-credentials
kubectl -n seedtest get secret r-brms-credentials
```

---

## 📚 생성할 파일 목록 (총 22개)

### Clustering (2개)
1. `portal_front/ops/k8s/cron/cluster-segments.yaml`
2. `portal_front/ops/k8s/jobs/cluster-segments-now.yaml`

### R Forecast (9개)
3. `r-forecast-plumber/api.R`
4. `r-forecast-plumber/Dockerfile`
5. `r-forecast-plumber/plumber.R`
6. `portal_front/ops/k8s/r-forecast-plumber/deployment.yaml`
7. `portal_front/ops/k8s/r-forecast-plumber/service.yaml`
8. `portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml`
9. `apps/seedtest_api/app/clients/r_forecast.py`
10. `portal_front/ops/k8s/cron/fit-survival-churn.yaml`
11. `portal_front/ops/k8s/cron/forecast-prophet.yaml`

### R BRMS (9개)
12. `r-brms-plumber/api.R`
13. `r-brms-plumber/Dockerfile`
14. `r-brms-plumber/plumber.R`
15. `portal_front/ops/k8s/r-brms-plumber/deployment.yaml`
16. `portal_front/ops/k8s/r-brms-plumber/service.yaml`
17. `portal_front/ops/k8s/r-brms-plumber/externalsecret.yaml`
18. `apps/seedtest_api/app/clients/r_brms.py`
19. `portal_front/ops/k8s/cron/fit-bayesian-growth.yaml`
20. `portal_front/ops/k8s/jobs/fit-bayesian-growth-now.yaml`

### ESO/Secret (2개)
21. `portal_front/ops/k8s/secrets/externalsecret-r-services.yaml`
22. `portal_front/ops/k8s/SECRET_MANAGEMENT_GUIDE.md`

---

## 🎯 다음 단계

**즉시 시작**:
1. Phase 1 파일 생성 (Clustering CronJob)
2. Phase 2 파일 생성 (R Forecast 서비스)
3. Phase 3 파일 생성 (R BRMS 서비스)
4. Phase 4 파일 생성 (ESO/Secret)

**순차 배포**:
- Phase 1 → Phase 2 → Phase 3 → Phase 4

---

**최종 업데이트**: 2025-11-02 01:13 KST  
**작성자**: Cascade AI  
**상태**: 🚀 전체 배포 계획 수립 완료, 파일 생성 시작

**다음**: Phase 1 파일 생성 시작
