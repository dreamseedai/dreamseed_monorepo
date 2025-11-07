# BRMS 환경 변수 정합 가이드

## 개요

`fit_bayesian_growth.py`와 CronJob 간의 환경 변수 이름 정합성을 보장합니다.

## 환경 변수 매핑

### 지원되는 환경 변수 이름

`fit_bayesian_growth.py`는 다음 환경 변수들을 모두 지원합니다 (우선순위 순서):

| 파라미터 | 우선순위 1 | 우선순위 2 | 기본값 |
|---------|-----------|-----------|-------|
| Lookback Weeks | `BRMS_LOOKBACK_WEEKS` | `LOOKBACK_WEEKS` | `8` |
| Samples/Iter | `BRMS_N_SAMPLES` | `BRMS_ITER` | `1000` |
| Chains | `BRMS_N_CHAINS` | `BRMS_CHAINS` | `2` |
| Family | `BRMS_FAMILY` | - | `gaussian` |

### 코드 구현

```python
# fit_bayesian_growth.py
lookback_weeks = int(
    os.getenv("BRMS_LOOKBACK_WEEKS") or os.getenv("LOOKBACK_WEEKS", "8")
)
n_samples = int(
    os.getenv("BRMS_N_SAMPLES") or os.getenv("BRMS_ITER", "1000")
)
n_chains = int(
    os.getenv("BRMS_N_CHAINS") or os.getenv("BRMS_CHAINS", "2")
)
family = os.getenv("BRMS_FAMILY", "gaussian").lower()
```

## CronJob 설정

### fit-bayesian-growth.yaml

```yaml
env:
  - name: BRMS_LOOKBACK_WEEKS
    value: "12"  # Cron에서는 12주 사용 (job 기본값 8주보다 더 긴 기간)
  - name: BRMS_N_SAMPLES
    value: "1000"  # 기본값
  - name: BRMS_N_CHAINS
    value: "2"  # 기본값
  - name: BRMS_FAMILY
    value: "gaussian"  # 기본값
```

**참고**: CronJob에서는 더 긴 기간(12주)을 사용하여 더 많은 데이터로 모델을 피팅합니다.

## 기본값 비교

### Job 기본값 (fit_bayesian_growth.py)
- `LOOKBACK_WEEKS=8`
- `BRMS_ITER=1000`
- `BRMS_CHAINS=2`
- `BRMS_FAMILY=gaussian`

### CronJob 기본값 (fit-bayesian-growth.yaml)
- `BRMS_LOOKBACK_WEEKS=12` (더 긴 기간)
- `BRMS_N_SAMPLES=1000`
- `BRMS_N_CHAINS=2`
- `BRMS_FAMILY=gaussian`

## 사용 예시

### 로컬 실행
```bash
# 기본값 사용
python -m apps.seedtest_api.jobs.fit_bayesian_growth

# 환경 변수 override
LOOKBACK_WEEKS=8 BRMS_ITER=1000 BRMS_CHAINS=2 \
  python -m apps.seedtest_api.jobs.fit_bayesian_growth
```

### CronJob 실행
```yaml
# CronJob에서 설정된 값 사용
env:
  - name: BRMS_LOOKBACK_WEEKS
    value: "12"
  - name: BRMS_N_SAMPLES
    value: "1000"
```

### 수동 Job 실행
```bash
# CronJob의 설정 상속
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth \
  fit-brms-test-$(date +%s)

# 환경 변수 override
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth \
  fit-brms-test-custom --env="BRMS_LOOKBACK_WEEKS=8" \
  --env="BRMS_N_SAMPLES=500" --env="BRMS_N_CHAINS=1"
```

## 마이그레이션 가이드

### 기존 코드에서 새 코드로

**이전 (단일 환경 변수)**:
```python
lookback_weeks = int(os.getenv("LOOKBACK_WEEKS", "12"))
n_samples = int(os.getenv("BRMS_ITER", "2000"))
n_chains = int(os.getenv("BRMS_CHAINS", "4"))
```

**현재 (다중 환경 변수 지원)**:
```python
lookback_weeks = int(
    os.getenv("BRMS_LOOKBACK_WEEKS") or os.getenv("LOOKBACK_WEEKS", "8")
)
n_samples = int(
    os.getenv("BRMS_N_SAMPLES") or os.getenv("BRMS_ITER", "1000")
)
n_chains = int(
    os.getenv("BRMS_N_CHAINS") or os.getenv("BRMS_CHAINS", "2")
)
```

## 참고

- CronJob에서는 `BRMS_LOOKBACK_WEEKS=12`를 사용하여 더 많은 데이터로 모델 피팅
- 로컬/수동 실행에서는 기본값 `LOOKBACK_WEEKS=8` 사용 가능
- 모든 환경 변수는 양쪽 이름을 모두 지원하므로 마이그레이션 부담 없음

