# 파이프라인 구현 상태 점검

**작성일**: 2025-11-01

## 🔍 현재 상태 진단

### 발견된 문제

1. **이미지 풀 실패**
   - 에러: `gcr.io/univprepai/seedtest-api:latest: not found`
   - 영향: 모든 CronJob이 이미지 풀에 실패할 수 있음
   - 해결 필요: 이미지 빌드 또는 경로 변경

2. **Secret 누락**
   - `seedtest-irt-credentials` 또는 `r-irt-credentials` 없음
   - IRT 캘리브레이션 CronJob 실행 불가

3. **명령어 경로 불일치**
   - 배포된 CronJob: `apps.seedtest_api.jobs.*`
   - 일부 파일: `seedtest_api.jobs.*` 또는 `portal_front.apps.seedtest_api.jobs.*`

---

## ✅ 완료된 구현 항목

### 1. 일일 KPI 산출
- ✅ 코드: `apps/seedtest_api/jobs/compute_daily_kpis.py`
- ✅ CronJob: `compute-daily-kpis` (02:10 UTC)
- ⚠️ 이미지 경로 확인 필요

### 2. 토픽 일별 피처 집계
- ✅ 코드: `apps/seedtest_api/jobs/aggregate_features_daily.py`
- ✅ CronJob: `aggregate-features-daily` (02:25 UTC)
- ⚠️ 기존 파일(`aggregate-features.yaml`)과 병존, 경로 확인 필요

### 3. IRT 주간 캘리브레이션
- ✅ 코드: `apps/seedtest_api/jobs/mirt_calibrate.py` (개선 완료)
- ✅ CronJob: `calibrate-irt-weekly` (매주 일요일 03:10 UTC)
- ⚠️ Secret 누락, R IRT 서비스 확인 필요

### 4. θ 온라인 업데이트
- ✅ 코드: `apps/seedtest_api/services/irt_update_service.py`
- ✅ 통합: `finish_exam()` 자동 트리거
- ✅ 배포: 코드 통합만으로 완료

### 5. Quarto 리포팅
- ✅ 코드: `apps/seedtest_api/jobs/generate_weekly_report.py`
- ✅ 템플릿: `reports/quarto/weekly_report.qmd`
- ✅ 마이그레이션: `20251101_1700_report_artifacts.py`
- ⚠️ Quarto 런너 이미지 빌드 필요
- ⚠️ S3 Secret/ConfigMap 생성 필요

### 6. 비활성 사용자 감지
- ✅ 코드: `apps/seedtest_api/jobs/detect_inactivity.py`
- ✅ CronJob: `detect-inactivity` (05:00 UTC)
- ⚠️ 이미지 경로 확인 필요

---

## 🔧 즉시 수정 필요 사항

### A. 이미지 경로 문제 해결

**옵션 1: 이미지 빌드 및 푸시**
```bash
# Dockerfile 확인 후 빌드
docker build -t gcr.io/univprepai/seedtest-api:latest -f apps/seedtest_api/Dockerfile .
docker push gcr.io/univprepai/seedtest-api:latest
```

**옵션 2: 기존 이미지 사용**
- `ghcr.io/dreamseedai/seedtest-api:latest` 사용 가능 여부 확인
- 또는 다른 레지스트리 이미지 사용

**옵션 3: 로컬 개발용**
- `ImagePullPolicy: Never` 설정 (이미지 미리 로드 필요)

### B. 명령어 경로 통일

**현재 혼재 상태**:
- `apps.seedtest_api.jobs.*` (일부 CronJob)
- `seedtest_api.jobs.*` (일부 파일)
- `portal_front.apps.seedtest_api.jobs.*` (일부 파일)

**권장**: 프로젝트 루트 기준으로 통일
- 컨테이너 내부: `/app` 디렉터리가 루트
- PYTHONPATH 설정 또는 절대 경로 사용

**수정 예시**:
```yaml
env:
  - name: PYTHONPATH
    value: "/app"
command: ["python3", "-m", "apps.seedtest_api.jobs.aggregate_features_daily"]
```

### C. IRT Secret 생성

```bash
# R IRT Plumber 서비스 정보 확인 후 생성
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='<your-token>' \
  --from-literal=base_url='http://r-irt-plumber.seedtest.svc.cluster.local:8000'
```

또는 기존 Secret 확인:
```bash
kubectl -n seedtest get secrets | grep irt
```

---

## 📋 다음 단계 실행 순서

### 1단계: 이미지 문제 해결 (최우선)

```bash
# 옵션 A: 이미지 빌드
docker build -t gcr.io/univprepai/seedtest-api:latest .
docker push gcr.io/univprepai/seedtest-api:latest

# 옵션 B: 기존 이미지 확인 및 경로 변경
kubectl -n seedtest get deployments -o yaml | grep image:
# 결과에 따라 CronJob 이미지 경로 수정
```

### 2단계: 3) IRT 캘리브레이션 활성화

```bash
# Secret 확인/생성
kubectl -n seedtest get secret r-irt-credentials || \
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='<token>'

# CronJob 스케줄 확인 (현재: 매주 일요일)
# 필요시 일일로 변경:
kubectl -n seedtest patch cronjob calibrate-irt-weekly -p '{"spec":{"schedule":"0 3 * * *"}}'

# 수동 실행 테스트
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly manual-irt-test-$(date +%s)
```

### 3단계: 4) θ 온라인 업데이트 검증

```bash
# 세션 완료 후 확인
kubectl -n seedtest logs -l app=seedtest-api | grep "trigger_ability_update"

# DB 확인
psql $DATABASE_URL -c "SELECT user_id, theta, fitted_at FROM mirt_ability ORDER BY fitted_at DESC LIMIT 5;"
```

### 4단계: 5) Quarto 리포팅 설정

```bash
# A. Quarto 런너 이미지 빌드
docker build -f Dockerfile.quarto-runner -t gcr.io/univprepai/seedtest-report-runner:latest .
docker push gcr.io/univprepai/seedtest-report-runner:latest

# B. S3 Secret 생성
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='...' \
  --from-literal=AWS_SECRET_ACCESS_KEY='...'

# C. ConfigMap 생성
kubectl -n seedtest create configmap report-config \
  --from-literal=S3_BUCKET=my-reports-bucket

# D. 마이그레이션 적용
cd apps/seedtest_api && alembic upgrade head

# E. CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml
```

---

## 🎯 권장 작업 순서

1. **이미지 문제 해결** (모든 Job의 전제조건)
2. **IRT Secret 생성 및 캘리브레이션 활성화** (3번)
3. **θ 온라인 업데이트 검증** (4번, 이미 통합됨)
4. **Quarto 런너 이미지 빌드 및 리포팅 설정** (5번)

---

## 참고

- 전체 파이프라인 요약: `apps/seedtest_api/docs/PIPELINE_IMPLEMENTATION_SUMMARY.md`
- 다음 단계 가이드: `apps/seedtest_api/docs/NEXT_STEPS_3_4_5.md`

