# IRT 캘리브레이션 운영 체크리스트

**작성일**: 2025-11-02  
**상태**: ✅ 운영 준비 완료

---

## ✅ 완료된 구현

### 1. Cron 매니페스트 (야간 IRT 캘리브레이션)

**파일**: `portal_front/ops/k8s/cron/calibrate-irt.yaml`

**설정**:
- 스케줄: 매주 일요일 03:10 UTC (`"10 3 * * 0"`)
  - 일일 실행으로 변경: `"0 3 * * *"` (매일 03:00 UTC)
- 이미지: `asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest`
- 명령어: `python3 -m apps.seedtest_api.jobs.mirt_calibrate`

**환경 변수**:
- `MIRT_LOOKBACK_DAYS=30` (기본값: 30일)
- `MIRT_MODEL=2PL` (기본값: 2PL)
- `MIRT_MAX_OBS=500000` (기본값: 0 = 무제한)
- `R_IRT_BASE_URL=http://r-irt-plumber.seedtest.svc.cluster.local:80`
- `R_IRT_TIMEOUT_SECS=300` (5분)
- `R_IRT_INTERNAL_TOKEN` (Secret에서, 선택)
- `DATABASE_URL` (Secret에서, 필수)
- `MIRT_MAX_RETRIES=3` (재시도 횟수, 기본값: 3)
- `MIRT_RETRY_DELAY_SECS=5.0` (재시도 지연 시간, 기본값: 5초)

**배포**:
```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml
```

**수동 실행**:
```bash
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  calibrate-irt-test-$(date +%s)
```

---

### 2. r-irt-plumber 페이로드 확장 (anchors/model)

**파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`

**구현**:
- ✅ `_load_anchors()`: `question.meta->'tags'`에 'anchor' 포함된 아이템 로드
- ✅ 페이로드에 `anchors` 필드 추가
- ✅ 기존 환경 변수로 모델 선택 (`MIRT_MODEL=2PL` 기본)

**페이로드 구조**:
```json
{
  "observations": [
    {"user_id": "...", "item_id": "...", "is_correct": true, "responded_at": "..."}
  ],
  "model": "2PL",
  "anchors": [
    {
      "item_id": "...",
      "params": {"a": 1.0, "b": 0.0, "c": 0.2},
      "fixed": true
    }
  ]
}
```

**응답 구조**:
```json
{
  "item_params": [...],
  "abilities": [...],
  "fit_meta": {
    "linking_constants": {"A": 1.0, "B": 0.0}
  }
}
```

**주의**: r-irt-plumber 측 `/irt/calibrate`에서 `anchors` 필드 해석 및 linking constants 반환 로직이 필요합니다.

---

### 3. 리포트 템플릿에 θ/IRT 세부 섹션

**파일**: `reports/quarto/weekly_report.qmd`

**포함 내용**:
- ✅ Ability(θ) 추세 플롯
- ✅ Linking/Equating Constants 섹션
- ✅ KPI 표/레이다 차트
- ✅ Topic/일별 성과 차트
- ✅ 추천 문구 섹션

**리포트 생성 파이프라인**:
- ✅ `tools/quarto-runner/Dockerfile`: 런너 이미지
- ✅ `apps/seedtest_api/jobs/generate_weekly_report.py`: KPI 로드 → Quarto render → S3 업로드 → report_artifact upsert
- ✅ `portal_front/ops/k8s/cron/generate-weekly-report.yaml`: 월요일 04:00 UTC

---

## 🔧 운영 체크리스트

### 1. r-irt-plumber에서 anchors 파라미터 처리 확인

**확인 항목**:
- [ ] `/irt/calibrate` 엔드포인트가 `anchors` 필드를 받아들이는지
- [ ] Linking constants를 계산하여 반환하는지
- [ ] 응답에 `fit_meta.linking_constants`가 포함되는지

**테스트**:
```bash
# 앵커 문항 설정 확인
kubectl -n seedtest exec deploy/seedtest-api -c api -- python3 -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text(\"\"\"
        SELECT COUNT(*) 
        FROM question 
        WHERE meta->'tags' @> '[\"anchor\"]'::jsonb
    \"\"\"))
    print(f'Anchor items: {result.fetchone()[0]}')
"

# R IRT 서비스 health check
kubectl -n seedtest exec deploy/seedtest-api -c api -- \
  curl -f http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz
```

---

### 2. Secrets 마운트 확인

#### DATABASE_URL

**CronJob 설정**:
```yaml
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: seedtest-db-credentials
        key: DATABASE_URL
        optional: false
```

**확인**:
```bash
kubectl -n seedtest get secret seedtest-db-credentials
kubectl -n seedtest get cronjob calibrate-irt-weekly -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].env[?(@.name=="DATABASE_URL")]}'
```

#### R_IRT_INTERNAL_TOKEN (선택)

**CronJob 설정**:
```yaml
env:
  - name: R_IRT_INTERNAL_TOKEN
    valueFrom:
      secretKeyRef:
        name: r-irt-credentials
        key: token
        optional: true
