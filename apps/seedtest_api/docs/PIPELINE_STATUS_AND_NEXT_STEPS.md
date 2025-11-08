# 파이프라인 구현 현황 및 다음 실행안

**작성일**: 2025-11-01  
**버전**: V1

## 구현 현황 vs 계획 항목

### 1) 원천 적재 (ELT)

- **현재**: FastAPI → Postgres 직접 적재는 운용 중
- **Kafka 연동**: 미도입 (옵션)
- **제안**: V1은 Kafka 생략 (복잡도/운영비용 절감). 필요시 로드맵에 별도 PR로 편입

### 2) 정제/피처링 (`features_topic_daily`)

- **현재**: R dbplyr/arrow 기반 배치 미도입
- **스키마**: 합의 완료 (앞선 계약)
- **착수 필요**: 일/시간 단위 집계 → `features_topic_daily` 업서트 배치 (Job) 구현

### 3) 모형 추정 주기

- **IRT(a,b,c) 주간 캘리브레이션**: Dev 계약서/오퍼레이션(Plumber, Cron) 준비되어 있고 일부 반영
  - 실제 데이터 흐름 연결은 진행 중
  - `apps/seedtest_api/jobs/mirt_calibrate.py` 구현 완료
  - `exam_results` 또는 `attempt` VIEW에서 관측 추출 로직 포함
- **개인 θ 온라인 업데이트**: 미도입 (세션 종료 트리거/EAP/MI)
  - 후속 작업 필요

### 4) 예측 (P, S)

- **현재**: 일 1회 P(goal|state)/S(churn) 계산은 미도입 상태였음
- **금회 착수**: 일일 KPI 배치 구현 완료
  - 코드: `apps/seedtest_api/jobs/compute_daily_kpis.py`
  - 역할: 최근 N일(`exam_results`) 유저 목록 조회 → `calculate_and_store_weekly_kpi` 호출 → `weekly_kpi` 업서트
- **K8s CronJob**: 매일 02:10 UTC
  - 매니페스트: `portal_front/ops/k8s/cron/compute-daily-kpis.yaml`
  - 이미지: `gcr.io/univprepai/seedtest-api:latest`

### 5) 리포팅 (Quarto)

- **현재**: 설계/워크플로/런너 가이드는 준비되었으나 실제 Quarto 프로젝트/Job/S3 업로드는 미도입
- **착수 필요**: 템플릿/런너 이미지/Job/결과 URL 저장까지 파이프라인 구성

---

## 이번에 반영(착수)한 항목

### ✅ 일일 KPI 일괄 계산 배치

**파일**: `apps/seedtest_api/jobs/compute_daily_kpis.py`

**기능**:
- 최근 N일(`KPI_LOOKBACK_DAYS`, 기본 30일) 내 `exam_results`에서 유저 목록 조회
- 각 유저에 대해 `calculate_and_store_weekly_kpi` 호출
- `weekly_kpi` 테이블에 `I_t`/`E_t`/`R_t`/`A_t`/`P`/`S` 반영

**환경 변수**:
- `KPI_LOOKBACK_DAYS`: 조회 기간 (기본 30일)
- `METRICS_DEFAULT_TARGET`: 기본 목표값 (기본 "0.0")
- `METRICS_USE_BAYESIAN`: 베이지안 사용 여부 (기본 "false")
- `DATABASE_URL`: 데이터베이스 연결 URL

### ✅ K8s CronJob 매니페스트

**파일**: `portal_front/ops/k8s/cron/compute-daily-kpis.yaml`

**스케줄**: 매일 02:10 UTC  
**설정**:
- `concurrencyPolicy: Forbid` (중복 실행 방지)
- `successfulJobsHistoryLimit: 2`
- `failedJobsHistoryLimit: 3`
- 리소스: 메모리 256Mi (요청) / 512Mi (제한), CPU 100m (요청) / 500m (제한)

---

## 즉시 확인/운영 안내

### 로컬 또는 파드 수동 실행 예

```bash
# 로컬
export DATABASE_URL="postgresql://..."
export KPI_LOOKBACK_DAYS=30
python -m apps.seedtest_api.jobs.compute_daily_kpis

# 특정 날짜 지정
python -m apps.seedtest_api.jobs.compute_daily_kpis --date 2025-11-01

# Dry-run (변경 사항 커밋 안 함)
python -m apps.seedtest_api.jobs.compute_daily_kpis --dry-run
```

### K8s 적용

```bash
# CronJob 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/compute-daily-kpis.yaml

# 스케줄 확인
kubectl -n seedtest get cronjob compute-daily-kpis

# 로그 확인 (생성된 Job 이름 확인 후)
kubectl -n seedtest get jobs | grep compute-daily-kpis
kubectl -n seedtest logs job/<generated-job-name>

# 수동 트리거
kubectl -n seedtest create job --from=cronjob/compute-daily-kpis manual-run-$(date +%s)
```

