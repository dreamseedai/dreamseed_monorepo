"""FastAPI dependencies for JWT authentication and role-based access control."""

from __future__ import annotations

import os
from typing import Callable, Literal

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=True)


class UserContext:
    """User context extracted from JWT token."""

    def __init__(self, user_id: str, tenant_id: str, roles: list[str]):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.roles = roles

    def __repr__(self) -> str:
        return f"<UserContext(user_id={self.user_id!r}, tenant_id={self.tenant_id!r}, roles={self.roles})>"


def get_current_user(
    token_data: HTTPAuthorizationCredentials = Depends(bearer),
) -> UserContext:
    """Extract and validate user context from JWT token.

    Args:
        token_data: Bearer token from request header

    Returns:
        UserContext with user_id, tenant_id, and roles

    Raises:
        HTTPException: 401 if token is invalid or missing required claims
    """
    token = token_data.credentials
    secret = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        roles = payload.get("roles", [])

        if not user_id or not tenant_id:
            raise ValueError("Missing required claims: sub or tenant_id")

        return UserContext(user_id, tenant_id, roles)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
        )


def require_role(
    *allowed: Literal["student", "teacher", "admin", "owner"]
) -> Callable[[UserContext], UserContext]:
    """Create dependency that requires specific role(s).

    Args:
        allowed: One or more role names that are allowed

    Returns:
        FastAPI dependency function that validates role

    Example:
        @router.get("/classes", dependencies=[Depends(require_role("teacher", "admin"))])
        def list_classes(): ...
    """

    def _dep(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not any(r in user.roles for r in allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {allowed}",
            )
        return user

    return _dep
