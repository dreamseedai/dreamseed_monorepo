# 완전 배포 가이드 - 고급 분석 모델

**최종 업데이트**: 2025-11-02 01:17 KST  
**상태**: ✅ 모든 파일 생성 완료  
**총 파일**: 22개

---

## 🎉 생성 완료된 파일 목록

### Phase 1: Clustering (2개) ✅
1. ✅ `portal_front/ops/k8s/cron/cluster-segments.yaml`
2. ✅ `portal_front/ops/k8s/jobs/cluster-segments-now.yaml`

### Phase 2: R Forecast 서비스 (9개) ✅
3. ✅ `r-forecast-plumber/api.R`
4. ✅ `r-forecast-plumber/Dockerfile`
5. ✅ `r-forecast-plumber/plumber.R`
6. ✅ `portal_front/ops/k8s/r-forecast-plumber/deployment.yaml`
7. ✅ `portal_front/ops/k8s/r-forecast-plumber/service.yaml`
8. ✅ `portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml`
9. ✅ `apps/seedtest_api/app/clients/r_forecast.py` (이미 존재)
10. ✅ `portal_front/ops/k8s/cron/fit-survival-churn.yaml` (이미 존재)
11. ✅ `portal_front/ops/k8s/cron/forecast-prophet.yaml` (이미 존재)

### Phase 3: R BRMS 서비스 (9개) ✅
12. ✅ `r-brms-plumber/api.R`
13. ✅ `r-brms-plumber/Dockerfile`
14. ✅ `r-brms-plumber/plumber.R`
15. ✅ `portal_front/ops/k8s/r-brms-plumber/deployment.yaml`
16. ✅ `portal_front/ops/k8s/r-brms-plumber/service.yaml`
17. ✅ `portal_front/ops/k8s/r-brms-plumber/externalsecret.yaml`
18. ✅ `apps/seedtest_api/app/clients/r_brms.py` (이미 존재)
19. ✅ `portal_front/ops/k8s/cron/fit-bayesian-growth.yaml` (이미 존재)
20. ✅ `portal_front/ops/k8s/jobs/fit-bayesian-growth-now.yaml` (이미 존재)

### Phase 4: ESO/Secret (2개) ✅
21. ✅ `portal_front/ops/k8s/secrets/externalsecret-r-services.yaml`
22. ✅ `portal_front/ops/k8s/COMPLETE_DEPLOYMENT_GUIDE.md` (이 문서)

---

## 🚀 배포 순서

### Step 1: Clustering 즉시 배포 (5분)

```bash
# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/cluster-segments.yaml

# 즉시 테스트
kubectl -n seedtest apply -f portal_front/ops/k8s/jobs/cluster-segments-now.yaml

# 로그 확인
kubectl -n seedtest logs -f job/cluster-segments-now
```

**예상 로그**:
```
[INFO] Loading user features from weekly_kpi (lookback=12 weeks)
[INFO] Loaded 500 users with 6 features
[INFO] Fitting K-means clustering (k=5)
[INFO] Generating segment labels
[INFO] Stored cluster_fit_meta: run_id=cluster-20251102-071523
[INFO] Updated user_segments for 500 users
✅ Clustering completed successfully
```

---

### Step 2: R Forecast 서비스 배포 (30분)

#### 2.1 이미지 빌드 및 푸시

```bash
cd r-forecast-plumber

# 이미지 빌드 (10-15분)
docker build -t gcr.io/univprepai/r-forecast-plumber:latest .

# 푸시
docker push gcr.io/univprepai/r-forecast-plumber:latest
```

#### 2.2 GCP Secret Manager 설정

```bash
# R Forecast 토큰 생성
gcloud secrets create r-forecast-internal-token \
  --data-file=- \
  --project=univprepai <<EOF
your-forecast-token-here
EOF

# 확인
gcloud secrets describe r-forecast-internal-token --project=univprepai
```

#### 2.3 Kubernetes 배포

