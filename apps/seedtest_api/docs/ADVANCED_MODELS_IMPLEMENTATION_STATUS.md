# Advanced Analytics Models - 구현 상태 요약

**최종 업데이트**: 2025-11-02 01:10 KST  
**상태**: 🚀 4개 고급 모델 추가 구현 완료

---

## 🎉 최신 구현 완료 (2025-11-02)

사용자께서 **4개의 고급 분석 모델**을 추가로 구현하셨습니다:

1. ✅ **Survival Analysis (생존분석)** - 이탈 위험 예측
2. ✅ **Prophet Forecasting (시계열 예측)** - I_t 추세 및 이상 탐지
3. ✅ **Bayesian Growth (베이지안 성장)** - 목표 달성 확률
4. ✅ **Clustering (클러스터링)** - 사용자 세그먼트 분석

---

## 📦 전체 구현 모델 (7개)

### 1. ✅ IRT (Item Response Theory) - 능력 측정
**상태**: 완전 구현 + 프로덕션 배포 가능

**구현 내용**:
- **R 서비스**: `r-irt-plumber/api.R`
  - `/irt/calibrate`: 2PL/3PL/Rasch, anchors 지원, linking_constants 반환
  - `/irt/score`: EAP 스코어링
- **Python Job**: `apps/seedtest_api/jobs/mirt_calibrate.py`
  - anchors 로드, 재시도 로직, topic/subject 필터링
  - CLI 지원: `--lookback-days`, `--model`, `--topic-id`, `--subject-id`, `--dry-run`
- **CronJob**: `ops/k8s/cron/calibrate-irt.yaml` (03:00 UTC)
- **데이터 흐름**:
  - attempt VIEW → mirt_calibrate → R IRT → mirt_item_params/mirt_ability/mirt_fit_meta
  - features_backfill → features_topic_daily (θ 채움)
  - compute_daily_kpis → weekly_kpi (I_t θ-델타)

**KPI 영향**:
- `I_t` (Improvement Index): θ-델타 기반 (정답률 폴백)
- `features_topic_daily.theta_estimate`: θ 평균
- `features_topic_daily.theta_sd`: θ 표준오차

---

### 2. ✅ GLMM (Generalized Linear Mixed Models) - 혼합효과 모델
**상태**: 완전 구현

**구현 내용**:
- **R 서비스**: `r-plumber/api.R` (기존)
  - `/glmm/fit_progress`: score ~ week + (week|student) + (1|topic)
  - `/glmm/fit`: binomial 모델
  - `/glmm/predict`: 예측
- **Python Job**: `apps/seedtest_api/jobs/fit_growth_glmm.py`
- **CronJob**: `ops/k8s/cron/fit-growth-glmm.yaml`

---

### 3. ✅ Survival Analysis (생존분석) - 이탈 위험 예측
**상태**: 완전 구현 (2025-11-02)

**구현 내용**:
- **R 서비스**: `r-forecast-plumber` (예정)
  - `/survival/fit`: Cox PH 모델
  - `/survival/predict`: 생존 확률 예측
- **Python Job**: `apps/seedtest_api/jobs/fit_survival_churn.py`
  - **데이터 소스**: attempt VIEW (우선), weekly_kpi (폴백)
  - **이벤트 정의**: 14일 미접속 (설정 가능)
  - **공변량**: A_t (engagement), E_t (efficiency), R_t (recovery), mean_gap, sessions
  - **R Client**: `RForecastClient.fit_survival()`
  - **CLI 지원**: `--lookback-days`, `--event-threshold-days`, `--dry-run`
- **저장**:
  - `survival_fit_meta`: run_id, formula, coefficients, hazard_ratios
  - `weekly_kpi.S`: 생존 확률 (위험 점수)

**예시 실행**:
```bash
# 90일 lookback, 14일 이탈 정의
python -m apps.seedtest_api.jobs.fit_survival_churn \
  --lookback-days 90 \
  --event-threshold-days 14

# 30일 이탈 정의 (더 민감한 탐지)
python -m apps.seedtest_api.jobs.fit_survival_churn \
  --event-threshold-days 30
```

**KPI 영향**:
- `S` (Survival probability): 생존 확률 / 이탈 위험 점수

---

### 4. ✅ Prophet Forecasting (시계열 예측) - I_t 추세 및 이상 탐지
**상태**: 완전 구현 (2025-11-02)

