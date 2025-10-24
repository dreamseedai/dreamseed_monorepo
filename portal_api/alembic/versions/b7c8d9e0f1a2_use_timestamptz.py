"""normalize datetime columns to timestamptz (UTC)

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2025-09-25 00:00:10.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision = "b7c8d9e0f1a2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC';"
    )
    op.execute(
        "ALTER TABLE content ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC';"
    )
    op.execute(
        "ALTER TABLE content ALTER COLUMN updated_at TYPE timestamptz USING updated_at AT TIME ZONE 'UTC';"
    )
    op.execute(
        "ALTER TABLE attempts ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC';"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE attempts ALTER COLUMN created_at TYPE timestamp;")
    op.execute("ALTER TABLE content ALTER COLUMN updated_at TYPE timestamp;")
    op.execute("ALTER TABLE content ALTER COLUMN created_at TYPE timestamp;")
    op.execute("ALTER TABLE users ALTER COLUMN created_at TYPE timestamp;")
