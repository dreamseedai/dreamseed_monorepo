from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_serializer
from typing_extensions import Annotated


class TopicBreakdown(BaseModel):
    topic: str
    correct: int
    total: int
    # Accuracy constrained to [0, 1] when present
    accuracy: Annotated[Optional[float], Field(ge=0, le=1, default=None)] = None


class ResultPayload(BaseModel):
    session_id: str
    status: str
    score: Annotated[
        Dict[str, float],
        Field(
            ...,
            description=(
                "Named score metrics for the session (e.g., 'scaled', 'raw', "
                "'percent_correct'). Values are floats."
            ),
            json_schema_extra={
                "examples": [{"scaled": 128.5, "raw": 34.0, "percent_correct": 0.68}]
            },
        ),
    ]
    topics: List[TopicBreakdown] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QuestionItem(BaseModel):
    # Constrain question_id to int | str when available
    question_id: int | str | None = None
    is_correct: bool
    user_answer: Any | None = None
    correct_answer: Any | None = None
    explanation: Optional[str] = None
    topic: Optional[str] = None


class ScoreDetail(BaseModel):
    raw: Optional[float] = Field(default=None, description="Raw score")
    scaled: Optional[float] = Field(default=None, description="Scaled score")


class ResultContract(BaseModel):
    exam_session_id: str
    user_id: Optional[str] = None
    exam_id: Optional[int] = None
    score: Annotated[
        float,
        Field(
            ...,
            description="Scaled score for the exam attempt (float).",
            json_schema_extra={"examples": [128.5]},
        ),
    ]
    # Detailed score values; optional in Phase 1 responses
    score_detail: Optional[ScoreDetail] = Field(
        default=None,
        description="Detailed score values, including raw and scaled.",
        json_schema_extra={
            "examples": [
                {"raw": 34.0, "scaled": 128.5},
                {"scaled": 500.0},
            ]
        },
    )
    ability_estimate: Optional[float] = None
    standard_error: Optional[float] = None
    # Percentile constrained to [0, 100] when present
    percentile: Annotated[Optional[int], Field(ge=0, le=100, default=None)] = None
    topic_breakdown: List[TopicBreakdown] = Field(default_factory=list)
    questions: List[QuestionItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    created_at: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="Creation timestamp in UTC ISO 8601 format.",
            json_schema_extra={"examples": ["2025-10-22T12:34:56.789Z"]},
        ),
    ]
    updated_at: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="Last update timestamp in UTC ISO 8601 format.",
            json_schema_extra={"examples": ["2025-10-22T12:40:00Z"]},
        ),
    ]
    status: str

    @field_serializer("created_at", when_used="json")  # type: ignore[misc]
    def _serialize_created_at(self, v: Optional[datetime]) -> Optional[str]:
        return v.isoformat() if v else None

    @field_serializer("updated_at", when_used="json")  # type: ignore[misc]
    def _serialize_updated_at(self, v: Optional[datetime]) -> Optional[str]:
        return v.isoformat() if v else None
