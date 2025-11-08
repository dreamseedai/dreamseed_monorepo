# 통계/모형 설계 준수 점검

**작성일**: 2025-11-02  
**목적**: 요구사항과 구현 상태 대조

---

## ✅ 완전히 적용된 항목

### 1. IRT(mirt/ltm/eRm)
- ✅ **2PL 기본**: `model="2PL"` 기본값 사용
- ✅ **신규 문항 앵커 동등화**: 
  - `tag_anchor_items.py`로 앵커 문항 선정
  - `mirt_calibrate.py`에서 anchors 로드 및 `/irt/calibrate` 전달
  - `linking_constants` 저장 (`mirt_fit_meta.model_spec.linking_constants`)

### 2. 혼합효과(lme4)
- ✅ **Formula**: `score ~ week + (week|student) + (1|topic)` 정확히 구현
- ✅ **평균 추세와 개인차 분리**: 고정효과(week)와 무작위효과(week|student, topic) 포함

### 3. 베이지안(brms)
- ✅ **사전 분포 설정**: priors (intercept, week, sd) 설정됨
- ✅ **목표달성 확률과 불확실성**: `weekly_kpi.P`와 `sigma` 업데이트

### 4. 시계열(prophet)
- ✅ **주차별 향상지수 이력**: `weekly_kpi`에서 `I_t` 추출
- ✅ **단기 추세 예측**: `forecast_periods` 설정 가능
- ✅ **비정상 변동 탐지**: `anomaly_threshold` (Z-score) 기반 탐지

### 5. 생존분석(survival)
- ✅ **14일 미접속 이벤트**: `event_threshold_days=14` 설정
- ✅ **공변량 포함**: 
  - `A_t` (engagement)
  - `E_t` (efficiency)
  - `R_t` (recovery)
  - `mean_gap` (학습간격)
  - `sessions` (세션 수)

---

## ⚠️ 부분 적용 / 개선 필요 항목

### 1. IRT - 과목·토픽별 calibrated bank

**현재 상태**:
- ✅ `attempt VIEW`에 `topic_id` 존재
- ✅ `question` 테이블에 `topic_id` 존재
- ❌ **과목/토픽별 필터링 옵션 없음**: 현재는 전체 데이터로 캘리브레이션

**필요 작업**:
- `mirt_calibrate.py`에 `--topic-id` 또는 `--subject-id` 필터링 옵션 추가
- 또는 각 토픽별로 별도 캘리브레이션 실행 (CronJob에서 반복)

**권장 접근**:
1. 전체 캘리브레이션: 기본 동작 (현재)
2. 토픽별 캘리브레이션: `MIRT_TOPIC_ID` 환경 변수 또는 CLI 옵션으로 필터링
3. 과목별 캘리브레이션: `MIRT_SUBJECT_ID` 환경 변수 (exam_id와 연결?)

---

### 2. 클러스터링 - 의미 있는 세그먼트 라벨

**현재 상태**:
- ✅ 클러스터링 스캐폴딩 완료
- ❌ **세그먼트 라벨**: `"cluster_1"` 형식만 생성 (의미 없는 라벨)

**필요 작업**:
- 세그먼트 특성 기반 의미 있는 라벨 생성:
  - `"short_frequent"`: 짧고 자주 (낮은 gap, 높은 sessions)
  - `"long_rare"`: 길고 드물게 (높은 gap, 낮은 sessions)
  - `"hint_heavy"`: 힌트 집중형 (높은 avg_hints)
  - `"improving"`: 향상 지속형 (높은 improvement)
  - `"struggling"`: 어려움 겪는형 (낮은 efficiency, 높은 hints)

**권장 접근**:
1. 클러스터 중심점(centers) 분석
2. 각 클러스터의 특징 벡터 추출
3. 규칙 기반 라벨링 (임계값 기반)

---

### 3. 베이지안 - 소표본/잡음 안정화 설명

