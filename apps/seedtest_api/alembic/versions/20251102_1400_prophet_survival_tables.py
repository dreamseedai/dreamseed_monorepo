"""Prophet and Survival analysis tables

Revision ID: 20251102_1400
Revises: 20251031_2110
Create Date: 2025-11-02 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251102_1400"
down_revision = "20251031_2110_attempt_view"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Prophet forecast and Survival analysis tables."""

    # Check if tables already exist (may have been created by other migrations)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Prophet fit metadata table
    if "prophet_fit_meta" not in existing_tables:
        op.create_table(
            "prophet_fit_meta",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "metric", sa.Text(), nullable=False, comment="Metric name (e.g., I_t)"
            ),
            sa.Column(
                "changepoints",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Detected changepoints",
            ),
            sa.Column(
                "forecast",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                comment="Forecast data (insample + future)",
            ),
            sa.Column(
                "fit_meta",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Model metadata (RMSE, MAE, etc.)",
            ),
            sa.Column(
                "fitted_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_prophet_fit_meta")),
            sa.UniqueConstraint("run_id", name=op.f("uq_prophet_fit_meta_run_id")),
        )
        op.create_index(
            op.f("ix_prophet_fit_meta_fitted_at"),
            "prophet_fit_meta",
            ["fitted_at"],
            unique=False,
        )
        op.create_index(
            op.f("ix_prophet_fit_meta_metric"),
            "prophet_fit_meta",
            ["metric"],
            unique=False,
        )

    # Prophet anomalies table
    if "prophet_anomalies" not in existing_tables:
        op.create_table(
            "prophet_anomalies",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("week_start", sa.Date(), nullable=False),
            sa.Column("metric", sa.Text(), nullable=False),
            sa.Column(
                "value", sa.Float(), nullable=True, comment="Actual observed value"
            ),
            sa.Column(
                "expected",
                sa.Float(),
                nullable=True,
                comment="Prophet expected value (yhat)",
            ),
            sa.Column(
                "anomaly_score",
                sa.Float(),
                nullable=False,
                comment="Z-score or anomaly magnitude",
            ),
            sa.Column(
                "detected_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_prophet_anomalies")),
            sa.UniqueConstraint(
                "run_id",
                "week_start",
                "metric",
                name=op.f("uq_prophet_anomalies_run_week_metric"),
            ),
        )
        op.create_index(
            op.f("ix_prophet_anomalies_run_id"),
            "prophet_anomalies",
            ["run_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_prophet_anomalies_week_start"),
            "prophet_anomalies",
            ["week_start"],
            unique=False,
        )
        op.create_index(
            op.f("ix_prophet_anomalies_detected_at"),
            "prophet_anomalies",
            ["detected_at"],
            unique=False,
        )

    # Survival fit metadata table
    if "survival_fit_meta" not in existing_tables:
        op.create_table(
            "survival_fit_meta",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "family",
                sa.Text(),
                nullable=False,
                comment="Model family (cox, weibull, etc.)",
            ),
            sa.Column(
                "event_threshold_days",
                sa.Integer(),
                nullable=False,
                comment="Days threshold for event definition",
            ),
            sa.Column(
                "coefficients",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Model coefficients",
            ),
            sa.Column(
                "concordance",
                sa.Float(),
                nullable=True,
                comment="Concordance index (C-statistic)",
            ),
            sa.Column(
                "n", sa.Integer(), nullable=True, comment="Number of observations"
            ),
            sa.Column(
                "survival_curve",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Baseline survival curve",
            ),
            sa.Column(
                "run_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_survival_fit_meta")),
            sa.UniqueConstraint("run_id", name=op.f("uq_survival_fit_meta_run_id")),
        )
        op.create_index(
            op.f("ix_survival_fit_meta_run_at"),
            "survival_fit_meta",
            ["run_at"],
            unique=False,
        )
        op.create_index(
            op.f("ix_survival_fit_meta_family"),
            "survival_fit_meta",
            ["family"],
            unique=False,
        )

    # Survival risk scores table
    if "survival_risk" not in existing_tables:
        op.create_table(
            "survival_risk",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column(
                "risk_score",
                sa.Float(),
                nullable=False,
                comment="Normalized risk score (0-1)",
            ),
            sa.Column(
                "hazard_ratio",
                sa.Float(),
                nullable=True,
                comment="Hazard ratio relative to baseline",
            ),
            sa.Column(
                "rank_percentile",
                sa.Float(),
                nullable=True,
                comment="Risk rank percentile (0-1)",
            ),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_survival_risk")),
        )
        op.create_index(
            op.f("ix_survival_risk_run_id"), "survival_risk", ["run_id"], unique=False
        )
        op.create_index(
            op.f("ix_survival_risk_user_id"), "survival_risk", ["user_id"], unique=False
        )
        op.create_index(
            op.f("ix_survival_risk_updated_at"),
            "survival_risk",
            ["updated_at"],
            unique=False,
        )
        op.create_index(
            op.f("ix_survival_risk_user_updated"),
            "survival_risk",
            ["user_id", "updated_at"],
            unique=False,
        )


def downgrade() -> None:
    """Drop Prophet and Survival tables."""
    op.drop_index(op.f("ix_survival_risk_user_updated"), table_name="survival_risk")
    op.drop_index(op.f("ix_survival_risk_updated_at"), table_name="survival_risk")
    op.drop_index(op.f("ix_survival_risk_user_id"), table_name="survival_risk")
    op.drop_index(op.f("ix_survival_risk_run_id"), table_name="survival_risk")
    op.drop_table("survival_risk")

    op.drop_index(op.f("ix_survival_fit_meta_family"), table_name="survival_fit_meta")
    op.drop_index(op.f("ix_survival_fit_meta_run_at"), table_name="survival_fit_meta")
    op.drop_table("survival_fit_meta")

    op.drop_index(
        op.f("ix_prophet_anomalies_detected_at"), table_name="prophet_anomalies"
    )
    op.drop_index(
        op.f("ix_prophet_anomalies_week_start"), table_name="prophet_anomalies"
    )
    op.drop_index(op.f("ix_prophet_anomalies_run_id"), table_name="prophet_anomalies")
    op.drop_table("prophet_anomalies")

    op.drop_index(op.f("ix_prophet_fit_meta_metric"), table_name="prophet_fit_meta")
    op.drop_index(op.f("ix_prophet_fit_meta_fitted_at"), table_name="prophet_fit_meta")
    op.drop_table("prophet_fit_meta")
