"""Add GIN index on exam_results.result_json

Revision ID: 20251023_1100_exam_results_gin_index
Revises: 20251022_1700_exam_results_defaults_and_percentile_numeric
Create Date: 2025-10-23 11:00:00
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251023_1100_exam_results_gin_index"
down_revision = "20251022_1700_exam_results_defaults_and_percentile_numeric"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Safe-create a GIN index on result_json for future JSONB containment queries
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS exam_results_result_json_gin
        ON exam_results
        USING GIN (result_json)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS exam_results_result_json_gin
        """
    )
