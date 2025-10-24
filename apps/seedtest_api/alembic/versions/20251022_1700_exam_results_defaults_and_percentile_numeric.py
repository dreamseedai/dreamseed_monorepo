"""set status default and make percentile numeric

Revision ID: 20251022_1700_exam_results_defaults_and_percentile_numeric
Revises: 20251022_1530_exam_results_add_org_id
Create Date: 2025-10-22 17:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251022_1700_exam_results_defaults_and_percentile_numeric"
down_revision = "20251022_1530_exam_results_add_org_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure a database-level default for status
    op.execute("ALTER TABLE exam_results ALTER COLUMN status SET DEFAULT 'ready'")
    # Allow fractional percentiles by converting to numeric
    op.execute(
        "ALTER TABLE exam_results ALTER COLUMN percentile TYPE numeric USING percentile::numeric"
    )


def downgrade() -> None:
    # Drop default on status
    op.execute("ALTER TABLE exam_results ALTER COLUMN status DROP DEFAULT")
    # Revert percentile to integer (fractional data will be truncated)
    op.execute(
        "ALTER TABLE exam_results ALTER COLUMN percentile TYPE integer USING percentile::integer"
    )
