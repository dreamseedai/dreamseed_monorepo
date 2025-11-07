# Advanced Analytics 파라미터 튜닝 가이드

**최종 업데이트**: 2025-11-02  
**대상**: Bayesian Growth, Prophet Forecasting, Survival Analysis

---

## 🎯 파라미터 조정 시나리오

### 시나리오 1: 시계열 데이터 부족

**증상**:
```
[WARN] Insufficient time series data: 3 weeks (minimum: 8)
[ERROR] Cannot fit model with < 8 data points
```

**원인**: 신규 사용자 또는 활동 기록이 적은 사용자

**해결**:
```bash
# Bayesian Growth Model
kubectl -n seedtest set env cronjob/fit-bayesian-growth LOOKBACK_WEEKS=4

# Prophet Forecasting
kubectl -n seedtest set env cronjob/forecast-prophet PROPHET_LOOKBACK_WEEKS=4
```

**권장 범위**:
- **최소**: 4주 (Prophet 최소 요구사항)
- **기본**: 12주 (계절성 패턴 감지)
- **최대**: 24주 (장기 트렌드 분석)

---

### 시나리오 2: 이벤트 데이터 부족 (Survival)

**증상**:
```
[WARN] Insufficient event data: 5 events (minimum: 10)
[ERROR] Cox model requires at least 10 events
```

**원인**: 이탈 사용자 수가 적음 (높은 retention)

**해결**:
```bash
# Option 1: Lookback 기간 증가 (더 많은 데이터 포함)
kubectl -n seedtest set env cronjob/fit-survival-churn SURVIVAL_LOOKBACK_DAYS=180

# Option 2: 이벤트 정의 완화 (더 많은 이벤트 포함)
kubectl -n seedtest set env cronjob/fit-survival-churn SURVIVAL_EVENT_THRESHOLD_DAYS=30
```

**권장 범위**:
- **SURVIVAL_LOOKBACK_DAYS**: 60~180일
- **SURVIVAL_EVENT_THRESHOLD_DAYS**: 7~30일

**트레이드오프**:
- `LOOKBACK_DAYS` ↑ → 더 많은 데이터, 하지만 오래된 패턴 포함
- `EVENT_THRESHOLD_DAYS` ↑ → 더 많은 이벤트, 하지만 이탈 정의 완화

---

### 시나리오 3: MCMC 수렴 실패 (Bayesian)

**증상**:
```
[WARN] MCMC chains did not converge (Rhat > 1.1)
[WARN] Effective sample size too low (ESS < 400)
```

**원인**: MCMC 샘플링이 불충분하거나 모델이 복잡함

**해결**:
```bash
# Option 1: Iteration 증가 (더 많은 샘플)
kubectl -n seedtest set env cronjob/fit-bayesian-growth BRMS_ITER=2000

# Option 2: Chain 증가 (병렬 샘플링)
kubectl -n seedtest set env cronjob/fit-bayesian-growth BRMS_CHAINS=4

# Option 3: 모델 패밀리 변경 (더 robust)
kubectl -n seedtest set env cronjob/fit-bayesian-growth BRMS_FAMILY=student
```

**권장 범위**:
- **BRMS_ITER**: 1000~2000 (기본 1000)
- **BRMS_CHAINS**: 2~4 (기본 2)
- **BRMS_FAMILY**: `gaussian` (기본) 또는 `student` (outlier-robust)

**리소스 영향**:
- `ITER=2000, CHAINS=4` → 실행 시간 2~4배 증가
- 메모리: 2Gi → 4Gi 권장
- CPU: 1000m → 2000m 권장

---

### 시나리오 4: Prophet 이상치 과다 감지

**증상**:
```
[INFO] Detected 50 anomalies (25% of data points)
```

**원인**: 임계값이 너무 낮음 (정상 변동을 이상치로 판단)

**해결**:
```bash
# 임계값 증가 (더 보수적)
kubectl -n seedtest set env cronjob/forecast-prophet PROPHET_ANOMALY_THRESHOLD=3.0
```

**권장 범위**:
- **2.0**: 매우 민감 (5% 이상치)
- **2.5**: 기본 (1% 이상치)
- **3.0**: 보수적 (0.3% 이상치)

**선택 기준**:
- 노이즈가 많은 데이터 → 3.0
- 안정적인 데이터 → 2.0

---

### 시나리오 5: Churn 알림 과다 발생

