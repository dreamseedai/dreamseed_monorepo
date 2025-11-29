# Quarto 리포트 배치 생성 가이드

**작성일**: 2025-11-01

## 개요

기존 단일 사용자 리포트 생성 방식을 배치 처리로 확장하여, 주간으로 모든 활성 사용자에 대해 리포트를 자동 생성합니다.

---

## 파일 구조

### 1. 배치 Job 스크립트

**파일**: `apps/seedtest_api/jobs/generate_weekly_report_batch.py`

**주요 기능**:
- DB에서 활성 사용자 목록 조회
- Cohort 필터링 지원 (SQL WHERE 절)
- 순차 처리 (향후 병렬 처리 가능)
- 진행 상황 추적 및 에러 처리

**사용 예시**:
```bash
# 모든 활성 사용자에 대해 리포트 생성
python3 -m apps.seedtest_api.jobs.generate_weekly_report_batch \
  --week 2025-01-06

# 특정 조직(cohort)만 처리
python3 -m apps.seedtest_api.jobs.generate_weekly_report_batch \
  --week 2025-01-06 \
  --cohort "org_id = 'org123'"

# 최대 500명만 처리
python3 -m apps.seedtest_api.jobs.generate_weekly_report_batch \
  --week 2025-01-06 \
  --max-users 500

# Dry-run (S3 업로드/DB 저장 스킵)
python3 -m apps.seedtest_api.jobs.generate_weekly_report_batch \
  --week 2025-01-06 \
  --dry-run
```

### 2. Kubernetes CronJob

**파일**: `portal_front/ops/k8s/cron/generate-weekly-report-batch.yaml`

**주요 설정**:
- 스케줄: 매주 월요일 04:00 UTC
- 자동 주 계산: 지난 주 월요일 날짜 계산
- 리소스: 메모리 4-8Gi, CPU 2-4 cores
- Secret 주입: AWS, DB 자격증명

---

## 환경 변수

### 필수

- `DATABASE_URL`: PostgreSQL 연결 문자열
- `S3_BUCKET`: S3 버킷 이름
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS 자격증명

### 선택

- `REPORT_FORMAT`: 리포트 포맷 (`html` 또는 `pdf`, 기본값: `pdf`)
- `AWS_REGION`: AWS 리전 (기본값: `ap-northeast-2`)
- `COHORT_FILTER`: SQL WHERE 절 (예: `org_id = 'org123'`)
- `MAX_USERS`: 최대 처리 사용자 수 (기본값: 1000)

---

## 배포

### 1. 이미지 빌드 및 푸시

```bash
# 이미지 빌드
docker build -f tools/quarto-runner/Dockerfile \
  -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest .

# 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest
```

### 2. Secret 생성

```bash
# AWS S3 Secret
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='<key>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<secret>'

# 또는 ExternalSecret 사용 (권장)
kubectl apply -f portal_front/ops/k8s/secrets/external-secrets-example.yaml
```

### 3. CronJob 배포

```bash
# 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report-batch.yaml

# 확인
kubectl -n seedtest get cronjob generate-weekly-report-batch
```

---

## 테스트

### 수동 Job 실행

```bash
# Job 수동 생성
kubectl -n seedtest create job --from=cronjob/generate-weekly-report-batch \
  manual-batch-test-$(date +%s)

# 완료 대기
kubectl -n seedtest wait --for=condition=complete job/manual-batch-test-* --timeout=3600s

# 로그 확인
kubectl -n seedtest logs job/manual-batch-test-* --tail=100
```

### 로컬 테스트

```bash
export DATABASE_URL="postgresql://..."
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export S3_BUCKET="seedtest-reports"
export REPORT_FORMAT="pdf"

# 배치 실행
python3 -m apps.seedtest_api.jobs.generate_weekly_report_batch \
  --week 2025-01-06 \
  --max-users 10 \
  --dry-run
```

