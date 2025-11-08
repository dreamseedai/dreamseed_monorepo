# IRT Analytics Pipeline - 통합 테스트 가이드

**최종 업데이트**: 2025-11-01 23:56 KST  
**상태**: ✅ 모든 구현 완료 - 테스트 준비

---

## 🎯 구현 완료 항목

### 1. I_t θ-델타 기반 전환 ✅
- **파일**: `apps/seedtest_api/services/metrics.py`
- **함수**: `compute_improvement_index(conn, user_id, as_of)`
- **로직**: θ 우선 → 정답률 폴백

### 2. features_topic_daily θ 채우기 ✅
- **파일**: `apps/seedtest_api/services/features_backfill.py`
- **함수**: `load_user_topic_theta()`, `backfill_features_topic_daily()`
- **로직**: student_topic_theta → mirt_ability 폴백

### 3. mirt_calibrate anchors 지원 ✅
- **파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`
- **함수**: `_load_anchors()`, payload에 anchors 포함
- **페이로드**: `{"observations": [...], "model": "2PL", "anchors": [...]}`

### 4. 재시도 로직 (백오프) ✅
- **파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`
- **함수**: `_call_calibrate()` - 3회 재시도 (0.5s, 1.0s, 1.5s)

### 5. Calibrate CronJob ✅
- **파일**: `portal_front/ops/k8s/cron/calibrate-irt.yaml`
- **스케줄**: 매일 03:00 UTC

---

## 🧪 테스트 시나리오

### Test 1: I_t θ-델타 계산 (θ 있는 경우)

**사전 준비**:
```sql
-- 테스트 사용자에 θ 데이터 삽입
INSERT INTO mirt_ability (user_id, theta, se, fitted_at, run_id)
VALUES 
  ('test-user-001', 0.5, 0.3, NOW() - INTERVAL '7 days', 'test-run-recent'),
  ('test-user-001', 0.2, 0.3, NOW() - INTERVAL '21 days', 'test-run-old');

-- 검증: θ 데이터 확인
SELECT user_id, theta, se, fitted_at 
FROM mirt_ability 
WHERE user_id = 'test-user-001'
ORDER BY fitted_at DESC;
```

**테스트 실행**:
```python
# Python 테스트
from apps.seedtest_api.services.db import get_session
from apps.seedtest_api.services.metrics import compute_improvement_index
from datetime import date

with get_session() as session:
    i_t = compute_improvement_index(
        session, 
        user_id='test-user-001', 
        as_of=date.today()
    )
    print(f"I_t (theta-based): {i_t}")
    # 예상: Δθ = 0.5 - 0.2 = 0.3 기반 계산
```

**예상 결과**:
```
I_t (theta-based): 0.285  # (Δθ × exposure_adj × se_penalty)
```

**검증 SQL**:
```sql
-- weekly_kpi에서 I_t 확인
SELECT 
    user_id, 
    week_start, 
    kpis->>'I_t' AS improvement_index,
    kpis->>'method' AS calculation_method
FROM weekly_kpi
WHERE user_id = 'test-user-001'
ORDER BY week_start DESC
LIMIT 5;

-- 예상: method = 'theta_delta'
```

---

### Test 2: I_t 정답률 폴백 (θ 없는 경우)

**사전 준비**:
```sql
-- θ 데이터 없는 사용자
DELETE FROM mirt_ability WHERE user_id = 'test-user-002';

-- attempt 데이터는 있어야 함
SELECT COUNT(*) FROM attempt WHERE student_id::text = 'test-user-002';
```

**테스트 실행**:
```python
with get_session() as session:
    i_t = compute_improvement_index(
        session, 
        user_id='test-user-002', 
        as_of=date.today()
    )
    print(f"I_t (accuracy-based): {i_t}")
    # 예상: Δ정답률 기반 계산
```

**예상 결과**:
```
I_t (accuracy-based): 0.125  # (Δaccuracy × exposure_adj × ci_penalty)
```

**검증 SQL**:
```sql
SELECT 
    user_id, 
    kpis->>'I_t' AS improvement_index,
    kpis->>'method' AS calculation_method
FROM weekly_kpi
WHERE user_id = 'test-user-002'
ORDER BY week_start DESC
LIMIT 1;

-- 예상: method = 'accuracy_delta' 또는 NULL
```

---

### Test 3: features_topic_daily θ 백필

