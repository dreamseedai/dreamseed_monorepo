# IRT Analytics Pipeline - 완전 가이드

**최종 업데이트**: 2025-11-01 23:56 KST  
**상태**: ✅ Production Ready

---

## 📚 문서 구조

이 디렉토리는 IRT Analytics Pipeline의 완전한 구현 및 배포 가이드를 제공합니다.

### 🎯 빠른 시작

1. **[FINAL_IMPLEMENTATION_STATUS.md](./FINAL_IMPLEMENTATION_STATUS.md)** ⭐
   - 전체 구현 상태 요약
   - 완료된 기능 목록
   - 즉시 배포 가능 여부 확인

2. **[DEPLOYMENT_COMMANDS.md](../../portal_front/ops/k8s/DEPLOYMENT_COMMANDS.md)** ⭐
   - 배포 명령어 모음
   - 단계별 배포 가이드
   - 문제 해결 가이드

3. **[INTEGRATION_TEST_GUIDE.md](./INTEGRATION_TEST_GUIDE.md)** ⭐
   - 통합 테스트 시나리오
   - 검증 SQL 쿼리
   - 성능 벤치마크

---

## 📖 상세 가이드

### 구현 가이드

#### [IRT_CALIBRATION_GUIDE.md](./IRT_CALIBRATION_GUIDE.md)
- IRT Calibration 완전 가이드
- 환경 변수 설정
- R IRT API 스펙
- 검증 체크리스트
- 온라인 θ 업데이트 일관성
- 앵커 동등화 (Equating)
- 문제 해결

#### [R_GLMM_SERVICE_GUIDE.md](./R_GLMM_SERVICE_GUIDE.md)
- GLMM R Plumber 서비스 구현
- API 엔드포인트 정의
- Kubernetes 배포
- 테스트 방법

#### [ADVANCED_ANALYTICS_ROADMAP.md](./ADVANCED_ANALYTICS_ROADMAP.md)
- 6개 고급 분석 모델 로드맵
- 각 모델별 구현 상태
- R 서비스 요구사항
- 데이터베이스 스키마
- CronJob 스케줄

---

### 배포 가이드

#### [DEPLOYMENT_GUIDE_IRT_PIPELINE.md](./DEPLOYMENT_GUIDE_IRT_PIPELINE.md)
- 7단계 배포 프로세스
- Phase별 배포 전략
- 검증 방법
- 일일/주간 운영 체크리스트
- 모니터링 및 알림 설정

#### [../../portal_front/ops/k8s/DEPLOYMENT_COMMANDS.md](../../portal_front/ops/k8s/DEPLOYMENT_COMMANDS.md)
- 즉시 실행 가능한 명령어
- Kubernetes 리소스 배포
- Health check
- 로그 확인
- 롤백 방법

---

### 테스트 가이드

#### [INTEGRATION_TEST_GUIDE.md](./INTEGRATION_TEST_GUIDE.md)
- 6가지 테스트 시나리오
  1. I_t θ-델타 계산 (θ 있음)
  2. I_t 정답률 폴백 (θ 없음)
  3. features_topic_daily θ 백필
  4. mirt_calibrate anchors 페이로드
  5. 재시도 로직 (백오프)
  6. Calibrate CronJob 배포
- 검증 SQL 쿼리
- 문제 해결
- 성능 벤치마크

---

## 🚀 빠른 배포

### 자동 배포 (권장)

```bash
cd /home/won/projects/dreamseed_monorepo

# Dry-run으로 미리보기
./portal_front/ops/k8s/deploy-irt-pipeline.sh --dry-run

# 실제 배포
./portal_front/ops/k8s/deploy-irt-pipeline.sh
```

### 수동 배포

```bash
# 1) ExternalSecret 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/r-irt-plumber/externalsecret.yaml

# 2) IRT Calibration CronJob
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 3) GLMM 매니페스트
kubectl -n seedtest apply -f portal_front/ops/k8s/jobs/glmm-fit-progress-scripts.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/jobs/glmm-fit-progress-now.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/glmm-fit-progress.yaml

# 4) Health check
kubectl -n seedtest run curl-irt --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz

# 5) 테스트 실행
kubectl -n seedtest create -f portal_front/ops/k8s/jobs/calibrate-irt-now.yaml
kubectl -n seedtest logs -f job/calibrate-irt-now
```