**현재 상태**:
- ✅ Priors 설정됨:
  ```python
  priors = {
      "intercept": {"dist": "normal", "mean": 0, "sd": 1},
      "week": {"dist": "normal", "mean": 0, "sd": 0.5},
      "sd": {"dist": "cauchy", "location": 0, "scale": 1},
  }
  ```
- ⚠️ **소표본/잡음 안정화 설명 부족**: 코드 주석이나 문서에 설명 없음

**필요 작업**:
- `fit_bayesian_growth.py`에 priors 설정 이유 및 소표본/잡음 안정화 설명 추가
- `BAYESIAN_GROWTH_GUIDE.md`에 이론적 배경 추가

---

## 📋 추가 작업 계획

### 작업 1: IRT 과목/토픽별 필터링

**파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`

**변경 사항**:
1. `--topic-id` CLI 옵션 추가
2. `MIRT_TOPIC_ID` 환경 변수 지원
3. SQL 쿼리에 `topic_id` 필터링 추가 (attempt VIEW JOIN 또는 question 테이블 JOIN)

**예상 구현**:
```python
# topic_id 필터링 추가
if topic_id:
    stmt_attempt = sa.text(
        """
        SELECT 
            a.student_id::text AS user_id,
            a.item_id::text AS item_id,
            a.correct AS is_correct,
            a.completed_at AS responded_at
        FROM attempt a
        INNER JOIN question q ON q.id = a.item_id
        WHERE a.completed_at >= :since
          AND a.item_id IS NOT NULL
          AND a.student_id IS NOT NULL
          AND q.topic_id = :topic_id
        ORDER BY a.completed_at
        """
    )
```

---

### 작업 2: 클러스터링 세그먼트 라벨 생성

**파일**: `apps/seedtest_api/jobs/cluster_segments.py`

**변경 사항**:
1. `_generate_segment_label()` 함수 추가
2. 클러스터 중심점과 사용자 피처 비교하여 의미 있는 라벨 생성

**예상 구현**:
```python
def _generate_segment_label(cluster_id: int, center: Dict, user_features: Dict) -> str:
    """Generate meaningful segment label based on cluster characteristics."""
    gap = user_features.get("gap", 7.0)
    sessions = user_features.get("sessions", 0.0)
    hints = user_features.get("avg_hints", 0.0)
    improvement = user_features.get("improvement", 0.0)
    
    # Rule-based labeling
    if gap < 3 and sessions > 10:
        return "short_frequent"
    elif gap > 7 and sessions < 5:
        return "long_rare"
    elif hints > 2.0:
        return "hint_heavy"
    elif improvement > 0.3:
        return "improving"
    elif improvement < -0.2:
        return "struggling"
    else:
        return f"cluster_{cluster_id}"
```

---

### 작업 3: 베이지안 Priors 설명 보강

**파일**: 
- `apps/seedtest_api/jobs/fit_bayesian_growth.py`
- `apps/seedtest_api/docs/BAYESIAN_GROWTH_GUIDE.md`

**변경 사항**:
1. Priors 설정 이유 및 소표본/잡음 안정화 설명 추가
2. 각 prior 분포의 역할 설명

---

## ✅ 점검 완료 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| IRT 2PL 기본 | ✅ | 기본값 `model="2PL"` |
| IRT 앵커 동등화 | ✅ | anchors 로드 및 linking constants 저장 |
| IRT 과목/토픽별 bank | ⚠️ | 필터링 옵션 추가 필요 |
| GLMM formula | ✅ | 정확히 구현됨 |
| 베이지안 priors | ✅ | 설정됨 (설명 보강 필요) |
| 베이지안 P/σ | ✅ | weekly_kpi 업데이트 |
| Prophet I_t 이력 | ✅ | weekly_kpi에서 추출 |
| Prophet 추세/이상 | ✅ | forecast + anomaly detection |
| Survival 14일 이벤트 | ✅ | event_threshold_days=14 |
| Survival 공변량 | ✅ | A_t, E_t, R_t, mean_gap, sessions |
| 클러스터링 세그먼트 | ⚠️ | 의미 있는 라벨 생성 필요 |

---

**다음 단계**: 미적용된 3개 항목 추가 작업 진행할까요?