**사전 준비**:
```sql
-- θ 데이터 준비
INSERT INTO mirt_ability (user_id, theta, se, fitted_at, run_id)
VALUES ('test-user-003', 1.2, 0.25, NOW() - INTERVAL '1 day', 'test-run-001');

-- 또는 topic-level θ
INSERT INTO student_topic_theta (user_id, topic_id, theta, se, updated_at)
VALUES ('test-user-003', 'topic-math', 1.5, 0.2, NOW() - INTERVAL '1 day');

-- attempt 데이터 확인
SELECT COUNT(*) FROM attempt 
WHERE student_id::text = 'test-user-003' 
  AND topic_id = 'topic-math'
  AND completed_at >= NOW() - INTERVAL '7 days';
```

**테스트 실행**:
```python
from apps.seedtest_api.services.features_backfill import backfill_features_topic_daily
from datetime import date, timedelta

target_date = date.today() - timedelta(days=1)

with get_session() as session:
    backfill_features_topic_daily(
        session,
        user_id='test-user-003',
        topic_id='topic-math',
        target_date=target_date,
        include_theta=True  # ← θ 포함
    )
    print(f"Backfilled for {target_date}")
```

**검증 SQL**:
```sql
-- features_topic_daily에서 θ 확인
SELECT 
    user_id, 
    topic_id, 
    date,
    attempts,
    correct,
    theta_estimate,  -- ← 채워져야 함
    theta_sd,        -- ← 채워져야 함
    improvement
FROM features_topic_daily
WHERE user_id = 'test-user-003'
  AND topic_id = 'topic-math'
  AND date >= NOW() - INTERVAL '7 days'
ORDER BY date DESC;

-- 예상: theta_estimate = 1.5 (topic-level) 또는 1.2 (user-level)
```

---

### Test 4: mirt_calibrate anchors 페이로드

**사전 준비**:
```sql
-- 앵커 문항 태깅
UPDATE question
SET meta = jsonb_set(
    COALESCE(meta, '{}'::jsonb),
    '{tags}',
    '["anchor"]'::jsonb,
    true
)
WHERE id IN (101, 102, 103, 104, 105);

-- IRT 파라미터 설정
UPDATE question
SET meta = jsonb_set(
    COALESCE(meta, '{}'::jsonb),
    '{irt}',
    '{"a": 1.2, "b": 0.5, "c": 0.25}'::jsonb,
    true
)
WHERE id IN (101, 102, 103, 104, 105);

-- 검증
SELECT id, meta->'tags', meta->'irt'
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb
LIMIT 10;
```

**테스트 실행** (Dry-run):
```bash
# Dry-run으로 페이로드 확인
DRY_RUN=true python -m apps.seedtest_api.jobs.mirt_calibrate
```

**예상 출력**:
```
[INFO] Loaded 12345 observations from attempt VIEW
[INFO] Loaded 5 anchors/seeds from question.meta
[INFO] Anchor items: [101, 102, 103, 104, 105]
[DRY_RUN] Would send payload:
{
  "observations": [...],
  "model": "2PL",
  "anchors": [
    {"item_id": "101", "params": {"a": 1.2, "b": 0.5, "c": 0.25}, "fixed": true},
    {"item_id": "102", "params": {"a": 1.2, "b": 0.5, "c": 0.25}, "fixed": true},
    ...
  ]
}
```

**실제 테스트** (R IRT 서비스 필요):
```bash
# R IRT 서비스 확인
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -sS http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz

# Calibration 실행
python -m apps.seedtest_api.jobs.mirt_calibrate
```

**검증 SQL**:
```sql
-- mirt_fit_meta에서 anchors 사용 확인
SELECT 
    run_id,
    model_spec->>'n_anchors' AS n_anchors,
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- 예상: n_anchors = 5, linking_constants = {"slope": 1.02, "intercept": 0.05}
```

---

### Test 5: 재시도 로직 (백오프)

**테스트 방법**: R IRT 서비스를 일시적으로 중지하여 재시도 로직 확인

**사전 준비**:
```bash
# R IRT 서비스 스케일 다운 (재시도 테스트용)
kubectl -n seedtest scale deployment r-irt-plumber --replicas=0

# 확인
kubectl -n seedtest get pods -l app=r-irt-plumber
```

**테스트 실행**:
```bash
# Calibration 실행 (재시도 발생)
python -m apps.seedtest_api.jobs.mirt_calibrate
```