**증상**:
```
[INFO] Triggered 200 churn alerts (40% of users)
```

**원인**: 임계값이 너무 낮음

**해결**:
```bash
# 임계값 증가 (더 높은 위험만 알림)
kubectl -n seedtest set env cronjob/fit-survival-churn CHURN_ALERT_THRESHOLD=0.8
```

**권장 범위**:
- **0.6**: 매우 민감 (상위 40% 알림)
- **0.7**: 기본 (상위 30% 알림)
- **0.8**: 보수적 (상위 20% 알림)

**비즈니스 목표에 따라 조정**:
- 적극적 retention → 0.6
- 선택적 개입 → 0.8

---

## 📊 파라미터 전체 목록

### Bayesian Growth Model

| 파라미터 | 기본값 | 범위 | 설명 | 영향 |
|---------|--------|------|------|------|
| `LOOKBACK_WEEKS` | 12 | 4~24 | 학습 데이터 기간 | 데이터 양 ↔ 최신성 |
| `BRMS_ITER` | 1000 | 1000~2000 | MCMC 샘플 수 | 정확도 ↔ 실행 시간 |
| `BRMS_CHAINS` | 2 | 2~4 | MCMC 체인 수 | 수렴성 ↔ 리소스 |
| `BRMS_FAMILY` | gaussian | gaussian, student | 모델 패밀리 | 정규성 가정 ↔ robustness |
| `BRMS_UPDATE_KPI` | true | true/false | weekly_kpi.P 갱신 | - |

### Prophet Forecasting

| 파라미터 | 기본값 | 범위 | 설명 | 영향 |
|---------|--------|------|------|------|
| `PROPHET_LOOKBACK_WEEKS` | 12 | 4~24 | 학습 데이터 기간 | 계절성 감지 ↔ 최신성 |
| `PROPHET_FORECAST_WEEKS` | 4 | 2~8 | 예측 기간 | 예측 범위 ↔ 정확도 |
| `PROPHET_ANOMALY_THRESHOLD` | 2.5 | 2.0~3.0 | 이상치 Z-score | 민감도 ↔ 정밀도 |

### Survival Analysis

| 파라미터 | 기본값 | 범위 | 설명 | 영향 |
|---------|--------|------|------|------|
| `SURVIVAL_LOOKBACK_DAYS` | 90 | 60~180 | 학습 데이터 기간 | 데이터 양 ↔ 최신성 |
| `SURVIVAL_EVENT_THRESHOLD_DAYS` | 14 | 7~30 | 이탈 정의 (일) | 이벤트 수 ↔ 정의 엄격성 |
| `SURVIVAL_UPDATE_KPI` | true | true/false | weekly_kpi.S 갱신 | - |
| `CHURN_ALERT_THRESHOLD` | 0.7 | 0.6~0.8 | 알림 임계값 | 민감도 ↔ 정밀도 |

### Compute Daily KPIs

| 파라미터 | 기본값 | 범위 | 설명 | 영향 |
|---------|--------|------|------|------|
| `KPI_LOOKBACK_DAYS` | 30 | 7~90 | KPI 계산 기간 | - |
| `METRICS_DEFAULT_TARGET` | 0.0 | -3.0~3.0 | 기본 목표값 | - |
| `METRICS_USE_BAYESIAN` | true | true/false | 베이지안 메트릭 사용 | - |
| `METRICS_USE_IRT_THETA` | true | true/false | IRT θ 사용 | - |

---

## 🔧 파라미터 변경 방법

### 방법 1: kubectl set env (즉시 적용)

```bash
# 단일 파라미터 변경
kubectl -n seedtest set env cronjob/fit-bayesian-growth BRMS_ITER=2000

# 여러 파라미터 변경
kubectl -n seedtest set env cronjob/forecast-prophet \
  PROPHET_LOOKBACK_WEEKS=8 \
  PROPHET_ANOMALY_THRESHOLD=3.0
```

### 방법 2: YAML 수정 후 재적용

```bash
# 1. YAML 파일 수정
vim portal_front/ops/k8s/cron/fit-bayesian-growth.yaml

# 2. 재적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-bayesian-growth.yaml
```

### 방법 3: kubectl patch (JSON)

```bash
kubectl -n seedtest patch cronjob fit-bayesian-growth --type=json -p='[
  {"op": "replace", "path": "/spec/jobTemplate/spec/template/spec/containers/0/env/6/value", "value": "2000"}
]'
```

