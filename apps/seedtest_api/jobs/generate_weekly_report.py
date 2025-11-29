"""
Generate weekly student reports using Quarto.
- Loads user KPIs, ability trends, and goal attainment data
- Renders Quarto template to HTML/PDF
- Uploads to S3 and stores artifact URL in database
Environment:
  REPORT_WEEK_START (optional): Week start date (YYYY-MM-DD, defaults to last week)
  REPORT_FORMAT (optional): Output format (html, pdf, default: html)
  S3_BUCKET (required): S3 bucket name for report storage
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (required): AWS credentials
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from ..services.db import get_session
from ..services.metrics import week_start as iso_week_start


def load_user_kpis(session, user_id: str, week_start: date) -> Optional[Dict[str, Any]]:
    """Load weekly KPIs for a user."""
    result = session.execute(
        text(
            """
            SELECT kpis
            FROM weekly_kpi
            WHERE user_id = :user_id
              AND week_start = :week_start
            LIMIT 1
        """
        ),
        {"user_id": user_id, "week_start": week_start},
    )
    row = result.fetchone()
    if row:
        kpis = row[0]
        if isinstance(kpis, str):
            return json.loads(kpis)
        return kpis
    return None


def load_ability_trend(session, user_id: str, weeks: int = 8) -> List[Dict[str, Any]]:
    """Load ability (theta) trend over multiple weeks."""
    since_date = date.today() - timedelta(weeks=weeks)
    result = session.execute(
        text(
            """
            SELECT 
                theta,
                se,
                fitted_at
            FROM mirt_ability
            WHERE user_id = :user_id
              AND fitted_at >= :since
            ORDER BY fitted_at ASC
        """
        ),
        {"user_id": user_id, "since": since_date},
    )
    rows = result.fetchall()
    return [
        {
            "theta": float(row[0]) if row[0] is not None else None,
            "se": float(row[1]) if row[1] is not None else None,
            "date": row[2].isoformat() if row[2] else None,
        }
        for row in rows
    ]


def load_goal_data(session, user_id: str) -> List[Dict[str, Any]]:
    """Load interest/goal data for a user."""
    result = session.execute(
        text(
            """
            SELECT 
                subject_id,
                interest_1_5,
                target_score,
                target_date,
                updated_at
            FROM interest_goal
            WHERE student_id::text = :user_id
            ORDER BY updated_at DESC
        """
        ),
        {"user_id": user_id},
    )
    rows = result.fetchall()
    return [
        {
            "subject_id": row[0],
            "interest": row[1],
            "target_score": row[2],
            "target_date": row[3].isoformat() if row[3] else None,
            "updated_at": row[4].isoformat() if row[4] else None,
        }
        for row in rows
    ]


def load_topic_features(
    session, user_id: str, week_start: date
) -> List[Dict[str, Any]]:
    """Load daily topic features for the week."""
    week_end = week_start + timedelta(days=6)
    result = session.execute(
        text(
            """
            SELECT 
                topic_id,
                date,
                attempts,
                correct,
                avg_time_ms,
                rt_median,
                hints,
                theta_mean,
                theta_sd,
                improvement
            FROM features_topic_daily
            WHERE user_id = :user_id
              AND date >= :week_start
              AND date <= :week_end
            ORDER BY topic_id, date
        """
        ),
        {"user_id": user_id, "week_start": week_start, "week_end": week_end},
    )
    rows = result.fetchall()
    return [
        {
            "topic_id": row[0],
            "date": row[1].isoformat() if row[1] else None,
            "attempts": row[2],
            "correct": row[3],
            "avg_time_ms": row[4],
            "rt_median": float(row[5]) if row[5] is not None else None,
            "hints": row[6],
            "theta_estimate": float(row[7]) if row[7] is not None else None,
            "theta_sd": float(row[8]) if row[8] is not None else None,
            "improvement": float(row[9]) if row[9] is not None else None,
        }
        for row in rows
    ]


def load_item_params(session, user_id: str, weeks: int = 4) -> List[Dict[str, Any]]:
    """Load IRT item parameters for items attempted by user recently."""
    since_date = date.today() - timedelta(weeks=weeks)
    result = session.execute(
        text(
            """
            SELECT DISTINCT
                p.item_id,
                p.params->>'a' AS discrimination,
                p.params->>'b' AS difficulty,
                p.params->>'c' AS guessing,
                p.model,
                p.fitted_at
            FROM mirt_item_params p
            INNER JOIN attempt a ON p.item_id = a.item_id::text
            WHERE a.student_id::text = :user_id
              AND a.completed_at >= :since
              AND p.params ? 'b'
            ORDER BY p.fitted_at DESC
            LIMIT 200
        """
        ),
        {"user_id": user_id, "since": since_date},
    )
    rows = result.fetchall()
    return [
        {
            "item_id": row[0],
            "discrimination": float(row[1]) if row[1] is not None else None,
            "difficulty": float(row[2]) if row[2] is not None else None,
            "guessing": float(row[3]) if row[3] is not None else None,
            "model": row[4],
            "fitted_at": row[5].isoformat() if row[5] else None,
        }
        for row in rows
    ]


def render_quarto_report(
    template_dir: Path,
    data: Dict[str, Any],
    output_dir: Path,
    format: str = "html",
) -> Optional[Path]:
    """Render Quarto report from template.

    Args:
        template_dir: Directory containing Quarto template (_quarto.yml, *.qmd files)
        data: Data dictionary to pass to template
        output_dir: Directory to write rendered output
        format: Output format (html, pdf)

    Returns:
        Path to rendered output file or None if failed
    """
    # Write data JSON for template
    data_file = template_dir / "_data.json"
    with open(data_file, "w") as f:
        json.dump(data, f, indent=2, default=str)

    # Run quarto render
    try:
        cmd = [
            "quarto",
            "render",
            str(template_dir),
            "--to",
            format,
            "--output-dir",
            str(output_dir),
        ]
        subprocess.run(
            cmd,
            cwd=str(template_dir),
            capture_output=True,
            text=True,
            check=True,
        )

        # Find output file
        if format == "html":
            output_file = output_dir / "index.html"
        else:
            output_file = output_dir / "index.pdf"

        if output_file.exists():
            return output_file
        else:
            print(f"[ERROR] Quarto output not found: {output_file}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Quarto render failed: {e}")
        print(f"[ERROR] stdout: {e.stdout}")
        print(f"[ERROR] stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print(
            "[ERROR] Quarto not found in PATH. Install Quarto: https://quarto.org/docs/get-started/"
        )
        return None


def upload_to_s3(file_path: Path, bucket: str, key: str) -> Optional[str]:
    """Upload file to S3 and return public URL.

    Args:
        file_path: Local file path
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        S3 URL or None if failed
    """
    try:
        import boto3  # type: ignore
        from botocore.exceptions import ClientError  # type: ignore
    except ImportError:
        print("[ERROR] boto3 not installed. Install: pip install boto3")
        return None

    try:
        region = os.getenv("AWS_REGION", "ap-northeast-2")
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=region,
        )

        s3_client.upload_file(
            str(file_path),
            bucket,
            key,
            ExtraArgs={
                "ContentType": (
                    "text/html" if file_path.suffix == ".html" else "application/pdf"
                )
            },
        )

        # Generate public URL
        url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
        return url

    except ClientError as e:
        print(f"[ERROR] S3 upload failed: {e}")
        return None


def save_report_artifact(
    session,
    user_id: str,
    week_start: date,
    report_url: str,
    format: str = "html",
) -> None:
    """Save report artifact URL to database."""
    # Create report_artifacts table if it doesn't exist (via migration)
    # For now, we'll use a simple INSERT with ON CONFLICT
    session.execute(
        text(
            """
            INSERT INTO report_artifacts (user_id, week_start, format, url, generated_at)
            VALUES (:user_id, :week_start, :format, :url, NOW())
            ON CONFLICT (user_id, week_start, format)
            DO UPDATE SET
                url = EXCLUDED.url,
                generated_at = NOW()
        """
        ),
        {
            "user_id": user_id,
            "week_start": week_start,
            "format": format,
            "url": report_url,
        },
    )
    session.commit()


def _load_linking_constants(session) -> Dict[str, Any]:
    """Load latest linking/equating constants from mirt_fit_meta.model_spec.linking_constants.
    Returns empty dict if none.
    """
    result = session.execute(
        text(
            """
            SELECT model_spec, run_id, fitted_at
            FROM mirt_fit_meta
            ORDER BY fitted_at DESC
            LIMIT 1
            """
        )
    )
    row = result.fetchone()
    if not row:
        return {}
    model_spec = row[0] if row[0] is not None else {}
    if isinstance(model_spec, str):
        try:
            model_spec = json.loads(model_spec)
        except Exception:
            model_spec = {}
    lc = model_spec.get("linking_constants") or {}
    if lc:
        lc["_run_id"] = row[1]
        lc["_fitted_at"] = row[2].isoformat() if row[2] else None
    return lc


def load_bayesian_growth(session, user_id: str) -> Optional[Dict[str, Any]]:
    """Load Bayesian goal probability for user.

    Current pipeline updates weekly_kpi with P (goal probability) and sigma (uncertainty).
    This loader reads the latest values from weekly_kpi. If unavailable, returns None.
    """
    result = session.execute(
        text(
            """
            SELECT kpis
            FROM weekly_kpi
            WHERE user_id = :user_id
            ORDER BY week_start DESC
            LIMIT 1
            """
        ),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        return None
    k = row[0] or {}
    if isinstance(k, str):
        try:
            k = json.loads(k)
        except Exception:
            k = {}
    p = k.get("P")
    sigma = k.get("sigma")
    if p is None and sigma is None:
        return None
    out: Dict[str, Any] = {}
    if p is not None:
        try:
            out["P"] = float(p)
        except Exception:
            pass
    if sigma is not None:
        try:
            out["sigma"] = float(sigma)
        except Exception:
            pass
    return out or None


def load_prophet_forecast(session, user_id: str) -> Optional[Dict[str, Any]]:
    """Load latest Prophet forecast and anomalies.

    Current pipeline stores a global forecast (not per-user) in prophet_fit_meta:
      columns: run_id, metric, changepoints, forecast, fit_meta, fitted_at
    This loader fetches the latest entry and returns it.
    """
    result = session.execute(
        text(
            """
            SELECT 
                fit_meta,
                forecast,
                fitted_at
            FROM prophet_fit_meta
            ORDER BY fitted_at DESC
            LIMIT 1
            """
        )
    )
    row = result.fetchone()
    if not row:
        return None

    fit_meta = row[0] if row[0] else {}
    if isinstance(fit_meta, str):
        try:
            fit_meta = json.loads(fit_meta)
        except Exception:
            fit_meta = {}

    forecast_data = row[1] if row[1] else {}
    if isinstance(forecast_data, str):
        try:
            forecast_data = json.loads(forecast_data)
        except Exception:
            forecast_data = {}

    # Anomalies table schema: run_id, week_start, metric, value, expected, anomaly_score, detected_at
    anomalies_result = session.execute(
        text(
            """
            SELECT week_start, value, anomaly_score
            FROM prophet_anomalies
            ORDER BY detected_at DESC
            LIMIT 12
            """
        )
    )
    anomalies = [
        {
            "week": r[0].isoformat() if r[0] else None,
            "score": float(r[1]) if r[1] is not None else None,
            "anomaly_score": float(r[2]) if r[2] is not None else None,
        }
        for r in anomalies_result.fetchall()
    ]

    return {
        "fit_meta": fit_meta,
        "forecast_data": forecast_data,
        "anomalies": anomalies,
        "fitted_at": row[2].isoformat() if row[2] else None,
    }


def load_survival_risk(session, user_id: str) -> Optional[Dict[str, Any]]:
    """Load survival analysis risk score and model metadata for user.

    Returns latest churn risk from weekly_kpi.S, and the most recent survival model
    coefficients and hazard ratios from survival_fit_meta.
    """
    # Get latest risk score from weekly_kpi.S
    kpi_result = session.execute(
        text(
            """
            SELECT kpis->>'S' AS churn_risk
            FROM weekly_kpi
            WHERE user_id = :user_id
            ORDER BY week_start DESC
            LIMIT 1
        """
        ),
        {"user_id": user_id},
    )
    kpi_row = kpi_result.fetchone()
    churn_risk = None
    if kpi_row and kpi_row[0]:
        try:
            churn_risk = float(kpi_row[0])
        except Exception:
            pass

    # Get survival model meta
    meta_result = session.execute(
        text(
            """
            SELECT coefficients, hazard_ratios, fitted_at
            FROM survival_fit_meta
            ORDER BY fitted_at DESC
            LIMIT 1
            """
        )
    )
    meta_row = meta_result.fetchone()
    fit_meta = {}
    if meta_row:
        coeffs = meta_row[0]
        hrs = meta_row[1]
        if isinstance(coeffs, str):
            try:
                coeffs = json.loads(coeffs)
            except Exception:
                coeffs = {}
        if isinstance(hrs, str):
            try:
                hrs = json.loads(hrs)
            except Exception:
                hrs = {}
        fit_meta = {"coefficients": coeffs or {}, "hazard_ratios": hrs or {}}

    return {
        "churn_risk": churn_risk,
        "fit_meta": fit_meta,
        "fitted_at": (
            meta_row[2].isoformat()
            if meta_row and len(meta_row) > 2 and meta_row[2]
            else None
        ),
    }


def load_user_segment(session, user_id: str) -> Optional[Dict[str, Any]]:
    """Load user segment assignment from clustering.
    Returns segment label, features snapshot, and segment metadata.
    """
    result = session.execute(
        text(
            """
            SELECT 
                s.segment_label,
                s.features_snapshot,
                s.assigned_at,
                m.segment_description
            FROM user_segment s
            LEFT JOIN segment_meta m ON s.segment_label = m.segment_label
            WHERE s.user_id = :user_id
            ORDER BY s.assigned_at DESC
            LIMIT 1
        """
        ),
        {"user_id": user_id},
    )
    row = result.fetchone()
    if not row:
        return None

    features = row[1] if row[1] else {}
    if isinstance(features, str):
        try:
            features = json.loads(features)
        except Exception:
            features = {}

    return {
        "segment_label": row[0],
        "features_snapshot": features,
        "assigned_at": row[2].isoformat() if row[2] else None,
        "segment_description": row[3],
    }


def generate_report_for_user(
    user_id: str,
    week_start: date,
    template_dir: Path,
    output_format: str = "html",
    s3_bucket: Optional[str] = None,
) -> Optional[str]:
    """Generate weekly report for a single user.

    Returns:
        Report URL (S3 or local path) or None if failed
    """
    with get_session() as session:
        # Load data
        kpis = load_user_kpis(session, user_id, week_start)
        ability_trend = load_ability_trend(session, user_id)
        goals = load_goal_data(session, user_id)
        topic_features = load_topic_features(session, user_id, week_start)
        item_params = load_item_params(session, user_id)
        recommendations = (
            []
        )  # load_top_recommendations(session, user_id, week_start, top_n=5)
        linking_constants = _load_linking_constants(session)

        # Load advanced analytics data
        bayesian_growth = load_bayesian_growth(session, user_id)
        prophet_forecast = load_prophet_forecast(session, user_id)
        survival_risk = load_survival_risk(session, user_id)
        user_segment = load_user_segment(session, user_id)

        if not kpis:
            print(f"[WARN] No KPIs found for user={user_id} week={week_start}")
            return None

        # Prepare data for template
        data = {
            "user_id": user_id,
            "week_start": week_start.isoformat(),
            "kpis": kpis,
            "ability_trend": ability_trend,
            "goals": goals,
            "topic_features": topic_features,
            "item_params": item_params,
            "recommendations": recommendations,
            "linking_constants": linking_constants,
            "bayesian_growth": bayesian_growth,
            "prophet_forecast": prophet_forecast,
            "survival_risk": survival_risk,
            "user_segment": user_segment,
        }

        # Render Quarto report
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            rendered_file = render_quarto_report(
                template_dir,
                data,
                output_dir,
                format=output_format,
            )

            if not rendered_file:
                return None

            # Upload to S3 if bucket provided
            if s3_bucket:
                key = (
                    f"reports/{user_id}/{week_start.isoformat()}/report.{output_format}"
                )
                url = upload_to_s3(rendered_file, s3_bucket, key)

                if url:
                    # Save to database
                    save_report_artifact(
                        session, user_id, week_start, url, output_format
                    )
                    return url
                else:
                    return None
            else:
                # Return local path (for testing)
                return str(rendered_file)


def main(target_week_start: Optional[date] = None, dry_run: bool = False) -> int:
    """Generate weekly reports for all active users.

    Args:
        target_week_start: Week start date (defaults to last week)
        dry_run: If True, skip S3 upload and DB save

    Returns:
        Exit code: 0 on success, 1 on failure
    """
    if target_week_start is None:
        # Default to last week
        target_week_start = iso_week_start(date.today() - timedelta(weeks=1))

    template_dir = Path(__file__).parent.parent.parent / "reports" / "quarto"
    if not template_dir.exists():
        print(f"[ERROR] Template directory not found: {template_dir}")
        return 1

    output_format = os.getenv("REPORT_FORMAT", "html")
    s3_bucket = os.getenv("S3_BUCKET") if not dry_run else None

    if not s3_bucket and not dry_run:
        print("[ERROR] S3_BUCKET environment variable required")
        return 1

    # Load active users from weekly_kpi
    with get_session() as session:
        result = session.execute(
            text(
                """
                SELECT DISTINCT user_id
                FROM weekly_kpi
                WHERE week_start = :week_start
                LIMIT 1000
            """
            ),
            {"week_start": target_week_start},
        )
        user_ids = [row[0] for row in result.fetchall()]

    if not user_ids:
        print(f"[INFO] No users found for week={target_week_start}")
        return 0

    print(
        f"[INFO] Generating reports for {len(user_ids)} users; week={target_week_start}, format={output_format}, dry_run={dry_run}"
    )

    processed = 0
    failed = 0

    # Ensure type narrowing for static analyzers
    assert target_week_start is not None

    for user_id in user_ids:
        try:
            url = generate_report_for_user(
                user_id,
                target_week_start,
                template_dir,
                output_format,
                s3_bucket,
            )
            if url:
                processed += 1
                if os.getenv("DEBUG", "").lower() == "true":
                    print(f"[DEBUG] OK user={user_id} url={url}")
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"[ERROR] user={user_id} error={e}")

    print(
        f"[INFO] Summary: processed={processed}, failed={failed}, week={target_week_start}"
    )
    return 0 if failed == 0 else 1


def cli() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate weekly student reports")
    parser.add_argument(
        "--week",
        help="Week start date (YYYY-MM-DD, defaults to last week)",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--user",
        help="User ID for single-user report generation (optional)",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip S3 upload and DB save",
    )

    args = parser.parse_args()

    target_week = None
    if args.week:
        try:
            target_week = datetime.strptime(args.week, "%Y-%m-%d").date()
        except ValueError:
            print(f"[ERROR] Invalid date format: {args.week} (expected YYYY-MM-DD)")
            exit(1)

    # Single user mode
    if args.user:
        if not target_week:
            target_week = iso_week_start(date.today() - timedelta(weeks=1))

        template_dir = Path(__file__).parent.parent.parent / "reports" / "quarto"
        if not template_dir.exists():
            print(f"[ERROR] Template directory not found: {template_dir}")
            exit(1)

        output_format = os.getenv("REPORT_FORMAT", "html")
        s3_bucket = os.getenv("S3_BUCKET") if not args.dry_run else None

        url = generate_report_for_user(
            user_id=args.user,
            week_start=target_week,
            template_dir=template_dir,
            output_format=output_format,
            s3_bucket=s3_bucket,
        )
        if url:
            print(f"[SUCCESS] Report generated: {url}")
            exit(0)
        else:
            print(
                f"[ERROR] Report generation failed for user={args.user}, week={target_week}"
            )
            exit(1)

    # Batch mode (all users)
    exit_code = main(target_week_start=target_week, dry_run=args.dry_run)
    exit(exit_code)


if __name__ == "__main__":
    cli()