**예상 출력**:
```
[INFO] Loaded 12345 observations from attempt VIEW
[INFO] Loaded 5 anchors/seeds from question.meta
[INFO] Calling R IRT service...
[WARN] R IRT service call failed (attempt 1/3): Connection refused
[INFO] Retrying in 0.5 seconds...
[WARN] R IRT service call failed (attempt 2/3): Connection refused
[INFO] Retrying in 1.0 seconds...
[WARN] R IRT service call failed (attempt 3/3): Connection refused
[ERROR] R IRT service call failed after 3 attempts
```

**복구**:
```bash
# R IRT 서비스 복구
kubectl -n seedtest scale deployment r-irt-plumber --replicas=2
```

---

### Test 6: Calibrate CronJob 배포 및 실행

**배포**:
```bash
# CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 확인
kubectl -n seedtest get cronjob calibrate-irt-nightly
kubectl -n seedtest describe cronjob calibrate-irt-nightly
```

**예상 출력**:
```
NAME                    SCHEDULE    SUSPEND   ACTIVE   LAST SCHEDULE   AGE
calibrate-irt-nightly   0 3 * * *   False     0        <none>          10s
```

**수동 실행**:
```bash
# One-off Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-nightly \
  calibrate-irt-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/calibrate-irt-test-<timestamp>
```

**예상 로그**:
```
[INFO] Loaded 12345 observations from attempt VIEW
[INFO] Loaded 50 anchors/seeds from question.meta
[INFO] Total observations: 12345
[INFO] Model: 2PL, Anchors: 50
[INFO] Calling R IRT service...
[INFO] Linking constants received: {'slope': 1.02, 'intercept': 0.05}
Calibration upsert completed: 150 items, 500 abilities
Linking constants stored in fit_meta.model_spec.linking_constants
✅ IRT calibration completed successfully
```

**검증**:
```sql
-- 최근 calibration 결과 확인
SELECT 
    run_id,
    model_spec->>'model' AS model,
    model_spec->>'n_items' AS n_items,
    model_spec->>'n_users' AS n_users,
    model_spec->>'n_anchors' AS n_anchors,
    model_spec->'linking_constants' AS linking_constants,
    metrics->>'aic' AS aic,
    fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- mirt_item_params 확인
SELECT COUNT(*), AVG((params->>'a')::float), AVG((params->>'b')::float)
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 hour';

-- mirt_ability 확인
SELECT COUNT(*), AVG(theta), STDDEV(theta)
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 hour';
```

---

## 🔍 통합 테스트 체크리스트

### Phase 1: 단위 테스트
- [ ] I_t θ-델타 계산 (θ 있음)
- [ ] I_t 정답률 폴백 (θ 없음)
- [ ] features_backfill θ 로드 (topic-level)
- [ ] features_backfill θ 로드 (user-level 폴백)
- [ ] mirt_calibrate anchors 로드
- [ ] mirt_calibrate 재시도 로직

### Phase 2: 통합 테스트
- [ ] aggregate_features_daily 실행 (AGG_INCLUDE_THETA=true)
- [ ] compute_daily_kpis 실행 (I_t 계산)
- [ ] mirt_calibrate 전체 파이프라인 (anchors 포함)
- [ ] Calibrate CronJob 수동 실행

### Phase 3: 엔드투엔드 테스트
- [ ] 앵커 문항 태깅 → Calibration → KPI 계산 → 리포트 생성
- [ ] θ 데이터 흐름: mirt_ability → features_topic_daily → weekly_kpi
- [ ] Linking constants: calibration → fit_meta → weekly_report

---

## 🐛 문제 해결

### 문제 1: I_t가 NULL

**원인**:
- θ 데이터 없음
- attempt 데이터 부족

**해결**:
```sql
-- θ 데이터 확인
SELECT COUNT(*) FROM mirt_ability WHERE user_id = '<user_id>';

-- attempt 데이터 확인
SELECT COUNT(*) FROM attempt 
WHERE student_id::text = '<user_id>'
  AND completed_at >= NOW() - INTERVAL '28 days';

-- 수동 calibration 실행
python -m apps.seedtest_api.jobs.mirt_calibrate
```

---

### 문제 2: features_topic_daily theta_estimate NULL

**원인**:
- `AGG_INCLUDE_THETA=false`
- θ 데이터 없음

