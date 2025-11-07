# IRT 파이프라인 최종 구현 완료 문서

**작성일**: 2025-11-02  
**상태**: ✅ **모든 구현 완료**

---

## ✅ 완료된 모든 작업

### 1. Python 측 구현

#### IRT 캘리브레이션 파이프라인
- ✅ **파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`
- ✅ 관측치 추출: attempt VIEW → responses → exam_results (우선순위)
- ✅ Anchors 로드: `question.meta.tags`에서 "anchor" 태그 확인
- ✅ R IRT 서비스 호출: `/irt/calibrate` 엔드포인트
- ✅ DB Upsert: `mirt_item_params`, `mirt_ability`, `mirt_fit_meta`
- ✅ Linking constants 저장: `mirt_fit_meta.model_spec.linking_constants`
- ✅ 백오프/재시도: 3회 재시도, 지수 백오프 (5초, 10초, 15초)

#### I_t θ-델타 기반 전환
- ✅ **파일**: `apps/seedtest_api/services/metrics.py`
- ✅ θ 기반 계산: `METRICS_USE_IRT_THETA=true` 설정 시
- ✅ 폴백: 정답률 기반 (θ 값이 없을 때)
- ✅ `weekly_kpi`에 I_t 저장

#### features_topic_daily에 θ 채우기
- ✅ **파일**: `apps/seedtest_api/services/features_backfill.py`
- ✅ `student_topic_theta` 우선, `mirt_ability` 폴백
- ✅ `theta_mean`, `theta_sd` 컬럼 채움
- ✅ `AGG_INCLUDE_THETA=true` 환경 변수로 제어

#### Anchors 아이템 태깅
- ✅ **파일**: `apps/seedtest_api/jobs/tag_anchor_items.py`
- ✅ 후보 자동 탐색 (IRT 파라미터, 안정성 기준)
- ✅ Dry-run 모드 지원
- ✅ 검증 기능

---

### 2. R 서비스 측 구현

#### r-irt-plumber /irt/calibrate
- ✅ **파일**: `r-irt-plumber/api.R`
- ✅ Observations → wide matrix 변환
- ✅ 2PL/3PL/Rasch 모델 선택
- ✅ mirt 적합 후 item params (a, b, c) 및 abilities (EAP, SE) 계산
- ✅ **Anchors 처리**: 선형 링크 (A, B) 계산
- ✅ **Linking constants 반환**: `{A, B, n_anchors_used}` 응답에 포함
- ✅ `fit_meta`에 `linking_constants` 포함

#### r-irt-plumber /irt/score
- ✅ 고정 item params에 대해 EAP 스코어링
- ✅ theta/SE 반환

#### 헬스체크
- ✅ `/healthz` 엔드포인트 포함

---

### 3. Kubernetes 매니페스트

#### CronJob
- ✅ **파일**: `portal_front/ops/k8s/cron/calibrate-irt.yaml`
- ✅ 스케줄: 매일 03:00 UTC
- ✅ 이미지: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest`
- ✅ 명령: `python3 -m apps.seedtest_api.jobs.mirt_calibrate`
- ✅ 환경 변수: MIRT_*, R_IRT_*, DATABASE_URL 등

#### ExternalSecret 연동
- ✅ **파일**: `portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml`
- ✅ DATABASE_URL: GSM에서 자동 주입
- ✅ R_IRT_INTERNAL_TOKEN: GSM에서 자동 주입 (선택)
- ✅ ClusterSecretStore 예시 포함
- ✅ 설정 가이드 포함

#### CronJob (ExternalSecret 버전)
- ✅ **파일**: `portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml`
- ✅ ExternalSecret-managed Secret 참조
- ✅ 모든 환경 변수 설정 포함

---

### 4. 리포트 생성

#### Quarto 리포트 템플릿
- ✅ **파일**: `reports/quarto/weekly_report.qmd`
- ✅ Ability(θ) 추세 플롯
- ✅ **Linking Constants 섹션**: `linking_constants.A`, `B`, `n_anchors_used` 표시
- ✅ KPI 표/레이다 차트
- ✅ Topic/일별 성과 차트
- ✅ 추천 문구 섹션

#### 리포트 생성 파이프라인
- ✅ **파일**: `apps/seedtest_api/jobs/generate_weekly_report.py`
- ✅ KPI 로드 → Quarto render → S3 업로드 → `report_artifacts` upsert
- ✅ CronJob: 월요일 04:00 UTC

---

## 📋 배포 가이드

### Step 1: ExternalSecret 설정 (선택)

```bash
# ESO 설치 확인
kubectl get crd | grep externalsecrets

# GCP Service Account Key Secret 생성
kubectl -n seedtest create secret generic eso-gcp-credentials \
  --from-literal=secret-access-key="$(cat eso-gcp-key.json | jq -r .private_key)"

# ClusterSecretStore 생성
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# ExternalSecret 생성
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# Secret 생성 확인
kubectl -n seedtest get secret calibrate-irt-credentials
```

### Step 2: CronJob 배포

**옵션 A: ExternalSecret 사용**
```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml
```

