# IRT 캘리브레이션 검증 가이드

**작성일**: 2025-11-02  
**상태**: ✅ IRT calibrate 파이프라인 완성

---

## ✅ 완료된 기능

### 1. 관측치 추출 → R IRT 호출 → DB Upsert 파이프라인

**파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`

**기능**:
- ✅ `attempt` VIEW에서 최근 관측치 추출 (user_id, item_id, correct)
- ✅ r-irt-plumber `/irt/calibrate` 호출 (JSON)
- ✅ `mirt_item_params` upsert (item_id, params{a,b,c}, model, version, fitted_at)
- ✅ `mirt_ability` upsert (user_id, theta, se, model, version, fitted_at)
- ✅ `mirt_fit_meta` upsert (run_id, model_spec, metrics, fitted_at, linking_constants)

**환경 변수**:
- `R_IRT_BASE_URL`: r-irt-plumber 서비스 URL
- `R_IRT_INTERNAL_TOKEN`: 내부 인증 토큰 (선택)
- `R_IRT_TIMEOUT_SECS`: 타임아웃 (기본값: 300초)
- `MIRT_LOOKBACK_DAYS`: 관측치 조회 기간 (기본값: 30일)
- `MIRT_MODEL`: IRT 모델 타입 (기본값: 2PL)
- `MIRT_MAX_OBS`: 최대 관측치 수 (기본값: 0 = 무제한)
- `DRY_RUN`: Dry-run 모드 (기본값: false)
- `IRT_UPDATE_QUESTION_META`: question.meta.irt 자동 업데이트 (기본값: false)

---

## 🔍 R IRT Plumber 페이로드/응답 스키마

### 요청 페이로드 (`POST /irt/calibrate`)

```json
{
  "observations": [
    {
      "user_id": "uuid-string",
      "item_id": "item-id-string",
      "is_correct": true,
      "responded_at": "2025-10-31T12:00:00Z"
    }
  ],
  "model": "2PL",  // "2PL", "3PL", "Rasch"
  "anchors": [  // 선택적: 앵커 문항
    {
      "item_id": "anchor-item-id",
      "params": {
        "a": 1.0,
        "b": 0.0,
        "c": 0.2  // 3PL만
      },
      "fixed": true
    }
  ]
}
```

### 응답 스키마

```json
{
  "item_params": [
    {
      "item_id": "item-id-string",
      "params": {
        "a": 1.2,  // discrimination
        "b": -0.6, // difficulty
        "c": 0.2   // guessing (3PL만)
      },
      "model": "2PL",
      "version": "v1"
    }
  ],
  "abilities": [
    {
      "user_id": "uuid-string",
      "theta": 0.85,  // ability estimate
      "se": 0.15,     // standard error
      "model": "2PL",
      "version": "v1"
    }
  ],
  "fit_meta": {
    "run_id": "fit-2025-11-02T03:00:00Z",
    "model_spec": {
      "model": "2PL",
      "n_items": 150,
      "n_observations": 50000,
      "linking_constants": {  // 앵커 동등화 시 포함
        "A": 1.0,
        "B": 0.0
      }
    },
    "metrics": {
      "aic": 12345.67,
      "bic": 12456.78,
      "loglik": -6123.45
    }
  }
}
```

---

## ✅ 검증 체크리스트

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

-- Sample item params
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

-- Sample abilities
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
-- 온라인 업데이트 vs 캘리브레이션 구분
SELECT 
    'calibration' AS source,
    COUNT(*) AS count,
    AVG(theta) AS avg_theta,
    MAX(fitted_at) AS latest_fit
FROM mirt_ability
WHERE version LIKE 'v%'  -- 캘리브레이션 버전

UNION ALL

SELECT 
    'online' AS source,
    COUNT(*) AS count,
    AVG(theta) AS avg_theta,
    MAX(fitted_at) AS latest_fit
FROM mirt_ability
WHERE version LIKE 'online%'  -- 온라인 업데이트 버전

ORDER BY source;

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
    meta->'irt'->>'b' AS anchor_b
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb;

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

---

## 🔧 CronJob 설정

### 주간 실행 (권장)

**파일**: `portal_front/ops/k8s/cron/calibrate-irt.yaml`

```yaml
schedule: "10 3 * * 0"  # 매주 일요일 03:10 UTC
```

### 일일 실행

```yaml
schedule: "0 3 * * *"  # 매일 03:00 UTC
```

---

## 📋 권장 후속 작업

### 1. I_t(개선지수) θ-델타 기반 전환

**파일**: `apps/seedtest_api/services/metrics.py`

**현재**: 정답률 기반 improvement index

**개선**:
- `compute_improvement_index`에서 θ_prev/θ_recent 사용
- `mirt_ability` 또는 `student_topic_theta`에서 θ 값 로드
- 폴백: 정답률 기반 (θ 값이 없는 경우)

### 2. features_topic_daily에 θ 백필

**파일**: `apps/seedtest_api/jobs/aggregate_features_daily.py`

**현재**: `theta_mean`, `theta_sd` 컬럼 존재하나 비어있음

**개선**:
- 최근 캘리브레이션 또는 온라인 업데이트 값 사용
- `student_topic_theta` 우선, 없으면 `mirt_ability` 사용

### 3. Anchoring/동등화 완성

**현재**: `question.meta.tags`에 "anchor" 태그 확인 및 전달 구현됨

**확인 필요**:
- r-irt-plumber가 `anchors` 파라미터를 지원하는지
- Linking constants 반환 여부

---

## 🚀 즉시 실행 가능

현재 상태에서 다음 작업들이 즉시 실행 가능합니다:

1. ✅ **CronJob 활성화**: `calibrate-irt.yaml` 배포
2. ✅ **수동 테스트**: Job으로 즉시 실행
3. ⏭️ **검증**: DB 쿼리로 결과 확인
4. ⏭️ **후속 작업**: I_t 전환, θ 백필, 앵커 완성

**CronJob 매니페스트 생성 준비 완료!** 🎉