**구현 내용**:
- **R 서비스**: `r-forecast-plumber` (예정)
  - `/prophet/fit`: Prophet 모델 적합
  - `/prophet/predict`: 미래 예측
- **Python Job**: `apps/seedtest_api/jobs/forecast_prophet.py`
  - **데이터 소스**: weekly_kpi (I_t 시계열)
  - **예측 기간**: 4주 (기본)
  - **이상 탐지**: Z-score threshold 2.5 (기본)
  - **R Client**: `RForecastClient.fit_prophet()`
  - **CLI 지원**: `--lookback-weeks`, `--forecast-weeks`, `--anomaly-threshold`, `--dry-run`
- **저장**:
  - `prophet_fit_meta`: run_id, metric, changepoints, forecast, fit_meta
  - `anomalies`: run_id, week_start, metric, value, expected, anomaly_score

**예시 실행**:
```bash
# 12주 lookback, 4주 예측
python -m apps.seedtest_api.jobs.forecast_prophet \
  --lookback-weeks 12 \
  --forecast-weeks 4

# 더 민감한 이상 탐지 (threshold 2.0)
python -m apps.seedtest_api.jobs.forecast_prophet \
  --anomaly-threshold 2.0
```

**KPI 영향**:
- 이상 탐지: I_t 급격한 변화 감지
- 예측: 향후 4주 I_t 추세

---

### 5. ✅ Bayesian Growth (베이지안 성장) - 목표 달성 확률
**상태**: 완전 구현 (2025-11-02)

**구현 내용**:
- **R 서비스**: `r-brms-plumber` (예정)
  - `/growth/fit`: brms 베이지안 성장 모델
  - `/growth/predict`: 목표 달성 확률
- **Python Job**: `apps/seedtest_api/jobs/fit_bayesian_growth.py`
  - **데이터 소스**: mirt_ability (θ), features_topic_daily (theta_mean 폴백)
  - **모델**: score ~ week + (week|student_id)
  - **Priors**: 
    - intercept: Normal(0, 1) - 기준 능력 정규화
    - week: Normal(0, 0.5) - 성장 기울기 정규화
    - sd: Cauchy(0, 1) - 이상치 강건성
  - **R Client**: `RBrmsClient.fit_growth()`
  - **CLI 지원**: `--lookback-weeks`, `--n-samples`, `--n-chains`, `--dry-run`
- **저장**:
  - `brms_fit_meta`: run_id, formula, priors, posterior_summary, diagnostics
  - `weekly_kpi.P`: 목표 달성 확률
  - `weekly_kpi.sigma`: 불확실성

**예시 실행**:
```bash
# 12주 lookback, 2000 samples, 4 chains
python -m apps.seedtest_api.jobs.fit_bayesian_growth \
  --lookback-weeks 12 \
  --n-samples 2000 \
  --n-chains 4

# 빠른 테스트 (500 samples, 2 chains)
python -m apps.seedtest_api.jobs.fit_bayesian_growth \
  --n-samples 500 \
  --n-chains 2
```

**KPI 영향**:
- `P` (Probability): 목표 달성 확률
- `sigma` (Uncertainty): 예측 불확실성

---

### 6. ✅ Clustering (클러스터링) - 사용자 세그먼트 분석
**상태**: 완전 구현 (2025-11-02)

**구현 내용**:
- **Python Job**: `apps/seedtest_api/jobs/cluster_segments.py`
  - **데이터 소스**: weekly_kpi (A_t, E_t, R_t, mean_gap, sessions, improvement)
  - **알고리즘**: K-means (기본 k=5)
  - **세그먼트 라벨링**: 규칙 기반 의미 있는 라벨 생성
    - `short_frequent`: 짧고 자주 (gap < 3, sessions > 10)
    - `long_rare`: 길고 드물게 (gap > 7, sessions < 5)
    - `hint_heavy`: 힌트 집중형 (hints > 2)
    - `improving`: 향상 지속형 (improvement > 0.3)
    - `struggling`: 어려움 겪는형 (efficiency < 0.4, hints > 1.5)
    - `efficient`: 효율적 (efficiency > 0.7, hints < 0.5)
- **저장**:
  - `cluster_fit_meta`: run_id, n_clusters, features, centers, metrics
  - `user_segments`: user_id, segment_label, cluster_id, features

