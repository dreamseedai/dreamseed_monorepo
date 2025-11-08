# CronJob 스모크 테스트 가이드

## 개요

Prophet 및 Survival 모델의 CronJob 스모크 테스트 방법과 결과 확인 절차를 안내합니다.

## 스모크 테스트 실행

### 1. CronJob 적용

```bash
# Prophet CronJob
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/forecast-prophet.yaml

# Survival CronJob
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-survival-churn.yaml
```

### 2. 즉시 실행 (스모크 테스트)

```bash
# Prophet 스모크 테스트
kubectl -n seedtest create job --from=cronjob/forecast-prophet \
  forecast-prophet-smoke-$(date +%s)

# Survival 스모크 테스트
kubectl -n seedtest create job --from=cronjob/fit-survival-churn \
  survival-smoke-$(date +%s)
```

## 상태 확인

### 빠른 확인 스크립트

```bash
# 모든 스모크 테스트 확인
./scripts/check-smoke-tests.sh

# Prophet만 확인
./scripts/check-smoke-tests.sh prophet

# Survival만 확인
./scripts/check-smoke-tests.sh survival
```

### 수동 확인

#### Job 상태 확인

```bash
# 최신 Prophet Job
kubectl -n seedtest get jobs | grep forecast-prophet-smoke | tail -1

# 최신 Survival Job
kubectl -n seedtest get jobs | grep survival-smoke | tail -1
```

#### Pod 상태 확인

```bash
# Prophet Pod
PROPHET_JOB="forecast-prophet-smoke-<timestamp>"
PROPHET_POD=$(kubectl -n seedtest get pods -l job-name=$PROPHET_JOB -o jsonpath='{.items[0].metadata.name}')
kubectl -n seedtest get pod $PROPHET_POD

# Survival Pod
SURVIVAL_JOB="survival-smoke-<timestamp>"
SURVIVAL_POD=$(kubectl -n seedtest get pods -l job-name=$SURVIVAL_JOB -o jsonpath='{.items[0].metadata.name}')
kubectl -n seedtest get pod $SURVIVAL_POD
```

#### 로그 확인

```bash
# Prophet 로그 (실시간)
kubectl -n seedtest logs -f $PROPHET_POD

# Survival 로그 (실시간)
kubectl -n seedtest logs -f $SURVIVAL_POD

# 최근 로그만 확인
kubectl -n seedtest logs $PROPHET_POD --tail=50
kubectl -n seedtest logs $SURVIVAL_POD --tail=50
```

## 예상 결과

### Prophet 스모크 테스트

**성공 기준**:
- Job 상태: `Complete`
- Pod 상태: `Succeeded`
- 로그에 `[OK] Prophet fit completed` 또는 유사한 성공 메시지
- DB에 `prophet_fit_meta` 레코드 생성 확인

**로그 예시**:
```
[INFO] Forecasting I_t trend (lookback=12 weeks, forecast=4 weeks)
[INFO] Loaded 12 weekly I_t observations
[INFO] Forecast: 4 periods
[OK] Prophet fit completed
```

**DB 확인**:
```sql
SELECT run_id, metric, fitted_at
FROM prophet_fit_meta
ORDER BY fitted_at DESC
LIMIT 5;
```

### Survival 스모크 테스트

**성공 기준**:
- Job 상태: `Complete`
- Pod 상태: `Succeeded`
- 로그에 `[OK] Survival fit completed` 또는 유사한 성공 메시지
- DB에 `survival_fit_meta` 레코드 생성 확인
- `weekly_kpi.S` 업데이트 확인 (선택)

**로그 예시**:
```
[INFO] Fitting survival model (lookback=90 days, event_threshold=14 days)
[INFO] Loaded 1245 user observations
[INFO] Calling R Forecast service /survival/fit...
[OK] Survival fit completed
```

**DB 확인**:
```sql
-- 모델 메타
SELECT run_id, fitted_at
FROM survival_fit_meta
ORDER BY fitted_at DESC
LIMIT 5;

-- 위험 점수 (survival_risk 테이블이 있는 경우)
SELECT user_id, risk_score, updated_at
FROM survival_risk
ORDER BY updated_at DESC
LIMIT 10;

-- weekly_kpi.S 업데이트 확인
SELECT user_id, week_start, kpis->>'S' AS churn_risk
FROM weekly_kpi
WHERE kpis->>'S' IS NOT NULL
ORDER BY week_start DESC
LIMIT 10;
```

## 문제 해결

### Job이 Pending 상태

**원인**:
- 리소스 부족
- 이미지 Pull 실패
- 볼륨 마운트 실패

**해결**:
```bash
# Pod 이벤트 확인
kubectl -n seedtest describe pod $POD_NAME

# 리소스 확인
kubectl -n seedtest describe node | grep -A 5 "Allocated resources"
```

### Job이 Failed 상태

**원인**:
- Python 스크립트 오류
- R 서비스 접근 불가
- DB 연결 실패
- 데이터 부족

**해결**:
```bash
# 전체 로그 확인
kubectl -n seedtest logs $POD_NAME

# 이전 컨테이너 로그 (재시작된 경우)
kubectl -n seedtest logs $POD_NAME --previous
```

**일반적인 오류**:

1. **R 서비스 접근 불가**:
   ```
   Connection refused: r-forecast-plumber.seedtest.svc.cluster.local:80
   ```
   - 해결: `kubectl -n seedtest get svc r-forecast-plumber` 확인
   - `kubectl -n seedtest get pods -l app=r-forecast-plumber` 확인

2. **데이터 부족**:
   ```
   [WARN] Insufficient I_t data for Prophet fitting (need >= 4 weeks)
   ```
   - 해결: `weekly_kpi` 테이블에 충분한 데이터가 있는지 확인

3. **DB 연결 실패**:
   ```
   could not connect to server
   ```
   - 해결: Cloud SQL Proxy 상태 확인
   - `DATABASE_URL` Secret 확인

### R 서비스 응답 없음

**확인 사항**:
```bash
# R 서비스 Pod 상태
kubectl -n seedtest get pods -l app=r-forecast-plumber

# R 서비스 로그
kubectl -n seedtest logs -l app=r-forecast-plumber

# 헬스체크
kubectl -n seedtest run -it --rm test-curl --image=curlimages/curl --restart=Never -- \
  curl http://r-forecast-plumber.seedtest.svc.cluster.local:80/healthz
```

## 정리

### Job 삭제

```bash
# 특정 Job 삭제
kubectl -n seedtest delete job forecast-prophet-smoke-<timestamp>
kubectl -n seedtest delete job survival-smoke-<timestamp>

# 모든 스모크 Job 삭제
kubectl -n seedtest delete jobs -l job-name=forecast-prophet-smoke
kubectl -n seedtest delete jobs -l job-name=survival-smoke
```

### Pod 정리

```bash
# 완료된 Pod 자동 정리 (TTL 설정 시)
# 수동 삭제 (필요시)
kubectl -n seedtest delete pods -l job-name=forecast-prophet-smoke-<timestamp>
kubectl -n seedtest delete pods -l job-name=survival-smoke-<timestamp>
```

## 참고

- [Prophet API 포맷 명세서](./API_FORMAT_SPEC.md)
- [Survival API 포맷 명세서](./API_FORMAT_SPEC.md)
- [R Forecast Plumber 배포 가이드](./R_FORECAST_PLUMBER_DEPLOYMENT.md)

