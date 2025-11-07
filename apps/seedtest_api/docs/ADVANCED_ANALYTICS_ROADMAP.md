# Advanced Analytics 파이프라인 로드맵

**작성일**: 2025-11-01  
**상태**: 6개 모델 스캐폴딩 완료

---

## ✅ 구현 완료 현황

### 1. IRT (mirt/eRm/ltm) - 2PL 기본, 앵커 동등화 ✅

**파일**: `apps/seedtest_api/jobs/mirt_calibrate.py` (347 lines)

**기능**:
- 관측 데이터 추출 (attempt VIEW → responses → exam_results)
- 앵커 문항 로드 (`question.meta.irt`, `tags: ["anchor"]`)
- R IRT Plumber `/irt/calibrate` 호출
- `mirt_item_params`, `mirt_ability`, `mirt_fit_meta` 업데이트
- 링킹 상수 저장 (동등화)
- `question.meta.irt` 업데이트 (선택, `IRT_UPDATE_QUESTION_META=true`)

**환경 변수**:
```bash
IRT_CALIB_LOOKBACK_DAYS=30
IRT_MODEL=2PL
R_IRT_BASE_URL=http://r-irt-plumber.seedtest.svc.cluster.local:80
R_IRT_INTERNAL_TOKEN=<token>
R_IRT_TIMEOUT_SECS=300
IRT_UPDATE_QUESTION_META=false
```

**배포**:
```bash
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml
# 스케줄: 매일 03:00 UTC
```

---

### 2. GLMM (lme4) - 평균 추세 vs 개인차/토픽 효과 ✅

**파일**: `apps/seedtest_api/jobs/fit_growth_glmm.py` (새로 생성)

**기능**:
- 주차별 score (z-scored accuracy) 계산
- Formula: `score ~ week + (week|student_id) + (1|topic_id)`
- R GLMM Plumber `/glmm/fit_progress` 호출
- `growth_glmm_meta` 저장 (고정효과, 무작위효과, 적합 지표)
- `weekly_kpi.growth_slope` 업데이트 (선택)

**환경 변수**:
```bash
GLMM_LOOKBACK_WEEKS=12
GLMM_MIN_OBSERVATIONS=10
R_GLMM_BASE_URL=http://r-glmm-plumber.seedtest.svc.cluster.local:80
R_GLMM_INTERNAL_TOKEN=<token>
R_GLMM_TIMEOUT_SECS=300
GLMM_UPDATE_KPI=false
```

**R 서비스 엔드포인트 (필요)**:
```r
# POST /glmm/fit_progress
# Input: {data: [{student_id, topic_id, week, score}], formula, family}
# Output: {fixed_effects, random_effects, fit_metrics}
```

---

### 3. Bayesian (brms) - 목표확률/불확실성 ✅

**파일**: `apps/seedtest_api/jobs/fit_bayesian_growth.py` (새로 생성)

**기능**:
- 주차별 theta 시계열 로드
- Priors 설정 (intercept, week, sd)
- R brms Plumber `/growth/fit` 호출 (Stan 샘플링)
- `growth_brms_meta` 저장 (posterior summary, diagnostics)
- `weekly_kpi.P` 및 불확실성 업데이트 (향후)

**환경 변수**:
```bash
BRMS_LOOKBACK_WEEKS=12
R_BRMS_BASE_URL=http://r-brms-plumber.seedtest.svc.cluster.local:80
R_BRMS_INTERNAL_TOKEN=<token>
R_BRMS_TIMEOUT_SECS=600  # Stan 샘플링 시간
```

**R 서비스 엔드포인트 (필요)**:
```r
# POST /growth/fit
# Input: {data, formula, priors, n_samples}
# Output: {posterior_summary, diagnostics}

# POST /growth/predict
# Input: {model_id, new_data}
# Output: {predictions, credible_intervals}
```

---

### 4. Time Series (prophet) - I_t 추세/이상 탐지 ✅

**파일**: `apps/seedtest_api/jobs/forecast_prophet.py` (새로 생성)

**기능**:
- 주차별 I_t 시계열 로드
- Prophet 모델 적합 (changepoints, seasonality)
- 단기 예측 (1-4주)
- 이상치 탐지 (z-score threshold)
- `prophet_fit_meta`, `prophet_anomalies` 저장

**환경 변수**:
```bash
PROPHET_LOOKBACK_WEEKS=12
R_FORECAST_BASE_URL=http://r-forecast-plumber.seedtest.svc.cluster.local:80
R_FORECAST_INTERNAL_TOKEN=<token>
R_FORECAST_TIMEOUT_SECS=300
```

