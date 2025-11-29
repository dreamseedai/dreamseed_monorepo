"""Unified authentication module for DreamSeedAI.

This module provides a single, consistent authentication interface that supports:
1. JWT token authentication (for API clients, mobile apps)
2. OIDC header-based authentication (for web dashboard via reverse proxy)
3. Multi-tenancy via org_id/tenant_id
4. Role-based access control (RBAC)

Design Philosophy:
- Single source of truth for user context (UserContext class)
- Flexible authentication methods (JWT or Headers)
- Backward compatible with existing code
- Doc 02 compliant (OIDC, RBAC, Multi-tenancy)

Usage:
    from apps.seedtest_api.auth.unified import get_current_user, require_role

    @router.get("/dashboard")
    def dashboard(user: UserContext = Depends(get_current_user)):
        return {"user": user.user_id, "org": user.org_id}

    @router.post("/classes", dependencies=[Depends(require_role("teacher", "admin"))])
    def create_class(user: UserContext = Depends(get_current_user)):
        ...
"""

from __future__ import annotations

import os
from typing import Callable, Literal, Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

# ============================================================================
# Configuration
# ============================================================================

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")  # For RS256

# Header Configuration (OIDC Reverse Proxy)
HEADER_USER = os.getenv("AUTH_HEADER_USER", "X-User")
HEADER_ORG_ID = os.getenv("AUTH_HEADER_ORG", "X-Org-Id")
HEADER_ROLES = os.getenv("AUTH_HEADER_ROLES", "X-Roles")
HEADER_GROUPS = os.getenv("AUTH_HEADER_GROUPS", "X-Auth-Request-Groups")

# Development Mode
LOCAL_DEV = os.getenv("LOCAL_DEV", "false").lower() == "true"

bearer = HTTPBearer(auto_error=False)


# ============================================================================
# User Context Model
# ============================================================================


class UserContext(BaseModel):
    """Unified user context for all authentication methods.

    Attributes:
        user_id: Unique user identifier (from JWT 'sub' or header X-User)
        org_id: Organization/tenant ID for multi-tenancy (from JWT or header X-Org-Id)
        roles: List of canonicalized role names (admin, teacher, counselor, student, viewer)
        scope: Optional OAuth2 scope string
        auth_method: How the user was authenticated (jwt, header, dev)
    """

    user_id: str
    org_id: Optional[str] = None  # Changed to str to match header format
    roles: list[str] = []
    scope: Optional[str] = None
    auth_method: str = "unknown"

    # Backward compatibility aliases
    @property
    def tenant_id(self) -> Optional[str]:
        """Alias for org_id (for compatibility with auth/deps.py)."""
        return self.org_id

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return "admin" in self.roles

    def is_teacher(self) -> bool:
        """Check if user has teacher role."""
        return "teacher" in self.roles

    def is_counselor(self) -> bool:
        """Check if user has counselor role."""
        return "counselor" in self.roles

    def is_student(self) -> bool:
        """Check if user has student role."""
        return "student" in self.roles

    def is_viewer(self) -> bool:
        """Check if user has viewer role."""
        return "viewer" in self.roles

    def has_role(self, *required_roles: str) -> bool:
        """Check if user has any of the required roles."""
        return any(role in self.roles for role in required_roles)


# ============================================================================
# Role Canonicalization
# ============================================================================


def canonicalize_roles(raw_roles: str | list[str]) -> list[str]:
    """Canonicalize role names from IdP to standard DreamSeedAI roles.

    Converts various role naming conventions to standard roles:
    - admin: System administrator (all permissions)
    - teacher: Teacher (class management, student assessment)
    - counselor: Counseling teacher (student counseling, support)
    - student: Student (personal dashboard access)
    - viewer: Read-only user

    Args:
        raw_roles: Comma-separated role string or list of roles from IdP

    Returns:
        List of canonicalized role names

    Examples:
        >>> canonicalize_roles("  Admin,  Principal")
        ['admin']
        >>> canonicalize_roles("Teacher, 교사")
        ['teacher']
        >>> canonicalize_roles(["상담사", "Counselor"])
        ['counselor']
    """
    if not raw_roles:
        return ["viewer"]  # Default role

    # Handle both string and list input
    if isinstance(raw_roles, str):
        normalized = [r.strip().lower() for r in raw_roles.split(",") if r.strip()]
    else:
        normalized = [str(r).strip().lower() for r in raw_roles if r]

    canonical_roles = set()

    for role in normalized:
        # Admin keywords (English, Korean)
        if any(
            kw in role
            for kw in ["admin", "관리자", "administrator", "principal", "교장"]
        ):
            canonical_roles.add("admin")

        # Teacher keywords (English, Korean)
        elif any(
            kw in role for kw in ["teacher", "교사", "선생", "instructor", "professor"]
        ):
            canonical_roles.add("teacher")

        # Counselor keywords (English, Korean)
        elif any(kw in role for kw in ["counsel", "상담", "advisor", "guidance"]):
            canonical_roles.add("counselor")

        # Student keywords (English, Korean)
        elif any(kw in role for kw in ["student", "학생", "pupil", "learner"]):
            canonical_roles.add("student")

        # Viewer/Read-only keywords
        elif any(kw in role for kw in ["viewer", "조회", "reader", "guest", "일반"]):
            canonical_roles.add("viewer")

        # Keep original if no match (for extensibility)
        else:
            canonical_roles.add(role)

    # If no roles matched, default to viewer
    if not canonical_roles:
        canonical_roles.add("viewer")

    return sorted(list(canonical_roles))


