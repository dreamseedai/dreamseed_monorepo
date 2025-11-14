# 분석 모델 배포 및 검증 체크리스트

## 📋 배포 순서 (권장)

### 1. 이미지/리소스

#### r-brms-plumber
```bash
cd /home/won/projects/dreamseed_monorepo/r-brms-plumber
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-brms-plumber:latest

kubectl -n seedtest apply -f portal_front/ops/k8s/r-brms-plumber/
```

#### r-forecast-plumber
```bash
cd /home/won/projects/dreamseed_monorepo/r-forecast-plumber
docker build -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest .
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/r-forecast-plumber:latest

kubectl -n seedtest apply -f portal_front/ops/k8s/r-forecast-plumber/
```

**확인 사항:**
- Pod가 `Running` 상태인지 확인: `kubectl -n seedtest get pods -l app=r-brms-plumber`
- ServiceMonitor가 생성되었는지 확인: `kubectl -n seedtest get servicemonitor r-brms-plumber`

### 2. Secrets/ESO

```bash
# ExternalSecret 확인
kubectl -n seedtest get externalsecret r-brms-credentials
kubectl -n seedtest get externalsecret r-forecast-credentials

# Secret 동기화 확인
kubectl -n seedtest get secret r-brms-credentials -o jsonpath='{.data}' | jq
kubectl -n seedtest get secret r-forecast-credentials -o jsonpath='{.data}' | jq

# DATABASE_URL 확인
kubectl -n seedtest get secret seedtest-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

**확인 사항:**
- `r-brms-internal-token`, `r-forecast-internal-token` 키가 GCP Secret Manager에 존재하는지
- ExternalSecret 상태가 `Ready`인지: `kubectl -n seedtest get externalsecret -o wide`

### 3. Alembic 마이그레이션

```bash
# 마이그레이션 확인
kubectl -n seedtest exec -it deployment/seedtest-api -- python -m alembic current

# 새 마이그레이션 적용
kubectl -n seedtest exec -it deployment/seedtest-api -- python -m alembic upgrade head

# 테이블 생성 확인
kubectl -n seedtest exec -it deployment/seedtest-api -- python -c "
from apps.seedtest_api.services.db import get_session
from sqlalchemy import inspect
with get_session() as conn:
    inspector = inspect(conn.bind)
    tables = ['growth_brms_meta', 'prophet_fit_meta', 'prophet_anomalies', 'survival_fit_meta', 'survival_risk']
    for t in tables:
        print(f'{t}: {inspector.has_table(t)}')
"
```

**필요한 테이블:**
- `growth_brms_meta` (베이지안 성장 모델 메타)
- `prophet_fit_meta` (Prophet 적합 메타)
- `prophet_anomalies` (Prophet 이상치)
- `survival_fit_meta` (생존 분석 메타)
- `survival_risk` (사용자별 생존 위험 점수)

### 4. seedtest-api 설정

```bash
# Deployment 환경 변수 확인/업데이트
kubectl -n seedtest get deployment seedtest-api -o jsonpath='{.spec.template.spec.containers[0].env}' | jq

# 환경 변수 추가/수정
kubectl -n seedtest set env deployment/seedtest-api \
  METRICS_USE_BAYESIAN=true \
  METRICS_DEFAULT_TARGET=0.0 \
  CHURN_ALERT_THRESHOLD=0.7

# 재시작
kubectl -n seedtest rollout restart deployment/seedtest-api
```

**필수 환경 변수:**
- `METRICS_USE_BAYESIAN=true` (베이지안 모델 활성화)
- `METRICS_DEFAULT_TARGET=0.0` (목표 달성 기준, 옵션)
- `CHURN_ALERT_THRESHOLD=0.7` (이탈 위험 임계값, 옵션)

### 5. Cron 적용

```bash
# CronJob 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-bayesian-growth.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/forecast-prophet.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-survival-churn.yaml

# CronJob 상태 확인
kubectl -n seedtest get cronjobs
```

**기존 CronJob (이미 적용됨):**
- `compute-daily-kpis` (주간 KPI 계산)
- `aggregate-features-daily` (일일 피처 집계)

---

## 🔍 스모크/검증

### 1. 서비스 헬스 체크

```bash
# r-brms-plumber
kubectl -n seedtest port-forward svc/r-brms-plumber 8000:8000 &
curl http://localhost:8000/healthz

# r-forecast-plumber
kubectl -n seedtest port-forward svc/r-forecast-plumber 8001:8000 &
curl http://localhost:8001/healthz

