# Alembic Migration Job 수정 가이드

**작성일**: 2025-11-01

## 문제 진단

### 발견된 에러

```
ImportError: Can't find Python file alembic/env.py
```

### 원인 분석

1. **작업 디렉토리 불일치**:
   - Job 설정: `workingDir: /app/seedtest_api`
   - 실제 경로: `/app/apps/seedtest_api` 또는 다른 구조

2. **PYTHONPATH 미설정**:
   - `apps.seedtest_api` 모듈 import를 위해 필요

3. **alembic.ini 경로**:
   - 상대 경로로 설정되어 있어 작업 디렉토리가 중요

## 해결 방법

### 수정된 Job 매니페스트

**파일**: `portal_front/ops/k8s/jobs/alembic-upgrade-staging.yaml`

**주요 변경사항**:

1. **workingDir 수정**: `/app/apps/seedtest_api`
2. **PYTHONPATH 추가**: `/app`
3. **alembic 명령어**: `alembic -c alembic.ini upgrade head` (명시적 config 파일 지정)
4. **디버깅 로그 추가**: 경로 및 파일 존재 확인

### 적용 방법

```bash
# 기존 Job 삭제
kubectl -n seedtest delete job alembic-upgrade-staging

# 새 Job 생성
kubectl -n seedtest apply -f portal_front/ops/k8s/jobs/alembic-upgrade-staging.yaml

# 로그 확인
kubectl -n seedtest logs -f job/alembic-upgrade-staging -c migrator
```

## 검증

### Job 상태 확인

```bash
# Job 상태
kubectl -n seedtest get job alembic-upgrade-staging

# Pod 상태
kubectl -n seedtest get pods -l job-name=alembic-upgrade-staging

# 로그 확인
kubectl -n seedtest logs job/alembic-upgrade-staging -c migrator
```

### 마이그레이션 완료 확인

```bash
# Alembic 버전 확인 (Job 내부)
kubectl -n seedtest exec job/alembic-upgrade-staging -c migrator -- \
  bash -c "cd /app/apps/seedtest_api && alembic -c alembic.ini current"

# 또는 DB 직접 확인
psql $DATABASE_URL -c "SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1;"
```

### 테이블 생성 확인

```sql
-- attempt VIEW 확인
SELECT COUNT(*) FROM attempt LIMIT 1;

-- 새로운 테이블 확인
\d classroom
\d session
\d interest_goal
\d features_topic_daily

-- question.meta 확인
\d question
-- meta 컬럼이 JSONB 타입인지 확인
```

## 트러블슈팅

### 여전히 env.py를 찾지 못하는 경우

1. **컨테이너 내부 경로 확인**:
   ```bash
   kubectl -n seedtest exec <pod-name> -c migrator -- \
     find /app -name "env.py" -type f
   ```

2. **작업 디렉토리 조정**:
   - 실제 경로에 맞춰 `workingDir` 수정

3. **절대 경로로 alembic 실행**:
   ```bash
   python3 -m alembic -c /app/apps/seedtest_api/alembic.ini upgrade head
   ```

### DATABASE_URL 연결 실패

```bash
# Secret 확인
kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d

# Cloud SQL Proxy 확인
kubectl -n seedtest logs job/alembic-upgrade-staging -c cloud-sql-proxy
```

### Import 에러

```bash
# Python 경로 확인
kubectl -n seedtest exec <pod-name> -c migrator -- \
  python3 -c "import sys; print('\n'.join(sys.path))"

# 모듈 import 테스트
kubectl -n seedtest exec <pod-name> -c migrator -- \
  python3 -c "from apps.seedtest_api.db.base import Base; print('OK')"
```

## 예상 결과

성공 시 다음 로그가 나타나야 합니다:

```
=== Alembic Migration Job ===
Working directory: /app/apps/seedtest_api
PYTHONPATH: /app
Alembic config check:
alembic.ini found
alembic/env.py found

Waiting for Cloud SQL Proxy...
Checking database connection...
✅ Connected: PostgreSQL 14.x...
Running Alembic upgrade...
INFO  [alembic.runtime.migration] Running upgrade ...
INFO  [alembic.runtime.migration] Running upgrade ... -> ..., ...
Current Alembic version:
xxx (head)
✅ Migration completed successfully
```

## 참고

- Alembic 문서: https://alembic.sqlalchemy.org/
- 전체 배포 가이드: `apps/seedtest_api/docs/COMPLETE_DEPLOYMENT_GUIDE.md`

