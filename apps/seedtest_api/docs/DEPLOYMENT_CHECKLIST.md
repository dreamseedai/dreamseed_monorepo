# 파이프라인 배포 체크리스트

**작성일**: 2025-11-01

## ✅ 완료된 수정 사항

### 이미지 경로 수정

모든 CronJob의 이미지를 실제 배포 환경 이미지로 변경:
- **이전**: `gcr.io/univprepai/seedtest-api:latest` (존재하지 않음)
- **현재**: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:f830ff9c2-with-env`

**수정된 파일**:
- `portal_front/ops/k8s/cron/compute-daily-kpis.yaml`
- `portal_front/ops/k8s/cron/aggregate-features-daily.yaml`
- `portal_front/ops/k8s/cron/calibrate-irt.yaml`
- `portal_front/ops/k8s/cron/mirt-calibrate.yaml`
- `portal_front/ops/k8s/cron/detect-inactivity.yaml`

### 명령어 경로 통일

모든 CronJob의 명령어를 `apps.seedtest_api.jobs.*`로 통일:
- **수정 전**: `seedtest_api.jobs.*` 또는 `portal_front.apps.seedtest_api.jobs.*`
- **수정 후**: `apps.seedtest_api.jobs.*`

---

## 📋 배포 전 체크리스트

### 필수 확인 사항

#### 1. 이미지 접근 권한
```bash
# 이미지가 클러스터에서 접근 가능한지 확인
kubectl -n seedtest run test-image --image=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:f830ff9c2-with-env --rm -it --restart=Never -- echo "OK"
```

#### 2. Secret 존재 확인
```bash
# 데이터베이스 Secret
kubectl -n seedtest get secret seedtest-db-credentials

# IRT Secret (필요시 생성)
kubectl -n seedtest get secret r-irt-credentials || \
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='<your-token>'
```

#### 3. 서비스 확인
```bash
# R IRT Plumber 서비스 확인
kubectl -n seedtest get svc r-irt-plumber
```

---

## 🚀 배포 순서

### 1단계: 기존 CronJob 업데이트

```bash
# 업데이트된 매니페스트 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/aggregate-features-daily.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/detect-inactivity.yaml
```

### 2단계: IRT 캘리브레이션 설정

```bash
# Secret 확인/생성
kubectl -n seedtest get secret r-irt-credentials || \
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='<your-token>'

# CronJob 스케줄 확인 (현재: 매주 일요일 03:10 UTC)
# 필요시 일일로 변경:
kubectl -n seedtest patch cronjob calibrate-irt-weekly -p '{"spec":{"schedule":"0 3 * * *"}}'

# 또는 신규 CronJob 사용 (mirt-calibrate.yaml)
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml
```

### 3단계: 수동 테스트 실행

```bash
# 각 Job 수동 실행 테스트
kubectl -n seedtest create job --from=cronjob/compute-daily-kpis manual-test-kpis-$(date +%s)
kubectl -n seedtest create job --from=cronjob/aggregate-features-daily manual-test-features-$(date +%s)
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly manual-test-irt-$(date +%s)
kubectl -n seedtest create job --from=cronjob/detect-inactivity manual-test-inactivity-$(date +%s)
```

### 4단계: 로그 확인

```bash
# Job 상태 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -5

# 파드 로그 확인
JOB_NAME=<job-name>
kubectl -n seedtest logs job/$JOB_NAME

# 실시간 로그
kubectl -n seedtest logs -f job/$JOB_NAME
```

---

## 🔍 문제 해결 가이드

### 이미지 풀 실패

**증상**: `ImagePullBackOff`, `ErrImagePull`

**해결**:
1. 이미지 태그 확인 (특정 버전 사용 권장)
2. 레지스트리 접근 권한 확인
3. ImagePullSecret 확인:
   ```bash
   kubectl -n seedtest get sa default -o yaml | grep imagePullSecrets
   ```

### 명령어 실행 실패

**증상**: `ModuleNotFoundError`, `No module named 'apps'`

**해결**:
1. PYTHONPATH 환경 변수 추가:
   ```yaml
   env:
     - name: PYTHONPATH
       value: "/app"
   ```
2. 또는 절대 경로 사용: `/app/apps/seedtest_api/jobs/...`

### 데이터베이스 연결 실패

**증상**: `connection refused`, `authentication failed`

**해결**:
1. Secret 확인:
   ```bash
   kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d
   ```
2. 데이터베이스 서버 상태 확인
3. 네트워크 정책 확인

### R IRT 서비스 연결 실패

**증상**: `connection refused`, `service not found`

**해결**:
1. 서비스 존재 확인:
   ```bash
   kubectl -n seedtest get svc r-irt-plumber
   ```
2. 엔드포인트 확인:
   ```bash
   kubectl -n seedtest get endpoints r-irt-plumber
   ```
3. 서비스 URL 확인:
   - `calibrate-irt.yaml`: `http://r-irt-plumber.seedtest.svc.cluster.local:8000`
   - 서비스 이름/포트가 일치하는지 확인

---

## ✅ 배포 후 검증

### 1. CronJob 상태 확인

```bash
kubectl -n seedtest get cronjobs
```

**확인 사항**:
- `SCHEDULE` 올바른지 확인
- `SUSPEND`가 `False`인지 확인
- `LAST SCHEDULE` 타임스탬프 확인 (다음 실행 예정 시간)

### 2. 최근 Job 실행 확인

```bash
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -10
```

**확인 사항**:
- `STATUS`가 `Complete` 또는 `Running`
- `AGE`가 최근인지 확인

### 3. 로그 확인

```bash
# 각 Job의 최근 실행 로그
for job in $(kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp -o name | tail -5); do
  echo "=== $job ==="
  kubectl -n seedtest logs $job --tail=20
done
```

### 4. 데이터베이스 확인

```sql
-- weekly_kpi 최근 업데이트 확인
SELECT user_id, week_start, kpis, updated_at
FROM weekly_kpi
ORDER BY updated_at DESC
LIMIT 5;

-- features_topic_daily 최근 집계 확인
SELECT user_id, topic_id, date, attempts, computed_at
FROM features_topic_daily
ORDER BY computed_at DESC
LIMIT 5;

-- mirt_ability 최근 업데이트 확인
SELECT user_id, theta, se, fitted_at
FROM mirt_ability
ORDER BY fitted_at DESC
LIMIT 5;
```

---

## 📊 예상 실행 스케줄

| 시간 (UTC) | CronJob | 기능 |
|-----------|---------|------|
| 02:10 | `compute-daily-kpis` | 일일 KPI 계산 |
| 02:25 | `aggregate-features-daily` | 일별 피처 집계 |
| 03:00 | `mirt-calibrate` 또는 `calibrate-irt-weekly` | IRT 캘리브레이션 |
| 05:00 | `detect-inactivity` | 비활성 사용자 감지 |
| 04:00 (월) | `generate-weekly-report` | 주간 리포트 생성 |

---

## 참고 문서

- 구현 상태: `apps/seedtest_api/docs/IMPLEMENTATION_STATUS_CHECK.md`
- 다음 단계: `apps/seedtest_api/docs/NEXT_STEPS_3_4_5.md`
- 전체 파이프라인: `apps/seedtest_api/docs/PIPELINE_IMPLEMENTATION_SUMMARY.md`

