# 다음 단계 3-5 구현 가이드

**작성일**: 2025-11-01

## 현재 상태

### ✅ 완료된 항목

1. **일일 KPI 산출** (`compute_daily_kpis.py`)
   - CronJob 배포 완료: `compute-daily-kpis` (02:10 UTC)
   - 경로: `python3 -m seedtest_api.jobs.compute_daily_kpis`

2. **토픽 일별 피처 집계** (`aggregate_features_daily.py`)
   - CronJob 배포 완료: `aggregate-features-daily` (02:25 UTC)
   - 경로: `python3 -m apps.seedtest_api.jobs.aggregate_features_daily`
   - ⚠️ 주의: 기존 파일(`aggregate-features.yaml`)과 병존 중, 경로 확인 필요

---

## 3) IRT 주간 캘리브레이션 라인 정합

### 구현 상태

- ✅ `apps/seedtest_api/jobs/mirt_calibrate.py`: 이미 구현 완료
  - `attempt` VIEW 우선 사용
  - Fallback: `responses` 테이블 → `exam_results` JSON
  - R IRT Plumber 서비스 호출 (`/irt/calibrate`)
  - `mirt_item_params`, `mirt_ability`, `mirt_fit_meta` 업서트

### 필요한 작업

#### A. CronJob 확인/수정

**파일**: `portal_front/ops/k8s/cron/calibrate-irt.yaml` (이미 존재)

**확인 사항**:
1. 스케줄 확인 (현재: 매주 일요일 03:10 UTC)
2. 명령어 경로 확인: `apps.seedtest_api.jobs.mirt_calibrate`
3. 환경 변수:
   - `R_IRT_BASE_URL` (Secret에서)
   - `R_IRT_INTERNAL_TOKEN` (Secret에서)
   - `IRT_CALIB_LOOKBACK_DAYS=30`
   - `IRT_MODEL=2PL`

**권장 수정**:
- 스케줄: 매일 03:00 UTC로 변경 (주간 → 일일)
- 또는 주간 유지: 매주 일요일 03:00 UTC

#### B. R IRT Plumber 서비스 확인

- 서비스 배포 상태 확인
- Secret 생성 확인:
  ```bash
  kubectl -n seedtest get secret seedtest-irt-credentials
  ```

### 완료 후 효과

- `mirt_item_params`: 문항 파라미터(a, b, c) 채워짐
- `mirt_ability`: 사용자 능력(θ) 추정치 채워짐
- `features_topic_daily.theta_mean/theta_sd` 업데이트 가능 (Dev 계약서 6)

---

## 4) θ 온라인 업데이트 (세션 종료 트리거)

### 구현 상태

- ✅ `apps/seedtest_api/services/irt_update_service.py`: 구현 완료
- ✅ `apps/seedtest_api/services/result_service.py`: `finish_exam()` 통합 완료

### 필요한 작업

#### A. 배포 및 테스트

**현재 상태**: 코드 통합 완료, 자동 실행됨

**확인 사항**:
1. 세션 종료 시 자동 트리거 확인
2. R IRT Plumber 서비스 `/irt/score` 엔드포인트 확인
3. `mirt_ability` 테이블 업데이트 확인

**테스트 방법**:
```bash
# 세션 완료 후 확인
SELECT user_id, theta, se, fitted_at
FROM mirt_ability
WHERE user_id = '<test_user_id>'
ORDER BY fitted_at DESC
LIMIT 1;
```

#### B. (선택) 수동 트리거 엔드포인트 추가

필요시 FastAPI 엔드포인트 추가:
```python
@router.post("/analysis/irt/update")
async def trigger_irt_update(user_id: str, ...):
    trigger_ability_update(user_id, ...)
```

---

## 5) 리포팅 (Quarto)

### 구현 상태

- ✅ `apps/seedtest_api/jobs/generate_weekly_report.py`: 구현 완료
- ✅ `reports/quarto/weekly_report.qmd`: 템플릿 완료
- ✅ `apps/seedtest_api/alembic/versions/20251101_1700_report_artifacts.py`: 마이그레이션 완료

### 필요한 작업

#### A. Quarto 런너 이미지 빌드

**Dockerfile 필요** (`Dockerfile.quarto-runner`):

```dockerfile
FROM rstudio/quarto:latest

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install boto3 sqlalchemy psycopg2-binary

# Copy application code
COPY apps/seedtest_api /app/apps/seedtest_api
COPY reports /app/reports

WORKDIR /app
```

**빌드 및 푸시**:
```bash
docker build -f Dockerfile.quarto-runner -t gcr.io/univprepai/seedtest-report-runner:latest .
docker push gcr.io/univprepai/seedtest-report-runner:latest
```

#### B. CronJob 환경 설정

**Secret 생성** (AWS S3):
```bash
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='...' \
  --from-literal=AWS_SECRET_ACCESS_KEY='...'
```

**ConfigMap 생성** (S3 버킷):
```bash
kubectl -n seedtest create configmap report-config \
  --from-literal=S3_BUCKET=my-reports-bucket
```

#### C. 마이그레이션 적용

```bash
# report_artifacts 테이블 생성
cd apps/seedtest_api
alembic upgrade head
```

#### D. CronJob 배포

**파일**: `portal_front/ops/k8s/cron/generate-weekly-report.yaml`

**스케줄**: 매주 월요일 04:00 UTC (이미 설정됨)

---

## 우선순위별 진행 계획

### 즉시 진행 가능 (코드 완료)

1. **3) IRT 캘리브레이션 CronJob 활성화**
   - `calibrate-irt.yaml` 스케줄 확인/수정
   - Secret 확인
   - 수동 테스트 실행

2. **4) θ 온라인 업데이트**
   - 이미 통합 완료, 실제 세션으로 테스트
   - 필요시 로그 모니터링

### 준비 필요한 작업

3. **5) Quarto 리포팅**
   - Quarto 런너 이미지 빌드 (가장 중요)
   - S3 설정 및 Secret 생성
   - 마이그레이션 적용

---

## 트러블슈팅 체크리스트

### 이미지 풀 실패 (`ImagePullBackOff`)

**원인**: `gcr.io/univprepai/seedtest-api:latest` 이미지 미존재

**해결**:
1. 이미지 빌드 및 푸시:
   ```bash
   docker build -t gcr.io/univprepai/seedtest-api:latest .
   docker push gcr.io/univprepai/seedtest-api:latest
   ```

2. 또는 기존 이미지 사용 (예: `ghcr.io/dreamseedai/seedtest-api:latest`)

3. CronJob 매니페스트에서 이미지 경로 수정

### 명령어 경로 불일치

**현재 상황**:
- 배포된 CronJob: `apps.seedtest_api.jobs.aggregate_features_daily`
- 새로 만든 파일: `seedtest_api.jobs.aggregate_features_daily`

**해결**: 경로 통일 필요 (프로젝트 구조에 따라 결정)

### 메모리 부족

**증상**: `Insufficient memory`, `OOMKilled`

**해결**: CronJob의 `resources.limits.memory` 증가

---

## 다음 작업 순서

1. **이미지 문제 해결** (우선)
   - `gcr.io/univprepai/seedtest-api:latest` 빌드 또는 경로 변경

2. **3) IRT 캘리브레이션 활성화**
   - CronJob 스케줄 확인 및 Secret 확인

3. **4) θ 온라인 업데이트 테스트**
   - 실제 세션으로 검증

4. **5) Quarto 리포팅 설정**
   - 런너 이미지 빌드
   - S3 설정