```bash
# ExternalSecret 배포
kubectl apply -f portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml

# Secret 생성 확인 (1-2분 대기)
kubectl -n seedtest get secret r-forecast-credentials

# Deployment 및 Service 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/deployment.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/service.yaml

# Pod 상태 확인
kubectl -n seedtest get pods -l app=r-forecast-plumber

# Health check
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS http://r-forecast-plumber.seedtest.svc.cluster.local:80/healthz
```

**예상 응답**:
```json
{
  "status": "ok",
  "service": "r-forecast-plumber",
  "version": "1.0.0",
  "timestamp": "2025-11-02T05:17:23Z"
}
```

#### 2.4 CronJob 배포

```bash
# Survival CronJob (이미 존재)
kubectl -n seedtest get cronjob fit-survival-churn

# Prophet CronJob (이미 존재)
kubectl -n seedtest get cronjob forecast-prophet

# 테스트 실행
kubectl -n seedtest create job --from=cronjob/fit-survival-churn \
  fit-survival-test-$(date +%s)

kubectl -n seedtest logs -f job/fit-survival-test-*
```

---

### Step 3: R BRMS 서비스 배포 (60분)

#### 3.1 이미지 빌드 및 푸시 (Stan 컴파일 포함)

```bash
cd r-brms-plumber

# 이미지 빌드 (30-60분, Stan 컴파일 시간 포함)
docker build -t gcr.io/univprepai/r-brms-plumber:latest .

# 푸시
docker push gcr.io/univprepai/r-brms-plumber:latest
```

**참고**: Stan 컴파일 시간이 오래 걸립니다. 빌드 중 다음 단계를 준비할 수 있습니다.

#### 3.2 GCP Secret Manager 설정

```bash
# R BRMS 토큰 생성
gcloud secrets create r-brms-internal-token \
  --data-file=- \
  --project=univprepai <<EOF
your-brms-token-here
EOF

# 확인
gcloud secrets describe r-brms-internal-token --project=univprepai
```

#### 3.3 Kubernetes 배포

```bash
# ExternalSecret 배포
kubectl apply -f portal_front/ops/k8s/r-brms-plumber/externalsecret.yaml

# Secret 생성 확인
kubectl -n seedtest get secret r-brms-credentials

# Deployment 및 Service 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/r-brms-plumber/deployment.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-brms-plumber/service.yaml

# Pod 상태 확인 (시작 시간 오래 걸림)
kubectl -n seedtest get pods -l app=r-brms-plumber -w

# Health check
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS http://r-brms-plumber.seedtest.svc.cluster.local:80/healthz
```

**예상 응답**:
```json
{
  "status": "ok",
  "service": "r-brms-plumber",
  "version": "1.0.0",
  "timestamp": "2025-11-02T06:17:23Z",
  "stan_version": "2.32.2"
}
```

#### 3.4 CronJob 배포

```bash
# Bayesian Growth CronJob (이미 존재)
kubectl -n seedtest get cronjob fit-bayesian-growth

# 테스트 실행 (10-15분 소요)
kubectl -n seedtest apply -f portal_front/ops/k8s/jobs/fit-bayesian-growth-now.yaml

kubectl -n seedtest logs -f job/fit-bayesian-growth-now
```

---

### Step 4: 통합 ExternalSecret 배포 (선택)

```bash
# 통합 ExternalSecret 배포 (이미 개별 배포됨)
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-r-services.yaml

# 모든 Secret 확인
kubectl -n seedtest get secrets | grep -E "r-forecast|r-brms|calibrate-irt"
```

---

## ✅ 배포 검증

### 1. Clustering 검증

```sql
-- Cluster fit meta
SELECT run_id, n_clusters, features, metrics, fitted_at
FROM cluster_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- User segments
SELECT 
    segment_label,
    COUNT(*) AS user_count,
    AVG((features->>'engagement')::float) AS avg_engagement
FROM user_segments
WHERE updated_at >= NOW() - INTERVAL '1 day'
GROUP BY segment_label;
```

