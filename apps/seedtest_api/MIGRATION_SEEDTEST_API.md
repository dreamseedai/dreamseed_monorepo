# seedtest-api → seedtest_api 병합 완료

**날짜**: 2025-11-07  
**작업자**: Windsurf AI Assistant

## 배경

`apps/` 디렉토리에 중복된 두 개의 디렉토리가 존재했습니다:

- **`seedtest-api/`** (9 files) - 레거시 실험 코드
- **`seedtest_api/`** (293 files) - 메인 프로덕션 API

## 수행 작업

### 1. 고유 파일 이동

레거시 디렉토리에서 프로덕션에 없던 고유 파일 2개를 이동:

```bash
# 성장 예측 통계 모듈
apps/seedtest-api/score_analysis/growth.py
→ apps/seedtest_api/score_analysis/growth.py

# 성장 예측 API 엔드포인트
apps/seedtest-api/routers/forecast.py
→ apps/seedtest_api/routers/forecast.py
```

### 2. 코드 리팩토링

#### `routers/forecast.py`
- DB 세션 생성을 프로젝트 표준 패턴으로 변경
- `from ..db.session import get_db` 사용
- 미사용 import 제거 (`Optional`)

#### `score_analysis/__init__.py` 생성
```python
from .growth import forecast_summary, prob_reach_target
__all__ = ["forecast_summary", "prob_reach_target"]
```

### 3. 메인 앱 통합

`app/main.py`에 새 라우터 등록:

```python
from ..routers.forecast import router as forecast_router
# ...
app.include_router(forecast_router)  # Student growth forecasting API
```

### 4. 레거시 디렉토리 삭제

```bash
rm -rf apps/seedtest-api/
```

## 새로운 API 엔드포인트

### `GET /forecast/student`

학생의 성장 예측 및 목표 달성 확률 계산

**Query Parameters:**
- `user_id` (required): 학생 ID
- `target` (required): 목표 점수
- `horizon` (optional, default=5): 예측 기간 (시험 횟수)

**Response:**
```json
{
  "user_id": "student123",
  "theta": 0.5,
  "se": 0.2,
  "target": 85.0,
  "target_theta": 0.85,
  "horizon": 5,
  "forecast": {
    "target": 0.85,
    "horizon": 5,
    "probability": 0.73
  }
}
```

**알고리즘:**
- 현재 능력치(θ)를 Normal(μ, σ²)로 모델링
- 향후 K번의 시험에서 정보 획득으로 불확실성 감소 (shrink factor)
- 목표 점수 초과 확률 계산 (1 - ∏P(X_t < target))

## 환경 변수

```bash
# 점수 ↔ 능력치(θ) 선형 변환
ABILITY_TO_SCORE_A=1.0  # θ = (score - B) / A
ABILITY_TO_SCORE_B=0.0
```

## 의존성

- `scipy` (optional): 더 정확한 정규분포 CDF 계산
- Fallback: Python 표준 라이브러리 `math.erf` 사용

## 테스트 방법

```bash
# 1. 서버 실행
cd apps/seedtest_api
uvicorn app.main:app --reload --port 8000

# 2. API 호출
curl "http://localhost:8000/forecast/student?user_id=test123&target=85&horizon=5"
```

## 남은 작업

- [ ] `ability_estimates` 테이블 확인 (GLMM 결과 저장)
- [ ] 실제 학생 데이터로 예측 정확도 검증
- [ ] 프론트엔드 UI 통합 (학생 대시보드)
- [ ] 단위 테스트 작성 (`tests/test_forecast_api.py`)

## 파일 변경 이력

### 추가된 파일
- `apps/seedtest_api/routers/forecast.py`
- `apps/seedtest_api/score_analysis/growth.py`
- `apps/seedtest_api/score_analysis/__init__.py`
- `apps/seedtest_api/MIGRATION_SEEDTEST_API.md` (이 문서)

### 수정된 파일
- `apps/seedtest_api/app/main.py` (라우터 등록)

### 삭제된 디렉토리
- `apps/seedtest-api/` (전체)

## 참고

레거시 디렉토리의 다른 파일들은 이미 프로덕션에 최신 버전이 존재:

| 레거시 파일 | 프로덕션 파일 | 상태 |
|------------|--------------|------|
| `jobs/mirt_calibrate.py` | `jobs/mirt_calibrate.py` | ✅ 최신 버전 (더 많은 기능) |
| `jobs/mixed_effects.py` | - | ⚠️ 미사용 (GLMM 실험 코드) |
| `routers/recommend.py` | `services/recommendation.py` | ✅ 통합됨 |
| `feedback/recommend.py` | `services/recommendation.py` | ✅ 통합됨 |
| `alembic/versions/20250101_0006_glmm_tables.py` | `alembic/versions/20251102_1100_glmm_meta.py` | ✅ 최신 버전 |
