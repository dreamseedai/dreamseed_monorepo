# 🚀 Advanced Analytics Pipeline - 배포 준비 완료

**최종 업데이트**: 2025-11-02 10:26 KST  
**상태**: ✅ Production Ready

---

## 📦 준비 완료된 컴포넌트

### ✅ 1. 배포 스크립트
- **`portal_front/ops/k8s/deploy-advanced-analytics.sh`** (13KB)
  - 통합 배포 스크립트 (Bayesian/Prophet/Survival)
  - Dry-run 모드 지원
  - 마이그레이션 스킵 옵션
  - 대화형 스모크 테스트

- **`portal_front/ops/k8s/verify-advanced-analytics.sh`** (8.3KB)
  - 자동 검증 스크립트
  - 7단계 체크 (서비스/시크릿/CronJob/헬스/테이블/Job)
  - Pass/Fail 판정

- **`portal_front/ops/k8s/deploy-irt-pipeline.sh`** (4.9KB)
  - IRT 파이프라인 배포 스크립트 (기존)

### ✅ 2. 문서
- **`DEPLOYMENT_CHECKLIST_ADVANCED_ANALYTICS.md`** (16KB)
  - 상세 배포 체크리스트
  - 8단계 배포 절차
  - 스모크 테스트 가이드
  - 트러블슈팅

- **`DEPLOYMENT_SUMMARY.md`** (6.1KB)
  - 한눈에 보는 배포 절차
  - 검증 항목
  - 롤백 절차

- **`PARAMETER_TUNING_GUIDE.md`** (9.3KB)
  - 5가지 시나리오별 파라미터 조정
  - 전체 파라미터 목록
  - 환경별 권장 파라미터

- **`DEPLOYMENT_GUIDE_IRT_PIPELINE.md`** (13KB)
  - IRT 파이프라인 가이드 (기존)

### ✅ 3. K8s 매니페스트
- **CronJobs**:
  - `fit-bayesian-growth.yaml` (Mon 04:30 UTC)
  - `forecast-prophet.yaml` (Mon 05:00 UTC)
  - `fit-survival-churn.yaml` (Daily 05:00 UTC)
  - `compute-daily-kpis.yaml` (Daily 02:10 UTC)

- **ExternalSecrets**:
  - `r-brms-plumber/externalsecret.yaml`
  - `r-forecast-plumber/externalsecret.yaml`

- **R Services**:
  - `r-brms-plumber/deployment.yaml`
  - `r-brms-plumber/service.yaml`
  - `r-forecast-plumber/deployment.yaml`
  - `r-forecast-plumber/service.yaml`

### ✅ 4. Alembic 마이그레이션
- **`20251102_1400_prophet_survival_tables.py`**
  - `prophet_fit_meta`, `prophet_anomalies`
  - `survival_fit_meta`, `survival_risk`

### ✅ 5. Python Jobs
- **`apps/seedtest_api/jobs/fit_bayesian_growth.py`**
- **`apps/seedtest_api/jobs/forecast_prophet.py`**
- **`apps/seedtest_api/jobs/fit_survival_churn.py`**
- **`apps/seedtest_api/jobs/compute_daily_kpis.py`** (업데이트됨)

---

## 🎯 배포 실행 (3단계)

### Step 1: Dry-run 테스트

```bash
cd /home/won/projects/dreamseed_monorepo

# Dry-run으로 배포 시뮬레이션
./portal_front/ops/k8s/deploy-advanced-analytics.sh --dry-run
```

**예상 시간**: 1분

---

### Step 2: 실제 배포

```bash
# 전체 배포 (마이그레이션 포함)
./portal_front/ops/k8s/deploy-advanced-analytics.sh

# 또는 마이그레이션 스킵 (이미 적용된 경우)
./portal_front/ops/k8s/deploy-advanced-analytics.sh --skip-migration
```

**예상 시간**: 3~5분 (마이그레이션 포함)

**배포 단계**:
1. ExternalSecrets 적용 (r-brms, r-forecast)
2. Database credentials 확인
3. Alembic 마이그레이션 (Prophet/Survival 테이블)
4. compute-daily-kpis 업데이트 (METRICS_USE_BAYESIAN=true)
5. CronJobs 적용 (Bayesian/Prophet/Survival)
6. R 서비스 헬스 체크
7. 스모크 테스트 (선택)

