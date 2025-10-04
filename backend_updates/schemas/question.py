
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    PROBLEM_SOLVING = "problem_solving"
    PROOF = "proof"
    EXPLANATION = "explanation"
    GENERAL = "general"

class Subject(str, Enum):
    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"

class TranslationStatus(str, Enum):
    COMPLETE = "complete"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"

# Question Schemas

class QuestionHint(BaseModel):
    id: str
    hint_text_en: str
    hint_text_ko: Optional[str] = None
    hint_text_zh: Optional[str] = None
    hint_order: int

class AdaptiveLearningMetadata(BaseModel):
    prerequisites: List[str] = []
    learning_objectives: List[str] = []
    assessment_criteria: List[str] = []
    min_difficulty: int
    max_difficulty: int
    optimal_difficulty: int
    success_indicators: List[str] = []

class QuestionContent(BaseModel):
    question_en: str
    question_ko: Optional[str] = None
    question_zh: Optional[str] = None
    answer_en: Optional[str] = None
    answer_ko: Optional[str] = None
    answer_zh: Optional[str] = None
    solution_en: Optional[str] = None
    solution_ko: Optional[str] = None
    solution_zh: Optional[str] = None
    explanation_en: Optional[str] = None
    explanation_ko: Optional[str] = None
    explanation_zh: Optional[str] = None
    hints: List[QuestionHint] = []

class QuestionMetadata(BaseModel):
    subject: Subject
    category: str
    grade_level: int
    grade_code: str
    education_level: str
    difficulty_level: DifficultyLevel
    difficulty_score: int
    adaptive_factor: float
    topics: List[str]
    question_type: QuestionType
    source: str
    original_id: Optional[int] = None

class MathContent(BaseModel):
    has_mathml: bool
    latex_expressions: List[str] = []
    math_complexity: str

class QualityMetrics(BaseModel):
    content_quality_score: float
    math_accuracy_score: float
    pedagogical_value_score: float
    accessibility_score: float

class TranslationStatus(BaseModel):
    en: TranslationStatus
    ko: TranslationStatus
    zh: TranslationStatus

class QuestionResponse(BaseModel):
    id: str
    original_id: Optional[int]
    title: str
    content: QuestionContent
    metadata: QuestionMetadata
    math_content: MathContent
    adaptive_learning: Optional[AdaptiveLearningMetadata] = None
    quality_metrics: QualityMetrics
    translation_status: TranslationStatus
    created_at: datetime
    updated_at: datetime
    version: str

    @classmethod
    def from_db_row(cls, row):
        """Create QuestionResponse from database row"""
        return cls(
            id=str(row.id),
            original_id=row.original_id,
            title=row.title,
            content=QuestionContent(
                question_en=row.question_en,
                question_ko=row.question_ko,
                question_zh=row.question_zh,
                answer_en=row.answer_en,
                answer_ko=row.answer_ko,
                answer_zh=row.answer_zh,
                solution_en=row.solution_en,
                solution_ko=row.solution_ko,
                solution_zh=row.solution_zh,
                explanation_en=row.explanation_en,
                explanation_ko=row.explanation_ko,
                explanation_zh=row.explanation_zh,
                hints=[QuestionHint(**hint) for hint in (row.hints or [])]
            ),
            metadata=QuestionMetadata(
                subject=row.subject,
                category=row.category,
                grade_level=row.grade_level,
                grade_code=row.grade_code,
                education_level=row.education_level,
                difficulty_level=row.difficulty_level,
                difficulty_score=row.difficulty_score,
                adaptive_factor=row.adaptive_factor,
                topics=row.topics,
                question_type=row.question_type,
                source=row.source,
                original_id=row.original_id
            ),
            math_content=MathContent(
                has_mathml=row.has_mathml,
                latex_expressions=row.latex_expressions,
                math_complexity=row.math_complexity
            ),
            adaptive_learning=AdaptiveLearningMetadata(**row.adaptive_learning) if row.adaptive_learning else None,
            quality_metrics=QualityMetrics(
                content_quality_score=row.content_quality_score,
                math_accuracy_score=row.math_accuracy_score,
                pedagogical_value_score=row.pedagogical_value_score,
                accessibility_score=row.accessibility_score
            ),
            translation_status=TranslationStatus(
                en=row.translation_status_en,
                ko=row.translation_status_ko,
                zh=row.translation_status_zh
            ),
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version
        )

# Adaptive Learning Schemas

class PersonalizedQuestionRequest(BaseModel):
    student_id: str
    subject: Subject
    limit: int = Field(default=10, ge=1, le=50)

class LearningSessionCreate(BaseModel):
    student_id: str
    session_type: str
    subject: Subject
    grade_level: Optional[int] = None
    initial_difficulty: float = 1.0

class QuestionAttemptCreate(BaseModel):
    session_id: str
    question_id: str
    student_id: str
    student_answer: Optional[str] = None
    is_correct: bool
    time_spent_seconds: int
    attempts_count: int = 1
    difficulty_at_attempt: float
    hints_used: int = 0

class LearningAnalyticsResponse(BaseModel):
    overall_performance: Dict[str, Any]
    subject_performance: List[Dict[str, Any]]
    topic_progress: List[Dict[str, Any]]
    recent_sessions: List[Dict[str, Any]]

# Statistics Schemas

class QuestionStatistics(BaseModel):
    overview: Dict[str, Any]
    subject_distribution: List[Dict[str, Any]]
    grade_distribution: List[Dict[str, Any]]
    difficulty_distribution: List[Dict[str, Any]]
