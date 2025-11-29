# 모든 분석 모델 스캐폴딩 완료 상태

## 완료된 스캐폴딩

### ✅ 1. 베이지안 (BRMS)

**구현 완료**:
- `fit_bayesian_growth.py`: 주간 정답률 추출 및 R 서비스 호출
- `r_brms.py` 클라이언트: `fit_growth()`, `predict_goal_probability()` 구현
- `metrics.py`: `METRICS_USE_BAYESIAN=true` 플래그 지원
- `fit-bayesian-growth.yaml` CronJob: 환경 변수 정합 완료
- `externalsecret.yaml`: r-brms-credentials ESO 설정 완료

**환경 변수**:
- `LOOKBACK_WEEKS=8` (기본값, CronJob: 12)
- `BRMS_ITER=1000`, `BRMS_CHAINS=2`
- `BRMS_FAMILY=gaussian`

### ✅ 2. Prophet (시계열 예측)

**구현 완료**:
- `forecast_prophet.py`: I_t 시계열 Prophet 모델 피팅
- `r_forecast.py` 클라이언트: `fit_prophet()` 구현 완료
- `forecast-prophet.yaml` CronJob: 환경 변수 정합 완료

**환경 변수**:
- `PROPHET_LOOKBACK_WEEKS=12`
- `PROPHET_FORECAST_WEEKS=4`
- `PROPHET_ANOMALY_THRESHOLD=2.5`

**저장 테이블**:
- `prophet_fit_meta`: 모델 파라미터, changepoints
- `prophet_anomalies`: 이상치 정보

### ✅ 3. Survival (생존분석)

**구현 완료**:
- `fit_survival_churn.py`: 14일 미접속 위험 예측
- `r_forecast.py` 클라이언트: `fit_survival()`, `predict_survival()` 구현 완료
- `fit-survival-churn.yaml` CronJob: 환경 변수 정합 완료

**환경 변수**:
- `SURVIVAL_LOOKBACK_DAYS=90`
- `SURVIVAL_EVENT_THRESHOLD_DAYS=14`
- `SURVIVAL_UPDATE_KPI=true`

**저장 테이블**:
- `survival_fit_meta`: 모델 계수, hazard ratios
- `weekly_kpi.S`: 위험 점수 업데이트

### ✅ 4. Cluster (클러스터링)

**구현 완료**:
- `cluster_segments.py`: 사용자 세그먼트 클러스터링
- `r_cluster.py` 클라이언트: `fit_clusters()`, `predict_segment()` 구현 완료
- `cluster-segments.yaml` CronJob: 환경 변수 정합 완료

**환경 변수**:
- `CLUSTER_LOOKBACK_WEEKS=12`
- `CLUSTER_N_CLUSTERS=""` (자동 선택)
- `CLUSTER_METHOD=kmeans`

**저장 테이블**:
- `user_segment`: 사용자 세그먼트 할당
- `segment_meta`: 클러스터 메타데이터

## 환경 변수 정합 상태

### ✅ 모든 모델 정합 완료

| 모델 | Job 파일 | CronJob | 상태 |
|------|---------|---------|------|
| BRMS | `LOOKBACK_WEEKS`, `BRMS_ITER`, `BRMS_CHAINS` | 동일 | ✅ 정합 |
| Prophet | `PROPHET_LOOKBACK_WEEKS`, `PROPHET_FORECAST_WEEKS` | 동일 | ✅ 정합 |
| Survival | `SURVIVAL_LOOKBACK_DAYS`, `SURVIVAL_EVENT_THRESHOLD_DAYS` | 동일 | ✅ 정합 |
| Cluster | `CLUSTER_LOOKBACK_WEEKS`, `CLUSTER_N_CLUSTERS` | 동일 | ✅ 정합 |

## R 서비스 클라이언트 구현 상태

### ✅ 완료
- `r_brms.py`: BRMS 클라이언트 구현
- `r_forecast.py`: Prophet/Survival 클라이언트 구현
- `r_cluster.py`: Cluster 클라이언트 구현

