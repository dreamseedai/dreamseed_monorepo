# 분석 모델 파이프라인 로드맵

**작성일**: 2025-11-01  
**상태**: IRT 완성, 나머지 모델 스캐폴딩 준비

---

## ✅ 완료된 모델

### 1. IRT (Item Response Theory) - 2PL/3PL/Rasch

**구현 상태**: ✅ 완료

**파일**:
- `apps/seedtest_api/jobs/mirt_calibrate.py` - 캘리브레이션 파이프라인
- `apps/seedtest_api/app/clients/r_irt.py` - R IRT Plumber 클라이언트
- `apps/seedtest_api/services/irt_update_service.py` - 온라인 theta 업데이트
- `apps/seedtest_api/services/question_meta.py` - question.meta.irt 관리
- `portal_front/ops/k8s/cron/mirt-calibrate.yaml` - 주간 CronJob

**기능**:
- ✅ attempt VIEW에서 관측 추출
- ✅ 앵커 동등화 지원 (question.meta tags에 "anchor")
- ✅ Linking constants 저장 (mirt_fit_meta.model_spec.linking_constants)
- ✅ question.meta.irt 반영 (옵션 또는 별도 Job)
- ✅ 온라인 theta 업데이트 (세션 완료 시)

**엔드포인트**:
- `POST /irt/calibrate`: 관측 데이터로 문항 파라미터 및 능력 추정
- `POST /irt/score`: 개인 theta 추정 (EAP/MI)

**저장**:
- `mirt_item_params`: 문항 파라미터 (a, b, c, model, version)
- `mirt_ability`: 사용자 능력 (theta, se, model, version)
- `mirt_fit_meta`: 캘리브레이션 메타데이터 (linking_constants 포함)

**주기**: 매일 03:00 UTC (CronJob)

---

## ⏭️ 다음 구현할 모델들

### 2. 혼합효과 모델 (GLMM) - lme4

**목적**: 평균 추세 vs 개인차/토픽 효과 분리

**필요 작업**:
1. 데이터 변환: 주차별 score(정규화된 성취) 계산
2. R GlMM Plumber 서비스 엔드포인트 추가:
   - `POST /glmm/fit_progress`: `score ~ week + (week|student) + (1|topic)` 모델 적합
3. 결과 저장:
   - `growth_glmm_meta`: 고정효과(week 추세), 무작위효과, 적합 지표
   - `weekly_kpi`: 고정효과/개인 기울기 연결

**예상 파일**:
- `apps/seedtest_api/app/clients/r_glmm.py` - R GlMM Plumber 클라이언트
- `apps/seedtest_api/jobs/glmm_fit_progress.py` - 주간 GLMM 적합 Job
- `portal_front/ops/k8s/cron/glmm-fit-progress.yaml` - 주간 CronJob

---

### 3. 베이지안 모델 (brms)

**목적**: 목표확률 P(goal|state) 및 불확실성 제공

**필요 작업**:
1. R brms Plumber 서비스 생성/배포
2. 엔드포인트:
   - `POST /growth/fit`: priors 포함, 샘플 수/적합시간 제어
   - `POST /growth/predict`: posterior 기반 P(goal|state)와 credible interval
3. 결과 저장:
   - `growth_brms_meta`: posterior 요약
   - `weekly_kpi.P/σ`: 목표확률 및 불확실성 업데이트

**예상 파일**:
- `apps/seedtest_api/app/clients/r_brms.py` - R brms Plumber 클라이언트
- `apps/seedtest_api/jobs/brms_fit_growth.py` - 베이지안 성장 모델 적합 Job
- `portal_front/ops/k8s/cron/brms-fit-growth.yaml` - 주간 CronJob

---

### 4. 시계열 모델 (prophet)

**목적**: I_t 추세/이상 탐지

**필요 작업**:
1. R forecast Plumber 서비스 생성/배포
2. 엔드포인트:
   - `POST /prophet/fit`: I_t 시계열 적합, changepoints/holidays(선택)
   - `POST /prophet/predict`: 단기 예측 + anomaly score
