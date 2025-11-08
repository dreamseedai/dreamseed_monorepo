# Kubernetes 배포 가이드

**최종 업데이트**: 2025-11-02 00:14 KST

---

## 📚 배포 가이드 선택

### ⭐ 빠른 배포 (권장 - 5분)

**[QUICK_DEPLOY.md](./QUICK_DEPLOY.md)** - 2단계로 즉시 배포

```bash
# 1. Secret 생성
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://...'

# 2. CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml
```

**대상**: 빠르게 시작하고 싶은 경우  
**난이도**: ⭐ 쉬움  
**소요 시간**: 5분

---

### 🔐 ExternalSecret 배포 (프로덕션 권장 - 15분)

**[DEPLOYMENT_EXECUTION_GUIDE.md](./DEPLOYMENT_EXECUTION_GUIDE.md)** - GCP Secret Manager 연동

```bash
# 1. ExternalSecret 설정
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# 2. Secret 확인
kubectl -n seedtest get secret calibrate-irt-credentials

# 3. CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml
```

**대상**: 프로덕션 환경, Secret 자동 관리 필요  
**난이도**: ⭐⭐ 보통  
**소요 시간**: 15분 (사전 준비 포함)

---

### 📖 전체 배포 명령어

**[DEPLOYMENT_COMMANDS.md](./DEPLOYMENT_COMMANDS.md)** - 모든 배포 명령어 모음

- ExternalSecret 배포
- CronJob 배포
- One-off Job 실행
- Health check
- 로그 확인
- 롤백 방법
- 문제 해결

**대상**: 전체 명령어 참조 필요  
**난이도**: ⭐⭐ 보통

---

### 🤖 자동 배포 스크립트

**[deploy-irt-pipeline.sh](./deploy-irt-pipeline.sh)** - 원클릭 배포

```bash
# Dry-run
./portal_front/ops/k8s/deploy-irt-pipeline.sh --dry-run

# 실제 배포
./portal_front/ops/k8s/deploy-irt-pipeline.sh
```

**대상**: 전체 파이프라인 자동 배포  
**난이도**: ⭐ 쉬움  
**소요 시간**: 10분

---

## 📂 파일 구조

```
portal_front/ops/k8s/
├── README.md                              # 이 문서
├── QUICK_DEPLOY.md                        # ⭐ 빠른 배포 (5분)
├── DEPLOYMENT_COMMANDS.md                 # 전체 명령어 모음
├── DEPLOYMENT_EXECUTION_GUIDE.md          # ExternalSecret 배포 (15분)
├── deploy-irt-pipeline.sh                 # 자동 배포 스크립트
│
├── secrets/
│   └── externalsecret-calibrate-irt.yaml  # ExternalSecret 정의
│
├── cron/
│   ├── calibrate-irt.yaml                 # 기본 CronJob (Secret 직접 참조)
│   ├── calibrate-irt-with-externalsecret.yaml  # ExternalSecret 통합
│   ├── fit-growth-glmm.yaml               # GLMM CronJob
│   └── ...
│
├── jobs/
│   ├── calibrate-irt-now.yaml             # One-off IRT Job
│   ├── glmm-fit-progress-now.yaml         # One-off GLMM Job
│   └── ...
│
└── r-irt-plumber/
    ├── externalsecret.yaml                # R IRT 토큰 ExternalSecret
    └── ...
```

---

## 🚀 빠른 시작

### 1단계: 배포 방법 선택

| 방법 | 소요 시간 | 난이도 | 프로덕션 | 문서 |
|------|----------|--------|---------|------|
| **빠른 배포** | 5분 | ⭐ | ⚠️ | [QUICK_DEPLOY.md](./QUICK_DEPLOY.md) |
| **ExternalSecret** | 15분 | ⭐⭐ | ✅ | [DEPLOYMENT_EXECUTION_GUIDE.md](./DEPLOYMENT_EXECUTION_GUIDE.md) |
| **자동 스크립트** | 10분 | ⭐ | ✅ | [deploy-irt-pipeline.sh](./deploy-irt-pipeline.sh) |

### 2단계: 배포 실행

#### 빠른 배포 (권장)

```bash
# Secret 생성
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://user:password@host:5432/seedtest'

kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='your-token'

# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml
```

#### ExternalSecret 배포

```bash
# ExternalSecret 설정
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# Secret 확인 (1-2분 대기)
kubectl -n seedtest get secret calibrate-irt-credentials

# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml
```

### 3단계: 테스트

```bash
# One-off Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-nightly \
  calibrate-irt-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/calibrate-irt-test-<timestamp>
```

### 4단계: 검증

```sql
-- 데이터베이스 검증
SELECT COUNT(*) FROM mirt_item_params WHERE fitted_at >= NOW() - INTERVAL '1 hour';
SELECT COUNT(*) FROM mirt_ability WHERE fitted_at >= NOW() - INTERVAL '1 hour';
SELECT model_spec->'linking_constants' FROM mirt_fit_meta ORDER BY fitted_at DESC LIMIT 1;
```

---

## 🔍 배포 후 확인

### CronJob 확인

```bash
# CronJob 목록
kubectl -n seedtest get cronjobs

# 상세 정보
kubectl -n seedtest describe cronjob calibrate-irt-nightly

# 스케줄 확인
kubectl -n seedtest get cronjob calibrate-irt-nightly -o jsonpath='{.spec.schedule}'
# 예상: 0 3 * * * (매일 03:00 UTC)
```

### Secret 확인

