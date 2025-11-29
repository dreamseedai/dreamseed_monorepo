# IRT 캘리브레이션 후속 작업 가이드

**작성일**: 2025-11-02  
**상태**: IRT calibrate 완성, 후속 작업 준비

---

## ✅ 완료된 작업

### IRT Calibrate 파이프라인

- ✅ 관측치 추출 (`attempt` VIEW)
- ✅ r-irt-plumber `/irt/calibrate` 호출
- ✅ `mirt_item_params`, `mirt_ability`, `mirt_fit_meta` upsert
- ✅ 앵커 동등화 지원 (linking constants 저장)
- ✅ CronJob 매니페스트 준비 완료

---

## 📋 권장 후속 작업

### 1. I_t(개선지수) θ-델타 기반 전환

**목적**: 정답률 기반 improvement를 θ 기반으로 전환

**파일**: `apps/seedtest_api/services/metrics.py` - `compute_improvement_index`

**현재 구현**:
- 정답률 기반 improvement 계산

**개선 방향**:
```python
def compute_improvement_index(
    session,
    user_id: str,
    target_date: date,
    window_days: int = 14,
) -> float:
    """Compute improvement index using θ delta (preferred) or accuracy fallback.
    
    Priority:
    1. θ delta from mirt_ability or student_topic_theta
    2. Accuracy delta (fallback)
    """
    # Try θ-based calculation first
    since_date = target_date - timedelta(days=window_days)
    
    # Load θ values
    theta_recent = _load_theta(session, user_id, target_date)
    theta_prev = _load_theta(session, user_id, since_date)
    
    if theta_recent is not None and theta_prev is not None:
        # θ-based improvement (delta normalized)
        theta_delta = theta_recent - theta_prev
        # Normalize by typical SE (e.g., 0.3)
        improvement = theta_delta / 0.3
        return max(-1.0, min(1.0, improvement))  # Clamp to [-1, 1]
    
    # Fallback: accuracy-based
    return _compute_accuracy_improvement(session, user_id, since_date, target_date)
```

**테이블 활용**:
- `mirt_ability`: 전체 능력 (user_id, theta, se, fitted_at)
- `student_topic_theta`: 토픽별 능력 (user_id, topic_id, theta, se, updated_at)

---

### 2. features_topic_daily에 θ 백필

**목적**: 일별 토픽 피처에 θ_mean/θ_sd 채우기

**파일**: `apps/seedtest_api/jobs/aggregate_features_daily.py` - `_load_theta_if_needed`

**현재 구현**:
- `student_topic_theta` 또는 `mirt_ability`에서 θ 로드
- `theta_mean`, `theta_sd` 컬럼에 저장

**확인 사항**:
- 현재 `_load_theta_if_needed` 함수가 올바르게 동작하는지
- `AGG_INCLUDE_THETA` 환경 변수로 제어되는지

**개선 사항**:
```python
def _load_theta_if_needed(
    session,
    user_id: str,
    topic_id: str,
    target_date: date,
) -> tuple[float | None, float | None]:
    """Load θ estimate and SE for user/topic/date.
    
    Priority:
    1. student_topic_theta (topic-specific, preferred)
    2. mirt_ability (general ability, fallback)
    
    Returns:
        (theta_mean, theta_sd) or (None, None)
    """
    # Try topic-specific first
    result = session.execute(
        text("""
            SELECT theta, se, updated_at
            FROM student_topic_theta
            WHERE user_id = :user_id
              AND topic_id = :topic_id
              AND updated_at >= :since_date
            ORDER BY updated_at DESC
            LIMIT 1
        """),
        {
            "user_id": user_id,
            "topic_id": topic_id,
            "since_date": target_date - timedelta(days=30),
        },
    )
    row = result.fetchone()
    
    if row and row[0] is not None:
        return (float(row[0]), float(row[1]) if row[1] else None)
    
    # Fallback: general ability
    result = session.execute(
        text("""
            SELECT theta, se, fitted_at
            FROM mirt_ability
            WHERE user_id = :user_id
              AND fitted_at >= :since_date
            ORDER BY fitted_at DESC
            LIMIT 1
        """),
        {
            "user_id": user_id,
            "since_date": target_date - timedelta(days=30),
        },
    )
    row = result.fetchone()
    
    if row and row[0] is not None:
        return (float(row[0]), float(row[1]) if row[1] else None)
    
    return (None, None)
```

---

### 3. Anchoring/동등화 완성

**현재 상태**:
- ✅ `question.meta.tags`에서 "anchor" 태그 확인
- ✅ 앵커 파라미터 로드 (`question.meta.irt`에서 a, b, c)
- ✅ `anchors` 파라미터를 r-irt-plumber에 전달
- ✅ Linking constants를 `mirt_fit_meta.model_spec.linking_constants`에 저장

**확인 필요**:
1. r-irt-plumber가 `anchors` 파라미터를 지원하는지
2. Linking constants가 응답에 포함되는지

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

## 🔧 구현 우선순위

### Phase 1: 즉시 적용 가능 (현재)

1. ✅ **IRT Calibrate 파이프라인**: 완료
2. ✅ **CronJob 매니페스트**: 생성 완료
3. ⏭️ **검증 스크립트**: DB 쿼리 실행

### Phase 2: 다음 주 (권장)

1. **I_t θ-델타 전환**: `compute_improvement_index` 개선
2. **θ 백필 완성**: `aggregate_features_daily`에서 θ_mean/θ_sd 채우기
3. **앵커 동등화 검증**: r-irt-plumber 응답 확인 및 linking constants 활용

### Phase 3: 추가 개선

1. **Version 관리**: 캘리브레이션 버전(`v1`, `v2`) vs 온라인 버전(`online-...`) 구분
2. **부분 캘리브레이션**: 신규 문항만 선택적으로 캘리브레이션
3. **자동 앵커 선택**: 통계적 기준으로 앵커 문항 자동 선택

---

## 📊 모니터링 및 알림

### CronJob 성공/실패 알림

```yaml
# Kubernetes Event 기반 모니터링
kubectl -n seedtest get events --field-selector involvedObject.kind=Job --sort-by=.lastTimestamp | grep calibrate-irt
```

### DB 메트릭 확인

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
```

---

## 🚀 다음 단계

1. **CronJob 배포**: `kubectl apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml`
2. **검증 실행**: Job으로 즉시 테스트
3. **후속 작업 구현**: I_t 전환, θ 백필, 앵커 검증

**모든 준비 완료!** 🎉