---

### Step 3: 검증

```bash
# 자동 검증 스크립트 실행
./portal_front/ops/k8s/verify-advanced-analytics.sh
```

**예상 시간**: 2~3분

**검증 항목**:
- ✅ R 서비스 Running 상태
- ✅ Secrets 존재 확인
- ✅ CronJobs 활성화 확인
- ✅ METRICS_USE_BAYESIAN=true 확인
- ✅ R 서비스 헬스 체크 (200 OK)
- ✅ Database 테이블 존재 확인
- ✅ 최근 Job 실행 기록

---

## 🔍 스모크 테스트 (선택)

배포 스크립트 실행 중 또는 수동으로 실행:

```bash
# 1. Bayesian Growth Model
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth fit-bayesian-growth-now
kubectl -n seedtest logs -f job/fit-bayesian-growth-now

# 2. Prophet Forecasting
kubectl -n seedtest create job --from=cronjob/forecast-prophet forecast-prophet-now
kubectl -n seedtest logs -f job/forecast-prophet-now

# 3. Survival Analysis
kubectl -n seedtest create job --from=cronjob/fit-survival-churn fit-survival-churn-now
kubectl -n seedtest logs -f job/fit-survival-churn-now
```

**예상 시간**: 각 5~10분

---

## 📊 배포 후 확인사항

### 1. CronJob 스케줄 확인

```bash
kubectl -n seedtest get cronjobs | grep -E 'fit-bayesian|forecast-prophet|fit-survival|compute-daily'
```

**예상 결과**:
```
NAME                   SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
fit-bayesian-growth    30 4 * * 1    False     0        <none>          5m
forecast-prophet       0 5 * * 1     False     0        <none>          5m
fit-survival-churn     0 5 * * *     False     0        <none>          5m
compute-daily-kpis     10 2 * * *    False     0        <none>          1d
```

---

### 2. Database 테이블 확인

```bash
kubectl -n seedtest run psql-check --rm -it --image=postgres:15 --restart=Never \
  --env="DATABASE_URL=$(kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d)" \
  -- psql $DATABASE_URL -c "\dt prophet_* survival_*"
```

**예상 결과**:
```
                 List of relations
 Schema |        Name        | Type  |  Owner
--------+--------------------+-------+----------
 public | prophet_anomalies  | table | postgres
 public | prophet_fit_meta   | table | postgres
 public | survival_fit_meta  | table | postgres
 public | survival_risk      | table | postgres
```

---

### 3. R 서비스 상태 확인

```bash
kubectl -n seedtest get pods -l 'app in (r-brms-plumber,r-forecast-plumber)'
```

**예상 결과**:
```
NAME                                READY   STATUS    RESTARTS   AGE
r-brms-plumber-xxx                  1/1     Running   0          10m
r-forecast-plumber-xxx              1/1     Running   0          10m
```

---

## 🔄 운영 파라미터 (기본값)

### Bayesian Growth Model
- `LOOKBACK_WEEKS=12` (학습 데이터 12주)
- `BRMS_ITER=1000` (MCMC 샘플 1000개)
- `BRMS_CHAINS=2` (MCMC 체인 2개)
- `BRMS_UPDATE_KPI=true` (weekly_kpi.P 갱신)

### Prophet Forecasting
- `PROPHET_LOOKBACK_WEEKS=12` (학습 데이터 12주)
- `PROPHET_FORECAST_WEEKS=4` (4주 예측)
- `PROPHET_ANOMALY_THRESHOLD=2.5` (Z-score 2.5)

### Survival Analysis
- `SURVIVAL_LOOKBACK_DAYS=90` (학습 데이터 90일)
- `SURVIVAL_EVENT_THRESHOLD_DAYS=14` (14일 비활동 = 이탈)
- `SURVIVAL_UPDATE_KPI=true` (weekly_kpi.S 갱신)
- `CHURN_ALERT_THRESHOLD=0.7` (상위 30% 알림)

**파라미터 조정이 필요한 경우**: `PARAMETER_TUNING_GUIDE.md` 참고

---

## 🐛 트러블슈팅 (빠른 참조)

### 문제 1: 시계열 데이터 부족
```bash
kubectl -n seedtest set env cronjob/fit-bayesian-growth LOOKBACK_WEEKS=4
kubectl -n seedtest set env cronjob/forecast-prophet PROPHET_LOOKBACK_WEEKS=4
```

