"""
Analytics Proxy Router

FastAPI router that proxies requests to r-analytics (plumber, port 8010).
All endpoints are protected by JWT/JWKS scopes (reports:view, analysis:run, etc.).
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.seedtest_api.app.clients.r_analytics import RAnalyticsClient
from apps.seedtest_api.security.jwt import require_scopes

# settings/env는 클라이언트 내부에서 읽음

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_r_analytics_client() -> RAnalyticsClient:
    """Dependency: Create RAnalyticsClient instance."""
    return RAnalyticsClient()


class TopicThetaRequest(BaseModel):
    student_id: str
    topic_ids: List[str] = Field(default_factory=list)


@router.get("/health", dependencies=[Depends(require_scopes("reports:view"))])
def health(
    client: RAnalyticsClient = Depends(get_r_analytics_client),
) -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        return client.health()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"r-analytics error: {e}")


@router.post(
    "/score/topic-theta",
    dependencies=[Depends(require_scopes("analysis:run", "reports:view"))],
)
def score_topic_theta(
    body: TopicThetaRequest,
    client: RAnalyticsClient = Depends(get_r_analytics_client),
) -> Dict[str, Any]:
    """Score topic-level theta for a student."""
    try:
        return client.score_topic_theta(body.student_id, body.topic_ids)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"r-analytics error: {e}")


class ImprovementRequest(BaseModel):
    student_id: str
    window_days: int = 14


@router.post(
    "/improvement/index",
    dependencies=[Depends(require_scopes("analysis:run", "reports:view"))],
)
def improvement_index(
    body: ImprovementRequest,
    client: RAnalyticsClient = Depends(get_r_analytics_client),
) -> Dict[str, Any]:
    """Compute improvement index (I_t) for a student."""
    try:
        return client.improvement_index(body.student_id, body.window_days)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"r-analytics error: {e}")


class GoalAttainmentRequest(BaseModel):
    student_id: str
    subject_id: str
    target_score: float
    target_date: str  # YYYY-MM-DD


@router.post(
    "/goal/attainment",
    dependencies=[Depends(require_scopes("analysis:run", "reports:view"))],
)
def goal_attainment(
    body: GoalAttainmentRequest,
    client: RAnalyticsClient = Depends(get_r_analytics_client),
) -> Dict[str, Any]:
    """Compute goal attainment probability P(goal|state)."""
    try:
        return client.goal_attainment(
            body.student_id,
            body.subject_id,
            body.target_score,
            body.target_date,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"r-analytics error: {e}")


class RecommendRequest(BaseModel):
    student_id: str
    k: int = 5


@router.post(
    "/recommend/next-topics",
    dependencies=[Depends(require_scopes("recommend:plan", "reports:view"))],
)
def recommend_next_topics(
    body: RecommendRequest,
    client: RAnalyticsClient = Depends(get_r_analytics_client),
) -> Dict[str, Any]:
    """Recommend next topics for a student."""
    try:
        return client.recommend_next_topics(body.student_id, body.k)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"r-analytics error: {e}")


class RiskChurnRequest(BaseModel):
    student_id: str


@router.post(
    "/risk/churn",
    dependencies=[Depends(require_scopes("analysis:run", "reports:view"))],
)
def risk_churn(
    body: RiskChurnRequest,
    client: RAnalyticsClient = Depends(get_r_analytics_client),
) -> Dict[str, Any]:
    """Assess churn risk for a student."""
    try:
        return client.risk_churn(body.student_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"r-analytics error: {e}")


class ReportRequest(BaseModel):
    student_id: str
    period: str = "weekly"  # or "monthly"


@router.post(
    "/report/generate",
    dependencies=[Depends(require_scopes("reports:generate", "reports:view"))],
)
def report_generate(
    body: ReportRequest,
    client: RAnalyticsClient = Depends(get_r_analytics_client),
) -> Dict[str, Any]:
    """Generate weekly/monthly report for a student."""
    try:
        return client.report_generate(body.student_id, body.period)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"r-analytics error: {e}")

