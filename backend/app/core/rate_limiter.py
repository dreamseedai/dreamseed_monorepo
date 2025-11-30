"""
Rate Limiting Configuration

Redis 기반 rate limiting (slowapi 사용)
"""

from typing import Optional

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from .settings import settings


def get_user_id_or_ip(request: Request) -> str:
    """
    Rate limit 키 생성: 인증된 사용자는 user_id, 아니면 IP.

    Args:
        request: FastAPI Request 객체

    Returns:
        str: "user:{user_id}" 또는 IP 주소
    """
    # Request state에서 user 확인 (current_user dependency에서 설정됨)
    user = getattr(request.state, "user", None)

    if user and hasattr(user, "id"):
        return f"user:{user.id}"

    # 인증되지 않은 경우 IP 사용
    return get_remote_address(request)


def get_redis_url_for_rate_limiting() -> str:
    """
    Rate limiting용 Redis URL 생성.

    Returns:
        str: Redis URL (DB 2 사용)
    """
    base_url = settings.REDIS_URL.rsplit("/", 1)[0]  # Remove /0
    return f"{base_url}/{settings.REDIS_RATE_LIMIT_DB}"


# Global limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_redis_url_for_rate_limiting(),
    default_limits=[f"{settings.RATE_LIMIT_DEFAULT_PER_MINUTE}/minute"],
    enabled=settings.RATE_LIMIT_ENABLED,
    headers_enabled=True,  # X-RateLimit-* 헤더 추가
)
