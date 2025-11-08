"""Example router demonstrating unified authentication and multi-tenancy.

This is a reference implementation showing best practices for:
1. Using unified authentication (JWT + Headers)
2. Role-based access control (RBAC)
3. Multi-tenancy data isolation
4. Session/resource access control

Use this as a template when migrating existing routers or creating new ones.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

# Unified authentication imports
from apps.seedtest_api.auth.unified import (
    UserContext,
    get_current_user,
    require_role,
    require_admin,
    require_teacher_or_admin,
)

# Multi-tenancy imports
from apps.seedtest_api.auth.multitenancy import (
    verify_org_access,
    verify_session_access,
    get_org_filter_sql,
    get_org_filter_value,
)

# Database
from apps.seedtest_api.db.session import get_db

router = APIRouter(prefix="/api/example", tags=["example"])


# ============================================================================
# Pydantic Models (Example)
# ============================================================================

class StudentResponse(BaseModel):
    id: str
    name: str
    org_id: str
    grade: int


class ClassResponse(BaseModel):
    id: str
    name: str
    org_id: str
    teacher_id: str


class ExamSessionResponse(BaseModel):
    id: str
    user_id: str
    org_id: str
    exam_id: str
    score: Optional[float]


# ============================================================================
# Example 1: Basic Authentication
# ============================================================================

@router.get("/me")
async def get_current_user_info(user: UserContext = Depends(get_current_user)):
    """Get current authenticated user information.
    
    Authentication: Any authenticated user (JWT or Headers)
    Authorization: None (all authenticated users)
    """
    return {
        "user_id": user.user_id,
        "org_id": user.org_id,
        "roles": user.roles,
        "auth_method": user.auth_method,
        "is_admin": user.is_admin(),
        "is_teacher": user.is_teacher(),
        "is_student": user.is_student(),
    }


# ============================================================================
# Example 2: Role-based Access Control
# ============================================================================

@router.get("/admin/stats")
async def get_admin_stats(user: UserContext = Depends(require_admin)):
    """Admin-only endpoint.
    
    Authentication: JWT or Headers
    Authorization: Admin role required
    """
    return {
        "message": "Admin statistics",
        "total_users": 1000,
        "total_orgs": 50,
    }


@router.get("/classes", dependencies=[Depends(require_role("teacher", "admin"))])
async def list_classes(
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List classes (teacher or admin only).
    
    Authentication: JWT or Headers
    Authorization: Teacher or Admin role
    Multi-tenancy: Filtered by organization (except admin)
    """
    # Example: SQLAlchemy query with org filter
    # stmt = select(Class).where(enforce_org_filter(Class.org_id, user))
    # classes = db.execute(stmt).scalars().all()
    
    # Mock response
    return {
        "classes": [
            {"id": "class1", "name": "Math 101", "org_id": user.org_id},
            {"id": "class2", "name": "Science 201", "org_id": user.org_id},
        ],
        "filtered_by_org": user.org_id if not user.is_admin() else None,
    }


@router.post("/classes", dependencies=[Depends(require_teacher_or_admin)])
async def create_class(
    name: str,
    user: UserContext = Depends(get_current_user)
):
    """Create a new class.
    
    Authentication: JWT or Headers
    Authorization: Teacher or Admin role
    Multi-tenancy: Class created in user's organization
    """
    if not user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no organization"
        )
    
    # Create class in user's organization
    new_class = {
        "id": "new_class_id",
        "name": name,
        "org_id": user.org_id,
        "teacher_id": user.user_id,
    }
    
    return new_class


# ============================================================================
# Example 3: Multi-tenancy Data Isolation
# ============================================================================

