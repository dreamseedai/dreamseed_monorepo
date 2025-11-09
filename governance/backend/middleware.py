import logging
from typing import List, Optional, Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .policy_client import get_policy_client


class PolicyEnforcementMiddleware(BaseHTTPMiddleware):
    """전역 정책 검사 미들웨어 - 모든 요청에 대해 사전 정의된 정책을 평가하여 접근을 제어합니다."""
    
    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        """
        PolicyEnforcementMiddleware 초기화.

        Args:
            app: FastAPI 애플리케이션 인스턴스.
            excluded_paths: 정책 검사를 제외할 경로 목록 (기본값: ["/health", "/metrics", "/docs", "/openapi.json"]).
        """
        super().__init__(app)
        # 제외 경로 설정 (기본 값 적용)
        self.excluded_paths = set(excluded_paths) if excluded_paths is not None else {"/health", "/metrics", "/docs", "/openapi.json"}
        # 로거 설정
        self.logger = logging.getLogger("PolicyEnforcementMiddleware")
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """요청에 대해 정책을 검사하고 허용되지 않으면 403 응답을 반환하는 미들웨어 디스패치 메서드."""
        # 요청 시작 로깅
        self.logger.info(f"정책 검사 시작 - 경로: {request.url.path}, 메소드: {request.method}")

        # 특정 경로는 정책 평가 생략
        if self._should_evaluate(request):
            # 정책 평가 입력 데이터 구성
            input_data = {
                "user": getattr(request.state, "user", {}),
                "resource": {
                    "path": request.url.path,
                    "method": request.method
                },
                "action": request.method.lower()
            }
            try:
                # 정책 엔진 평가 호출 (비동기)
                result = await get_policy_client().evaluate("dreamseedai.access_control.allow", input_data)
            except Exception as e:
                # 평가 호출 중 오류 발생 - 로그 기록 및 기본 거부 처리
                self.logger.error(f"정책 평가 오류 - 경로: {request.url.path}, 에러: {e}")
                result = {"allow": False, "error": str(e)}

            # 평가 결과 처리
            allow_flag = result.get("allow", False)
            if not allow_flag:
                # 정책 거부 로깅
                self.logger.warning(f"정책 거부 - 경로: {request.url.path}, 사용자: {getattr(request.state, 'user', {})}")
                # TODO: governance_policy_evaluations_total{result="deny"} 메트릭 증가
                # TODO: governance_policy_deny_total{...} 메트릭 증가 (사용자 역할 기준)
                return JSONResponse(status_code=403, content={"error": "Access denied by policy"})
            else:
                # 정책 허용 로깅
                self.logger.info(f"정책 허용 - 경로: {request.url.path}, 사용자: {getattr(request.state, 'user', {})}")
                # TODO: governance_policy_evaluations_total{result="allow"} 메트릭 증가

        # 정책 검사 통과 또는 제외 경로의 경우, 다음 미들웨어/라우트 핸들러 실행
        response = await call_next(request)
        return response

    def _should_evaluate(self, request: Request) -> bool:
        """정책 평가 필요 여부 판단"""
        return request.url.path not in self.excluded_paths
