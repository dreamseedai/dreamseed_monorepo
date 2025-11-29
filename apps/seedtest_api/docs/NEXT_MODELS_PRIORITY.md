# 다음 모델 구현 우선순위 가이드

**작성일**: 2025-11-02  
**상태**: IRT, GLMM, Quarto 리포팅 완료

---

## ✅ 완료된 모델

1. **IRT (2PL/3PL/Rasch) + 동등화**
   - ✅ r-irt-plumber: `/irt/calibrate` anchors 지원 + linking_constants 반환
   - ✅ Calibrate Job: `mirt_calibrate.py`
   - ✅ Cron: 매일 03:00 UTC
   - ✅ I_t θ-델타 전환
   - ✅ features_topic_daily θ 채움

2. **GLMM (lme4)**
   - ✅ r-plumber: `/glmm/fit_progress` 추가
   - ✅ `score ~ week + (week|student) + (1|topic)` 모델
   - ✅ 기존 `/glmm/fit`, `/glmm/predict` 유지

3. **Quarto 리포팅**
   - ✅ 런너 이미지, 리포트 생성 Job, Cron
   - ✅ 템플릿에 Ability(θ)/Linking 섹션 포함

---

## ⏭️ 구현 필요 모델

### 1. 베이지안 (brms) - 추천 우선순위: **높음**

**목적**: 목표 달성 확률 P(goal|state) 및 불확실성 제공

**이유**:
- 이미 `METRICS_USE_BAYESIAN` 플래그가 코드에 존재
- `compute_goal_attainment_probability`에서 Bayesian 경로 준비됨
- 목표 달성 확률은 사용자 동기 부여에 중요

**필요 작업**:
- `r-brms-plumber` 서비스 스캐폴딩
- `/growth/fit`: 성장 모델 적합 (posterior 샘플링)
- `/growth/predict`: P(goal|state) 및 credible interval 계산
- `growth_brms_meta` 테이블 생성 (Alembic migration)
- Python 클라이언트 (`app/clients/r_brms.py`)
- Job (`jobs/fit_bayesian_growth.py`)
- CronJob 설정
- `weekly_kpi.P` 및 `σ` 업데이트

**예상 시간**: 1-2일

---

### 2. 시계열 (prophet) - 추천 우선순위: **중간**

**목적**: I_t 시계열 추세 및 이상 탐지

**이유**:
- 학습 패턴 변화 감지에 유용
- 이상치 탐지로 조기 개입 가능
- 단기 예측으로 학습 계획 수립 지원

**필요 작업**:
- `r-forecast-plumber` 서비스 스캐폴딩
- `/prophet/fit`: I_t 시계열 적합 (changepoints, holidays)
- `/prophet/predict`: 단기 예측 + anomaly score
- `prophet_fit_meta` 테이블 생성
- `anomalies` 테이블 생성 (주차, score, flag)
- Python 클라이언트 및 Job
- CronJob 설정
- `weekly_kpi` 보조 필드 업데이트

**예상 시간**: 1-2일

---

### 3. 생존분석 (survival) - 추천 우선순위: **높음**

**목적**: 14일 미접속 위험 예측 및 조기 경고

**이유**:
- 사용자 이탈 방지에 직접적 영향
- 고위험군 조기 식별 가능
- 비즈니스 임팩트 높음

**필요 작업**:
- `r-forecast-plumber`에 `/survival/fit`, `/survival/predict` 추가
- Event 정의: 14일 미접속
- 공변량: A_t, E_t, R_t, mean_gap, sessions
- `survival_fit_meta` 테이블 생성
- 위험 점수 저장 및 `weekly_kpi.S` 업데이트
- 일일 갱신 CronJob (05:00 UTC)
- 7일 미접속 시 즉시 갱신 트리거

**예상 시간**: 1-2일

**참고**: 이미 `detect_inactivity.py` Job이 있으므로 통합 가능

---

