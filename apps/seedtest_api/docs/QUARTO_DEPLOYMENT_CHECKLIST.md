# Quarto 리포팅 배포 체크리스트

**작성일**: 2025-11-01

## ✅ 구현 완료된 파일

1. **템플릿**: `reports/quarto/weekly_report.qmd`
   - ✅ KPI 요약, 능력 추세, 목표, 토픽 성능, 추천 Top-N 포함

2. **Job**: `apps/seedtest_api/jobs/generate_weekly_report.py`
   - ✅ 데이터 로드 (KPI, 능력, 목표, 토픽 피처, 추천)
   - ✅ Quarto 렌더
   - ✅ S3 업로드
   - ✅ `report_artifacts` 테이블 저장

3. **Dockerfile**: `tools/quarto-runner/Dockerfile`
   - ✅ R + Quarto + Python 환경
   - ✅ boto3, sqlalchemy, psycopg2-binary 포함

4. **CronJob**: `portal_front/ops/k8s/cron/generate-weekly-report.yaml`
   - ✅ 스케줄: 매주 월요일 04:00 UTC
   - ✅ 환경 변수 설정 완료

---

## 📋 배포 전 체크리스트

### 1. 이미지 빌드

```bash
# 이미지 빌드
docker build -f tools/quarto-runner/Dockerfile \
  -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest .

# 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest
```

### 2. S3 설정

```bash
# 버킷 생성 (아직 없는 경우)
aws s3 mb s3://seedtest-reports --region us-east-1

# 버킷 정책 확인 (필요시 수정)
aws s3api get-bucket-policy --bucket seedtest-reports
```

### 3. Kubernetes Secret 생성

```bash
# S3 자격증명 Secret
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='<your-access-key>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<your-secret-key>'

# 기존 Secret 확인
kubectl -n seedtest get secret aws-s3-credentials
```

### 4. Kubernetes ConfigMap 생성

```bash
# 리포트 설정 ConfigMap
kubectl -n seedtest create configmap report-config \
  --from-literal=S3_BUCKET=seedtest-reports \
  --from-literal=AWS_REGION=us-east-1

# ConfigMap 확인
kubectl -n seedtest get configmap report-config
```

### 5. 마이그레이션 적용

```bash
# report_artifacts 테이블 생성 확인
cd apps/seedtest_api
export DATABASE_URL="postgresql://..."
alembic upgrade head

# 또는 K8s Pod에서 실행
kubectl -n seedtest exec -it <seedtest-api-pod> -- \
  bash -c "cd /app/apps/seedtest_api && alembic upgrade head"
```

### 6. CronJob 배포

```bash
# CronJob 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml

# CronJob 확인
kubectl -n seedtest get cronjob generate-weekly-report
```

---

## 🧪 테스트

### 수동 Job 실행

```bash
# Job 수동 생성
kubectl -n seedtest create job --from=cronjob/generate-weekly-report manual-test-$(date +%s)

# 완료 대기 (최대 30분)
kubectl -n seedtest wait --for=condition=complete job/manual-test-* --timeout=1800s

# 로그 확인
kubectl -n seedtest logs job/manual-test-* --tail=100
```

### 로컬 테스트 (dry-run)

```bash
# 환경 변수 설정
export DATABASE_URL="postgresql://..."
export REPORT_FORMAT=html

# Dry-run 실행 (S3 업로드 없음)
python -m apps.seedtest_api.jobs.generate_weekly_report --dry-run

# 특정 주 리포트 생성
python -m apps.seedtest_api.jobs.generate_weekly_report --week 2025-10-27 --dry-run
```

---

## ✅ 검증

### 1. 리포트 생성 확인

```sql
SELECT 
    user_id,
    week_start,
    format,
    url,
    generated_at
FROM report_artifacts
ORDER BY generated_at DESC
LIMIT 10;
```

### 2. S3 업로드 확인

```bash
# S3 파일 목록
aws s3 ls s3://seedtest-reports/reports/ --recursive | head -20

# 리포트 다운로드
aws s3 cp s3://seedtest-reports/reports/<user_id>/<week_start>/report.html ./report.html
```

### 3. CronJob 실행 확인

```bash
# 최근 실행된 Job
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | grep generate-weekly-report | tail -5

# CronJob 상태
kubectl -n seedtest get cronjob generate-weekly-report -o yaml | grep -A 5 "status:"
```

---

## 🔍 문제 해결

### 이미지 빌드 실패

```bash
# 베이스 이미지 확인
docker pull rstudio/quarto:latest

# 빌드 로그 확인
docker build -f tools/quarto-runner/Dockerfile . 2>&1 | tee build.log
```

### S3 업로드 실패

```bash
# Secret 확인
kubectl -n seedtest get secret aws-s3-credentials -o jsonpath='{.data}' | base64 -d

# AWS 자격증명 테스트
aws s3 ls s3://seedtest-reports/
```

### Quarto 렌더 실패

```bash
# 템플릿 문법 확인
docker run --rm -v $(pwd)/reports:/app/reports \
  rstudio/quarto:latest quarto check reports/quarto/weekly_report.qmd
```

### 데이터 로드 실패

```sql
-- 사용자 KPI 확인
SELECT * FROM weekly_kpi WHERE user_id = '<user_id>' ORDER BY week_start DESC LIMIT 5;

-- 토픽 피처 확인
SELECT * FROM features_topic_daily WHERE user_id = '<user_id>' ORDER BY date DESC LIMIT 10;
```

---

## 📚 참고 문서

- Quarto 리포팅 가이드: `apps/seedtest_api/docs/QUARTO_REPORTING_GUIDE.md`
- 전체 배포 가이드: `apps/seedtest_api/docs/COMPLETE_DEPLOYMENT_GUIDE.md`