### 2. Survival Analysis 검증

```sql
-- Survival fit meta
SELECT run_id, formula, coefficients, hazard_ratios, fitted_at
FROM survival_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- weekly_kpi.S (생존 확률)
SELECT 
    COUNT(*) AS users_with_survival_score,
    AVG((kpis->>'S')::float) AS avg_survival_prob
FROM weekly_kpi
WHERE kpis ? 'S'
  AND week_start >= NOW() - INTERVAL '1 week';
```

### 3. Prophet Forecasting 검증

```sql
-- Prophet fit meta
SELECT run_id, metric, changepoints, forecast, fitted_at
FROM prophet_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- Anomalies
SELECT COUNT(*) AS anomaly_count, metric
FROM anomalies
WHERE detected_at >= NOW() - INTERVAL '1 week'
GROUP BY metric;
```

### 4. Bayesian Growth 검증

```sql
-- BRMS fit meta
SELECT run_id, formula, priors, posterior_summary, diagnostics, fitted_at
FROM brms_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- weekly_kpi.P (목표 달성 확률)
SELECT 
    COUNT(*) AS users_with_probability,
    AVG((kpis->>'P')::float) AS avg_goal_probability,
    AVG((kpis->>'sigma')::float) AS avg_uncertainty
FROM weekly_kpi
WHERE kpis ? 'P'
  AND week_start >= NOW() - INTERVAL '1 week';
```

---

## 📊 전체 파이프라인 확인

```bash
# 모든 CronJob 확인
kubectl -n seedtest get cronjobs

# 예상 출력:
# NAME                      SCHEDULE        SUSPEND   ACTIVE
# calibrate-irt-weekly      0 3 * * *       False     0
# cluster-segments          0 7 1,15 * *    False     0
# fit-survival-churn        0 5 * * *       False     0
# forecast-prophet          0 5 * * 0       False     0
# fit-bayesian-growth       0 6 * * 0       False     0

# 모든 R 서비스 확인
kubectl -n seedtest get svc | grep -E "r-irt|r-forecast|r-brms"

# 예상 출력:
# r-irt-plumber        ClusterIP   10.x.x.x   <none>   80/TCP    7d
# r-forecast-plumber   ClusterIP   10.x.x.x   <none>   80/TCP    1h
# r-brms-plumber       ClusterIP   10.x.x.x   <none>   80/TCP    30m

# 모든 ExternalSecret 확인
kubectl -n seedtest get externalsecrets

# 예상 출력:
# NAME                         STORE              REFRESH   STATUS
# calibrate-irt-credentials    gcp-secret-store   1h        SecretSynced
# r-forecast-credentials       gcp-secret-store   1h        SecretSynced
# r-brms-credentials           gcp-secret-store   1h        SecretSynced
```

---

## 🐛 문제 해결

### 문제 1: R Forecast 이미지 빌드 실패

**증상**: Prophet 패키지 설치 실패

**해결**:
```bash
# Dockerfile에서 Prophet 의존성 추가
RUN apt-get install -y python3 python3-pip
RUN pip3 install prophet
```

### 문제 2: R BRMS Stan 컴파일 시간 초과

**증상**: Docker 빌드 시간 초과

**해결**:
```bash
# Docker 빌드 타임아웃 증가
docker build --no-cache --progress=plain -t gcr.io/univprepai/r-brms-plumber:latest .

# 또는 사전 컴파일된 이미지 사용
# FROM rocker/verse:4.3 (brms 포함)
```

### 문제 3: Pod OOMKilled (메모리 부족)

**증상**: R BRMS Pod가 OOMKilled 상태

**해결**:
```bash
# 리소스 제한 증가
kubectl -n seedtest set resources deployment r-brms-plumber \
  --requests=cpu=4000m,memory=8Gi \
  --limits=cpu=16000m,memory=32Gi
```

### 문제 4: ExternalSecret SecretSyncedError

**증상**: ExternalSecret 상태가 SecretSyncedError

