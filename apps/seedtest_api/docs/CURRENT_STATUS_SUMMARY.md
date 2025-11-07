# 현재 구현 상태 요약

**작성일**: 2025-11-02  
**기준**: 점검 결과 및 추가 구현 상태

---

## ✅ 완료된 항목

### 1. IRT (2PL/3PL/Rasch) + 동등화

**상태**: ✅ 완료

- **r-irt-plumber**: `/irt/calibrate`에 anchors 지원과 linking_constants 반환 추가
- **Calibrate Job**: `apps/seedtest_api/jobs/mirt_calibrate.py`
  - attempt VIEW에서 관측 추출 → anchors 로드 → `/irt/calibrate` 호출(백오프/재시도)
  - `mirt_item_params`/`mirt_ability`/`mirt_fit_meta` upsert
- **Cron**: `ops/k8s/cron/calibrate-irt.yaml` (매일 03:00 UTC)
- **I_t**: θ-델타 기반으로 전환(없으면 정답률 폴백), `weekly_kpi`에 저장
- **features_topic_daily**: θ 평균/표준오차 채워 upsert(backfill 서비스 반영)

**참고 문서**:
- `apps/seedtest_api/docs/IRT_CALIBRATION_COMPLETE.md`
- `apps/seedtest_api/docs/IRT_CALIBRATION_SETUP.md`

---

### 2. 혼합효과 (lme4)

**상태**: ✅ 완료

- **r-plumber**: `/glmm/fit_progress` 추가
  - `score ~ week + (week|student) + (1|topic)`, gaussian 기본
  - fit_meta/metrics/랜덤효과 반환
- **기존**: `/glmm/fit`, `/glmm/predict` 유지(binomial)
- **Job**: `apps/seedtest_api/jobs/glmm_fit_progress.py`
- **Cron**: `portal_front/ops/k8s/cron/glmm-fit-progress.yaml`

---

### 3. Quarto 리포팅

**상태**: ✅ 완료

- **런너 이미지**: `tools/quarto-runner/Dockerfile` (Quarto + Python + S3/DB deps)
- **리포트 생성 Job**: `apps/seedtest_api/jobs/generate_weekly_report.py`
  - `weekly_kpi` → Quarto 렌더(pdf/html) → S3 업로드 → `report_artifact` upsert
- **Cron**: `ops/k8s/cron/generate-weekly-report.yaml`
  - 버킷/리전/포맷 env 반영(`S3_BUCKET`, `AWS_REGION`, `REPORT_FORMAT`)
- **템플릿**: `reports/quarto/weekly_report.qmd` (Ability(θ)/Linking 섹션 포함)

**참고 문서**:
- `apps/seedtest_api/docs/QUARTO_REPORTING_GUIDE.md`
- `apps/seedtest_api/docs/QUARTO_BATCH_REPORTING.md`

---

## ⏭️ 미구현 항목 (우선순위별)

### 1. 생존분석 (survival) - **추천 우선순위 1위**

**이유**: 사용자 이탈 방지는 최우선 과제, 비즈니스 ROI 높음

**필요 작업**:
- r-forecast-plumber: `/survival/fit`, `/survival/predict`
  - event = 14일 미접속
  - 공변량 = A_t, E_t, R_t, mean_gap, sessions
- `survival_fit_meta` 테이블 생성 (Alembic migration)
- Python 클라이언트 (`app/clients/r_forecast.py` 확장)
- Job (`jobs/fit_survival_churn.py` 완성)
- CronJob 설정 (일일 05:00 UTC)
- `weekly_kpi.S` 업데이트
- 7일 미접속 시 즉시 갱신 트리거

**기존 코드**:
- `apps/seedtest_api/jobs/fit_survival_churn.py` (스캐폴딩 완료)
- `apps/seedtest_api/jobs/detect_inactivity.py` (통합 가능)

**예상 시간**: 1-2일

---

### 2. 베이지안 (brms) - **추천 우선순위 2위**

**이유**: `METRICS_USE_BAYESIAN` 플래그가 이미 코드에 존재, 기술적 연속성 높음

**필요 작업**:
- r-brms-plumber: brms 기반 성장/목표확률 엔드포인트 스캐폴딩
  - `POST /growth/fit`: priors 포함, 샘플 수/적합시간 제어
  - `POST /growth/predict`: posterior 기반 P(goal|state)와 credible interval
- `growth_brms_meta` 테이블 생성 (Alembic migration)
- Python 클라이언트 (`app/clients/r_brms.py`)
- Job (`jobs/fit_bayesian_growth.py` 완성)
- CronJob 설정
- API에서 `METRICS_USE_BAYESIAN` 플래그로 전환/폴백 유지
- `weekly_kpi.P/σ` 업데이트

