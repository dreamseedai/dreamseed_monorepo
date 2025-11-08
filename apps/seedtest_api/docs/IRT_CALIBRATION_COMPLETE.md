# IRT 캘리브레이션 파이프라인 완성 가이드

**작성일**: 2025-11-01  
**상태**: ✅ IRT calibrate 파이프라인 완성 및 개선

---

## ✅ 완료된 개선 사항

### 1. 앵커 동등화 지원

**구현 위치**: `apps/seedtest_api/jobs/mirt_calibrate.py`

- ✅ `question.meta`에서 앵커 문항 자동 로드 (tags에 "anchor" 포함)
- ✅ 앵커 파라미터를 r-irt-plumber에 전달
- ✅ Linking constants를 `mirt_fit_meta.model_spec.linking_constants`에 저장

**앵커 문항 설정 예시**:
```sql
-- 문항에 "anchor" 태그 추가
UPDATE question
SET meta = jsonb_set(
    COALESCE(meta, '{}'::jsonb),
    '{tags}',
    '["algebra", "anchor"]'::jsonb,
    true
)
WHERE id = 1001;

-- 또는 question.meta.irt에 이미 파라미터가 있고 anchor로 고정
UPDATE question
SET meta = jsonb_set(
    jsonb_set(
        COALESCE(meta, '{}'::jsonb),
        '{irt}',
        '{"a": 1.0, "b": 0.0, "model": "2PL"}'::jsonb,
        true
    ),
    '{tags}',
    '["anchor"]'::jsonb,
    true
)
WHERE id = 1001;
```

### 2. Linking Constants 저장

**저장 위치**: `mirt_fit_meta.model_spec.linking_constants`

Linking constants는 앵커 동등화 시 생성되며, 다음 모델 간 파라미터 변환에 사용됩니다.

**조회 예시**:
```sql
SELECT 
    run_id,
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
WHERE model_spec ? 'linking_constants'
ORDER BY fitted_at DESC
LIMIT 1;
```

### 3. question.meta.irt 반영

**방법 1: 캘리브레이션 중 자동 반영** (옵션)

환경 변수 `IRT_UPDATE_QUESTION_META=true` 설정 시 캘리브레이션 결과를 자동으로 `question.meta.irt`에 반영합니다.

**CronJob 설정 예시**:
```yaml
env:
  - name: IRT_UPDATE_QUESTION_META
    value: "true"  # 캘리브레이션 후 question.meta 자동 업데이트
```

**방법 2: 별도 Job으로 배치 반영**

**파일**: `apps/seedtest_api/jobs/update_question_meta_from_calibration.py`

```bash
# 배치 업데이트 실행
python3 -m apps.seedtest_api.jobs.update_question_meta_from_calibration

# Dry-run
DRY_RUN=true python3 -m apps.seedtest_api.jobs.update_question_meta_from_calibration
```

---

## 📋 파이프라인 구조

### 데이터 흐름

```
attempt VIEW
    ↓
관측 추출 (user_id, item_id, correct, responded_at)
    ↓
앵커 로드 (question.meta에서 "anchor" 태그 확인)
    ↓
r-irt-plumber /irt/calibrate
    ↓
결과: item_params, abilities, fit_meta (linking_constants 포함)
    ↓
저장:
  - mirt_item_params
  - mirt_ability
  - mirt_fit_meta (linking_constants 포함)
    ↓
(선택) question.meta.irt 업데이트
```

### 앵커 동등화 흐름

```
기존 앵커 문항 (question.meta.irt에 파라미터 있음)
    ↓
앵커 문항을 fixed로 표시
    ↓
r-irt-plumber가 앵커 기준으로 신규 문항 동등화
    ↓
Linking constants 생성 (A, B: theta_new = A * theta_old + B)
    ↓
mirt_fit_meta.model_spec.linking_constants에 저장
```

---

## 🔧 CronJob 설정

### 현재 설정

**파일**: `portal_front/ops/k8s/cron/mirt-calibrate.yaml

**주요 설정**:
- 스케줄: 매일 03:00 UTC
- 이미지: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:f830ff9c2-with-env`
- 명령어: `python3 -m apps.seedtest_api.jobs.mirt_calibrate`
- 환경 변수:
  - `IRT_CALIB_LOOKBACK_DAYS=30`: 최근 30일 관측 사용
  - `IRT_MODEL=2PL`: 2PL 모델 사용
  - `IRT_UPDATE_QUESTION_META=false`: question.meta 자동 업데이트 비활성화 (기본값)

