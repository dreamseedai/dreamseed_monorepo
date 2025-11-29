# 파이프라인 구현 완료 요약

**작성일**: 2025-11-01  
**버전**: V1

## 완료된 작업

### ✅ A. `features_topic_daily` 집계 배치

**파일**:
- `apps/seedtest_api/jobs/aggregate_features_daily.py`
- `portal_front/ops/k8s/cron/aggregate-features-daily.yaml`

**기능**:
- `attempt` VIEW에서 일별 토픽별 집계
- `attempts`, `correct`, `avg_time_ms`, `rt_median`, `hints` 계산
- IRT theta 추정치 포함 옵션
- `improvement` 향상지수 계산
- `features_topic_daily` 테이블 업서트

**스케줄**: 매일 01:15 UTC

### ✅ B. IRT 주간 캘리브레이션 라인 정합

**파일**:
- `apps/seedtest_api/jobs/mirt_calibrate.py` (개선)
- `portal_front/ops/k8s/cron/mirt-calibrate.yaml`

**개선사항**:
- `attempt` VIEW 우선 사용 (표준화된 스키마)
- Fallback: `responses` 테이블 → `exam_results` JSON
- 관측 추출 로직 강화 (최대 50,000개)

**스케줄**: 매일 03:00 UTC

### ✅ C. θ 온라인 업데이트 (세션 종료 트리거)

**파일**:
- `apps/seedtest_api/services/irt_update_service.py` (신규)
- `apps/seedtest_api/services/result_service.py` (통합)

**기능**:
- 세션 종료 시 자동 능력 업데이트 (백그라운드)
- EAP (Expected A Posteriori) 추정
- `mirt_ability` 테이블 실시간 업데이트
- 비차단식 실행 (능력 업데이트 실패가 세션 완료를 막지 않음)

**트리거**: `finish_exam()` 호출 시 자동 실행

## 배포 스케줄

### 일일 배치 실행 순서

1. **01:15 UTC**: `aggregate-features-daily`
   - `features_topic_daily` 일별 집계

2. **02:10 UTC**: `compute-daily-kpis`
   - `weekly_kpi` 계산 (I_t, E_t, R_t, A_t, P, S)

3. **03:00 UTC**: `mirt-calibrate`
   - IRT 문항 파라미터 및 능력 추정

### 실시간 처리

- **세션 종료 시**: `irt_update_service` 트리거
  - 최근 시도 데이터 기반 EAP 추정
  - `mirt_ability` 테이블 업데이트

## 데이터 흐름

```
세션 완료
  ↓
finish_exam()
  ↓
trigger_ability_update() (백그라운드)
  ↓
attempt VIEW에서 최근 시도 로드
  ↓
mirt_item_params 또는 question.meta에서 문항 파라미터 로드
  ↓
R IRT Plumber 서비스 (/irt/score) 호출
  ↓
mirt_ability 테이블 업데이트
```

### ✅ D. 리포팅 (Quarto)

**파일**:
- `apps/seedtest_api/jobs/generate_weekly_report.py` (신규)
- `reports/quarto/weekly_report.qmd` (신규)
- `apps/seedtest_api/alembic/versions/20251101_1700_report_artifacts.py` (신규)
- `portal_front/ops/k8s/cron/generate-weekly-report.yaml` (신규)

**기능**:
- 주간 리포트 생성 (KPIs, 능력 추세, 목표, 토픽 성과)
- Quarto 템플릿 렌더링 (HTML/PDF)
- S3 업로드 및 URL 저장
- `report_artifacts` 테이블에 리포트 URL 저장

**스케줄**: 매주 월요일 04:00 UTC

### ✅ E. 예측 이벤트 트리거

**파일**:
- `apps/seedtest_api/jobs/detect_inactivity.py` (신규)
- `portal_front/ops/k8s/cron/detect-inactivity.yaml` (신규)

**기능**:
- 7일 미접속 사용자 감지 (다중 소스 확인)
- 즉시 P(goal|state) 및 S(churn) 재계산
- `weekly_kpi` 테이블 업데이트 (P, S만 업데이트)

**스케줄**: 매일 05:00 UTC

## 전체 파이프라인 완료 ✅

모든 계획된 파이프라인 구성 요소가 구현 완료되었습니다:
1. ✅ A. `features_topic_daily` 집계 배치
2. ✅ B. IRT 주간 캘리브레이션 라인 정합
3. ✅ C. θ 온라인 업데이트
4. ✅ D. Quarto 리포팅 파이프라인
5. ✅ E. 예측 이벤트 트리거

## 참고 문서

- 전체 현황: `apps/seedtest_api/docs/PIPELINE_STATUS_AND_NEXT_STEPS.md`
- IRT 캘리브레이션: `apps/seedtest_api/docs/IRT_CALIBRATION_SETUP.md`
- θ 온라인 업데이트: `apps/seedtest_api/docs/THETA_ONLINE_UPDATE.md`
- 구현 요약: `apps/seedtest_api/docs/IMPLEMENTATION_SUMMARY.md`

