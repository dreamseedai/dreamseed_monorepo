"""
Pydantic schemas for irt_student_abilities-based dashboards.

These schemas support:
- Student self-view (ability summary + trend)
- Tutor priority lists (at-risk students)
- Parent PDF reports (progress summary)
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class ThetaBand(str, Enum):
    """Theta ability band classification."""
    A = "A"          # θ ≥ 1.0
    B_PLUS = "B+"    # 0.3 ≤ θ < 1.0
    B = "B"          # -0.3 ≤ θ < 0.3
    C = "C"          # -1.0 ≤ θ < -0.3
    D = "D"          # θ < -1.0


class RiskLevel(str, Enum):
    """Student risk level for intervention prioritization."""
    LOW = "low"        # θ ≥ 0.3 & θ_se ≤ 0.5
    MEDIUM = "medium"  # -0.3 ≤ θ < 0.3
    HIGH = "high"      # θ < -0.3 or θ_se > 0.6


# ============================================================================
# Student Dashboard Schemas
# ============================================================================

class SubjectAbilitySummary(BaseModel):
    """Single subject ability summary for student dashboard."""
    
    subject: str = Field(..., description="Subject name (e.g., 'math', 'english')")
    theta: float = Field(..., description="Current ability estimate")
    theta_se: float = Field(..., description="Standard error of theta", alias="thetaSe")
    theta_band: ThetaBand = Field(..., description="Ability band classification", alias="thetaBand")
    percentile: int = Field(..., ge=0, le=100, description="Percentile rank (0-100)")
    delta_theta_7d: Optional[float] = Field(
        None, 
        description="Change in theta over last 7 days",
        alias="deltaTheta7d"
    )
    risk_level: RiskLevel = Field(..., description="Risk level for intervention", alias="riskLevel")
    status_label: str = Field(..., description="Human-readable status", alias="statusLabel")
    recommended_action: str = Field(
        ..., 
        description="Next suggested action for student",
        alias="recommendedAction"
    )
    
    class Config:
        populate_by_name = True


class StudentAbilitySummaryResponse(BaseModel):
    """Overall ability summary for student (all subjects)."""
    
    student_id: str = Field(..., description="UUID of student", alias="studentId")
    as_of: datetime = Field(..., description="Timestamp of latest calibration", alias="asOf")
    subjects: List[SubjectAbilitySummary] = Field(..., description="Per-subject summaries")
    
    class Config:
        populate_by_name = True


class ThetaTrendPoint(BaseModel):
    """Single point in theta trend time series."""
    
    calibrated_at: datetime = Field(..., description="Calibration timestamp", alias="calibratedAt")
    theta: float = Field(..., description="Ability estimate at this time")
    theta_se: float = Field(..., description="Standard error at this time", alias="thetaSe")
    
    class Config:
        populate_by_name = True


class StudentThetaTrendResponse(BaseModel):
    """Theta trend over time for a single subject."""
    
    student_id: str = Field(..., description="UUID of student", alias="studentId")
    subject: str = Field(..., description="Subject name")
    points: List[ThetaTrendPoint] = Field(..., description="Time series of theta values")
    
    class Config:
        populate_by_name = True


# ============================================================================
# Tutor Priority List Schemas
# ============================================================================

class StudentFlag(str, Enum):
    """Flags for student priority classification."""
    RECENT_DECLINE = "recent_decline"        # Δθ < -0.15 over 14d
    NO_ACTIVITY_7D = "no_activity_7d"        # No sessions in last 7d
    HIGH_UNCERTAINTY = "high_uncertainty"    # θ_se > 0.6
    STEADY_PROGRESS = "steady_progress"      # Δθ > 0.10 over 14d
    LOW_BASELINE = "low_baseline"            # θ < -1.0


class SuggestedAction(BaseModel):
    """Suggested action for tutor to assign to student."""
    
    type: str = Field(..., description="Action type: assign_exam, assign_practice_set, schedule_1on1")
    label: str = Field(..., description="Human-readable label")
    exam_id: Optional[str] = Field(None, description="Exam UUID if type=assign_exam", alias="examId")
    bucket_id: Optional[str] = Field(None, description="Practice bucket UUID if applicable", alias="bucketId")
    
    class Config:
        populate_by_name = True


class TutorPriorityStudent(BaseModel):
    """Single student in tutor's priority list."""
    
    student_id: str = Field(..., description="UUID of student", alias="studentId")
    student_name: str = Field(..., description="Student display name", alias="studentName")
    school: Optional[str] = Field(None, description="School name")
    grade: Optional[str] = Field(None, description="Grade level (e.g., '10', '11')")
    
    theta: float = Field(..., description="Current ability estimate")
    theta_se: float = Field(..., description="Standard error", alias="thetaSe")
    theta_band: ThetaBand = Field(..., description="Ability band", alias="thetaBand")
    
    delta_theta_14d: Optional[float] = Field(
        None, 
        description="Change over last 14 days",
        alias="deltaTheta14d"
    )
    last_activity_at: Optional[datetime] = Field(
        None, 
        description="Last exam session timestamp",
        alias="lastActivityAt"
    )
    sessions_last_7d: int = Field(
        ..., 
        description="Number of sessions in last 7 days",
        alias="sessionsLast7d"
    )
    
    priority_score: float = Field(
        ..., 
        description="Computed priority score (higher = more urgent)",
        alias="priorityScore"
    )
    risk_level: RiskLevel = Field(..., description="Risk classification", alias="riskLevel")
    flags: List[StudentFlag] = Field(default_factory=list, description="Status flags")
    
    recommended_focus: List[str] = Field(
        default_factory=list,
        description="Suggested focus areas",
        alias="recommendedFocus"
    )
    next_suggested_actions: List[SuggestedAction] = Field(
        default_factory=list,
        description="Actionable items for tutor",
        alias="nextSuggestedActions"
    )
    
    class Config:
        populate_by_name = True


