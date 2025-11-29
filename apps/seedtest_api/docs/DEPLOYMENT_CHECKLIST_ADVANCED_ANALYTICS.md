# Advanced Analytics 배포 체크리스트

**최종 업데이트**: 2025-11-02  
**상태**: Production Ready  
**대상**: Bayesian Growth, Prophet Forecasting, Survival Analysis

---

## 🎯 배포 전 준비사항

### ✅ 사전 확인

- [ ] **R 서비스 이미지 빌드 완료**
  - `r-brms-plumber` 이미지 빌드 및 푸시
  - `r-forecast-plumber` 이미지 빌드 및 푸시
  - 이미지 태그: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest`
  - 이미지 태그: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest`

- [ ] **GCP Secret Manager 설정**
  - `r-brms-internal-token` 시크릿 생성 (선택사항)
  - `r-forecast-internal-token` 시크릿 생성 (선택사항)
  - ExternalSecrets Operator 설치 확인

- [ ] **Database 접근 확인**
  - `seedtest-db-credentials` Secret 존재 확인
  - `DATABASE_URL` 키 포함 확인

- [ ] **K8s 리소스 확인**
  - Namespace `seedtest` 존재 확인
  - ServiceAccount `seedtest-api` 존재 확인
  - Cloud SQL Proxy 설정 확인

---

## 🚀 배포 순서 (권장)

### Phase 1: R 서비스 배포

```bash
# 1. R BRMS Plumber 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/r-brms-plumber/deployment.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-brms-plumber/service.yaml

# 2. R Forecast Plumber 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/deployment.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/service.yaml

# 3. ServiceMonitor 적용 (Prometheus 모니터링)
kubectl -n seedtest apply -f portal_front/ops/k8s/r-brms-plumber/servicemonitor.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/servicemonitor.yaml

# 4. 서비스 상태 확인
kubectl -n seedtest get pods -l 'app in (r-brms-plumber,r-forecast-plumber)'
kubectl -n seedtest get svc -l 'app in (r-brms-plumber,r-forecast-plumber)'
```

**예상 결과**:
```
NAME                                READY   STATUS    RESTARTS   AGE
r-brms-plumber-xxx                  1/1     Running   0          30s
r-forecast-plumber-xxx              1/1     Running   0          30s
```

---

### Phase 2: ExternalSecrets 동기화

```bash
# 1. ExternalSecret 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/r-brms-plumber/externalsecret.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/externalsecret.yaml

# 2. 동기화 대기 (최대 60초)
sleep 10

# 3. Secret 생성 확인
kubectl -n seedtest get secret r-brms-credentials
kubectl -n seedtest get secret r-forecast-credentials
kubectl -n seedtest get secret seedtest-db-credentials
```

**예상 결과**:
```
NAME                      TYPE     DATA   AGE
r-brms-credentials        Opaque   1      10s
r-forecast-credentials    Opaque   1      10s
seedtest-db-credentials   Opaque   1      5d
```

---

### Phase 3: Alembic 마이그레이션

```bash
# 1. 마이그레이션 실행 (Prophet/Survival 테이블 생성)
kubectl -n seedtest run alembic-migrate-prophet-survival \
  --image=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest \
  --rm -it --restart=Never \
  --env="DATABASE_URL=$(kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d)" \
  -- /bin/sh -c "cd /app && alembic upgrade head"

# 2. 테이블 생성 확인
kubectl -n seedtest run psql-verify \
  --image=postgres:15 --rm -it --restart=Never \
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
(4 rows)
```

---

### Phase 4: seedtest-api 설정 업데이트

```bash
# 1. compute-daily-kpis CronJob 업데이트 (METRICS_USE_BAYESIAN=true)
kubectl -n seedtest patch cronjob compute-daily-kpis --type=json -p='[
  {"op": "replace", "path": "/spec/jobTemplate/spec/template/spec/containers/0/env/4/value", "value": "true"}
]'

# 또는 전체 매니페스트 재적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml

# 2. 환경 변수 확인
kubectl -n seedtest get cronjob compute-daily-kpis -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].env[?(@.name=="METRICS_USE_BAYESIAN")].value}'
```

**예상 결과**: `true`

---

### Phase 5: CronJob 배포

```bash
# 1. Bayesian Growth Model CronJob
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-bayesian-growth.yaml

# 2. Prophet Forecasting CronJob
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/forecast-prophet.yaml

# 3. Survival Analysis CronJob
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-survival-churn.yaml

# 4. CronJob 확인
kubectl -n seedtest get cronjobs | grep -E 'fit-bayesian|forecast-prophet|fit-survival'
```

