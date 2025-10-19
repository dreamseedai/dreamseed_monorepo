"""
Enable RLS and create policies for attempts, responses, item_bank

Revision ID: 20250101_0008
Revises: 20250101_0007
Create Date: 2025-01-01 00:08:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250101_0008'
down_revision = '20250101_0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # enable RLS
    op.execute("ALTER TABLE attempts  ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE responses ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE item_bank ENABLE ROW LEVEL SECURITY;")

    # attempts policies
    op.execute("DROP POLICY IF EXISTS attempts_policy_read  ON attempts;")
    op.execute("DROP POLICY IF EXISTS attempts_policy_write ON attempts;")
    op.execute(
        """
        CREATE POLICY attempts_policy_read ON attempts
          FOR SELECT USING (
            seedtest.is_admin()
            OR org_id = seedtest.current_org_id()
            OR org_id IS NULL
          );
        """
    )
    op.execute(
        """
        CREATE POLICY attempts_policy_write ON attempts
          FOR INSERT, UPDATE
          USING (
            seedtest.is_admin() OR org_id = seedtest.current_org_id()
          )
          WITH CHECK (
            seedtest.is_admin() OR org_id = seedtest.current_org_id()
          );
        """
    )

    # responses policies
    op.execute("DROP POLICY IF EXISTS responses_policy_read  ON responses;")
    op.execute("DROP POLICY IF EXISTS responses_policy_write ON responses;")
    op.execute(
        """
        CREATE POLICY responses_policy_read ON responses
          FOR SELECT USING (
            seedtest.is_admin()
            OR org_id = seedtest.current_org_id()
            OR org_id IS NULL
          );
        """
    )
    op.execute(
        """
        CREATE POLICY responses_policy_write ON responses
          FOR INSERT, UPDATE
          USING (
            seedtest.is_admin() OR org_id = seedtest.current_org_id()
          )
          WITH CHECK (
            seedtest.is_admin() OR org_id = seedtest.current_org_id()
          );
        """
    )

    # item_bank policies (owner_org_id)
    op.execute("DROP POLICY IF EXISTS item_bank_policy_read  ON item_bank;")
    op.execute("DROP POLICY IF EXISTS item_bank_policy_write ON item_bank;")
    op.execute(
        """
        CREATE POLICY item_bank_policy_read ON item_bank
          FOR SELECT USING (
            seedtest.is_admin()
            OR owner_org_id = seedtest.current_org_id()
            OR owner_org_id IS NULL
          );
        """
    )
    op.execute(
        """
        CREATE POLICY item_bank_policy_write ON item_bank
          FOR INSERT, UPDATE
          USING (
            seedtest.is_admin() OR owner_org_id = seedtest.current_org_id()
          )
          WITH CHECK (
            seedtest.is_admin() OR owner_org_id = seedtest.current_org_id()
          );
        """
    )


def downgrade() -> None:
    for stmt in [
        "DROP POLICY IF EXISTS item_bank_policy_write ON item_bank;",
        "DROP POLICY IF EXISTS item_bank_policy_read  ON item_bank;",
        "DROP POLICY IF EXISTS responses_policy_write ON responses;",
        "DROP POLICY IF EXISTS responses_policy_read  ON responses;",
        "DROP POLICY IF EXISTS attempts_policy_write ON attempts;",
        "DROP POLICY IF EXISTS attempts_policy_read  ON attempts;",
    ]:
        op.execute(stmt)
    op.execute("ALTER TABLE item_bank DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE responses DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE attempts  DISABLE ROW LEVEL SECURITY;")
