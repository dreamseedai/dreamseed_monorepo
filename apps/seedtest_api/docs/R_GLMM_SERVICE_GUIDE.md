# R GLMM Plumber 서비스 구현 가이드

**목적**: 혼합효과 모델(lme4)을 통한 평균 추세 vs 개인차/토픽 효과 분리

---

## 📦 서비스 개요

### 엔드포인트
- `POST /glmm/fit_progress` - 성장 추세 모델 적합
- `POST /glmm/predict` - 개인별 예측 (선택)
- `GET /health` - Health check

### Formula
```r
score ~ week + (week|student_id) + (1|topic_id)
```

**해석**:
- `score`: z-scored 주간 정답률
- `week`: 주차 인덱스 (0, 1, 2, ...)
- `(week|student_id)`: 학생별 랜덤 절편 + 기울기
- `(1|topic_id)`: 토픽별 랜덤 절편

---

## 🔧 R Plumber 구현

### 1. 디렉토리 구조

```
r-glmm-plumber/
├── plumber.R           # 메인 API 정의
├── Dockerfile          # 컨테이너 이미지
├── renv.lock           # R 패키지 의존성
└── README.md           # 서비스 문서
```

### 2. plumber.R

```r
# r-glmm-plumber/plumber.R
library(plumber)
library(lme4)
library(jsonlite)

#* @apiTitle GLMM Growth Model Service
#* @apiDescription Mixed-effects models for learning progress analysis

#* Health check
#* @get /health
function() {
  list(
    status = "ok",
    service = "r-glmm-plumber",
    version = "1.0.0",
    timestamp = Sys.time()
  )
}

#* Fit growth model with mixed effects
#* @post /glmm/fit_progress
#* @param req Request object
function(req) {
  tryCatch({
    # Parse request body
    body <- req$body
    if (is.null(body)) {
      stop("Request body is empty")
    }
    
    data_list <- body$data
    formula_str <- body$formula %||% "score ~ week + (week|student_id) + (1|topic_id)"
    family_str <- body$family %||% "gaussian"
    
    # Convert to data frame
    df <- as.data.frame(do.call(rbind, lapply(data_list, as.data.frame)))
    
    # Ensure numeric types
    df$week <- as.numeric(df$week)
    df$score <- as.numeric(df$score)
    df$student_id <- as.factor(df$student_id)
    df$topic_id <- as.factor(df$topic_id)
    
    # Fit model
    formula_obj <- as.formula(formula_str)
    
    if (family_str == "gaussian") {
      model <- lmer(formula_obj, data = df, REML = TRUE)
    } else {
      # For binomial/poisson, use glmer
      model <- glmer(formula_obj, data = df, family = family_str)
    }
    
    # Extract fixed effects
    fixed_effects <- fixef(model)
    
    # Extract random effects
    random_effects <- ranef(model)
    
    # Convert random effects to list format
    random_effects_list <- list()
    for (group_name in names(random_effects)) {
      re_df <- as.data.frame(random_effects[[group_name]])
      re_list <- list()
      for (col_name in colnames(re_df)) {
        re_list[[col_name]] <- as.list(re_df[[col_name]])
        names(re_list[[col_name]]) <- rownames(re_df)
      }
      random_effects_list[[group_name]] <- re_list
    }
    
    # Fit metrics
    fit_metrics <- list(
      aic = AIC(model),
      bic = BIC(model),
      loglik = as.numeric(logLik(model)),
      n_obs = nrow(df),
      n_groups = list(
        student_id = length(unique(df$student_id)),
        topic_id = length(unique(df$topic_id))
      )
    )
    
    # Return results
    list(
      status = "ok",
      fixed_effects = as.list(fixed_effects),
      random_effects = random_effects_list,
      fit_metrics = fit_metrics
    )
    
  }, error = function(e) {
    list(
      status = "error",
      message = as.character(e)
    )
  })
}

#* Predict individual trajectories
#* @post /glmm/predict
#* @param req Request object
function(req) {
  tryCatch({
    body <- req$body
    
    # This would require storing the model object
    # For now, return a placeholder
    list(
      status = "not_implemented",
      message = "Prediction endpoint requires model persistence"
    )
    
  }, error = function(e) {
    list(
      status = "error",
      message = as.character(e)
    )
  })
}
```

### 3. Dockerfile

```dockerfile
# r-glmm-plumber/Dockerfile
FROM rocker/r-ver:4.3.1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c('plumber', 'lme4', 'jsonlite'), repos='https://cran.rstudio.com/')"

# Create app directory
WORKDIR /app

# Copy plumber script
COPY plumber.R /app/plumber.R

# Expose port
EXPOSE 8080

# Run plumber
CMD ["R", "-e", "pr <- plumber::plumb('/app/plumber.R'); pr$run(host='0.0.0.0', port=8080)"]
```

