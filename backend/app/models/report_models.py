"""
Report comment models - Teacher/tutor comments for parent reports.

This module handles the multi-source comment system for parent reports:
1. School teachers write summaries and guidance
2. Academy teachers/tutors provide supplementary insights
3. Comments are organized by section (summary, plan, guidance)
4. Bilingual support (Korean primary, English secondary)

Comment Flow:
1. Teacher/tutor writes comment via API (draft or published)
2. Parent report builder fetches published comments
3. PDF generation combines IRT ability data + comments
4. Parents see consolidated report with all sources

Architecture:
- ReportComment: Single comment entry (1 section, 1 language, 1 period)
- Multiple comments combine to form complete report
- source_type distinguishes school vs academy vs tutor
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ============================================================================
# Enums
# ============================================================================


class ReportSourceType(str, enum.Enum):
    """
    Comment source classification (mapped from organization type).

    Mapping from OrganizationType:
    - PUBLIC_SCHOOL, PRIVATE_SCHOOL → SCHOOL_TEACHER
    - ACADEMY, TUTORING_CENTER → ACADEMY_TEACHER
    - PRIVATE_TUTOR → TUTOR

    Used for:
    - PDF section headers ("학교 선생님 의견" vs "학원/튜터 의견")
    - Comment priority logic (school primary, tutor secondary)
    - UI filtering (show only school comments, etc.)
    """

    SCHOOL_TEACHER = "school_teacher"  # 공립/사립 학교 선생님
    ACADEMY_TEACHER = "academy_teacher"  # 입시학원 강사
    TUTOR = "tutor"  # 개인 과외/튜터


class ReportSection(str, enum.Enum):
    """
    Parent report section identifier.

    Sections:
    - SUMMARY: Overall assessment for the period (1-3 paragraphs)
    - NEXT_4W_PLAN: Recommended activities for next 4 weeks (bullet points)
    - PARENT_GUIDANCE: Advice for parents on supporting student (1-2 paragraphs)

    Each section can have multiple comments from different sources
    (e.g., school summary + tutor summary).
    """

    SUMMARY = "summary"  # 종합 소견 (전체 요약)
    NEXT_4W_PLAN = "next_4w_plan"  # 다음 4주 계획 (추천 활동)
    PARENT_GUIDANCE = "parent_guidance"  # 학부모 가이드 (학습 지원 조언)


# ============================================================================
# Models
# ============================================================================


class ReportComment(Base):
    """
    Teacher/tutor comment for parent report section.

    Granularity: One comment = 1 student + 1 period + 1 section + 1 language + 1 source

    Example records:
    - Student A, Nov 2025, SUMMARY, ko, SCHOOL_TEACHER → "최근 4주 동안..."
    - Student A, Nov 2025, SUMMARY, en, SCHOOL_TEACHER → "During the past 4 weeks..."
    - Student A, Nov 2025, SUMMARY, ko, TUTOR → "수학 과외 관점에서..."
    - Student A, Nov 2025, NEXT_4W_PLAN, ko, SCHOOL_TEACHER → "1. 기초 개념 복습..."

    Constraints:
    - No unique constraint (same student/period/section can have multiple sources)
    - Foreign keys: student_id, organization_id, author_id (all CASCADE on delete)

    Workflow:
    1. Teacher writes draft (is_published=False)
    2. Teacher reviews/edits
    3. Teacher publishes (is_published=True)
    4. Parent report builder fetches published comments only
    5. PDF generation combines comments from all sources

    Indexing strategy:
    - (student_id, period_start, is_published): Fetch published comments for student
    - (organization_id, period_start): Org-level report generation
    - (author_id): Teacher's comment history
    """

    __tablename__ = "report_comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    source_type: Mapped[ReportSourceType] = mapped_column(
        Enum(ReportSourceType, name="report_source_type"),
        nullable=False,
    )

    section: Mapped[ReportSection] = mapped_column(
        Enum(ReportSection, name="report_section"),
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(5),
        default="ko",
        nullable=False,
        comment="ISO 639-1 language code (ko, en)",
    )

    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Report period start date (inclusive)",
    )

    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Report period end date (inclusive)",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Comment text (Markdown supported)",
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Published comments appear in parent reports",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    # student: Mapped["User"] = relationship("User", foreign_keys=[student_id])  # TODO: Uncomment
    # author: Mapped["User"] = relationship("User", foreign_keys=[author_id])    # TODO: Uncomment
    # organization: Mapped["Organization"] = relationship("Organization")         # TODO: Uncomment

    def __repr__(self) -> str:
        return (
            f"<ReportComment(id={self.id}, student={self.student_id}, "
            f"section={self.section}, source={self.source_type}, published={self.is_published})>"
        )


# ============================================================================
# Helper Functions
# ============================================================================


def determine_source_type(org_type: str) -> ReportSourceType:
    """
    Map organization type to report source type.

    Args:
        org_type: OrganizationType value

    Returns:
        ReportSourceType for PDF section labeling

    Examples:
        >>> determine_source_type("public_school")
        ReportSourceType.SCHOOL_TEACHER
        >>> determine_source_type("academy")
        ReportSourceType.ACADEMY_TEACHER
        >>> determine_source_type("private_tutor")
        ReportSourceType.TUTOR
    """
    from app.models.org_models import OrganizationType

    if org_type in (
        OrganizationType.PUBLIC_SCHOOL.value,
        OrganizationType.PRIVATE_SCHOOL.value,
    ):
        return ReportSourceType.SCHOOL_TEACHER
    elif org_type in (
        OrganizationType.ACADEMY.value,
        OrganizationType.TUTORING_CENTER.value,
    ):
        return ReportSourceType.ACADEMY_TEACHER
    elif org_type == OrganizationType.PRIVATE_TUTOR.value:
        return ReportSourceType.TUTOR
    else:
        # Fallback for homeschool or unknown types
        return ReportSourceType.TUTOR


def can_edit_comment(comment: ReportComment, user_id: uuid.UUID) -> bool:
    """
    Check if user can edit this comment.

    Rules:
    - Author can always edit their own comments
    - Org admins can edit all comments from their org

    Args:
        comment: ReportComment instance
        user_id: Current user UUID

    Returns:
        True if user can edit this comment
    """
    return comment.author_id == user_id
    # TODO: Add org admin check when OrgMembership relationship is available


def validate_period(period_start: datetime, period_end: datetime) -> None:
    """
    Validate report period dates.

    Rules:
    - period_end must be after period_start
    - Period must be <= 12 weeks (84 days)
    - Period must not be in the future (> now + 1 day)

    Raises:
        ValueError: If period is invalid
    """
    if period_start >= period_end:
        raise ValueError("period_end must be after period_start")

    delta = period_end - period_start
    if delta.days > 84:
        raise ValueError("Report period cannot exceed 12 weeks (84 days)")

    if period_end > datetime.utcnow() + delta.__class__(days=1):
        raise ValueError("Report period cannot be in the future")
