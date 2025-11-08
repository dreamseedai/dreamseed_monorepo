"""
Student Role Guard
==================
FastAPI dependency for requiring 'student' role in JWT/session.

Usage:
    @router.get('/api/student/dashboard')
    def get_dashboard(user: UserContext = Depends(require_student)):
        ...
"""
from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from shared.auth.dependencies import get_current_user


@dataclass
class UserContext:
    """
    User context with tenant and role information.
    
    Attributes:
        user_id: UUID of the user (student_id for students)
        tenant_id: UUID of the tenant/organization
        username: Username or email
        roles: List of roles (e.g., ['student', 'admin'])
        lang: Language code (e.g., 'ko', 'zh', 'en') - optional
    """
    user_id: str
    tenant_id: str
    username: str
    roles: List[str]
    lang: str = 'en'  # Default language


def parse_user_context(user_dict: Dict[str, Any]) -> UserContext:
    """
    Parse user dictionary from session/JWT into UserContext.
    
    Expected fields:
    - sub or user_id: User UUID
    - tenant_id or org_id: Tenant UUID
    - username or email: Username
    - roles: List of role strings
    - lang: Language code (optional, defaults to 'en')
    """
    user_id = user_dict.get('sub') or user_dict.get('user_id')
    tenant_id = user_dict.get('tenant_id') or user_dict.get('org_id')
    username = user_dict.get('username') or user_dict.get('email')
    roles = user_dict.get('roles', [])
    lang = user_dict.get('lang', 'en')  # Language from JWT
    
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid user context: missing user_id or tenant_id'
        )
    
    return UserContext(
        user_id=str(user_id),
        tenant_id=str(tenant_id),
        username=str(username),
        roles=roles if isinstance(roles, list) else [],
        lang=str(lang) if lang else 'en'
    )


def require_student(user_dict: Dict[str, Any] = Depends(get_current_user)) -> UserContext:
    """
    Require 'student' or 'admin' role.
    
    Raises:
        HTTPException: 403 if user doesn't have student or admin role
    
    Returns:
        UserContext with user_id, tenant_id, username, roles
    """
    user = parse_user_context(user_dict)
    
    if 'student' not in user.roles and 'admin' not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='student role required'
        )
    
    return user
