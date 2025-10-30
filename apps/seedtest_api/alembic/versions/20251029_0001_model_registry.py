"""
Model registry and analysis run tables

Revision ID: 20251029_0001_model_registry
Revises: 
Create Date: 2025-10-29
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251029_0001_model_registry"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_registry",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("version", sa.String(length=100), nullable=False),
        sa.Column("hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", "version", name="uq_model_registry_name_version"),
    )

    op.create_table(
        "analysis_run",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("model_id", sa.Integer, nullable=True),
        sa.Column("params", sa.JSON, nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("started_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime, nullable=True),
        sa.ForeignKeyConstraint(["model_id"], ["model_registry.id"], name="fk_analysis_run_model"),
    )

    op.create_table(
        "report_artifact",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("run_id", sa.Integer, nullable=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["analysis_run.id"], name="fk_report_artifact_run"),
    )

    op.create_table(
        "analysis_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("run_id", sa.Integer, nullable=True),
        sa.Column("level", sa.String(length=16), nullable=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("meta", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["analysis_run.id"], name="fk_analysis_log_run"),
    )

    # Optional: extend a hypothetical content_recommend_log with model/version columns if table exists
    try:
        op.add_column("content_recommend_log", sa.Column("model_name", sa.String(length=200), nullable=True))
        op.add_column("content_recommend_log", sa.Column("model_version", sa.String(length=100), nullable=True))
    except Exception:
        # Table may not exist in all deployments
        pass


def downgrade() -> None:
    # Drop optional columns if present
    try:
        op.drop_column("content_recommend_log", "model_version")
        op.drop_column("content_recommend_log", "model_name")
    except Exception:
        pass

    op.drop_table("analysis_log")
    op.drop_table("report_artifact")
    op.drop_table("analysis_run")
    op.drop_table("model_registry")
