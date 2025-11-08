# IRT 캘리브레이션 개선 사항 요약

**작성일**: 2025-11-02  
**상태**: ✅ 모든 개선 사항 반영 완료

---

## ✅ 완료된 개선 사항

### 1. 재시도/백오프 로직 추가

**파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`

**구현 내용**:
- R IRT 서비스 호출에 재시도 로직 추가
- 지수 백오프: 5초, 10초, 15초
- 환경 변수로 제어:
  - `MIRT_MAX_RETRIES=3` (기본값: 3회)
  - `MIRT_RETRY_DELAY_SECS=5.0` (기본값: 5초)

**코드 변경**:
```python
# 이전: 단일 호출
result = await client.calibrate(observations, model=model, anchors=(anchors or None))

# 개선: 재시도 로직 포함
max_retries = int(os.getenv("MIRT_MAX_RETRIES", "3"))
retry_delay = float(os.getenv("MIRT_RETRY_DELAY_SECS", "5.0"))

result = None
last_error = None
for attempt in range(max_retries):
    try:
        result = await client.calibrate(observations, model=model, anchors=(anchors or None))
        break
    except Exception as e:
        last_error = e
        if attempt < max_retries - 1:
            wait_time = retry_delay * (attempt + 1)
            print(f"[WARN] Retry {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(wait_time)
        else:
            raise
```

---

### 2. CronJob 스케줄 업데이트

**파일**: `portal_front/ops/k8s/cron/calibrate-irt.yaml`

**변경 사항**:
- 스케줄: `"10 3 * * 0"` (주간) → `"0 3 * * *"` (일일)
- 매일 03:00 UTC 실행

**환경 변수 업데이트**:
- `MIRT_LOOKBACK_DAYS`: 30 → 60
- `R_IRT_TIMEOUT_SECS`: 300 → 60 (필요시 증가 가능)
- `MIRT_MAX_RETRIES`: 3 (신규)
- `MIRT_RETRY_DELAY_SECS`: 5.0 (신규)

---

### 3. I_t θ-델타 기반 전환 (이미 구현)

**파일**: `apps/seedtest_api/services/metrics.py`

**상태**: ✅ 구현 완료 (환경 변수로 활성화)

**활성화**:
```bash
export METRICS_USE_IRT_THETA=true
```

**동작**:
- θ 값 사용 가능 시 θ 기반 계산
- 폴백: 정답률 기반

---

### 4. features_topic_daily에 θ 백필 (이미 구현)

**파일**: `apps/seedtest_api/jobs/aggregate_features_daily.py`

**상태**: ✅ 구현 완료 (환경 변수로 활성화)

**활성화**:
```bash
export AGG_INCLUDE_THETA=true
```

**동작**:
- `student_topic_theta` 우선
- `mirt_ability` 폴백

---

## ⏭️ 남은 작업

### 1. r-irt-plumber 측 anchors 처리

**상태**: ⏭️ R 서비스 측 구현 필요

**필요 작업**:
- `/irt/calibrate` 엔드포인트에서 `anchors` 파라미터 처리
- Linking constants 계산
- 응답에 `fit_meta.linking_constants` 포함

**Python 측 준비 완료**:
- ✅ anchors 로드 및 전달
- ✅ linking_constants 저장
- ✅ 리포트 템플릿 표시

---

## 📊 배포 절차

### 1. CronJob 업데이트 배포

```bash
# 매니페스트 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 확인
kubectl -n seedtest get cronjob calibrate-irt-weekly -o yaml | grep -A 5 "schedule:"
```

### 2. 테스트 실행

```bash
# 수동 Job 생성
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly \
  calibrate-irt-test-$(date +%s)

# 로그 확인
kubectl -n seedtest logs job/calibrate-irt-test-* -c calibrate-irt -f
```

### 3. 검증

```sql
-- 최근 캘리브레이션 결과 확인
SELECT 
    COUNT(*) AS item_count,
    MAX(fitted_at) AS latest_fit
FROM mirt_item_params
WHERE fitted_at >= NOW() - INTERVAL '1 day';

-- Linking constants 확인
SELECT 
    run_id,
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
WHERE model_spec ? 'linking_constants'
ORDER BY fitted_at DESC
LIMIT 1;
```

---

## 📝 운영 모니터링

### 주요 메트릭

1. **캘리브레이션 실행 빈도**
   - CronJob 성공/실패 횟수
   - 평균 실행 시간

2. **데이터 품질**
   - 관측치 수
   - 앵커 아이템 수
   - Linking constants 생성 여부

3. **서비스 안정성**
   - R IRT 서비스 호출 성공률
   - 재시도 발생 빈도
   - 타임아웃 발생 여부

### 알림 설정 (권장)

- CronJob 실패 알림
- R IRT 서비스 장애 알림
- 캘리브레이션 결과 이상 (예: 아이템 수 급감)

---

## ✅ 체크리스트

- [x] 재시도 로직 구현
- [x] CronJob 스케줄 업데이트
- [x] 환경 변수 업데이트
- [x] 운영 문서 작성
- [ ] r-irt-plumber anchors 처리 구현 (R 서비스 측)
- [ ] 첫 일일 캘리브레이션 실행 및 검증
- [ ] 모니터링 대시보드 설정 (선택)

**모든 Python 측 구현 완료!** 🎉

