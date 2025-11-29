"""
PDF report generation service using WeasyPrint + Jinja2.

Converts parent_report.html template to PDF with matplotlib charts.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import numpy as np

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.schemas.ability_schemas import ParentReportData, ParentReportSubject


# ============================================================================
# Configuration
# ============================================================================

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
STATIC_DIR = Path(__file__).parent.parent / "static" / "reports"

# Ensure static directory exists
STATIC_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Chart Generation (matplotlib)
# ============================================================================

def generate_theta_trend_chart(
    dates: List[datetime],
    thetas: List[float],
    theta_ses: List[float],
    subject: str,
    output_path: Path,
) -> str:
    """
    Generate theta trend chart with confidence band.
    
    Args:
        dates: List of calibration timestamps
        thetas: List of theta values
        theta_ses: List of standard errors
        subject: Subject name for title
        output_path: Output PNG file path
    
    Returns:
        Relative URL path to saved image
    """
    _, ax = plt.subplots(figsize=(10, 5))
    
    # Convert dates to numpy array for matplotlib
    dates_array = np.array(dates)
    
    # Plot theta line
    ax.plot(dates_array, thetas, 'o-', color='#2563eb', linewidth=2, 
            markersize=6, label='θ (Ability)')
    
    # Confidence band (θ ± SE)
    upper = [t + se for t, se in zip(thetas, theta_ses)]
    lower = [t - se for t, se in zip(thetas, theta_ses)]
    ax.fill_between(dates_array, lower, upper, alpha=0.2, color='#93c5fd', 
                     label='Confidence Interval (θ ± SE)')
    
    # Reference lines
    ax.axhline(y=0, color='#6b7280', linestyle='--', linewidth=1, 
               alpha=0.5, label='Average (θ=0)')
    ax.axhline(y=1, color='#10b981', linestyle=':', linewidth=1, 
               alpha=0.3, label='High (θ=+1)')
    ax.axhline(y=-1, color='#ef4444', linestyle=':', linewidth=1, 
               alpha=0.3, label='Low (θ=-1)')
    
    # Formatting
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('θ (Ability Estimate)', fontsize=12)
    ax.set_title(f'{subject.capitalize()} - Ability Trend Over Time', 
                 fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Y-axis limits
    y_min = min(lower) - 0.5
    y_max = max(upper) + 0.5
    ax.set_ylim(y_min, y_max)
    
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    # Return relative URL
    return f"/static/reports/{output_path.name}"


def generate_combined_trend_chart(
    report_data: ParentReportData,
    trend_points_by_subject: dict,
    output_path: Path,
) -> str:
    """
    Generate combined multi-subject trend chart.
    
    Args:
        report_data: Parent report data structure
        trend_points_by_subject: Dict[subject, List[ThetaTrendPoint]]
        output_path: Output PNG file path
    
    Returns:
        Relative URL path to saved image
    """
    _, ax = plt.subplots(figsize=(12, 6))
    
    colors = ['#2563eb', '#16a34a', '#dc2626', '#f59e0b', '#8b5cf6']
    
    for idx, (subject, points) in enumerate(trend_points_by_subject.items()):
        dates = [p.calibrated_at for p in points]
        thetas = [p.theta for p in points]
        # Convert to numpy arrays for matplotlib
        dates_array = np.array(dates)
        color = colors[idx % len(colors)]
        
        ax.plot(dates_array, thetas, 'o-', color=color, linewidth=2, 
                markersize=5, label=subject.capitalize())
    
    # Reference line
    ax.axhline(y=0, color='#6b7280', linestyle='--', linewidth=1, 
               alpha=0.5, label='Average (θ=0)')
    
    # Formatting
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('θ (Ability Estimate)', fontsize=12)
    ax.set_title('Multi-Subject Ability Trends', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return f"/static/reports/{output_path.name}"


# ============================================================================
# HTML → PDF Conversion
# ============================================================================

def render_parent_report_html(report_data: ParentReportData) -> str:
    """
    Render parent_report.html template with Jinja2.
    
    Args:
        report_data: Report data structure
    
    Returns:
        Rendered HTML string
    """
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("parent_report.html")
    
    # Convert Pydantic model to dict for Jinja2
    context = report_data.model_dump(by_alias=False)
    
    html = template.render(**context)
    return html


def generate_parent_report_pdf(
    report_data: ParentReportData,
    output_path: Optional[Path] = None,
) -> bytes:
    """
    Generate PDF from parent report data.
    
    Args:
        report_data: Report data structure
        output_path: Optional output file path (if None, returns bytes)
    
    Returns:
        PDF content as bytes
    
    Example:
        >>> pdf_bytes = generate_parent_report_pdf(report_data)
        >>> with open("report.pdf", "wb") as f:
        ...     f.write(pdf_bytes)
    """
    # Render HTML
    html_content = render_parent_report_html(report_data)
    
    # Generate PDF with WeasyPrint
    html_obj = HTML(string=html_content, base_url=str(TEMPLATES_DIR))
    
    if output_path:
        # Save to file
        html_obj.write_pdf(target=str(output_path))
        return output_path.read_bytes()
    else:
        # Return bytes
        pdf_bytes = html_obj.write_pdf()
        return pdf_bytes if pdf_bytes is not None else b""


# ============================================================================
# Convenience Functions
# ============================================================================

async def generate_parent_report_with_chart(
    report_data: ParentReportData,
    trend_points_by_subject: dict,
) -> bytes:
    """
    Generate complete parent report PDF with auto-generated trend chart.
    
    Args:
        report_data: Report data (without trend_chart_url populated)
        trend_points_by_subject: Dict[subject, List[ThetaTrendPoint]]
    
    Returns:
        PDF content as bytes
    """
    # Generate trend chart
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    chart_filename = f"trend_{report_data.student_name}_{timestamp}.png"
    chart_path = STATIC_DIR / chart_filename
    
    _ = generate_combined_trend_chart(
        report_data=report_data,
        trend_points_by_subject=trend_points_by_subject,
        output_path=chart_path,
    )
    
    # Update report data with chart URL
    report_data.trend_chart_url = str(chart_path)  # Use absolute path for WeasyPrint
    
    # Generate PDF
    pdf_bytes = generate_parent_report_pdf(report_data)
    
    return pdf_bytes


# ============================================================================
# Testing / Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example: Generate sample PDF for testing
    from app.schemas.ability_schemas import ThetaBand
    
    sample_data = ParentReportData(
        studentName="김학생",
        school="Dream High School",
        grade="10",
        periodStart="2025-10-25",
        periodEnd="2025-11-25",
        generatedAt=datetime.utcnow().isoformat(),
        parentFriendlySummaryKo=(
            "최근 4주 동안 2개 과목에서 학습 활동을 진행했습니다. "
            "전반적으로 안정적인 상태입니다."
        ),
        parentFriendlySummaryEn=(
            "Learning activities were conducted in 2 subjects over the last 28 days. "
            "Overall status is stable."
        ),
        subjects=[
            ParentReportSubject(
                subjectLabelKo="수학",
                subjectLabelEn="Mathematics",
                theta=0.45,
                thetaBand=ThetaBand.B_PLUS,
                percentile=67,
                deltaTheta4w=0.18,
                riskLabelKo="안정적",
                riskLabelEn="Stable",
            ),
            ParentReportSubject(
                subjectLabelKo="영어",
                subjectLabelEn="English",
                theta=-0.15,
                thetaBand=ThetaBand.B,
                percentile=44,
                deltaTheta4w=-0.05,
                riskLabelKo="보통",
                riskLabelEn="Moderate",
            ),
        ],
        trendChartUrl="/static/reports/trend_sample.png",
        schoolTeacherCommentKo=(
            "최근 4주 동안 꾸준히 성장하는 모습을 보여주고 있습니다. "
            "특히 수학 영역에서 눈에 띄는 향상이 있었습니다."
        ),
        schoolTeacherCommentEn=(
            "The student has shown steady progress over the last 4 weeks. "
            "Notable improvement was observed in mathematics."
        ),
        tutorCommentKo=None,
        tutorCommentEn=None,
        nextPlansKo=[
            "수학: 난이도 중상 문제 집중 연습",
            "영어: 독해 속도 향상 훈련",
            "정기 모의고사 응시 (격주)",
        ],
        nextPlansEn=[
            "Math: Focus on medium-high difficulty problems",
            "English: Reading speed improvement training",
            "Regular mock exams (biweekly)",
        ],
        parentGuidanceKo=(
            "자녀의 학습 패턴을 긍정적으로 유지하기 위해 정기적인 격려와 "
            "작은 목표 달성 시 칭찬을 아끼지 마세요."
        ),
        parentGuidanceEn=(
            "To maintain your child's positive learning pattern, provide regular "
            "encouragement and praise for small achievements."
        ),
    )
    
    # Generate sample trend chart
    sample_dates = [
        datetime(2025, 10, 25),
        datetime(2025, 11, 1),
        datetime(2025, 11, 8),
        datetime(2025, 11, 15),
        datetime(2025, 11, 22),
    ]
    sample_thetas_math = [0.15, 0.25, 0.30, 0.38, 0.45]
    sample_ses_math = [0.55, 0.48, 0.42, 0.38, 0.32]
    
    chart_path = STATIC_DIR / "trend_sample.png"
    generate_theta_trend_chart(
        dates=sample_dates,
        thetas=sample_thetas_math,
        theta_ses=sample_ses_math,
        subject="math",
        output_path=chart_path,
    )
    
    # Generate PDF
    pdf_path = STATIC_DIR / "sample_report.pdf"
    pdf_bytes = generate_parent_report_pdf(sample_data, output_path=pdf_path)
    
    print(f"✅ Sample PDF generated: {pdf_path}")
    print(f"   Size: {len(pdf_bytes):,} bytes")
