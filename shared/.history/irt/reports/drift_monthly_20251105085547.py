"""
Monthly IRT Drift Report Generator
===================================
Generate PDF reports for monthly IRT calibration drift analysis.

Features:
- Window metadata and statistics
- Drift alerts with severity breakdown
- Item information curves for top drifted items
- Trend analysis and recommendations
- HTML template rendering with Jinja2
- PDF export with WeasyPrint

Usage:
    python -m shared.irt.reports.drift_monthly --window-id 45 --output /tmp/drift_2025_10.pdf
    
    # Or from Python:
    from shared.irt.reports.drift_monthly import generate_monthly_report
    generate_monthly_report(window_id=45, out_path="/tmp/report.pdf")
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from sqlalchemy.engine import Connection

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    HTML = None

from shared.db import get_db_engine
from shared.irt.service import fetch_item_info_curves


# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"


# ==============================================================================
# Report Generator
# ==============================================================================

def generate_monthly_report(
    window_id: int,
    out_path: str,
    format: str = "pdf",
    include_curves: bool = True,
    max_curves: int = 10
) -> str:
    """
    Generate monthly drift report for a calibration window.
    
    Args:
        window_id: Calibration window ID
        out_path: Output file path
        format: Output format ('html' or 'pdf')
        include_curves: Include item information curves
        max_curves: Maximum number of curves to include
    
    Returns:
        Path to generated report
    
    Example:
        >>> report_path = generate_monthly_report(
        ...     window_id=45,
        ...     out_path="/tmp/drift_2025_10.pdf"
        ... )
        >>> print(f"Report saved to {report_path}")
    """
    engine = get_db_engine()
    
    with engine.connect() as db:
        # Load window metadata
        meta_result = db.execute(
            text("""
                SELECT id, label, start_at, end_at, population_tags
                FROM shared_irt.windows
                WHERE id = :wid
            """),
            {"wid": window_id}
        ).mappings().first()
        
        if not meta_result:
            raise ValueError(f"Window {window_id} not found")
        
        meta = dict(meta_result)
        
        # Load statistics
        stats_result = db.execute(
            text("""
                SELECT 
                    COUNT(DISTINCT ic.item_id) AS total_items,
                    COUNT(DISTINCT ic.item_id) FILTER (WHERE ic.drift_flag IS NOT NULL) AS drifted_items,
                    COUNT(da.id) AS total_alerts,
                    COUNT(da.id) FILTER (WHERE da.severity = 'high') AS high_alerts,
                    COUNT(da.id) FILTER (WHERE da.severity = 'medium') AS medium_alerts,
                    COUNT(da.id) FILTER (WHERE da.severity = 'low') AS low_alerts,
                    AVG(ic.n_responses)::int AS avg_responses
                FROM shared_irt.item_calibration ic
                LEFT JOIN shared_irt.drift_alerts da ON da.window_id = ic.window_id AND da.item_id = ic.item_id
                WHERE ic.window_id = :wid
            """),
            {"wid": window_id}
        ).mappings().first()
        
        stats = dict(stats_result) if stats_result else {}
        
        # Load drift alerts
        alerts_result = db.execute(
            text("""
                SELECT 
                    a.item_id,
                    a.metric,
                    a.value,
                    a.threshold,
                    a.severity,
                    a.message,
                    i.id_str,
                    i.bank_id,
                    i.lang,
                    i.is_anchor,
                    ic.a_hat,
                    ic.b_hat,
                    ic.c_hat,
                    ic.n_responses
                FROM shared_irt.drift_alerts a
                JOIN shared_irt.items i ON i.id = a.item_id
                LEFT JOIN shared_irt.item_calibration ic ON ic.item_id = a.item_id AND ic.window_id = a.window_id
                WHERE a.window_id = :wid
                ORDER BY 
                    CASE a.severity 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END,
                    a.metric,
                    ABS(a.value) DESC
            """),
            {"wid": window_id}
        ).mappings().all()
        
        alerts = [dict(row) for row in alerts_result]
        
        # Load item information curves for top drifted items
        curves = []
        if include_curves and alerts:
            # Get unique item IDs from top alerts
            item_ids = list({alert['item_id'] for alert in alerts})[:max_curves]
            
            if item_ids:
                curves = fetch_item_info_curves(db, item_ids, steps=41)
        
        # Metric breakdown
        metric_counts = {}
        for alert in alerts:
            metric = alert['metric']
            metric_counts[metric] = metric_counts.get(metric, 0) + 1
        
        # Generate report
        report_data = {
            "generated_at": datetime.utcnow(),
            "window": meta,
            "stats": stats,
            "alerts": alerts,
            "curves": curves,
            "metric_counts": metric_counts,
            "has_alerts": len(alerts) > 0,
            "has_curves": len(curves) > 0
        }
        
        html_content = render_report_html(report_data)
        
        # Save output
        if format == "pdf":
            if not WEASYPRINT_AVAILABLE:
                raise ImportError(
                    "WeasyPrint is not installed. "
                    "Install with: pip install weasyprint"
                )
            
            HTML(string=html_content).write_pdf(out_path)
        else:  # html
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
        
        return out_path


def render_report_html(data: dict) -> str:
    """
    Render report HTML from template.
    
    Args:
        data: Report data dictionary
    
    Returns:
        Rendered HTML string
    """
    # Ensure template directory exists
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if template exists
    template_path = TEMPLATE_DIR / "drift_monthly.html"
    
    if not template_path.exists():
        # Use inline template if file doesn't exist
        return render_inline_template(data)
    
    # Load from file
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True
    )
    
    template = env.get_template("drift_monthly.html")
    return template.render(**data)


def render_inline_template(data: dict) -> str:
    """
    Render report using inline HTML template (fallback).
    
    Args:
        data: Report data dictionary
    
    Returns:
        Rendered HTML string
    """
    # Simplified inline template
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>IRT Drift Report - {data['window']['label']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .metadata {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            background: white;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            padding: 15px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #34495e;
            color: white;
        }}
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        .severity-high {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .severity-medium {{
            color: #f39c12;
            font-weight: bold;
        }}
        .severity-low {{
            color: #95a5a6;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            font-size: 12px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <h1>IRT Drift Monitoring Report</h1>
    
    <div class="metadata">
        <p><strong>Window:</strong> {data['window']['label']}</p>
        <p><strong>Period:</strong> {data['window']['start_at']} to {data['window']['end_at']}</p>
        <p><strong>Generated:</strong> {data['generated_at'].strftime('%Y-%m-%d %H:%M UTC')}</p>
    </div>
    
    <h2>Summary Statistics</h2>
    <div class="stats">
        <div class="stat-box">
            <div class="stat-value">{data['stats'].get('total_items', 0)}</div>
            <div class="stat-label">Total Items</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{data['stats'].get('drifted_items', 0)}</div>
            <div class="stat-label">Drifted Items</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{data['stats'].get('total_alerts', 0)}</div>
            <div class="stat-label">Total Alerts</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{data['stats'].get('avg_responses', 0)}</div>
            <div class="stat-label">Avg Responses</div>
        </div>
    </div>
    
    <h2>Drift Alerts</h2>
"""
    
    if data['has_alerts']:
        html += """
    <table>
        <thead>
            <tr>
                <th>Item ID</th>
                <th>Bank</th>
                <th>Lang</th>
                <th>Metric</th>
                <th>Value</th>
                <th>Threshold</th>
                <th>Severity</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>
"""
        for alert in data['alerts']:
            severity_class = f"severity-{alert['severity']}"
            html += f"""
            <tr>
                <td>{alert['id_str']}</td>
                <td>{alert['bank_id']}</td>
                <td>{alert['lang']}</td>
                <td>{alert['metric']}</td>
                <td>{alert['value']:.3f}</td>
                <td>{alert['threshold']:.3f}</td>
                <td class="{severity_class}">{alert['severity'].upper()}</td>
                <td>{alert['message']}</td>
            </tr>
"""
        html += """
        </tbody>
    </table>
"""
    else:
        html += "<p>No drift alerts detected. All items are stable.</p>"
    
    html += """
    <div class="footer">
        <p>Generated by IRT Drift Monitoring System | DreamSeed AI</p>
    </div>
</body>
</html>
"""
    
    return html