3. 결과 저장:
   - `prophet_fit_meta`: 적합 메타데이터
   - `anomalies`: 주차별 이상치 (주차, score, flag)
   - `weekly_kpi`: 보조 필드 업데이트

**예상 파일**:
- `apps/seedtest_api/app/clients/r_forecast.py` - R forecast Plumber 클라이언트
- `apps/seedtest_api/jobs/prophet_fit_engagement.py` - 주간 prophet 적합 Job
- `portal_front/ops/k8s/cron/prophet-fit-engagement.yaml` - 주간 CronJob

---

### 5. 생존분석 (survival)

**목적**: 14일 미접속 위험 추정

**필요 작업**:
1. R forecast Plumber 서비스 활용 (또는 별도 서비스)
2. 엔드포인트:
   - `POST /survival/fit`: event = 14일 미접속, 공변량 = A_t, E_t, R_t, mean_gap, sessions 등
   - `POST /survival/predict`: 개인별 S(t) 및 위험 순위
3. 결과 저장:
   - `survival_fit_meta`: 적합 메타데이터
   - `weekly_kpi.S`: 생존 확률 업데이트

**예상 파일**:
- `apps/seedtest_api/jobs/survival_fit_inactivity.py` - 생존분석 적합 Job
- `portal_front/ops/k8s/cron/survival-fit-inactivity.yaml` - 일일 CronJob

---

### 6. 클러스터링 (tidymodels)

**목적**: 학습 패턴 세그먼트 산출

**필요 작업**:
1. 입력 데이터 준비: 세션 요약(A_t 구성요소), I_t/E_t/R_t 분포, 반응시간/힌트 패턴, 주당 빈도, 간격
2. R tidymodels Plumber 서비스 생성/배포
3. 엔드포인트:
   - `POST /clustering/fit`: k-means/gaussian mixture 등, 최적 k 선택(실루엣/Gap 통계)
4. 결과 저장:
   - `user_segment`: user_id, segment_label, features_snapshot
   - `segment_meta`: 세그먼트 메타데이터

**예상 파일**:
- `apps/seedtest_api/app/clients/r_tidymodels.py` - R tidymodels Plumber 클라이언트
- `apps/seedtest_api/jobs/clustering_fit_segments.py` - 월간 클러스터링 Job
- `portal_front/ops/k8s/cron/clustering-fit-segments.yaml` - 월간 CronJob

---

## 📋 통합 포인트

### 공통 입력 경로

- `attempt VIEW`: 표준화된 시도 스키마
- `features_topic_daily`: 토픽별 일별 피처
- `weekly_kpi`: 주차별 집약 KPI
- `session`: 세션 메타데이터
- `interest_goal`: 목표 및 흥미도

### 결과 저장

- 각 모델별 meta 테이블: `*_fit_meta`
- `weekly_kpi` 집약 업데이트: P, S, 추세, 위험 등
- 리포트 섹션: Quarto 보고서에 결과 반영

### 스케줄링

- **K8s Cron**: 야간/주간 배치 실행
- **이벤트 트리거**: 세션 종료/7일 미접속 시 즉시 갱신

---

## 🚀 우선순위별 구현 계획

### 주차 1-2 (완료)

- ✅ IRT 주간 캘리브레이션 완성 (앵커 동등화 포함)
- ⏭️ GLMM 추세 모델 fit_progress 엔드포인트

### 주차 3

- brms 성장/목표확률 전환 (폴백 유지)
- prophet I_t 예측/이상 탐지

### 주차 4

- survival 위험 점수 일일 갱신
- tidymodels 세그먼트 1차 산출

### 상시

- weekly_kpi/Quarto 보고서에 결과 반영
- 모니터링 대시보드 강화

---

## 📚 참고

- **IRT 가이드**: `apps/seedtest_api/docs/IRT_CALIBRATION_COMPLETE.md`
- **전체 배포**: `apps/seedtest_api/docs/COMPLETE_DEPLOYMENT_GUIDE.md`

---

**IRT 완성 완료. 다음 모델 구현 준비 완료!** 🎉

