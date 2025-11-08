"""Header-based authentication for OIDC reverse proxy integration.

This module provides authentication via HTTP headers set by an OIDC reverse proxy
(e.g., oauth2-proxy, Keycloak, Traefik ForwardAuth).

Design:
- Supports both JWT tokens and header-based authentication
- Header names configurable via environment variables
- Role canonicalization for flexible IdP integration
- Multi-tenancy via org_id header
"""

from __future__ import annotations

import os
from typing import Literal, Optional

from fastapi import Header, HTTPException, status

from apps.seedtest_api.auth.deps import UserContext


# ============================================================================
# Configuration - Header Names (Environment Variable Override)
# ============================================================================

HEADER_USER = os.getenv("AUTH_HEADER_USER", "X-User")
HEADER_ORG_ID = os.getenv("AUTH_HEADER_ORG", "X-Org-Id")
HEADER_ROLES = os.getenv("AUTH_HEADER_ROLES", "X-Roles")
HEADER_GROUPS = os.getenv("AUTH_HEADER_GROUPS", "X-Auth-Request-Groups")


# ============================================================================
# Role Canonicalization
# ============================================================================

def canonicalize_roles(raw_roles: str) -> list[str]:
    """Canonicalize role names from IdP to standard DreamSeedAI roles.
    
    Converts various role naming conventions to standard roles:
    - admin: System administrator (all permissions)
    - teacher: Teacher (class management, student assessment)
    - counselor: Counseling teacher (student counseling, support)
    - student: Student (personal dashboard access)
    - viewer: Read-only user
    
    Args:
        raw_roles: Comma-separated role string from IdP
        
    Returns:
        List of canonicalized role names
        
    Examples:
        >>> canonicalize_roles("  Admin,  Principal")
        ['admin']
        >>> canonicalize_roles("Teacher, 교사")
        ['teacher']
        >>> canonicalize_roles("상담사 ")
        ['counselor']
        >>> canonicalize_roles("Student, 학생")
        ['student']
        >>> canonicalize_roles("일반 사용자")
        ['viewer']
    """
    if not raw_roles:
        return ["viewer"]  # Default role
    
    # Normalize: lowercase, strip whitespace
    normalized = [r.strip().lower() for r in raw_roles.split(",") if r.strip()]
    
    canonical_roles = set()
    
    for role in normalized:
        # Admin keywords (English, Korean)
        if any(kw in role for kw in ["admin", "관리자", "administrator", "principal", "교장"]):
            canonical_roles.add("admin")
        
        # Teacher keywords (English, Korean)
        elif any(kw in role for kw in ["teacher", "교사", "선생", "instructor", "professor"]):
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
        
        # If no match, keep original (for future extensibility)
        else:
            canonical_roles.add(role)
    
    # If no roles matched, default to viewer
    if not canonical_roles:
        canonical_roles.add("viewer")
    
    return sorted(list(canonical_roles))


# ============================================================================
# Header-based User Context Extraction
# ============================================================================

def get_user_from_headers(
    x_user: Optional[str] = Header(None, alias=HEADER_USER),
    x_org_id: Optional[str] = Header(None, alias=HEADER_ORG_ID),
    x_roles: Optional[str] = Header(None, alias=HEADER_ROLES),
    x_groups: Optional[str] = Header(None, alias=HEADER_GROUPS),
) -> UserContext:
    """Extract user context from HTTP headers set by OIDC reverse proxy.
    
    This function is designed to work with OIDC reverse proxies like:
    - oauth2-proxy
    - Keycloak (with appropriate header configuration)
    - Traefik ForwardAuth
    - Envoy External Auth
    
    Security:
    - Reverse proxy MUST strip all X-* headers from external requests
    - Only headers set by the trusted proxy should reach this function
    
    Args:
        x_user: User unique identifier (from X-User or AUTH_HEADER_USER)
        x_org_id: Organization ID (from X-Org-Id or AUTH_HEADER_ORG)
        x_roles: Comma-separated roles (from X-Roles or AUTH_HEADER_ROLES)
        x_groups: Comma-separated groups (from X-Auth-Request-Groups, optional)
        
    Returns:
        UserContext with user_id, tenant_id (org_id), and canonicalized roles
        
    Raises:
        HTTPException: 401 if required headers are missing
        
    Example:
        # In FastAPI endpoint
        @router.get("/dashboard")
        def dashboard(user: UserContext = Depends(get_user_from_headers)):
            return {"user": user.user_id, "org": user.tenant_id}
    """
    # Validate required headers
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
    
    # Optional: Merge groups into roles if needed
    # if x_groups:
    #     group_roles = canonicalize_roles(x_groups)
    #     canonical_roles.extend(group_roles)
    #     canonical_roles = sorted(list(set(canonical_roles)))
    
    return UserContext(
        user_id=x_user.strip(),
        tenant_id=x_org_id.strip(),  # org_id maps to tenant_id
        roles=canonical_roles
    )


