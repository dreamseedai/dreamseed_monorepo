"""Add IRT drift monitoring tables.

Revision ID: 20251105_1000_irt_drift_tables
Revises: 20251103_1300_prophet_survival_columns
Create Date: 2025-11-05 10:00:00.000000

Adds drift monitoring tables:
- drift_windows: time-period definitions (baseline vs recent)
- item_calibration: windowed IRT estimation results
- drift_alerts: automated parameter drift alerts
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as psql

revision = "20251105_1000_irt_drift_tables"
down_revision = "20251103_1300_prophet_survival_columns"
branch_labels = None
depends_on = None


def table_exists(conn, name: str) -> bool:
    return conn.dialect.has_table(conn, name)


def upgrade() -> None:
    conn = op.get_bind()

    # drift_windows: time-period definitions
    if not table_exists(conn, "drift_windows"):
        op.create_table(
            "drift_windows",
            sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column(
                "start_at",
                sa.DateTime(timezone=True),
                nullable=False,
                comment="Window start (inclusive)",
            ),
            sa.Column(
                "end_at",
                sa.DateTime(timezone=True),
                nullable=False,
                comment="Window end (exclusive)",
            ),
            sa.Column(
                "population_tags",
                psql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="Cohort filters (e.g., grade/school/language)",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_drift_windows_times",
            "drift_windows",
            ["start_at", "end_at"],
        )

    # item_calibration: windowed IRT estimation results
    if not table_exists(conn, "item_calibration"):
        op.create_table(
            "item_calibration",
            sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column(
                "item_id",
                sa.BigInteger,
                nullable=False,
                comment="Item/question identifier",
            ),
            sa.Column(
                "window_id",
                sa.BigInteger,
                nullable=False,
                comment="Reference to drift_windows.id",
            ),
            # Parameter estimates
            sa.Column("a_hat", sa.Float, nullable=False, comment="Discrimination estimate"),
            sa.Column("b_hat", sa.Float, nullable=False, comment="Difficulty estimate"),
            sa.Column("c_hat", sa.Float, nullable=False, comment="Guessing estimate"),
            # 95% confidence/credible intervals
            sa.Column("a_l95", sa.Float, nullable=True, comment="a lower 95% CI"),
            sa.Column("a_u95", sa.Float, nullable=True, comment="a upper 95% CI"),
            sa.Column("b_l95", sa.Float, nullable=True, comment="b lower 95% CI"),
            sa.Column("b_u95", sa.Float, nullable=True, comment="b upper 95% CI"),
            sa.Column("c_l95", sa.Float, nullable=True, comment="c lower 95% CI"),
            sa.Column("c_u95", sa.Float, nullable=True, comment="c upper 95% CI"),
            # Sample size & diagnostics
            sa.Column("n", sa.Integer, nullable=False, comment="Response count"),
            sa.Column(
                "dif",
                psql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="DIF results by group (Δb/Δa, statistics)",
            ),
            sa.Column(
                "info",
                psql.JSONB(astext_type=sa.Text()),
                nullable=True,
                comment="θ-information function summary",
            ),
            sa.Column("run_id", sa.Text, nullable=True, comment="Job run identifier"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_item_calibration_item_window",
            "item_calibration",
            ["item_id", "window_id"],
        )
        op.create_index(
            "ix_item_calibration_run_id",
            "item_calibration",
            ["run_id"],
        )

    # drift_alerts: automated drift detection alerts
    if not table_exists(conn, "drift_alerts"):
        op.create_table(
            "drift_alerts",
            sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column("item_id", sa.BigInteger, nullable=False, comment="Item identifier"),
            sa.Column(
                "window_id",
                sa.BigInteger,
                nullable=False,
                comment="Recent window where drift detected",
            ),
            sa.Column(
                "metric",
                sa.Text,
                nullable=False,
                comment="Metric name (delta_a, delta_b, delta_c, dif_*)",
            ),
            sa.Column("value", sa.Float, nullable=False, comment="Observed metric value"),
            sa.Column(
                "threshold",
                sa.Float,
                nullable=False,
                comment="Threshold that was exceeded",
            ),
            sa.Column(
                "severity",
                sa.Text,
                nullable=False,
                comment="Alert severity: minor, moderate, severe",
            ),
            sa.Column("run_id", sa.Text, nullable=True, comment="Job run identifier"),
            sa.Column(
                "resolved_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="When action was taken",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("NOW()"),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_drift_alerts_item_created",
            "drift_alerts",
            ["item_id", "created_at"],
        )
        op.create_index(
            "ix_drift_alerts_severity",
            "drift_alerts",
            ["severity", "resolved_at"],
        )
        op.create_index(
            "ix_drift_alerts_run_id",
            "drift_alerts",
            ["run_id"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    if table_exists(conn, "drift_alerts"):
        op.drop_index("ix_drift_alerts_run_id", table_name="drift_alerts")
        op.drop_index("ix_drift_alerts_severity", table_name="drift_alerts")
        op.drop_index("ix_drift_alerts_item_created", table_name="drift_alerts")
        op.drop_table("drift_alerts")
    if table_exists(conn, "item_calibration"):
        op.drop_index("ix_item_calibration_run_id", table_name="item_calibration")
        op.drop_index("ix_item_calibration_item_window", table_name="item_calibration")
        op.drop_table("item_calibration")
    if table_exists(conn, "drift_windows"):
        op.drop_index("ix_drift_windows_times", table_name="drift_windows")
        op.drop_table("drift_windows")