---

## 다음 실행안 (추천 순서)

### A. `features_topic_daily` 집계 배치 ⚡ **우선 추천**

**선택 1: R 컨테이너 (dbplyr/arrow) 일배치**
- `r-analytics-runner` 컨테이너 + `ops/k8s/cron/aggregate-features.yaml`
- 집계: `acc`, `rt_median`, `attempts`, `hints`, `theta_mean`, `theta_sd`, `improvement` → upsert

**선택 2: Python 배치 (초기 MVP)** ✅ **이번에 구현**
- `apps/seedtest_api/jobs/aggregate_features_daily.py`
- Postgres 윈도우 집계로 MVP 구현 → 이후 R로 교체 가능
- **장점**: 빠른 MVP 제공, 기존 인프라 재사용, 디버깅 용이

**구현 파일**:
- `apps/seedtest_api/jobs/aggregate_features_daily.py` (새로 생성)
- `portal_front/ops/k8s/cron/aggregate-features-daily.yaml` (새로 생성)

### B. IRT 주간 캘리브레이션 라인 정합

**준비됨**:
- `r-irt-plumber` 배포/ServiceMonitor/Cron(야간) 스펙
- `apps/seedtest_api/jobs/mirt_calibrate.py` 구현 완료

**해야 할 일**:
- `exam_results` 또는 `attempt` VIEW에서 관측 추출 파이프라인 연결 확인
- Cron 활성화 (`portal_front/ops/k8s/cron/mirt-calibrate.yaml`)

**완료 후**: `mirt_ability`/`mirt_item_params` 채워지면 `I_t`가 θ-델타 기반으로 전환 (Dev 계약서 6)

### C. θ 온라인 업데이트 (세션 종료 트리거)

**MVP**: 세션 종료 시 `attempt`/최근 θ 기반 EAP 업데이트 → `mirt_ability` 반영

**엔드포인트/작업**:
- `POST /analysis/irt/update?user_id=`, `session_id=` (또는 Worker 큐 처리)

**구현**:
- `apps/seedtest_api/services/irt_update_service.py` (신규)
- FastAPI 엔드포인트 또는 백그라운드 Worker

### D. 리포팅 (Quarto)

**구현 항목**:
- Quarto 템플릿/런너 이미지
- K8s Job (`ops/k8s/cron/generate-weekly-report.yaml`)
- S3 업로드 + `report_artifact` URL 저장

**권장**: 주간 리포트 MVP (능력 추세/목표확률/추천 Top-N)

### E. 예측 이벤트 트리거

**구현**: 7일 미접속 등 조건 발생 시 즉시 P/S 재계산

**방식**:
- Inactivity watcher Cron (`ops/k8s/cron/detect-inactivity.yaml`)
- 또는 DB 트리거/Worker 큐

---

## 결론/요청

### ✅ 완료된 항목

1. **일일 KPI 배치**: `compute_daily_kpis.py` + CronJob 매니페스트 반영
2. **K8s 적용**: `portal_front/ops/k8s/cron/compute-daily-kpis.yaml` 적용하면 V1 예측(P, S) 일일 산출 시작

### 🔄 다음 단계

**즉시 스캐폴딩 가능**:
- **A. `features_topic_daily` 집계 배치** (Python MVP 구현 완료)
  - `apps/seedtest_api/jobs/aggregate_features_daily.py`
  - `portal_front/ops/k8s/cron/aggregate-features-daily.yaml`

**대기 중인 결정**:
- A의 `features_topic_daily` 집계 방식: **R 컨테이너 vs Python 배치** (Python MVP 제공)
- 우선순위 지정: A → B → C → D → E 순서 추천 (또는 원하는 순서 알려주세요)

---

## 우선순위 추천

1. **A. `features_topic_daily` 집계 배치** (Python MVP)
   - KPI 파이프라인 핵심 구성 요소
   - 빠른 MVP 제공 가능 (Python 기반)
   - 이후 R로 교체 가능

2. **B. IRT 주간 캘리브레이션 라인 정합**
   - 데이터 흐름 연결 및 Cron 활성화
   - `mirt_ability`/`mirt_item_params` 채워지면 `I_t` 계산 정확도 향상

3. **C. θ 온라인 업데이트**
   - 실시간 능력 추정 개선
   - 세션 종료 시 즉시 반영

4. **D. 리포팅 (Quarto)**
   - 주간 리포트 MVP
   - 사용자 인사이트 제공

5. **E. 예측 이벤트 트리거**
   - 특정 조건 발생 시 즉시 재계산
   - 이탈/부활 예측 개선