### ⚠️ 남은 작업 (R 서비스 구현)
- `r-forecast-plumber`: `/prophet/fit`, `/prophet/predict`, `/survival/fit`, `/survival/predict` 엔드포인트
- `r-cluster-plumber`: `/cluster/fit`, `/cluster/predict` 엔드포인트 (또는 r-forecast-plumber에 포함)

## ESO (External Secrets Operator) 설정

### ✅ 완료
- `r-brms-plumber/externalsecret.yaml`: GCP Secret 경로 `r-brms-internal-token`
- `r-forecast-plumber/externalsecret.yaml`: GCP Secret 경로 `r-forecast-internal-token`
- `r-irt-plumber/externalsecret.yaml`: GCP Secret 경로 `r-irt-plumber/token`

**GCP Secret Manager 경로 구조**:
- `r-brms-internal-token` → `projects/univprepai/secrets/r-brms-internal-token`
- `r-forecast-internal-token` → `projects/univprepai/secrets/r-forecast-internal-token`
- `r-irt-plumber/token` → `projects/univprepai/secrets/r-irt-plumber-token`

## CronJob 스케줄 요약

| 모델 | CronJob | 스케줄 | 상태 |
|------|---------|--------|------|
| BRMS | `fit-bayesian-growth` | `30 4 * * 1` (매주 월요일 04:30 UTC) | ✅ 설정 완료 |
| Prophet | `forecast-prophet` | `0 5 * * 1` (매주 월요일 05:00 UTC) | ✅ 설정 완료 |
| Survival | `fit-survival-churn` | `0 5 * * *` (매일 05:00 UTC) | ✅ 설정 완료 |
| Cluster | `cluster-segments` | `0 7 1,15 * *` (매월 1일, 15일 07:00 UTC) | ✅ 설정 완료 |

## 데이터 흐름 요약

```
BRMS:
  attempt VIEW → fit_bayesian_growth.py → r-brms-plumber → growth_brms_meta → weekly_kpi.P

Prophet:
  weekly_kpi (I_t) → forecast_prophet.py → r-forecast-plumber → prophet_fit_meta/prophet_anomalies

Survival:
  attempt + weekly_kpi → fit_survival_churn.py → r-forecast-plumber → survival_fit_meta → weekly_kpi.S

Cluster:
  weekly_kpi + features_topic_daily → cluster_segments.py → r-cluster-plumber → user_segment/segment_meta
```

## 다음 단계

### 즉시 가능한 작업
1. ✅ 모든 Python 클라이언트 구현 완료
2. ✅ 모든 Job 파일 구현 완료
3. ✅ 모든 CronJob 설정 완료
4. ✅ 환경 변수 정합 완료
5. ✅ ESO 설정 완료

### 남은 작업 (R 서비스 구현)
1. **r-forecast-plumber**:
   - `/prophet/fit`: Prophet 모델 피팅
   - `/prophet/predict`: 단기 예측
   - `/survival/fit`: Survival 모델 피팅
   - `/survival/predict`: 생존 확률 예측

2. **r-cluster-plumber** (또는 r-forecast-plumber에 포함):
   - `/cluster/fit`: 클러스터링 모델 피팅
   - `/cluster/predict`: 세그먼트 예측

3. **Docker 이미지 빌드 및 배포**:
   - `r-brms-plumber`, `r-forecast-plumber`, `r-cluster-plumber` 이미지 빌드
   - GCP Container Registry에 푸시

## 참고 자료

- [PROPHET_SURVIVAL_CLUSTER_ALIGNMENT.md](./PROPHET_SURVIVAL_CLUSTER_ALIGNMENT.md): 환경 변수 정합 가이드
- [BRMS_INTEGRATION_FINAL.md](./BRMS_INTEGRATION_FINAL.md): BRMS 통합 완료 상태
- [ANALYTICS_MODELS_COMPLETE.md](./ANALYTICS_MODELS_COMPLETE.md): 전체 모델 통합 문서

