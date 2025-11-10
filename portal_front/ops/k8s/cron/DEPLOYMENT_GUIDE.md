# Analytics Pipeline Deployment Guide

**작성일**: 2025-11-01  
**버전**: V1 Production Ready

## 개요

이 가이드는 DreamSeed Analytics Pipeline의 전체 배치 작업을 K8s에 배포하고 운영하는 방법을 설명합니다.

## 파이프라인 구성 요소

### 1. 일일 KPI 계산 (compute-daily-kpis)
- **파일**: `compute-daily-kpis.yaml`
- **스케줄**: 매일 02:10 UTC
- **기능**: 모든 활성 사용자의 주간 KPI (I_t, E_t, R_t, A_t, P, S) 계산 및 저장
- **입력**: `exam_results`, `ability_estimates`, `mirt_ability`
- **출력**: `weekly_kpi` 테이블
- **상태**: ✅ **Production Ready**

### 2. 일일 피처 집계 (aggregate-features-daily)
- **파일**: `aggregate-features-daily.yaml`
- **스케줄**: 매일 01:15 UTC (compute-daily-kpis 이전)
- **기능**: 사용자/토픽별 일일 집계 (attempts, correct, rt_median, hints, theta, improvement)
- **입력**: `attempt` VIEW, `student_topic_theta`
- **출력**: `features_topic_daily` 테이블
- **상태**: ✅ **Production Ready**

### 3. IRT 주간 캘리브레이션 (mirt-calibrate)
- **파일**: `mirt-calibrate.yaml`
- **스케줄**: 매일 03:00 UTC (피처 집계 이후)
- **기능**: IRT 모형 파라미터 추정 (a, b, c) 및 능력치 (θ) 업데이트
- **입력**: `attempt` VIEW (최근 30일)
- **출력**: `mirt_item_params`, `mirt_ability`, `mirt_fit_meta`
- **의존성**: R IRT Plumber 서비스 (`R_IRT_BASE_URL`)
- **상태**: ✅ **Production Ready** (R IRT 서비스 배포 필요)

### 4. 비활성 사용자 감지 (detect-inactivity)
- **파일**: `detect-inactivity.yaml`
- **스케줄**: 매일 05:00 UTC (KPI 계산 이후)
- **기능**: 7일 이상 미접속 사용자 탐지 및 P/S 재계산
- **입력**: `exam_results`, `features_topic_daily`, `attempt`
- **출력**: `weekly_kpi` (P, S 업데이트)
- **상태**: ✅ **Production Ready**

### 5. 주간 리포트 생성 (generate-weekly-report)
- **파일**: `generate-weekly-report.yaml`
- **스케줄**: 매주 월요일 04:00 UTC
- **기능**: Quarto 기반 주간 학습 리포트 생성 및 S3 업로드
- **입력**: `weekly_kpi`, `mirt_ability`, `interest_goal`, `features_topic_daily`
- **출력**: S3 HTML/PDF, `report_artifacts` 테이블
- **의존성**: Quarto 런너 이미지, S3 버킷, AWS 자격증명
- **상태**: 🟡 **구현 완료, 이미지 빌드 필요**

---

## 배포 순서 (권장)

### Phase 1: 핵심 데이터 파이프라인 (즉시 배포 가능)

#### 1.1 일일 피처 집계 배포
```bash
# 1. 매니페스트 확인
cat portal_front/ops/k8s/cron/aggregate-features-daily.yaml

# 2. 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/aggregate-features-daily.yaml

# 3. 확인
kubectl -n seedtest get cronjob aggregate-features-daily
kubectl -n seedtest describe cronjob aggregate-features-daily

# 4. 수동 테스트 실행
kubectl -n seedtest create job --from=cronjob/aggregate-features-daily \
  aggregate-features-manual-$(date +%Y%m%d-%H%M%S)

# 5. 로그 확인
kubectl -n seedtest logs -f job/aggregate-features-manual-<timestamp>
```

**예상 출력**:
```
[INFO] Aggregating features for 1234 (user, topic, date) combinations; since=2025-10-25, anchor=2025-11-01, dry_run=False
[INFO] Summary: processed=1234, failed=0, duration_ms=8420
```

#### 1.2 일일 KPI 계산 배포
```bash
# 1. 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml

# 2. 확인
kubectl -n seedtest get cronjob compute-daily-kpis

# 3. 수동 테스트 실행
kubectl -n seedtest create job --from=cronjob/compute-daily-kpis \
  compute-daily-kpis-manual-$(date +%Y%m%d-%H%M%S)

# 4. 로그 확인
kubectl -n seedtest logs -f job/compute-daily-kpis-manual-<timestamp>
```

**예상 출력**:
```
[INFO] Computing KPIs for 87 users; week_start=2025-10-27, dry_run=False
[INFO] Summary: processed_users=87, failed_users=0, week=2025-10-27, duration_ms=842
```

