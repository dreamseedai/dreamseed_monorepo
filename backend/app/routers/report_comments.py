"""
Report comment API endpoints for teachers/tutors.

This module handles teacher/tutor input for parent reports:
- Create/update/publish comments
- Fetch existing comments (drafts + published)
- Support for school teachers and tutors (unified API)

Workflow:
1. Teacher writes draft comment (POST /comments, is_published=false)
2. Teacher edits draft (PUT /comments/{id})
3. Teacher publishes (PUT /comments/{id}/publish)
4. Parent report builder fetches published comments

Authorization:
- get_current_teacher_any_org: School teachers + tutors + academy teachers
- Comment ownership: Author can edit/delete their own comments
- Org admins: Can edit/delete any comments from their org (TODO)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_current_teacher_any_org
from app.models.org_models import Organization, OrgMembership
from app.models.report_models import (
    ReportComment,
    ReportSection,
    ReportSourceType,
    determine_source_type,
    validate_period,
)
from app.models.user import User


router = APIRouter(prefix="/api/teacher/reports", tags=["reports:comments"])


# ============================================================================
# Schemas
# ============================================================================


class ReportCommentCreate(BaseModel):
    """
    Request body for creating a new report comment.

    Fields:
    - studentId: Target student UUID
    - periodStart/periodEnd: Report period (must be ≤ 12 weeks)
    - section: SUMMARY | NEXT_4W_PLAN | PARENT_GUIDANCE
    - language: 'ko' or 'en'
    - content: Comment text (Markdown supported, 1-10000 chars)
    - publish: If true, is_published=true (visible in parent reports)
    """

    studentId: uuid.UUID = Field(..., description="Student UUID")
    periodStart: datetime = Field(..., description="Report period start (inclusive)")
    periodEnd: datetime = Field(..., description="Report period end (inclusive)")
    section: ReportSection = Field(..., description="Report section")
    language: str = Field("ko", max_length=5, description="Language code (ko, en)")
    content: str = Field(
        ..., min_length=1, max_length=10000, description="Comment text"
    )
    publish: bool = Field(False, description="Publish immediately (default: draft)")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace-only")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in ("ko", "en"):
            raise ValueError("Language must be 'ko' or 'en'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "studentId": "123e4567-e89b-12d3-a456-426614174000",
                "periodStart": "2025-11-01T00:00:00Z",
                "periodEnd": "2025-11-30T23:59:59Z",
                "section": "summary",
                "language": "ko",
                "content": "최근 4주 동안 수학 실력이 안정적으로 향상되었습니다. 특히 대수 문제 풀이에서 두각을 나타내고 있으며...",
                "publish": False,
            }
        }


class ReportCommentUpdate(BaseModel):
    """Request body for updating an existing comment."""

    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    language: Optional[str] = Field(None, max_length=5)
    publish: Optional[bool] = Field(None, description="Set publication status")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Content cannot be empty or whitespace-only")
        return v


class ReportCommentResponse(BaseModel):
    """Response schema for report comment."""

    id: int
    studentId: uuid.UUID
    organizationId: uuid.UUID
    authorId: uuid.UUID
    sourceType: ReportSourceType
    section: ReportSection
    language: str
    periodStart: datetime
    periodEnd: datetime
    content: str
    isPublished: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "studentId": "123e4567-e89b-12d3-a456-426614174000",
                "organizationId": "789e4567-e89b-12d3-a456-426614174000",
                "authorId": "456e4567-e89b-12d3-a456-426614174000",
                "sourceType": "school_teacher",
                "section": "summary",
                "language": "ko",
                "periodStart": "2025-11-01T00:00:00Z",
                "periodEnd": "2025-11-30T23:59:59Z",
                "content": "최근 4주 동안 수학 실력이 안정적으로 향상되었습니다...",
                "isPublished": True,
                "createdAt": "2025-11-25T10:00:00Z",
                "updatedAt": "2025-11-25T12:00:00Z",
            }
        }


class ReportCommentList(BaseModel):
    """Response for list of comments."""

    total: int
    comments: list[ReportCommentResponse]


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/{student_id}/comments",
    response_model=ReportCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_report_comment(
    student_id: uuid.UUID,
    payload: ReportCommentCreate,
    context: tuple[User, Organization, OrgMembership] = Depends(
        get_current_teacher_any_org
    ),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Create a new report comment for a student.

    Authorization: Teacher with any organization membership (school or tutoring).

    Business logic:
    - Validates period (≤ 12 weeks, not in future)
    - Determines source_type from org.type (school → SCHOOL_TEACHER, academy → ACADEMY_TEACHER, etc.)
    - Allows multiple comments for same (student, period, section) from different sources
    - Draft by default (is_published=false), can publish immediately with publish=true

    Example:
        POST /api/teacher/reports/{student_id}/comments
        {
            "periodStart": "2025-11-01",
            "periodEnd": "2025-11-30",
            "section": "summary",
            "language": "ko",
            "content": "최근 4주 동안...",
            "publish": false
        }
    """
    user, org, _ = context

    # Validate student_id matches payload
    if student_id != payload.studentId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="student_id in path must match studentId in payload",
        )

    # Validate period
    try:
        validate_period(payload.periodStart, payload.periodEnd)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # TODO: Verify student_id exists and is enrolled in org (optional - enforce at app layer)

    # Determine source type from org type
    source_type = determine_source_type(org.type.value)

    # Create comment
    comment = ReportComment(
        student_id=payload.studentId,
        organization_id=org.id,
        author_id=user.id,
        source_type=source_type,
        section=payload.section,
        language=payload.language,
        period_start=payload.periodStart,
        period_end=payload.periodEnd,
        content=payload.content,
        is_published=payload.publish,
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return ReportCommentResponse.model_validate(comment)


@router.get("/{student_id}/comments", response_model=ReportCommentList)
async def list_report_comments(
    student_id: uuid.UUID,
    period_start: Optional[datetime] = Query(
        None, description="Filter by period start"
    ),
    period_end: Optional[datetime] = Query(None, description="Filter by period end"),
    section: Optional[ReportSection] = Query(None, description="Filter by section"),
    published_only: bool = Query(False, description="Show only published comments"),
    context: tuple[User, Organization, OrgMembership] = Depends(
        get_current_teacher_any_org
    ),
    db: AsyncSession = Depends(get_async_session),
):
    """
    List report comments for a student.

    Filters:
    - Student: Required (path param)
    - Organization: Automatically filtered to current teacher's org
    - Period: Optional range filter
    - Section: Optional
    - Published: If true, show only published comments

    Returns comments ordered by updated_at DESC (most recent first).
    """
    _, org, _ = context

    # Build query
    filters = [
        ReportComment.student_id == student_id,
        ReportComment.organization_id == org.id,
    ]

    if period_start:
        filters.append(ReportComment.period_start >= period_start)
    if period_end:
        filters.append(ReportComment.period_end <= period_end)
    if section:
        filters.append(ReportComment.section == section)
    if published_only:
        filters.append(ReportComment.is_published == True)

    result = await db.execute(
        select(ReportComment)
        .where(and_(*filters))
        .order_by(ReportComment.updated_at.desc())
    )
    comments = result.scalars().all()

    return ReportCommentList(
        total=len(comments),
        comments=[ReportCommentResponse.model_validate(c) for c in comments],
    )


@router.get("/comments/{comment_id}", response_model=ReportCommentResponse)
async def get_report_comment(
    comment_id: int,
    context: tuple[User, Organization, OrgMembership] = Depends(
        get_current_teacher_any_org
    ),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get a single report comment by ID.

    Authorization: Comment must belong to teacher's organization.
    """
    _, org, _ = context

    result = await db.execute(
        select(ReportComment).where(ReportComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Verify comment belongs to teacher's org
    if comment.organization_id != org.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access comments from your organization",
        )

    return ReportCommentResponse.model_validate(comment)


@router.put("/comments/{comment_id}", response_model=ReportCommentResponse)
async def update_report_comment(
    comment_id: int,
    payload: ReportCommentUpdate,
    context: tuple[User, Organization, OrgMembership] = Depends(
        get_current_teacher_any_org
    ),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update an existing report comment.

    Authorization:
    - Comment author can edit their own comments
    - Org admins can edit any comments from their org (TODO)

    Partial update: Only provided fields are updated.
    """
    user, org, _ = context

    result = await db.execute(
        select(ReportComment).where(ReportComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Verify ownership
    if comment.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )

    # Verify org membership
    if comment.organization_id != org.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit comments from your organization",
        )

    # Update fields
    if payload.content is not None:
        comment.content = payload.content
    if payload.language is not None:
        comment.language = payload.language
    if payload.publish is not None:
        comment.is_published = payload.publish

    comment.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(comment)

    return ReportCommentResponse.model_validate(comment)


@router.put("/comments/{comment_id}/publish", response_model=ReportCommentResponse)
async def publish_report_comment(
    comment_id: int,
    context: tuple[User, Organization, OrgMembership] = Depends(
        get_current_teacher_any_org
    ),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Publish a report comment (make visible in parent reports).

    Shortcut for updating is_published=true.
    """
    user, org, _ = context

    result = await db.execute(
        select(ReportComment).where(ReportComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Verify ownership
    if comment.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish your own comments",
        )

    if comment.organization_id != org.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish comments from your organization",
        )

    comment.is_published = True
    comment.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(comment)

    return ReportCommentResponse.model_validate(comment)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report_comment(
    comment_id: int,
    context: tuple[User, Organization, OrgMembership] = Depends(
        get_current_teacher_any_org
    ),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Delete a report comment.

    Authorization: Comment author only (or org admins - TODO).
    """
    user, org, _ = context

    result = await db.execute(
        select(ReportComment).where(ReportComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Verify ownership
    if comment.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

    if comment.organization_id != org.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete comments from your organization",
        )

    await db.delete(comment)
    await db.commit()

    return None