---

## Cohort 필터링

특정 그룹의 사용자만 리포트를 생성하려면 `COHORT_FILTER` 환경 변수나 `--cohort` 인자를 사용합니다.

### 예시

```yaml
# CronJob에서 특정 조직만 처리
env:
  - name: COHORT_FILTER
    value: "org_id = 'org123'"
```

```bash
# CLI에서 특정 조직만 처리
python3 -m apps.seedtest_api.jobs.generate_weekly_report_batch \
  --week 2025-01-06 \
  --cohort "org_id = 'org123'"
```

**주의**: SQL WHERE 절이므로 SQL injection 방지를 위해 신뢰할 수 있는 입력만 사용하세요.

---

## 모니터링

### Job 상태 확인

```bash
# CronJob 상태
kubectl -n seedtest get cronjob generate-weekly-report-batch

# 최근 실행된 Job
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | \
  grep generate-weekly-report-batch | tail -5
```

### 리포트 생성 확인

```sql
-- 리포트 생성 통계
SELECT 
    DATE_TRUNC('week', generated_at) AS week,
    COUNT(*) AS report_count,
    COUNT(DISTINCT user_id) AS unique_users
FROM report_artifacts
WHERE generated_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('week', generated_at)
ORDER BY week DESC;

-- 특정 사용자 리포트 확인
SELECT user_id, week_start, format, url, generated_at
FROM report_artifacts
WHERE user_id = 'user123'
ORDER BY generated_at DESC
LIMIT 10;
```

### S3 업로드 확인

```bash
# S3 파일 목록
aws s3 ls s3://seedtest-reports/reports/ --recursive | \
  grep "$(date -u -d 'last monday - 7 days' +%Y-%m-%d)" | wc -l

# 특정 주 리포트 확인
aws s3 ls s3://seedtest-reports/reports/ --recursive | \
  grep "2025-01-06"
```

---

## 성능 최적화

### 현재 제한

- 순차 처리 (병렬 처리 미구현)
- 메모리: 4-8Gi (큰 리포트 생성 시 증가 가능)
- 시간: 사용자당 약 10-30초 (Quarto 렌더링 시간 포함)

### 향후 개선

1. **병렬 처리**: `multiprocessing` 또는 `concurrent.futures` 사용
2. **배치 분할**: 큰 사용자 집합을 여러 Job으로 분할
3. **캐싱**: 동일한 주 데이터 재사용
4. **점진적 처리**: 실패한 사용자만 재처리

---

## 문제 해결

### 메모리 부족

```bash
# 리소스 증가
kubectl -n seedtest patch cronjob generate-weekly-report-batch \
  -p '{"spec":{"jobTemplate":{"spec":{"template":{"spec":{"containers":[{"name":"generate-weekly-report","resources":{"limits":{"memory":"16Gi"}}}]}}}}}}}'
```

### 리포트 생성 실패

```bash
# 로그 확인
kubectl -n seedtest logs job/<job-name> --tail=200

# 특정 사용자 재생성
python3 -m apps.seedtest_api.jobs.generate_weekly_report \
  --user user123 --week 2025-01-06
```

### S3 업로드 실패

```bash
# AWS 자격증명 확인
kubectl -n seedtest get secret aws-s3-credentials -o jsonpath='{.data.AWS_ACCESS_KEY_ID}' | base64 -d

# 버킷 권한 확인
aws s3 ls s3://seedtest-reports/
```

---

## 참고

- **단일 사용자 생성**: `apps/seedtest_api/jobs/generate_weekly_report.py`
- **Quarto 리포팅 가이드**: `apps/seedtest_api/docs/QUARTO_REPORTING_GUIDE.md`
- **전체 배포 가이드**: `apps/seedtest_api/docs/COMPLETE_DEPLOYMENT_GUIDE.md`

---

**배치 리포트 생성 파이프라인 준비 완료!** 🎉

