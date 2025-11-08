"""
Pydantic Models for IRT System
===============================
Shared data models for FastAPI endpoints, ETL scripts, and calibration pipelines.

Usage:
    from shared.irt.models import DriftAlertOut, WindowSummary, ItemInfoCurve
    
    alert = DriftAlertOut(
        item_id=123,
        window_id=45,
        metric="Δb",
        value=0.35,
        threshold=0.25,
        severity="medium",
        message="Item 123: Δb = +0.350",
        created_at=datetime.now()
    )
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# ==============================================================================
# Type Aliases
# ==============================================================================

Lang = Literal['en', 'ko', 'zh-Hans', 'zh-Hant']
IRTModel = Literal['1PL', '2PL', '3PL']
Severity = Literal['low', 'medium', 'high']
DriftMetric = Literal['Δb', 'Δa', 'Δc', 'DIF', 'INFO']


# ==============================================================================
# Drift Alert Models
# ==============================================================================

class DriftAlertOut(BaseModel):
    """Drift alert response model"""
    item_id: int
    window_id: int
    metric: DriftMetric
    value: float
    threshold: float
    severity: Severity
    message: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DriftAlertResolve(BaseModel):
    """Request body for resolving drift alert"""
    resolved: bool = Field(..., description="True to resolve, False to reopen")
    note: Optional[str] = Field(None, description="Optional resolution note")


# ==============================================================================
# Window Models
# ==============================================================================

class WindowCreate(BaseModel):
    """Request body for creating calibration window"""
    label: str = Field(..., description="Window label (e.g., '2025-10 monthly')")
    start_at: datetime
    end_at: datetime
    population_tags: List[str] = Field(default_factory=lambda: ['global'])


class WindowSummary(BaseModel):
    """Window summary with calibration statistics"""
    window_id: int
    label: str
    start_at: datetime
    end_at: datetime
    n_items: int = Field(..., description="Number of calibrated items")
    n_alerts: int = Field(..., description="Number of active drift alerts")
    alerts_by_metric: dict = Field(
        default_factory=dict,
        description="Alert counts grouped by metric (Δb, Δa, etc.)"
    )
    
    class Config:
        from_attributes = True


class WindowDetail(BaseModel):
    """Detailed window information"""
    id: int
    label: str
    start_at: datetime
    end_at: datetime
    population_tags: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==============================================================================
# Item Models
# ==============================================================================

class ItemBase(BaseModel):
    """Base item model"""
    id: int
    id_str: str
    bank_id: str
    lang: Lang
    topic_tags: List[str] = Field(default_factory=list)
    is_anchor: bool = False
    exposure_count: int = 0


class ItemWithParams(ItemBase):
    """Item with current IRT parameters"""
    model: Optional[IRTModel] = None
    a: Optional[float] = None
    b: Optional[float] = None
    c: Optional[float] = None
    a_se: Optional[float] = None
    b_se: Optional[float] = None
    c_se: Optional[float] = None
    version: Optional[int] = None
    effective_from: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ItemCreate(BaseModel):
    """Request body for creating item"""
    id_str: str
    bank_id: str
    lang: Lang
    stem_rich: dict
    options_rich: Optional[dict] = None
    topic_tags: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    is_anchor: bool = False


# ==============================================================================
# Calibration Models
# ==============================================================================

class CalibrationResult(BaseModel):
    """Single item calibration result"""
    item_id: int
    window_id: int
    model: IRTModel
    a_hat: Optional[float] = None
    b_hat: Optional[float] = None
    c_hat: Optional[float] = None
    a_se: Optional[float] = None
    b_se: Optional[float] = None
    c_se: Optional[float] = None
    a_ci_low: Optional[float] = None
    a_ci_high: Optional[float] = None
    b_ci_low: Optional[float] = None
    b_ci_high: Optional[float] = None
    c_ci_low: Optional[float] = None
    c_ci_high: Optional[float] = None
    n_responses: int
    loglik: Optional[float] = None
    fit_statistics: Optional[dict] = None
    drift_flag: Optional[str] = None
    dif_metadata: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CalibrationSummary(BaseModel):
    """Summary of calibration results for a window"""
    window_id: int
    window_label: str
    total_items: int
    stable_items: int
    drifted_items: int
    avg_responses_per_item: float
    model_loglik: Optional[float] = None
    calibrated_at: datetime


# ==============================================================================
# Information Curve Models
# ==============================================================================

class InfoCurvePoint(BaseModel):
    """Single point on information curve"""
    theta: float = Field(..., description="Ability level θ")
    info: float = Field(..., description="Fisher information I(θ)")


class ItemInfoCurve(BaseModel):
    """Item information curve"""
    item_id: int
    model: IRTModel
    points: List[InfoCurvePoint] = Field(
        ...,
        description="Information curve points (theta, info)"
    )
    max_info: float = Field(..., description="Maximum information")
    max_info_theta: float = Field(..., description="θ at maximum information")


class TestInfoCurve(BaseModel):
    """Test information curve (sum of item curves)"""
    window_id: int
    item_ids: List[int]
    points: List[InfoCurvePoint]
    avg_info: float = Field(..., description="Average information across θ range")


# ==============================================================================
# Statistics Models
# ==============================================================================

class IRTStats(BaseModel):
    """Global IRT system statistics"""
    total_items: int
    anchor_items: int
    active_drift_alerts: int
    alerts_by_severity: dict = Field(
        default_factory=dict,
        description="Alert counts by severity (low, medium, high)"
    )
    total_calibration_windows: int
    latest_window_label: Optional[str] = None
    items_by_lang: dict = Field(
        default_factory=dict,
        description="Item counts by language"
    )
    items_by_bank: dict = Field(
        default_factory=dict,
        description="Item counts by bank"
    )


class ItemHistory(BaseModel):
    """Parameter history for a single item"""
    item_id: int
    id_str: str
    is_anchor: bool
    history: List[CalibrationResult] = Field(
        ...,
        description="Ordered list of calibrations (oldest to newest)"
    )


# ==============================================================================
# Response Data Models
# ==============================================================================

class ItemResponse(BaseModel):
    """Single item response record"""
    org_id: int
    user_id_hash: str
    item_id: int
    is_correct: bool
    score: float = Field(..., ge=0.0, le=1.0, description="Partial credit score")
    answered_at: datetime


class ItemResponseSummary(BaseModel):
    """Response statistics for an item"""
    item_id: int
    n_responses: int
    p_correct: float = Field(..., ge=0.0, le=1.0, description="Proportion correct")
    variance: float = Field(..., ge=0.0, description="Response variance")
    min_responses_met: bool = Field(..., description="Meets minimum response threshold")


# ==============================================================================
# Drift Detection Models
# ==============================================================================

class DriftThresholds(BaseModel):
    """Configurable drift detection thresholds"""
    delta_b: float = Field(0.25, description="Difficulty drift threshold |Δb|")
    delta_a: float = Field(0.2, description="Discrimination drift threshold |Δa|")
    delta_c: float = Field(0.1, description="Guessing drift threshold |Δc|")
    dif_threshold: float = Field(0.3, description="DIF threshold")
    info_drop_pct: float = Field(0.2, description="Information drop threshold (20%)")


class DriftComparison(BaseModel):
    """Comparison of current vs previous parameters"""
    item_id: int
    a_current: Optional[float] = None
    b_current: Optional[float] = None
    c_current: Optional[float] = None
    a_previous: Optional[float] = None
    b_previous: Optional[float] = None
    c_previous: Optional[float] = None
    delta_a: Optional[float] = None
    delta_b: Optional[float] = None
    delta_c: Optional[float] = None
    drifted: bool = Field(..., description="True if any parameter exceeds threshold")
    drift_severity: Optional[Severity] = None


# ==============================================================================
# Bayesian-specific Models
# ==============================================================================

class BayesianDiagnostics(BaseModel):
    """MCMC diagnostics for Bayesian calibration"""
    divergences: int = Field(..., description="Number of divergent transitions")
    r_hat_max: float = Field(..., description="Maximum R-hat (should be < 1.01)")
    ess_bulk_min: float = Field(..., description="Minimum bulk ESS (should be > 400)")
    warnings: List[str] = Field(default_factory=list)


class BayesianCalibrationResult(CalibrationResult):
    """Calibration result with Bayesian diagnostics"""
    diagnostics: Optional[BayesianDiagnostics] = None
    posterior_sd_a: Optional[float] = None
    posterior_sd_b: Optional[float] = None
    posterior_sd_c: Optional[float] = None


# ==============================================================================
# Report Models
# ==============================================================================

class DriftReportData(BaseModel):
    """Data for drift report generation"""
    window: WindowDetail
    statistics: CalibrationSummary
    active_alerts: List[DriftAlertOut]
    top_drifts: List[DriftComparison]
    test_info_curve: Optional[TestInfoCurve] = None


class ReportGenerateRequest(BaseModel):
    """Request body for report generation"""
    window_id: int
    format: Literal['html', 'pdf'] = 'pdf'
    include_plots: bool = True
    include_item_details: bool = False


# ==============================================================================
# Pagination Models
# ==============================================================================

class PaginationParams(BaseModel):
    """Common pagination parameters"""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum records to return")


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    total: int
    skip: int
    limit: int
    items: List[BaseModel]


# ==============================================================================
# Export Models
# ==============================================================================

class ExportFormat(BaseModel):
    """Export format specification"""
    format: Literal['csv', 'json', 'parquet'] = 'csv'
    include_metadata: bool = True
    include_response_data: bool = False


class ExportRequest(BaseModel):
    """Request body for data export"""
    window_id: int
    format: ExportFormat
    item_ids: Optional[List[int]] = None
    output_path: Optional[str] = None