---

## 📊 구현 현황

### ✅ 완료된 기능 (Production Ready)

#### 1. IRT Calibration Pipeline
- **Jobs**: `mirt_calibrate.py`
- **기능**:
  - 관측 추출 (attempt VIEW)
  - R IRT 서비스 호출
  - 앵커 문항 지원
  - 재시도 로직 (3회, 지수 백오프)
  - DB 업데이트 (item_params, ability, fit_meta)
- **CronJob**: 매일 03:00 UTC

#### 2. Anchor Item Tagging
- **Jobs**: `tag_anchor_items.py`
- **기능**:
  - 안정적인 문항 자동 선정
  - CLI 인터페이스
  - 안정성 검증 (difficulty variance)
  - Dry-run 모드

#### 3. I_t θ-델타 전환
- **Services**: `metrics.py`
- **기능**:
  - θ 기반 계산 (우선)
  - 정답률 기반 폴백
  - 노출 보정 × se 패널티

#### 4. features_topic_daily θ 백필
- **Services**: `features_backfill.py`
- **기능**:
  - student_topic_theta 우선
  - mirt_ability 폴백
  - AGG_INCLUDE_THETA 환경 변수

#### 5. Quarto Report θ Section
- **Templates**: `weekly_report.qmd`
- **기능**:
  - θ 트렌드 차트
  - 능력 통계 (백분위, 수준)
  - 문항 난이도 분포
  - 개인화된 인사이트

---

### 🔄 스캐폴딩 완료 (R 서비스 구현 대기)

#### 6. GLMM Growth Model
- **Jobs**: `fit_growth_glmm.py`
- **CronJob**: 매주 월요일 03:30 UTC
- **가이드**: `R_GLMM_SERVICE_GUIDE.md`

#### 7. Bayesian Growth Model
- **Jobs**: `fit_bayesian_growth.py`
- **R 서비스**: brms

#### 8. Prophet Time Series
- **Jobs**: `forecast_prophet.py`
- **R 서비스**: prophet

#### 9. Survival Analysis
- **Jobs**: `fit_survival_churn.py`
- **R 서비스**: survival

#### 10. User Clustering
- **Jobs**: `cluster_segments.py`
- **R 서비스**: tidymodels

---

## 🔍 검증 방법

### 데이터베이스 검증

```sql
-- 1. IRT Calibration 결과
SELECT 
    COUNT(*) AS item_count,
    AVG((params->>'a')::float) AS avg_discrimination,
    AVG((params->>'b')::float) AS avg_difficulty,
    MAX(fitted_at) AS last_fitted
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 day';

-- 2. 사용자 능력
SELECT 
    COUNT(*) AS user_count,
    AVG(theta) AS avg_theta,
    STDDEV(theta) AS sd_theta
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 day';

-- 3. Linking constants
SELECT 
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- 4. 앵커 문항
SELECT COUNT(*) AS anchor_count
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb;

-- 5. θ in features
SELECT COUNT(*) AS count_with_theta
FROM features_topic_daily
WHERE theta_estimate IS NOT NULL
  AND date >= NOW() - INTERVAL '7 days';

-- 6. I_t in KPIs
SELECT 
    COUNT(*) AS count_with_i_t,
    AVG((kpis->>'I_t')::float) AS avg_i_t
FROM weekly_kpi
WHERE kpis ? 'I_t'
  AND week_start >= NOW() - INTERVAL '4 weeks';
```

---

## 🐛 문제 해결

### 일반적인 문제

| 문제 | 원인 | 해결 방법 |
|------|------|----------|
| I_t가 NULL | θ 데이터 없음 | mirt_calibrate 실행 |
| theta_estimate NULL | AGG_INCLUDE_THETA=false | 환경 변수 true로 설정 |
| anchors 비어있음 | 앵커 태그 없음 | tag_anchor_items 실행 |
| R IRT 연결 실패 | 서비스 미배포 | R IRT Plumber 배포 확인 |
| CronJob 실행 안됨 | 스케줄 문제 | kubectl describe cronjob 확인 |

