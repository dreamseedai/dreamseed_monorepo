# Secret 참조 가이드 - calibrate-irt CronJob

**최종 업데이트**: 2025-11-02 01:29 KST

---

## 🔐 calibrate-irt CronJob Secret 정보

### 현재 사용 중인 Secret (수동 관리)

| 환경 변수 | Secret 이름 | Secret 키 | 설명 |
|----------|------------|----------|------|
| `DATABASE_URL` | `seedtest-db-credentials` | `DATABASE_URL` | PostgreSQL 연결 문자열 |
| `R_IRT_INTERNAL_TOKEN` | `r-irt-credentials` | `token` | R IRT Plumber 인증 토큰 (optional) |

### ExternalSecret 사용 시 (ESO 자동 관리)

| 환경 변수 | Secret 이름 | Secret 키 | GCP Secret Manager 경로 |
|----------|------------|----------|----------------------|
| `DATABASE_URL` | `calibrate-irt-credentials` | `DATABASE_URL` | `seedtest/database-url` |
| `R_IRT_INTERNAL_TOKEN` | `calibrate-irt-credentials` | `R_IRT_INTERNAL_TOKEN` | `r-irt-plumber/token` |

---

## 📋 빠른 참조

### 수동 Secret 생성

```bash
# DATABASE_URL
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://user:password@localhost:5432/seedtest'

# R_IRT_INTERNAL_TOKEN
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='your-token-here'
```

### ExternalSecret 사용

```bash
# 1. GCP Secret Manager에 Secret 생성
echo -n "postgresql://user:password@localhost:5432/seedtest" | \
  gcloud secrets create seedtest-database-url --data-file=- --project=univprepai

echo -n "your-token-here" | \
  gcloud secrets create r-irt-plumber-token --data-file=- --project=univprepai

# 2. ExternalSecret 배포
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# 3. CronJob 패치
kubectl -n seedtest patch cronjob calibrate-irt-weekly \
  --type strategic \
  --patch-file portal_front/ops/k8s/patches/calibrate-irt-externalsecret-patch.yaml
```

---

## 📚 관련 파일

- **ExternalSecret 매니페스트**: `portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml`
- **CronJob 패치**: `portal_front/ops/k8s/patches/calibrate-irt-externalsecret-patch.yaml`
- **마이그레이션 가이드**: `portal_front/ops/k8s/EXTERNALSECRET_MIGRATION_GUIDE.md`
- **기본 Secret 가이드**: `portal_front/ops/k8s/SECRET_SETUP_GUIDE.md`

---

## 🎯 권장 사항

**프로덕션 환경**: ExternalSecret 사용 (ESO + GCP Secret Manager)  
**개발/테스트 환경**: 수동 Secret 생성

---

**최종 업데이트**: 2025-11-02 01:29 KST