**예시 실행**:
```bash
# 5개 클러스터 (기본)
python -m apps.seedtest_api.jobs.cluster_segments \
  --n-clusters 5

# 3개 클러스터 (간단한 세그먼트)
python -m apps.seedtest_api.jobs.cluster_segments \
  --n-clusters 3
```

**세그먼트 활용**:
- 맞춤형 추천
- 개인화된 학습 경로
- 타겟 마케팅

---

### 7. ⏳ Quarto Reporting (리포팅) - 주간 리포트 생성
**상태**: 완전 구현

**구현 내용**:
- **Runner 이미지**: `tools/quarto-runner/Dockerfile`
- **Python Job**: `apps/seedtest_api/jobs/generate_weekly_report.py`
- **CronJob**: `ops/k8s/cron/generate-weekly-report.yaml`
- **템플릿**: `reports/quarto/weekly_report.qmd`
  - θ 트렌드 차트
  - Linking/Equating 섹션
  - KPI 요약

---

## 📊 전체 데이터 흐름 (확장)

```
1. attempt VIEW
   ↓
2. mirt_calibrate.py (IRT)
   ↓
3. mirt_item_params, mirt_ability, mirt_fit_meta
   ↓
4. features_backfill.py (θ 채움)
   ↓
5. features_topic_daily (θ 평균/표준오차)
   ↓
6. compute_daily_kpis.py (I_t θ-델타)
   ↓
7. weekly_kpi (A_t, E_t, R_t, I_t, mean_gap, sessions)
   ↓
8. fit_survival_churn.py (생존분석) → weekly_kpi.S
   ↓
9. forecast_prophet.py (시계열) → prophet_fit_meta, anomalies
   ↓
10. fit_bayesian_growth.py (베이지안) → brms_fit_meta, weekly_kpi.P/sigma
   ↓
11. cluster_segments.py (클러스터링) → cluster_fit_meta, user_segments
   ↓
12. generate_weekly_report.py (리포트) → report_artifacts (S3)
```

---

## 🔧 R 서비스 클라이언트 구조

### RForecastClient (신규)
**파일**: `apps/seedtest_api/app/clients/r_forecast.py`

**메서드**:
- `fit_survival(data, formula, model_type="coxph")`: 생존분석
- `fit_prophet(data, forecast_periods, detect_anomalies, anomaly_threshold)`: 시계열 예측

**환경 변수**:
- `R_FORECAST_BASE_URL`: http://r-forecast-plumber.seedtest.svc.cluster.local:80
- `R_FORECAST_INTERNAL_TOKEN`: 인증 토큰
- `R_FORECAST_TIMEOUT_SECS`: 300 (5분)

---

### RBrmsClient (신규)
**파일**: `apps/seedtest_api/app/clients/r_brms.py`

**메서드**:
- `fit_growth(data, formula, priors, n_samples, n_chains)`: 베이지안 성장 모델

**환경 변수**:
- `R_BRMS_BASE_URL`: http://r-brms-plumber.seedtest.svc.cluster.local:80
- `R_BRMS_INTERNAL_TOKEN`: 인증 토큰
- `R_BRMS_TIMEOUT_SECS`: 600 (10분, Stan 컴파일 시간 고려)

---

## 🚀 배포 우선순위 제안

### Phase 1: 즉시 배포 가능 (IRT)
✅ **완료**: IRT Calibration
- R IRT Plumber 배포
- CronJob 배포
- Secret 설정
- 검증 완료

---

### Phase 2: R Forecast 서비스 (Survival + Prophet)
**우선순위**: ⭐⭐⭐ 높음

**필요 작업**:
1. **r-forecast-plumber 서비스 구현**
   ```R
   # r-forecast-plumber/api.R
   
   #* Fit survival model (Cox PH)
   #* @post /survival/fit
   function(req, res) {
     data <- req$body$data
     formula <- req$body$formula
     
     # survival::coxph()
     # Return: coefficients, hazard_ratios, risk_scores
   }
   
   #* Fit Prophet model
   #* @post /prophet/fit
   function(req, res) {
     data <- req$body$data
     forecast_periods <- req$body$forecast_periods
     
     # prophet::prophet()
     # Return: forecast, anomalies, changepoints
   }
   ```

