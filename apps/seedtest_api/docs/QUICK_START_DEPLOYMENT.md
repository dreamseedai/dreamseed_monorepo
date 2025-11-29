# 파이프라인 빠른 배포 가이드

**작성일**: 2025-11-01

## 🚀 즉시 배포 가능한 항목

### 이미 수정 완료된 파일

다음 파일들은 이미지 경로와 명령어 경로를 수정했습니다:

1. ✅ `portal_front/ops/k8s/cron/compute-daily-kpis.yaml`
   - 이미지: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:f830ff9c2-with-env`
   - 명령어: `apps.seedtest_api.jobs.compute_daily_kpis`

2. ✅ `portal_front/ops/k8s/cron/aggregate-features-daily.yaml`
   - 이미지: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:f830ff9c2-with-env`
   - 명령어: `apps.seedtest_api.jobs.aggregate_features_daily`

3. ✅ `portal_front/ops/k8s/cron/detect-inactivity.yaml`
   - 이미지: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:f830ff9c2-with-env`
   - 명령어: `apps.seedtest_api.jobs.detect_inactivity`

---

## 📝 배포 전 필수 작업

### A. IRT Secret 생성 (3번 항목 활성화 전)

```bash
# 옵션 1: 기존 Secret 확인
kubectl -n seedtest get secret r-irt-credentials

# 옵션 2: 새로 생성 (토큰이 필요한 경우)
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='<your-token>'

# 옵션 3: Secret이 없어도 동작하도록 optional 설정 (calibrate-irt.yaml 참고)
```

### B. 기존 calibrate-irt-weekly 업데이트

```bash
# 기존 CronJob 업데이트
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 또는 신규 CronJob 배포 (선택)
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml
```

**주의**: `calibrate-irt-weekly`와 `mirt-calibrate`는 동일 기능이므로 하나만 활성화 권장

---

## 🎯 즉시 배포 명령어

### 1단계: 기본 CronJob 배포 (이미지 경로 수정 완료)

```bash
# 일일 KPI 계산
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml

# 일별 피처 집계
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/aggregate-features-daily.yaml

# 비활성 사용자 감지
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/detect-inactivity.yaml
```

### 2단계: IRT 캘리브레이션 (Secret 확인 후)

```bash
# Secret 확인
kubectl -n seedtest get secret r-irt-credentials || echo "Secret 필요"

# 기존 CronJob 업데이트
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 또는 신규 CronJob 배포
# kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml
```

### 3단계: 배포 확인

```bash
# CronJob 상태 확인
kubectl -n seedtest get cronjobs

# 다음 실행 예정 시간 확인
kubectl -n seedtest get cronjobs -o custom-columns=NAME:.metadata.name,SCHEDULE:.spec.schedule,LAST:.status.lastScheduleTime
```

### 4단계: 수동 테스트

```bash
# 각 Job 수동 실행
kubectl -n seedtest create job --from=cronjob/compute-daily-kpis test-kpis-$(date +%s)
kubectl -n seedtest create job --from=cronjob/aggregate-features-daily test-features-$(date +%s)
kubectl -n seedtest create job --from=cronjob/detect-inactivity test-inactivity-$(date +%s)
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly test-irt-$(date +%s)

# Job 완료 대기 (10분 타임아웃)
for job in $(kubectl -n seedtest get jobs -o name | grep test-); do
  echo "Waiting for $job..."
  kubectl -n seedtest wait --for=condition=complete $job --timeout=600s || echo "$job failed or timeout"
done
```

---

## 🔍 빠른 진단 명령어

### 이미지 풀 문제 진단

```bash
# 파드 이벤트 확인
kubectl -n seedtest get events --sort-by=.lastTimestamp | grep -i image | tail -10

# 특정 Job의 파드 상태
JOB_NAME=<job-name>
kubectl -n seedtest get pods -l job-name=$JOB_NAME -o wide
kubectl -n seedtest describe pod -l job-name=$JOB_NAME | tail -30
```

### 실행 중인 Job 확인

```bash
# 현재 실행 중인 Job
kubectl -n seedtest get jobs | grep -v Complete

# 최근 완료된 Job
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -5
```

### 로그 확인

```bash
# 최근 Job 로그 (자동으로 최신 파드 선택)
JOB_NAME=<job-name>
POD=$(kubectl -n seedtest get pods -l job-name=$JOB_NAME --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl -n seedtest logs $POD --tail=50
```

---

## ✅ 배포 검증 체크리스트

- [ ] CronJob이 정상적으로 배포되었는가?
  ```bash
  kubectl -n seedtest get cronjobs
  ```

- [ ] 이미지 경로가 올바른가?
  ```bash
  kubectl -n seedtest get cronjob <name> -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].image}'
  ```

- [ ] 명령어 경로가 올바른가?
  ```bash
  kubectl -n seedtest get cronjob <name> -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].command[*]}'
  ```

- [ ] Secret이 존재하는가?
  ```bash
  kubectl -n seedtest get secrets | grep -E "(db-credentials|irt-credentials)"
  ```

- [ ] 수동 실행 테스트가 성공하는가?
  ```bash
  kubectl -n seedtest create job --from=cronjob/<name> test-$(date +%s)
  kubectl -n seedtest wait --for=condition=complete job/test-* --timeout=600s
  ```

---

## 📊 다음 단계

1. **이미지 문제 해결 완료** ✅
   - 모든 CronJob 이미지 경로 수정 완료

2. **기본 CronJob 배포** (1-2번)
   - `compute-daily-kpis` ✅
   - `aggregate-features-daily` ✅
   - `detect-inactivity` ✅

3. **IRT 캘리브레이션 활성화** (3번)
   - Secret 생성/확인
   - `calibrate-irt-weekly` 업데이트 또는 `mirt-calibrate` 배포

4. **θ 온라인 업데이트** (4번)
   - 이미 코드 통합 완료, 실제 세션으로 테스트

5. **Quarto 리포팅** (5번)
   - 런너 이미지 빌드 필요
   - S3 설정 필요