### 활성화

```bash
# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml

# 상태 확인
kubectl -n seedtest get cronjob mirt-calibrate

# 수동 실행 테스트
kubectl -n seedtest create job --from=cronjob/mirt-calibrate manual-irt-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs job/manual-irt-test-* -c mirt-calibrate --tail=100
```

---

## 🧪 테스트

### 로컬 테스트

```bash
# 환경 변수 설정
export DATABASE_URL="postgresql://..."
export R_IRT_BASE_URL="http://r-irt-plumber.seedtest.svc.cluster.local:80"
export IRT_CALIB_LOOKBACK_DAYS=30
export IRT_MODEL=2PL

# 캘리브레이션 실행
python3 -m apps.seedtest_api.jobs.mirt_calibrate

# question.meta 반영 (별도)
python3 -m apps.seedtest_api.jobs.update_question_meta_from_calibration
```

### 검증

```sql
-- mirt_item_params 확인
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

-- mirt_ability 확인
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

-- Linking constants 확인
SELECT 
    run_id,
    model_spec->'linking_constants' AS linking_constants,
    metrics,
    fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- question.meta.irt 확인
SELECT 
    id,
    meta->'irt'->>'a' AS a,
    meta->'irt'->>'b' AS b,
    meta->'irt'->>'c' AS c,
    meta->'irt'->>'model' AS model,
    meta->'tags' AS tags
FROM question
WHERE meta ? 'irt'
ORDER BY updated_at DESC
LIMIT 10;
```

---

## 📊 모니터링

### Job 상태 확인

```bash
# 최근 실행된 Job
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | \
  grep mirt-calibrate | tail -5

# CronJob 상태
kubectl -n seedtest get cronjob mirt-calibrate

# 이벤트 확인
kubectl -n seedtest get events --sort-by=.lastTimestamp | \
  grep mirt-calibrate | tail -10
```

### 캘리브레이션 메트릭

```sql
-- 최근 캘리브레이션 통계
SELECT 
    DATE_TRUNC('day', fitted_at) AS calib_date,
    COUNT(DISTINCT item_id) AS item_count,
    COUNT(DISTINCT user_id) AS user_count
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

## 🔍 문제 해결

### 관측 데이터 없음

**증상**: `No observations found; exiting.`

**원인**:
- attempt VIEW가 비어있음
- lookback_days가 너무 짧음

**해결**:
```bash
# 관측 데이터 확인
psql $DATABASE_URL -c \
  "SELECT COUNT(*) FROM attempt WHERE completed_at >= NOW() - INTERVAL '30 days';"

# lookback_days 증가
kubectl -n seedtest set env cronjob/mirt-calibrate IRT_CALIB_LOOKBACK_DAYS=60
```

### r-irt-plumber 연결 실패

**증상**: `RuntimeError: R_IRT_BASE_URL is not configured` 또는 HTTP timeout

**해결**:
```bash
# 서비스 확인
kubectl -n seedtest get svc r-irt-plumber

# Pod 확인
kubectl -n seedtest get pods -l app=r-irt-plumber

# 엔드포인트 테스트
kubectl -n seedtest exec -it <api-pod> -- \
  curl http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz
```

### Linking Constants 미저장

**원인**: r-irt-plumber가 linking constants를 반환하지 않음

**확인**:
```sql
SELECT model_spec->'linking_constants'
FROM mirt_fit_meta
WHERE fitted_at >= NOW() - INTERVAL '7 days'
ORDER BY fitted_at DESC
LIMIT 1;
```

### question.meta 업데이트 실패

**원인**: question 테이블에 해당 item_id가 없음

**해결**: `update_question_meta_from_calibration.py` Job을 별도로 실행하여 배치 업데이트

---

## 🚀 다음 단계

### 권장 개선

1. **부분 캘리브레이션**: 신규 문항만 선택적으로 캘리브레이션
2. **캐싱**: 동일한 관측 데이터 재사용 방지
3. **병렬 처리**: 대용량 관측 데이터 처리 속도 향상

### 관련 작업

- ✅ IRT calibrate 파이프라인 완성
- ⏭️ GLMM fit_progress 엔드포인트 추가
- ⏭️ brms/prophet/survival 서비스 스캐폴딩

---

**IRT 캘리브레이션 파이프라인 완성 완료!** 🎉