```bash
# Secret 목록
kubectl -n seedtest get secrets | grep -E "seedtest-db|r-irt"

# Secret 상세
kubectl -n seedtest describe secret seedtest-db-credentials
```

### Job 실행 이력

```bash
# 최근 Job 목록
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -10

# 실패한 Job 확인
kubectl -n seedtest get jobs --field-selector status.successful!=1
```

---

## 🐛 문제 해결

### 일반적인 문제

| 문제 | 원인 | 해결 방법 | 문서 |
|------|------|----------|------|
| Secret 없음 | Secret 미생성 | Secret 생성 | [QUICK_DEPLOY.md](./QUICK_DEPLOY.md#step-1-secret-생성-1분) |
| Job 실패 | DB 연결 오류 | DATABASE_URL 확인 | [QUICK_DEPLOY.md](./QUICK_DEPLOY.md#문제-3-job-실패-database_url-오류) |
| R IRT 연결 실패 | 서비스 미배포 | R IRT 서비스 확인 | [DEPLOYMENT_COMMANDS.md](./DEPLOYMENT_COMMANDS.md#r-irt-서비스-연결-실패) |
| ExternalSecret 오류 | GSM 설정 오류 | ClusterSecretStore 확인 | [DEPLOYMENT_EXECUTION_GUIDE.md](./DEPLOYMENT_EXECUTION_GUIDE.md#문제-1-externalsecret-상태가-secretsyncederror) |

### 상세 문제 해결

- **빠른 배포**: [QUICK_DEPLOY.md - 문제 해결](./QUICK_DEPLOY.md#🐛-문제-해결)
- **ExternalSecret**: [DEPLOYMENT_EXECUTION_GUIDE.md - 문제 해결](./DEPLOYMENT_EXECUTION_GUIDE.md#🐛-문제-해결)
- **전체 명령어**: [DEPLOYMENT_COMMANDS.md - 문제 해결](./DEPLOYMENT_COMMANDS.md#🐛-문제-해결)

---

## 📊 일일 운영

### 매일 아침 체크 (09:00 KST)

```bash
# 1. 어젯밤 Job 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -5

# 2. 최근 로그 확인
kubectl -n seedtest logs -l job-name=calibrate-irt-nightly --tail=50 --since=12h

# 3. 데이터베이스 확인
psql $DATABASE_URL -c "
SELECT 
    'mirt_item_params' AS table_name,
    COUNT(*) AS count,
    MAX(fitted_at) AS last_update
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 day';
"
```

### CronJob 관리

```bash
# 일시 중지
kubectl -n seedtest patch cronjob calibrate-irt-nightly -p '{"spec":{"suspend":true}}'

# 재개
kubectl -n seedtest patch cronjob calibrate-irt-nightly -p '{"spec":{"suspend":false}}'

# 스케줄 변경 (매주 일요일)
kubectl -n seedtest patch cronjob calibrate-irt-nightly \
  -p '{"spec":{"schedule":"0 3 * * 0"}}'
```

---

## 📚 추가 문서

### IRT Analytics Pipeline

- **[README_IRT_PIPELINE.md](../../apps/seedtest_api/docs/README_IRT_PIPELINE.md)** - 전체 가이드 시작점
- **[FINAL_IMPLEMENTATION_STATUS.md](../../apps/seedtest_api/docs/FINAL_IMPLEMENTATION_STATUS.md)** - 구현 상태
- **[INTEGRATION_TEST_GUIDE.md](../../apps/seedtest_api/docs/INTEGRATION_TEST_GUIDE.md)** - 테스트 시나리오

### 상세 가이드

- **[IRT_CALIBRATION_GUIDE.md](../../apps/seedtest_api/docs/IRT_CALIBRATION_GUIDE.md)** - IRT Calibration 완전 가이드
- **[R_GLMM_SERVICE_GUIDE.md](../../apps/seedtest_api/docs/R_GLMM_SERVICE_GUIDE.md)** - GLMM R 서비스
- **[ADVANCED_ANALYTICS_ROADMAP.md](../../apps/seedtest_api/docs/ADVANCED_ANALYTICS_ROADMAP.md)** - 6개 모델 로드맵

---

## ✅ 체크리스트

### 배포 완료
- [ ] Secret 생성 (seedtest-db-credentials, r-irt-credentials)
- [ ] CronJob 배포 (calibrate-irt-nightly)
- [ ] CronJob 스케줄 확인 (0 3 * * *)
- [ ] One-off Job 테스트 성공

### 검증 완료
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

### 즉시 실행 (5분)
1. **[QUICK_DEPLOY.md](./QUICK_DEPLOY.md)** 참고하여 빠른 배포
2. One-off Job으로 테스트
3. 데이터베이스 검증

### 프로덕션 준비 (15분)
1. **[DEPLOYMENT_EXECUTION_GUIDE.md](./DEPLOYMENT_EXECUTION_GUIDE.md)** 참고하여 ExternalSecret 설정
2. GCP Secret Manager 연동
3. 모니터링 및 알림 설정

### 추가 모델 구현
1. **[R_GLMM_SERVICE_GUIDE.md](../../apps/seedtest_api/docs/R_GLMM_SERVICE_GUIDE.md)** - GLMM 추세 모델
2. **[ADVANCED_ANALYTICS_ROADMAP.md](../../apps/seedtest_api/docs/ADVANCED_ANALYTICS_ROADMAP.md)** - 전체 로드맵

---

**최종 업데이트**: 2025-11-02 00:14 KST  
**작성자**: Cascade AI

**시작하기**: [QUICK_DEPLOY.md](./QUICK_DEPLOY.md) ⭐
