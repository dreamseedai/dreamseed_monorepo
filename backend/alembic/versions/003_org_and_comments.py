"""Add organization and report comment tables

Revision ID: 003_org_and_comments
Revises: 002_core_entities
Create Date: 2025-11-25 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_org_and_comments'
down_revision: Union[str, None] = '002_core_entities'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE organization_type AS ENUM ('public_school', 'private_school', 'academy', 'tutoring_center', 'private_tutor', 'homeschool')")
    op.execute("CREATE TYPE org_role AS ENUM ('org_admin', 'org_head_teacher', 'org_teacher', 'org_assistant')")
    op.execute("CREATE TYPE report_source_type AS ENUM ('school_teacher', 'academy_teacher', 'tutor')")
    op.execute("CREATE TYPE report_section AS ENUM ('summary', 'next_4w_plan', 'parent_guidance')")
    
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('type', sa.Enum('public_school', 'private_school', 'academy', 'tutoring_center', 'private_tutor', 'homeschool', name='organization_type'), nullable=False),
        sa.Column('external_code', sa.String(50), nullable=True, unique=True, comment='School code, business registration number, etc.'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create org_memberships table
    op.create_table(
        'org_memberships',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.Enum('org_admin', 'org_head_teacher', 'org_teacher', 'org_assistant', name='org_role'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'organization_id', name='uq_org_membership_user_org'),
    )
    
    # Create student_org_enrollments table
    op.create_table(
        'student_org_enrollments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('label', sa.String(100), nullable=True, comment="Class, homeroom, or group identifier (e.g., '2-3', 'SAT Group A')"),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('student_id', 'organization_id', name='uq_student_org_enrollment_student_org'),
    )
    
    # Create report_comments table
    op.create_table(
        'report_comments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_type', sa.Enum('school_teacher', 'academy_teacher', 'tutor', name='report_source_type'), nullable=False),
        sa.Column('section', sa.Enum('summary', 'next_4w_plan', 'parent_guidance', name='report_section'), nullable=False),
        sa.Column('language', sa.String(5), nullable=False, server_default='ko', comment='ISO 639-1 language code (ko, en)'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False, comment='Report period start date (inclusive)'),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False, comment='Report period end date (inclusive)'),
        sa.Column('content', sa.Text(), nullable=False, comment='Comment text (Markdown supported)'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false', comment='Published comments appear in parent reports'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for org tables
    op.create_index('ix_org_memberships_user_id', 'org_memberships', ['user_id'])
    op.create_index('ix_org_memberships_organization_id', 'org_memberships', ['organization_id'])
    op.create_index('ix_student_org_enrollments_student_id', 'student_org_enrollments', ['student_id'])
    op.create_index('ix_student_org_enrollments_organization_id', 'student_org_enrollments', ['organization_id'])
    
    # Create indexes for report_comments (optimized for queries)
    op.create_index('ix_report_comments_student_period', 'report_comments', ['student_id', 'period_start', 'is_published'])
    op.create_index('ix_report_comments_organization_period', 'report_comments', ['organization_id', 'period_start'])
    op.create_index('ix_report_comments_author_id', 'report_comments', ['author_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_report_comments_author_id', 'report_comments')
    op.drop_index('ix_report_comments_organization_period', 'report_comments')
    op.drop_index('ix_report_comments_student_period', 'report_comments')
    op.drop_index('ix_student_org_enrollments_organization_id', 'student_org_enrollments')
    op.drop_index('ix_student_org_enrollments_student_id', 'student_org_enrollments')
    op.drop_index('ix_org_memberships_organization_id', 'org_memberships')
    op.drop_index('ix_org_memberships_user_id', 'org_memberships')
    
    # Drop tables
    op.drop_table('report_comments')
    op.drop_table('student_org_enrollments')
    op.drop_table('org_memberships')
    op.drop_table('organizations')
    
    # Drop enums
    op.execute('DROP TYPE report_section')
    op.execute('DROP TYPE report_source_type')
    op.execute('DROP TYPE org_role')
    op.execute('DROP TYPE organization_type')
