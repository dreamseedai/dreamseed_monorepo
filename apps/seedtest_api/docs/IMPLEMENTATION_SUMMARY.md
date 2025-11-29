# 파이프라인 구현 요약

**작성일**: 2025-11-01

## ✅ 완료된 작업

### 1. 일일 KPI 배치 (`compute_daily_kpis.py`)
- **파일**: `apps/seedtest_api/jobs/compute_daily_kpis.py`
- **기능**: 최근 N일 내 활성 유저에 대한 `I_t`/`E_t`/`R_t`/`A_t`/`P`/`S` 계산 및 `weekly_kpi` 업서트
- **K8s CronJob**: `portal_front/ops/k8s/cron/compute-daily-kpis.yaml` (매일 02:10 UTC)

### 2. `features_topic_daily` 집계 배치 (Python MVP) ⚡ **새로 생성**

**파일**: `apps/seedtest_api/jobs/aggregate_features_daily.py`

**기능**:
- `attempt` VIEW에서 일별 토픽별 집계 수행
- 계산 항목:
  - `attempts`: 총 시도 횟수
  - `correct`: 정답 개수
  - `avg_time_ms`: 평균 응답 시간
  - `rt_median`: 중앙값 응답 시간
  - `hints`: 힌트 사용 횟수
  - `theta_estimate` / `theta_sd`: IRT 능력 추정치 (옵션)
  - `improvement`: 향상지수 (정확도 또는 θ 기반 델타)
- `features_topic_daily` 테이블에 업서트

**환경 변수**:
- `AGG_LOOKBACK_DAYS`: 조회 기간 (기본 7일)
- `AGG_INCLUDE_THETA`: IRT theta 포함 여부 (기본 "false")
- `DATABASE_URL`: 데이터베이스 연결 URL

**K8s CronJob**: `portal_front/ops/k8s/cron/aggregate-features-daily.yaml` (매일 01:15 UTC)

## 📋 사용 방법

### 로컬 실행

```bash
# features_topic_daily 집계
export DATABASE_URL="postgresql://..."
export AGG_LOOKBACK_DAYS=7
python -m apps.seedtest_api.jobs.aggregate_features_daily

# 특정 날짜 지정
python -m apps.seedtest_api.jobs.aggregate_features_daily --date 2025-11-01

# Dry-run
python -m apps.seedtest_api.jobs.aggregate_features_daily --dry-run
```

### K8s 배포

```bash
# CronJob 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/aggregate-features-daily.yaml

# 상태 확인
kubectl -n seedtest get cronjob aggregate-features-daily

# 수동 실행
kubectl -n seedtest create job --from=cronjob/aggregate-features-daily manual-run-$(date +%s)
```

## 🔄 다음 단계 (우선순위)

### A. ✅ `features_topic_daily` 집계 배치 (완료)
- Python MVP 구현 완료
- 이후 필요시 R 컨테이너로 교체 가능

### B. IRT 주간 캘리브레이션 라인 정합
- `mirt_calibrate.py` 구현 완료됨
- Cron 활성화 필요 (`portal_front/ops/k8s/cron/mirt-calibrate.yaml`)
- `exam_results` 또는 `attempt` VIEW에서 관측 추출 파이프라인 연결 확인

### C. θ 온라인 업데이트
- 세션 종료 시 EAP 업데이트 → `mirt_ability` 반영
- FastAPI 엔드포인트 또는 백그라운드 Worker 구현

### D. 리포팅 (Quarto)
- 템플릿/런너 이미지/Job/S3 업로드 파이프라인 구성
- 주간 리포트 MVP

### E. 예측 이벤트 트리거
- 7일 미접속 등 조건 발생 시 즉시 P/S 재계산
- Inactivity watcher Cron 또는 DB 트리거/Worker 큐

## 📝 참고 문서

- 전체 현황: `apps/seedtest_api/docs/PIPELINE_STATUS_AND_NEXT_STEPS.md`
- IRT 표준화: `apps/seedtest_api/docs/IRT_STANDARDIZATION.md`
- 코어 도메인 표준화: `apps/seedtest_api/docs/CORE_DOMAIN_STANDARDIZATION.md`

