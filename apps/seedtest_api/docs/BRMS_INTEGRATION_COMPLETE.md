# BRMS (베이지안) Metrics 통합 완료

## 완료된 작업

### 1. `metrics.py` 개선 ✅

**파일**: `apps/seedtest_api/services/metrics.py`

**변경사항**:
- `compute_goal_attainment_probability()` 함수에 베이지안 경로 추가
- `METRICS_USE_BAYESIAN=true` 시:
  1. `weekly_kpi.kpis->>'P'` 우선 확인 (fit_bayesian_growth가 이미 계산한 값)
  2. 없으면 `growth_brms_meta`에서 최신 posterior 로드
  3. R BRMS client (`r_brms.prob_goal()`)로 P(goal|state) 계산
  4. 폴백: Normal approximation (기존 로직)

**코드 라인**: 665-745

### 2. R BRMS 클라이언트 확인 ✅

**파일**: `apps/seedtest_api/app/clients/r_brms.py`

**상태**: 이미 구현 완료
- `RBrmsClient`: `/growth/fit`, `/growth/predict` 엔드포인트 지원
- `prob_goal()`: 모듈 레벨 헬퍼 (metrics.py에서 사용)
- 폴백: R 서비스 미사용 시 Normal approximation

### 3. fit-bayesian-growth CronJob 연결 ✅

**파일**: `portal_front/ops/k8s/cron/fit-bayesian-growth.yaml`

**상태**: 배포 완료
- 스케줄: 매주 월요일 04:30 UTC (`30 4 * * 1`)
- 환경 변수:
  - `BRMS_LOOKBACK_WEEKS`: 12
  - `BRMS_N_SAMPLES`: 2000
  - `BRMS_N_CHAINS`: 4
  - `BRMS_UPDATE_KPI`: true (weekly_kpi에 P/σ 업데이트)
  - `R_BRMS_BASE_URL`: `http://r-brms-plumber.seedtest.svc.cluster.local:80`

### 4. 문서화 ✅

**파일**: `apps/seedtest_api/docs/BRMS_METRICS_INTEGRATION.md`

**내용**:
- 아키텍처 및 데이터 흐름
- 환경 변수 설명
- 사용법 및 검증 방법
- 트러블슈팅 가이드

## 사용 방법

### 1. 베이지안 모드 활성화

`compute-daily-kpis` CronJob에 환경 변수 추가:

```yaml
env:
  - name: METRICS_USE_BAYESIAN
    value: "true"  # 기본: "false"
```

또는 관련 서비스/Job에 직접 설정:

```bash
export METRICS_USE_BAYESIAN=true
python3 -m apps.seedtest_api.jobs.compute_daily_kpis
```

### 2. 수동 테스트

```bash
# 1. Bayesian growth model fitting
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth \
  fit-bayesian-growth-test-$(date +%s)

# 2. 로그 확인
kubectl -n seedtest logs -f job/fit-bayesian-growth-test-<timestamp>

# 3. KPI 확인
psql $DATABASE_URL -c "
  SELECT user_id, week_start, kpis->>'P' AS goal_probability
  FROM weekly_kpi
  WHERE kpis ? 'P'
  ORDER BY week_start DESC
  LIMIT 10;
"
```

## 데이터 흐름

```
┌─────────────────────────┐
│ fit-bayesian-growth     │
│ (CronJob: 월요일 04:30) │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ growth_brms_meta        │
│ - posterior_summary     │
│ - diagnostics           │
└───────────┬─────────────┘
            │
            ▼ (BRMS_UPDATE_KPI=true)
┌─────────────────────────┐
│ weekly_kpi              │
│ - kpis->>'P'            │
│ - kpis->>'sigma'        │
└───────────┬─────────────┘
            │
            ▼ (METRICS_USE_BAYESIAN=true)
┌─────────────────────────┐
│ metrics.py              │
│ compute_goal_attainment_ │
│ probability()            │
└─────────────────────────┘
```

## 다음 단계

### 즉시 가능
1. ✅ BRMS 클라이언트 생성 (완료)
2. ✅ metrics 전환 코드 추가 (완료)
3. ✅ fit-bayesian-growth Cron 연결 (완료)

### 추후 작업
- Prophet/시계열 모델 스캐폴딩
- Survival/생존분석 스캐폴딩
- Clustering/세그먼트 스캐폴딩

## 참고

- **이미지 빌드 필요**: `fit_bayesian_growth.py`의 폴백 로직이 포함된 새 이미지 빌드 및 푸시가 필요합니다.
- **r-brms-plumber 서비스**: Docker 이미지 빌드 및 배포가 완료되어야 합니다.
- **검증**: 첫 실행 후 `growth_brms_meta` 및 `weekly_kpi.P` 값 확인 권장.

