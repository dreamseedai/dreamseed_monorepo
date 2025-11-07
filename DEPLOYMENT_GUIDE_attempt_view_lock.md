# DEPLOYMENT_GUIDE: attempt VIEW V1 Schema Lock

## 대상

- Staging/Production PostgreSQL (exam_results 기반 attempt VIEW 사용 서비스 전반)

---

## 사전 준비

- **CI 녹색**: Kustomize/Kubeconform + Kyverno/Conftest
- **PR 승인 및 머지 준비**: 승인 라벨/리뷰 완료
- **로컬 검증 완료** (2025-10-31):
  - [x] alembic upgrade head (SUCCESS)
  - [x] pytest -k attempt_view_smoke -q (2 passed, 3 skipped)
  - [x] Schema validation (11 columns with correct types)

---

## Staging 절차 (6단계)

### 1) 마이그 확인

```bash
# 커밋/리비전 최신화 확인
cd apps/seedtest_api
alembic history | tail -n 5

# 시뮬레이션 (선택)
alembic upgrade head --sql > /tmp/ddl.sql
```

### 2) DB 백업 (선택)

```bash
# pg_dump 백업
pg_dump -Fc -h <host> -U <user> -d <db> -f backup_before_attempt_lock.dump

# 또는 managed backup (AWS RDS snapshot, Cloud SQL backup 등)
```

### 3) 마이그 적용

```bash
# Staging DB 연결
export DATABASE_URL="postgresql://USER:PASS@STAGING_HOST:PORT/DBNAME"

# 마이그레이션 적용
alembic upgrade head

# 예상 출력:
# INFO [alembic.runtime.migration] Running upgrade 20251031_2120 -> 20251101_0900
```

### 4) 스모크 테스트

```bash
# pytest 스모크 테스트
pytest -k attempt_view_smoke -q

# 예상: 5/5 passed (데이터 존재 시)

# 수동 쿼리 검증
psql $DATABASE_URL -c "SELECT count(*) FROM attempt;"
psql $DATABASE_URL -c "SELECT * FROM attempt ORDER BY completed_at DESC LIMIT 5;"
```

### 5) 다운스트림 점검

```bash
# ETL/리포트/대시보드에서 attempt를 참조하는 쿼리 샘플 실행
# - IRT 캘리브레이션 파이프라인
# - KPI 백필 쿼리 (features_topic_daily)
# - Analytics 대시보드 쿼리

# 성능/스캔 비용 확인
# 필요 시 인덱스 추가:
# CREATE INDEX ix_attempt_student_time ON attempt(student_id, completed_at);
```

### 6) 결과 기록/승인

```bash
# 스모크 5/5 passed 스크린샷 캡처
# 실행 로그 첨부
# 승인 코멘트 남기고 Production CR 생성
```

---

## Production 절차

### 변경관리 승인/윈도우 확보

- **CR 승인**: 변경 요청서 생성 및 승인
- **Maintenance Window**: 유지보수 시간대 예약 (off-peak 권장)

### 적용

```bash
# Production DB 연결 (bastion/VPN via)
export DATABASE_URL="postgresql://PROD_USER:PASS@PROD_HOST:PORT/PROD_DB"

# 마이그레이션 적용
alembic upgrade head

# 동일 스모크/점검 수행 (Staging과 동일)
pytest -k attempt_view_smoke -q
```

### 24시간 모니터링

- API 오류율 (분석/리포트 경로)
- ETL 실패/지연 (작업 로그/알람)
- 대시보드/쿼리 응답시간
- DB 부하 (세션/쿼리 Top/N)

---

## 모니터링 항목

| 메트릭 | 임계값 | 알림 채널 |
|--------|--------|----------|
| attempt VIEW 쿼리 지연 | > 500ms | #alerts-database |
| 쿼리 오류율 | > 0.1% | #alerts-critical |
| IRT 캘리브레이션 실패 | > 1 failure | #data-science |
| KPI 백필 작업 지연 | > 2x baseline | #data-engineering |

---

## 롤백

```bash
# Option 1: Alembic downgrade
alembic downgrade <down_revision_of_view>

# Option 2: Manual DROP (emergency)
psql $DATABASE_URL -c "DROP VIEW IF EXISTS attempt CASCADE;"

# Option 3: 백업 복원
psql $DATABASE_URL < backup_before_attempt_lock.dump

# 다운스트림 재검증
pytest -k attempt_view_smoke -q
```

---

## 부록: VIEW 스펙 요약

### attempt V1 고정 스펙

**컬럼/타입/변환/시도번호/결정적 ID/UUID**는 IRT/지표 파이프라인 공통 기준입니다.

