# 다음 모델 구현 우선순위 추천

**작성일**: 2025-11-02  
**기준**: 비즈니스 임팩트, 기술적 연속성, 구현 복잡도

---

## 📊 우선순위 매트릭스

| 모델 | 비즈니스 임팩트 | 기술 준비도 | 구현 복잡도 | 추천 순위 |
|------|----------------|------------|------------|----------|
| **생존분석** | ⭐⭐⭐⭐⭐ (이탈 방지) | ⭐⭐⭐ (detect_inactivity 있음) | ⭐⭐⭐ | **1위** |
| **베이지안** | ⭐⭐⭐⭐ (목표 동기) | ⭐⭐⭐⭐ (코드 구조 존재) | ⭐⭐⭐⭐ | **2위** |
| **시계열** | ⭐⭐⭐ (추세 분석) | ⭐⭐ (독립 구현) | ⭐⭐⭐ | **3위** |
| **클러스터링** | ⭐⭐ (세그먼트화) | ⭐⭐ (Python 대안 가능) | ⭐⭐ | **4위** |

---

## 🎯 추천 순서

### 1순위: 생존분석 (survival)

**이유**:
- 사용자 이탈 방지는 최우선 과제
- `detect_inactivity.py` Job과 자연스럽게 통합 가능
- 고위험군 조기 식별로 즉각적 개입 가능
- 비즈니스 ROI가 가장 높음

**구현 범위**:
- r-forecast-plumber `/survival/fit`, `/survival/predict`
- `survival_fit_meta` 테이블
- 위험 점수 저장 및 `weekly_kpi.S` 업데이트
- 일일 갱신 CronJob + 이벤트 트리거

**예상 시간**: 1-2일

---

### 2순위: 베이지안 (brms)

**이유**:
- `METRICS_USE_BAYESIAN` 플래그가 이미 코드에 존재
- `compute_goal_attainment_probability`에서 Bayesian 경로 준비됨
- 목표 달성 확률은 사용자 경험에 중요
- 기술적 연속성이 높음

**구현 범위**:
- r-brms-plumber 서비스 스캐폴딩
- `/growth/fit`, `/growth/predict` 엔드포인트
- `growth_brms_meta` 테이블
- Python 클라이언트 및 Job
- `weekly_kpi.P` 및 `σ` 업데이트

**예상 시간**: 1-2일

---

### 3순위: 시계열 (prophet)

**이유**:
- 학습 패턴 변화 감지에 유용
- 이상치 탐지로 조기 개입 가능
- 독립적 구현으로 다른 모델과 병행 가능

**구현 범위**:
- r-forecast-plumber `/prophet/fit`, `/prophet/predict`
- `prophet_fit_meta`, `anomalies` 테이블
- Python 클라이언트 및 Job
- `weekly_kpi` 보조 필드 업데이트

**예상 시간**: 1-2일

---

### 4순위: 클러스터링 (tidymodels)

**이유**:
- 세그먼트화는 중요하지만 즉각적 임팩트는 낮음
- Python 대안 (scikit-learn) 사용 시 R 서비스 불필요
- 다른 모델 구현 후 진행 가능

**구현 범위**:
- Python 버전 우선 고려 (scikit-learn)
- `user_segment`, `segment_meta` 테이블
- 월 1-2회 실행 Job
- 리포트/추천에 세그먼트 반영

**예상 시간**: 2-3일 (Python), 3-4일 (R)

---

## 🚀 즉시 구현 가능 항목

### ESO/Secret 연결

**파일 준비 완료**:
- `portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml`
- `portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml`
- `portal_front/ops/k8s/secrets/EXTERNALSECRET_SETUP_GUIDE.md`

**적용**:
```bash
# 1. ExternalSecret 생성
kubectl apply -f portal_front/ops/k8s/secrets/externalsecret-calibrate-irt.yaml

# 2. CronJob 업데이트
kubectl apply -f portal_front/ops/k8s/cron/calibrate-irt-with-externalsecret.yaml
```

---

## 📋 구현 요청

다음 중 우선순위를 지정해주시면 해당 모델부터 구현하겠습니다:

### 옵션 A: 생존분석 우선 (권장)

```bash
# 생존분석 전체 스캐폴딩
- r-forecast-plumber 서비스 확장
- Python 클라이언트 및 Job
- Alembic migration
- CronJob 설정
- detect_inactivity.py 통합
```

### 옵션 B: 베이지안 우선

```bash
# 베이지안 전체 스캐폴딩
- r-brms-plumber 서비스 생성
- Python 클라이언트 및 Job
- Alembic migration
- CronJob 설정
- metrics.py 통합
```

### 옵션 C: 시계열 우선

```bash
# 시계열 전체 스캐폴딩
- r-forecast-plumber 서비스 확장
- Python 클라이언트 및 Job
- Alembic migration
- CronJob 설정
```

### 옵션 D: 클러스터링 우선 (Python)

```bash
# 클러스터링 Python 버전
- scikit-learn 사용
- Job 생성
- Alembic migration
- CronJob 설정
```

---

## 💡 권장 접근

**2주 계획**:

**1주차**:
- 월-화: 생존분석 (survival)
- 수-목: 베이지안 (brms)

**2주차**:
- 월-화: 시계열 (prophet)
- 수-목: 클러스터링 (Python)

---

**원하시는 우선순위를 알려주시면 즉시 구현을 시작하겠습니다!** 🚀