**예상 결과**:
```
NAME                   SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
fit-bayesian-growth    30 4 * * 1    False     0        <none>          10s
forecast-prophet       0 5 * * 1     False     0        <none>          10s
fit-survival-churn     0 5 * * *     False     0        <none>          10s
```

---

## 🔍 스모크 테스트 / 검증

### 1. R 서비스 헬스 체크

```bash
# r-brms-plumber
kubectl -n seedtest run curl-brms-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -v http://r-brms-plumber.seedtest.svc.cluster.local:80/healthz

# r-forecast-plumber
kubectl -n seedtest run curl-forecast-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -v http://r-forecast-plumber.seedtest.svc.cluster.local:80/healthz
```

**예상 응답**: `200 OK` + `{"status":"ok"}`

---

### 2. 베이지안 KPI 계산 (P 값)

```bash
# compute_daily_kpis 수동 실행
kubectl -n seedtest create job --from=cronjob/compute-daily-kpis compute-daily-kpis-test

# 로그 확인
kubectl -n seedtest logs -f job/compute-daily-kpis-test

# 결과 확인 (weekly_kpi.P 갱신)
kubectl -n seedtest run psql-check-p --rm -it --image=postgres:15 --restart=Never \
  --env="DATABASE_URL=..." \
  -- psql $DATABASE_URL -c "
SELECT user_id, week_start, P, sigma, updated_at 
FROM weekly_kpi 
WHERE P IS NOT NULL 
ORDER BY updated_at DESC 
LIMIT 10;
"
```

**예상 결과**: `P` 값이 0.0~1.0 범위로 갱신됨

---

### 3. Prophet 예측 실행

```bash
# forecast_prophet 수동 실행
kubectl -n seedtest create job --from=cronjob/forecast-prophet forecast-prophet-test

# 로그 확인
kubectl -n seedtest logs -f job/forecast-prophet-test

# 결과 확인 (prophet_fit_meta, prophet_anomalies)
kubectl -n seedtest run psql-check-prophet --rm -it --image=postgres:15 --restart=Never \
  --env="DATABASE_URL=..." \
  -- psql $DATABASE_URL -c "
SELECT run_id, user_id, fitted_at, horizon_weeks 
FROM prophet_fit_meta 
ORDER BY fitted_at DESC 
LIMIT 5;

SELECT user_id, ds, anomaly_score, is_anomaly 
FROM prophet_anomalies 
WHERE is_anomaly = true 
ORDER BY ds DESC 
LIMIT 10;
"
```

**예상 결과**:
- `prophet_fit_meta`: 최근 실행 기록 존재
- `prophet_anomalies`: 이상치 감지 결과 존재

---

### 4. Survival 분석 실행

```bash
# fit_survival_churn 수동 실행
kubectl -n seedtest create job --from=cronjob/fit-survival-churn fit-survival-churn-test

# 로그 확인
kubectl -n seedtest logs -f job/fit-survival-churn-test

# 결과 확인 (survival_fit_meta, survival_risk, weekly_kpi.S)
kubectl -n seedtest run psql-check-survival --rm -it --image=postgres:15 --restart=Never \
  --env="DATABASE_URL=..." \
  -- psql $DATABASE_URL -c "
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
"
```

**예상 결과**:
- `survival_fit_meta`: 최근 실행 기록 존재
- `survival_risk`: 위험 점수 0.0~1.0 범위
- `weekly_kpi.S`: 생존 확률 0.0~1.0 범위

---

### 5. Weekly Report 생성 테스트

```bash
# generate_weekly_report 수동 실행
kubectl -n seedtest create job --from=cronjob/generate-weekly-report generate-weekly-report-test

# 로그 확인
kubectl -n seedtest logs -f job/generate-weekly-report-test

# 리포트 확인
kubectl -n seedtest run psql-check-report --rm -it --image=postgres:15 --restart=Never \
  --env="DATABASE_URL=..." \
  -- psql $DATABASE_URL -c "
SELECT user_id, week_start, format, url, generated_at 
FROM report_artifacts 
ORDER BY generated_at DESC 
LIMIT 5;
"
```

**예상 결과**:
- S3 URL 생성됨
- 리포트에 Bayesian/Prophet/Survival 섹션 포함

---

## 📊 운영 파라미터 (기본값)

### Bayesian Growth Model

