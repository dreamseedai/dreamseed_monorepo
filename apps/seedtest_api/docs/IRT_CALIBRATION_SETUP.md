# IRT 주간 캘리브레이션 설정 가이드

**작성일**: 2025-11-01

## 개요

IRT (Item Response Theory) 주간 캘리브레이션은 문항 파라미터(a, b, c)와 사용자 능력(θ)을 추정하여 `mirt_item_params`, `mirt_ability`, `mirt_fit_meta` 테이블에 저장합니다.

## 구현 현황

### ✅ 완료된 작업

1. **`mirt_calibrate.py` 개선**
   - `attempt` VIEW 우선 사용 (표준화된 스키마)
   - Fallback: `responses` 테이블 → `exam_results` JSON
   - 관측 추출 로직 강화 (최대 50,000개)

2. **K8s CronJob 매니페스트 생성**
   - 파일: `portal_front/ops/k8s/cron/mirt-calibrate.yaml`
   - 스케줄: 매일 03:00 UTC
   - 리소스: 메모리 1Gi (요청) / 2Gi (제한), CPU 500m (요청) / 2000m (제한)

## 데이터 흐름

### 관측 추출 우선순위

1. **`attempt` VIEW** (우선 사용)
   ```sql
   SELECT 
       student_id::text AS user_id,
       item_id::text AS item_id,
       correct AS is_correct,
       completed_at AS responded_at
   FROM attempt
   WHERE completed_at >= :since
   ```

2. **`responses` 테이블** (Fallback 1)
   ```sql
   SELECT user_id, item_id, is_correct, responded_at
   FROM responses
   WHERE responded_at >= :since
   ```

3. **`exam_results` JSON** (Fallback 2)
   - `result_json->'questions'` 배열을 unnest하여 추출

### IRT 파라미터 저장

**`mirt_item_params`**: 문항별 파라미터 (a, b, c)
```sql
INSERT INTO mirt_item_params (item_id, model, params, version, fitted_at)
VALUES (:item_id, :model, :params::jsonb, :version, NOW())
ON CONFLICT (item_id) DO UPDATE SET ...
```

**`mirt_ability`**: 사용자별 능력 추정치 (θ, se)
```sql
INSERT INTO mirt_ability (user_id, theta, se, model, version, fitted_at)
VALUES (:user_id, :theta, :se, :model, :version, NOW())
ON CONFLICT (user_id, version) DO UPDATE SET ...
```

**`mirt_fit_meta`**: 캘리브레이션 메타데이터
```sql
INSERT INTO mirt_fit_meta (run_id, model_spec, metrics, fitted_at)
VALUES (:run_id, :model_spec::jsonb, :metrics::jsonb, NOW())
ON CONFLICT (run_id) DO UPDATE SET ...
```

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `IRT_CALIB_LOOKBACK_DAYS` | 관측 데이터 조회 기간 (일) | `30` |
| `IRT_MODEL` | IRT 모델 타입 | `2PL` |
| `R_IRT_BASE_URL` | R IRT Plumber 서비스 URL | (필수) |
| `R_IRT_INTERNAL_TOKEN` | R IRT 서비스 인증 토큰 | (필수) |
| `R_IRT_TIMEOUT_SECS` | HTTP 요청 타임아웃 (초) | `300` (5분) |
| `DATABASE_URL` | PostgreSQL 연결 URL | (필수) |

## 사용 방법

### 로컬 실행

```bash
# 환경 변수 설정
export DATABASE_URL="postgresql://..."
export R_IRT_BASE_URL="http://r-irt-plumber:8000"
export R_IRT_INTERNAL_TOKEN="your-token"
export IRT_CALIB_LOOKBACK_DAYS=30
export IRT_MODEL="2PL"

# 실행
python -m apps.seedtest_api.jobs.mirt_calibrate
```

### K8s 배포

#### 1. Secret 생성 (R IRT 자격증명)

```bash
kubectl -n seedtest create secret generic seedtest-irt-credentials \
  --from-literal=R_IRT_BASE_URL='http://r-irt-plumber:8000' \
  --from-literal=R_IRT_INTERNAL_TOKEN='your-token'
```

#### 2. CronJob 적용

```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml
```

#### 3. 상태 확인

```bash
# CronJob 확인
kubectl -n seedtest get cronjob mirt-calibrate

# Job 실행 이력
kubectl -n seedtest get jobs | grep mirt-calibrate

# 로그 확인
kubectl -n seedtest logs job/<job-name>
```

#### 4. 수동 실행 (테스트)

```bash
kubectl -n seedtest create job --from=cronjob/mirt-calibrate manual-run-$(date +%s)
```

## 검증

### 1. 관측 데이터 확인

```sql
-- attempt VIEW에서 최근 30일 데이터 확인
SELECT COUNT(*) FROM attempt 
WHERE completed_at >= NOW() - INTERVAL '30 days';

-- 중복/누락 확인
SELECT 
    COUNT(DISTINCT student_id) AS unique_students,
    COUNT(DISTINCT item_id) AS unique_items,
    COUNT(*) AS total_attempts
FROM attempt
WHERE completed_at >= NOW() - INTERVAL '30 days';
```

### 2. IRT 파라미터 확인

```sql
-- 문항 파라미터 확인
SELECT item_id, model, params, fitted_at
FROM mirt_item_params
ORDER BY fitted_at DESC
LIMIT 10;

-- 사용자 능력 추정치 확인
SELECT user_id, theta, se, model, fitted_at
FROM mirt_ability
ORDER BY fitted_at DESC
LIMIT 10;

-- 캘리브레이션 메타데이터 확인
SELECT run_id, model_spec, metrics, fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 5;
```

## 스케줄링

### 현재 스케줄

- **매일 03:00 UTC** (한국 시간 12:00)
- `compute-daily-kpis` (02:10 UTC) 이후 실행
- `aggregate-features-daily` (01:15 UTC) 이후 실행

### 권장 실행 순서

1. `aggregate-features-daily` (01:15 UTC)
2. `compute-daily-kpis` (02:10 UTC)
3. `mirt-calibrate` (03:00 UTC)

이 순서로 실행하면 `features_topic_daily`에 최신 IRT theta 추정치가 반영됩니다.

## 문제 해결

### 1. 관측 데이터가 없음

```bash
# attempt VIEW 존재 확인
psql $DATABASE_URL -c "\d attempt"

# 데이터 확인
psql $DATABASE_URL -c "SELECT COUNT(*) FROM attempt WHERE completed_at >= NOW() - INTERVAL '30 days';"
```

### 2. R IRT 서비스 연결 실패

```bash
# R IRT Plumber 서비스 상태 확인
kubectl -n seedtest get svc | grep r-irt-plumber

# Pod 로그 확인
kubectl -n seedtest logs -l app=r-irt-plumber
```

### 3. 타임아웃 발생

- `R_IRT_TIMEOUT_SECS` 값 증가 (예: `600` = 10분)
- 관측 데이터 양 감소 (`IRT_CALIB_LOOKBACK_DAYS` 줄이기)
- 리소스 제한 증가 (K8s 매니페스트 수정)

## 참고 문서

- IRT 표준화: `apps/seedtest_api/docs/IRT_STANDARDIZATION.md`
- 파이프라인 현황: `apps/seedtest_api/docs/PIPELINE_STATUS_AND_NEXT_STEPS.md`

