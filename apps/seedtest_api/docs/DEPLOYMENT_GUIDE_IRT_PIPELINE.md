# IRT 파이프라인 배포 가이드

**최종 업데이트**: 2025-11-01  
**상태**: Production Ready

---

## 🎯 배포 완료 항목

### ✅ 1. IRT Calibration Job
- **파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`
- **기능**: 관측 추출 → R IRT 호출 → DB 업데이트
- **개선사항**:
  - 재시도 로직 (최대 3회, 지수 백오프)
  - 앵커 문항 자동 로드
  - Dry-run 모드

### ✅ 2. Anchor Tagging Job
- **파일**: `apps/seedtest_api/jobs/tag_anchor_items.py`
- **기능**: 안정적인 문항 자동 선정 및 태깅
- **개선사항**:
  - CLI 인터페이스 (argparse)
  - 상세한 후보 검색 로직
  - 안정성 검증 (difficulty variance)

### ✅ 3. GLMM Growth Model
- **파일**: `apps/seedtest_api/jobs/fit_growth_glmm.py`
- **CronJob**: `portal_front/ops/k8s/cron/fit-growth-glmm.yaml`
- **가이드**: `apps/seedtest_api/docs/R_GLMM_SERVICE_GUIDE.md`

### ✅ 4. Quarto Report θ Section
- **템플릿**: `reports/quarto/weekly_report.qmd`
- **Job**: `apps/seedtest_api/jobs/generate_weekly_report.py`
- **추가 섹션**: θ 트렌드, 능력 통계, 문항 난이도 분포

---

## 🚀 배포 순서

### Phase 1: R IRT 서비스 확인 (사전 준비)

```bash
# 1. R IRT Plumber 서비스 상태 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 2. Health check
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl http://r-irt-plumber.seedtest.svc.cluster.local:80/health

# 예상 응답: {"status": "ok", "version": "1.0.0"}
```

**R IRT 서비스가 없는 경우**:
- `apps/seedtest_api/docs/IRT_CALIBRATION_GUIDE.md` 참고하여 R Plumber 서비스 구현
- 또는 기존 R IRT 서비스에 anchors 파라미터 처리 추가

---

### Phase 2: 앵커 문항 태깅

```bash
# 1. Dry-run으로 후보 확인
kubectl -n seedtest run tag-anchors-dryrun \
  --image=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest \
  --rm -it --restart=Never \
  --env="DATABASE_URL=postgresql://..." \
  --env="DRY_RUN=true" \
  -- python -m apps.seedtest_api.jobs.tag_anchor_items

# 2. 실제 태깅 (로컬 또는 임시 Pod)
kubectl -n seedtest run tag-anchors \
  --image=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest \
  --rm -it --restart=Never \
  --env="DATABASE_URL=postgresql://..." \
  -- python -m apps.seedtest_api.jobs.tag_anchor_items \
  --min-responses 100 \
  --discrimination-min 0.8 \
  --max-candidates 50

# 3. 검증
kubectl -n seedtest run verify-anchors \
  --image=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest \
  --rm -it --restart=Never \
  --env="DATABASE_URL=postgresql://..." \
  -- python -m apps.seedtest_api.jobs.tag_anchor_items verify
```

**예상 출력**:
```
[SEARCH] Finding anchor candidates...
[FOUND] 150 candidates, selecting top 50
[TAG] Tagging 50 items as anchors...
✅ Results:
  - Tagged: 48
  - Skipped (already tagged): 2
  - Errors: 0
✅ Tagging complete!
```

---

### Phase 3: IRT Calibration Dry-run

```bash
# 1. CronJob 배포 (DRY_RUN=true)
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/mirt-calibrate.yaml

# 2. 수동 Dry-run 실행
kubectl -n seedtest set env cronjob/mirt-calibrate DRY_RUN=true
kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-dryrun-$(date +%s)

