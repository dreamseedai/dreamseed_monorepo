from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class AbilityEstimate(BaseModel):
    theta: float = Field(..., description="Estimated ability (theta)")
    standard_error: Optional[float] = Field(
        default=None, description="Standard error of theta estimate"
    )
    method: str = Field(
        default="heuristic",
        description="Estimation method: heuristic | irt | mixed_effects",
    )


class TopicInsight(BaseModel):
    topic: str
    accuracy: float = Field(..., ge=0.0, le=1.0)
    correct: int
    total: int
    strength: bool = Field(
        ..., description="True if topic considered a strength (e.g., accuracy>=0.75)"
    )


class RecommendationItem(BaseModel):
    topic: Optional[str] = None
    message: str
    kind: str = Field(
        default="study", description="study | concept | practice | meta"
    )


class GrowthForecastPoint(BaseModel):
    step: int
    score_scaled: float


class GrowthForecast(BaseModel):
    horizon: int = 6
    points: List[GrowthForecastPoint] = Field(default_factory=list)
    method: str = Field(
        default="linear_smoothing", description="Forecast method summary"
    )
    # Optional probability-of-achievement goals
    # Each goal represents P(score_scaled >= target_score) within the given horizon
    # using a Normal approximation around the forecast mean.
    class ForecastGoal(BaseModel):
        target_score: float
        horizon: int
        probability: float = Field(..., ge=0.0, le=1.0)

    goals: List[ForecastGoal] = Field(default_factory=list)


class Benchmark(BaseModel):
    percentile: int
    label: str = Field(
        default="cohort", description="Comparison baseline label (e.g., cohort)"
    )


class AnalysisReport(BaseModel):
    exam_session_id: str
    user_id: Optional[str] = None
    ability: AbilityEstimate
    topic_insights: List[TopicInsight] = Field(default_factory=list)
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    forecast: Optional[GrowthForecast] = None
    benchmark: Optional[Benchmark] = None
