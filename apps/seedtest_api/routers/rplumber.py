"""
R Plumber Analytics Service Router

Proxy endpoints for R GLMM analytics service.
"""

import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ...deps import get_current_user, User
from ...core.config import config

router = APIRouter(
    prefix="/api/seedtest/analysis/rplumber",
    tags=["R Analytics"]
)

# R Plumber service URL (cluster internal)
R_PLUMBER_URL = "http://r-glmm-plumber.seedtest.svc.cluster.local"


class Observation(BaseModel):
    student_id: str
    item_id: str
    correct: int


class GLMMFitRequest(BaseModel):
    observations: List[Observation]
    formula: Optional[str] = None


@router.get("/health")
async def r_plumber_health():
    """
    R Plumber service health check
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{R_PLUMBER_URL}/healthz")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"R Plumber service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking R Plumber health: {str(e)}")


@router.post("/glmm/fit")
async def glmm_fit(
    request: GLMMFitRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Fit GLMM model via R Plumber service
    
    Requires teacher or admin role.
    """
    if not (current_user.is_teacher() or current_user.is_admin()):
        raise HTTPException(status_code=403, detail="Requires teacher or admin role")
    
    try:
        # Convert Pydantic models to dict
        payload = {
            "observations": [obs.dict() for obs in request.observations]
        }
        if request.formula:
            payload["formula"] = request.formula
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{R_PLUMBER_URL}/glmm/fit",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        if hasattr(e, 'response') and e.response is not None:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"R Plumber error: {e.response.text}"
            )
        raise HTTPException(status_code=503, detail=f"R Plumber service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling R Plumber: {str(e)}")


@router.post("/glmm/predict")
async def glmm_predict(
    model: Dict[str, Any],
    newdata: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user)
):
    """
    Predict using fitted GLMM model
    """
    if not (current_user.is_teacher() or current_user.is_admin()):
        raise HTTPException(status_code=403, detail="Requires teacher or admin role")
    
    try:
        payload = {
            "model": model,
            "newdata": newdata
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{R_PLUMBER_URL}/glmm/predict",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        if hasattr(e, 'response') and e.response is not None:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"R Plumber error: {e.response.text}"
            )
        raise HTTPException(status_code=503, detail=f"R Plumber service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling R Plumber: {str(e)}")


@router.post("/analysis/student-abilities")
async def student_abilities(
    model: Dict[str, Any],
    student_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """
    Get student ability estimates (extended endpoint)
    """
    if not (current_user.is_teacher() or current_user.is_admin()):
        raise HTTPException(status_code=403, detail="Requires teacher or admin role")
    
    try:
        payload = {
            "model": model,
            "student_ids": student_ids
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{R_PLUMBER_URL}/analysis/student-abilities",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        if hasattr(e, 'response') and e.response is not None:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"R Plumber error: {e.response.text}"
            )
        raise HTTPException(status_code=503, detail=f"R Plumber service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling R Plumber: {str(e)}")