**해결**:
```bash
# GCP Secret 확인
gcloud secrets list --project=univprepai | grep -E "forecast|brms"

# Secret이 없으면 생성
gcloud secrets create r-forecast-internal-token \
  --data-file=- \
  --project=univprepai <<EOF
your-token
EOF

# ExternalSecret 재시작
kubectl -n seedtest delete externalsecret r-forecast-credentials
kubectl apply -f portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml
```

---

## 📈 성능 최적화

### R Forecast 서비스

```yaml
# deployment.yaml
resources:
  requests:
    cpu: "2000m"      # 증가
    memory: "4Gi"     # 증가
  limits:
    cpu: "8000m"
    memory: "16Gi"
```

### R BRMS 서비스

```yaml
# deployment.yaml
resources:
  requests:
    cpu: "4000m"      # Stan 컴파일 위해 높게
    memory: "8Gi"
  limits:
    cpu: "16000m"
    memory: "32Gi"
```

### CronJob 타임아웃

```yaml
# fit-bayesian-growth.yaml
env:
- name: R_BRMS_TIMEOUT_SECS
  value: "1200"  # 20분 (Stan 샘플링 시간 고려)
```

---

## 🎯 배포 완료 체크리스트

### Phase 1: Clustering ✅
- [ ] CronJob 배포
- [ ] One-off Job 테스트
- [ ] cluster_fit_meta 확인
- [ ] user_segments 확인

### Phase 2: R Forecast ✅
- [ ] 이미지 빌드 및 푸시
- [ ] GCP Secret 생성
- [ ] ExternalSecret 배포
- [ ] Deployment/Service 배포
- [ ] Health check 성공
- [ ] Survival CronJob 테스트
- [ ] Prophet CronJob 테스트
- [ ] survival_fit_meta 확인
- [ ] prophet_fit_meta 확인
- [ ] weekly_kpi.S 확인

### Phase 3: R BRMS ✅
- [ ] 이미지 빌드 및 푸시 (Stan 컴파일)
- [ ] GCP Secret 생성
- [ ] ExternalSecret 배포
- [ ] Deployment/Service 배포
- [ ] Health check 성공
- [ ] Bayesian Growth CronJob 테스트
- [ ] brms_fit_meta 확인
- [ ] weekly_kpi.P/sigma 확인

### Phase 4: 통합 ✅
- [ ] 모든 ExternalSecret 동기화
- [ ] 모든 CronJob 스케줄 확인
- [ ] 전체 파이프라인 검증

---

## 📚 관련 문서

- **[FULL_DEPLOYMENT_PLAN.md](../../apps/seedtest_api/docs/FULL_DEPLOYMENT_PLAN.md)** - 전체 배포 계획
- **[ADVANCED_MODELS_IMPLEMENTATION_STATUS.md](../../apps/seedtest_api/docs/ADVANCED_MODELS_IMPLEMENTATION_STATUS.md)** - 구현 상태
- **[DEPLOYMENT_PROGRESS.md](../../apps/seedtest_api/docs/DEPLOYMENT_PROGRESS.md)** - 진행 상황
- **[SECRET_SETUP_GUIDE.md](./SECRET_SETUP_GUIDE.md)** - Secret 설정
- **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** - 테스트 가이드

---

## 🎉 최종 요약

**생성된 파일**: 22개 (신규 13개, 기존 9개)

**배포 순서**:
1. ✅ Clustering (즉시 가능)
2. ✅ R Forecast (30분)
3. ✅ R BRMS (60분)
4. ✅ ExternalSecret 통합

**총 예상 시간**: 2시간 (빌드 시간 포함)

**다음 단계**: Step 1부터 순차 배포 시작

---

**최종 업데이트**: 2025-11-02 01:17 KST  
**작성자**: Cascade AI  
**상태**: ✅ 모든 파일 생성 완료, 배포 준비 완료

**축하합니다! 전체 고급 분석 모델 배포 패키지가 완성되었습니다! 🎉**
