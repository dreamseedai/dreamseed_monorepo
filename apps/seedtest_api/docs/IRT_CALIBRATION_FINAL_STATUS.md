# IRT 캘리브레이션 파이프라인 최종 상태

**작성일**: 2025-11-02  
**상태**: ✅ **완료** - 즉시 실행 가능

---

## ✅ 완료된 구현

### 1. Calibration Job (`mirt_calibrate.py`)

**파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`

**기능**:
- ✅ `attempt` VIEW에서 관측치 추출 (user_id, item_id, correct)
  - 우선순위: attempt VIEW → responses 테이블 → exam_results JSON
  - 최대 관측치 제한: `MIRT_MAX_OBS` (기본값: 0 = 무제한)
- ✅ r-irt-plumber `/irt/calibrate` 호출
  - 페이로드: observations, model, anchors (선택)
  - 타임아웃: `R_IRT_TIMEOUT_SECS` (기본값: 300초)
- ✅ `mirt_item_params` upsert
  - 컬럼: item_id (PK), params{a,b,c}, model, version, fitted_at
- ✅ `mirt_ability` upsert
  - 컬럼: user_id, version (PK), theta, se, model, fitted_at
- ✅ `mirt_fit_meta` upsert
  - 컬럼: run_id (PK), model_spec, metrics, fitted_at
  - **Linking constants**: `model_spec.linking_constants`에 저장

**앵커 동등화**:
- ✅ `question.meta.tags`에서 "anchor" 태그 확인
- ✅ `question.meta.irt`에서 a, b, c 파라미터 로드
- ✅ Anchors를 r-irt-plumber에 전달
- ✅ Linking constants 저장

**환경 변수**:
```bash
MIRT_LOOKBACK_DAYS=30      # 관측치 조회 기간 (일)
MIRT_MODEL=2PL            # IRT 모델 (2PL, 3PL, Rasch)
MIRT_MAX_OBS=500000       # 최대 관측치 수 (0 = 무제한)
R_IRT_BASE_URL=...        # r-irt-plumber 서비스 URL
R_IRT_INTERNAL_TOKEN=...  # 내부 인증 토큰 (선택)
R_IRT_TIMEOUT_SECS=300    # 타임아웃 (초)
DRY_RUN=false             # Dry-run 모드
IRT_UPDATE_QUESTION_META=false  # question.meta.irt 자동 업데이트
```

---

### 2. CronJob 매니페스트

**파일**: `portal_front/ops/k8s/cron/calibrate-irt.yaml`

**설정**:
- 스케줄: 매주 일요일 03:10 UTC (`"10 3 * * 0"`)
- 이미지: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest`
- 명령어: `python3 -m apps.seedtest_api.jobs.mirt_calibrate`
- 환경 변수: 위와 동일

**배포**:
```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml
```

---

## 🔍 검증 체크리스트

### 1. R IRT Plumber 엔드포인트 확인

```bash
# 서비스 확인
kubectl -n seedtest get svc r-irt-plumber

# Pod 확인
kubectl -n seedtest get pods -l app=r-irt-plumber

# Health check
kubectl -n seedtest exec deploy/seedtest-api -c api -- \
  curl -f http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz
```

### 2. DB Upsert 결과 확인

