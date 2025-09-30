"""indexes for content_audit_log

Revision ID: ee8f940d61f4
Revises: b517600fb8bb
Create Date: 2025-09-25 00:38:37.673667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee8f940d61f4'
down_revision: Union[str, None] = 'b517600fb8bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_cal_user_id_id ON content_audit_log (user_id, id DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cal_content_id_id ON content_audit_log (content_id, id DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cal_action_id ON content_audit_log (action, id DESC)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_cal_action_id")
    op.execute("DROP INDEX IF EXISTS ix_cal_content_id_id")
    op.execute("DROP INDEX IF EXISTS ix_cal_user_id_id")