# ============================================================================
# Hybrid Authentication (JWT or Headers)
# ============================================================================

def get_current_user_hybrid(
    # JWT auth (via Bearer token)
    authorization: Optional[str] = Header(None),
    # Header auth (via OIDC proxy)
    x_user: Optional[str] = Header(None, alias=HEADER_USER),
    x_org_id: Optional[str] = Header(None, alias=HEADER_ORG_ID),
    x_roles: Optional[str] = Header(None, alias=HEADER_ROLES),
) -> UserContext:
    """Hybrid authentication: Try JWT first, fall back to headers.
    
    Priority:
    1. If Authorization header exists → JWT authentication
    2. If X-User/X-Org-Id/X-Roles exist → Header authentication
    3. Otherwise → 401 Unauthorized
    
    This allows flexible deployment:
    - Development: JWT tokens for testing
    - Production: OIDC reverse proxy with headers
    - Migration: Both can coexist
    
    Args:
        authorization: Bearer token (optional)
        x_user: User ID from header (optional)
        x_org_id: Org ID from header (optional)
        x_roles: Roles from header (optional)
        
    Returns:
        UserContext from either JWT or headers
        
    Raises:
        HTTPException: 401 if neither auth method succeeds
    """
    # Try JWT first (if Authorization header exists)
    if authorization and authorization.startswith("Bearer "):
        try:
            from apps.seedtest_api.auth.deps import get_current_user
            from fastapi.security import HTTPAuthorizationCredentials
            
            token = authorization.replace("Bearer ", "").strip()
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            return get_current_user(creds)
        except Exception:
            pass  # Fall through to header auth
    
    # Try header auth
    if x_user and x_org_id and x_roles:
        return get_user_from_headers(
            x_user=x_user,
            x_org_id=x_org_id,
            x_roles=x_roles
        )
    
    # No valid auth method
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either Bearer token or OIDC headers.",
    )


# ============================================================================
# Role-based Access Control (RBAC) for Header Auth
# ============================================================================

def require_role_header(*allowed: Literal["student", "teacher", "counselor", "admin", "viewer"]):
    """Create dependency that requires specific role(s) via header auth.
    
    Similar to require_role() from deps.py, but uses header-based auth.
    
    Args:
        allowed: One or more role names that are allowed
        
    Returns:
        FastAPI dependency function that validates role
        
    Example:
        @router.get("/classes", dependencies=[Depends(require_role_header("teacher", "admin"))])
        def list_classes(user: UserContext = Depends(get_user_from_headers)):
            return {"classes": [...]}
    """
    from fastapi import Depends
    
    def _dep(user: UserContext = Depends(get_user_from_headers)) -> UserContext:
        if all(r not in user.roles for r in allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {allowed}, got: {user.roles}",
            )
        return user
    
    return _dep


# ============================================================================
# Utility Functions
# ============================================================================

def has_role(user: UserContext, *required_roles: str) -> bool:
    """Check if user has any of the required roles.
    
    Args:
        user: UserContext instance
        required_roles: One or more role names to check
        
    Returns:
        True if user has at least one of the required roles
        
    Example:
        if has_role(user, "admin", "teacher"):
            # User is admin or teacher
            ...
    """
    return any(role in user.roles for role in required_roles)


def is_admin(user: UserContext) -> bool:
    """Check if user has admin role."""
    return "admin" in user.roles


def is_teacher(user: UserContext) -> bool:
    """Check if user has teacher role."""
    return "teacher" in user.roles


def is_counselor(user: UserContext) -> bool:
    """Check if user has counselor role."""
    return "counselor" in user.roles


def is_student(user: UserContext) -> bool:
    """Check if user has student role."""
    return "student" in user.roles