# ==============================================================================
# CLI
# ==============================================================================

@click.command()
@click.option("--window-id", required=True, type=int,
              help="Calibration window ID")
@click.option("--output", "-o", required=True, type=str,
              help="Output file path")
@click.option("--format", type=click.Choice(["html", "pdf"]), default="pdf",
              help="Output format (default: pdf)")
@click.option("--no-curves", is_flag=True,
              help="Exclude item information curves")
@click.option("--max-curves", default=10,
              help="Maximum number of curves to include")
def main(
    window_id: int,
    output: str,
    format: str,
    no_curves: bool,
    max_curves: int
):
    """
    Generate monthly IRT drift report.
    
    Example:
        python -m shared.irt.reports.drift_monthly \\
            --window-id 45 \\
            --output /tmp/drift_2025_10.pdf
    """
    try:
        report_path = generate_monthly_report(
            window_id=window_id,
            out_path=output,
            format=format,
            include_curves=not no_curves,
            max_curves=max_curves
        )
        
        print(f"✓ Report generated successfully: {report_path}")
        
        # Print summary
        from pathlib import Path
        file_size = Path(report_path).stat().st_size
        print(f"  File size: {file_size / 1024:.1f} KB")
        print(f"  Format: {format.upper()}")
        
    except Exception as e:
        print(f"✗ Error generating report: {e}")
        raise


if __name__ == "__main__":
    main()
