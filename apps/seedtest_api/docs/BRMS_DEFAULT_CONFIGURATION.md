# BRMS 기본 설정 가이드

## 개요

베이지안(brms) 모델의 기본 설정값과 입력 스키마를 정리합니다.

## 기본값 설정

### 환경 변수 (CronJob)

```yaml
env:
  # 데이터 소스
  - name: BRMS_LOOKBACK_WEEKS
    value: "12"  # 12주 데이터 사용
  
  # MCMC 파라미터
  - name: BRMS_N_SAMPLES
    value: "1000"  # posterior samples 수 (기본값)
  - name: BRMS_N_CHAINS
    value: "2"  # MCMC chains 수 (기본값)
  
  # 점수 소스
  - name: BRMS_SCORE_SOURCE
    value: "accuracy"  # 주간 정답률 기반 정규화 (기본값)
  
  # 업데이트 옵션
  - name: BRMS_UPDATE_KPI
    value: "true"  # weekly_kpi.P 업데이트
```

### R BRMS 서비스 파라미터

```python
# 기본 payload 구조
{
    "rows": [
        {"student": "user-123", "week": 0, "score": 0.5},
        {"student": "user-123", "week": 1, "score": 0.6},
        ...
    ],
    "family": "gaussian",  # 기본값
    "iter": 1000,  # 기본값 (BRMS_N_SAMPLES)
    "chains": 2  # 기본값 (BRMS_N_CHAINS)
}
```

## 입력 스키마

### 기본 스키마: 주차별 정규화 성취 (z-score)

**데이터 소스**: `weekly_kpi`에서 주간 정답률(`acc`) 추출 후 z-score 정규화

**프로세스**:
1. 주간 정답률 계산: `weekly_kpi`에서 `AVG(acc)` 또는 직접 계산
2. 전역 z-score 정규화: 모든 사용자의 주간 정답률 평균/표준편차로 정규화
3. 주차 인덱스 생성: 첫 주차를 0부터 시작하는 연속 인덱스로 변환

**입력 형식**:
```python
rows = [
    {"student": "user-123", "week": 0, "score": 0.2},  # z-scored accuracy
    {"student": "user-123", "week": 1, "score": 0.5},
    {"student": "user-456", "week": 0, "score": -0.3},
    ...
]
```

### 대체 소스: Theta 기반

`BRMS_SCORE_SOURCE=theta`로 설정 시:
- `mirt_ability`: 사용자 레벨 theta
- `student_topic_theta`: 토픽 레벨 theta (평균)
- `features_topic_daily`: 일일 theta_mean (주간 평균)

## 점수 계산 상세

### 정답률 기반 (기본값)

```sql
-- 주간 정답률 추출
SELECT 
    user_id,
    week_start,
    AVG(acc) AS accuracy
FROM weekly_kpi
WHERE week_start >= :since_date
GROUP BY user_id, week_start
```

**정규화**:
1. 전체 사용자의 주간 정답률 수집
2. 전역 평균(μ)과 표준편차(σ) 계산
3. z-score: `z = (acc - μ) / σ`

### Theta 기반 (대체)

```sql
-- mirt_ability에서 theta 추출
SELECT 
    user_id,
    fitted_at::date AS date,
    theta AS score
FROM mirt_ability
WHERE fitted_at >= :since_date
ORDER BY user_id, fitted_at
```

## CronJob 설정

### fit-bayesian-growth.yaml

```yaml
env:
  - name: BRMS_LOOKBACK_WEEKS
    value: "12"
  - name: BRMS_N_SAMPLES
    value: "1000"  # 기본값
  - name: BRMS_N_CHAINS
    value: "2"  # 기본값
  - name: BRMS_SCORE_SOURCE
    value: "accuracy"  # 주간 정답률 (기본값)
  - name: BRMS_UPDATE_KPI
    value: "true"
```

## 코드 위치

### Job 파일
- `apps/seedtest_api/jobs/fit_bayesian_growth.py`
  - 데이터 추출 로직
  - 주차별 score 계산 및 정규화
  - R BRMS 서비스 호출

### 클라이언트
- `apps/seedtest_api/app/clients/r_brms.py`
  - `fit_growth()`: R 서비스 호출
  - 기본값: `family="gaussian"`, `iter=2000`, `chains=4` (코드 기본값)
  - 환경 변수로 override 가능

## 주의사항

### MCMC 파라미터 조정

**기본값 (iter=1000, chains=2)**:
- 빠른 실행, 적은 리소스 사용
- 소규모 데이터셋에 적합

**더 높은 품질 (iter=2000, chains=4)**:
- 더 정확한 posterior 추정
- 수렴 진단 개선
- 더 많은 리소스 필요

**권장**:
- 초기 테스트: iter=1000, chains=2
- 프로덕션: iter=2000, chains=4

### 점수 소스 선택

**정답률 기반 (accuracy)**:
- 장점: 직관적, 해석 용이
- 단점: IRT 능력 추정과 다를 수 있음

**Theta 기반**:
- 장점: IRT 능력과 일관성
- 단점: theta 데이터가 없으면 사용 불가

## 검증

### 입력 데이터 확인

```python
# fit_bayesian_growth.py 실행 전 데이터 확인
from apps.seedtest_api.jobs.fit_bayesian_growth import fit_bayesian_growth
import asyncio

async def check_data():
    # 데이터 로드 확인
    from apps.seedtest_api.services.db import get_session
    import sqlalchemy as sa
    
    with get_session() as s:
        stmt = sa.text("""
            SELECT COUNT(*) as cnt
            FROM weekly_kpi
            WHERE week_start >= CURRENT_DATE - INTERVAL '12 weeks'
        """)
        result = s.execute(stmt).scalar()
        print(f"Weekly KPI rows: {result}")

asyncio.run(check_data())
```

### R 서비스 호출 테스트

```python
from apps.seedtest_api.app.clients.r_brms import RBrmsClient

client = RBrmsClient()

# 샘플 데이터로 테스트
test_rows = [
    {"student": "user-1", "week": 0, "score": 0.5},
    {"student": "user-1", "week": 1, "score": 0.6},
    {"student": "user-2", "week": 0, "score": 0.3},
]

result = await client.fit_growth(
    test_rows,
    n_samples=1000,  # 기본값
    n_chains=2,  # 기본값
)
print(result)
```

## 참고 자료

- [BRMS_METRICS_INTEGRATION.md](./BRMS_METRICS_INTEGRATION.md): Metrics 통합 가이드
- [BAYESIAN_GROWTH_GUIDE.md](./BAYESIAN_GROWTH_GUIDE.md): BRMS 모델 상세 가이드