**R 서비스 엔드포인트 (필요)**:
```r
# POST /prophet/fit
# Input: {data: [{ds, y}], forecast_periods, detect_anomalies, anomaly_threshold}
# Output: {forecast, anomalies, changepoints}
```

---

### 5. Survival (survival) - 14일 미접속 위험 ✅

**파일**: `apps/seedtest_api/jobs/fit_survival_churn.py` (새로 생성)

**기능**:
- 사용자 활동 데이터 로드 (A_t, E_t, R_t, mean_gap, sessions)
- Event: 14일 미접속 (days_since_last >= 14)
- Cox proportional hazards 모델 적합
- `survival_fit_meta` 저장 (coefficients, hazard ratios)
- `weekly_kpi.S` 업데이트 (위험 점수)

**환경 변수**:
```bash
SURVIVAL_LOOKBACK_DAYS=90
R_FORECAST_BASE_URL=http://r-forecast-plumber.seedtest.svc.cluster.local:80
R_FORECAST_INTERNAL_TOKEN=<token>
R_FORECAST_TIMEOUT_SECS=300
SURVIVAL_UPDATE_KPI=true
```

**R 서비스 엔드포인트 (필요)**:
```r
# POST /survival/fit
# Input: {data: [{user_id, time, event, covariates...}], formula}
# Output: {coefficients, hazard_ratios, risk_scores}
```

---

### 6. Clustering (tidymodels) - 학습 패턴 세그먼트 ✅

**파일**: `apps/seedtest_api/jobs/cluster_segments.py` (새로 생성)

**기능**:
- 사용자 피처 벡터 로드 (A_t, I_t, E_t, R_t, sessions, gap, rt, hints)
- k-means 또는 Gaussian mixture 클러스터링
- 최적 k 선택 (silhouette, Gap 통계)
- `user_segment`, `segment_meta` 저장
- 세그먼트 라벨 (e.g., "short_frequent", "long_rare", "hint_heavy")

**환경 변수**:
```bash
CLUSTER_LOOKBACK_WEEKS=12
R_CLUSTER_BASE_URL=http://r-cluster-plumber.seedtest.svc.cluster.local:80
R_CLUSTER_INTERNAL_TOKEN=<token>
R_CLUSTER_TIMEOUT_SECS=300
```

**R 서비스 엔드포인트 (필요)**:
```r
# POST /cluster/fit
# Input: {data, method, n_clusters, features}
# Output: {assignments, centers, metrics}
```

---

## 📊 데이터베이스 스키마 (필요)

### 기존 테이블 (이미 존재)
- `mirt_item_params` - IRT 문항 파라미터
- `mirt_ability` - 사용자 능력 (θ)
- `mirt_fit_meta` - IRT 적합 메타데이터
- `weekly_kpi` - 주간 KPI (I_t, E_t, R_t, A_t, P, S)
- `features_topic_daily` - 토픽별 일일 피처

### 신규 테이블 (필요)