# 3. 로그 확인
kubectl -n seedtest logs -f job/mirt-calibrate-dryrun-<timestamp>
```

**예상 출력**:
```
[INFO] Loaded 12345 observations from attempt VIEW
[INFO] Loaded 50 anchors/seeds from question.meta
[INFO] Total observations: 12345
[INFO] Model: 2PL, Anchors: 50
[DRY_RUN] Skipping R IRT service call and DB updates
[DRY_RUN] Would calibrate 12345 observations with 50 anchors
```

---

### Phase 4: IRT Calibration 실제 실행

```bash
# 1. DRY_RUN 비활성화
kubectl -n seedtest set env cronjob/mirt-calibrate DRY_RUN=false

# 2. 수동 실행 (첫 번째 실제 calibration)
kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-prod-$(date +%s)

# 3. 로그 모니터링 (5-10분 소요)
kubectl -n seedtest logs -f job/mirt-calibrate-prod-<timestamp>
```

**예상 출력**:
```
[INFO] Loaded 12345 observations from attempt VIEW
[INFO] Loaded 50 anchors/seeds from question.meta
[INFO] Total observations: 12345
[INFO] Model: 2PL, Anchors: 50
[INFO] Calling R IRT service...
[INFO] Linking constants received: ['slope', 'intercept']
Calibration upsert completed: 150 items, 500 abilities
Linking constants stored in fit_meta.model_spec.linking_constants
✅ IRT calibration completed successfully
```

**재시도 로직 작동 예시**:
```
[WARN] R IRT service call failed (attempt 1/3): Connection timeout
[INFO] Retrying in 5.0 seconds...
[INFO] Calling R IRT service...
[INFO] Linking constants received: ['slope', 'intercept']
✅ IRT calibration completed successfully
```

---

### Phase 5: 결과 검증

```sql
-- 1. mirt_item_params 확인
SELECT 
    COUNT(*) AS total_items,
    AVG((params->>'a')::float) AS avg_discrimination,
    AVG((params->>'b')::float) AS avg_difficulty,
    MAX(fitted_at) AS last_fitted
FROM mirt_item_params;

-- 예상 결과
-- total_items | avg_discrimination | avg_difficulty | last_fitted
-- ------------|-------------------|----------------|-------------
-- 150         | 1.15              | 0.05           | 2025-11-01 03:15:23

-- 2. mirt_ability 확인
SELECT 
    COUNT(*) AS total_users,
    AVG(theta) AS avg_theta,
    STDDEV(theta) AS sd_theta,
    MAX(fitted_at) AS last_fitted
FROM mirt_ability;

-- 예상 결과
-- total_users | avg_theta | sd_theta | last_fitted
-- ------------|-----------|----------|-------------
-- 500         | 0.02      | 0.98     | 2025-11-01 03:15:23

-- 3. mirt_fit_meta 확인 (linking constants)
SELECT 
    run_id,
    model_spec->>'model' AS model,
    model_spec->>'n_items' AS n_items,
    model_spec->>'n_users' AS n_users,
    model_spec->'linking_constants' AS linking_constants,
    metrics->>'aic' AS aic,
    fitted_at
FROM mirt_fit_meta
ORDER BY fitted_at DESC
LIMIT 1;

-- 예상 결과
-- run_id                   | model | n_items | n_users | linking_constants              | aic      | fitted_at
-- -------------------------|-------|---------|---------|--------------------------------|----------|----------
-- fit-2025-11-01T03:15:23Z | 2PL   | 150     | 500     | {"slope":1.02,"intercept":0.05}| 12345.67 | 2025-11-01 03:15:23

-- 4. 앵커 문항 확인
SELECT 
    q.id,
    q.meta->'tags' AS tags,
    p.params->>'a' AS discrimination,
    p.params->>'b' AS difficulty
