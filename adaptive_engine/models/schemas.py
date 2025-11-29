from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Question(BaseModel):
    question_id: str | int
    a: float = Field(1.0, description="Discrimination")
    b: float = Field(0.0, description="Difficulty")
    c: float = Field(0.2, description="Guessing")
    topic: Optional[str] = None
    topic_name: Optional[str] = None
    text: Optional[str] = None


class StartRequest(BaseModel):
    user_id: int
    exam_id: int


class StartResponse(BaseModel):
    session_id: str
    theta: float
    status: str


class NextRequest(BaseModel):
    theta: float
    available_questions: List[Question]
    seen_ids: List[str | int] = Field(default_factory=list)


class NextResponse(BaseModel):
    question: Optional[Question]


class AnswerRequest(BaseModel):
    theta: float
    question: Question
    correct: bool
    answered_items: List[Dict] = Field(
        default_factory=list
    )  # items like {"info": float}


class AnswerResponse(BaseModel):
    theta_after: float
    std_error: float
    stop: bool


class FinishRequest(BaseModel):
    responses: List[Dict]
    questions: List[Question] | Dict[str, Question] | Dict[int, Question]


class FinishResponse(BaseModel):
    feedback: List[str]
    status: str
    theta: Optional[float] = None
    se: Optional[float] = None
    scaled_score: Optional[float] = None
    ci: Optional[Dict] = None
    percentile: Optional[float] = None
    items_review: Optional[List[Dict]] = None
    topic_breakdown: Optional[Dict[str, Dict[str, float]]] = None
    recommendations: Optional[List[str]] = None
