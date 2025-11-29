# IRT 파이프라인 테스트 체크리스트

**작성일**: 2025-11-02  
**상태**: ✅ 테스트 준비 완료

---

## ✅ 테스트 항목

### 1. I_t θ 전환 테스트

**목적**: θ 값이 있을 때 θ 기반 계산, 없을 때 정답률 기반 폴백 확인

#### 준비

```sql
-- 테스트 사용자의 θ 값 확인
SELECT user_id, theta, se, fitted_at
FROM mirt_ability
WHERE user_id = 'test-user-123'
ORDER BY fitted_at DESC
LIMIT 10;

-- 최근 14일간 시도 확인
SELECT COUNT(*) 
FROM attempt
WHERE student_id::text = 'test-user-123'
  AND completed_at >= NOW() - INTERVAL '14 days';
```

#### 테스트

```bash
# 환경 변수 설정
export METRICS_USE_IRT_THETA=true
export DATABASE_URL="postgresql://..."

# I_t 계산 (Python REPL 또는 테스트 스크립트)
python3 -c "
from apps.seedtest_api.services.metrics import compute_improvement_index
from apps.seedtest_api.services.db import get_session
from datetime import date

with get_session() as session:
    i_t = compute_improvement_index(
        session, 
        'test-user-123', 
        date.today(),
        window_days=14
    )
    print(f'I_t: {i_t}')
"
```

#### 검증

- [ ] θ 값이 있을 때: `compute_improvement_index`가 θ 델타 기반 값 반환
- [ ] θ 값이 없을 때: 정답률 기반 폴백 값 반환
- [ ] `METRICS_USE_IRT_THETA=false`일 때: 항상 정답률 기반

#### 확인 쿼리

```sql
-- 사용자의 최근 I_t 값 확인
SELECT 
    user_id,
    week_start,
    kpis->>'I_t' AS i_t,
    updated_at
FROM weekly_kpi
WHERE user_id = 'test-user-123'
ORDER BY week_start DESC
LIMIT 5;
```

---

### 2. features_topic_daily θ 채움 테스트

**목적**: `theta_mean`, `theta_sd` 컬럼이 올바르게 채워지는지 확인

#### 준비

```sql
-- 테스트 사용자/토픽의 θ 값 확인
SELECT user_id, topic_id, theta, se, updated_at
FROM student_topic_theta
WHERE user_id = 'test-user-123'
ORDER BY updated_at DESC
LIMIT 10;

-- 또는 전체 능력
SELECT user_id, theta, se, fitted_at
FROM mirt_ability
WHERE user_id = 'test-user-123'
ORDER BY fitted_at DESC
LIMIT 5;
```

#### 테스트

```bash
# 환경 변수 설정
export AGG_INCLUDE_THETA=true
export DATABASE_URL="postgresql://..."

# 단일 사용자/토픽 백필
python3 -c "
from apps.seedtest_api.services.features_backfill import backfill_features_topic_daily
from apps.seedtest_api.services.db import get_session
from datetime import date

with get_session() as session:
    backfill_features_topic_daily(
        session,
        'test-user-123',
        'topic-1',
        date.today(),
        include_theta=True
    )
    session.commit()
    print('Backfill completed')
"
```

#### 검증

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
WHERE student_id::text = 'test-user-123'
  AND theta_mean IS NOT NULL
ORDER BY date DESC
LIMIT 10;
```

#### 확인 항목

- [ ] `theta_mean`이 채워짐
- [ ] `theta_sd`가 채워짐 (SE 값 사용)
- [ ] `student_topic_theta` 우선, 없으면 `mirt_ability` 사용
- [ ] `AGG_INCLUDE_THETA=false`일 때: `theta_mean`, `theta_sd`가 NULL

---

### 3. calibrate-irt Cron 테스트

**목적**: CronJob이 올바르게 실행되고 결과가 저장되는지 확인

#### 준비

```bash
# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# CronJob 상태 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly
```

#### 테스트

```bash
# 수동 Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  calibrate-irt-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs job/calibrate-irt-test-* -c calibrate-irt -f
```

#### 검증

```sql
-- 최근 캘리브레이션 결과 확인
SELECT 
    COUNT(*) AS item_count,
    COUNT(DISTINCT item_id) AS unique_items,
    MAX(fitted_at) AS latest_fit
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 hour';

-- Ability 확인
SELECT 
    COUNT(*) AS ability_count,
    COUNT(DISTINCT user_id) AS unique_users,
    AVG(theta) AS avg_theta,
    MAX(fitted_at) AS latest_fit
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 hour';

-- Fit meta 확인
SELECT 
    run_id,
    model_spec->'model' AS model,
    model_spec->'n_items' AS n_items,
    model_spec->'n_observations' AS n_observations,
    fitted_at
FROM mirt_fit_meta
WHERE fitted_at >= NOW() - INTERVAL '1 hour'
ORDER BY fitted_at DESC
LIMIT 1;
```

#### 확인 항목

- [ ] Job이 성공적으로 완료됨
- [ ] `mirt_item_params`에 아이템 파라미터 저장
- [ ] `mirt_ability`에 능력 추정치 저장
- [ ] `mirt_fit_meta`에 메타데이터 저장
- [ ] 재시도 로직이 동작 (로그에서 확인)

---

### 4. Anchors/Linking 테스트

**목적**: Anchors가 로드되고 linking constants가 계산/저장되는지 확인

#### 준비

```bash
# Anchor 아이템 태깅
python -m apps.seedtest_api.jobs.tag_anchor_items

