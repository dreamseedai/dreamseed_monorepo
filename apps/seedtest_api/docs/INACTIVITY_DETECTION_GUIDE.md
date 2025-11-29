# 비활성 사용자 감지 및 예측 이벤트 트리거 가이드

**작성일**: 2025-11-01

## 개요

7일 이상 비활성 사용자를 감지하고 즉시 P(goal|state) 및 S(churn) 재계산을 트리거하는 파이프라인입니다.

## 구현 현황

### ✅ 완료된 작업

1. **비활성 사용자 감지 Job**
   - 파일: `apps/seedtest_api/jobs/detect_inactivity.py`
   - 기능: 다중 소스에서 마지막 접속일 확인 → 7일 미접속 사용자 식별
   - P/S 즉시 재계산 및 `weekly_kpi` 업데이트

2. **K8s CronJob**
   - 파일: `portal_front/ops/k8s/cron/detect-inactivity.yaml`
   - 스케줄: 매일 05:00 UTC (일일 KPI 계산 이후)

## 감지 소스

다음 소스에서 마지막 활동일을 확인합니다:

1. **`exam_results.updated_at` (또는 `created_at`)**
   - 가장 최근 시험 결과 제출 시각

2. **`features_topic_daily.last_seen_at`**
   - 토픽별 피처 계산 시 업데이트되는 타임스탬프

3. **`attempt.completed_at`**
   - attempt VIEW의 완료 시각

4. **`session.ended_at`** (선택적)
   - 세션 테이블의 종료 시각

## 데이터 흐름

```
비활성 사용자 감지 트리거 (매일 05:00 UTC)
  ↓
다중 소스에서 마지막 접속일 확인
  - exam_results
  - features_topic_daily
  - attempt VIEW
  - session (선택적)
  ↓
7일 미접속 사용자 식별
  ↓
P(goal|state) 및 S(churn) 즉시 재계산
  ↓
weekly_kpi 테이블 업데이트
  - 기존 I_t, E_t, R_t, A_t 유지
  - P, S만 업데이트
```

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `INACTIVITY_THRESHOLD_DAYS` | 비활성 판단 기준 (일) | `7` |
| `KPI_LOOKBACK_DAYS` | 사용자 활동 조회 기간 (일) | `30` |
| `METRICS_DEFAULT_TARGET` | 목표값 기본값 | `0.0` |
| `METRICS_USE_BAYESIAN` | 베이지안 사용 여부 | `false` |
| `METRICS_CHURN_HORIZON_DAYS` | 이탈 위험 기준 기간 (일) | `14` |
| `DATABASE_URL` | PostgreSQL 연결 URL | (필수) |

## 사용 방법

### 로컬 실행

```bash
# 환경 변수 설정
export DATABASE_URL="postgresql://..."
export INACTIVITY_THRESHOLD_DAYS=7

# 기본 실행 (7일 미접속 감지)
python -m apps.seedtest_api.jobs.detect_inactivity

# 특정 임계값 지정
python -m apps.seedtest_api.jobs.detect_inactivity --threshold 14

# Dry-run (DB 저장 생략)
python -m apps.seedtest_api.jobs.detect_inactivity --dry-run
```

### K8s 배포

#### 1. CronJob 적용

```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/detect-inactivity.yaml
```

#### 2. 상태 확인

```bash
# CronJob 확인
kubectl -n seedtest get cronjob detect-inactivity

# Job 실행 이력
kubectl -n seedtest get jobs | grep detect-inactivity

# 로그 확인
kubectl -n seedtest logs job/<job-name>
```

#### 3. 수동 실행

```bash
kubectl -n seedtest create job --from=cronjob/detect-inactivity manual-run-$(date +%s)
```

## 검증

### 1. 비활성 사용자 확인

```sql
-- 7일 미접속 사용자 목록
SELECT DISTINCT user_id
FROM exam_results
WHERE user_id IS NOT NULL
  AND COALESCE(updated_at, created_at) < NOW() - INTERVAL '7 days'
  AND user_id NOT IN (
      SELECT DISTINCT user_id
      FROM exam_results
      WHERE user_id IS NOT NULL
        AND COALESCE(updated_at, created_at) >= NOW() - INTERVAL '7 days'
  )
LIMIT 10;
```

### 2. P/S 재계산 확인

```sql
-- 최근 업데이트된 weekly_kpi 확인
SELECT 
    user_id,
    week_start,
    kpis->>'P' AS goal_probability,
    kpis->>'S' AS churn_risk,
    updated_at
FROM weekly_kpi
WHERE updated_at >= NOW() - INTERVAL '1 day'
  AND (kpis->>'S' IS NOT NULL OR kpis->>'P' IS NOT NULL)
ORDER BY updated_at DESC
LIMIT 10;
```

## 문제 해결

### 1. 비활성 사용자가 감지되지 않음

- **원인**: 모든 소스에서 최근 활동이 있음
- **해결**: `INACTIVITY_THRESHOLD_DAYS` 값 확인 및 조정

### 2. P/S 계산 실패

- **원인**: 사용자 데이터 부족 또는 계산 로직 오류
- **해결**: 로그 확인 및 `compute_churn_risk`, `compute_goal_attainment_probability` 함수 검증

### 3. weekly_kpi 업데이트 실패

- **원인**: 기존 KPI 항목이 없거나 JSON 형식 오류
- **해결**: 자동으로 `calculate_and_store_weekly_kpi` 호출하여 전체 KPI 계산

## 성능 고려사항

- **배치 크기**: 기본적으로 모든 비활성 사용자 처리 (필요시 LIMIT 추가)
- **실행 시간**: 일일 05:00 UTC (일일 KPI 계산 이후)
- **에러 처리**: 개별 사용자 처리 실패가 전체 Job을 중단하지 않음

## 참고 문서

- 메트릭 계산: `apps/seedtest_api/services/metrics.py`
- 파이프라인 현황: `apps/seedtest_api/docs/PIPELINE_STATUS_AND_NEXT_STEPS.md`

