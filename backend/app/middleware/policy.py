"""
DreamSeedAI Governance Middleware
FastAPI Middleware + route → action 매핑 (Regex 기반)
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List
import logging

from app.governance_settings import governance_settings
from app.policy.loader import load_policy_bundle
from app.policy.rbac import check_permission
from app.policy.feature_flags import feature_enabled
from app.middleware.policy_routes import route_to_action as route_map

logger = logging.getLogger("governance.middleware")

# 정책 번들 로드 (앱 시작 시 1회)
try:
    POLICY = load_policy_bundle()
except Exception as e:
    logger.warning(f"Failed to load policy bundle: {e}")
    logger.warning("Governance enforcement will be disabled")
    POLICY = None


def extract_user_roles(request: Request) -> List[str]:
    """
    요청에서 사용자 역할 추출

    Args:
        request: FastAPI Request 객체

    Returns:
        역할 리스트
    """
    # 헤더에서 역할 추출 (예시)
    roles_header = request.headers.get("X-Roles", "")
    if roles_header:
        return [r.strip() for r in roles_header.split(",") if r.strip()]

    # TODO: JWT 토큰에서 추출하는 방식으로 변경
    # from ..auth.jwt import decode_token
    # token = request.headers.get("Authorization", "").replace("Bearer ", "")
    # payload = decode_token(token)
    # return payload.get("roles", [])

    return []


class GovernanceMiddleware(BaseHTTPMiddleware):
    """거버넌스 정책 집행 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        """
        요청 전처리: RBAC, Feature Flags 체크
        """
        # 정책 번들 미로드 시 패스
        if POLICY is None:
            return await call_next(request)

        # 사용자 역할 추출
        roles = extract_user_roles(request)

        # 액션 매핑 (policy_routes.py에서 가져옴)
        action, required_flag, approval_rule = route_map(
            request.method, request.url.path
        )

        # RBAC 체크
        if action != "unknown":
            has_permission = check_permission(POLICY, roles, action)

            if not has_permission:
                # Strict mode에 따라 차단 또는 경고
                if governance_settings.POLICY_STRICT_MODE == "enforce":
                    return Response(
                        content="Forbidden by governance policy",
                        status_code=403,
                        media_type="text/plain",
                    )
                else:
                    # Soft mode: 경고만 로그
                    logger.warning(
                        f"[SOFT] RBAC violation: user={roles}, action={action}"
                    )

        # Feature Flag 체크
        if required_flag and not feature_enabled(POLICY, required_flag):
            if governance_settings.POLICY_STRICT_MODE == "enforce":
                return Response(
                    content=f"Feature disabled by policy: {required_flag}",
                    status_code=403,
                    media_type="text/plain",
                )
            else:
                logger.warning(f"[SOFT] Feature flag violation: flag={required_flag}")

        # TODO: Approval 체크
        # if approval_rule:
        #     approval_status = check_approval(user_id, approval_rule, request)
        #     if approval_status == "pending":
        #         return Response(content="Approval pending", status_code=202)

        # 통과: 실제 핸들러 호출
        response = await call_next(request)

        # TODO: 감사 로그 기록
        # await log_audit(user_id, action, response.status_code)

        return response