FROM question q
INNER JOIN mirt_item_params p ON q.id::text = p.item_id
WHERE q.meta->'tags' @> '["anchor"]'::jsonb
LIMIT 10;
```

---

### Phase 6: GLMM Growth Model 배포

```bash
# 1. R GLMM Plumber 서비스 배포 (가이드 참고)
# apps/seedtest_api/docs/R_GLMM_SERVICE_GUIDE.md 참고하여 구현

# 2. GLMM CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/fit-growth-glmm.yaml

# 3. 수동 테스트
kubectl -n seedtest create job --from=cronjob/fit-growth-glmm \
  fit-growth-glmm-test-$(date +%s)

# 4. 로그 확인
kubectl -n seedtest logs -f job/fit-growth-glmm-test-<timestamp>
```

---

### Phase 7: Quarto 리포트 생성 테스트

```bash
# 1. 리포트 생성 CronJob 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml

# 2. 수동 테스트
kubectl -n seedtest create job --from=cronjob/generate-weekly-report \
  generate-weekly-report-test-$(date +%s)

# 3. 로그 확인
kubectl -n seedtest logs -f job/generate-weekly-report-test-<timestamp>
```

**리포트 확인**:
```sql
-- report_artifacts 테이블 확인
SELECT 
    user_id,
    week_start,
    format,
    url,
    generated_at
FROM report_artifacts
ORDER BY generated_at DESC
LIMIT 10;
```

---

## 📊 모니터링 및 알림

### CloudWatch/Stackdriver 메트릭

```yaml
# 모니터링할 메트릭
- cronjob_success_count{job="mirt-calibrate"}
- cronjob_duration_seconds{job="mirt-calibrate"}
- cronjob_failure_count{job="mirt-calibrate"}
```

### 알림 설정 (예시)

```yaml
# AlertManager 규칙
- alert: IRTCalibrationFailed
  expr: cronjob_failure_count{job="mirt-calibrate"} > 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "IRT Calibration job failed"
    description: "mirt-calibrate job has failed {{ $value }} times"

- alert: IRTCalibrationSlow
  expr: cronjob_duration_seconds{job="mirt-calibrate"} > 1800
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "IRT Calibration is taking too long"
    description: "mirt-calibrate job took {{ $value }}s (>30min)"
```

---

## 🔄 일일 운영 체크리스트

### 매일 아침 (09:00 KST)

```bash
# 1. 어젯밤 Calibration 성공 여부 확인
kubectl -n seedtest get jobs -l job-name=mirt-calibrate --sort-by=.metadata.creationTimestamp

# 2. 최근 로그 확인
kubectl -n seedtest logs -l job-name=mirt-calibrate --tail=100 --timestamps

# 3. DB 확인
psql $DATABASE_URL -c "
SELECT 
    'mirt_item_params' AS table_name,
    COUNT(*) AS count,
    MAX(fitted_at) AS last_update
FROM mirt_item_params
UNION ALL
SELECT 
    'mirt_ability',
    COUNT(*),
    MAX(fitted_at)
FROM mirt_ability;
"
```

### 매주 월요일 (10:00 KST)

```bash
# 1. 주간 리포트 생성 확인
kubectl -n seedtest get jobs -l job-name=generate-weekly-report --sort-by=.metadata.creationTimestamp

# 2. 리포트 URL 확인
psql $DATABASE_URL -c "
SELECT user_id, week_start, url, generated_at
FROM report_artifacts
WHERE generated_at >= NOW() - INTERVAL '1 day'
ORDER BY generated_at DESC
LIMIT 20;
"

# 3. GLMM 모델 결과 확인
psql $DATABASE_URL -c "
SELECT run_id, fitted_at, fit_metrics
FROM growth_glmm_meta
ORDER BY fitted_at DESC
LIMIT 5;
"
```

---

## 🐛 문제 해결

### 문제 1: R IRT 서비스 연결 실패

**증상**:
```
[WARN] R IRT service call failed (attempt 1/3): Connection refused
[WARN] R IRT service call failed (attempt 2/3): Connection refused
[WARN] R IRT service call failed (attempt 3/3): Connection refused
[ERROR] R IRT service call failed after 3 attempts
```

**해결**:
```bash
# 1. R IRT 서비스 상태 확인
kubectl -n seedtest get pods -l app=r-irt-plumber
kubectl -n seedtest logs -l app=r-irt-plumber --tail=50