| 파라미터 | 기본값 | 설명 | 조정 범위 |
|---------|--------|------|-----------|
| `LOOKBACK_WEEKS` | 12 | 학습 데이터 기간 | 8~24 |
| `BRMS_ITER` | 1000 | MCMC 샘플 수 | 1000~2000 |
| `BRMS_CHAINS` | 2 | MCMC 체인 수 | 2~4 |
| `BRMS_FAMILY` | gaussian | 모델 패밀리 | gaussian, student |
| `BRMS_UPDATE_KPI` | true | weekly_kpi.P 갱신 | true/false |

### Prophet Forecasting

| 파라미터 | 기본값 | 설명 | 조정 범위 |
|---------|--------|------|-----------|
| `PROPHET_LOOKBACK_WEEKS` | 12 | 학습 데이터 기간 | 8~24 |
| `PROPHET_FORECAST_WEEKS` | 4 | 예측 기간 | 2~8 |
| `PROPHET_ANOMALY_THRESHOLD` | 2.5 | 이상치 Z-score | 2.0~3.0 |

### Survival Analysis

| 파라미터 | 기본값 | 설명 | 조정 범위 |
|---------|--------|------|-----------|
| `SURVIVAL_LOOKBACK_DAYS` | 90 | 학습 데이터 기간 | 60~180 |
| `SURVIVAL_EVENT_THRESHOLD_DAYS` | 14 | 이탈 정의 (일) | 7~30 |
| `SURVIVAL_UPDATE_KPI` | true | weekly_kpi.S 갱신 | true/false |

### Churn Alert

| 파라미터 | 기본값 | 설명 | 조정 범위 |
|---------|--------|------|-----------|
| `CHURN_ALERT_THRESHOLD` | 0.7 | 알림 임계값 | 0.6~0.8 |

---

## 🔄 모니터링 / 롤백

### ServiceMonitor 확인

```bash
# Prometheus 타겟 확인
kubectl -n seedtest get servicemonitor

# 메트릭 스크레이프 확인 (Prometheus UI)
# - r_brms_plumber_up
# - r_forecast_plumber_up
# - cronjob_success_count{job="fit-bayesian-growth"}
# - cronjob_success_count{job="forecast-prophet"}
# - cronjob_success_count{job="fit-survival-churn"}
```

### CronJob 로그 확인

```bash
# 최근 Job 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -10

# 특정 Job 로그
kubectl -n seedtest logs job/fit-bayesian-growth-<timestamp>
kubectl -n seedtest logs job/forecast-prophet-<timestamp>
kubectl -n seedtest logs job/fit-survival-churn-<timestamp>
```

### 롤백 절차

#### 1. 즉시 폴백 (ENV 플래그)

```bash
# Bayesian 메트릭 비활성화
kubectl -n seedtest set env cronjob/compute-daily-kpis METRICS_USE_BAYESIAN=false
```

#### 2. CronJob 일시 중지

```bash
kubectl -n seedtest patch cronjob fit-bayesian-growth -p '{"spec":{"suspend":true}}'
kubectl -n seedtest patch cronjob forecast-prophet -p '{"spec":{"suspend":true}}'
kubectl -n seedtest patch cronjob fit-survival-churn -p '{"spec":{"suspend":true}}'
```

#### 3. Alembic 다운그레이드

```bash
# 마이그레이션 롤백
kubectl -n seedtest run alembic-downgrade --rm -it \
  --image=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest \
  --env="DATABASE_URL=..." \
  -- /bin/sh -c "cd /app && alembic downgrade -1"
```

---

## 🎯 권장 후속 작업

### 1. 리포트 시각화 강화

- [ ] Prophet 예측 밴드 차트 추가
- [ ] 이상치 타임라인 추가
- [ ] 생존 곡선 (Kaplan-Meier) 추가
- [ ] 위험 게이지 추가

### 2. 세그멘테이션 결합

- [ ] 세그먼트별 베이지안 예측
- [ ] 세그먼트별 이탈 위험 분석
- [ ] 추천 전략 가중치 조정

### 3. Anchors 링크 고도화

- [ ] Stocking-Lord 방법 구현
- [ ] Haebara 방법 구현
- [ ] 리포트에 링크 메타데이터 추가

### 4. 알림 고도화

- [ ] 이탈 위험 임계값 초과 시 Slack 알림
- [ ] 이상치 감지 시 이메일 알림
- [ ] 예측 신뢰도 낮을 시 경고

---

## ✅ 최종 배포 체크리스트

### 사전 준비
- [ ] R 서비스 이미지 빌드 완료
- [ ] GCP Secret Manager 설정 완료
- [ ] Database 접근 확인 완료
- [ ] K8s 리소스 확인 완료