```sql
-- GLMM 성장 모델 메타데이터
CREATE TABLE IF NOT EXISTS growth_glmm_meta (
    run_id TEXT PRIMARY KEY,
    formula TEXT NOT NULL,
    fixed_effects JSONB,
    random_effects_summary JSONB,
    fit_metrics JSONB,
    fitted_at TIMESTAMP DEFAULT NOW()
);

-- Bayesian 성장 모델 메타데이터
CREATE TABLE IF NOT EXISTS growth_brms_meta (
    run_id TEXT PRIMARY KEY,
    formula TEXT NOT NULL,
    priors JSONB,
    posterior_summary JSONB,
    diagnostics JSONB,
    fitted_at TIMESTAMP DEFAULT NOW()
);

-- Prophet 예측 메타데이터
CREATE TABLE IF NOT EXISTS prophet_fit_meta (
    run_id TEXT PRIMARY KEY,
    metric TEXT NOT NULL,
    changepoints JSONB,
    forecast JSONB,
    fitted_at TIMESTAMP DEFAULT NOW()
);

-- Prophet 이상치
CREATE TABLE IF NOT EXISTS prophet_anomalies (
    run_id TEXT NOT NULL,
    week_start DATE NOT NULL,
    metric TEXT NOT NULL,
    value FLOAT,
    expected FLOAT,
    anomaly_score FLOAT,
    detected_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (run_id, week_start, metric)
);

-- 생존분석 메타데이터
CREATE TABLE IF NOT EXISTS survival_fit_meta (
    run_id TEXT PRIMARY KEY,
    formula TEXT NOT NULL,
    coefficients JSONB,
    hazard_ratios JSONB,
    fitted_at TIMESTAMP DEFAULT NOW()
);

-- 사용자 세그먼트
CREATE TABLE IF NOT EXISTS user_segment (
    user_id TEXT PRIMARY KEY,
    segment_label TEXT NOT NULL,
    features_snapshot JSONB,
    assigned_at TIMESTAMP DEFAULT NOW()
);

-- 세그먼트 메타데이터
CREATE TABLE IF NOT EXISTS segment_meta (
    run_id TEXT PRIMARY KEY,
    method TEXT NOT NULL,
    n_clusters INT,
    centers JSONB,
    metrics JSONB,
    fitted_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🚀 배포 계획

### Phase 1: IRT 완성 (주차 1-2)
- [x] `mirt_calibrate.py` 완성 (이미 완료)
- [ ] R IRT Plumber 서비스 배포 확인
- [ ] CronJob 활성화 및 테스트
- [ ] 앵커 문항 태깅 및 동등화 검증

### Phase 2: GLMM 추세 모델 (주차 2-3)
- [x] `fit_growth_glmm.py` 스캐폴딩 완료
- [ ] R GLMM Plumber `/glmm/fit_progress` 엔드포인트 구현
- [ ] CronJob 매니페스트 작성
- [ ] 주간 실행 및 결과 검증

### Phase 3: Bayesian + Prophet (주차 3-4)
- [x] `fit_bayesian_growth.py` 스캐폴딩 완료
- [x] `forecast_prophet.py` 스캐폴딩 완료
- [ ] R brms Plumber 서비스 구현 (Stan)
- [ ] R forecast Plumber `/prophet/fit` 엔드포인트 구현
- [ ] CronJob 배포 및 테스트

### Phase 4: Survival + Clustering (주차 4-5)
- [x] `fit_survival_churn.py` 스캐폴딩 완료
- [x] `cluster_segments.py` 스캐폴딩 완료
- [ ] R forecast Plumber `/survival/fit` 엔드포인트 구현
- [ ] R cluster Plumber `/cluster/fit` 엔드포인트 구현
- [ ] 일일/월간 실행 스케줄 설정

---

## 📋 CronJob 스케줄 (권장)

| 시간 (UTC) | Job | 설명 | 의존성 |
|-----------|-----|------|--------|
| 02:10 | compute-daily-kpis | 주간 KPI 계산 | exam_results, attempt |
| 02:25 | aggregate-features-daily | 토픽별 피처 집계 | attempt, question |
| 03:00 | mirt-calibrate | IRT 캘리브레이션 | attempt, R IRT |
| 03:30 | fit-growth-glmm | GLMM 추세 모델 | features_topic_daily, R GLMM |
| 04:00 (월) | generate-weekly-report | 주간 리포트 생성 | weekly_kpi, S3 |
| 04:30 (월) | fit-bayesian-growth | Bayesian 성장 모델 | mirt_ability, R brms |
| 05:00 (월) | forecast-prophet | Prophet I_t 예측 | weekly_kpi, R forecast |
| 06:00 | fit-survival-churn | 생존분석 (일일) | weekly_kpi, R forecast |
| 00:00 (1일) | cluster-segments | 클러스터링 (월간) | weekly_kpi, features, R cluster |

---

## 🔧 R Plumber 서비스 구현 가이드

### 1. R GLMM Plumber (새로 필요)

```r
# /glmm/fit_progress
#* @post /glmm/fit_progress
function(req, res) {
  data <- req$body$data
  formula <- as.formula(req$body$formula)
  family <- req$body$family %||% "gaussian"
  
  df <- as.data.frame(data)
  model <- lme4::lmer(formula, data = df)
  
  list(
    fixed_effects = fixef(model),
    random_effects = ranef(model),
    fit_metrics = list(
      aic = AIC(model),
      bic = BIC(model),
      loglik = logLik(model)
    )
  )
}
```

### 2. R brms Plumber (새로 필요)

```r
# /growth/fit
#* @post /growth/fit
function(req, res) {
  data <- req$body$data
  formula <- as.formula(req$body$formula)
  priors <- req$body$priors
  n_samples <- req$body$n_samples %||% 2000
  
  df <- as.data.frame(data)
  
  # Convert priors to brms format
  prior_specs <- c(
    prior(normal(0, 1), class = Intercept),
    prior(normal(0, 0.5), class = b, coef = week)
  )
  
  fit <- brms::brm(
    formula, 
    data = df,
    prior = prior_specs,
    iter = n_samples,
    chains = 4,
    cores = 4
  )
  
  list(
    posterior_summary = summary(fit)$fixed,
    diagnostics = list(
      rhat = max(rhat(fit)),
      ess_bulk = min(neff_ratio(fit))
    )
  )
}
```

### 3. R Forecast Plumber (확장 필요)

```r
# /prophet/fit
#* @post /prophet/fit
function(req, res) {
  data <- req$body$data
  forecast_periods <- req$body$forecast_periods %||% 4
  detect_anomalies <- req$body$detect_anomalies %||% TRUE
  threshold <- req$body$anomaly_threshold %||% 2.5
  
  df <- as.data.frame(data)
  m <- prophet::prophet(df)
  future <- prophet::make_future_dataframe(m, periods = forecast_periods, freq = "week")
  forecast <- predict(m, future)
  
  # Detect anomalies
  anomalies <- NULL
  if (detect_anomalies) {
    residuals <- df$y - forecast$yhat[1:nrow(df)]
    z_scores <- scale(residuals)
    anomalies <- df[abs(z_scores) > threshold, ]
  }
  
  list(
    forecast = forecast,
    anomalies = anomalies,
    changepoints = m$changepoints
  )
}