# 2. 서비스 재시작
kubectl -n seedtest rollout restart deployment/r-irt-plumber

# 3. 연결 테스트
kubectl -n seedtest run curl-test --image=curlimages/curl:latest --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/health
```

---

### 문제 2: 관측 데이터 없음

**증상**:
```
[INFO] Loaded 0 observations from attempt VIEW
[WARN] No observations found; exiting.
```

**해결**:
```sql
-- 1. attempt VIEW 확인
SELECT COUNT(*) FROM attempt WHERE completed_at >= NOW() - INTERVAL '30 days';

-- 2. 데이터가 없으면 LOOKBACK_DAYS 증가
-- mirt-calibrate.yaml에서 MIRT_LOOKBACK_DAYS=60 또는 90으로 변경

-- 3. 폴백 테이블 확인
SELECT COUNT(*) FROM responses WHERE responded_at >= NOW() - INTERVAL '30 days';
```

---

### 문제 3: 앵커 문항 없음

**증상**:
```
[INFO] Loaded 0 anchors/seeds from question.meta
```

**해결**:
```bash
# 앵커 태깅 실행
kubectl -n seedtest run tag-anchors \
  --image=asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-api:latest \
  --rm -it --restart=Never \
  --env="DATABASE_URL=postgresql://..." \
  -- python -m apps.seedtest_api.jobs.tag_anchor_items \
  --max-candidates 50
```

---

### 문제 4: Linking constants 품질 낮음

**증상**:
```sql
SELECT model_spec->'linking_constants' FROM mirt_fit_meta ORDER BY fitted_at DESC LIMIT 1;
-- {"slope": 1.5, "intercept": 0.8}  -- 너무 큰 변환
```

**해결**:
```bash
# 1. 앵커 문항 재선정 (더 엄격한 기준)
python -m apps.seedtest_api.jobs.tag_anchor_items \
  --min-responses 200 \
  --discrimination-min 1.0 \
  --difficulty-min -1.0 \
  --difficulty-max 1.0

# 2. 앵커 검증
python -m apps.seedtest_api.jobs.tag_anchor_items verify

# 3. Calibration 재실행
kubectl -n seedtest create job --from=cronjob/mirt-calibrate \
  mirt-calibrate-refit-$(date +%s)
```

---

## 📚 관련 문서

- `IRT_CALIBRATION_GUIDE.md` - IRT Calibration 완전 가이드
- `R_GLMM_SERVICE_GUIDE.md` - GLMM R 서비스 구현 가이드
- `ADVANCED_ANALYTICS_ROADMAP.md` - 전체 Analytics 로드맵
- `IRT_ONLINE_UPDATE_GUIDE.md` - θ 온라인 업데이트 가이드

---

## ✅ 배포 완료 체크리스트

- [ ] R IRT Plumber 서비스 배포 및 Health check
- [ ] 앵커 문항 태깅 (50개 선정)
- [ ] IRT Calibration Dry-run 테스트
- [ ] IRT Calibration 실제 실행 및 검증
- [ ] mirt_item_params, mirt_ability, mirt_fit_meta 확인
- [ ] Linking constants 품질 확인
- [ ] GLMM Growth Model 배포 (선택)
- [ ] Quarto 리포트 생성 테스트
- [ ] 모니터링 및 알림 설정
- [ ] 일일/주간 운영 체크리스트 수립

---

**최종 업데이트**: 2025-11-01  
**작성자**: Cascade AI  
**상태**: Production Ready - 즉시 배포 가능
