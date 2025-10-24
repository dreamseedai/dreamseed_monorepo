"""convert exam_results.user_id to TEXT if currently UUID

Revision ID: 20251022_0900_exam_results_userid_text
Revises: 20251021_1510_exam_results_expand
Create Date: 2025-10-22 09:00:00
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '20251022_0900_exam_results_userid_text'
down_revision = '20251021_1510_exam_results_expand'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='exam_results' AND column_name='user_id' AND data_type='uuid'
          ) THEN
            ALTER TABLE exam_results
              ALTER COLUMN user_id TYPE text USING user_id::text;
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
  # Irreversible safely: keep TEXT type
  pass
