# Staging 배포 스크립트 — attempt VIEW V1

## 사용 방법

### 1. 배포 (Runbook)
```bash
# 경로 A: 서버/도커
export DATABASE_URL='postgresql://USER:PASS@HOST:PORT/DBNAME'
bash scripts/staging/runbook_attempt_view_lock.sh A

# 경로 B: Kubernetes/ArgoCD
export K8S_NAMESPACE=internal  # 기본값: internal
bash scripts/staging/runbook_attempt_view_lock.sh B
```

### 2. 검증
```bash
export DATABASE_URL='postgresql://USER:PASS@HOST:PORT/DBNAME'
bash scripts/staging/verify_attempt_view.sh
```

### 3. 롤백
```bash
# 방법 1: Alembic downgrade
export DATABASE_URL='postgresql://USER:PASS@HOST:PORT/DBNAME'
bash scripts/staging/rollback_attempt_view.sh 1

# 방법 2: DB 백업 복구
export DATABASE_URL='postgresql://USER:PASS@HOST:PORT/DBNAME'
bash scripts/staging/rollback_attempt_view.sh 2
```

## 체크리스트

### 배포 전
- [ ] DATABASE_URL 설정 확인
- [ ] 백업 수행 (권장)
- [ ] Alembic 리비전 확인

### 배포 중
- [ ] 마이그레이션 실행
- [ ] 스모크 테스트 통과
- [ ] 애플리케이션 재시작 (필요 시)

### 배포 후
- [ ] VIEW 정의 확인
- [ ] 컬럼 타입 검증
- [ ] 성능 확인 (EXPLAIN ANALYZE)
- [ ] 헬스체크 통과
- [ ] 다운스트림 서비스 점검

## 참고
- 배포 가이드: `DEPLOYMENT_GUIDE_attempt_view_lock.md`
- Runbook: `RUNBOOK_attempt_view_lock.md`