# ============================================================================
# JWT Authentication
# ============================================================================


def _decode_jwt_token(token: str) -> dict:
    """Decode and validate JWT token.

    Supports both HS256 (symmetric) and RS256 (asymmetric) algorithms.
    """
    try:
        # Use public key for RS256, secret for HS256
        if JWT_ALGORITHM == "RS256":
            if not JWT_PUBLIC_KEY:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWT_PUBLIC_KEY not configured for RS256 algorithm",
                )
            key = JWT_PUBLIC_KEY
        else:
            key = JWT_SECRET

        payload = jwt.decode(token, key, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


def _extract_user_from_jwt(payload: dict) -> UserContext:
    """Extract UserContext from JWT payload."""
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user_id in token (sub or user_id claim required)",
        )

    # Extract org_id (try multiple claim names for compatibility)
    org_id = payload.get("org_id") or payload.get("tenant_id")
    if org_id is not None:
        org_id = str(org_id)  # Normalize to string

    # Extract and canonicalize roles
    raw_roles = payload.get("roles", [])
    if isinstance(raw_roles, str):
        raw_roles = [r.strip() for r in raw_roles.split() if r.strip()]
    roles = canonicalize_roles(raw_roles) if raw_roles else ["viewer"]

    scope = payload.get("scope")

    return UserContext(
        user_id=str(user_id), org_id=org_id, roles=roles, scope=scope, auth_method="jwt"
    )


# ============================================================================
# Header-based Authentication (OIDC Reverse Proxy)
# ============================================================================


def _extract_user_from_headers(
    x_user: Optional[str],
    x_org_id: Optional[str],
    x_roles: Optional[str],
) -> UserContext:
    """Extract UserContext from HTTP headers set by OIDC reverse proxy."""
    if not x_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing authentication header: {HEADER_USER}",
        )

    if not x_org_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing organization header: {HEADER_ORG_ID}",
        )

    if not x_roles:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing roles header: {HEADER_ROLES}",
        )

    # Canonicalize roles
    canonical_roles = canonicalize_roles(x_roles)

    return UserContext(
        user_id=x_user.strip(),
        org_id=x_org_id.strip(),
        roles=canonical_roles,
        auth_method="header",
    )


# ============================================================================
# Unified Authentication (Main Entry Point)
# ============================================================================


async def get_current_user(
    # JWT auth
    authorization: HTTPAuthorizationCredentials = Depends(bearer),
    # Header auth (OIDC proxy)
    x_user: Optional[str] = Header(None, alias=HEADER_USER),
    x_org_id: Optional[str] = Header(None, alias=HEADER_ORG_ID),
    x_roles: Optional[str] = Header(None, alias=HEADER_ROLES),
) -> UserContext:
    """Unified authentication: JWT or Headers (with LOCAL_DEV fallback).

    Priority:
    1. LOCAL_DEV mode → Return dev user (for testing)
    2. Authorization header exists → JWT authentication
    3. X-User/X-Org-Id/X-Roles exist → Header authentication
    4. Otherwise → 401 Unauthorized

    This allows flexible deployment:
    - Development: LOCAL_DEV=true for quick testing
    - API clients: JWT tokens
    - Web dashboard: OIDC reverse proxy with headers

    Args:
        authorization: Bearer token (optional)
        x_user: User ID from header (optional)
        x_org_id: Org ID from header (optional)
        x_roles: Roles from header (optional)

    Returns:
        UserContext from JWT, headers, or dev mode

    Raises:
        HTTPException: 401 if no valid authentication method
    """
    # LOCAL_DEV mode (highest priority for developer convenience)
    if LOCAL_DEV and not authorization and not x_user:
        return UserContext(
            user_id="dev-user",
            org_id="1",
            roles=["admin", "teacher", "student"],  # Dev user has all roles
            scope="*",
            auth_method="dev",
        )

    # Try JWT authentication
    if authorization:
        try:
            payload = _decode_jwt_token(authorization.credentials)
            return _extract_user_from_jwt(payload)
        except HTTPException:
            # If JWT fails and headers are present, try header auth
            if not (x_user and x_org_id and x_roles):
                raise  # Re-raise JWT error if no headers

    # Try header authentication
    if x_user and x_org_id and x_roles:
        return _extract_user_from_headers(x_user, x_org_id, x_roles)

    # No valid authentication method
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either Bearer token or OIDC headers.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ============================================================================
# Role-based Access Control (RBAC)
# ============================================================================


