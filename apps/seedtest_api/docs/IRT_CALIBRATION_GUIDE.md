# IRT Calibration 완전 가이드

**작성일**: 2025-11-01  
**상태**: Production Ready

---

## ✅ 구현 완료

### 파일
- `apps/seedtest_api/jobs/mirt_calibrate.py` (361 lines)
- `portal_front/ops/k8s/cron/mirt-calibrate.yaml`

### 기능
1. **관측 데이터 추출**
   - attempt VIEW (우선순위 1)
   - responses 테이블 (폴백 1)
   - exam_results JSON (폴백 2)

2. **앵커 문항 로드**
   - `question.meta.irt` (a, b, c 시드 값)
   - `question.meta.tags` 중 "anchor" 태그

3. **R IRT Plumber 호출**
   - `POST /irt/calibrate`
   - Payload: observations, model, anchors
   - Response: item_params, abilities, fit_meta

4. **데이터베이스 업데이트**
   - `mirt_item_params` - 문항 파라미터 (a, b, c)
   - `mirt_ability` - 사용자 능력 (θ, se)
   - `mirt_fit_meta` - 적합 메타데이터 (linking constants)

5. **선택 기능**
   - `question.meta.irt` 업데이트 (IRT_UPDATE_QUESTION_META=true)
   - Dry-run 모드 (DRY_RUN=true)
   - 관측 수 제한 (MIRT_MAX_OBS)

---

## 🔧 환경 변수

### 필수
```bash
# R IRT 서비스
R_IRT_BASE_URL=http://r-irt-plumber.seedtest.svc.cluster.local:80

# 데이터베이스
DATABASE_URL=postgresql://user:pass@localhost:5432/seedtest
```

### 선택
```bash
# Calibration 설정
MIRT_LOOKBACK_DAYS=60          # 관측 기간 (기본: 30일)
MIRT_MODEL=2PL                 # IRT 모델 (2PL, 3PL, Rasch)
MIRT_MAX_OBS=500000            # 최대 관측 수 (0=무제한)

# R IRT 서비스 설정
R_IRT_INTERNAL_TOKEN=<token>   # 내부 인증 토큰 (선택)
R_IRT_TIMEOUT_SECS=300         # 타임아웃 (기본: 60초)

# 동작 모드
DRY_RUN=false                  # true 시 R 호출 스킵
IRT_UPDATE_QUESTION_META=false # true 시 question.meta.irt 업데이트
```

---

## 🚀 실행 방법

### 로컬 테스트

```bash
# 환경 변수 설정
export DATABASE_URL='postgresql://...'
export R_IRT_BASE_URL='http://localhost:8080'
export MIRT_LOOKBACK_DAYS=30
export MIRT_MODEL=2PL
export DRY_RUN=true

# 실행
python -m apps.seedtest_api.jobs.mirt_calibrate
```

### Docker 테스트

```bash
docker run --rm \
  -e DATABASE_URL='postgresql://...' \
  -e R_IRT_BASE_URL='http://r-irt-plumber:80' \
  -e MIRT_LOOKBACK_DAYS=30 \
  -e MIRT_MODEL=2PL \
  gcr.io/univprepai/seedtest-api:latest \
  python -m apps.seedtest_api.jobs.mirt_calibrate
```

### Kubernetes CronJob

```bash
# 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml

# 수동 실행
kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/mirt-calibrate-test-<timestamp>
```

---

## 📊 R IRT Plumber API 스펙

### Request: POST /irt/calibrate

```json
{
  "observations": [
    {
      "user_id": "user-123",
      "item_id": "item-456",
      "is_correct": true,
      "responded_at": "2025-11-01T12:34:56Z"
    }
  ],
  "model": "2PL",
  "anchors": [
    {
      "item_id": "item-anchor-1",
      "params": {"a": 1.2, "b": 0.5},
      "fixed": true
    }
  ]
}
```

### Response

```json
{
  "item_params": [
    {
      "item_id": "item-456",
      "model": "2PL",
      "params": {
        "a": 1.15,
        "b": 0.32,
        "c": null
      },
      "version": "v1"
    }
  ],
  "abilities": [
    {
      "user_id": "user-123",
      "theta": 0.85,
      "se": 0.12,
      "model": "2PL",
      "version": "v1"
    }
  ],
  "fit_meta": {
    "run_id": "fit-2025-11-01T12:34:56Z",
    "model_spec": {
      "model": "2PL",
      "n_items": 150,
      "n_users": 500,
      "linking_constants": {
        "slope": 1.02,
        "intercept": 0.05
      }
    },
    "metrics": {
      "aic": 12345.67,
      "bic": 12456.78,
      "loglik": -6172.83
    }
  }
}
```

---

## 🔍 검증 체크리스트

### 1. R IRT 서비스 확인

```bash
# 서비스 상태
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# Health check
curl http://r-irt-plumber.seedtest.svc.cluster.local:80/health

# 예상 응답
{"status": "ok", "version": "1.0.0"}
```

### 2. Dry-run 테스트