**옵션 B: 직접 Secret 사용**
```bash
# Secret 직접 생성
kubectl -n seedtest create secret generic seedtest-db-credentials \
  --from-literal=DATABASE_URL='postgresql://...'
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='<token>'

# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml
```

### Step 3: r-irt-plumber 배포

```bash
# Deployment 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/r-irt-plumber/deployment.yaml

# 서비스 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 헬스체크
kubectl -n seedtest exec deploy/seedtest-api -c api -- \
  curl -f http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz
```

### Step 4: 테스트 실행

```bash
# 수동 Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  calibrate-irt-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs job/calibrate-irt-test-* -c calibrate-irt -f
```

---

## ✅ 검증 체크리스트

### 1. IRT 캘리브레이션 결과

```sql
-- 최근 캘리브레이션 확인
SELECT 
    COUNT(*) AS item_count,
    COUNT(DISTINCT item_id) AS unique_items,
    MAX(fitted_at) AS latest_fit
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 day';

-- Ability 확인
SELECT 
    COUNT(*) AS ability_count,
    COUNT(DISTINCT user_id) AS unique_users,
    AVG(theta) AS avg_theta,
    MAX(fitted_at) AS latest_fit
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 day';

-- Linking constants 확인
SELECT 
    run_id,
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
WHERE model_spec ? 'linking_constants'
ORDER BY fitted_at DESC
LIMIT 1;
```

### 2. Anchors 사용 확인

```sql
-- Anchor 아이템 수
SELECT COUNT(*) 
FROM question 
WHERE meta->'tags' @> '["anchor"]'::jsonb;

-- Anchor 아이템의 캘리브레이션 결과
SELECT 
    q.id,
    q.meta->'irt'->>'b' AS anchor_b,
    mip.params->>'b' AS calibrated_b,
    mip.fitted_at
FROM question q
JOIN mirt_item_params mip ON q.id::text = mip.item_id
WHERE q.meta->'tags' @> '["anchor"]'::jsonb
ORDER BY mip.fitted_at DESC
LIMIT 10;
```

### 3. I_t θ 전환 확인

```sql
-- I_t 값 확인 (θ 기반 또는 정답률 기반)
SELECT 
    user_id,
    week_start,
    kpis->>'I_t' AS i_t,
    updated_at
FROM weekly_kpi
WHERE kpis ? 'I_t'
ORDER BY updated_at DESC
LIMIT 10;
```

### 4. features_topic_daily θ 채움 확인

```sql
-- theta_mean/theta_sd 채움 확인
SELECT 
    student_id,
    topic_id,
    date,
    theta_mean,
    theta_sd,
    attempts,
    updated_at
FROM features_topic_daily
WHERE theta_mean IS NOT NULL
ORDER BY updated_at DESC
LIMIT 10;
```

### 5. 리포트 생성 확인

```sql
-- 최근 리포트 확인
SELECT 
    user_id,
    week_start,
    format,
    report_url,
    generated_at
FROM report_artifacts
WHERE generated_at >= NOW() - INTERVAL '7 days'
ORDER BY generated_at DESC
LIMIT 10;
```

---

## 📊 운영 모니터링

### CronJob 상태

```bash
# CronJob 상태
kubectl -n seedtest get cronjob calibrate-irt-weekly

# 최근 실행된 Job
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | grep calibrate-irt | tail -5

# 이벤트 확인
kubectl -n seedtest get events --sort-by=.lastTimestamp | grep calibrate-irt | tail -10
```

### 서비스 헬스체크

```bash
# r-irt-plumber 헬스체크
kubectl -n seedtest exec deploy/seedtest-api -c api -- \
  curl -f http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz

# Pod 상태
kubectl -n seedtest get pods -l app=r-irt-plumber
```

---

## 🎉 최종 상태

### ✅ 완료된 모든 구현

1. **Python 측**: 모든 파이프라인 구현 완료
2. **R 서비스 측**: anchors 처리 및 linking constants 반환 구현 완료
3. **Kubernetes**: CronJob, ExternalSecret 연동 완료
4. **리포트**: Linking Constants 섹션 포함 완료
5. **문서화**: 모든 가이드 및 체크리스트 작성 완료

### 📋 배포 준비 상태

- ✅ 코드 구현 완료
- ✅ Kubernetes 매니페스트 준비 완료
- ✅ ExternalSecret 연동 준비 완료
- ✅ 테스트 체크리스트 준비 완료
- ✅ 운영 문서 준비 완료

**모든 구현 완료! 즉시 배포 및 운영 가능** 🚀

---

## 다음 단계 (선택)

### 성능 최적화

- r-irt-plumber NCYCLES/옵션 튜닝
- Anchors 처리 고도화 (동등화 방식 개선)
- 예외/경고 로그 강화

### 테스트 추가

- I_t θ/정답률 폴백 유닛테스트
- features_backfill θ 채움 유닛테스트
- calibrate anchors 응답 파싱/업서트 통합 테스트

### 모니터링 강화

- 캘리브레이션 메트릭 대시보드
- 알림 설정 (실패, 이상치 감지)
- 성능 모니터링 (실행 시간, 메모리 사용량)