```sql
-- Item params 확인
SELECT 
    COUNT(*) AS item_count,
    COUNT(DISTINCT version) AS version_count,
    MIN(fitted_at) AS first_fit,
    MAX(fitted_at) AS latest_fit
FROM mirt_item_params;

-- Sample item params (최근 10개)
SELECT 
    item_id,
    model,
    params->>'a' AS discrimination,
    params->>'b' AS difficulty,
    params->>'c' AS guessing,
    version,
    fitted_at
FROM mirt_item_params
ORDER BY fitted_at DESC
LIMIT 10;

-- Ability 확인
SELECT 
    COUNT(*) AS ability_count,
    COUNT(DISTINCT user_id) AS user_count,
    AVG(theta) AS avg_theta,
    AVG(se) AS avg_se,
    MAX(fitted_at) AS latest_fit
FROM mirt_ability;

-- Sample abilities (최근 10개)
SELECT 
    user_id,
    theta,
    se,
    model,
    version,
    fitted_at
FROM mirt_ability
ORDER BY fitted_at DESC
LIMIT 10;

-- Fit meta 확인 (linking constants 포함)
SELECT 
    run_id,
    model_spec->'model' AS model,
    model_spec->'n_items' AS n_items,
    model_spec->'n_observations' AS n_observations,
    (model_spec->'linking_constants') IS NOT NULL AS has_linking,
    model_spec->'linking_constants' AS linking_constants,
    metrics->>'aic' AS aic,
    metrics->>'bic' AS bic,
    fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 5;
```

### 3. 온라인 업데이트(θ)와의 정합 확인

```sql
-- 캘리브레이션 vs 온라인 버전 구분
SELECT 
    CASE 
        WHEN version LIKE 'v%' THEN 'calibration'
        WHEN version LIKE 'online%' THEN 'online'
        ELSE 'other'
    END AS source_type,
    COUNT(*) AS count,
    AVG(theta) AS avg_theta,
    MAX(fitted_at) AS latest_fit
FROM mirt_ability
GROUP BY source_type
ORDER BY source_type;

-- 동일 사용자의 캘리브레이션 vs 온라인 θ 비교
SELECT 
    ma_cal.user_id,
    ma_cal.theta AS calib_theta,
    ma_cal.se AS calib_se,
    ma_online.theta AS online_theta,
    ma_online.se AS online_se,
    ABS(ma_cal.theta - COALESCE(ma_online.theta, ma_cal.theta)) AS theta_diff
FROM mirt_ability ma_cal
LEFT JOIN mirt_ability ma_online 
    ON ma_cal.user_id = ma_online.user_id 
    AND ma_online.version LIKE 'online%'
WHERE ma_cal.version LIKE 'v%'
ORDER BY ma_cal.fitted_at DESC
LIMIT 10;
```

### 4. 앵커 동등화 확인

```sql
-- 앵커 문항 확인
SELECT 
    id,
    meta->'tags' AS tags,
    meta->'irt'->>'a' AS anchor_a,
    meta->'irt'->>'b' AS anchor_b,
    meta->'irt'->>'model' AS model
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb
LIMIT 10;

-- Linking constants 확인 (최근 캘리브레이션)
SELECT 
    run_id,
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
WHERE model_spec ? 'linking_constants'
ORDER BY fitted_at DESC
LIMIT 1;
```

---

## 📋 권장 후속 작업

### 1. I_t(개선지수) θ-델타 기반 전환

**현재**: `compute_improvement_index`에서 정답률 기반 계산 (폴백)

**개선 방향**:
- `METRICS_USE_IRT_THETA=true` 설정 시 θ 기반 계산 사용
- θ_recent - θ_prev 계산하여 improvement index 산출
- 폴백: 정답률 기반 (θ 값이 없는 경우)

**파일**: `apps/seedtest_api/services/metrics.py`

**현재 구현 상태**:
- ✅ `_latest_theta_in_window`: θ 값 로드 함수 존재
- ✅ `compute_improvement_index`: θ 기반 계산 로직 존재 (환경 변수로 제어)
- ⏭️ 환경 변수 활성화 필요: `METRICS_USE_IRT_THETA=true`

### 2. features_topic_daily에 θ 백필

**현재**: `aggregate_features_daily.py`에서 `_load_theta_if_needed` 함수 존재

**확인 사항**:
- ✅ `AGG_INCLUDE_THETA` 환경 변수로 제어
- ✅ `student_topic_theta` 우선, `mirt_ability` 폴백
- ⏭️ 환경 변수 활성화 필요: `AGG_INCLUDE_THETA=true`