| 컬럼 | 타입 | 규칙 |
|------|------|------|
| `id` | bigint | (exam_result_id + question_id) md5 64bit |
| `student_id` | uuid | user_id 캐스트 or md5-based UUID |
| `item_id` | bigint | questions[].question_id |
| `correct` | boolean | is_correct \| correct (default: FALSE) |
| `response_time_ms` | int | time_spent_sec * 1000 (default: 0) |
| `hint_used` | boolean | used_hints > 0 |
| `attempt_no` | int | ROW_NUMBER by (student_id, item_id) |
| `started_at` | timestamptz | completed_at - time_spent_sec |
| `completed_at` | timestamptz | COALESCE(updated_at, created_at) |
| `session_id` | text | exam_results.session_id |
| `topic_id` | text | questions[].topic |

### V1 Schema Lock 정책

- 컬럼명/타입 변경 금지 → V2 migration + RFC 필요
- `student_id` 해시 알고리즘 고정
- `attempt_no` 정렬 로직 고정
- 향후 MV(Materialized View)/인덱스 최적화는 별도 PR

---

## 참고 자료

- **Migration**: `apps/seedtest_api/alembic/versions/20251101_0900_attempt_view_lock.py`
- **Tests**: `apps/seedtest_api/tests/test_attempt_view_smoke.py`
- **Docs**: `apps/seedtest_api/docs/IRT_STANDARDIZATION.md`
- **Branch**: https://github.com/dreamseedai/dreamseed_monorepo/tree/feature/db/attempt-view-lock-PR-7A

---

## Kubernetes 스테이징 배포 가이드 (2025-11-01 추가)

### 환경 정보

**Cloud SQL**
- Instance: `seedtest-staging`
- Connection: `univprepai:asia-northeast3:seedtest-staging`
- Database: `dreamseed`
- User: `seedstg`

**Kubernetes**
- Namespace: `seedtest`
- Deployment: `seedtest-api`
- Image: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest`
- Secret: `seedtest-db-credentials`

### 1) 보안 조치 (비밀번호 회전)

```bash
# 1-1) Cloud SQL 비밀번호 회전
PROJECT=univprepai
INSTANCE=seedtest-staging
DBUSER=seedstg
NEWPASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

gcloud sql users set-password $DBUSER --instance=$INSTANCE --password="$NEWPASS"

# 1-2) Kubernetes Secret 갱신
NS=seedtest
SECRET=seedtest-db-credentials
DBNAME=dreamseed

kubectl -n $NS create secret generic $SECRET \
  --from-literal=DATABASE_URL="postgresql+psycopg://$DBUSER:$NEWPASS@127.0.0.1:5432/$DBNAME" \
  --dry-run=client -o yaml | kubectl apply -f -

# 1-3) 배포 재시작
kubectl -n $NS rollout restart deploy/seedtest-api
kubectl -n $NS rollout status deploy/seedtest-api --timeout=180s
```

### 2) 런타임 스모크 테스트 (90초)

```bash
NS=seedtest
APP=seedtest-api
POD=$(kubectl -n $NS get pod -l app=$APP -o jsonpath='{.items[0].metadata.name}')

# 2-1) ENV 주입 확인
kubectl -n $NS exec $POD -c api -- sh -c 'echo ${DATABASE_URL:+DATABASE_URL_set}'

# 2-2) DB 연결 핑
kubectl -n $NS exec $POD -c api -- python -c "
import os, psycopg
url=os.environ['DATABASE_URL'].replace('postgresql+psycopg','postgresql')
with psycopg.connect(url) as c:
    with c.cursor() as cur:
        cur.execute('SELECT 1;')
        print(cur.fetchone())
print('DB OK')
"