```bash
# DRY_RUN=true로 실행
kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-dryrun-$(date +%s)

# 로그 확인 (R 호출 없이 데이터 로드만 확인)
kubectl -n seedtest logs job/mirt-calibrate-dryrun-<timestamp>

# 예상 출력
# [INFO] Loaded 12345 observations from attempt VIEW
# [INFO] Loaded 50 anchors/seeds from question.meta
# [INFO] Total observations: 12345
# [INFO] Model: 2PL, Anchors: 50
# [DRY_RUN] Skipping R IRT service call and DB updates
# [DRY_RUN] Would calibrate 12345 observations with 50 anchors
```

### 3. 실제 Calibration 실행

```bash
# DRY_RUN=false로 실행
kubectl -n seedtest set env cronjob/mirt-calibrate DRY_RUN=false

kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-prod-$(date +%s)

# 로그 확인 (5-10분 소요)
kubectl -n seedtest logs -f job/mirt-calibrate-prod-<timestamp>

# 예상 출력
# [INFO] Loaded 12345 observations from attempt VIEW
# [INFO] Loaded 50 anchors/seeds from question.meta
# [INFO] Total observations: 12345
# [INFO] Model: 2PL, Anchors: 50
# [INFO] Linking constants received: ['slope', 'intercept']
# Calibration upsert completed: 150 items, 500 abilities
# Linking constants stored in fit_meta.model_spec.linking_constants
```

### 4. 데이터베이스 검증

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
LIMIT 20;

-- 예상 결과
-- item_id | model | discrimination | difficulty | guessing | version | fitted_at
-- --------|-------|----------------|------------|----------|---------|----------
-- item-1  | 2PL   | 1.15           | 0.32       | null     | v1      | 2025-11-01 12:34:56
-- item-2  | 2PL   | 0.98           | -0.15      | null     | v1      | 2025-11-01 12:34:56

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
LIMIT 20;

-- 예상 결과
-- user_id  | theta | se   | model | version | fitted_at
-- ---------|-------|------|-------|---------|----------
-- user-123 | 0.85  | 0.12 | 2PL   | v1      | 2025-11-01 12:34:56
-- user-456 | -0.32 | 0.15 | 2PL   | v1      | 2025-11-01 12:34:56

-- mirt_fit_meta 확인
SELECT 
    run_id,
    model_spec->>'model' AS model,
    model_spec->>'n_items' AS n_items,
    model_spec->>'n_users' AS n_users,
    model_spec->'linking_constants' AS linking_constants,
    metrics->>'aic' AS aic,
    fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 5;

-- 예상 결과
-- run_id                      | model | n_items | n_users | linking_constants          | aic      | fitted_at
-- ----------------------------|-------|---------|---------|----------------------------|----------|----------
-- fit-2025-11-01T12:34:56Z    | 2PL   | 150     | 500     | {"slope":1.02,"intercept":0.05} | 12345.67 | 2025-11-01 12:34:56

-- 통계 확인
SELECT 
    COUNT(*) AS total_items,
    AVG((params->>'a')::float) AS avg_discrimination,
    AVG((params->>'b')::float) AS avg_difficulty
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 day';

SELECT 
    COUNT(*) AS total_users,
    AVG(theta) AS avg_theta,
    STDDEV(theta) AS sd_theta
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '1 day';
```

### 5. question.meta.irt 업데이트 확인 (선택)

```sql
-- IRT_UPDATE_QUESTION_META=true인 경우
SELECT 
    id,
    meta->'irt' AS irt_params
FROM question
WHERE meta ? 'irt'
  AND updated_at >= NOW() - INTERVAL '1 day'
LIMIT 10;

-- 예상 결과
-- id  | irt_params
-- ----|------------
-- 123 | {"a": 1.15, "b": 0.32, "model": "2PL", "version": "v1"}
-- 456 | {"a": 0.98, "b": -0.15, "model": "2PL", "version": "v1"}
```

---

## 🔄 온라인 θ 업데이트와의 정합성

### Version 구분

- **Calibration (배치)**: `version = "v1"` 또는 `"YYYYMMDD"`
- **Online Update (실시간)**: `version = "online"`

### 우선순위

```python
# services/irt_update_service.py
def load_item_params(item_ids):
    # 1. 최신 calibration 버전 사용
    params = load_from_mirt_item_params(item_ids, version="v1")
    
    # 2. 없으면 question.meta.irt 사용
    if not params:
        params = load_from_question_meta(item_ids)
    
    return params
```

### 동기화 전략

```sql
-- Calibration 후 online 버전 초기화 (선택)
UPDATE mirt_ability
SET version = 'v1',
    fitted_at = NOW()
WHERE version = 'online'
  AND user_id IN (
    SELECT user_id FROM mirt_ability WHERE version = 'v1'
  );
```

---

## 📈 앵커 문항 동등화 (Equating)

### 앵커 문항 태깅

```sql
-- 앵커 문항 지정
UPDATE question
SET meta = jsonb_set(
    COALESCE(meta, '{}'::jsonb),
    '{tags}',
    '["anchor"]'::jsonb,
    true
)
WHERE id IN (123, 456, 789);  -- 안정적인 문항 ID