# 또는 Pod 내부에서 직접 호출
kubectl -n seedtest exec -it deployment/r-brms-plumber -- curl http://localhost:8000/healthz
kubectl -n seedtest exec -it deployment/r-forecast-plumber -- curl http://localhost:8000/healthz
```

**예상 응답:**
- HTTP 200
- `{"status":"ok","engine":"brms"}` 또는 `{"status":"ok","engine":"forecast"}`

### 2. 베이지안 KPI (P) 검증

```bash
# 수동 Job 실행
kubectl -n seedtest create job --from=cronjob/fit-bayesian-growth fit-bayesian-growth-smoke-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/fit-bayesian-growth-smoke-<timestamp> --tail=100

# weekly_kpi.P 업데이트 확인
kubectl -n seedtest exec -it deployment/seedtest-api -- python -c "
from apps.seedtest_api.services.db import get_session
from sqlalchemy import text
with get_session() as conn:
    result = conn.execute(text('''
        SELECT user_id, week_start, P, COUNT(*) as cnt
        FROM weekly_kpi
        WHERE P IS NOT NULL AND P BETWEEN 0 AND 1
        GROUP BY user_id, week_start, P
        ORDER BY week_start DESC
        LIMIT 10
    ''')).fetchall()
    for row in result:
        print(row)
"
```

**확인 사항:**
- `fit_bayesian_growth.py`가 성공적으로 완료되었는지
- `growth_brms_meta` 테이블에 posterior 메타가 저장되었는지
- `weekly_kpi.P` 컬럼이 0..1 범위 값으로 채워졌는지

### 3. Prophet 검증

```bash
# 수동 Job 실행
kubectl -n seedtest create job --from=cronjob/forecast-prophet forecast-prophet-smoke-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/forecast-prophet-smoke-<timestamp> --tail=100

# prophet_fit_meta 저장 확인
kubectl -n seedtest exec -it deployment/seedtest-api -- python -c "
from apps.seedtest_api.services.db import get_session
from sqlalchemy import text
with get_session() as conn:
    result = conn.execute(text('''
        SELECT user_id, fit_id, horizon_weeks, rmse, mae, created_at
        FROM prophet_fit_meta
        ORDER BY created_at DESC
        LIMIT 5
    ''')).fetchall()
    for row in result:
        print(row)
    
    anomaly_count = conn.execute(text('SELECT COUNT(*) FROM prophet_anomalies')).scalar()
    print(f'Total anomalies: {anomaly_count}')
"
```

**확인 사항:**
- `forecast_prophet.py`가 성공적으로 완료되었는지
- `prophet_fit_meta`에 적합 메타가 저장되었는지
- `prophet_anomalies`에 이상치가 탐지되었는지 (있을 경우)

### 4. Survival 검증

```bash
# 수동 Job 실행
kubectl -n seedtest create job --from=cronjob/fit-survival-churn survival-smoke-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/survival-smoke-<timestamp> --tail=100

# survival_risk 저장 확인
kubectl -n seedtest exec -it deployment/seedtest-api -- python -c "
from apps.seedtest_api.services.db import get_session
from sqlalchemy import text
with get_session() as conn:
    result = conn.execute(text('''
        SELECT user_id, risk_score, hazard_ratio, rank_percentile, updated_at
        FROM survival_risk
        ORDER BY risk_score DESC
        LIMIT 10
    ''')).fetchall()
    for row in result:
        print(row)
    
    # weekly_kpi.S 업데이트 확인
    kpi_count = conn.execute(text('''
        SELECT COUNT(*) FROM weekly_kpi WHERE S IS NOT NULL AND S BETWEEN 0 AND 1
    ''')).scalar()
    print(f'Weekly KPI with S: {kpi_count}')
"
```

**확인 사항:**
- `fit_survival_churn.py`가 성공적으로 완료되었는지
- `survival_fit_meta`에 모델 메타가 저장되었는지
- `survival_risk`에 사용자별 위험 점수가 저장되었는지
- `weekly_kpi.S` 컬럼이 0..1 범위 값으로 갱신되었는지

### 5. 리포트 생성 검증

```bash
# 리포트 생성 Job 실행 (기존 CronJob 또는 수동)
kubectl -n seedtest create job --from=cronjob/generate-weekly-report report-smoke-$(date +%s)

# 로그 확인
kubectl -n seedtest logs -f job/report-smoke-<timestamp> --tail=100

# 리포트 URL 확인
kubectl -n seedtest exec -it deployment/seedtest-api -- python -c "
from apps.seedtest_api.services.db import get_session
from sqlalchemy import text
with get_session() as conn:
    result = conn.execute(text('''
        SELECT user_id, week_start, report_url, created_at
        FROM weekly_report
        ORDER BY created_at DESC
        LIMIT 5
    ''')).fetchall()
    for row in result:
        print(row)
