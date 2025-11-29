# θ 온라인 업데이트 가이드

**작성일**: 2025-11-01

## 개요

세션 종료 시 최근 시도 데이터를 기반으로 EAP (Expected A Posteriori) 또는 Maximum Likelihood 추정을 수행하여 사용자의 능력(θ)을 실시간으로 업데이트합니다.

## 구현 현황

### ✅ 완료된 작업

1. **`irt_update_service.py` 구현**
   - `attempt` VIEW 또는 `exam_results`에서 최근 시도 데이터 로드
   - `mirt_item_params` 또는 `question.meta`에서 문항 파라미터 로드
   - R IRT Plumber 서비스를 통한 EAP 추정
   - `mirt_ability` 테이블 자동 업데이트

2. **세션 종료 트리거 통합**
   - `finish_exam()` 함수에서 자동 트리거 (백그라운드)
   - 비차단식 실행 (능력 업데이트 실패가 세션 완료를 막지 않음)

## 데이터 흐름

### 1. 세션 종료 시 트리거

```
세션 종료 → finish_exam() → trigger_ability_update() (백그라운드)
```

### 2. 능력 업데이트 프로세스

1. **최근 시도 로드**
   - `attempt` VIEW에서 최근 N일(기본 30일) 시도 조회
   - Fallback: `exam_results` JSON

2. **문항 파라미터 로드**
   - `mirt_item_params` 테이블에서 문항 파라미터 조회
   - Fallback: `question.meta->'irt'` JSONB

3. **EAP 추정**
   - R IRT Plumber 서비스 호출 (`/irt/score`)
   - 입력: `item_params` + `responses`
   - 출력: `theta`, `standard_error`

4. **DB 업데이트**
   - `mirt_ability` 테이블에 업서트
   - `ON CONFLICT (user_id, version) DO UPDATE`

## API 사용

### 자동 트리거 (세션 종료 시)

```python
# finish_exam() 호출 시 자동으로 백그라운드 실행
POST /exams/{session_id}/finish
```

### 수동 트리거 (관리자용)

```python
# 수동으로 능력 업데이트 트리거
POST /analysis/irt/update?user_id={user_id}
```

**요청 예시:**
```bash
curl -X POST "http://api.example.com/analysis/irt/update?user_id=user123" \
  -H "Authorization: Bearer <token>"
```

**응답 예시:**
```json
{
  "user_id": "user123",
  "theta": 0.65,
  "standard_error": 0.15,
  "updated_at": "2025-11-01T12:00:00Z"
}
```

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `R_IRT_BASE_URL` | R IRT Plumber 서비스 URL | (필수) |
| `R_IRT_INTERNAL_TOKEN` | R IRT 서비스 인증 토큰 | (필수) |
| `R_IRT_TIMEOUT_SECS` | HTTP 요청 타임아웃 (초) | `20` |

## 코드 예시

### Python 서비스 호출

```python
from apps.seedtest_api.services.irt_update_service import (
    update_ability_sync,
    trigger_ability_update,
)

# 동기 실행 (차단)
theta, se = update_ability_sync(
    user_id="user123",
    session_id="session456",
    lookback_days=30,
    model="2PL",
    version="v1",
)

# 비동기 실행 (백그라운드)
trigger_ability_update(
    user_id="user123",
    session_id="session456",
    background=True,
)
```

## 검증

### 1. 능력 업데이트 확인

```sql
-- 최근 업데이트된 능력 추정치 확인
SELECT user_id, theta, se, model, version, fitted_at
FROM mirt_ability
WHERE user_id = 'user123'
ORDER BY fitted_at DESC
LIMIT 1;
```

### 2. 시도 데이터 확인

```sql
-- 최근 시도 데이터 확인 (attempt VIEW)
SELECT 
    student_id::text AS user_id,
    item_id,
    correct,
    completed_at
FROM attempt
WHERE student_id::text = 'user123'
  AND completed_at >= NOW() - INTERVAL '30 days'
ORDER BY completed_at DESC
LIMIT 50;
```

### 3. 문항 파라미터 확인

```sql
-- 사용된 문항 파라미터 확인
SELECT item_id, params, model, version
FROM mirt_item_params
WHERE item_id IN (
    SELECT DISTINCT item_id::text
    FROM attempt
    WHERE student_id::text = 'user123'
      AND completed_at >= NOW() - INTERVAL '30 days'
)
ORDER BY fitted_at DESC;
```

## 문제 해결

### 1. 능력 업데이트가 실행되지 않음

- **원인**: `user_id`가 없거나 `finish_exam()` 호출되지 않음
- **해결**: 세션 완료 시 `user_id` 전달 확인

### 2. R IRT 서비스 연결 실패

- **원인**: `R_IRT_BASE_URL` 또는 `R_IRT_INTERNAL_TOKEN` 미설정
- **해결**: 환경 변수 설정 확인

### 3. 문항 파라미터가 없음

- **원인**: `mirt_item_params` 테이블이 비어있거나 캘리브레이션 미실행
- **해결**: IRT 주간 캘리브레이션 실행 (`mirt_calibrate.py`)

### 4. 시도 데이터가 없음

- **원인**: `attempt` VIEW 또는 `exam_results` 테이블에 데이터 없음
- **해결**: 시도 데이터 확인 및 `attempt` VIEW 생성 확인

## 성능 고려사항

- **백그라운드 실행**: 세션 완료 응답 시간에 영향을 주지 않음
- **최대 조회 기간**: 기본 30일, 필요시 조정 가능
- **타임아웃**: R IRT 서비스 호출 타임아웃 기본 20초
- **에러 처리**: 능력 업데이트 실패가 세션 완료를 막지 않음

## 참고 문서

- IRT 캘리브레이션: `apps/seedtest_api/docs/IRT_CALIBRATION_SETUP.md`
- IRT 표준화: `apps/seedtest_api/docs/IRT_STANDARDIZATION.md`

