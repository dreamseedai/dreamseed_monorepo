# R Plumber Integration Guide

FastAPI와 R Plumber GLMM Analytics Service 통합 가이드입니다.

## 📦 설치 및 설정

### 1. 환경 변수 설정

`apps/seedtest_api/.env` 또는 K8s ConfigMap/Secret:

```bash
# R Plumber Service
R_PLUMBER_BASE_URL=http://r-glmm-plumber.seedtest.svc.cluster.local:8000
R_PLUMBER_INTERNAL_TOKEN=your-secret-token-here
```

### 2. Settings 업데이트

`apps/seedtest_api/settings.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # R Plumber Analytics Service
    R_PLUMBER_BASE_URL: str = Field(
        default="http://r-glmm-plumber.seedtest.svc.cluster.local:8000",
        env="R_PLUMBER_BASE_URL"
    )
    R_PLUMBER_INTERNAL_TOKEN: Optional[str] = Field(
        default=None,
        env="R_PLUMBER_INTERNAL_TOKEN"
    )
```

### 3. 클라이언트 초기화

`apps/seedtest_api/app/main.py`:

```python
from apps.seedtest_api.clients.r_plumber_extended import create_extended_r_plumber_client

# Global client instance
r_client = None

@app.on_event("startup")
async def startup_event():
    global r_client
    settings = Settings()
    r_client = create_extended_r_plumber_client(
        base_url=settings.R_PLUMBER_BASE_URL,
        internal_token=settings.R_PLUMBER_INTERNAL_TOKEN,
        timeout=30.0
    )
    logger.info(f"R Plumber client initialized: {settings.R_PLUMBER_BASE_URL}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("R Plumber client shutting down")
```

## 🔌 API 엔드포인트 예시

### 기본 GLMM 분석

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

class ObservationModel(BaseModel):
    student_id: str
    item_id: str
    correct: int  # 0 or 1

