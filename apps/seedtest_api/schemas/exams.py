from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class LastAnswer(BaseModel):
    choice: Optional[int] = None
    choices: Optional[List[int]] = None
    text: Optional[str] = None


QuestionType = Literal["mcq", "text", "multi"]


class Question(BaseModel):
    id: str
    text: str
    type: QuestionType = "mcq"
    options: Optional[List[str]] = None


class ResultSummary(BaseModel):
    score: int
    correct: int
    incorrect: int
    duration_sec: Optional[int] = None
    by_section: Optional[Dict[str, Dict[str, int]]] = None


class NextQuestionResponse(BaseModel):
    done: bool
    next_difficulty: Optional[int] = None
    question: Optional["QuestionOut"] = None
    result: Optional[Dict] = None
    finished: Optional[bool] = None  # legacy 호환


# ----- New/extended schemas -----


class CreateExamRequest(BaseModel):
    exam_id: str
    mode: Optional[str] = None


class CreateExamResponse(BaseModel):
    exam_session_id: str
    start_time: str
    exam_id: str


class QuestionOut(BaseModel):
    id: str
    text: str
    type: Literal["mcq", "text", "multi"]
    options: Optional[List[str]] = None
    timer_sec: Optional[int] = None


class AnswerSubmission(BaseModel):
    question_id: str
    answer: Optional[str] = None
    elapsed_time: Optional[float] = Field(default=None, description="seconds")


class NextStepRequest(BaseModel):
    session_id: str
    last_question_id: Optional[str] = None
    last_answer: Optional[Dict] = None
    difficulty: Optional[int] = None


class NextQuestionRequest(NextStepRequest):
    """Backward-compatible alias for legacy imports."""

    pass