-- 앵커 문항 확인
SELECT id, meta->'tags' AS tags
FROM question
WHERE meta->'tags' @> '["anchor"]'::jsonb;
```

### 링킹 상수 활용

```sql
-- 최근 링킹 상수 조회
SELECT 
    run_id,
    model_spec->'linking_constants'->>'slope' AS slope,
    model_spec->'linking_constants'->>'intercept' AS intercept,
    fitted_at
FROM mirt_fit_meta
WHERE model_spec ? 'linking_constants'
ORDER BY fitted_at DESC
LIMIT 1;

-- 예상 결과
-- run_id                      | slope | intercept | fitted_at
-- ----------------------------|-------|-----------|----------
-- fit-2025-11-01T12:34:56Z    | 1.02  | 0.05      | 2025-11-01 12:34:56
```

### 동등화 적용

```python
# 새 문항 파라미터를 기존 척도로 변환
def equate_params(new_params, linking_constants):
    slope = linking_constants.get("slope", 1.0)
    intercept = linking_constants.get("intercept", 0.0)
    
    equated_params = {}
    for item_id, params in new_params.items():
        equated_params[item_id] = {
            "a": params["a"] * slope,
            "b": params["b"] * slope + intercept,
            "c": params.get("c"),  # guessing은 변환 안 함
        }
    
    return equated_params
```

---

## 🎯 다음 단계

### 1. I_t (개선지수) θ 기반 전환

```python
# services/metrics.py
def compute_improvement_index(user_id, week_start):
    # θ 기반 계산
    theta_prev = load_theta(user_id, week_start - timedelta(weeks=1))
    theta_recent = load_theta(user_id, week_start)
    
    if theta_prev and theta_recent:
        I_t = (theta_recent - theta_prev) / (1 + abs(theta_prev))
    else:
        # 폴백: 정답률 기반
        I_t = compute_accuracy_based_improvement(user_id, week_start)
    
    return I_t
```

### 2. features_topic_daily에 θ 백필

```python
# jobs/aggregate_features_daily.py
def aggregate_with_theta(user_id, topic_id, date):
    # 기존 피처
    features = compute_basic_features(user_id, topic_id, date)
    
    # θ 추가 (AGG_INCLUDE_THETA=true)
    if os.getenv("AGG_INCLUDE_THETA", "false").lower() == "true":
        theta_stats = compute_topic_theta(user_id, topic_id, date)
        features.update({
            "theta_mean": theta_stats.get("mean"),
            "theta_sd": theta_stats.get("sd"),
        })
    
    return features
```

### 3. Quarto 리포트에 θ 섹션 추가

```r
# reports/quarto/weekly_report.qmd

## IRT Ability (θ) Trend

```{r theta-trend}
theta_data <- load_theta_history(user_id, weeks = 12)

ggplot(theta_data, aes(x = week_start, y = theta)) +
  geom_line(color = "blue", size = 1) +
  geom_ribbon(aes(ymin = theta - se, ymax = theta + se), alpha = 0.2) +
  labs(
    title = "Ability (θ) Trend",
    x = "Week",
    y = "θ (ability)"
  ) +
  theme_minimal()
```
```

---

## 🔧 문제 해결

### R IRT 서비스 연결 실패

```bash
# 서비스 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get endpoints r-irt-plumber

# Pod 로그
kubectl -n seedtest logs -l app=r-irt-plumber --tail=100

# 연결 테스트
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/health
```

### 관측 데이터 없음

```bash
# attempt VIEW 확인
kubectl -n seedtest exec -it <pod-name> -- psql $DATABASE_URL -c \
  "SELECT COUNT(*) FROM attempt WHERE completed_at >= NOW() - INTERVAL '30 days';"

# 폴백 테이블 확인
kubectl -n seedtest exec -it <pod-name> -- psql $DATABASE_URL -c \
  "SELECT COUNT(*) FROM responses WHERE responded_at >= NOW() - INTERVAL '30 days';"
```

### Calibration 실패

```bash
# Job 로그 확인
kubectl -n seedtest logs job/<job-name> | grep -i "error\|exception\|failed"

# R IRT 서비스 로그
kubectl -n seedtest logs -l app=r-irt-plumber --tail=100 | grep -i "error"

# 재시도
kubectl -n seedtest delete job <job-name>
kubectl -n seedtest create job --from=cronjob/mirt-calibrate <job-name>-retry
```

---

## 📚 참고 문서

- `/apps/seedtest_api/docs/ADVANCED_ANALYTICS_ROADMAP.md` - 전체 로드맵
- `/apps/seedtest_api/docs/IRT_ONLINE_UPDATE_GUIDE.md` - θ 온라인 업데이트
- `/portal_front/ops/k8s/cron/PRODUCTION_DEPLOYMENT_GUIDE.md` - 운영 배포

---

**최종 업데이트**: 2025-11-01  
**작성자**: Cascade AI  
**상태**: Production Ready - 즉시 배포 가능
