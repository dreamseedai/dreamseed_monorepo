# 분석 모델 스캐폴딩 검증 체크리스트

## 추천 확인 포인트

### 1. 베이지안 KPI(P) 적용 확인

**목적**: `METRICS_USE_BAYESIAN=true`일 때 `weekly_kpi.P`가 posterior 기반 값으로 채워지는지 확인

**방법**:
```bash
# 1. seedtest-api Deployment에 METRICS_USE_BAYESIAN=true 추가
kubectl -n seedtest set env deployment/seedtest-api METRICS_USE_BAYESIAN=true

# 2. compute_daily_kpis 실행 (CronJob 또는 수동 Job)
kubectl -n seedtest create job --from=cronjob/compute-daily-kpis \
  compute-daily-kpis-test-$(date +%s)
kubectl -n seedtest logs -f job/compute-daily-kpis-test-<timestamp>

# 3. weekly_kpi.P 확인 (psql 또는 Python 스크립트)
psql $DATABASE_URL -c "
  SELECT user_id, week_start, kpis->>'P' AS goal_probability, kpis->>'sigma' AS uncertainty
  FROM weekly_kpi
  WHERE kpis->>'P' IS NOT NULL
  ORDER BY week_start DESC
  LIMIT 10;
"
```

**기대 결과**:
- `weekly_kpi.P`가 0~1 사이 값으로 채워짐
- `weekly_kpi.sigma` (불확실성)가 함께 저장됨
- 로그에 "Using Bayesian posterior for goal probability" 메시지 확인

### 2. Prophet E2E 스모크 테스트

**목적**: `forecast_prophet.py` Job이 정상 실행되고 `prophet_fit_meta`에 레코드가 저장되는지 확인

**방법**:
```bash
# 1. CronJob 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/forecast-prophet.yaml

# 2. 수동 실행
kubectl -n seedtest create job --from=cronjob/forecast-prophet \
  forecast-prophet-test-$(date +%s)

# 3. 로그 확인
kubectl -n seedtest logs -f job/forecast-prophet-test-<timestamp>

# 4. DB 확인
psql $DATABASE_URL -c "
  SELECT run_id, metric, fitted_at
  FROM prophet_fit_meta
  ORDER BY fitted_at DESC
  LIMIT 5;
"

# 5. 이상치 확인
psql $DATABASE_URL -c "
  SELECT week_start, value, anomaly_score
  FROM prophet_anomalies
  ORDER BY detected_at DESC
  LIMIT 10;
"
```

**기대 결과**:
- 로그에 `[OK] Prophet fit completed` 메시지
- `prophet_fit_meta`에 최소 1개 레코드 저장
- `prophet_anomalies`에 이상치 플래그된 주차 기록 (있는 경우)

**문제 발생 시**:
- `r-forecast-plumber` 서비스 접근 불가: `kubectl -n seedtest get svc r-forecast-plumber`
- `R_FORECAST_BASE_URL` 환경 변수 확인
- `r-forecast-credentials` Secret 확인: `kubectl -n seedtest get secret r-forecast-credentials`

### 3. Survival Cron 스모크 테스트

**목적**: `fit_survival_churn.py` Job이 정상 실행되고 `weekly_kpi.S`가 업데이트되는지 확인

**방법**:
```bash
# 1. CronJob 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-survival-churn.yaml

# 2. 수동 실행
kubectl -n seedtest create job --from=cronjob/fit-survival-churn \
  fit-survival-test-$(date +%s)

# 3. 로그 확인
kubectl -n seedtest logs -f job/fit-survival-test-<timestamp>

# 4. DB 확인
psql $DATABASE_URL -c "
  SELECT user_id, week_start, kpis->>'S' AS churn_risk
  FROM weekly_kpi
  WHERE kpis->>'S' IS NOT NULL
  ORDER BY week_start DESC
  LIMIT 10;
"

# 5. Survival 모델 메타 확인
psql $DATABASE_URL -c "
  SELECT run_id, fitted_at
  FROM survival_fit_meta
  ORDER BY fitted_at DESC
  LIMIT 5;
"
```