"
```

**확인 사항:**
- `weekly_report.qmd` 템플릿이 정상적으로 렌더링되었는지
- 베이지안 신뢰대역/게이지가 표시되는지
- Prophet 예측/이상치 플롯이 포함되는지
- Survival 위험 게이지/생존곡선이 포함되는지
- S3 업로드 및 DB URL 저장이 성공했는지

---

## ⚙️ 운영 파라미터 (기본값)

### 베이지안 모델

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `LOOKBACK_WEEKS` | `12` | 성장 모델 학습 기간 (주) |
| `BRMS_ITER` | `1000~2000` | MCMC 반복 횟수 |
| `BRMS_CHAINS` | `2~4` | MCMC 체인 수 |
| `BRMS_FAMILY` | `gaussian` | 분포 가족 (gaussian, lognormal 등) |

**CronJob 스케줄:** `0 2 * * 1` (매주 월요일 02:00)

### Prophet 모델

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `PROPHET_LOOKBACK_WEEKS` | `12` | 시계열 입력 기간 (주) |
| `PROPHET_FORECAST_WEEKS` | `4` | 예측 기간 (주) |
| `PROPHET_ANOMALY_THRESHOLD` | `2.5` | 이상치 탐지 임계값 (표준편차) |

**CronJob 스케줄:** `0 3 * * 1` (매주 월요일 03:00)

### Survival 모델

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `SURVIVAL_LOOKBACK_DAYS` | `90` | 관찰 기간 (일) |
| `SURVIVAL_EVENT_THRESHOLD_DAYS` | `14` | 이벤트 정의 임계값 (일, 미접속) |
| `SURVIVAL_UPDATE_KPI` | `true` | weekly_kpi.S 자동 갱신 여부 |

**CronJob 스케줄:** `0 4 * * 1` (매주 월요일 04:00)

### 알림 로직

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `CHURN_ALERT_THRESHOLD` | `0.7` | 이탈 위험 임계값 (0.6~0.8 권장) |

**동작:**
- `weekly_kpi.S >= CHURN_ALERT_THRESHOLD`일 때 `alert_queue`에 이벤트 기록
- 부모/교사 알림 트리거 용도

---

## 📊 모니터링/롤백

### ServiceMonitor 확인

```bash
# Prometheus 타겟 상태 확인
kubectl -n seedtest get servicemonitor
kubectl -n monitoring get prometheus -o yaml | grep -A 10 serviceMonitorSelector

# 스크레이프 상태 확인 (Prometheus UI 또는 쿼리)
# prometheus.io/scrape: "true" 레이블 확인
kubectl -n seedtest get svc -l app=r-brms-plumber -o yaml | grep -A 5 prometheus.io
```

### CronJob 모니터링

```bash
# Job 실행 이력 확인
kubectl -n seedtest get jobs --sort-by=.metadata.creationTimestamp | tail -20

# 성공률 확인
kubectl -n seedtest get cronjobs fit-bayesian-growth -o jsonpath='{.status.lastScheduleTime}'
kubectl -n seedtest get jobs -l job-name=fit-bayesian-growth-* --sort-by=.status.startTime

# 로그 집계 (예: 실패 원인 분석)
kubectl -n seedtest logs -l job-name=fit-bayesian-growth-* --tail=50 | grep -i error
```

**알람 설정 권장:**
- CronJob 실패 횟수 임계값 (예: 연속 3회 실패)
- Job 완료 시간 임계값 (예: 30분 초과)
- 잔여 TTL 후 자동 정리 확인

### 롤백 절차

#### 1. 즉시 폴백 (환경 변수)

```bash
# 베이지안 모델 비활성화
kubectl -n seedtest set env deployment/seedtest-api METRICS_USE_BAYESIAN=false
kubectl -n seedtest rollout restart deployment/seedtest-api

# CronJob 일시 중지
kubectl -n seedtest patch cronjob fit-bayesian-growth -p '{"spec":{"suspend":true}}'
kubectl -n seedtest patch cronjob forecast-prophet -p '{"spec":{"suspend":true}}'
kubectl -n seedtest patch cronjob fit-survival-churn -p '{"spec":{"suspend":true}}'
```

#### 2. 마이그레이션 롤백

```bash
# 특정 마이그레이션으로 다운그레이드
kubectl -n seedtest exec -it deployment/seedtest-api -- python -m alembic downgrade <revision>