# /survival/fit
#* @post /survival/fit
function(req, res) {
  data <- req$body$data
  formula <- as.formula(req$body$formula)
  
  df <- as.data.frame(data)
  fit <- survival::coxph(formula, data = df)
  
  # Compute risk scores
  risk_scores <- predict(fit, type = "risk")
  names(risk_scores) <- df$user_id
  
  list(
    coefficients = coef(fit),
    hazard_ratios = exp(coef(fit)),
    risk_scores = as.list(risk_scores)
  )
}
```

### 4. R Cluster Plumber (새로 필요)

```r
# /cluster/fit
#* @post /cluster/fit
function(req, res) {
  data <- req$body$data
  method <- req$body$method %||% "kmeans"
  n_clusters <- req$body$n_clusters
  features <- req$body$features
  
  df <- as.data.frame(data)
  X <- df[, features]
  
  # Auto-select k if not provided
  if (is.null(n_clusters)) {
    # Use silhouette or Gap statistic
    sil_scores <- sapply(3:8, function(k) {
      km <- kmeans(X, centers = k, nstart = 25)
      cluster::silhouette(km$cluster, dist(X))[, 3] %>% mean()
    })
    n_clusters <- which.max(sil_scores) + 2
  }
  
  # Fit model
  if (method == "kmeans") {
    fit <- kmeans(X, centers = n_clusters, nstart = 25)
    assignments <- fit$cluster
    centers <- fit$centers
  } else {
    # Gaussian mixture
    fit <- mclust::Mclust(X, G = n_clusters)
    assignments <- fit$classification
    centers <- fit$parameters$mean
  }
  
  # Convert to list
  assignments_list <- as.list(assignments)
  names(assignments_list) <- df$user_id
  
  list(
    assignments = assignments_list,
    centers = centers,
    metrics = list(
      within_ss = fit$tot.withinss,
      between_ss = fit$betweenss
    )
  )
}
```

---

## 🧪 테스트 명령어

```bash
# 1. IRT Calibrate
kubectl -n seedtest create job --from=cronjob/mirt-calibrate mirt-calibrate-test-$(date +%s)

# 2. GLMM Growth (배포 후)
kubectl -n seedtest create job --from=cronjob/fit-growth-glmm fit-growth-glmm-test-$(date +%s)

# 3. Bayesian Growth (배포 후)
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth fit-bayesian-growth-test-$(date +%s)

# 4. Prophet Forecast (배포 후)
kubectl -n seedtest create job --from=cronjob/forecast-prophet forecast-prophet-test-$(date +%s)

# 5. Survival Churn (배포 후)
kubectl -n seedtest create job --from=cronjob/fit-survival-churn fit-survival-churn-test-$(date +%s)

# 6. Clustering (배포 후)
kubectl -n seedtest create job --from=cronjob/cluster-segments cluster-segments-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/<job-name>
```

---

## 📚 다음 단계

### 즉시 실행 가능
1. **IRT Calibrate 테스트** - 이미 완성됨, 즉시 배포 가능
2. **DB 마이그레이션** - 신규 테이블 생성 (growth_glmm_meta, growth_brms_meta, etc.)

### R 서비스 구현 필요
3. **R GLMM Plumber** - `/glmm/fit_progress` 엔드포인트
4. **R brms Plumber** - `/growth/fit`, `/growth/predict` 엔드포인트
5. **R Forecast Plumber 확장** - `/prophet/fit`, `/survival/fit` 엔드포인트
6. **R Cluster Plumber** - `/cluster/fit` 엔드포인트

### CronJob 배포
7. **CronJob 매니페스트 작성** - 각 Job별 YAML 파일
8. **스케줄 조정** - 의존성 고려한 실행 순서
9. **모니터링 설정** - 로그, 메트릭, 알림

---

**최종 업데이트**: 2025-11-01  
**작성자**: Cascade AI  
**상태**: 6개 모델 스캐폴딩 완료, R 서비스 구현 대기 중
