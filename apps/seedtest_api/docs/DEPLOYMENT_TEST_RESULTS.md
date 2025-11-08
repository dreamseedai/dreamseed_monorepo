# 배포 및 테스트 결과

## 실행 명령어 요약

### 1. R 서비스 배포
```bash
# r-brms-plumber
cd portal_front/r-brms-plumber
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest
kubectl -n seedtest apply -f ../../ops/k8s/r-brms-plumber/

# r-forecast-plumber
cd ../r-forecast-plumber
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest
kubectl -n seedtest apply -f ../../ops/k8s/r-forecast-plumber/
```

### 2. CronJob 적용
```bash
cd ../../ops/k8s/cron
kubectl -n seedtest apply -f fit-bayesian-growth.yaml
kubectl -n seedtest apply -f forecast-prophet.yaml
kubectl -n seedtest apply -f fit-survival-churn.yaml
```

### 3. 테스트 Job 생성
```bash
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth brms-test-$(date +%s)
kubectl -n seedtest create job --from=cronjob/forecast-prophet prophet-test-$(date +%s)
kubectl -n seedtest create job --from=cronjob/fit-survival-churn survival-test-$(date +%s)
```

## 배포 상태 확인

### R 서비스
```bash
# Deployment 상태
kubectl -n seedtest get deployment r-brms-plumber r-forecast-plumber

# Service 상태
kubectl -n seedtest get svc r-brms-plumber r-forecast-plumber

# Pod 상태
kubectl -n seedtest get pods | grep -E "r-brms|r-forecast"
```

### CronJob
```bash
kubectl -n seedtest get cronjob | grep -E "fit-bayesian-growth|forecast-prophet|fit-survival-churn"
```

### 테스트 Job
```bash
# Job 상태
kubectl -n seedtest get jobs | grep -E "brms-test|prophet-test|survival-test"

# Pod 로그
kubectl -n seedtest logs -f job/<job-name>
```

## 로그 확인 방법

### brms-test Job
```bash
JOB_NAME=$(kubectl -n seedtest get jobs | grep brms-test | tail -1 | awk '{print $1}')
kubectl -n seedtest logs -f job/$JOB_NAME
```

### prophet-test Job
```bash
JOB_NAME=$(kubectl -n seedtest get jobs | grep prophet-test | tail -1 | awk '{print $1}')
kubectl -n seedtest logs -f job/$JOB_NAME
```

### survival-test Job
```bash
JOB_NAME=$(kubectl -n seedtest get jobs | grep survival-test | tail -1 | awk '{print $1}')
kubectl -n seedtest logs -f job/$JOB_NAME
```

## 예상 결과

### 성공 시
- Job이 `Completed` 상태로 전환
- Pod 로그에 "[INFO] Fitting Bayesian growth model..." 메시지
- R 서비스 호출 성공 메시지
- `growth_brms_meta` 테이블에 데이터 저장

### 실패 가능 원인
1. R 서비스 이미지 미빌드: `ImagePullBackOff`
2. R 서비스 미사용 가능: 네트워크/서비스 연결 실패
3. 데이터 부족: 최소 데이터 요구사항 미달
4. 환경 변수 오류: 잘못된 설정

## 트러블슈팅

### R 서비스 Pod가 ImagePullBackOff 상태
```bash
# 이미지 확인
kubectl -n seedtest describe pod <pod-name> | grep -A 5 "Events"

# 이미지 빌드 및 푸시 필요
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest ./r-brms-plumber
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest
```

### Job이 실패 상태
```bash
# 로그 확인
kubectl -n seedtest logs job/<job-name>

# Pod 이벤트 확인
kubectl -n seedtest describe job <job-name>
```

### 데이터 확인
```sql
-- growth_brms_meta 확인
SELECT run_id, fitted_at, posterior_summary
FROM growth_brms_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- weekly_kpi.P 확인
SELECT user_id, week_start, kpis->>'P' AS goal_probability
FROM weekly_kpi
WHERE kpis ? 'P'
ORDER BY week_start DESC
LIMIT 10;
```

