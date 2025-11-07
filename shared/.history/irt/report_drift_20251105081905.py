#!/usr/bin/env python3
"""
IRT Drift Monthly Report Generator
===================================
Generates PDF report from Jinja2 template with drift alerts and parameter trends

Usage:
    python -m shared.irt.report_drift --window-id 5 --output /tmp/drift_report_2025_10.pdf
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import asyncpg
import click
from jinja2 import Template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# HTML Template for PDF report
REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>IRT Drift Report - {{ window_label }}</title>
    <style>
        body { font-family: 'Noto Sans', Arial, sans-serif; margin: 40px; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th { background-color: #3498db; color: white; padding: 12px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #ecf0f1; }
        tr:hover { background-color: #f8f9fa; }
        .severity-high { color: #e74c3c; font-weight: bold; }
        .severity-medium { color: #f39c12; }
        .severity-low { color: #95a5a6; }
        .stats-box { background-color: #ecf0f1; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .stats-box h3 { margin-top: 0; color: #2c3e50; }
        .metric { display: inline-block; margin-right: 30px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #3498db; }
        .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #bdc3c7; 
                  color: #7f8c8d; font-size: 12px; text-align: center; }
    </style>
</head>
<body>
    <h1>IRT Drift Monitoring Report</h1>
    
    <div class="stats-box">
        <h3>Window: {{ window_label }}</h3>
        <div class="metric">
            <div class="metric-value">{{ stats.total_items }}</div>
            <div>Total Items Calibrated</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ stats.drifted_items }}</div>
            <div>Items with Drift</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ stats.alerts_high }}</div>
            <div>High Severity Alerts</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ stats.alerts_total }}</div>
            <div>Total Active Alerts</div>
        </div>
    </div>
    
    <h2>Active Drift Alerts</h2>
    {% if alerts %}
    <table>
        <thead>
            <tr>
                <th>Item ID</th>
                <th>Bank ID</th>
                <th>Metric</th>
                <th>Value</th>
                <th>Severity</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>
            {% for alert in alerts %}
            <tr>
                <td>{{ alert.item_id_str or alert.item_id }}</td>
                <td>{{ alert.bank_id }}</td>
                <td><strong>{{ alert.metric }}</strong></td>
                <td>{{ "%.3f" | format(alert.value) if alert.value else "N/A" }}</td>
                <td class="severity-{{ alert.severity }}">{{ alert.severity.upper() }}</td>
                <td>{{ alert.message }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>No active drift alerts for this window. ✓</p>
    {% endif %}
    
    <h2>Top 10 Largest Parameter Shifts</h2>
    {% if top_drifts %}
    <table>
        <thead>
            <tr>
                <th>Item ID</th>
                <th>Parameter</th>
                <th>Previous</th>
                <th>Current</th>
                <th>Δ</th>
                <th>Drift Flag</th>
            </tr>
        </thead>
        <tbody>
            {% for item in top_drifts %}
            <tr>
                <td>{{ item.item_id }}</td>
                <td>{{ item.param }}</td>
                <td>{{ "%.3f" | format(item.prev_value) }}</td>
                <td>{{ "%.3f" | format(item.curr_value) }}</td>
                <td><strong>{{ "%+.3f" | format(item.delta) }}</strong></td>
                <td>{{ item.drift_flag or "—" }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>Insufficient calibration history for drift comparison.</p>
    {% endif %}
    
    <div class="footer">
        Generated on {{ report_date.strftime('%Y-%m-%d %H:%M UTC') }}<br>
        IRT Drift Monitoring System | DreamSeed AI
    </div>
</body>
</html>
"""