**기존 코드**:
- `apps/seedtest_api/services/metrics.py`: `compute_goal_attainment_probability`에서 Bayesian 경로 준비됨
- `apps/seedtest_api/jobs/fit_bayesian_growth.py` (스캐폴딩 완료)

**예상 시간**: 1-2일

---

### 3. 시계열 (prophet) - **추천 우선순위 3위**

**이유**: 학습 패턴 변화 감지에 유용, 독립적 구현 가능

**필요 작업**:
- r-forecast-plumber: `/prophet/fit`, `/prophet/predict`
  - I_t 시계열 적합, changepoints/holidays(선택)
  - 단기 예측 + anomaly score
- `prophet_fit_meta` 테이블 생성 (Alembic migration)
- `anomalies` 테이블 생성 (주차, score, flag)
- Python 클라이언트 (`app/clients/r_forecast.py` 확장)
- Job (`jobs/forecast_prophet.py` 완성)
- CronJob 설정
- `weekly_kpi` 보조 필드 업데이트

**기존 코드**:
- `apps/seedtest_api/jobs/forecast_prophet.py` (스캐폴딩 완료)

**예상 시간**: 1-2일

---

### 4. 클러스터링 (tidymodels) - **추천 우선순위 4위**

**이유**: 세그먼트화는 중요하지만 즉각적 임팩트는 낮음, Python 대안 고려 가능

**필요 작업**:
- R 컨테이너 또는 Python 대안으로 세그먼트 산출/저장
- 입력: 세션 요약(A_t 구성요소), I_t/E_t/R_t 분포, 반응시간/힌트 사용 패턴, 주당 빈도, 간격
- 처리: k-means/Gaussian mixture 등, 최적 k 선택(실루엣/Gap 통계)
- `user_segment` 테이블 생성 (user_id, segment_label, features_snapshot)
- `segment_meta` 테이블 생성
- 월 1-2회 실행 CronJob
- 리포트/추천에 세그먼트 라벨 반영

**기존 코드**:
- `apps/seedtest_api/jobs/cluster_segments.py` (스캐폴딩 완료)

**예상 시간**: 2-3일 (Python), 3-4일 (R)

---

## 🚀 권장 후속 작업 (즉시 가능)

### 1. r-irt-plumber anchors 고도화

**현재 상태**: 간단한 선형 링크(A,B) 적용

**개선 제안**:
- 필요 시 Stocking-Lord/Haebara 방식으로 개선
- 응답에 linking_constants를 `fit_meta.linking_constants`와 함께 이미 반환

---

### 2. ESO/Secret/ConfigMap 연결

**목적**: calibrate-irt Cron에 DATABASE_URL, R_IRT_INTERNAL_TOKEN 주입을 ExternalSecret으로 구성

**파일 준비**:
- `portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml`
- `portal_front/ops/k8s/secrets/externalsecret-calibrate-irt-final.yaml`
- `portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml`

**적용 방법**:
```bash
# 1. ExternalSecret 생성
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt-final.yaml

# 2. CronJob 업데이트
kubectl apply -f portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml
```

**참고 문서**:
- `portal_front/ops/k8s/secrets/README_SECRETS.md`
- `portal_front/ops/k8s/secrets/EXTERNALSECRET_SETUP_GUIDE.md`

---

### 3. 테스트 보강

**필요 작업**:
- metrics(θ/정답률 폴백) 테스트
- features_backfill(θ 반영) 테스트
- `/irt/calibrate` anchors 응답 업서트 테스트

---

## 📊 우선순위 매트릭스

| 모델 | 비즈니스 임팩트 | 기술 준비도 | 구현 복잡도 | 추천 순위 |
|------|----------------|------------|------------|----------|
| **생존분석** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | **1위** |
| **베이지안** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **2위** |
| **시계열** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | **3위** |
| **클러스터링** | ⭐⭐ | ⭐⭐ | ⭐⭐ | **4위** |

---

## 📋 다음 단계

**우선순위를 지정해주시면 해당 모델부터 구현하겠습니다:**

1. **생존분석 (survival)** - 사용자 이탈 방지
2. **베이지안 (brms)** - 목표 달성 확률
3. **시계열 (prophet)** - 추세 분석 및 이상 탐지
4. **클러스터링 (tidymodels)** - 세그먼트화

**또는 ESO/Secret 연결 패치를 먼저 진행하시겠습니까?** 🔐

---

**참고 문서**:
- `apps/seedtest_api/docs/NEXT_MODELS_PRIORITY.md`
- `apps/seedtest_api/docs/IMPLEMENTATION_PRIORITY_RECOMMENDATION.md`
- `apps/seedtest_api/docs/ANALYTICS_MODELS_ROADMAP.md`