```

**확인**:
```bash
kubectl -n seedtest get secret r-irt-credentials
kubectl -n seedtest get cronjob calibrate-irt-weekly -o jsonpath='{.spec.jobTemplate.spec.template.spec.containers[0].env[?(@.name=="R_IRT_INTERNAL_TOKEN")]}'
```

**Secret 생성 (필요 시)**:
```bash
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='<your-token>' \
  --dry-run=client -o yaml | kubectl apply -f -
```

---

### 3. 모니터링

#### Cron 실행 완료 로그

```bash
# 최근 실행된 Job 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | grep calibrate-irt | tail -5

# CronJob 상태
kubectl -n seedtest get cronjob calibrate-irt-weekly

# 로그 확인
kubectl -n seedtest logs job/<job-name> -c calibrate-irt --tail=100

# 실시간 로그 팔로우
kubectl -n seedtest logs job/<job-name> -c calibrate-irt -f
```

#### mirt_item_params/mirt_ability/mirt_fit_meta upsert 수치 확인

```sql
-- 최근 캘리브레이션 통계
SELECT 
    DATE_TRUNC('day', fitted_at) AS calib_date,
    COUNT(DISTINCT item_id) AS item_count,
    COUNT(DISTINCT user_id) AS user_count,
    AVG((params->>'b')::float) AS avg_difficulty,
    MAX(fitted_at) AS latest_fit
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('day', fitted_at)
ORDER BY calib_date DESC;

-- Ability 통계
SELECT 
    DATE_TRUNC('day', fitted_at) AS calib_date,
    COUNT(DISTINCT user_id) AS user_count,
    AVG(theta) AS avg_theta,
    AVG(se) AS avg_se,
    MAX(fitted_at) AS latest_fit
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('day', fitted_at)
ORDER BY calib_date DESC;

-- Fit meta 확인 (linking constants 포함)
SELECT 
    run_id,
    model_spec->'model' AS model,
    model_spec->'n_items' AS n_items,
    model_spec->'n_observations' AS n_observations,
    (model_spec->'linking_constants') IS NOT NULL AS has_linking,
    model_spec->'linking_constants' AS linking_constants,
    metrics->>'aic' AS aic,
    fitted_at
FROM mirt_fit_meta
WHERE fitted_at >= NOW() - INTERVAL '7 days'
ORDER BY fitted_at DESC
LIMIT 5;
```

#### report_artifact에 최신 리포트 URL 저장 여부 확인

```sql
-- 최근 리포트 생성 확인
SELECT 
    user_id,
    week_start,
    format,
    report_url,
    generated_at
FROM report_artifacts
WHERE generated_at >= NOW() - INTERVAL '7 days'
ORDER BY generated_at DESC
LIMIT 20;

-- 사용자별 리포트 수
SELECT 
    user_id,
    COUNT(*) AS report_count,
    MAX(generated_at) AS latest_report
FROM report_artifacts
GROUP BY user_id
ORDER BY latest_report DESC
LIMIT 10;
```

---

## 🚀 권장 후속 작업 상태

### ✅ 1. I_t를 θ-델타 기반으로 전환

**상태**: ✅ **구현 완료**

**파일**: `apps/seedtest_api/services/metrics.py` - `compute_improvement_index`

**활성화 방법**:
```bash
# 환경 변수 설정
export METRICS_USE_IRT_THETA=true
```

**동작**:
- `METRICS_USE_IRT_THETA=true` 설정 시 θ 기반 계산 사용
- θ 값이 없거나 부족한 경우 정답률 기반으로 폴백
- 폴백 로직: 정확도 델타 계산

**테스트**:
```sql
-- 사용자의 최근 θ 값 확인
SELECT user_id, theta, se, fitted_at
FROM mirt_ability
WHERE user_id = 'test-user-123'
ORDER BY fitted_at DESC
LIMIT 5;
```

---

### ✅ 2. aggregate_features_daily.py에 theta_mean/theta_sd 채우기

**상태**: ✅ **구현 완료**

**파일**: `apps/seedtest_api/jobs/aggregate_features_daily.py` - `_load_theta_if_needed`

**활성화 방법**:
```bash
# 환경 변수 설정
export AGG_INCLUDE_THETA=true
```

**동작**:
- `student_topic_theta` 우선 사용 (토픽별 θ)
- 없으면 `mirt_ability` 사용 (전체 능력)
- `features_topic_daily.theta_mean`, `theta_sd` 컬럼에 저장

**확인**:
```sql
-- theta_mean/theta_sd가 채워진 피처 확인
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

