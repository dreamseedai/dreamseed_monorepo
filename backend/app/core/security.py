"""
Authentication and authorization dependencies

This module provides multi-level authorization:
1. User role (student, teacher, parent, admin)
2. Organization membership (school, academy, tutor)
3. Organization role (org_admin, org_head_teacher, org_teacher, org_assistant)
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.users import fastapi_users
from app.models.user import User
from app.models.org_models import (
    Organization,
    OrgMembership,
    OrganizationType,
    OrgRole,
    is_school_org,
    is_tutoring_org,
)


# Current user dependency (active users only)
async def get_current_user(
    user: User = Depends(fastapi_users.current_user(active=True))
) -> User:
    """
    Get currently authenticated user
    
    Args:
        user: User from FastAPI-Users authentication
        
    Returns:
        Authenticated user object
        
    Raises:
        HTTPException: If authentication fails
    """
    return user


# Role-based dependencies
async def get_current_student(user: User = Depends(get_current_user)) -> User:
    """
    Require student role
    
    Raises:
        HTTPException: If user is not a student
    """
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student role required"
        )
    return user


async def get_current_teacher(user: User = Depends(get_current_user)) -> User:
    """
    Require teacher role
    
    Raises:
        HTTPException: If user is not a teacher
    """
    if user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher role required"
        )
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """
    Require admin role
    
    Raises:
        HTTPException: If user is not an admin
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return user


async def get_current_parent(user: User = Depends(get_current_user)) -> User:
    """
    Require parent role
    
    Raises:
        HTTPException: If user is not a parent
    """
    if user.role != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent role required"
        )
    return user


# ============================================================================
# Organization-based dependencies
# ============================================================================

async def get_current_teacher_with_memberships(
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_async_session),
) -> tuple[User, list[OrgMembership]]:
    """
    Get teacher with their organization memberships.
    
    Returns teacher user and all org memberships (may be empty if newly created teacher).
    Used as base dependency for school_teacher/tutor dependencies.
    
    Returns:
        Tuple of (user, memberships list)
        
    Example:
        user, memberships = context
        for m in memberships:
            print(f"Teacher at {m.organization.name} as {m.role}")
    """
    result = await db.execute(
        select(OrgMembership)
        .where(OrgMembership.user_id == current_user.id)
        .options(selectinload(OrgMembership.organization))
    )
    memberships = result.scalars().all()
    return current_user, memberships


async def get_current_school_teacher(
    data: tuple[User, list[OrgMembership]] = Depends(get_current_teacher_with_memberships),
) -> tuple[User, Organization, OrgMembership]:
    """
    Require teacher with school organization membership.
    
    Filters for:
    - Organization type: PUBLIC_SCHOOL or PRIVATE_SCHOOL
    - Organization role: ORG_TEACHER, ORG_HEAD_TEACHER, or ORG_ADMIN
    
    Returns first matching school membership (if teacher belongs to multiple schools,
    caller may need additional filtering logic).
    
    Returns:
        Tuple of (user, organization, membership)
        
    Raises:
        HTTPException 403: If teacher has no school memberships
        
    Example usage:
        @router.get("/school/report")
        async def school_report(
            context: tuple[User, Organization, OrgMembership] = Depends(get_current_school_teacher),
        ):
            user, org, membership = context
            # Only teachers from schools can access this endpoint
    """
    user, memberships = data
    
    for m in memberships:
        org = m.organization
        if is_school_org(org.type) and m.role in (
            OrgRole.ORG_TEACHER,
            OrgRole.ORG_HEAD_TEACHER,
            OrgRole.ORG_ADMIN,
        ):
            return user, org, m
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="School teacher membership required. You must be affiliated with a school organization.",
    )


async def get_current_tutor(
    data: tuple[User, list[OrgMembership]] = Depends(get_current_teacher_with_memberships),
) -> tuple[User, Organization, OrgMembership]:
    """
    Require teacher with tutoring organization membership.
    
    Filters for:
    - Organization type: ACADEMY, TUTORING_CENTER, or PRIVATE_TUTOR
    - Organization role: ORG_TEACHER, ORG_HEAD_TEACHER, or ORG_ADMIN
    
    Returns first matching tutoring membership.
    
    Returns:
        Tuple of (user, organization, membership)
        
    Raises:
        HTTPException 403: If teacher has no tutoring organization memberships
        
    Example usage:
        @router.get("/tutor/priorities")
        async def tutor_priorities(
            context: tuple[User, Organization, OrgMembership] = Depends(get_current_tutor),
        ):
            user, org, membership = context
            # Only tutors/academy teachers can access this endpoint
    """
    user, memberships = data
    
    for m in memberships:
        org = m.organization
        if is_tutoring_org(org.type) and m.role in (
            OrgRole.ORG_TEACHER,
            OrgRole.ORG_HEAD_TEACHER,
            OrgRole.ORG_ADMIN,
        ):
            return user, org, m
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Tutor/academy membership required. You must be affiliated with a tutoring organization.",
    )


async def get_current_teacher_any_org(
    data: tuple[User, list[OrgMembership]] = Depends(get_current_teacher_with_memberships),
) -> tuple[User, Organization, OrgMembership]:
    """
    Require teacher with ANY organization membership (school or tutoring).
    
    Less restrictive than get_current_school_teacher or get_current_tutor.
    Used for endpoints that work for both school teachers and tutors.
    
    Returns:
        Tuple of (user, organization, membership) for first active membership
        
    Raises:
        HTTPException 403: If teacher has no organization memberships
        
    Example usage:
        @router.get("/teacher/students")
        async def list_students(
            context: tuple[User, Organization, OrgMembership] = Depends(get_current_teacher_any_org),
        ):
            user, org, membership = context
            # Both school teachers and tutors can access this endpoint
    """
    user, memberships = data
    
    for m in memberships:
        if m.role in (
            OrgRole.ORG_TEACHER,
            OrgRole.ORG_HEAD_TEACHER,
            OrgRole.ORG_ADMIN,
        ):
            return user, m.organization, m
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Organization membership required. You must be affiliated with a school, academy, or tutoring organization.",
    )
