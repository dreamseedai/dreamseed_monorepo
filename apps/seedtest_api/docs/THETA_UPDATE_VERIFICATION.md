# θ 온라인 업데이트 검증 가이드

**작성일**: 2025-11-01

## 개요

세션 종료 시 자동으로 트리거되는 θ 온라인 업데이트가 정상 작동하는지 검증하는 방법입니다.

## 구현 상태

### ✅ 완료된 구현

1. **자동 트리거**
   - `apps/seedtest_api/services/result_service.py`: `finish_exam()` 함수에 통합
   - 백그라운드 실행 (비차단)

2. **업데이트 서비스**
   - `apps/seedtest_api/services/irt_update_service.py`
   - EAP 추정 및 `mirt_ability` 업데이트

3. **검증 유틸리티**
   - `apps/seedtest_api/services/theta_online_verification.py`

## 검증 방법

### 1. 최근 업데이트 확인

```bash
# Python 스크립트 실행
python -m apps.seedtest_api.services.theta_online_verification --hours 24

# 또는 DB 직접 쿼리
psql $DATABASE_URL -c "
SELECT 
    user_id,
    theta,
    se,
    fitted_at
FROM mirt_ability
WHERE fitted_at >= NOW() - INTERVAL '24 hours'
ORDER BY fitted_at DESC
LIMIT 10;
"
```

### 2. 특정 사용자 검증

```bash
# 검증 스크립트 사용
python -m apps.seedtest_api.services.theta_online_verification --user-id user123

# 또는 DB 쿼리
psql $DATABASE_URL -c "
SELECT 
    ma.user_id,
    ma.theta,
    ma.se,
    ma.fitted_at,
    (SELECT COUNT(*) FROM attempt WHERE student_id::text = ma.user_id AND completed_at >= NOW() - INTERVAL '7 days') AS recent_attempts
FROM mirt_ability ma
WHERE ma.user_id = 'user123'
ORDER BY ma.fitted_at DESC
LIMIT 1;
"
```

### 3. 세션 완료 로그 확인

```bash
# K8s Pod 로그에서 트리거 확인
kubectl -n seedtest logs -l app=seedtest-api | grep -i "trigger_ability_update" | tail -20

# 또는 특정 Pod
POD=$(kubectl -n seedtest get pods -l app=seedtest-api -o jsonpath='{.items[0].metadata.name}')
kubectl -n seedtest logs $POD | grep -i "trigger_ability_update" | tail -10
```

### 4. 수동 트리거 테스트

```python
# Python 인터랙티브 셸
from apps.seedtest_api.services.irt_update_service import trigger_ability_update

# 백그라운드 실행
trigger_ability_update("user123", "session456", background=True)

# 동기 실행 (테스트용)
from apps.seedtest_api.services.irt_update_service import update_ability_sync
theta, se = update_ability_sync("user123")
print(f"Theta: {theta}, SE: {se}")
```

## 검증 체크리스트

- [ ] 최근 24시간 내 `mirt_ability` 업데이트 확인
- [ ] 세션 완료 로그에서 `trigger_ability_update` 호출 확인
- [ ] R IRT 서비스 연결 확인 (로그 확인)
- [ ] 업데이트 실패 시 에러 로그 확인 (에러가 세션 완료를 막지 않는지 확인)

## 문제 해결

### 능력 업데이트가 실행되지 않음

**확인 사항**:
1. `user_id`가 `finish_exam()`에 전달되는지 확인
2. `irt_update_service` import 에러 없는지 확인
3. 백그라운드 스레드가 시작되는지 확인

**해결**:
```python
# result_service.py에서 로그 추가
print(f"[DEBUG] Triggering ability update for user={user_id}")
trigger_ability_update(user_id, session_id, background=True)
```

### R IRT 서비스 연결 실패

**확인 사항**:
1. 서비스 URL: `http://r-irt-plumber.seedtest.svc.cluster.local:80`
2. 서비스 상태: `kubectl -n seedtest get svc r-irt-plumber`
3. 파드 상태: `kubectl -n seedtest get pods -l app=r-irt-plumber`

**해결**: 서비스 배포 확인 및 네트워크 정책 확인

### 문항 파라미터 없음

**확인**:
```sql
SELECT COUNT(*) FROM mirt_item_params;
SELECT COUNT(*) FROM question WHERE meta ? 'irt';
```

**해결**: IRT 캘리브레이션 실행 (`mirt_calibrate.py`)

## 참고 문서

- θ 온라인 업데이트: `apps/seedtest_api/docs/THETA_ONLINE_UPDATE.md`
- IRT 캘리브레이션: `apps/seedtest_api/docs/IRT_CALIBRATION_SETUP.md`