### 4. 클러스터링 (tidymodels) - 추천 우선순위: **낮음**

**목적**: 학습 패턴 세그먼트 분류

**이유**:
- 세그먼트화는 중요하지만 즉각적 임팩트는 낮음
- 다른 모델 구현 후 진행 가능
- Python 대안 (scikit-learn) 고려 가능

**필요 작업**:
- R 컨테이너 또는 Python 대안 선택
- k-means/Gaussian mixture 모델
- 최적 k 선택 (실루엣/Gap 통계)
- `user_segment` 테이블 생성
- `segment_meta` 테이블 생성
- 월 1-2회 실행 CronJob
- 리포트/추천에 세그먼트 라벨 반영

**예상 시간**: 2-3일

**참고**: Python 대안 사용 시 R 서비스 불필요

---

## 📊 우선순위 추천

### 시나리오 A: 비즈니스 임팩트 우선 (권장)

1. **생존분석 (survival)** - 사용자 이탈 방지
2. **베이지안 (brms)** - 목표 달성 확률 제공
3. **시계열 (prophet)** - 추세 분석 및 이상 탐지
4. **클러스터링 (tidymodels)** - 세그먼트화

### 시나리오 B: 기술적 연속성 우선

1. **베이지안 (brms)** - 이미 코드 구조 존재
2. **생존분석 (survival)** - `detect_inactivity.py`와 통합 용이
3. **시계열 (prophet)** - 독립적 구현
4. **클러스터링 (tidymodels)** - Python 대안 고려

### 시나리오 C: 빠른 완성 우선

1. **베이지안 (brms)** - 코드 구조 준비됨
2. **시계열 (prophet)** - 상대적으로 단순
3. **생존분석 (survival)** - 기존 Job과 통합
4. **클러스터링 (tidymodels)** - Python으로 빠른 구현

---

## 🚀 즉시 진행 가능

### ESO/Secret 연결 패치

현재 Secret 구조:
- `seedtest-db-credentials` (DATABASE_URL)
- `r-irt-credentials` (token)

**생성 준비 완료**:
- `portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml`
- `portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml`

**적용 방법**:
```bash
# ExternalSecret 생성
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# CronJob 업데이트
kubectl apply -f portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml
```

---

## 📋 다음 단계 결정 가이드

### 질문 1: 어떤 모델이 가장 시급한가?

- **사용자 이탈 방지**: 생존분석 우선
- **목표 달성 동기 부여**: 베이지안 우선
- **학습 패턴 분석**: 시계열 우선
- **사용자 세분화**: 클러스터링 우선

### 질문 2: 리소스 제약이 있는가?

- **R 서비스 최소화**: 베이지안 → Python 대안 고려
- **빠른 완성**: 베이지안 + 시계열
- **완전한 구현**: 모든 모델 순차 진행

### 질문 3: 기존 코드 활용 가능한가?

- **베이지안**: `METRICS_USE_BAYESIAN` 플래그 존재
- **생존분석**: `detect_inactivity.py` 통합 가능
- **시계열**: 독립적 구현
- **클러스터링**: Python 대안 가능

---

## 💡 권장 접근

### 단계별 구현 (2주 계획)

**주차 1**:
1. 생존분석 (survival) - 최우선
2. 베이지안 (brms) - 기존 코드 활용

**주차 2**:
3. 시계열 (prophet) - 추세 분석
4. 클러스터링 (tidymodels 또는 Python) - 세그먼트화

---

## 🔧 즉시 작업 가능

원하시면 다음을 바로 생성하겠습니다:

1. **베이지안 (brms)** 전체 스캐폴딩
2. **생존분석 (survival)** 전체 스캐폴딩
3. **시계열 (prophet)** 전체 스캐폴딩
4. **클러스터링** Python 버전 (scikit-learn)

**우선순위를 알려주시면 해당 모델부터 구현하겠습니다!** 🚀