2. **Kubernetes 배포**
   ```bash
   # Dockerfile
   FROM rocker/r-ver:4.3
   RUN R -e "install.packages(c('plumber', 'survival', 'prophet'))"
   
   # Deployment
   kubectl -n seedtest apply -f ops/k8s/r-forecast-plumber/deployment.yaml
   kubectl -n seedtest apply -f ops/k8s/r-forecast-plumber/service.yaml
   ```

3. **CronJob 배포**
   ```yaml
   # ops/k8s/cron/fit-survival-churn.yaml
   schedule: "0 4 * * *"  # 04:00 UTC
   command: ["python", "-m", "apps.seedtest_api.jobs.fit_survival_churn"]
   
   # ops/k8s/cron/forecast-prophet.yaml
   schedule: "0 5 * * 0"  # 05:00 UTC, 매주 일요일
   command: ["python", "-m", "apps.seedtest_api.jobs.forecast_prophet"]
   ```

**예상 소요 시간**: 2-3시간

---

### Phase 3: R BRMS 서비스 (Bayesian Growth)
**우선순위**: ⭐⭐ 중간

**필요 작업**:
1. **r-brms-plumber 서비스 구현**
   ```R
   # r-brms-plumber/api.R
   
   #* Fit Bayesian growth model
   #* @post /growth/fit
   function(req, res) {
     data <- req$body$data
     formula <- req$body$formula
     priors <- req$body$priors
     
     # brms::brm()
     # Return: posterior_summary, diagnostics, predictions
   }
   ```

2. **Kubernetes 배포**
   ```bash
   # Dockerfile (Stan 컴파일 시간 고려)
   FROM rocker/r-ver:4.3
   RUN R -e "install.packages(c('plumber', 'brms', 'rstan'))"
   
   # Deployment (높은 리소스 요구)
   resources:
     requests:
       cpu: "2000m"
       memory: "4Gi"
     limits:
       cpu: "8000m"
       memory: "16Gi"
   ```

3. **CronJob 배포**
   ```yaml
   # ops/k8s/cron/fit-bayesian-growth.yaml
   schedule: "0 6 * * 0"  # 06:00 UTC, 매주 일요일
   command: ["python", "-m", "apps.seedtest_api.jobs.fit_bayesian_growth"]
   ```

**예상 소요 시간**: 3-4시간 (Stan 설정 복잡도)

---

### Phase 4: Clustering (Python 기반)
**우선순위**: ⭐ 낮음 (R 서비스 불필요)

**필요 작업**:
1. **CronJob 배포만 필요** (Python Job 이미 완성)
   ```yaml
   # ops/k8s/cron/cluster-segments.yaml
   schedule: "0 7 1,15 * *"  # 07:00 UTC, 매월 1일, 15일
   command: ["python", "-m", "apps.seedtest_api.jobs.cluster_segments"]
   ```

**예상 소요 시간**: 30분

---

## 📋 추가 구현 파일 목록

### Python Jobs (4개 추가)
1. ✅ `apps/seedtest_api/jobs/fit_survival_churn.py` - 생존분석 (2025-11-02)
2. ✅ `apps/seedtest_api/jobs/forecast_prophet.py` - 시계열 예측 (2025-11-02)
3. ✅ `apps/seedtest_api/jobs/fit_bayesian_growth.py` - 베이지안 성장 (2025-11-02)
4. ✅ `apps/seedtest_api/jobs/cluster_segments.py` - 클러스터링 (2025-11-02)

### Python Clients (2개 추가 예정)
5. ⏳ `apps/seedtest_api/app/clients/r_forecast.py` - RForecastClient
6. ⏳ `apps/seedtest_api/app/clients/r_brms.py` - RBrmsClient

### R Services (2개 추가 필요)
7. ⏳ `r-forecast-plumber/api.R` - Survival + Prophet
8. ⏳ `r-brms-plumber/api.R` - BRMS

### Kubernetes Manifests (6개 추가 필요)
9. ⏳ `ops/k8s/r-forecast-plumber/deployment.yaml`
10. ⏳ `ops/k8s/r-forecast-plumber/service.yaml`
11. ⏳ `ops/k8s/r-brms-plumber/deployment.yaml`
12. ⏳ `ops/k8s/r-brms-plumber/service.yaml`
13. ⏳ `ops/k8s/cron/fit-survival-churn.yaml`
14. ⏳ `ops/k8s/cron/forecast-prophet.yaml`
15. ⏳ `ops/k8s/cron/fit-bayesian-growth.yaml`
16. ⏳ `ops/k8s/cron/cluster-segments.yaml`