# 검증
python -m apps.seedtest_api.jobs.tag_anchor_items verify
```

#### 확인

```sql
-- Anchor 아이템 확인
SELECT 
    id,
    meta->'tags' AS tags,
    meta->'irt'->>'a' AS anchor_a,
    meta->'irt'->>'b' AS anchor_b
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb
LIMIT 10;
```

#### 테스트

```bash
# 캘리브레이션 실행 (anchors 포함)
python -m apps.seedtest_api.jobs.mirt_calibrate

# 또는 Kubernetes Job
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  calibrate-irt-anchors-test-$(date +%s)
```

#### 검증

```sql
-- Linking constants 확인
SELECT 
    run_id,
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
WHERE model_spec ? 'linking_constants'
ORDER BY fitted_at DESC
LIMIT 1;

-- Anchor 아이템의 캘리브레이션된 파라미터 확인
SELECT 
    mip.item_id,
    mip.params->>'a' AS calibrated_a,
    mip.params->>'b' AS calibrated_b,
    q.meta->'irt'->>'a' AS anchor_a,
    q.meta->'irt'->>'b' AS anchor_b,
    mip.fitted_at
FROM mirt_item_params mip
JOIN question q ON q.id::text = mip.item_id
WHERE q.meta->'tags' @> '["anchor"]'::jsonb
ORDER BY mip.fitted_at DESC
LIMIT 10;
```

#### 확인 항목

- [ ] 로그에 "Loaded N anchors/seeds from question.meta" 메시지
- [ ] 페이로드에 `anchors` 필드 포함 (r-irt-plumber 로그 확인)
- [ ] 응답에 `linking_constants` 포함 (r-irt-plumber 측 구현 필요)
- [ ] `mirt_fit_meta.model_spec.linking_constants`에 저장됨

#### 리포트에서 확인

```bash
# 리포트 생성 (linking constants 포함)
python -m apps.seedtest_api.jobs.generate_weekly_report \
  --user test-user-123 \
  --week 2025-11-03

# 리포트에서 Linking Constants 섹션 확인
# reports/quarto/weekly_report.qmd 템플릿에서 표시됨
```

---

## 통합 테스트 시나리오

### 시나리오 1: 전체 파이프라인 테스트

1. **Anchor 아이템 태깅**
   ```bash
   python -m apps.seedtest_api.jobs.tag_anchor_items
   ```

2. **IRT 캘리브레이션 실행**
   ```bash
   kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
     calibrate-irt-full-test-$(date +%s)
   ```

3. **일별 피처 집계 (θ 포함)**
   ```bash
   export AGG_INCLUDE_THETA=true
   python -m apps.seedtest_api.jobs.aggregate_features_daily
   ```

4. **주간 KPI 계산 (θ 기반 I_t)**
   ```bash
   export METRICS_USE_IRT_THETA=true
   python -m apps.seedtest_api.jobs.compute_daily_kpis
   ```

5. **리포트 생성**
   ```bash
   python -m apps.seedtest_api.jobs.generate_weekly_report \
     --user test-user-123 --week 2025-11-03
   ```

### 검증

```sql
-- 전체 파이프라인 결과 확인
SELECT 
    'mirt_item_params' AS table_name,
    COUNT(*) AS count,
    MAX(fitted_at) AS latest
FROM mirt_item_params
UNION ALL
SELECT 
    'mirt_ability',
    COUNT(*),
    MAX(fitted_at)
FROM mirt_ability
UNION ALL
SELECT 
    'features_topic_daily (with theta)',
    COUNT(*),
    MAX(updated_at)
FROM features_topic_daily
WHERE theta_mean IS NOT NULL
UNION ALL
SELECT 
    'weekly_kpi (with I_t)',
    COUNT(*),
    MAX(updated_at)
FROM weekly_kpi
WHERE kpis ? 'I_t';
```

---

## 문제 해결

### I_t가 θ 기반이 아닌 경우

**원인**: `METRICS_USE_IRT_THETA=false` 또는 θ 값 없음

**해결**:
```bash
# 환경 변수 확인
echo $METRICS_USE_IRT_THETA

# θ 값 확인
psql $DATABASE_URL -c "
SELECT user_id, theta, fitted_at
FROM mirt_ability
WHERE user_id = 'test-user-123'
ORDER BY fitted_at DESC
LIMIT 1;
"
```

### features_topic_daily에 θ가 없음

**원인**: `AGG_INCLUDE_THETA=false` 또는 θ 값 없음

**해결**:
```bash
# 환경 변수 설정
export AGG_INCLUDE_THETA=true

# θ 값 확인
psql $DATABASE_URL -c "
SELECT * FROM student_topic_theta WHERE user_id = 'test-user-123';
SELECT * FROM mirt_ability WHERE user_id = 'test-user-123';
"
```

### Linking constants가 없음

**원인**: r-irt-plumber 측 anchors 처리 미구현

**해결**: `R_IRT_PLUMBER_ANCHORS_GUIDE.md` 참고하여 R 서비스 수정

---

## 테스트 완료 체크리스트

- [ ] I_t θ 전환 테스트 통과
- [ ] features_topic_daily θ 채움 테스트 통과
- [ ] calibrate-irt Cron 테스트 통과
- [ ] Anchors/Linking 테스트 통과 (r-irt-plumber 측 구현 후)
- [ ] 통합 테스트 시나리오 통과

**테스트 준비 완료!** 🧪

