"""
Prometheus 메트릭 엔드포인트
===========================
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(tags=["Monitoring"])


@router.get("/metrics")
def metrics():
    """
    Prometheus 메트릭 엔드포인트.

    Returns:
        Prometheus 텍스트 형식 메트릭
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/healthz")
def healthz():
    """
    헬스 체크 엔드포인트.

    Returns:
        {"ok": True}
    """
    return {"ok": True}


@router.get("/readyz")
def readyz():
    """
    준비 상태 체크 엔드포인트.

    Returns:
        {"ready": True}
    """
    return {"ready": True}