---

## 📈 파라미터 튜닝 워크플로우

### 1. 초기 배포 (기본값)
```bash
./portal_front/ops/k8s/deploy-advanced-analytics.sh
```

### 2. 첫 실행 및 로그 확인
```bash
# Job 트리거
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth fit-bayesian-growth-test

# 로그 모니터링
kubectl -n seedtest logs -f job/fit-bayesian-growth-test
```

### 3. 문제 식별
- 데이터 부족 경고 → `LOOKBACK_*` 조정
- 수렴 실패 → `BRMS_ITER`, `BRMS_CHAINS` 증가
- 이상치 과다 → `PROPHET_ANOMALY_THRESHOLD` 증가
- 알림 과다 → `CHURN_ALERT_THRESHOLD` 증가

### 4. 파라미터 조정
```bash
kubectl -n seedtest set env cronjob/<cronjob-name> PARAM=VALUE
```

### 5. 재실행 및 검증
```bash
# 재실행
kubectl -n seedtest create job --from=cronjob/<cronjob-name> <cronjob-name>-retest

# 결과 확인
kubectl -n seedtest logs -f job/<cronjob-name>-retest
```

### 6. 프로덕션 적용
- 파라미터가 안정화되면 YAML 파일에 반영
- Git 커밋하여 버전 관리

---

## 🎯 환경별 권장 파라미터

### Development (개발 환경)

```yaml
# 빠른 실행, 적은 리소스
LOOKBACK_WEEKS: 4
BRMS_ITER: 1000
BRMS_CHAINS: 2
PROPHET_LOOKBACK_WEEKS: 4
SURVIVAL_LOOKBACK_DAYS: 60
```

### Staging (스테이징 환경)

```yaml
# 프로덕션과 유사, 약간 완화
LOOKBACK_WEEKS: 8
BRMS_ITER: 1000
BRMS_CHAINS: 2
PROPHET_LOOKBACK_WEEKS: 8
SURVIVAL_LOOKBACK_DAYS: 90
```

### Production (프로덕션 환경)

```yaml
# 최고 품질, 충분한 리소스
LOOKBACK_WEEKS: 12
BRMS_ITER: 2000
BRMS_CHAINS: 4
PROPHET_LOOKBACK_WEEKS: 12
SURVIVAL_LOOKBACK_DAYS: 90
PROPHET_ANOMALY_THRESHOLD: 2.5
CHURN_ALERT_THRESHOLD: 0.7
```

---

## 🔍 모니터링 및 최적화

### 메트릭 추적

```sql
-- Bayesian 모델 품질 (Rhat, ESS)
SELECT 
    run_id,
    model_spec->>'rhat_max' AS rhat_max,
    model_spec->>'ess_min' AS ess_min,
    fitted_at
FROM bayesian_fit_meta
ORDER BY fitted_at DESC
LIMIT 10;
-- 목표: rhat_max < 1.1, ess_min > 400

-- Prophet 이상치 비율
SELECT 
    run_id,
    COUNT(*) FILTER (WHERE is_anomaly) * 100.0 / COUNT(*) AS anomaly_rate,
    fitted_at
FROM prophet_anomalies
GROUP BY run_id, fitted_at
ORDER BY fitted_at DESC
LIMIT 10;
-- 목표: anomaly_rate 1~5%

-- Survival 이벤트 수
SELECT 
    run_id,
    n_events,
    n_users,
    n_events * 100.0 / n_users AS event_rate,
    fitted_at
FROM survival_fit_meta
ORDER BY fitted_at DESC
LIMIT 10;
-- 목표: n_events > 10, event_rate 5~20%
```

### 성능 최적화

```bash
# 실행 시간 확인
kubectl -n seedtest get jobs --sort-by=.status.completionTime | tail -10

# 리소스 사용량 확인
kubectl -n seedtest top pods -l job-name=fit-bayesian-growth
```

---

## 📚 관련 문서

- `DEPLOYMENT_CHECKLIST_ADVANCED_ANALYTICS.md` - 배포 체크리스트
- `DEPLOYMENT_SUMMARY.md` - 배포 요약
- `INTEGRATION_TEST_GUIDE.md` - 통합 테스트 가이드

---

**최종 업데이트**: 2025-11-02  
**작성자**: Cascade AI  
**상태**: Production Ready
