"""
Organization models - Multi-level permission system.

This module defines the 3-axis structure:
1. User Type (student, teacher, parent, admin)
2. Organization Type (school, academy, tutoring center, private tutor)
3. Organization Role (org_admin, org_head_teacher, org_teacher, org_assistant)

Architecture:
- Organization: Schools, academies, tutoring centers
- OrgMembership: Teachers/admins belonging to organizations
- StudentOrgEnrollment: Students enrolled in organizations

Example flows:
- Public school teacher: User(role=teacher) + OrgMembership(org=public_school, role=org_teacher)
- Academy tutor: User(role=teacher) + OrgMembership(org=academy, role=org_teacher)
- Student: User(role=student) + StudentOrgEnrollment(org=public_school) + StudentOrgEnrollment(org=academy)
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ============================================================================
# Enums
# ============================================================================


class OrganizationType(str, enum.Enum):
    """
    Organization classification by educational context.

    Determines:
    - Permission scope (school-wide vs individual tutoring)
    - Report comment source labeling
    - Dashboard feature availability
    """

    PUBLIC_SCHOOL = "public_school"  # 공립학교
    PRIVATE_SCHOOL = "private_school"  # 사립학교
    ACADEMY = "academy"  # 입시/보충 학원
    TUTORING_CENTER = "tutoring_center"  # 종합 과외 센터
    PRIVATE_TUTOR = "private_tutor"  # 개인 과외
    HOMESCHOOL = "homeschool"  # 홈스쿨


class OrgRole(str, enum.Enum):
    """
    Role within an organization (not global user role).

    Hierarchy:
    - ORG_ADMIN: Full org management, add/remove members, billing
    - ORG_HEAD_TEACHER: Academic leadership, approve reports, manage classes
    - ORG_TEACHER: Regular teaching duties, view assigned students
    - ORG_ASSISTANT: Limited access, data entry support
    """

    ORG_ADMIN = "org_admin"  # 조직 관리자
    ORG_HEAD_TEACHER = "org_head_teacher"  # 수석 교사/학년부장
    ORG_TEACHER = "org_teacher"  # 일반 교사
    ORG_ASSISTANT = "org_assistant"  # 보조 인력


# ============================================================================
# Models
# ============================================================================


class Organization(Base):
    """
    Educational organization (school, academy, tutoring center).

    Represents a single institution where teachers work and students enroll.
    Multiple organizations can coexist (e.g., student attends school + academy).

    Relationships:
    - memberships: Teachers/admins working at this org
    - enrollments: Students enrolled in this org
    """

    __tablename__ = "organizations"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType, name="organization_type"),
        nullable=False,
    )

    external_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        comment="School code, business registration number, etc.",
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    memberships: Mapped[list["OrgMembership"]] = relationship(
        "OrgMembership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    enrollments: Mapped[list["StudentOrgEnrollment"]] = relationship(
        "StudentOrgEnrollment",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, type={self.type})>"


class OrgMembership(Base):
    """
    Teacher/admin membership in an organization.

    Links a teacher/admin user to an organization with a specific role.
    One teacher can belong to multiple organizations (e.g., teaching at 2 schools).

    Examples:
    - User(role=teacher) + OrgMembership(org=school_a, role=org_teacher)
    - User(role=teacher) + OrgMembership(org=academy_b, role=org_head_teacher)

    Constraints:
    - Unique (user_id, organization_id): One role per org
    - User must be teacher or admin (enforced at application layer)
    """

    __tablename__ = "org_memberships"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "organization_id",
            name="uq_org_membership_user_org",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[OrgRole] = mapped_column(
        Enum(OrgRole, name="org_role"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    # user: Mapped["User"] = relationship("User")  # TODO: Uncomment when User model ready
    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="memberships",
    )

    def __repr__(self) -> str:
        return f"<OrgMembership(user_id={self.user_id}, org={self.organization_id}, role={self.role})>"


class StudentOrgEnrollment(Base):
    """
    Student enrollment in an organization.

    Links a student to an organization (school, academy, tutor).
    Students can enroll in multiple organizations simultaneously
    (e.g., main school + entrance exam academy + private tutor).

    Examples:
    - Student attends public_school (homeroom 2-3)
    - Student attends academy (SAT prep class)
    - Student has private_tutor (1:1 math tutoring)

    Constraints:
    - Unique (student_id, organization_id): No duplicate enrollments
    - Student_id must be user with role=student (enforced at app layer)

    Fields:
    - label: Optional class/group identifier (e.g., "2-3", "SAT Prep Group A")
    """

    __tablename__ = "student_org_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "organization_id",
            name="uq_student_org_enrollment_student_org",
        ),
    )

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

    label: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Class, homeroom, or group identifier (e.g., '2-3', 'SAT Group A')",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    # student: Mapped["User"] = relationship("User")  # TODO: Uncomment when User model ready
    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="enrollments",
    )

    def __repr__(self) -> str:
        return f"<StudentOrgEnrollment(student_id={self.student_id}, org={self.organization_id}, label={self.label})>"


# ============================================================================
# Helper Functions
# ============================================================================


def is_school_org(org_type: OrganizationType) -> bool:
    """Check if organization is a school (public or private)."""
    return org_type in (
        OrganizationType.PUBLIC_SCHOOL,
        OrganizationType.PRIVATE_SCHOOL,
    )


def is_tutoring_org(org_type: OrganizationType) -> bool:
    """Check if organization is a tutoring/academy organization."""
    return org_type in (
        OrganizationType.ACADEMY,
        OrganizationType.TUTORING_CENTER,
        OrganizationType.PRIVATE_TUTOR,
    )


def can_write_reports(role: OrgRole) -> bool:
    """Check if role has permission to write parent reports."""
    return role in (
        OrgRole.ORG_ADMIN,
        OrgRole.ORG_HEAD_TEACHER,
        OrgRole.ORG_TEACHER,
    )