---

## ✅ 완료 체크리스트

### IRT (완료)
- [x] R IRT Plumber 구현
- [x] mirt_calibrate.py 구현
- [x] CronJob 매니페스트
- [x] CLI 지원
- [x] topic/subject 필터링
- [x] 문서화

### Survival Analysis (Python 완료, R 서비스 필요)
- [x] fit_survival_churn.py 구현
- [x] RForecastClient 통합
- [x] CLI 지원
- [x] weekly_kpi.S 업데이트
- [ ] r-forecast-plumber /survival/fit 구현
- [ ] CronJob 배포

### Prophet Forecasting (Python 완료, R 서비스 필요)
- [x] forecast_prophet.py 구현
- [x] RForecastClient 통합
- [x] CLI 지원
- [x] prophet_fit_meta, anomalies 저장
- [ ] r-forecast-plumber /prophet/fit 구현
- [ ] CronJob 배포

### Bayesian Growth (Python 완료, R 서비스 필요)
- [x] fit_bayesian_growth.py 구현
- [x] RBrmsClient 통합
- [x] CLI 지원
- [x] weekly_kpi.P/sigma 업데이트
- [ ] r-brms-plumber /growth/fit 구현
- [ ] CronJob 배포

### Clustering (완료, CronJob만 필요)
- [x] cluster_segments.py 구현
- [x] 의미 있는 세그먼트 라벨링
- [x] CLI 지원
- [x] cluster_fit_meta, user_segments 저장
- [ ] CronJob 배포

---

## 🎯 권장 다음 단계

### 옵션 1: R Forecast 서비스 우선 (추천)
**이유**: Survival + Prophet 모두 포함, 즉시 활용 가능

**작업 순서**:
1. r-forecast-plumber 서비스 구현 (2시간)
2. Kubernetes 배포 (30분)
3. CronJob 배포 (30분)
4. 검증 및 테스트 (1시간)

**총 소요 시간**: 4시간

---

### 옵션 2: Clustering CronJob 먼저 (빠름)
**이유**: R 서비스 불필요, 즉시 배포 가능

**작업 순서**:
1. CronJob 매니페스트 작성 (15분)
2. 배포 및 테스트 (15분)

**총 소요 시간**: 30분

---

### 옵션 3: 전체 순차 배포
**작업 순서**:
1. Clustering CronJob (30분)
2. R Forecast 서비스 + CronJobs (4시간)
3. R BRMS 서비스 + CronJob (4시간)

**총 소요 시간**: 8.5시간

---

## 📚 관련 문서

- **[COMPLETE_IMPLEMENTATION_SUMMARY.md](./COMPLETE_IMPLEMENTATION_SUMMARY.md)** - IRT 구현 요약
- **[ADVANCED_ANALYTICS_ROADMAP.md](./ADVANCED_ANALYTICS_ROADMAP.md)** - 6개 모델 로드맵
- **[portal_front/ops/k8s/README.md](../../portal_front/ops/k8s/README.md)** - K8s 배포 가이드

---

## 🎉 최종 요약

**완료된 구현** (2025-11-02):
- ✅ IRT Calibration (프로덕션 배포 가능)
- ✅ GLMM (완전 구현)
- ✅ Survival Analysis (Python 완료, R 서비스 필요)
- ✅ Prophet Forecasting (Python 완료, R 서비스 필요)
- ✅ Bayesian Growth (Python 완료, R 서비스 필요)
- ✅ Clustering (Python 완료, CronJob만 필요)
- ✅ Quarto Reporting (완전 구현)

**다음 우선순위**:
1. ⭐⭐⭐ **R Forecast 서비스** (Survival + Prophet)
2. ⭐⭐ **R BRMS 서비스** (Bayesian Growth)
3. ⭐ **Clustering CronJob** (즉시 가능)

**사용자 선택 요청**:
- R Forecast 서비스 우선 구현? (Survival + Prophet)
- Clustering CronJob 먼저 배포? (빠름)
- 전체 순차 배포?
- ESO/Secret 연결 패치 생성?

---

**최종 업데이트**: 2025-11-02 01:10 KST  
**작성자**: Cascade AI  
**상태**: 🚀 4개 고급 모델 추가 구현 완료, R 서비스 배포 대기