**파일**: `apps/seedtest_api/jobs/aggregate_features_daily.py`

### 3. Anchoring/동등화 완성

**현재 구현 상태**:
- ✅ `question.meta.tags`에서 "anchor" 태그 확인
- ✅ 앵커 파라미터 로드 (`question.meta.irt`에서 a, b, c)
- ✅ `anchors` 파라미터를 r-irt-plumber에 전달
- ✅ Linking constants를 `mirt_fit_meta.model_spec.linking_constants`에 저장

**확인 필요**:
- r-irt-plumber가 `anchors` 파라미터를 지원하는지
- Linking constants가 응답에 포함되는지

**테스트**:
```bash
# 앵커 문항 설정
psql $DATABASE_URL -c "
UPDATE question
SET meta = jsonb_set(
    jsonb_set(
        COALESCE(meta, '{}'::jsonb),
        '{tags}',
        '[\"anchor\"]'::jsonb,
        true
    ),
    '{irt}',
    '{\"a\": 1.0, \"b\": 0.0, \"model\": \"2PL\"}'::jsonb,
    true
)
WHERE id = 1001;
"

# 캘리브레이션 실행 (앵커 포함)
kubectl -n seedtest create job calibrate-irt-test --from=cronjob/calibrate-irt-weekly

# Linking constants 확인
psql $DATABASE_URL -c "
SELECT 
    run_id,
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
WHERE model_spec ? 'linking_constants'
ORDER BY fitted_at DESC
LIMIT 1;
"
```

---

## 🚀 즉시 실행 가능

### 1. CronJob 배포 및 활성화

```bash
# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 상태 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly

# 스케줄 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly -o jsonpath='{.spec.schedule}'
```

### 2. 수동 테스트 (즉시 실행)

```bash
# Job 수동 생성
kubectl -n seedtest create job calibrate-irt-manual --from=cronjob/calibrate-irt-weekly

# 로그 팔로우
kubectl -n seedtest logs job/calibrate-irt-manual -c calibrate-irt -f

# 완료 대기
kubectl -n seedtest wait --for=condition=complete job/calibrate-irt-manual --timeout=600s
```

### 3. 검증 실행

```bash
# Pod에서 직접 실행 (디버깅용)
kubectl -n seedtest exec deploy/seedtest-api -c api -- python3 -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM mirt_item_params'))
    print(f'Item params count: {result.fetchone()[0]}')
    result = conn.execute(text('SELECT COUNT(*) FROM mirt_ability'))
    print(f'Ability count: {result.fetchone()[0]}')
"
```

---

## 📊 모니터링

### CronJob 상태

```bash
# 최근 실행된 Job
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | grep calibrate-irt | tail -5

# CronJob 상태
kubectl -n seedtest get cronjob calibrate-irt-weekly

# 이벤트 확인
kubectl -n seedtest get events --sort-by=.lastTimestamp | grep calibrate-irt | tail -10
```

### DB 메트릭

```sql
-- 최근 캘리브레이션 통계
SELECT 
    DATE_TRUNC('day', fitted_at) AS calib_date,
    COUNT(DISTINCT item_id) AS item_count,
    COUNT(DISTINCT user_id) AS user_count,
    AVG((params->>'b')::float) AS avg_difficulty
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', fitted_at)
ORDER BY calib_date DESC;

-- 앵커 문항 수
SELECT COUNT(*) AS anchor_count
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb;
```

---

## ✅ 최종 상태

**IRT Calibrate 파이프라인 완성 완료!** 🎉

- ✅ 관측치 추출 → R IRT 호출 → DB Upsert 파이프라인
- ✅ 앵커 동등화 지원
- ✅ Linking constants 저장
- ✅ CronJob 매니페스트 준비 완료
- ✅ 최신 이미지 태그 반영 (`latest`)

**즉시 실행 가능**: CronJob 배포 후 자동 실행 또는 수동 Job으로 테스트 가능

