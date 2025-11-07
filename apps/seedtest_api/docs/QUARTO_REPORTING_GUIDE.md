# Quarto 리포팅 가이드

**작성일**: 2025-11-01

## 개요

주간 학습 리포트를 Quarto로 생성하여 S3에 업로드하고, 리포트 URL을 데이터베이스에 저장합니다.

## 아키텍처

### 데이터 흐름

```
CronJob (매주 월 04:00 UTC) 
  → generate_weekly_report.py
  → KPI/능력/목표/피처 데이터 로드
  → Quarto 렌더 (HTML/PDF)
  → S3 업로드
  → report_artifacts 테이블 저장
```

### 주요 컴포넌트

1. **템플릿**: `reports/quarto/weekly_report.qmd`
2. **Job**: `apps/seedtest_api/jobs/generate_weekly_report.py`
3. **런너 이미지**: `tools/quarto-runner/Dockerfile`
4. **CronJob**: `portal_front/ops/k8s/cron/generate-weekly-report.yaml`

## 설정

### 환경 변수

```bash
# 리포트 주간 시작일 (선택사항, 기본값: 지난 주)
REPORT_WEEK_START=2025-10-27

# 출력 형식 (html, pdf, 기본값: html)
REPORT_FORMAT=html

# S3 설정
S3_BUCKET=seedtest-reports
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_REGION=us-east-1

# 데이터베이스
DATABASE_URL=postgresql://...
```

### Kubernetes Secret 및 ConfigMap

```bash
# S3 Secret 생성
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='<key>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<secret>'

# ConfigMap 생성
kubectl -n seedtest create configmap report-config \
  --from-literal=S3_BUCKET=seedtest-reports \
  --from-literal=AWS_REGION=us-east-1
```

### S3 버킷 설정

1. 버킷 생성:
   ```bash
   aws s3 mb s3://seedtest-reports --region us-east-1
   ```

2. 버킷 정책 (예시):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::<account-id>:user/report-uploader"
         },
         "Action": ["s3:PutObject", "s3:GetObject"],
         "Resource": "arn:aws:s3:::seedtest-reports/*"
       }
     ]
   }
   ```

## 이미지 빌드

### 1. 로컬 빌드

```bash
# 프로젝트 루트에서
docker build -f tools/quarto-runner/Dockerfile \
  -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest .

# 또는 GCR 사용 시
docker build -f tools/quarto-runner/Dockerfile \
  -t gcr.io/univprepai/seedtest-report-runner:latest .
```

### 2. 이미지 푸시

```bash
# Artifact Registry
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest

# 또는 GCR
docker push gcr.io/univprepai/seedtest-report-runner:latest
```

### 3. 빌드 검증

```bash
# 이미지 실행 테스트
docker run --rm \
  -e DATABASE_URL="postgresql://..." \
  -e S3_BUCKET=seedtest-reports \
  asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest \
  python3 -m apps.seedtest_api.jobs.generate_weekly_report
```

## 배포

### 1. 마이그레이션 적용

```bash
# report_artifacts 테이블 생성
cd apps/seedtest_api
export DATABASE_URL="postgresql://..."
alembic upgrade head
```

### 2. CronJob 배포

```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml
```

### 3. 수동 실행 테스트

```bash
# Job 수동 생성
kubectl -n seedtest create job --from=cronjob/generate-weekly-report manual-report-$(date +%s)

# 완료 대기
kubectl -n seedtest wait --for=condition=complete job/manual-report-* --timeout=1800s

# 로그 확인
kubectl -n seedtest logs job/manual-report-* --tail=100
```

## 템플릿 커스터마이징

### 기본 템플릿

`reports/quarto/weekly_report.qmd` 파일을 수정하여 리포트 형식을 변경할 수 있습니다.

### 데이터 구조

템플릿에 전달되는 데이터 (`_data.json`):

```json
{
  "user_id": "user123",
  "week_start": "2025-10-27",
  "kpis": {
    "I_t": 0.75,
    "E_t": 0.82,
    "R_t": 0.65,
    "A_t": 0.90,
    "P": 0.85,
    "S": 0.10
  },
  "ability_trend": [
    {"theta": 1.2, "se": 0.1, "date": "2025-10-27T00:00:00Z"},
    ...
  ],
  "goals": [
    {"subject_id": 1, "interest_1_5": 4, "target_score": 150, "target_date": "2025-12-31"},
    ...
  ],
  "topic_features": [
    {"topic_id": "algebra", "attempts": 50, "correct": 40, "theta_estimate": 1.5, "improvement": 0.1},
    ...
  ]
}
```

### 템플릿 수정 예시

```markdown
---
title: "Custom Weekly Report"
format:
  html:
    theme: cosmo
---

## Custom Section

```{r}
#| echo: false
# Custom analysis here
```

## Recommendations

Custom recommendations based on your data.
```

## 검증

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
# S3에 리포트 존재 확인
aws s3 ls s3://seedtest-reports/reports/ --recursive

# 리포트 다운로드
aws s3 cp s3://seedtest-reports/reports/<path> ./report.html
```

### 3. CronJob 실행 확인

```bash
# 최근 실행된 Job 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | grep generate-weekly-report | tail -5

# CronJob 스케줄 확인
kubectl -n seedtest get cronjob generate-weekly-report
```

## 문제 해결

### Quarto 렌더 실패

**증상**: `Error: quarto render failed`

**해결**:
1. 템플릿 문법 확인:
   ```bash
   docker run --rm -v $(pwd)/reports:/app/reports \
     rstudio/quarto:latest quarto check reports/quarto/weekly_report.qmd
   ```
2. 데이터 파일 확인 (`_data.json` 형식)
3. R 패키지 확인 (필요시 템플릿에 추가)

### S3 업로드 실패

**증상**: `AccessDenied` 또는 `NoCredentialsError`

**해결**:
1. Secret 확인:
   ```bash
   kubectl -n seedtest get secret aws-s3-credentials -o yaml
   ```
2. AWS 자격증명 확인:
   ```bash
   kubectl -n seedtest exec -it <pod> -- env | grep AWS
   ```
3. 버킷 권한 확인

### 데이터 로드 실패

**증상**: `No data found for user` 또는 빈 리포트

**해결**:
1. 사용자 KPI 확인:
   ```sql
   SELECT * FROM weekly_kpi WHERE user_id = 'user123';
   ```
2. Lookback 기간 확인
3. 데이터 품질 확인

### 이미지 빌드 실패

**증상**: `Package not found` 또는 빌드 에러

**해결**:
1. 베이스 이미지 확인: `rstudio/quarto:latest`
2. Python 패키지 의존성 확인
3. Docker 빌드 로그 확인:
   ```bash
   docker build -f tools/quarto-runner/Dockerfile . 2>&1 | tee build.log
   ```

## 성능 최적화

- **병렬 처리**: 여러 사용자 리포트 생성 시 병렬 처리 고려
- **캐싱**: 이전 주 리포트 재사용 (데이터 변경 없을 시)
- **리소스**: 메모리 4Gi, CPU 2000m 권장

## 참고 문서

- Quarto 문서: https://quarto.org/
- S3 설정: https://docs.aws.amazon.com/s3/
