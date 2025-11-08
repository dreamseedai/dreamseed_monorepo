# Runbooks - 운영 스크립트 샘플

이 디렉토리는 **민감한 정보가 없는 샘플 스크립트**만 포함합니다.

## 보안 원칙

- ✅ **커밋 가능**: `.sample` 확장자, 민감 정보 없음
- ❌ **커밋 금지**: 실제 실행 스크립트 (`scripts/local/`, `scripts/staging/`)
- 🔐 **민감 정보**: 비밀번호, API 키, 프로덕션 엔드포인트 등은 절대 커밋 금지

## 사용 방법

### 1. 로컬 실행 디렉토리 생성

```bash
mkdir -p scripts/local
```

### 2. 샘플 스크립트 복사

```bash
# DB Secret 회전 스크립트
cp docs/runbooks/staging_rotate_db_secret.sh.sample scripts/local/staging_rotate_db_secret.sh
chmod +x scripts/local/staging_rotate_db_secret.sh

# 마이그레이션 + 스모크 테스트 스크립트
cp docs/runbooks/staging_migrate_and_smoke.sh.sample scripts/local/staging_migrate_and_smoke.sh
chmod +x scripts/local/staging_migrate_and_smoke.sh
```

### 3. 환경 변수 설정 (선택)

```bash
# .env.local 파일 생성 (gitignore 대상)
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

# 환경 변수 로드
source scripts/local/.env.local
```

### 4. 스크립트 실행

```bash
# DB Secret 회전
scripts/local/staging_rotate_db_secret.sh

# 마이그레이션 + 스모크 테스트
scripts/local/staging_migrate_and_smoke.sh
```

## 스크립트 목록

### `staging_rotate_db_secret.sh.sample`

**목적**: Cloud SQL 비밀번호 회전 + Kubernetes Secret 갱신 + 배포 재시작

**단계**:
1. Cloud SQL 사용자 비밀번호 회전
2. Kubernetes Secret 업데이트
3. Deployment 롤아웃
4. 상태 확인

**필수 변수**:
- `PROJECT`: GCP 프로젝트 ID
- `INSTANCE`: Cloud SQL 인스턴스 이름
- `NS`: Kubernetes 네임스페이스
- `APP`: Deployment 이름
- `SECRET`: Secret 이름
- `DBNAME`: 데이터베이스 이름
- `DBUSER`: 데이터베이스 사용자

**실행 예시**:
```bash
PROJECT=univprepai \
INSTANCE=seedtest-staging \
NS=seedtest \
APP=seedtest-api \
SECRET=seedtest-db-credentials \
DBNAME=dreamseed \
DBUSER=seedstg \
scripts/local/staging_rotate_db_secret.sh
```

### `staging_migrate_and_smoke.sh.sample`

**목적**: Alembic 마이그레이션 실행 + 런타임 스모크 테스트

**단계**:
1. Kubernetes Job으로 Alembic upgrade 실행
2. Job 로그 모니터링
3. 런타임 스모크 테스트 (DATABASE_URL, DB 연결, Alembic 버전)
4. 최종 상태 확인

**필수 변수**:
- `PROJECT`: GCP 프로젝트 ID
- `NS`: Kubernetes 네임스페이스
- `APP_IMAGE`: Docker 이미지 (태그 포함)
- `SECRET`: Secret 이름
- `CONN_NAME`: Cloud SQL Connection Name

**실행 예시**:
```bash
PROJECT=univprepai \
NS=seedtest \
APP_IMAGE=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:f830ff9c2-with-env \
SECRET=seedtest-db-credentials \
CONN_NAME=univprepai:asia-northeast3:seedtest-staging \
scripts/local/staging_migrate_and_smoke.sh
```

## Makefile 통합 (선택)

프로젝트 루트의 `Makefile`에 추가:

```makefile
.PHONY: stg-rotate stg-migrate

stg-rotate:
	@PROJECT=$(PROJECT) INSTANCE=$(INSTANCE) NS=$(NS) APP=$(APP) \
	SECRET=$(SECRET) DBNAME=$(DBNAME) DBUSER=$(DBUSER) \
	scripts/local/staging_rotate_db_secret.sh

stg-migrate:
	@PROJECT=$(PROJECT) NS=$(NS) APP_IMAGE=$(APP_IMAGE) \
	SECRET=$(SECRET) CONN_NAME=$(CONN_NAME) \
	scripts/local/staging_migrate_and_smoke.sh
```

**사용**:
```bash
# .env.local 로드 후
source scripts/local/.env.local

# 단축 명령어
make stg-rotate
make stg-migrate
```

## 보안 체크리스트

- [ ] 실제 비밀번호는 절대 스크립트에 하드코딩하지 않음
- [ ] `scripts/local/` 디렉토리는 `.gitignore`에 포함됨
- [ ] 민감한 환경 변수는 런타임에만 입력
- [ ] 비밀번호는 최소 16자 이상 (32자 권장)
- [ ] 특수문자 포함 강력한 비밀번호 사용
- [ ] 정기적인 비밀번호 회전 (분기별 권장)

## 트러블슈팅

### gcloud 인증 오류
```bash
gcloud auth login
gcloud config set project univprepai
```

### kubectl 컨텍스트 오류
```bash
gcloud container clusters get-credentials <cluster-name> --region <region>
kubectl config current-context
```

### Job 실패 시 로그 확인
```bash
kubectl -n seedtest get jobs
kubectl -n seedtest logs job/<job-name> -c migrator
kubectl -n seedtest describe job/<job-name>
```

### Secret 확인
```bash
kubectl -n seedtest get secret seedtest-db-credentials
kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

## 참고 자료

- [DEPLOYMENT_GUIDE_attempt_view_lock.md](../../DEPLOYMENT_GUIDE_attempt_view_lock.md)
- [Kubernetes 스테이징 배포 가이드](../../DEPLOYMENT_GUIDE_attempt_view_lock.md#kubernetes-스테이징-배포-가이드-2025-11-01-추가)
- [Cloud SQL Proxy 문서](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [Workload Identity 가이드](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
