# Production 배포 스크립트 — attempt VIEW V1

⚠️ **PRODUCTION ENVIRONMENT** - 모든 단계를 신중하게 진행하세요.

## 배포 전 체크리스트

### 필수 사항
- [ ] **Staging 검증 완료**: 스테이징 환경에서 최소 24시간 안정성 확인
- [ ] **백업 완료**: 프로덕션 DB 백업 (pg_dump 또는 managed backup)
- [ ] **변경 승인**: Change Management 승인 완료
- [ ] **팀 알림**: 배포 시작 30분 전 팀 공지
- [ ] **모니터링 준비**: Grafana/Datadog 대시보드 오픈
- [ ] **롤백 계획**: 롤백 스크립트 및 백업 파일 확인

### 권장 사항
- [ ] **배포 시간**: 트래픽이 낮은 시간대 (예: 새벽 2-4시)
- [ ] **On-call 대기**: 최소 2명의 엔지니어 대기
- [ ] **커뮤니케이션**: Slack 채널에서 실시간 진행 상황 공유

## 사용 방법

### 1. 배포 실행

```bash
# DATABASE_URL 설정
export DATABASE_URL='postgresql://USER:PASS@PROD_HOST:PORT/DBNAME'

# 배포 스크립트 실행
bash scripts/production/runbook_attempt_view_lock.sh
```

스크립트는 다음 단계를 진행합니다:
1. Prerequisites 확인
2. 백업 확인
3. 현재 상태 검증
4. 마이그레이션 적용
5. VIEW 검증
6. Smoke 테스트
7. 애플리케이션 검증

### 2. 배포 후 모니터링 (30분)

```bash
# 에러 로그 확인
kubectl logs -f deployment/seedtest-api -n production --tail=100

# 메트릭 확인
# - Error rate: < 0.1%
# - Latency p95: < 500ms
# - Database connections: stable
# - attempt VIEW query count: > 0
```

### 3. 롤백 (필요시)

```bash
export DATABASE_URL='postgresql://USER:PASS@PROD_HOST:PORT/DBNAME'

# 방법 1: Alembic downgrade (권장)
bash scripts/production/rollback_attempt_view.sh
# 선택: 1

# 방법 2: DB 백업 복구 (긴급)
bash scripts/production/rollback_attempt_view.sh
# 선택: 2
```

## 배포 타임라인

| 시간 | 단계 | 예상 소요 |
|------|------|-----------|
| T-30min | 팀 공지 및 준비 | 30분 |
| T-0 | 배포 시작 | - |
| T+5min | 마이그레이션 완료 | 5분 |
| T+10min | 검증 완료 | 5분 |
| T+40min | 모니터링 완료 | 30분 |
| T+60min | 배포 완료 선언 | - |

## 트러블슈팅

### VIEW 생성 실패
```sql
-- VIEW 존재 확인
SELECT * FROM pg_views WHERE viewname = 'attempt';

-- 수동 생성 (긴급)
-- RUNBOOK_attempt_view_lock.md 참조
```

### 성능 저하
```sql
-- 쿼리 분석
EXPLAIN ANALYZE SELECT * FROM attempt LIMIT 100;

-- 인덱스 확인
SELECT * FROM pg_indexes WHERE tablename = 'exam_results';
```

### 롤백 결정 기준
- Error rate > 1% for 5 minutes
- Latency p95 > 2x baseline for 10 minutes
- Critical downstream service failure
- Data integrity issues detected

## 참고 문서

- **배포 가이드**: `DEPLOYMENT_GUIDE_attempt_view_lock.md`
- **Runbook**: `RUNBOOK_attempt_view_lock.md`
- **PR**: #73 (279d6aa1a)
- **스테이징 스크립트**: `scripts/staging/`

## 긴급 연락처

- **On-call Engineer**: [PagerDuty]
- **Database Team**: [Slack #db-ops]
- **DevOps Team**: [Slack #devops]

---

**마지막 업데이트**: 2025-11-01  
**작성자**: Data Engineering Team
