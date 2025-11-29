from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AnsweredItem(BaseModel):
    question_id: str | int
    a: float
    b: float
    c: float
    is_correct: bool
    info: float


class SessionState(BaseModel):
    session_id: str
    user_id: int
    exam_id: int
    theta: float = 0.0
    answered: List[AnsweredItem] = Field(default_factory=list)
    seen_ids: List[str | int] = Field(default_factory=list)
    remaining_time_sec: Optional[int] = None
    # timing
    started_at: Optional[float] = None  # epoch seconds
    last_answer_at: Optional[float] = None  # epoch seconds
    # topic exposure tracking: {topic -> count}
    topic_counts: Dict[str, int] = Field(default_factory=dict)
    # Bayesian prior for ability
    prior_mean: float = 0.0
    prior_sd: float = 1.0
    # histories
    theta_history: List[float] = Field(default_factory=list)
    se_history: List[float] = Field(default_factory=list)
    # last topic answered (for simple avoid-same-topic heuristic)
    last_topic: Optional[str] = None