**기대 결과**:
- 로그에 `[OK] Survival fit completed` 메시지
- `survival_fit_meta`에 최소 1개 레코드 저장
- `weekly_kpi.S`에 위험 점수(0~1) 업데이트

**문제 발생 시**:
- `r-forecast-plumber` `/survival/fit` 엔드포인트 구현 확인
- 입력 데이터 형식 확인 (session, attempt VIEW)
- `SURVIVAL_UPDATE_KPI=true` 환경 변수 확인

### 4. ESO 비밀키 동기화 확인

**목적**: External Secrets Operator가 GCP Secret Manager에서 비밀을 정상적으로 동기화하는지 확인

**방법**:
```bash
# 1. Secret 존재 확인
kubectl -n seedtest get secret r-brms-credentials
kubectl -n seedtest get secret r-forecast-credentials

# 2. ExternalSecret 상태 확인
kubectl -n seedtest get externalsecret r-brms-credentials
kubectl -n seedtest get externalsecret r-forecast-credentials

# 3. ExternalSecret 상세 정보 (동기화 상태)
kubectl -n seedtest describe externalsecret r-brms-credentials
kubectl -n seedtest describe externalsecret r-forecast-credentials

# 4. Secret 값 확인 (base64 디코딩)
kubectl -n seedtest get secret r-brms-credentials -o jsonpath='{.data.token}' | base64 -d
kubectl -n seedtest get secret r-forecast-credentials -o jsonpath='{.data.token}' | base64 -d
```

**기대 결과**:
- `r-brms-credentials`, `r-forecast-credentials` Secret이 존재
- ExternalSecret 상태가 `READY`
- Secret 값이 GCP Secret Manager와 동기화됨

**문제 발생 시**:
- SecretStore 확인: `kubectl -n seedtest get secretstore gcpsm-secret-store`
- GCP Secret Manager에 실제 Secret 존재 확인:
  - `r-brms-internal-token`
  - `r-forecast-internal-token`
- External Secrets Operator 로그 확인: `kubectl -n external-secrets-system logs -l app.kubernetes.io/name=external-secrets`

### 5. BRMS Cron 스모크 테스트

**목적**: `fit_bayesian_growth.py` Job이 정상 실행되고 `growth_brms_meta`에 posterior가 저장되는지 확인

**방법**:
```bash
# 1. CronJob 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-bayesian-growth.yaml

# 2. 수동 실행
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth \
  fit-bayesian-test-$(date +%s)

# 3. 로그 확인
kubectl -n seedtest logs -f job/fit-bayesian-test-<timestamp>

# 4. DB 확인
psql $DATABASE_URL -c "
  SELECT run_id, fitted_at, posterior_summary->>'mean' AS mean_effect
  FROM growth_brms_meta
  ORDER BY fitted_at DESC
  LIMIT 5;
"
```

**기대 결과**:
- 로그에 `[OK] Bayesian growth fit completed` 메시지
- `growth_brms_meta`에 posterior 요약 저장
- `posterior_summary`에 `mean`, `l95`, `u95` 값 포함

## 전체 검증 순서

### Step 1: 인프라 확인
```bash
# ESO Secret 동기화 확인
kubectl -n seedtest get externalsecret

# R 서비스 배포 확인
kubectl -n seedtest get deployment r-brms-plumber r-forecast-plumber
kubectl -n seedtest get svc r-brms-plumber r-forecast-plumber

# R 서비스 헬스체크
kubectl -n seedtest run -it --rm test-curl --image=curlimages/curl --restart=Never -- \
  curl http://r-brms-plumber.seedtest.svc.cluster.local:80/healthz
kubectl -n seedtest run -it --rm test-curl --image=curlimages/curl --restart=Never -- \
  curl http://r-forecast-plumber.seedtest.svc.cluster.local:80/healthz
```