### 배포 실행
- [ ] R 서비스 배포 (r-brms-plumber, r-forecast-plumber)
- [ ] ExternalSecrets 동기화 확인
- [ ] Alembic 마이그레이션 실행
- [ ] seedtest-api 설정 업데이트 (METRICS_USE_BAYESIAN=true)
- [ ] CronJob 배포 (fit-bayesian-growth, forecast-prophet, fit-survival-churn)

### 검증
- [ ] R 서비스 헬스 체크 (200 OK)
- [ ] 베이지안 KPI 계산 (weekly_kpi.P 갱신)
- [ ] Prophet 예측 실행 (prophet_fit_meta, prophet_anomalies 생성)
- [ ] Survival 분석 실행 (survival_fit_meta, survival_risk, weekly_kpi.S 갱신)
- [ ] Weekly Report 생성 (S3 업로드, 섹션 렌더링 확인)

### 모니터링
- [ ] ServiceMonitor 타겟 상태 확인
- [ ] CronJob 로그 확인
- [ ] 실패 알람 설정 확인
- [ ] 롤백 절차 숙지

---

## 🐛 트러블슈팅

### 문제 1: R 서비스 연결 실패

**증상**:
```
[ERROR] Failed to call R BRMS service: Connection refused
```

**해결**:
```bash
# 1. Pod 상태 확인
kubectl -n seedtest get pods -l app=r-brms-plumber

# 2. 로그 확인
kubectl -n seedtest logs -l app=r-brms-plumber --tail=50

# 3. 재시작
kubectl -n seedtest rollout restart deployment/r-brms-plumber
```

---

### 문제 2: 시계열 데이터 부족

**증상**:
```
[WARN] Insufficient time series data: 3 weeks (minimum: 8)
```

**해결**:
```bash
# LOOKBACK_WEEKS 감소
kubectl -n seedtest set env cronjob/fit-bayesian-growth LOOKBACK_WEEKS=4
kubectl -n seedtest set env cronjob/forecast-prophet PROPHET_LOOKBACK_WEEKS=4
```

---

### 문제 3: 이벤트 데이터 부족 (Survival)

**증상**:
```
[WARN] Insufficient event data: 5 events (minimum: 10)
```

**해결**:
```bash
# SURVIVAL_LOOKBACK_DAYS 증가
kubectl -n seedtest set env cronjob/fit-survival-churn SURVIVAL_LOOKBACK_DAYS=180

# 또는 EVENT_THRESHOLD_DAYS 증가 (더 많은 이벤트 포함)
kubectl -n seedtest set env cronjob/fit-survival-churn SURVIVAL_EVENT_THRESHOLD_DAYS=30
```

---

### 문제 4: MCMC 수렴 실패 (Bayesian)

**증상**:
```
[WARN] MCMC chains did not converge (Rhat > 1.1)
```

**해결**:
```bash
# ITER 증가, CHAINS 증가
kubectl -n seedtest set env cronjob/fit-bayesian-growth BRMS_ITER=2000
kubectl -n seedtest set env cronjob/fit-bayesian-growth BRMS_CHAINS=4
```

---

## 📚 관련 문서

- `DEPLOYMENT_GUIDE_IRT_PIPELINE.md` - IRT 파이프라인 배포 가이드
- `README_IRT_PIPELINE.md` - IRT 파이프라인 개요
- `INTEGRATION_TEST_GUIDE.md` - 통합 테스트 가이드
- `FINAL_IMPLEMENTATION_STATUS.md` - 최종 구현 상태

---

**최종 업데이트**: 2025-11-02  
**작성자**: Cascade AI  
**상태**: Production Ready - 즉시 배포 가능

---

## 🚀 빠른 시작

```bash
# 1. 배포 스크립트 실행 (dry-run)
cd /home/won/projects/dreamseed_monorepo
chmod +x portal_front/ops/k8s/deploy-advanced-analytics.sh
./portal_front/ops/k8s/deploy-advanced-analytics.sh --dry-run

# 2. 실제 배포
./portal_front/ops/k8s/deploy-advanced-analytics.sh

# 3. 검증
kubectl -n seedtest get cronjobs | grep -E 'fit-bayesian|forecast-prophet|fit-survival'
kubectl -n seedtest get pods -l 'app in (r-brms-plumber,r-forecast-plumber)'
```

**배포 완료 후 스모크 테스트를 실행하여 모든 컴포넌트가 정상 작동하는지 확인하세요.**