**해결**:
```bash
# 환경 변수 확인
echo $AGG_INCLUDE_THETA  # 'true'여야 함

# 수동 백필
python -c "
from apps.seedtest_api.services.features_backfill import backfill_features_topic_daily
from apps.seedtest_api.services.db import get_session
from datetime import date, timedelta

with get_session() as session:
    backfill_features_topic_daily(
        session,
        user_id='<user_id>',
        topic_id='<topic_id>',
        target_date=date.today() - timedelta(days=1),
        include_theta=True
    )
"
```

---

### 문제 3: anchors 페이로드 비어있음

**원인**:
- 앵커 문항 태그 없음

**해결**:
```bash
# 앵커 문항 태깅
python -m apps.seedtest_api.jobs.tag_anchor_items --max-candidates 50

# 검증
python -c "
from apps.seedtest_api.services.db import get_session
from sqlalchemy import text

with get_session() as session:
    result = session.execute(text('''
        SELECT COUNT(*) FROM question 
        WHERE meta->'tags' @> '[\"anchor\"]'::jsonb
    '''))
    print(f'Anchor items: {result.fetchone()[0]}')
"
```

---

### 문제 4: R IRT 서비스 연결 실패

**원인**:
- R IRT 서비스 미배포
- 네트워크 이슈

**해결**:
```bash
# 서비스 상태 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# Health check
kubectl -n seedtest run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz

# 로그 확인
kubectl -n seedtest logs -l app=r-irt-plumber --tail=50
```

---

## 📊 성능 벤치마크

### 예상 실행 시간

| Job | 데이터 규모 | 예상 시간 | 비고 |
|-----|------------|----------|------|
| mirt_calibrate | 10K obs, 100 items | 2-5분 | R IRT 서비스 성능 의존 |
| aggregate_features_daily | 1K users, 7 days | 1-3분 | θ 로드 포함 시 +20% |
| compute_daily_kpis | 1K users | 30초-1분 | I_t θ 계산 포함 |
| tag_anchor_items | 1K items | 10-30초 | 안정성 검증 포함 |

### 최적화 팁

1. **mirt_calibrate**:
   - `MIRT_MAX_OBS` 설정으로 관측 수 제한
   - 앵커 수를 50개 이하로 유지

2. **aggregate_features_daily**:
   - `AGG_LOOKBACK_DAYS` 최소화 (기본 7일)
   - 병렬 처리 고려 (user_id 기준 샤딩)

3. **compute_daily_kpis**:
   - 주간 단위로 실행 (매일 불필요)
   - 증분 업데이트 고려

---

## ✅ 테스트 완료 기준

### 성공 기준
- [ ] I_t가 θ 기반으로 계산됨 (θ 있는 경우)
- [ ] I_t가 정답률 기반으로 폴백됨 (θ 없는 경우)
- [ ] features_topic_daily에 theta_estimate 채워짐
- [ ] mirt_calibrate anchors 페이로드 포함
- [ ] 재시도 로직 작동 (3회)
- [ ] Calibrate CronJob 정상 실행
- [ ] linking_constants 저장 및 리포트 표시

### 데이터 검증
```sql
-- 전체 파이프라인 검증
WITH recent_calibration AS (
    SELECT run_id, fitted_at
    FROM mirt_fit_meta
    ORDER BY fitted_at DESC
    LIMIT 1
)
SELECT 
    'mirt_item_params' AS table_name,
    COUNT(*) AS count,
    MAX(fitted_at) AS last_update
FROM mirt_item_params
WHERE run_id = (SELECT run_id FROM recent_calibration)
UNION ALL
SELECT 
    'mirt_ability',
    COUNT(*),
    MAX(fitted_at)
FROM mirt_ability
WHERE run_id = (SELECT run_id FROM recent_calibration)
UNION ALL
SELECT 
    'features_topic_daily (with theta)',
    COUNT(*),
    MAX(computed_at)
FROM features_topic_daily
WHERE theta_estimate IS NOT NULL
  AND date >= NOW() - INTERVAL '7 days'
UNION ALL
SELECT 
    'weekly_kpi (with I_t)',
    COUNT(*),
    MAX(updated_at)
FROM weekly_kpi
WHERE kpis ? 'I_t'
  AND week_start >= NOW() - INTERVAL '4 weeks';
```

---

**최종 업데이트**: 2025-11-01 23:56 KST  
**작성자**: Cascade AI  
**상태**: ✅ 테스트 준비 완료