#### 1.3 데이터 검증
```sql
-- features_topic_daily 확인
SELECT user_id, topic_id, date, attempts, correct, rt_median, improvement
FROM features_topic_daily
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC, user_id
LIMIT 20;

-- weekly_kpi 확인
SELECT user_id, week_start, 
       kpis->>'I_t' AS improvement,
       kpis->>'E_t' AS efficiency,
       kpis->>'P' AS goal_prob,
       kpis->>'S' AS churn_risk
FROM weekly_kpi
WHERE week_start >= CURRENT_DATE - INTERVAL '14 days'
ORDER BY week_start DESC, user_id
LIMIT 20;
```

---

### Phase 2: IRT 캘리브레이션 (R 서비스 배포 후)

#### 2.1 R IRT Plumber 서비스 배포

**전제 조건**: R IRT Plumber 이미지 빌드 및 푸시 완료

```bash
# 1. Secret 생성 (IRT 서비스 자격증명)
kubectl -n seedtest create secret generic seedtest-irt-credentials \
  --from-literal=R_IRT_BASE_URL='http://r-irt-plumber.seedtest.svc.cluster.local:8000' \
  --from-literal=R_IRT_INTERNAL_TOKEN='<your-internal-token>' \
  --dry-run=client -o yaml | kubectl apply -f -

# 2. R IRT Plumber Deployment 배포 (별도 매니페스트 필요)
# kubectl -n seedtest apply -f portal_front/ops/k8s/deployments/r-irt-plumber.yaml

# 3. Service 확인
kubectl -n seedtest get svc r-irt-plumber

# 4. 헬스체크
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:8000/health
```

#### 2.2 IRT 캘리브레이션 CronJob 배포
```bash
# 1. 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml

# 2. 확인
kubectl -n seedtest get cronjob mirt-calibrate

# 3. 수동 테스트 실행
kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-manual-$(date +%Y%m%d-%H%M%S)

# 4. 로그 확인 (5-10분 소요)
kubectl -n seedtest logs -f job/mirt-calibrate-manual-<timestamp>
```

**예상 출력**:
```
[INFO] Loaded 5000 observations from attempt VIEW
[INFO] Calling R IRT service...
Calibration upsert completed.
```

#### 2.3 IRT 결과 검증
```sql
-- mirt_item_params 확인
SELECT item_id, model, params->>'a' AS discrimination, params->>'b' AS difficulty
FROM mirt_item_params
ORDER BY fitted_at DESC
LIMIT 20;

-- mirt_ability 확인
SELECT user_id, theta, se, model, fitted_at
FROM mirt_ability
ORDER BY fitted_at DESC
LIMIT 20;

-- mirt_fit_meta 확인
SELECT run_id, model_spec, metrics, fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 5;
```

---

### Phase 3: 예측 이벤트 트리거

#### 3.1 비활성 사용자 감지 배포
```bash
# 1. 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/detect-inactivity.yaml

# 2. 확인
kubectl -n seedtest get cronjob detect-inactivity

# 3. 수동 테스트 실행
kubectl -n seedtest create job --from=cronjob/detect-inactivity \
  detect-inactivity-manual-$(date +%Y%m%d-%H%M%S)

# 4. 로그 확인
kubectl -n seedtest logs -f job/detect-inactivity-manual-<timestamp>
```

**예상 출력**:
```
[INFO] Found 12 inactive users (threshold=7 days); dry_run=False
[INFO] Summary: processed=12, failed=0, threshold=7 days, duration_ms=324
```

---

### Phase 4: 리포팅 (선택 사항)

#### 4.1 Quarto 런너 이미지 빌드

**Dockerfile.quarto-runner** (예시):
```dockerfile
FROM rstudio/quarto:latest

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    boto3 \
    sqlalchemy \
    psycopg2-binary

# Copy application code
COPY apps /app/apps
COPY reports /app/reports

WORKDIR /app

# Set Python path
ENV PYTHONPATH=/app
```

```bash
# 이미지 빌드
docker build -f Dockerfile.quarto-runner -t gcr.io/univprepai/seedtest-report-runner:latest .

# 푸시
docker push gcr.io/univprepai/seedtest-report-runner:latest
```

#### 4.2 S3 및 ConfigMap 설정
```bash
# ConfigMap 생성
kubectl -n seedtest create configmap report-config \
  --from-literal=S3_BUCKET='dreamseed-reports' \
  --dry-run=client -o yaml | kubectl apply -f -

# Secret 생성 (AWS 자격증명)
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='<your-access-key>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<your-secret-key>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

#### 4.3 주간 리포트 CronJob 배포
```bash
# 1. 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml

# 2. 확인
kubectl -n seedtest get cronjob generate-weekly-report

# 3. 수동 테스트 실행
kubectl -n seedtest create job --from=cronjob/generate-weekly-report \
  generate-weekly-report-manual-$(date +%Y%m%d-%H%M%S)

# 4. 로그 확인
kubectl -n seedtest logs -f job/generate-weekly-report-manual-<timestamp>
```

---

## 모니터링 및 운영

### 전체 CronJob 상태 확인
```bash
# 모든 CronJob 목록
kubectl -n seedtest get cronjob