### 문제 2: 이벤트 데이터 부족 (Survival)
```bash
kubectl -n seedtest set env cronjob/fit-survival-churn SURVIVAL_LOOKBACK_DAYS=180
kubectl -n seedtest set env cronjob/fit-survival-churn SURVIVAL_EVENT_THRESHOLD_DAYS=30
```

### 문제 3: MCMC 수렴 실패
```bash
kubectl -n seedtest set env cronjob/fit-bayesian-growth BRMS_ITER=2000
kubectl -n seedtest set env cronjob/fit-bayesian-growth BRMS_CHAINS=4
```

### 문제 4: R 서비스 연결 실패
```bash
kubectl -n seedtest rollout restart deployment/r-brms-plumber
kubectl -n seedtest rollout restart deployment/r-forecast-plumber
```

---

## 🔙 롤백 절차

### 즉시 폴백 (Bayesian 비활성화)
```bash
kubectl -n seedtest set env cronjob/compute-daily-kpis METRICS_USE_BAYESIAN=false
```

### CronJob 일시 중지
```bash
kubectl -n seedtest patch cronjob fit-bayesian-growth -p '{"spec":{"suspend":true}}'
kubectl -n seedtest patch cronjob forecast-prophet -p '{"spec":{"suspend":true}}'
kubectl -n seedtest patch cronjob fit-survival-churn -p '{"spec":{"suspend":true}}'
```

### Alembic 다운그레이드
```bash
kubectl -n seedtest run alembic-downgrade --rm -it \
  --image=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest \
  --env="DATABASE_URL=..." \
  -- /bin/sh -c "cd /app && alembic downgrade -1"
```

---

## 📚 상세 문서

| 문서 | 용도 |
|------|------|
| `DEPLOYMENT_CHECKLIST_ADVANCED_ANALYTICS.md` | 상세 배포 체크리스트 (16KB) |
| `DEPLOYMENT_SUMMARY.md` | 배포 요약 (6.1KB) |
| `PARAMETER_TUNING_GUIDE.md` | 파라미터 조정 가이드 (9.3KB) |
| `DEPLOYMENT_GUIDE_IRT_PIPELINE.md` | IRT 파이프라인 가이드 (13KB) |
| `INTEGRATION_TEST_GUIDE.md` | 통합 테스트 가이드 |
| `FINAL_IMPLEMENTATION_STATUS.md` | 최종 구현 상태 |

---

## ✅ 최종 체크리스트

### 배포 전
- [ ] R 서비스 이미지 빌드 완료 (r-brms-plumber, r-forecast-plumber)
- [ ] GCP Secret Manager 설정 (r-brms-internal-token, r-forecast-internal-token)
- [ ] Database 접근 확인 (seedtest-db-credentials)
- [ ] K8s 리소스 확인 (namespace, serviceaccount)

### 배포 실행
- [ ] Dry-run 테스트 완료
- [ ] 실제 배포 실행
- [ ] 검증 스크립트 통과

### 배포 후
- [ ] CronJob 스케줄 확인
- [ ] Database 테이블 생성 확인
- [ ] R 서비스 상태 확인
- [ ] 스모크 테스트 실행 (선택)

### 모니터링
- [ ] ServiceMonitor 타겟 확인
- [ ] CronJob 로그 확인
- [ ] 실패 알람 설정 확인

---

## 🎉 배포 시작!

```bash
# 1단계: Dry-run
./portal_front/ops/k8s/deploy-advanced-analytics.sh --dry-run

# 2단계: 실제 배포
./portal_front/ops/k8s/deploy-advanced-analytics.sh

# 3단계: 검증
./portal_front/ops/k8s/verify-advanced-analytics.sh
```

**배포 중 이슈 발생 시**: `DEPLOYMENT_CHECKLIST_ADVANCED_ANALYTICS.md` 트러블슈팅 섹션 참고

**파라미터 조정 필요 시**: `PARAMETER_TUNING_GUIDE.md` 참고

---

**최종 업데이트**: 2025-11-02 10:26 KST  
**작성자**: Cascade AI  
**상태**: ✅ Production Ready - 즉시 배포 가능

**바로 배포·검증 진행하셔도 됩니다!** 🚀