자세한 내용은 각 가이드의 "문제 해결" 섹션 참고

---

## 📈 성능 최적화

### 권장 설정

```yaml
# mirt-calibrate.yaml
env:
  - name: MIRT_LOOKBACK_DAYS
    value: "30"  # 30일 이하 권장
  - name: MIRT_MAX_OBS
    value: "500000"  # 50만 관측 이하 권장
  - name: MIRT_MAX_RETRIES
    value: "3"
  - name: MIRT_RETRY_DELAY_SECS
    value: "5.0"

# aggregate-features-daily.yaml
env:
  - name: AGG_LOOKBACK_DAYS
    value: "7"  # 7일 권장
  - name: AGG_INCLUDE_THETA
    value: "true"
```

### 예상 실행 시간

| Job | 데이터 규모 | 예상 시간 |
|-----|------------|----------|
| mirt_calibrate | 10K obs, 100 items | 2-5분 |
| aggregate_features_daily | 1K users, 7 days | 1-3분 |
| compute_daily_kpis | 1K users | 30초-1분 |
| tag_anchor_items | 1K items | 10-30초 |

---

## 🔐 보안 고려사항

### Secrets 관리

```yaml
# ExternalSecret 사용 (권장)
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: r-irt-credentials
  namespace: seedtest
spec:
  secretStoreRef:
    name: gcpsm-secret-store
  data:
    - secretKey: token
      remoteRef:
        key: r-irt-internal-token
```

### 환경 변수

- `R_IRT_INTERNAL_TOKEN`: ExternalSecret으로 주입
- `DATABASE_URL`: Kubernetes Secret으로 관리
- 민감 정보는 절대 코드에 하드코딩하지 않음

---

## 📞 지원 및 문의

### 문서 업데이트

이 문서들은 지속적으로 업데이트됩니다. 최신 버전은 다음 위치에서 확인:

```
apps/seedtest_api/docs/
├── README_IRT_PIPELINE.md           # 이 문서
├── FINAL_IMPLEMENTATION_STATUS.md   # 구현 상태
├── IRT_CALIBRATION_GUIDE.md         # IRT 가이드
├── R_GLMM_SERVICE_GUIDE.md          # GLMM 가이드
├── ADVANCED_ANALYTICS_ROADMAP.md    # 전체 로드맵
├── DEPLOYMENT_GUIDE_IRT_PIPELINE.md # 배포 가이드
└── INTEGRATION_TEST_GUIDE.md        # 테스트 가이드
```

### 추가 리소스

- **배포 스크립트**: `portal_front/ops/k8s/deploy-irt-pipeline.sh`
- **배포 명령어**: `portal_front/ops/k8s/DEPLOYMENT_COMMANDS.md`
- **Kubernetes Manifests**: `portal_front/ops/k8s/cron/`, `portal_front/ops/k8s/jobs/`

---

## ✅ 체크리스트

### 배포 전
- [ ] R IRT Plumber 서비스 배포 확인
- [ ] GCP Secret Manager 토큰 생성
- [ ] SecretStore 설정 확인
- [ ] 앵커 문항 태깅 (50개)

### 배포 후
- [ ] ExternalSecret → Secret 생성 확인
- [ ] CronJob 배포 확인
- [ ] One-off Job 테스트 성공
- [ ] 데이터베이스 검증 (6개 쿼리)

### 운영
- [ ] 일일 체크 (매일 09:00 KST)
- [ ] 주간 체크 (매주 월요일 10:00 KST)
- [ ] 모니터링 및 알림 설정
- [ ] 로그 보관 정책 수립

---

**최종 업데이트**: 2025-11-01 23:56 KST  
**작성자**: Cascade AI  
**상태**: ✅ Production Ready - 즉시 배포 가능

**다음 단계**: `./portal_front/ops/k8s/deploy-irt-pipeline.sh` 실행
