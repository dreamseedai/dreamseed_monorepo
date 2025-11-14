# IRT Analytics Pipeline - 빠른 배포 가이드

**최종 업데이트**: 2025-11-02 00:14 KST  
**소요 시간**: 5분  
**난이도**: ⭐ 쉬움

---

## 🚀 2단계 빠른 배포

ExternalSecret 없이 직접 Secret을 생성하여 즉시 배포할 수 있습니다.

### Step 1: Secret 생성 (1분)

```bash
# 1. 데이터베이스 Secret 생성
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://user:password@host:5432/seedtest'

# 2. R IRT 토큰 Secret 생성 (선택)
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='your-secret-token-here'

# 3. Secret 확인
kubectl -n seedtest get secrets | grep -E "seedtest-db-credentials|r-irt-credentials"
```

**예상 출력**:
```
seedtest-db-credentials   Opaque   1      5s
r-irt-credentials         Opaque   1      3s
```

### Step 2: CronJob 배포 (1분)

```bash
# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 확인
kubectl -n seedtest get cronjob
```

**예상 출력**:
```
NAME                   SCHEDULE    SUSPEND   ACTIVE   LAST SCHEDULE   AGE
calibrate-irt-nightly  0 3 * * *   False     0        <none>          10s
```

---

## ✅ 배포 완료! 이제 테스트하세요

### 테스트 실행 (5분)

```bash
# 1. One-off Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-nightly \
  calibrate-irt-test-$(date +%s)

# 2. 로그 실시간 확인
kubectl -n seedtest logs -f job/calibrate-irt-test-<timestamp>
```

**예상 로그**:
```
[INFO] Loaded 12345 observations from attempt VIEW
[INFO] Loaded 50 anchors/seeds from question.meta
[INFO] Calling R IRT service...
[INFO] Linking constants received: {'slope': 1.02, 'intercept': 0.05}
✅ IRT calibration completed successfully
```

### 데이터베이스 검증

```sql
-- 결과 확인
SELECT COUNT(*) FROM mirt_item_params WHERE fitted_at >= NOW() - INTERVAL '1 hour';
SELECT COUNT(*) FROM mirt_ability WHERE fitted_at >= NOW() - INTERVAL '1 hour';
SELECT model_spec->'linking_constants' FROM mirt_fit_meta ORDER BY fitted_at DESC LIMIT 1;
```

---

## 🔧 Secret 업데이트 방법

### DATABASE_URL 변경

```bash
# 기존 Secret 삭제
kubectl -n seedtest delete secret seedtest-db-credentials

# 새로운 값으로 재생성
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://new-user:new-pass@new-host:5432/seedtest'

# CronJob 재시작 (다음 실행 시 자동 반영)
kubectl -n seedtest rollout restart cronjob/calibrate-irt-nightly
```

### R IRT 토큰 변경

```bash
# 기존 Secret 삭제
kubectl -n seedtest delete secret r-irt-credentials

# 새로운 토큰으로 재생성
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='new-token-here'
```

---

## 🐛 문제 해결

### 문제 1: Secret 이미 존재

**증상**:
```
Error from server (AlreadyExists): secrets "seedtest-db-credentials" already exists
```

**해결**:
```bash
# 기존 Secret 삭제 후 재생성
kubectl -n seedtest delete secret seedtest-db-credentials
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://...'
```

### 문제 2: CronJob 실행 안됨

**증상**:
```bash
kubectl -n seedtest get jobs
# No resources found
```

**원인**: CronJob은 스케줄에 따라 자동 실행됩니다 (매일 03:00 UTC)

**해결**: 수동으로 Job 생성
```bash
kubectl -n seedtest create job --from=cronjob/calibrate-irt-nightly \
  calibrate-irt-manual-$(date +%s)
```

### 문제 3: Job 실패 (DATABASE_URL 오류)

**증상**:
```bash
kubectl -n seedtest logs job/calibrate-irt-test-<timestamp>
# Error: could not connect to database
```

**해결**:
```bash
# 1. Secret 값 확인
kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d
echo ""

# 2. 올바른 형식인지 확인
# 형식: postgresql://user:password@host:5432/dbname

# 3. Secret 재생성
kubectl -n seedtest delete secret seedtest-db-credentials
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://correct-url'
```

### 문제 4: R IRT 서비스 연결 실패

**증상**:
```
[ERROR] R IRT service call failed after 3 attempts
```

**해결**:
```bash
# 1. R IRT 서비스 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 2. Health check
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz

# 3. 서비스 재시작
kubectl -n seedtest rollout restart deployment r-irt-plumber
```

