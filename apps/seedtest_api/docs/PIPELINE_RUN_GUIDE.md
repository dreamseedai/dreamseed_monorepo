# 메트릭스 파이프라인 실행 가이드

IRT 기반 θ를 사용한 주간 KPI 계산 파이프라인 실행 방법입니다.

## 사전 요구사항

### 데이터베이스

### 환경 변수 설정

#### 필수

#### 선택 (IRT 캘리브레이션용)

## 전체 파이프라인 실행

캘리브레이션 → 백필 → KPI 재계산을 한 번에 실행:

```bash
# 저장소 루트에서
make -C apps/seedtest_api pipeline-calibrate-and-kpi
```

## 개별 단계 실행

 pruning 각 단계를 개별적으로 실행할 수 있습니다.

### 1. IRT 캘리브레이션

R IRT 서비스를 사용하여 모델 캘리브레이션:

```bash
make -C apps/seedtest_api job-mirt-calibrate
```

이 작업은:

### 2. 토픽별 θ 백필

일반 능력(ability)에서 토픽별 θ를 백필:

```bash
make -C apps/seedtest_api job-backfill-topic-theta
```

이 작업은:

### 3. 주간 KPI 재계산

현재 ISO 주간 시작일(월요일) 기준으로 주간 KPI를 재계산:

```bash
make -C apps/seedtest_api job-recompute-weekly-kpi
```

이 작업은:

## 유용한 환경 변수

### 백필 작업 제어

```bash
# 백필: exam_results에서 토픽을 찾기 위해 거슬러 올라갈 일수 (기본값: 180)
export BF_LOOKBACK_DAYS=365
```

### KPI 재계산 제어

```bash
# KPI 재계산: exam_results에서 사용자를 찾기 위해 거슬러 올라갈 일수 (기본값: 90)
export KPI_USERS_SINCE_DAYS=120

# KPI 재계산: 현재 주간 시작일 대신 특정 주간 시작일 사용
export KPI_WEEK_START=2025-10-27
```

### 캘리브레이션 제어

```bash
# 캘리브레이션: 데이터를 찾기 위해 거슬러 올라갈 일수 (기본값: 30)
export IRT_CALIB_LOOKBACK_DAYS=60

# IRT 모델 유형 (기본값: "2PL")
export IRT_MODEL=3PL
```

## 실행 예시

### 전체 파이프라인 실행 (특정 주간 대상)

```bash
export KPI_WEEK_START=2025-10-27
export BF_LOOKBACK_DAYS=365
export KPI_USERS_SINCE_DAYS=120

make -C apps/seedtest_api pipeline-calibrate-and-kpi
```

### 백필만 실행 (더 긴 기간 데이터 사용)

```bash
export BF_LOOKBACK_DAYS=365
make -C apps/seedtest_api job-backfill-topic-theta
```

### 특정 주간에 대해 KPI만 재계산

```bash
export KPI_WEEK_START=2025-10-27
make -C apps/seedtest_api job-recompute-weekly-kpi
```

## 주의사항 및 가정

1. **토픽 발견**: `exam_results.result_json.questions[].topic`을 사용합니다. 정규화된 items→topics 매핑이 있다면 백필 작업을 개선할 수 있습니다.

2. **백필 범위**: 백필 작업은 사용자가 실제로 접촉한 토픽만 시드합니다 (lookback 기간 내 관찰된 토픽). 카탈로그의 모든 토픽으로 확장하지 않습니다.

3. **멱등성**: 캘리브레이션 작업과 백필은 `INSERT ... ON CONFLICT` upsert를 통해 멱등적입니다.

4. **I_t 계산**: `METRICS_USE_IRT_THETA=true`이고 최근 노출이 충분할 때, I_t는 이미 Δθ를 사용합니다. 토픽별 θ와 일반 능력 모두 I_t 계산에 사용할 수 있습니다.

## 문제 해결

### "R_IRT_BASE_URL is not configured" 오류

IRT 캘리브레이션을 실행하려면 R IRT 서비스가 필요합니다. 환경 변수를 설정하거나 캘리브레이션 단계를 건너뛰고 백필/KPI 재계산만 실행하세요.

### "No users found" 메시지


### 데이터베이스 연결 오류

`DATABASE_URL`이 올바르게 설정되어 있는지 확인하세요:
```bash
echo $DATABASE_URL
```

## 추가 정보

