# Advanced Analytics 배포 요약

**최종 업데이트**: 2025-11-02  
**상태**: Production Ready

---

## 🎯 한눈에 보는 배포 절차

```bash
# 1. 배포 스크립트 실행
cd /home/won/projects/dreamseed_monorepo
./portal_front/ops/k8s/deploy-advanced-analytics.sh

# 2. 검증 스크립트 실행
./portal_front/ops/k8s/verify-advanced-analytics.sh

# 3. 스모크 테스트 (선택)
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth fit-bayesian-growth-now
kubectl -n seedtest create job --from=cronjob/forecast-prophet forecast-prophet-now
kubectl -n seedtest create job --from=cronjob/fit-survival-churn fit-survival-churn-now
```

---

## 📦 배포되는 컴포넌트

### 1. R 서비스
- **r-brms-plumber**: Bayesian 성장 모델 (Stan/brms)
- **r-forecast-plumber**: Prophet 예측 + Survival 분석

### 2. ExternalSecrets
- **r-brms-credentials**: R BRMS 서비스 인증 토큰
- **r-forecast-credentials**: R Forecast 서비스 인증 토큰

### 3. CronJobs
- **fit-bayesian-growth**: 월요일 04:30 UTC (베이지안 성장 모델)
- **forecast-prophet**: 월요일 05:00 UTC (Prophet 예측)
- **fit-survival-churn**: 매일 05:00 UTC (생존 분석)
- **compute-daily-kpis**: 매일 02:10 UTC (METRICS_USE_BAYESIAN=true)

### 4. Database Tables (Alembic)
- **prophet_fit_meta**: Prophet 모델 메타데이터
- **prophet_anomalies**: 이상치 감지 결과
- **survival_fit_meta**: Survival 모델 메타데이터
- **survival_risk**: 사용자별 이탈 위험 점수

---

## 🔍 검증 항목

### ✅ 서비스 헬스
```bash
# r-brms-plumber
curl http://r-brms-plumber.seedtest.svc.cluster.local:80/healthz
# 예상: {"status":"ok"}

# r-forecast-plumber
curl http://r-forecast-plumber.seedtest.svc.cluster.local:80/healthz
# 예상: {"status":"ok"}
```

### ✅ 베이지안 KPI (P 값)
```sql
-- compute_daily_kpis 실행 후
SELECT user_id, week_start, P, sigma, updated_at 
FROM weekly_kpi 
WHERE P IS NOT NULL 
ORDER BY updated_at DESC 
LIMIT 10;
-- 예상: P 값 0.0~1.0 범위
```

### ✅ Prophet 예측
```sql
-- forecast_prophet 실행 후
SELECT run_id, user_id, fitted_at, horizon_weeks 
FROM prophet_fit_meta 
ORDER BY fitted_at DESC 
LIMIT 5;

SELECT user_id, ds, anomaly_score, is_anomaly 
FROM prophet_anomalies 
WHERE is_anomaly = true 
ORDER BY ds DESC 
LIMIT 10;
-- 예상: 최근 실행 기록 + 이상치 감지 결과
```

### ✅ Survival 분석
```sql
-- fit_survival_churn 실행 후
SELECT run_id, fitted_at, n_users, n_events 
FROM survival_fit_meta 
ORDER BY fitted_at DESC 
LIMIT 5;

SELECT user_id, risk_score, risk_percentile, predicted_at 
FROM survival_risk 
ORDER BY predicted_at DESC 
LIMIT 10;

SELECT user_id, week_start, S, updated_at 
FROM weekly_kpi 
WHERE S IS NOT NULL 
ORDER BY updated_at DESC 
LIMIT 10;
-- 예상: 위험 점수 0.0~1.0, weekly_kpi.S 갱신
```

### ✅ Weekly Report
```sql
-- generate_weekly_report 실행 후
SELECT user_id, week_start, format, url, generated_at 
FROM report_artifacts 
ORDER BY generated_at DESC 
LIMIT 5;
-- 예상: S3 URL 생성, Bayesian/Prophet/Survival 섹션 포함
```

---

## 🔧 운영 파라미터 조정

### 데이터 부족 시

```bash
# 시계열 데이터 부족 (Prophet/Bayesian)
kubectl -n seedtest set env cronjob/fit-bayesian-growth LOOKBACK_WEEKS=4
kubectl -n seedtest set env cronjob/forecast-prophet PROPHET_LOOKBACK_WEEKS=4

# 이벤트 데이터 부족 (Survival)
kubectl -n seedtest set env cronjob/fit-survival-churn SURVIVAL_LOOKBACK_DAYS=180
kubectl -n seedtest set env cronjob/fit-survival-churn SURVIVAL_EVENT_THRESHOLD_DAYS=30
```

### 성능 튜닝

```bash
# Bayesian MCMC 수렴 개선
kubectl -n seedtest set env cronjob/fit-bayesian-growth BRMS_ITER=2000
kubectl -n seedtest set env cronjob/fit-bayesian-growth BRMS_CHAINS=4

# Prophet 이상치 민감도 조정
kubectl -n seedtest set env cronjob/forecast-prophet PROPHET_ANOMALY_THRESHOLD=3.0

# Churn 알림 임계값 조정
kubectl -n seedtest set env cronjob/fit-survival-churn CHURN_ALERT_THRESHOLD=0.6
```

---

## 🔄 롤백 절차

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

## 📊 모니터링

### Prometheus 메트릭
- `r_brms_plumber_up`: R BRMS 서비스 상태
- `r_forecast_plumber_up`: R Forecast 서비스 상태
- `cronjob_success_count{job="fit-bayesian-growth"}`: Bayesian Job 성공 횟수
- `cronjob_success_count{job="forecast-prophet"}`: Prophet Job 성공 횟수
- `cronjob_success_count{job="fit-survival-churn"}`: Survival Job 성공 횟수

### 로그 확인
```bash
# CronJob 로그
kubectl -n seedtest logs -l job-name=fit-bayesian-growth --tail=100
kubectl -n seedtest logs -l job-name=forecast-prophet --tail=100
kubectl -n seedtest logs -l job-name=fit-survival-churn --tail=100

# R 서비스 로그
kubectl -n seedtest logs -l app=r-brms-plumber --tail=100
kubectl -n seedtest logs -l app=r-forecast-plumber --tail=100
```

---

## 📚 상세 문서

- **배포 체크리스트**: `DEPLOYMENT_CHECKLIST_ADVANCED_ANALYTICS.md`
- **IRT 파이프라인**: `DEPLOYMENT_GUIDE_IRT_PIPELINE.md`
- **통합 테스트**: `INTEGRATION_TEST_GUIDE.md`
- **최종 구현 상태**: `FINAL_IMPLEMENTATION_STATUS.md`

---

## 🎉 배포 완료 후

1. **스모크 테스트 실행** (위 3개 Job)
2. **로그 모니터링** (5~10분 소요)
3. **DB 결과 확인** (위 SQL 쿼리)
4. **Weekly Report 생성** (Bayesian/Prophet/Survival 섹션 확인)

---

**배포 준비 완료! 바로 실행하셔도 됩니다.**

```bash
./portal_front/ops/k8s/deploy-advanced-analytics.sh
```