@router.post("/glmm/fit")
async def fit_glmm(observations: List[ObservationModel]):
    """Fit GLMM model to observations"""
    try:
        result = await r_client.glmm_fit(
            observations=[obs.dict() for obs in observations]
        )
        return result
    except Exception as e:
        logger.error(f"GLMM fit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 학생 능력 추정

```python
@router.get("/students/{student_id}/ability")
async def get_student_ability(student_id: str):
    """Get student ability estimate"""
    # 1. Fetch student's response history
    observations = await fetch_student_responses(student_id)
    
    # 2. Fit GLMM
    fit_result = await r_client.glmm_fit(observations)
    model = fit_result["model"]
    
    # 3. Extract ability
    abilities = await r_client.student_abilities(model, [student_id])
    
    return {
        "student_id": student_id,
        "ability": abilities["abilities"][student_id],
        "mean_ability": abilities["mean_ability"],
        "converged": fit_result.get("warnings", []) == []
    }
```

### 문항 추천 (적응형 학습)

```python
@router.get("/students/{student_id}/recommend-items")
async def recommend_items(
    student_id: str,
    target_probability: float = 0.7,
    n_items: int = 5
):
    """Recommend next items for adaptive learning"""
    # 1. Fit current model
    observations = await fetch_all_responses()
    fit_result = await r_client.glmm_fit(observations)
    model = fit_result["model"]
    
    # 2. Get available items
    item_pool = await fetch_available_items(student_id)
    
    # 3. Get recommendations
    recommendations = await r_client.recommend_items(
        model=model,
        student_id=student_id,
        item_pool=item_pool,
        target_probability=target_probability,
        n_items=n_items
    )
    
    return {
        "student_id": student_id,
        "recommended_items": recommendations["recommended_items"],
        "expected_probabilities": recommendations["expected_probabilities"],
        "target_probability": target_probability
    }
```

### 문항 난이도 분석

```python
@router.get("/items/{item_id}/difficulty")
async def get_item_difficulty(item_id: str):
    """Get item difficulty estimate"""
    # Fit model
    observations = await fetch_all_responses()
    fit_result = await r_client.glmm_fit(observations)
    model = fit_result["model"]
    
    # Get difficulty
    difficulties = await r_client.item_difficulties(model, [item_id])
    
    return {
        "item_id": item_id,
        "difficulty": difficulties["difficulties"][item_id],
        "mean_difficulty": difficulties["mean_difficulty"],
        "sd_difficulty": difficulties["sd_difficulty"]
    }
```

### 배치 예측

```python
@router.post("/predict/batch")
async def batch_predict(
    student_ids: List[str],
    item_ids: List[str]
):
    """Predict probabilities for multiple student-item pairs"""
    # Fit model
    observations = await fetch_all_responses()
    fit_result = await r_client.glmm_fit(observations)
    model = fit_result["model"]
    
    # Create newdata for all pairs
    newdata = [
        {"student_id": sid, "item_id": iid}
        for sid in student_ids
        for iid in item_ids
    ]
    
    # Predict
    pred_result = await r_client.glmm_predict(model, newdata)
    
    return {
        "predictions": pred_result["predictions"],
        "n_predictions": pred_result["n_predictions"]
    }
```

## 🎯 고급 사용 패턴

### 모델 캐싱

```python
from functools import lru_cache
from datetime import datetime, timedelta

# 모델을 일정 시간 캐싱
model_cache = {}
CACHE_TTL = timedelta(hours=1)

async def get_cached_model() -> Dict[str, Any]:
    """Get GLMM model with caching"""
    now = datetime.now()
    
    if "model" in model_cache:
        cached_at = model_cache["cached_at"]
        if now - cached_at < CACHE_TTL:
            return model_cache["model"]
    
    # Fit new model
    observations = await fetch_all_responses()
    fit_result = await r_client.glmm_fit(observations)
    
    model_cache["model"] = fit_result["model"]
    model_cache["cached_at"] = now
    
    return fit_result["model"]
```

### 에러 처리 및 재시도

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def robust_glmm_fit(observations: List[Dict[str, Any]]):
    """GLMM fit with automatic retry"""
    try:
        result = await r_client.glmm_fit(observations)
        
        # Check convergence
        if result.get("warnings"):
            logger.warning(f"GLMM fit warnings: {result['warnings']}")
        
        return result
    except Exception as e:
        logger.error(f"GLMM fit failed: {e}")
        raise
```

### 비동기 배치 처리

```python
async def process_students_batch(student_ids: List[str]):
    """Process multiple students in parallel"""
    model = await get_cached_model()
    
    # Process in parallel
    tasks = [
        r_client.student_abilities(model, [sid])
        for sid in student_ids
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter successful results
    abilities = {}
    for sid, result in zip(student_ids, results):
        if not isinstance(result, Exception):
            abilities[sid] = result["abilities"][sid]
    
    return abilities
```

## 🔐 보안 고려사항

### 1. 내부 전용 네트워크

```yaml
# K8s NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: r-glmm-plumber-ingress
spec:
  podSelector:
    matchLabels:
      app: r-glmm-plumber
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: seedtest-api
```

### 2. 토큰 로테이션

```bash
# Secret 업데이트
kubectl create secret generic r-plumber-secrets \
  --from-literal=internal-token=$(openssl rand -hex 32) \
  --dry-run=client -o yaml | kubectl apply -f -

# Pod 재시작으로 새 토큰 로드
kubectl rollout restart deployment r-glmm-plumber -n seedtest
kubectl rollout restart deployment seedtest-api -n seedtest
```

## 📊 모니터링

### Health Check 엔드포인트

```python
@router.get("/health/r-plumber")
async def check_r_plumber_health():
    """Check R Plumber service health"""
    try:
        health = await r_client.health()
        return {
            "status": "healthy",
            "r_service": health
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## 🚀 배포 체크리스트

- [ ] R Plumber 이미지 빌드 및 푸시
- [ ] K8s Secret 생성 (INTERNAL_TOKEN)
- [ ] ArgoCD Application 등록
- [ ] Settings에 환경 변수 추가
- [ ] FastAPI 클라이언트 초기화
- [ ] Health check 엔드포인트 테스트
- [ ] 기본 API 엔드포인트 구현
- [ ] 에러 처리 및 로깅 설정
- [ ] NetworkPolicy 적용 (프로덕션)
- [ ] 모니터링 대시보드 설정

## 📚 참고 자료

- R Plumber API 문서: `r-plumber/README.md`
- 테스트 시나리오: `tests/r-plumber.http`
- K8s 매니페스트: `ops/k8s/r-plumber/`
- ArgoCD 설정: `infra/argocd/apps/r-plumber.yaml`

