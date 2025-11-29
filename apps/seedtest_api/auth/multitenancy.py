"""Multi-tenancy data isolation utilities for DreamSeedAI.

This module provides utilities to enforce organization-level data isolation
across the entire application, ensuring users can only access data from their
own organization (unless they are admins).

Design Principles:
1. **Defense in Depth**: Multiple layers of protection
2. **Fail Secure**: Default to deny access if org_id is missing
3. **Admin Bypass**: Admins can access all organizations
4. **Explicit Filtering**: Always require explicit org_id in queries

Usage:
    from apps.seedtest_api.auth.multitenancy import (
        enforce_org_filter,
        verify_org_access,
        get_org_filter_sql
    )

    # SQLAlchemy
    query = session.query(Student).filter(
        enforce_org_filter(Student.org_id, user)
    )

    # Raw SQL
    sql = f"SELECT * FROM students WHERE {get_org_filter_sql('org_id', user)}"

    # Resource access check
    verify_org_access(student.org_id, user)  # Raises 403 if denied
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import Column
from sqlalchemy.sql import ColumnElement

from .unified import UserContext


# ============================================================================
# SQLAlchemy Filters
# ============================================================================


def enforce_org_filter(
    org_id_column: Column | ColumnElement, user: UserContext, allow_null: bool = False
) -> ColumnElement:
    """Create SQLAlchemy filter expression for organization isolation.

    Args:
        org_id_column: SQLAlchemy column representing org_id
        user: Current user context
        allow_null: If True, allow resources with NULL org_id (global resources)

    Returns:
        SQLAlchemy filter expression

    Example:
        from sqlalchemy import select
        from models import Student

        stmt = select(Student).where(
            enforce_org_filter(Student.org_id, user)
        )
    """
    # Admins can see all organizations
    if user.is_admin():
        return org_id_column.isnot(None) if not allow_null else True  # type: ignore

    # Regular users: filter to their organization
    if not user.org_id:
        # User has no org_id → deny all access
        return org_id_column == "__NO_ACCESS__"  # type: ignore

    if allow_null:
        # Allow both user's org and NULL (global resources)
        return (org_id_column == user.org_id) | (org_id_column.is_(None))  # type: ignore
    else:
        # Only user's organization
        return org_id_column == user.org_id  # type: ignore


def get_org_filter_value(user: UserContext) -> Optional[str]:
    """Get organization ID for filtering queries.

    Returns:
        - None if user is admin (no filter needed)
        - user.org_id for regular users

    Example:
        org_filter = get_org_filter_value(user)
        if org_filter:
            query = query.filter(org_id=org_filter)
    """
    if user.is_admin():
        return None  # Admin sees all
    return user.org_id


# ============================================================================
# Raw SQL Helpers
# ============================================================================


def get_org_filter_sql(
    org_id_column: str, user: UserContext, allow_null: bool = False
) -> str:
    """Generate SQL WHERE clause for organization filtering.

    Args:
        org_id_column: Name of the org_id column
        user: Current user context
        allow_null: If True, allow NULL org_id (global resources)

    Returns:
        SQL WHERE clause string (without "WHERE" keyword)

    Example:
        sql = f"SELECT * FROM students WHERE {get_org_filter_sql('org_id', user)}"
        # For regular user: "SELECT * FROM students WHERE org_id = '123'"
        # For admin: "SELECT * FROM students WHERE 1=1"
    """
    # Admins can see all
    if user.is_admin():
        return "1=1"

    # Regular users
    if not user.org_id:
        return "1=0"  # Deny all

    # Escape single quotes to prevent SQL injection
    safe_org_id = user.org_id.replace("'", "''")

    if allow_null:
        return f"({org_id_column} = '{safe_org_id}' OR {org_id_column} IS NULL)"
    else:
        return f"{org_id_column} = '{safe_org_id}'"


# ============================================================================
# Resource Access Verification
# ============================================================================


def verify_org_access(
    resource_org_id: Optional[str], user: UserContext, resource_name: str = "resource"
) -> None:
    """Verify user has access to a resource's organization.

    Rules:
    - Admin: Can access any organization
    - Regular users: Can only access their own organization
    - If resource has no org_id: Deny access (fail secure)

    Args:
        resource_org_id: Organization ID of the resource
        user: Current user context
        resource_name: Name of resource for error message

    Raises:
        HTTPException: 403 if access is denied

    Example:
        student = db.query(Student).filter(id=student_id).first()
        verify_org_access(student.org_id, user, "student")
    """
    # Admins can access anything
    if user.is_admin():
        return

    # Resource has no org_id → deny (fail secure)
    if resource_org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: {resource_name} has no organization",
        )

    # User has no org_id → deny
    if user.org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: User has no organization",
        )

    # Check org match
    if resource_org_id != user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: {resource_name} belongs to organization {resource_org_id}",
        )


def verify_org_match(
    org_id_1: Optional[str],
    org_id_2: Optional[str],
    error_message: str = "Organization mismatch",
) -> None:
    """Verify two organization IDs match.

    Useful for validating that related resources belong to the same organization.

    Args:
        org_id_1: First organization ID
        org_id_2: Second organization ID
        error_message: Custom error message

    Raises:
        HTTPException: 400 if organizations don't match

    Example:
        # Ensure student and class are in same organization
        verify_org_match(student.org_id, class.org_id, "Student and class must be in same organization")
    """
    if org_id_1 != org_id_2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )


# ============================================================================
# Session/Result Access Control
# ============================================================================


def verify_session_access(
    session_user_id: str, session_org_id: Optional[str], user: UserContext
) -> None:
    """Verify user can access a session/exam.

    Rules:
    - Admin: Can access any session
    - Teacher: Can access sessions in their organization
    - Student: Can only access their own sessions

    Args:
        session_user_id: User ID who owns the session
        session_org_id: Organization ID of the session
        user: Current user context

    Raises:
        HTTPException: 403 if access is denied
    """
    # Admin can access anything
    if user.is_admin():
        return

    # Student: must own the session
    if user.is_student():
        if session_user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access your own sessions",
            )
        return

    # Teacher/Counselor: must be same organization
    if user.is_teacher() or user.is_counselor():
        if not session_org_id or not user.org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Missing organization information",
            )

        if session_org_id != user.org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Session belongs to different organization",
            )
        return

    # Unknown role: deny
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Insufficient permissions",
    )


# ============================================================================
# Bulk Operations
# ============================================================================


def filter_by_org(
    items: list[Any], user: UserContext, org_id_attr: str = "org_id"
) -> list[Any]:
    """Filter a list of items by organization.

    Useful for in-memory filtering when database filtering isn't possible.

    Args:
        items: List of objects with org_id attribute
        user: Current user context
        org_id_attr: Name of the org_id attribute

    Returns:
        Filtered list containing only accessible items

    Example:
        all_students = get_all_students()
        accessible_students = filter_by_org(all_students, user)
    """
    # Admin sees all
    if user.is_admin():
        return items

    # Regular users: filter to their org
    if not user.org_id:
        return []  # No org → no access

    return [item for item in items if getattr(item, org_id_attr, None) == user.org_id]


def validate_org_ids(org_ids: list[str], user: UserContext) -> None:
    """Validate that all organization IDs are accessible to the user.

    Useful for bulk operations where user provides multiple org_ids.

    Args:
        org_ids: List of organization IDs to validate
        user: Current user context

    Raises:
        HTTPException: 403 if any org_id is not accessible

    Example:
        # User wants to create assignments for multiple orgs
        validate_org_ids(request.org_ids, user)
    """
    # Admin can access any org
    if user.is_admin():
        return

    # Regular users: all org_ids must match their org
    if not user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: User has no organization",
        )

    invalid_orgs = [org_id for org_id in org_ids if org_id != user.org_id]
    if invalid_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Cannot access organizations: {invalid_orgs}",
        )


# ============================================================================
# Audit Logging
# ============================================================================


def log_org_access(
    user: UserContext,
    resource_type: str,
    resource_id: str,
    action: str,
    resource_org_id: Optional[str] = None,
) -> None:
    """Log organization-level access for audit trail.

    This is a placeholder for future audit logging implementation.

    Args:
        user: Current user context
        resource_type: Type of resource (e.g., "student", "class")
        resource_id: ID of the resource
        action: Action performed (e.g., "read", "update", "delete")
        resource_org_id: Organization ID of the resource
    """
    # TODO: Implement audit logging
    # For now, this is a no-op placeholder
    pass
