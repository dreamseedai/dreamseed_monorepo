"""
감사 로그 및 Prometheus 메트릭 미들웨어
======================================
trace_id 기반 요청 추적 및 지연시간 히스토그램 수집.

Features:
- trace_id 자동 생성 및 전파 (요청/응답/로그)
- Prometheus 메트릭 (요청 수, 지연시간 히스토그램)
- 구조화된 감사 로그 (structlog)
- 최소 라벨 정책 (Cardinality 폭발 방지)

Usage:
    from fastapi import FastAPI
    from shared.monitoring.middleware import AuditMetricsMiddleware
    
    app = FastAPI()
    app.add_middleware(
        AuditMetricsMiddleware,
        service_name="univprepai-api",
        service_version="v1"
    )
"""
from __future__ import annotations
import time
import uuid
import os
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from prometheus_client import Counter, Histogram
import structlog

logger = structlog.get_logger()

# Prometheus 메트릭 정의
REQ_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status", "service", "version"]
)

REQ_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency (seconds)",
    ["method", "path", "status", "service", "version"],
    # 웹 지연에 적합한 버킷 (5ms ~ 5s)
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5]
)


class AuditMetricsMiddleware(BaseHTTPMiddleware):
    """
    감사 로그 및 Prometheus 메트릭 미들웨어.
    
    모든 HTTP 요청에 대해:
    1. trace_id 생성/전파
    2. 지연시간 측정
    3. Prometheus 메트릭 기록
    4. 구조화된 감사 로그 출력
    
    Attributes:
        service_name: 서비스 이름 (예: 'univprepai-api')
        service_version: 서비스 버전 (예: 'v1', 'canary')
        path_template_enabled: 경로 템플릿 사용 여부 (Cardinality 방지)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        service_name: Optional[str] = None,
        service_version: Optional[str] = None,
        path_template_enabled: bool = True
    ):
        """
        미들웨어 초기화.
        
        Args:
            app: ASGI 애플리케이션
            service_name: 서비스 이름 (환경변수 SERVICE_NAME 또는 기본값)
            service_version: 서비스 버전 (환경변수 SERVICE_VERSION 또는 기본값)
            path_template_enabled: 경로 템플릿 사용 여부
        """
        super().__init__(app)
        self.service_name = service_name or os.getenv("SERVICE_NAME", "unknown")
        self.service_version = service_version or os.getenv("SERVICE_VERSION", "v1")
        self.path_template_enabled = path_template_enabled
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        요청 처리 및 메트릭 수집.
        
        Args:
            request: FastAPI Request 객체
            call_next: 다음 미들웨어/핸들러
        
        Returns:
            Response with X-Trace-ID header
        """
        # trace_id 생성 또는 전파
        trace_id = request.headers.get("x-trace-id") or uuid.uuid4().hex
        
        # 시작 시간
        start_time = time.perf_counter()
        
        # 기본 응답 (에러 시 사용)
        response = Response("Internal Server Error", status_code=500)
        status_code = 500
        
        try:
            # 다음 핸들러 호출
            response = await call_next(request)
            status_code = response.status_code
        
        except Exception as e:
            # 예외 발생 시 로깅
            logger.exception(
                "request_exception",
                trace_id=trace_id,
                error=str(e),
                service=self.service_name,
                version=self.service_version
            )
            status_code = 500
            raise
        
        finally:
            # 지연시간 계산
            elapsed = time.perf_counter() - start_time
            
            # 경로 정규화 (템플릿 사용 시)
            path = self._normalize_path(request)
            method = request.method
            
            # Prometheus 메트릭 기록
            REQ_COUNT.labels(
                method=method,
                path=path,
                status=str(status_code),
                service=self.service_name,
                version=self.service_version
            ).inc()
            
            REQ_LATENCY.labels(
                method=method,
                path=path,
                status=str(status_code),
                service=self.service_name,
                version=self.service_version
            ).observe(elapsed)
            
            # 감사 로그 (구조화)
            logger.info(
                "audit",
                trace_id=trace_id,
                method=method,
                path=path,
                status=status_code,
                latency_s=round(elapsed, 6),
                service=self.service_name,
                version=self.service_version,
                ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            
            # 응답 헤더에 trace_id 추가
            response.headers["x-trace-id"] = trace_id
        
        return response
    
    def _normalize_path(self, request: Request) -> str:
        """
        경로 정규화 (Cardinality 폭발 방지).
        
        동적 ID를 템플릿으로 변환:
        - /users/123 → /users/{id}
        - /api/v1/exams/456/results → /api/v1/exams/{id}/results
        
        Args:
            request: FastAPI Request 객체
        
        Returns:
            정규화된 경로
        """
        if not self.path_template_enabled:
            return request.url.path
        
        # FastAPI의 route 정보에서 템플릿 경로 가져오기
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                return route.path
        
        # 템플릿 정보가 없으면 원본 경로 사용
        return request.url.path


def setup_structlog():
    """
    structlog 설정.
    
    JSON 형식의 구조화된 로그 출력.
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
