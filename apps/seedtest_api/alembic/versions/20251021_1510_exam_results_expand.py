"""expand exam_results columns and indexes safely

Revision ID: 20251021_1510_exam_results_expand
Revises: 20251021_1010_exam_results_table
Create Date: 2025-10-21 15:10:00
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251021_1510_exam_results_expand"
down_revision = "20251021_1010_exam_results_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgcrypto for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Convert id to UUID if it was TEXT previously; set default
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'exam_results' AND column_name = 'id' AND data_type = 'text'
            ) THEN
                ALTER TABLE exam_results
                  ALTER COLUMN id TYPE uuid USING (
                    CASE
                      WHEN id ~ '^[0-9a-fA-F-]{36}$' THEN id::uuid
                      ELSE gen_random_uuid()
                    END
                  );
                ALTER TABLE exam_results ALTER COLUMN id SET DEFAULT gen_random_uuid();
            END IF;
        END$$;
        """
    )

    # Add missing columns if not exist
    op.execute(
        """
        DO $$ BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns WHERE table_name='exam_results' AND column_name='user_id'
          ) THEN
            ALTER TABLE exam_results ADD COLUMN user_id uuid NULL;
          END IF;
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns WHERE table_name='exam_results' AND column_name='exam_id'
          ) THEN
            ALTER TABLE exam_results ADD COLUMN exam_id integer NULL;
          END IF;
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns WHERE table_name='exam_results' AND column_name='standard_error'
          ) THEN
            ALTER TABLE exam_results ADD COLUMN standard_error numeric NULL;
          END IF;
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns WHERE table_name='exam_results' AND column_name='percentile'
          ) THEN
            ALTER TABLE exam_results ADD COLUMN percentile integer NULL;
          END IF;
        END $$;
        """
    )

    # Create composite index if not exists
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_exam_results_user_exam ON exam_results (user_id, exam_id)"
    )


def downgrade() -> None:
    # Best-effort: drop composite index and newly added columns if present
    op.execute("DROP INDEX IF EXISTS ix_exam_results_user_exam")
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='exam_results' AND column_name='percentile') THEN
            ALTER TABLE exam_results DROP COLUMN percentile;
          END IF;
          IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='exam_results' AND column_name='standard_error') THEN
            ALTER TABLE exam_results DROP COLUMN standard_error;
          END IF;
          IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='exam_results' AND column_name='exam_id') THEN
            ALTER TABLE exam_results DROP COLUMN exam_id;
          END IF;
          IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='exam_results' AND column_name='user_id') THEN
            ALTER TABLE exam_results DROP COLUMN user_id;
          END IF;
        END $$;
        """
    )