class TutorPriorityListResponse(BaseModel):
    """Tutor's priority list of students needing attention."""
    
    tutor_id: str = Field(..., description="UUID of tutor", alias="tutorId")
    subject: str = Field(..., description="Subject filter (e.g., 'math')")
    generated_at: datetime = Field(..., description="List generation timestamp", alias="generatedAt")
    window_days: int = Field(..., description="Analysis window in days", alias="windowDays")
    students: List[TutorPriorityStudent] = Field(
        ..., 
        description="Students sorted by priority_score (desc)"
    )
    
    class Config:
        populate_by_name = True


# ============================================================================
# Parent Report Schemas
# ============================================================================

class ParentReportSubject(BaseModel):
    """Subject summary for parent PDF report."""
    
    subject_label_ko: str = Field(..., description="Korean subject name", alias="subjectLabelKo")
    subject_label_en: str = Field(..., description="English subject name", alias="subjectLabelEn")
    theta: float = Field(..., description="Current ability")
    theta_band: ThetaBand = Field(..., description="Ability band", alias="thetaBand")
    percentile: int = Field(..., ge=0, le=100, description="Percentile rank")
    delta_theta_4w: Optional[float] = Field(
        None, 
        description="4-week change in theta",
        alias="deltaTheta4w"
    )
    risk_label_ko: str = Field(..., description="Korean risk level", alias="riskLabelKo")
    risk_label_en: str = Field(..., description="English risk level", alias="riskLabelEn")
    
    class Config:
        populate_by_name = True


class ParentReportData(BaseModel):
    """Complete data structure for parent PDF report template."""
    
    student_name: str = Field(..., description="Student full name", alias="studentName")
    school: Optional[str] = Field(None, description="School name")
    grade: Optional[str] = Field(None, description="Grade level")
    
    period_start: str = Field(..., description="Report period start (YYYY-MM-DD)", alias="periodStart")
    period_end: str = Field(..., description="Report period end (YYYY-MM-DD)", alias="periodEnd")
    generated_at: str = Field(..., description="Report generation timestamp", alias="generatedAt")
    
    parent_friendly_summary_ko: str = Field(
        ..., 
        description="Korean natural language summary",
        alias="parentFriendlySummaryKo"
    )
    parent_friendly_summary_en: str = Field(
        ..., 
        description="English natural language summary",
        alias="parentFriendlySummaryEn"
    )
    
    subjects: List[ParentReportSubject] = Field(..., description="Per-subject summaries")
    
    trend_chart_url: str = Field(
        ..., 
        description="URL/path to trend chart image",
        alias="trendChartUrl"
    )
    
    # School teacher comments (from public/private school)
    school_teacher_comment_ko: Optional[str] = Field(
        None,
        description="School teacher comment in Korean",
        alias="schoolTeacherCommentKo"
    )
    school_teacher_comment_en: Optional[str] = Field(
        None,
        description="School teacher comment in English",
        alias="schoolTeacherCommentEn"
    )
    
    # Academy/tutor comments (from academy/tutoring center/private tutor)
    tutor_comment_ko: Optional[str] = Field(
        None,
        description="Academy/tutor comment in Korean",
        alias="tutorCommentKo"
    )
    tutor_comment_en: Optional[str] = Field(
        None,
        description="Academy/tutor comment in English",
        alias="tutorCommentEn"
    )
    
    next_plans_ko: List[str] = Field(
        default_factory=list,
        description="Next 4-week plan items in Korean (from all sources)",
        alias="nextPlansKo"
    )
    next_plans_en: List[str] = Field(
        default_factory=list,
        description="Next 4-week plan items in English (from all sources)",
        alias="nextPlansEn"
    )
    
    parent_guidance_ko: Optional[str] = Field(
        None,
        description="Guidance for parents in Korean (prioritize school > tutor)",
        alias="parentGuidanceKo"
    )
    parent_guidance_en: Optional[str] = Field(
        None,
        description="Guidance for parents in English (prioritize school > tutor)",
        alias="parentGuidanceEn"
    )
    
    class Config:
        populate_by_name = True
