# IRT 온라인 업데이트 가이드

**작성일**: 2025-11-01

## 개요

세션 완료 시 최근 시도 데이터를 기반으로 EAP (Expected A Posteriori) 추정을 통해 사용자의 능력(θ)을 실시간으로 업데이트합니다.

## 아키텍처

### 데이터 흐름

```
세션 완료 → finish_exam() → session_hooks.on_session_complete() 
  → irt_update_service.update_ability_async() 
  → R IRT Plumber /irt/score 
  → mirt_ability 업데이트
```

### 주요 컴포넌트

1. **API 엔드포인트**: `POST /analysis/irt/update-theta`
2. **서비스**: `irt_update_service.py`
3. **세션 훅**: `session_hooks.py`
4. **R IRT 클라이언트**: `clients/r_irt.py`

## 설정

### 환경 변수

```bash
# R IRT 서비스 URL (기본값: 내부 서비스)
R_IRT_BASE_URL=http://r-irt-plumber.seedtest.svc.cluster.local:80

# 내부 인증 토큰 (선택사항)
R_IRT_INTERNAL_TOKEN=<token>

# 온라인 업데이트 활성화
ENABLE_IRT_ONLINE_UPDATE=true

# Lookback 기간 (일, 기본값: 30)
IRT_UPDATE_LOOKBACK_DAYS=30

# IRT 모델 타입 (기본값: 2PL)
IRT_MODEL=2PL
```

### Kubernetes Secret 설정

```bash
# R IRT 서비스 토큰 (필요시)
kubectl -n seedtest create secret generic r-irt-credentials \
  --from-literal=token='<your-token>'
```

## API 사용

### 엔드포인트

**POST** `/analysis/irt/update-theta`

**인증**: `analysis:run` 또는 `exam:write` 스코프 필요

**요청 본문**:
```json
{
  "user_id": "user123",
  "session_id": "session456",  // 선택사항
  "lookback_days": 30,          // 선택사항, 기본값: 30
  "model": "2PL",               // 선택사항, 기본값: "2PL"
  "version": "v1"               // 선택사항, 기본값: "v1"
}
```

**응답 (성공)**:
```json
{
  "user_id": "user123",
  "theta": 1.234,
  "se": 0.123,
  "model": "2PL",
  "version": "v1",
  "updated_at": "2025-11-01T12:00:00Z"
}
```

**응답 (실패)**:
- `400`: 잘못된 요청 (user_id 누락 등)
- `404`: 시도 데이터 없음 또는 R IRT 서비스 비사용 가능
- `500`: 내부 서버 오류

### 예시

```bash
# cURL 요청
curl -X POST "https://api.example.com/analysis/irt/update-theta" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "session456",
    "lookback_days": 30
  }'
```

## 세션 훅 통합

### 자동 트리거

`finish_exam()` 함수가 호출되면 자동으로 `session_hooks.on_session_complete()`가 호출됩니다:

```python
# apps/seedtest_api/services/result_service.py
def finish_exam(session_id: str, *, user_id: Optional[str] = None, ...):
    # ... 세션 완료 처리 ...
    
    # 세션 훅 호출 (백그라운드)
    if user_id:
        from ..services.session_hooks import on_session_complete
        on_session_complete(user_id, session_id)
    
    return result
```

### 수동 호출

필요시 직접 호출:

```python
from apps.seedtest_api.services.session_hooks import on_session_complete

# 세션 완료 후 수동 트리거
on_session_complete(user_id="user123", session_id="session456")
```

## 데이터 소스

### 1. 최근 시도 로드

우선순위:
1. **attempt VIEW** (표준화된 스키마)
2. **exam_results JSON** (Fallback)

### 2. 문항 파라미터 로드

우선순위:
1. **mirt_item_params** 테이블
2. **question.meta->'irt'** JSONB (Fallback)

### 3. R IRT 서비스 호출

```http
POST /irt/score
Content-Type: application/json
X-Internal-Token: <token>

{
  "item_params": [
    {"item_id": "1", "a": 1.0, "b": 0.5, "c": 0.2},
    ...
  ],
  "responses": [
    {"item_id": "1", "is_correct": true},
    ...
  ]
}
```

### 4. DB 업데이트

```sql
INSERT INTO mirt_ability (user_id, theta, se, model, version, fitted_at)
VALUES (:user_id, :theta, :se, :model, :version, NOW())
ON CONFLICT (user_id, version) DO UPDATE SET
  theta = EXCLUDED.theta,
  se = EXCLUDED.se,
  fitted_at = NOW()
```

## 검증

### 1. 업데이트 확인

```sql
SELECT 
    user_id,
    theta,
    se,
    fitted_at
FROM mirt_ability
WHERE user_id = 'user123'
ORDER BY fitted_at DESC
LIMIT 1;
```

### 2. 로그 확인

```bash
# K8s Pod 로그
kubectl -n seedtest logs -l app=seedtest-api | grep -i "theta update" | tail -20
```

### 3. 검증 스크립트

```bash
python -m apps.seedtest_api.services.theta_online_verification --user-id user123
```

## 문제 해결

### 시도 데이터 없음

**증상**: `404: no attempts found`

**해결**:
1. `attempt` VIEW 존재 확인:
   ```sql
   SELECT COUNT(*) FROM attempt WHERE student_id::text = 'user123';
   ```
2. Lookback 기간 확인 (기본 30일)

### 문항 파라미터 없음

**증상**: `theta_update_failed: no item parameters`

**해결**:
1. IRT 캘리브레이션 실행:
   ```bash
   kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly manual-calib-$(date +%s)
   ```
2. `mirt_item_params` 확인:
   ```sql
   SELECT COUNT(*) FROM mirt_item_params;
   ```

### R IRT 서비스 연결 실패

**증상**: `connection refused` 또는 `timeout`

**해결**:
1. 서비스 상태 확인:
   ```bash
   kubectl -n seedtest get svc r-irt-plumber
   kubectl -n seedtest get pods -l app=r-irt-plumber
   ```
2. 네트워크 정책 확인
3. 서비스 URL 확인: `R_IRT_BASE_URL` 환경 변수

### 업데이트가 실행되지 않음

**증상**: 세션 완료 후에도 `mirt_ability`가 업데이트되지 않음

**해결**:
1. `ENABLE_IRT_ONLINE_UPDATE=true` 확인
2. `finish_exam()` 호출 확인 (로그)
3. 에러 로그 확인:
   ```bash
   kubectl -n seedtest logs -l app=seedtest-api | grep -i "error\|exception" | tail -50
   ```

## 성능 고려사항

- **백그라운드 실행**: 세션 완료를 블로킹하지 않음
- **Lookback 제한**: 기본 30일, 최대 1000건
- **타임아웃**: R IRT 서비스 호출 5분 타임아웃
- **에러 처리**: 실패해도 세션 완료는 정상 처리

## 참고 문서

- θ 업데이트 검증: `apps/seedtest_api/docs/THETA_UPDATE_VERIFICATION.md`
- IRT 캘리브레이션: `apps/seedtest_api/docs/IRT_CALIBRATION_SETUP.md`
