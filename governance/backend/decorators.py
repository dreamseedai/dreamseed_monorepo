import logging
from fastapi import Request, HTTPException
from functools import wraps
from typing import Callable, Optional, Any, Dict

from .policy_client import get_policy_client

logger = logging.getLogger(__name__)


def require_policy(
    policy_path: str,
    input_builder: Optional[Callable[..., Any]] = None,
    deny_status_code: int = 403,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    정책 평가 데코레이터

    Args:
        policy_path: 평가할 정책 경로 (예: "dreamseedai.access_control.allow")
        input_builder: 정책 입력 데이터 생성 함수
        deny_status_code: 거부 시 HTTP 상태 코드
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Request 객체 추출
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            if request is None:
                logger.error(
                    "Request object not found in function %s arguments", func.__name__
                )
                raise HTTPException(
                    status_code=500, detail="Internal Server Error: Request not found"
                )

            # 정책 입력 데이터 생성
            if input_builder:
                input_data = await input_builder(request, *args, **kwargs)
            else:
                input_data: Dict[str, Any] = {
                    "user": getattr(request.state, "user", {}),
                    "resource": {"path": request.url.path, "method": request.method},
                    "action": request.method.lower(),
                }

            # 정책 평가 시작 로깅
            user_info = getattr(request.state, "user", {})
            # 사용자 식별자 추출 (가능하면)
            user_id = (
                user_info.get("id")
                if isinstance(user_info, dict)
                else getattr(user_info, "id", None)
            )
            logger.info(
                "Evaluating policy '%s' for user %s on %s %s",
                policy_path,
                user_id if user_id is not None else user_info,
                request.method,
                request.url.path,
            )

            # 정책 평가
            policy_client = get_policy_client()
            result: Dict[str, Any] = await policy_client.evaluate(
                policy_path, input_data
            )

            # 결과 로깅 및 정책 거부 처리
            allowed = (
                result.get("allow", False) if isinstance(result, dict) else bool(result)
            )
            if not allowed:
                # 거부 사유 추출
                reason = result.get("reason") if isinstance(result, dict) else None
                logger.warning(
                    "Access denied by policy '%s'. Reason: %s",
                    policy_path,
                    reason or "No reason provided",
                )
                raise HTTPException(
                    status_code=deny_status_code,
                    detail={
                        "error": "Policy violation",
                        "policy": policy_path,
                        "reason": result.get(
                            "reason", f"Access denied by policy '{policy_path}'"
                        ),
                    },
                )

            # 정책 통과 시 로깅 및 원본 함수 실행
            logger.info(
                "Policy '%s' check passed, proceeding to original function", policy_path
            )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