---

### ✅ 3. 백오프/재시도 추가

**상태**: ✅ **구현 완료**

**파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`

**구현**:
- `MIRT_MAX_RETRIES=3` (기본값: 3회)
- `MIRT_RETRY_DELAY_SECS=5.0` (기본값: 5초)
- 지수 백오프: `wait_time = retry_delay * (attempt + 1)`

**동작**:
- R IRT 서비스 호출 실패 시 자동 재시도
- 각 시도마다 대기 시간 증가 (5초, 10초, 15초)
- 최대 재시도 횟수 초과 시 예외 발생

**환경 변수**:
```yaml
env:
  - name: MIRT_MAX_RETRIES
    value: "3"
  - name: MIRT_RETRY_DELAY_SECS
    value: "5.0"
```

---

### ⏭️ 4. r-irt-plumber 측 anchors 처리 및 linking_constants 반환

**상태**: ⏭️ **R 서비스 측 구현 필요**

**필요 작업**:
1. `/irt/calibrate` 엔드포인트에서 `anchors` 파라미터 처리
2. Linking constants 계산
3. 응답에 `fit_meta.linking_constants` 포함

**Python 측 준비 완료**:
- ✅ `mirt_calibrate.py`에서 anchors 로드 및 전달
- ✅ `mirt_fit_meta.model_spec.linking_constants` 저장
- ✅ `weekly_report.qmd`에서 Linking Constants 표시

---

## 📊 모니터링 대시보드 쿼리

### 일일 캘리브레이션 통계

```sql
-- 일일 캘리브레이션 요약
SELECT 
    DATE_TRUNC('day', fitted_at) AS calib_date,
    COUNT(DISTINCT item_id) AS item_count,
    COUNT(DISTINCT user_id) AS user_count,
    AVG((params->>'b')::float) AS avg_difficulty,
    STDDEV((params->>'b')::float) AS sd_difficulty,
    MAX(fitted_at) AS latest_fit
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', fitted_at)
ORDER BY calib_date DESC;
```

### 앵커 아이템 사용 현황

```sql
-- 앵커 아이템 수 및 사용 현황
SELECT 
    COUNT(DISTINCT q.id) AS anchor_item_count,
    COUNT(DISTINCT mip.item_id) AS anchors_with_params,
    COUNT(DISTINCT CASE 
        WHEN mip.fitted_at >= NOW() - INTERVAL '30 days' 
        THEN mip.item_id 
    END) AS recent_anchors_used
FROM question q
LEFT JOIN mirt_item_params mip ON q.id::text = mip.item_id
WHERE q.meta->'tags' @> '["anchor"]'::jsonb;
```

### Linking Constants 현황

```sql
-- 최근 캘리브레이션에서 linking constants 포함 여부
SELECT 
    DATE_TRUNC('day', fitted_at) AS calib_date,
    COUNT(*) AS total_runs,
    COUNT(CASE WHEN model_spec ? 'linking_constants' THEN 1 END) AS runs_with_linking,
    MAX(CASE 
        WHEN model_spec ? 'linking_constants' 
        THEN model_spec->'linking_constants'::text 
    END) AS sample_linking_constants
FROM mirt_fit_meta
WHERE fitted_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', fitted_at)
ORDER BY calib_date DESC;
```

---

## 🔍 문제 해결

### 일반적인 문제

1. **"R IRT service call failed"**
   - 원인: r-irt-plumber 서비스 미가동 또는 네트워크 문제
   - 해결: 서비스 상태 확인, 재시도 로직 확인

2. **"No anchors found"**
   - 원인: `question.meta.tags`에 "anchor" 태그 없음
   - 해결: `tag_anchor_items.py` 실행하여 앵커 아이템 태깅

3. **"Linking constants not returned"**
   - 원인: r-irt-plumber 측 anchors 처리 로직 미구현
   - 해결: R 서비스 측 `/irt/calibrate` 엔드포인트 확장 필요

4. **"Theta not found in features_topic_daily"**
   - 원인: `AGG_INCLUDE_THETA=true` 미설정 또는 θ 값 없음
   - 해결: 환경 변수 설정 및 IRT 캘리브레이션 실행

---

## ✅ 최종 확인 사항

- [ ] CronJob 배포 완료
- [ ] Secrets 설정 확인
- [ ] r-irt-plumber 서비스 가동 확인
- [ ] 앵커 아이템 태깅 확인
- [ ] 첫 캘리브레이션 실행 및 검증
- [ ] Linking constants 저장 확인
- [ ] 리포트 생성 및 θ/IRT 섹션 확인

**모든 준비 완료!** 🎉