### Step 2: CronJob 적용
```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-bayesian-growth.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/forecast-prophet.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-survival-churn.yaml
```

### Step 3: 수동 테스트 실행
```bash
# 각 Job을 순차적으로 실행
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth brms-test-$(date +%s)
kubectl -n seedtest create job --from=cronjob/forecast-prophet prophet-test-$(date +%s)
kubectl -n seedtest create job --from=cronjob/fit-survival-churn survival-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/brms-test-<timestamp>
kubectl -n seedtest logs -f job/prophet-test-<timestamp>
kubectl -n seedtest logs -f job/survival-test-<timestamp>
```

### Step 4: 데이터 검증
```bash
# weekly_kpi 확인
psql $DATABASE_URL -c "
  SELECT 
    user_id,
    week_start,
    kpis->>'P' AS goal_probability,
    kpis->>'S' AS churn_risk,
    kpis->>'I_t' AS improvement_index
  FROM weekly_kpi
  WHERE week_start >= CURRENT_DATE - INTERVAL '2 weeks'
  ORDER BY week_start DESC, user_id
  LIMIT 20;
"

# 모델 메타 확인
psql $DATABASE_URL -c "
  SELECT 'growth_brms_meta' AS table_name, COUNT(*) AS count, MAX(fitted_at) AS latest
  FROM growth_brms_meta
  UNION ALL
  SELECT 'prophet_fit_meta', COUNT(*), MAX(fitted_at) FROM prophet_fit_meta
  UNION ALL
  SELECT 'survival_fit_meta', COUNT(*), MAX(fitted_at) FROM survival_fit_meta;
"
```

## 문제 해결 가이드

### R 서비스 접근 불가
**증상**: `Connection refused` 또는 `Service unavailable`

**해결**:
1. Service 존재 확인: `kubectl -n seedtest get svc`
2. Endpoint 확인: `kubectl -n seedtest get endpoints r-brms-plumber`
3. Pod 상태 확인: `kubectl -n seedtest get pods -l app=r-brms-plumber`
4. 서비스 로그 확인: `kubectl -n seedtest logs -l app=r-brms-plumber`

### ExternalSecret 동기화 실패
**증상**: Secret이 생성되지 않거나 값이 비어있음

**해결**:
1. SecretStore 상태 확인: `kubectl -n seedtest describe secretstore gcpsm-secret-store`
2. GCP Secret Manager 권한 확인
3. External Secrets Operator 로그 확인
4. GCP Secret 경로 확인: `r-brms-internal-token`, `r-forecast-internal-token`

### 데이터가 저장되지 않음
**증상**: Job 실행은 성공했지만 DB에 레코드가 없음

**해결**:
1. Job 로그에서 실제 DB 쿼리 확인
2. 테이블 존재 확인: `psql $DATABASE_URL -c "\dt growth_brms_meta prophet_fit_meta survival_fit_meta"`
3. 트랜잭션 커밋 확인 (session.commit() 호출 여부)
4. JSONB 필드 형식 확인

## 성공 기준

### ✅ 모든 검증 통과 시:
- [x] `weekly_kpi.P`에 posterior 기반 목표 확률 저장
- [x] `prophet_fit_meta`에 예측 결과 저장
- [x] `prophet_anomalies`에 이상치 플래그 저장
- [x] `survival_fit_meta`에 위험 모델 저장
- [x] `weekly_kpi.S`에 위험 점수 업데이트
- [x] 모든 CronJob이 정상 스케줄에 실행
- [x] ESO Secret이 정상 동기화

## 참고

- 모든 검증은 **staging 환경**에서 먼저 수행 권장
- R 서비스가 아직 구현되지 않은 경우, Python 클라이언트만으로는 테스트 불가 (R 서비스 구현 필요)
- 데이터가 충분하지 않은 경우, 일부 Job이 "No data found" 메시지와 함께 성공적으로 종료될 수 있음 (정상)