class DriftReporter:
    """Generate drift reports"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=3)
    
    async def close(self):
        if self.pool:
            await self.pool.close()
    
    async def gather_report_data(self, window_id: int) -> Dict:
        """Gather all data for report"""
        async with self.pool.acquire() as conn:
            # Window metadata
            window = await conn.fetchrow(
                "SELECT label, start_at, end_at FROM shared_irt.windows WHERE id = $1",
                window_id
            )
            
            if not window:
                raise ValueError(f"Window {window_id} not found")
            
            # Statistics
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_items,
                    SUM(CASE WHEN drift_flag IS NOT NULL THEN 1 ELSE 0 END) as drifted_items,
                    (SELECT COUNT(*) FROM shared_irt.drift_alerts 
                     WHERE window_id = $1 AND resolved_at IS NULL) as alerts_total,
                    (SELECT COUNT(*) FROM shared_irt.drift_alerts 
                     WHERE window_id = $1 AND resolved_at IS NULL AND severity = 'high') as alerts_high
                FROM shared_irt.item_calibration
                WHERE window_id = $1
                """,
                window_id
            )
            
            # Active alerts
            alerts = await conn.fetch(
                """
                SELECT 
                    da.item_id, i.id_str as item_id_str, i.bank_id,
                    da.metric, da.value, da.severity, da.message
                FROM shared_irt.drift_alerts da
                JOIN shared_irt.items i ON da.item_id = i.id
                WHERE da.window_id = $1 AND da.resolved_at IS NULL
                ORDER BY 
                    CASE da.severity
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        ELSE 3
                    END,
                    ABS(da.value) DESC NULLS LAST
                """,
                window_id
            )
            
            # Top drifts (comparison with previous window)
            top_drifts = await conn.fetch(
                """
                WITH prev_window AS (
                    SELECT id FROM shared_irt.windows
                    WHERE created_at < (SELECT created_at FROM shared_irt.windows WHERE id = $1)
                    ORDER BY created_at DESC LIMIT 1
                )
                SELECT 
                    curr.item_id,
                    'b' as param,
                    prev.b_hat as prev_value,
                    curr.b_hat as curr_value,
                    curr.b_hat - prev.b_hat as delta,
                    curr.drift_flag
                FROM shared_irt.item_calibration curr
                JOIN shared_irt.item_calibration prev 
                    ON curr.item_id = prev.item_id 
                    AND prev.window_id = (SELECT id FROM prev_window)
                WHERE curr.window_id = $1
                ORDER BY ABS(curr.b_hat - prev.b_hat) DESC
                LIMIT 10
                """,
                window_id
            )
            
            return {
                "window_id": window_id,
                "window_label": window['label'],
                "stats": dict(stats),
                "alerts": [dict(row) for row in alerts],
                "top_drifts": [dict(row) for row in top_drifts],
                "report_date": datetime.utcnow()
            }
    
    async def generate_report(self, window_id: int, output_path: str):
        """Generate HTML/PDF report"""
        data = await self.gather_report_data(window_id)
        
        # Render template
        template = Template(REPORT_TEMPLATE)
        html = template.render(**data)
        
        # Write HTML
        html_path = Path(output_path).with_suffix('.html')
        html_path.write_text(html, encoding='utf-8')
        logger.info(f"HTML report: {html_path}")
        
        # Convert to PDF (requires wkhtmltopdf or weasyprint)
        try:
            import subprocess
            pdf_path = Path(output_path).with_suffix('.pdf')
            subprocess.run(
                ['wkhtmltopdf', str(html_path), str(pdf_path)],
                check=True,
                capture_output=True
            )
            logger.info(f"PDF report: {pdf_path}")
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            logger.warning(f"PDF generation failed (install wkhtmltopdf): {e}")
            logger.info(f"HTML report available at: {html_path}")


@click.command()
@click.option('--database-url', envvar='DATABASE_URL', required=True)
@click.option('--window-id', type=int, required=True)
@click.option('--output', required=True, help='Output file path (PDF or HTML)')
def main(database_url: str, window_id: int, output: str):
    """Generate IRT drift report for a window"""
    reporter = DriftReporter(database_url)
    
    async def run():
        try:
            await reporter.connect()
            await reporter.generate_report(window_id, output)
        finally:
            await reporter.close()
    
    asyncio.run(run())


if __name__ == '__main__':
    main()