# 최근 Job 실행 이력
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp

# 실패한 Job 확인
kubectl -n seedtest get jobs --field-selector status.successful!=1
```

### 로그 조회
```bash
# 특정 CronJob의 최근 실행 로그
CRONJOB_NAME=compute-daily-kpis
LATEST_JOB=$(kubectl -n seedtest get jobs -l cronjob=$CRONJOB_NAME \
  --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl -n seedtest logs job/$LATEST_JOB --tail=100

# 실시간 로그 스트리밍
kubectl -n seedtest logs -f job/$LATEST_JOB
```

### 알림 설정 (Prometheus/Alertmanager)
```yaml
# Example alert rule
- alert: CronJobFailed
  expr: kube_job_status_failed{namespace="seedtest"} > 0
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "CronJob {{ $labels.job_name }} failed"
    description: "Job {{ $labels.job_name }} in namespace {{ $labels.namespace }} has failed."
```

---

## 문제 해결

### 1. Job이 실행되지 않음
```bash
# CronJob 상태 확인
kubectl -n seedtest describe cronjob <cronjob-name>

# Pod 이벤트 확인
kubectl -n seedtest get events --sort-by='.lastTimestamp'

# 이미지 Pull 실패 확인
kubectl -n seedtest get pods | grep ImagePullBackOff
```

### 2. Job이 실패함
```bash
# Pod 로그 확인
kubectl -n seedtest logs <pod-name>

# Pod 상세 정보
kubectl -n seedtest describe pod <pod-name>

# 재시도
kubectl -n seedtest delete job <job-name>
kubectl -n seedtest create job --from=cronjob/<cronjob-name> <job-name>-retry
```

### 3. 데이터베이스 연결 실패
```bash
# Secret 확인
kubectl -n seedtest get secret seedtest-db-credentials -o yaml

# DATABASE_URL 형식 확인 (예: postgresql+psycopg2://user:pass@host:5432/db)
kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Pod에서 직접 연결 테스트
kubectl -n seedtest run psql-test --image=postgres:15 --rm -it --restart=Never -- \
  psql "$DATABASE_URL" -c "SELECT 1"
```

### 4. R IRT 서비스 연결 실패
```bash
# R IRT 서비스 상태 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 서비스 엔드포인트 확인
kubectl -n seedtest get endpoints r-irt-plumber

# 연결 테스트
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:8000/health
```

---

## 우선순위 제안

### 즉시 배포 (Phase 1)
1. **aggregate-features-daily** - 피처 집계는 모든 다운스트림 작업의 기반
2. **compute-daily-kpis** - 일일 KPI 계산으로 P/S 예측 시작

### 단기 (1-2주, Phase 2)
3. **R IRT Plumber 서비스 배포** - IRT 캘리브레이션 인프라
4. **mirt-calibrate** - θ 기반 I_t 계산 활성화

### 중기 (2-4주, Phase 3-4)
5. **detect-inactivity** - 이벤트 기반 P/S 재계산
6. **generate-weekly-report** (선택) - 사용자 리포트 자동화

### 추가 개선 (백로그)
- θ 온라인 업데이트 (세션 종료 트리거)
- Kafka 기반 실시간 ELT (현재는 FastAPI → Postgres 직접 적재)
- R 기반 피처 집계 (dbplyr/arrow, 현재는 Python SQL)

---

## 참고 문서

- **Job별 상세 가이드**:
  - `portal_front/apps/seedtest_api/jobs/README_compute_daily_kpis.md`
  - `apps/seedtest_api/docs/QUARTO_REPORTING_GUIDE.md`
- **Dev Contracts**: `apps/seedtest_api/docs/DEV_CONTRACTS_*.md`
- **테스트**: `apps/seedtest_api/tests/test_compute_daily_kpis_smoke.py`

---

## 체크리스트

### Phase 1 배포 전
- [ ] `seedtest` namespace 존재 확인
- [ ] `seedtest-db-credentials` Secret 생성 (DATABASE_URL)
- [ ] `gcr.io/univprepai/seedtest-api:latest` 이미지 빌드 및 푸시
- [ ] DB 마이그레이션 완료 (features_topic_daily, weekly_kpi 테이블)

### Phase 2 배포 전
- [ ] R IRT Plumber 이미지 빌드 및 푸시
- [ ] `seedtest-irt-credentials` Secret 생성 (R_IRT_BASE_URL, R_IRT_INTERNAL_TOKEN)
- [ ] R IRT Plumber Deployment/Service 배포

### Phase 4 배포 전
- [ ] Quarto 런너 이미지 빌드 및 푸시
- [ ] S3 버킷 생성 및 권한 설정
- [ ] `report-config` ConfigMap 생성 (S3_BUCKET)
- [ ] `aws-s3-credentials` Secret 생성 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- [ ] `report_artifacts` 테이블 마이그레이션 완료

---

**최종 업데이트**: 2025-11-01  
**작성자**: Cascade AI  
**버전**: 1.0
