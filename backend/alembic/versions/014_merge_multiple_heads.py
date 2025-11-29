"""Merge multiple heads (003_org_and_comments, 003_zones_ai_requests, 013_add_assignment_tables)

Revision ID: 014_merge_multiple_heads
Revises: 003_org_and_comments, 003_zones_ai_requests, 013_add_assignment_tables
Create Date: 2025-11-28 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "014_merge_multiple_heads"
down_revision = (
    "003_org_and_comments",
    "003_zones_ai_requests",
    "013_add_assignment_tables",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge migration - no schema changes
    pass


def downgrade() -> None:
    # This is a merge migration - no schema changes
    pass
