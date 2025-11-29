"""Create prophet_fit_meta and prophet_anomalies tables

Revision ID: 20251102_1600_prophet_meta
Revises: 20251102_1500_brms_meta
Create Date: 2025-11-02 16:00:00
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "20251102_1600_prophet_meta"
down_revision = "20251102_1500_brms_meta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Check if prophet_fit_meta exists
    result1 = conn.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'prophet_fit_meta'
            )
            """
        )
    )
    table1_exists = result1.scalar()

    if not table1_exists:
        conn.execute(
            text(
                """
                CREATE TABLE prophet_fit_meta (
                    run_id TEXT PRIMARY KEY,
                    metric TEXT NOT NULL,
                    changepoints JSONB NOT NULL DEFAULT '[]'::jsonb,
                    forecast JSONB NOT NULL DEFAULT '[]'::jsonb,
                    fit_meta JSONB NOT NULL DEFAULT '{}'::jsonb,
                    fitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_prophet_fit_meta_fitted_at
                ON prophet_fit_meta (fitted_at DESC)
                """
            )
        )
        print("[INFO] Created prophet_fit_meta table")
    else:
        print("[INFO] prophet_fit_meta table already exists, skipping")

    # Check if prophet_anomalies exists
    result2 = conn.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'prophet_anomalies'
            )
            """
        )
    )
    table2_exists = result2.scalar()

    if not table2_exists:
        conn.execute(
            text(
                """
                CREATE TABLE prophet_anomalies (
                    run_id TEXT NOT NULL,
                    week_start DATE NOT NULL,
                    metric TEXT NOT NULL,
                    value FLOAT,
                    expected FLOAT,
                    anomaly_score FLOAT,
                    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (run_id, week_start, metric)
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_prophet_anomalies_detected_at
                ON prophet_anomalies (detected_at DESC)
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_prophet_anomalies_week_metric
                ON prophet_anomalies (week_start DESC, metric)
                """
            )
        )
        print("[INFO] Created prophet_anomalies table")
    else:
        print("[INFO] prophet_anomalies table already exists, skipping")


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS prophet_anomalies"))
    conn.execute(text("DROP TABLE IF EXISTS prophet_fit_meta"))