def require_role(
    *allowed: Literal["student", "teacher", "counselor", "admin", "viewer"]
) -> Callable[[UserContext], UserContext]:
    """Create dependency that requires specific role(s).

    Args:
        allowed: One or more role names that are allowed

    Returns:
        FastAPI dependency function that validates role

    Example:
        @router.get("/classes", dependencies=[Depends(require_role("teacher", "admin"))])
        def list_classes(user: UserContext = Depends(get_current_user)):
            return {"classes": [...]}
    """

    def _dep(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not user.has_role(*allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {allowed}, got: {user.roles}",
            )
        return user

    return _dep


def require_admin(user: UserContext = Depends(get_current_user)) -> UserContext:
    """Require admin role."""
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return user


def require_teacher_or_admin(
    user: UserContext = Depends(get_current_user),
) -> UserContext:
    """Require teacher or admin role."""
    if not (user.is_teacher() or user.is_admin()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin role required",
        )
    return user


# ============================================================================
# Multi-tenancy Helpers
# ============================================================================


def require_org_access(
    resource_org_id: str, user: UserContext = Depends(get_current_user)
) -> UserContext:
    """Verify user has access to resource's organization.

    Rules:
    - Admin: Can access any organization
    - Others: Can only access their own organization

    Args:
        resource_org_id: Organization ID of the resource being accessed
        user: Current user context

    Returns:
        UserContext if access is allowed

    Raises:
        HTTPException: 403 if user cannot access the organization
    """
    if user.is_admin():
        return user  # Admins can access any org

    if user.org_id != resource_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Resource belongs to organization {resource_org_id}",
        )

    return user


def get_org_filter(user: UserContext) -> Optional[str]:
    """Get organization filter for database queries.

    Returns:
        - None if user is admin (no filter needed, can see all orgs)
        - user.org_id otherwise (filter to user's organization)

    Usage:
        org_filter = get_org_filter(user)
        if org_filter:
            query = query.filter(org_id=org_filter)
    """
    if user.is_admin():
        return None  # Admin sees all organizations
    return user.org_id


# ============================================================================
# Backward Compatibility Layer
# ============================================================================


class User(BaseModel):
    """Legacy User model for backward compatibility with old deps.py.

    This is a compatibility shim. New code should use UserContext directly.
    """

    user_id: str
    org_id: Optional[int] = None
    roles: list[str] = []
    scope: Optional[str] = None

    def is_admin(self) -> bool:
        return any(r.lower() == "admin" for r in self.roles)

    def is_teacher(self) -> bool:
        return any(r.lower() == "teacher" for r in self.roles)

    def is_student(self) -> bool:
        return any(r.lower() == "student" for r in self.roles) or not (
            self.is_admin() or self.is_teacher()
        )

    @classmethod
    def from_user_context(cls, ctx: UserContext) -> "User":
        """Convert UserContext to legacy User model."""
        org_id_int = None
        if ctx.org_id:
            try:
                org_id_int = int(ctx.org_id)
            except ValueError:
                pass

        return cls(
            user_id=ctx.user_id, org_id=org_id_int, roles=ctx.roles, scope=ctx.scope
        )


async def get_current_user_legacy(ctx: UserContext = Depends(get_current_user)) -> User:
    """Get current user in legacy User format.

    This is for backward compatibility with existing code that expects
    the old User model from deps.py.

    New code should use get_current_user() directly to get UserContext.
    """
    return User.from_user_context(ctx)