### 4. 빌드 및 푸시

```bash
# 이미지 빌드
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-glmm-plumber:latest \
  -f r-glmm-plumber/Dockerfile \
  r-glmm-plumber/

# 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-glmm-plumber:latest
```

---

## 🚀 Kubernetes 배포

### 1. Deployment

```yaml
# ops/k8s/services/r-glmm-plumber-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: r-glmm-plumber
  namespace: seedtest
spec:
  replicas: 2
  selector:
    matchLabels:
      app: r-glmm-plumber
  template:
    metadata:
      labels:
        app: r-glmm-plumber
    spec:
      containers:
        - name: r-glmm-plumber
          image: asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-glmm-plumber:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 8080
              name: http
          env:
            - name: R_GLMM_INTERNAL_TOKEN
              valueFrom:
                secretKeyRef:
                  name: r-glmm-credentials
                  key: token
                  optional: true
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: 2000m
              memory: 4Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: r-glmm-plumber
  namespace: seedtest
spec:
  selector:
    app: r-glmm-plumber
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP
```

### 2. 배포

```bash
# Deployment 배포
kubectl -n seedtest apply -f ops/k8s/services/r-glmm-plumber-deployment.yaml

# 상태 확인
kubectl -n seedtest get pods -l app=r-glmm-plumber
kubectl -n seedtest get svc r-glmm-plumber

# Health check
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl http://r-glmm-plumber.seedtest.svc.cluster.local:80/health
```

---

## 🧪 API 테스트

### Request 예시

```bash
curl -X POST http://r-glmm-plumber.seedtest.svc.cluster.local:80/glmm/fit_progress \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"student_id": "s1", "topic_id": "t1", "week": 0, "score": 0.2},
      {"student_id": "s1", "topic_id": "t1", "week": 1, "score": 0.5},
      {"student_id": "s1", "topic_id": "t2", "week": 0, "score": -0.3},
      {"student_id": "s2", "topic_id": "t1", "week": 0, "score": 0.8},
      {"student_id": "s2", "topic_id": "t1", "week": 1, "score": 1.2}
    ],
    "formula": "score ~ week + (week|student_id) + (1|topic_id)",
    "family": "gaussian"
  }'
```

### Response 예시

```json
{
  "status": "ok",
  "fixed_effects": {
    "(Intercept)": 0.28,
    "week": 0.35
  },
  "random_effects": {
    "student_id": {
      "(Intercept)": {
        "s1": -0.15,
        "s2": 0.15
      },
      "week": {
        "s1": 0.05,
        "s2": -0.05
      }
    },
    "topic_id": {
      "(Intercept)": {
        "t1": 0.12,
        "t2": -0.12
      }
    }
  },
  "fit_metrics": {
    "aic": 45.67,
    "bic": 52.34,
    "loglik": -18.83,
    "n_obs": 5,
    "n_groups": {
      "student_id": 2,
      "topic_id": 2
    }
  }
}
```

---

## 📊 Python Job 연동

`apps/seedtest_api/jobs/fit_growth_glmm.py`가 이미 구현되어 있습니다.

### 실행 흐름

1. **데이터 로드**: `features_topic_daily`에서 주차별 score 계산
2. **R 서비스 호출**: `/glmm/fit_progress` POST
3. **결과 저장**: `growth_glmm_meta` 테이블
4. **KPI 업데이트**: `weekly_kpi.growth_slope` (선택)

### 환경 변수

```bash
GLMM_LOOKBACK_WEEKS=12
GLMM_MIN_OBSERVATIONS=10
R_GLMM_BASE_URL=http://r-glmm-plumber.seedtest.svc.cluster.local:80
R_GLMM_INTERNAL_TOKEN=<token>
R_GLMM_TIMEOUT_SECS=300
GLMM_UPDATE_KPI=false
```

---

## 🔄 CronJob 배포

CronJob 매니페스트는 다음 단계에서 작성됩니다.

---

## 📚 참고 자료

### lme4 문서
- https://cran.r-project.org/web/packages/lme4/
- https://cran.r-project.org/web/packages/lme4/vignettes/lmer.pdf

### Plumber 문서
- https://www.rplumber.io/

### 혼합효과 모델 이론
- Bates, D., Mächler, M., Bolker, B., & Walker, S. (2015). Fitting Linear Mixed-Effects Models Using lme4. Journal of Statistical Software, 67(1), 1-48.

---

**최종 업데이트**: 2025-11-01  
**작성자**: Cascade AI  
**상태**: R 서비스 구현 가이드 완료