# 예: prophet/survival 테이블 제거
kubectl -n seedtest exec -it deployment/seedtest-api -- python -m alembic downgrade -1
```

#### 3. 리소스 제거 (필요시)

```bash
# CronJob 삭제
kubectl -n seedtest delete cronjob fit-bayesian-growth
kubectl -n seedtest delete cronjob forecast-prophet
kubectl -n seedtest delete cronjob fit-survival-churn

# R 서비스 비활성화
kubectl -n seedtest scale deployment/r-brms-plumber --replicas=0
kubectl -n seedtest scale deployment/r-forecast-plumber --replicas=0
```

---

## 🚀 권장 후속 작업

### 1. 리포트 시각화 강화

**파일:** `reports/quarto/weekly_report.qmd`

- [x] 베이지안 신뢰대역/게이지 블록 추가 (완료)
- [x] Prophet 예측/이상치 플롯 추가 (완료)
- [x] Survival 위험 게이지/생존곡선 추가 (완료)

**추가 개선:**
- 세그먼트별 학습 패턴 비교 차트
- 코호트별 생존곡선 오버레이
- 예측 신뢰도 지표 표시

### 2. 세그먼테이션/추천 결합

**목표:**
- 세그먼트별 추천 전략 자동 선택
- 세그먼트별 스케줄 가중치 조정
- 세그먼트별 난이도 적응화

**구현 예정:**
- `r-cluster-plumber` 또는 `r-forecast-plumber`에 `/cluster/fit` 엔드포인트 추가
- `apps/seedtest_api/jobs/cluster_segments.py` 완성
- `apps/seedtest_api/services/decision.py`에서 세그먼트 기반 전략 선택 로직 추가

### 3. Anchors 링크 고도화

**목표:**
- Stocking-Lord 방법 구현
- Haebara 방법 구현
- 리포트에 링크 메타 강화

**구현 예정:**
- `r-irt-plumber/api.R`에 `/irt/link` 엔드포인트 추가
- `apps/seedtest_api/jobs/link_anchors.py` 생성
- `weekly_report.qmd`에 링크 메타 시각화 추가

---

## 🔧 트러블슈팅 가이드

### 문제: 시계열 입력 공백

**증상:**
- Prophet Job 실패: "insufficient data points"
- `forecast_prophet.py` 에러: "Series has less than 2 data points"

**해결:**
- `PROPHET_LOOKBACK_WEEKS` 증가 (예: 12 → 16)
- 최소 데이터 포인트 필터링 추가 (예: 4주 이상)
- `weekly_kpi` 백필 확인

### 문제: 이벤트 데이터 부족

**증상:**
- Survival Job 실패: "No events detected"
- `fit_survival_churn.py` 경고: "Concordance is undefined"

**해결:**
- `SURVIVAL_LOOKBACK_DAYS` 증가 (예: 90 → 120)
- `SURVIVAL_EVENT_THRESHOLD_DAYS` 조정 (예: 14 → 21)
- 최소 이벤트 수 필터링 추가 (예: 10명 이상)

### 문제: R 서비스 타임아웃

**증상:**
- `r-brms-plumber` 504 Gateway Timeout
- `fit_bayesian_growth.py` 에러: "Request timeout"

**해결:**
- `BRMS_ITER` 감소 (예: 2000 → 1000)
- `BRMS_CHAINS` 감소 (예: 4 → 2)
- R 서비스 리소스 증가 (CPU/Memory)

### 문제: 이미지 Pull 실패

**증상:**
- Pod `ImagePullBackOff` 상태
- `ErrImagePull`: "pull access denied"

**해결:**
- GCP 인증 확인: `gcloud auth configure-docker asia-northeast3-docker.pkg.dev`
- 이미지 태그 확인: `:latest` vs `:staging`
- Deployment 이미지 경로 확인

---

## 📝 체크리스트 요약

배포 전:
- [ ] Docker 이미지 빌드 및 푸시 완료
- [ ] K8s 리소스 (Deployment/Service/ServiceMonitor) 적용 완료
- [ ] ExternalSecret 동기화 확인
- [ ] Alembic 마이그레이션 적용 완료
- [ ] 환경 변수 설정 완료
- [ ] CronJob 매니페스트 적용 완료

배포 후:
- [ ] R 서비스 헬스 체크 통과
- [ ] 베이지안 KPI (P) 정상 업데이트 확인
- [ ] Prophet 메타/이상치 저장 확인
- [ ] Survival 위험 점수 저장 및 KPI 갱신 확인
- [ ] 리포트 생성 및 시각화 확인

운영:
- [ ] ServiceMonitor 타겟 상태 확인
- [ ] CronJob 성공률 모니터링 설정
- [ ] 알람 규칙 설정 완료
- [ ] 롤백 절차 문서화 및 테스트 완료