---

## 📊 일일 운영

### 매일 아침 체크 (09:00 KST)

```bash
# 1. 어젯밤 Job 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -5

# 2. 최근 로그 확인
kubectl -n seedtest logs -l job-name=calibrate-irt-nightly --tail=50 --since=12h

# 3. 실패한 Job 확인
kubectl -n seedtest get jobs --field-selector status.successful!=1
```

### 데이터베이스 확인

```sql
-- 일일 체크 쿼리
SELECT 
    'Last Calibration' AS check_type,
    MAX(fitted_at)::text AS result
FROM mirt_item_params
UNION ALL
SELECT 
    'Item Count',
    COUNT(*)::text
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 day'
UNION ALL
SELECT 
    'User Count',
    COUNT(*)::text
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 day'
UNION ALL
SELECT 
    'Anchor Count',
    COUNT(*)::text
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb;
```

---

## 🔄 CronJob 관리

### 일시 중지

```bash
# CronJob 중지
kubectl -n seedtest patch cronjob calibrate-irt-nightly -p '{"spec":{"suspend":true}}'

# 확인
kubectl -n seedtest get cronjob calibrate-irt-nightly
# SUSPEND: True
```

### 재개

```bash
# CronJob 재개
kubectl -n seedtest patch cronjob calibrate-irt-nightly -p '{"spec":{"suspend":false}}'

# 확인
kubectl -n seedtest get cronjob calibrate-irt-nightly
# SUSPEND: False
```

### 스케줄 변경

```bash
# 매주 일요일 03:00 UTC로 변경
kubectl -n seedtest patch cronjob calibrate-irt-nightly \
  -p '{"spec":{"schedule":"0 3 * * 0"}}'

# 확인
kubectl -n seedtest get cronjob calibrate-irt-nightly -o jsonpath='{.spec.schedule}'
```

---

## 📚 관련 문서

### 빠른 참조
- **이 문서**: 2단계 빠른 배포
- **[DEPLOYMENT_COMMANDS.md](./DEPLOYMENT_COMMANDS.md)**: 전체 배포 명령어
- **[DEPLOYMENT_EXECUTION_GUIDE.md](./DEPLOYMENT_EXECUTION_GUIDE.md)**: ExternalSecret 사용 (고급)

### 상세 가이드
- **[IRT_CALIBRATION_GUIDE.md](../../apps/seedtest_api/docs/IRT_CALIBRATION_GUIDE.md)**: IRT 완전 가이드
- **[INTEGRATION_TEST_GUIDE.md](../../apps/seedtest_api/docs/INTEGRATION_TEST_GUIDE.md)**: 테스트 시나리오
- **[README_IRT_PIPELINE.md](../../apps/seedtest_api/docs/README_IRT_PIPELINE.md)**: 전체 가이드

---

## ✅ 체크리스트

### 배포 완료
- [ ] `seedtest-db-credentials` Secret 생성
- [ ] `r-irt-credentials` Secret 생성 (선택)
- [ ] `calibrate-irt-nightly` CronJob 배포
- [ ] CronJob 스케줄 확인 (`0 3 * * *`)

### 테스트 완료
- [ ] One-off Job 생성 및 실행
- [ ] 로그에 "IRT calibration completed successfully"
- [ ] mirt_item_params 업데이트 확인
- [ ] mirt_ability 업데이트 확인
- [ ] linking_constants 저장 확인

### 운영 준비
- [ ] 일일 체크 스크립트 준비
- [ ] 알림 설정 (선택)
- [ ] 모니터링 대시보드 (선택)

---

## 🎯 다음 단계

### 즉시 실행
```bash
# 1. Secret 생성
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://user:password@host:5432/seedtest'

kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='your-token'

# 2. CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 3. 테스트
kubectl -n seedtest create job --from=cronjob/calibrate-irt-nightly \
  calibrate-irt-test-$(date +%s)
```

### 고급 설정 (선택)
- **ExternalSecret 사용**: `DEPLOYMENT_EXECUTION_GUIDE.md` 참고
- **GLMM 모델 추가**: `R_GLMM_SERVICE_GUIDE.md` 참고
- **전체 Analytics 파이프라인**: `ADVANCED_ANALYTICS_ROADMAP.md` 참고

---

**최종 업데이트**: 2025-11-02 00:14 KST  
**작성자**: Cascade AI  
**소요 시간**: 5분  
**난이도**: ⭐ 쉬움

**축하합니다! 5분 만에 배포 완료! 🎉**
