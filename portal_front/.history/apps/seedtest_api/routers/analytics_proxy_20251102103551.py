"""
Analytics Proxy Router

FastAPI endpoints that proxy requests to r-analytics plumber service.
Provides JWT-protected access to unified analytics capabilities.

Endpoints:
    GET  /analytics/health - Service health check
    POST /analytics/score/topic-theta - IRT-based topic ability scoring
    POST /analytics/improvement/index - Improvement tracking (I_t)
    POST /analytics/goal/attainment - Goal probability estimation
    POST /analytics/recommend/next-topics - Topic recommendations
    POST /analytics/risk/churn - 14-day churn risk assessment
    POST /analytics/report/generate - Comprehensive report generation

Security:
    All endpoints require JWT with appropriate scopes (analysis:run, reports:view, etc.)
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.seedtest_api.app.clients.r_analytics import RAnalyticsClient
from apps.seedtest_api.security.jwt import require_scopes

router = APIRouter(prefix="/analytics", tags=["analytics"])

def get_r_analytics_client() -> RAnalyticsClient:
    return RAnalyticsClient()

class TopicThetaRequest(BaseModel):
    student_id: str
    topic_ids: List[str] = Field(default_factory=list)

@router.get("/health", dependencies=[Depends(require_scopes("reports:view"))])
def health(client: RAnalyticsClient = Depends(get_r_analytics_client)) -> Dict[str, Any]:
    return client.health()

@router.post("/score/topic-theta", dependencies=[Depends(require_scopes("analysis:run","reports:view"))])
def score_topic_theta(body: TopicThetaRequest,
                      client: RAnalyticsClient = Depends(get_r_analytics_client)) -> Dict[str, Any]:
    try:
        return client.score_topic_theta(body.student_id, body.topic_ids)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"r-analytics error: {e}")

class ImprovementRequest(BaseModel):
    student_id: str
    window_days: int = 14

@router.post("/improvement/index", dependencies=[Depends(require_scopes("analysis:run","reports:view"))])
def improvement_index(body: ImprovementRequest,
                      client: RAnalyticsClient = Depends(get_r_analytics_client)) -> Dict[str, Any]:
    return client.improvement_index(body.student_id, body.window_days)

class GoalAttainmentRequest(BaseModel):
    student_id: str
    subject_id: str
    target_score: float
    target_date: str  # YYYY-MM-DD

@router.post("/goal/attainment", dependencies=[Depends(require_scopes("analysis:run","reports:view"))])
def goal_attainment(body: GoalAttainmentRequest,
                    client: RAnalyticsClient = Depends(get_r_analytics_client)) -> Dict[str, Any]:
    return client.goal_attainment(body.student_id, body.subject_id, body.target_score, body.target_date)

class RecommendRequest(BaseModel):
    student_id: str
    k: int = 5

@router.post("/recommend/next-topics", dependencies=[Depends(require_scopes("recommend:plan","reports:view"))])
def recommend_next_topics(body: RecommendRequest,
                          client: RAnalyticsClient = Depends(get_r_analytics_client)) -> Dict[str, Any]:
    return client.recommend_next_topics(body.student_id, body.k)

class RiskChurnRequest(BaseModel):
    student_id: str

@router.post("/risk/churn", dependencies=[Depends(require_scopes("analysis:run","reports:view"))])
def risk_churn(body: RiskChurnRequest,
               client: RAnalyticsClient = Depends(get_r_analytics_client)) -> Dict[str, Any]:
    return client.risk_churn(body.student_id)

class ReportRequest(BaseModel):
    student_id: str
    period: str = "weekly"  # or "monthly"

@router.post("/report/generate", dependencies=[Depends(require_scopes("reports:generate","reports:view"))])
def report_generate(body: ReportRequest,
                    client: RAnalyticsClient = Depends(get_r_analytics_client)) -> Dict[str, Any]:
    return client.report_generate(body.student_id, body.period)