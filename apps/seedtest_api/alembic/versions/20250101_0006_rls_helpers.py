"""
RLS helpers: schema and functions (current_org_id, is_admin)

Revision ID: 20250101_0006
Revises: 20250101_0005
Create Date: 2025-01-01 00:06:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250101_0006'
down_revision = '20250101_0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS seedtest;")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION seedtest.current_org_id()
        RETURNS int LANGUAGE plpgsql STABLE AS $$
        DECLARE v text;
        BEGIN
          BEGIN
            v := current_setting('seedtest.org_id', true);
          EXCEPTION WHEN others THEN
            RETURN NULL;
          END;
          IF v IS NULL OR v = '' THEN
            RETURN NULL;
          END IF;
          RETURN v::int;
        END $$;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION seedtest.is_admin()
        RETURNS boolean LANGUAGE sql STABLE AS $$
          SELECT current_user IN ('seedtest_admin');
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS seedtest.is_admin();")
    op.execute("DROP FUNCTION IF EXISTS seedtest.current_org_id();")
    # keep schema