@router.get("/students")
async def list_students(
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
    grade: Optional[int] = Query(None, description="Filter by grade")
):
    """List students in user's organization.
    
    Authentication: JWT or Headers
    Authorization: Any authenticated user
    Multi-tenancy: Automatically filtered by organization
    
    Rules:
    - Admin: Can see students from all organizations
    - Teacher/Counselor: Can see students from their organization
    - Student: Can only see themselves
    """
    # Example: SQLAlchemy with org filter
    # stmt = select(Student).where(enforce_org_filter(Student.org_id, user))
    # if grade:
    #     stmt = stmt.where(Student.grade == grade)
    # students = db.execute(stmt).scalars().all()
    
    # For students, only return their own data
    if user.is_student():
        return {
            "students": [
                {"id": user.user_id, "name": "Self", "org_id": user.org_id, "grade": 10}
            ]
        }
    
    # Mock response for teachers/admins
    org_filter = get_org_filter_value(user)
    return {
        "students": [
            {"id": "student1", "name": "Alice", "org_id": user.org_id or "org1", "grade": 10},
            {"id": "student2", "name": "Bob", "org_id": user.org_id or "org1", "grade": 11},
        ],
        "filtered_by_org": org_filter,
        "total": 2,
    }


@router.get("/students/{student_id}")
async def get_student(
    student_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific student details.
    
    Authentication: JWT or Headers
    Authorization: Depends on role
    Multi-tenancy: Verified by organization
    
    Rules:
    - Admin: Can access any student
    - Teacher/Counselor: Can access students in their organization
    - Student: Can only access themselves
    """
    # Example: Fetch student from database
    # student = db.query(Student).filter(Student.id == student_id).first()
    # if not student:
    #     raise HTTPException(404, "Student not found")
    
    # Mock student data
    student = {
        "id": student_id,
        "name": "Alice",
        "org_id": "org123",
        "grade": 10,
    }
    
    # Verify organization access
    verify_org_access(student["org_id"], user, "student")
    
    # Students can only see themselves
    if user.is_student() and student_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only access their own data"
        )
    
    return student


# ============================================================================
# Example 4: Session/Exam Access Control
# ============================================================================

@router.get("/exams/{session_id}")
async def get_exam_session(
    session_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get exam session details.
    
    Authentication: JWT or Headers
    Authorization: Complex rules based on role
    
    Rules:
    - Admin: Can access any session
    - Teacher: Can access sessions in their organization
    - Student: Can only access their own sessions
    """
    # Example: Fetch session from database
    # session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    # if not session:
    #     raise HTTPException(404, "Session not found")
    
    # Mock session data
    session = {
        "id": session_id,
        "user_id": "student123",
        "org_id": "org123",
        "exam_id": "exam456",
        "score": 85.5,
    }
    
    # Verify session access (Admin/Teacher/Student rules)
    verify_session_access(
        session_user_id=session["user_id"],
        session_org_id=session["org_id"],
        user=user
    )
    
    return session


@router.get("/exams/{session_id}/analysis")
async def get_exam_analysis(
    session_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analysis for an exam session.
    
    This is similar to the existing analysis.py endpoint,
    but using unified authentication and multi-tenancy.
    """
    # Fetch session
    # session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    # if not session:
    #     raise HTTPException(404, "Session not found")
    
    # Mock session
    session = {
        "id": session_id,
        "user_id": "student123",
        "org_id": "org123",
    }
    
    # Verify access
    verify_session_access(session["user_id"], session["org_id"], user)
    
    # Return analysis
    return {
        "session_id": session_id,
        "analysis": {
            "score": 85.5,
            "percentile": 75,
            "strengths": ["algebra", "geometry"],
            "weaknesses": ["calculus"],
        }
    }


# ============================================================================
# Example 5: Raw SQL with Multi-tenancy
# ============================================================================

@router.get("/reports/weekly")
async def get_weekly_report(
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly report using raw SQL.
    
    Demonstrates how to use get_org_filter_sql() for raw SQL queries.
    """
    # Generate org filter SQL
    org_filter = get_org_filter_sql("org_id", user)
    
    # Raw SQL query with org filter
    sql = f"""
        SELECT 
            DATE_TRUNC('week', created_at) as week,
            COUNT(*) as total_sessions,
            AVG(score) as avg_score
        FROM exam_sessions
        WHERE {org_filter}
        GROUP BY week
        ORDER BY week DESC
        LIMIT 10
    """
    
    # Execute query
    results = db.execute(text(sql)).fetchall()
    
    # Format results
    report = [
        {
            "week": str(row[0]),
            "total_sessions": row[1],
            "avg_score": float(row[2]) if row[2] else 0.0
        }
        for row in results
    ]
    
    return {
        "report": report,
        "org_filter_applied": org_filter,
    }


# ============================================================================
# Example 6: Conditional Logic Based on Role
# ============================================================================

@router.get("/dashboard")
async def get_dashboard(user: UserContext = Depends(get_current_user)):
    """Get role-specific dashboard data.
    
    Returns different data based on user's role.
    """
    if user.is_admin():
        return {
            "type": "admin_dashboard",
            "stats": {
                "total_users": 1000,
                "total_orgs": 50,
                "total_exams": 5000,
            }
        }
    
    elif user.is_teacher() or user.is_counselor():
        return {
            "type": "teacher_dashboard",
            "org_id": user.org_id,
            "stats": {
                "my_classes": 5,
                "my_students": 120,
                "pending_reviews": 15,
            }
        }
    
    elif user.is_student():
        return {
            "type": "student_dashboard",
            "user_id": user.user_id,
            "stats": {
                "completed_exams": 10,
                "avg_score": 85.5,
                "next_exam": "Math Final",
            }
        }
    
    else:
        return {
            "type": "viewer_dashboard",
            "message": "Read-only access"
        }


# ============================================================================
# Example 7: Bulk Operations with Org Validation
# ============================================================================

@router.post("/students/bulk-assign")
async def bulk_assign_students(
    student_ids: List[str],
    class_id: str,
    user: UserContext = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    """Assign multiple students to a class.
    
    Validates that all students belong to the user's organization.
    """
    # Fetch class
    # class_obj = db.query(Class).filter(Class.id == class_id).first()
    # if not class_obj:
    #     raise HTTPException(404, "Class not found")
    
    # Mock class
    class_obj = {"id": class_id, "org_id": "org123"}
    
    # Verify user can access this class
    verify_org_access(class_obj["org_id"], user, "class")
    
    # Fetch students
    # students = db.query(Student).filter(Student.id.in_(student_ids)).all()
    
    # Verify all students belong to the same organization
    # for student in students:
    #     verify_org_access(student.org_id, user, "student")
    
    return {
        "message": f"Assigned {len(student_ids)} students to class {class_id}",
        "class_id": class_id,
        "student_ids": student_ids,
    }


# ============================================================================
# Example 8: Error Handling
# ============================================================================

@router.get("/protected")
async def protected_endpoint(user: UserContext = Depends(get_current_user)):
    """Example of proper error handling.
    
    Shows how authentication/authorization errors are automatically handled.
    """
    # If we reach here, user is authenticated
    # HTTPException 401 is automatically raised if auth fails
    
    # Manual authorization check
    if not user.has_role("admin", "teacher"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires admin or teacher role"
        )
    
    return {"message": "Access granted"}


# ============================================================================
# Migration Notes
# ============================================================================

"""
MIGRATION FROM LEGACY AUTH:

Before (legacy deps.py):
    from ..deps import User, get_current_user, require_session_access
    
    @router.get("/endpoint")
    async def endpoint(
        current_user: User = Depends(get_current_user),
        _: None = Depends(require_session_access),
    ):
        if current_user.is_admin():
            ...

After (unified auth):
    from apps.seedtest_api.auth.unified import get_current_user, UserContext
    from apps.seedtest_api.auth.multitenancy import verify_session_access
    
    @router.get("/endpoint")
    async def endpoint(
        user: UserContext = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Fetch session
        session = db.query(ExamSession).filter(...).first()
        
        # Verify access
        verify_session_access(session.user_id, session.org_id, user)
        
        if user.is_admin():
            ...

Key Changes:
1. User → UserContext
2. current_user → user (convention)
3. require_session_access → verify_session_access (with explicit session data)
4. Add org filtering to all queries: enforce_org_filter()
5. Use canonicalized roles (admin, teacher, counselor, student, viewer)
"""