# 2-3) Alembic 버전 확인
kubectl -n $NS exec $POD -c api -- bash -c "cd /app/seedtest_api && PYTHONPATH=/app alembic current"
```

**예상 출력:**
```
DATABASE_URL_set
(1,)
DB OK
20251101_0900_attempt_view_lock (head)
```

### 3) 마이그레이션 실행 (Pod 내부)

```bash
POD=$(kubectl -n seedtest get pod -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')

# Alembic 마이그레이션
kubectl -n seedtest exec $POD -c api -- bash -c \
  "cd /app/seedtest_api && PYTHONPATH=/app alembic upgrade head"

# 현재 버전 확인
kubectl -n seedtest exec $POD -c api -- bash -c \
  "cd /app/seedtest_api && PYTHONPATH=/app alembic current"
```

### 4) Cloud SQL Proxy 사이드카 설정

**리소스 제한 및 헬스 프로브 권장:**

```yaml
- name: cloud-sql-proxy
  image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.11.3
  args:
    - "--structured-logs"
    - "--port=5432"
    - "univprepai:asia-northeast3:seedtest-staging"
  securityContext:
    runAsNonRoot: true
  resources:
    requests:
      cpu: "50m"
      memory: "64Mi"
    limits:
      cpu: "500m"
      memory: "256Mi"
  livenessProbe:
    tcpSocket:
      port: 5432
    periodSeconds: 10
  readinessProbe:
    tcpSocket:
      port: 5432
    periodSeconds: 5
```

### 5) Workload Identity 설정

```bash
# GSA에 Cloud SQL 권한 부여
GSA=seedtest-deployer@univprepai.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding univprepai \
  --member="serviceAccount:${GSA}" \
  --role="roles/cloudsql.client"

# Kubernetes SA 어노테이션
kubectl -n seedtest annotate serviceaccount seedtest-api \
  iam.gke.io/gcp-service-account=$GSA --overwrite

# Workload Identity 바인딩
gcloud iam service-accounts add-iam-policy-binding $GSA \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:univprepai.svc.id.goog[seedtest/seedtest-api]"

gcloud iam service-accounts add-iam-policy-binding $GSA \
  --role roles/iam.serviceAccountTokenCreator \
  --member "serviceAccount:univprepai.svc.id.goog[seedtest/seedtest-api]"
```

### 6) 주요 해결 사항

1. **ModuleNotFoundError: shared** → `COPY shared/ /app/shared/` Dockerfile에 추가
2. **ModuleNotFoundError: psycopg** → `psycopg[binary]==3.2.1` requirements.txt에 추가
3. **alembic/env.py 누락** → 표준 Alembic env.py 생성
4. **alembic_version VARCHAR(32) 부족** → `ALTER COLUMN version_num TYPE VARCHAR(64)`
5. **Cloud SQL 권한 오류** → Workload Identity + IAM 권한 설정

### 7) 보안 권장사항

- ✅ 비밀번호 32자 이상 랜덤 생성
- ✅ Secret 회전 후 즉시 배포 재시작
- ⚠️ Cloud SQL 공개 IP 비활성화 권장 (프록시 사이드카 사용 시)
- ⚠️ Authorized networks 최소화
- ⚠️ GSA 권한 최소화 (roles/cloudsql.client만 유지)

### 8) Alembic 구조 안정화

**권장 개선사항:**
- `psycopg2-binary` 제거, `psycopg` (v3)만 유지
- Revision ID를 32자 해시로 표준화 (또는 고정 길이 타임스탬프)
- `alembic/env.py`를 Dockerfile에 명시적으로 포함 확인

### 9) 외부 비밀 관리 (향후)

**ExternalSecret + GCP Secret Manager 통합:**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: seedtest-db-credentials
  namespace: seedtest
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: gcpsm-secret-store
    kind: SecretStore
  target:
    name: seedtest-db-credentials
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: seedtest-staging-database-url
```

### 10) 관측성 체크리스트

- [ ] Cloud SQL 자동 백업 활성화
- [ ] PITR (Point-in-Time Recovery) 설정
- [ ] `/health`, `/ready` 엔드포인트 추가
- [ ] Kubernetes Liveness/Readiness Probe 설정
- [ ] Cloud Monitoring 알림 설정
- [ ] 런북에 "비밀번호 회전 → Secret → 롤아웃 → 스모크" 체크리스트 추가

### 11) 운영 스크립트 (Runbooks)

**보안 원칙**: 민감 정보가 없는 샘플만 커밋, 실제 실행 스크립트는 로컬에서 관리

**샘플 스크립트 위치**: `docs/runbooks/*.sh.sample`  
**로컬 실행 스크립트**: `scripts/local/*.sh` (gitignore 대상)

#### 사용 방법

```bash
# 1. 로컬 디렉토리 생성
mkdir -p scripts/local

# 2. 샘플 복사
cp docs/runbooks/staging_rotate_db_secret.sh.sample scripts/local/staging_rotate_db_secret.sh
cp docs/runbooks/staging_migrate_and_smoke.sh.sample scripts/local/staging_migrate_and_smoke.sh
chmod +x scripts/local/*.sh

# 3. 환경 변수 설정 (선택)
cat > scripts/local/.env.local <<EOF
PROJECT=univprepai
INSTANCE=seedtest-staging
NS=seedtest
APP=seedtest-api
SECRET=seedtest-db-credentials
DBNAME=dreamseed
DBUSER=seedstg
APP_IMAGE=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest
CONN_NAME=univprepai:asia-northeast3:seedtest-staging
EOF

source scripts/local/.env.local

# 4. 실행
scripts/local/staging_rotate_db_secret.sh
scripts/local/staging_migrate_and_smoke.sh
```

#### 제공 스크립트

1. **`staging_rotate_db_secret.sh.sample`**
   - Cloud SQL 비밀번호 회전
   - Kubernetes Secret 갱신
   - Deployment 롤아웃
   - 상태 확인

2. **`staging_migrate_and_smoke.sh.sample`**
   - Alembic 마이그레이션 (Kubernetes Job)
   - 런타임 스모크 테스트
   - 로그 모니터링
   - 최종 상태 확인

자세한 내용은 [`docs/runbooks/README.md`](../docs/runbooks/README.md) 참고

---

**Last Updated**: 2025-11-01  
**Status**: ✅ Staging 배포 완료 (Cloud SQL + Kubernetes)
