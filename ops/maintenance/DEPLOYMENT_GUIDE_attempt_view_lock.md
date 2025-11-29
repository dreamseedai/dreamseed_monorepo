# DEPLOYMENT_GUIDE: attempt VIEW V1 Schema Lock

## 대상

- Staging/Production PostgreSQL (exam_results 기반 attempt VIEW 사용 서비스 전반)

---

## 사전 준비

- **CI 녹색**: ✅ 모든 체크 통과 (29개)
  - Code Quality Check, Unit Tests, Integration Tests
  - Security Scan, Docker Build Test, CodeQL
  - K8s Validations, Scope Guard
- **PR 머지 완료**: ✅ PR #73 merged (2025-11-01 07:12 UTC)
  - Commit: `279d6aa1a`
  - Branch: `main`
- **로컬 검증 완료** (2025-10-31):
  - [x] alembic upgrade head (SUCCESS)
  - [x] pytest -k attempt_view_smoke -q (3 passed)
  - [x] Schema validation (11 columns with correct types)
  - [x] isort import order fixed

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

**Last Updated**: 2025-10-31  
**Status**: ✅ Local 검증 완료, Staging 준비 완료
