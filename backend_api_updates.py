#!/usr/bin/env python3
"""
DreamSeedAI Backend API Updates
Updates backend API to work with new enhanced schema and adaptive learning features
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class BackendAPIUpdater:
    """
    Updates backend API endpoints and services for enhanced schema
    """
    
    def __init__(self):
        self.api_endpoints = []
        self.service_files = []
        
    def generate_question_service(self) -> str:
        """
        Generate enhanced question service with adaptive learning support
        """
        return '''
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.question import Question, QuestionHint, AdaptiveLearningMetadata
from models.student import Student, StudentProgress
from schemas.question import QuestionResponse, QuestionCreate, QuestionUpdate
from schemas.adaptive import AdaptiveLearningRequest, PersonalizedQuestionRequest
import logging

logger = logging.getLogger(__name__)

class QuestionService:
    """Enhanced question service with adaptive learning capabilities"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_question_by_id(self, question_id: str) -> Optional[QuestionResponse]:
        """Get question by ID with all related data"""
        try:
            # Get question with hints and adaptive metadata
            query = text("""
                SELECT 
                    q.*,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'id', h.id,
                                'hint_text_en', h.hint_text_en,
                                'hint_text_ko', h.hint_text_ko,
                                'hint_text_zh', h.hint_text_zh,
                                'hint_order', h.hint_order
                            ) ORDER BY h.hint_order
                        ) FILTER (WHERE h.id IS NOT NULL), 
                        '[]'::json
                    ) as hints,
                    json_build_object(
                        'prerequisites', alm.prerequisites,
                        'learning_objectives', alm.learning_objectives,
                        'assessment_criteria', alm.assessment_criteria,
                        'min_difficulty', alm.min_difficulty,
                        'max_difficulty', alm.max_difficulty,
                        'optimal_difficulty', alm.optimal_difficulty,
                        'success_indicators', alm.success_indicators
                    ) as adaptive_learning
                FROM questions q
                LEFT JOIN question_hints h ON q.id = h.question_id
                LEFT JOIN adaptive_learning_metadata alm ON q.id = alm.question_id
                WHERE q.id = :question_id
                GROUP BY q.id, alm.id
            """)
            
            result = self.db.execute(query, {"question_id": question_id}).fetchone()
            
            if not result:
                return None
            
            return QuestionResponse.from_db_row(result)
            
        except Exception as e:
            logger.error(f"Error getting question {question_id}: {e}")
            return None
    
    def get_personalized_questions(self, request: PersonalizedQuestionRequest) -> List[QuestionResponse]:
        """Get personalized questions based on student's learning profile"""
        try:
            # Call the database function for personalized questions
            query = text("""
                SELECT * FROM get_personalized_questions(
                    :student_id, :subject, :limit
                )
            """)
            
            results = self.db.execute(query, {
                "student_id": request.student_id,
                "subject": request.subject,
                "limit": request.limit
            }).fetchall()
            
            questions = []
            for row in results:
                # Get full question details
                question = self.get_question_by_id(row.question_id)
                if question:
                    questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error getting personalized questions: {e}")
            return []
    
    def get_questions_by_filters(self, 
                                subject: Optional[str] = None,
                                grade_level: Optional[int] = None,
                                difficulty_level: Optional[str] = None,
                                topics: Optional[List[str]] = None,
                                has_mathml: Optional[bool] = None,
                                limit: int = 20,
                                offset: int = 0) -> List[QuestionResponse]:
        """Get questions with advanced filtering"""
        try:
            # Build dynamic query
            where_conditions = []
            params = {"limit": limit, "offset": offset}
            
            if subject:
                where_conditions.append("q.subject = :subject")
                params["subject"] = subject
            
            if grade_level:
                where_conditions.append("q.grade_level = :grade_level")
                params["grade_level"] = grade_level
            
            if difficulty_level:
                where_conditions.append("q.difficulty_level = :difficulty_level")
                params["difficulty_level"] = difficulty_level
            
            if topics:
                where_conditions.append("q.topics && :topics")
                params["topics"] = topics
            
            if has_mathml is not None:
                where_conditions.append("q.has_mathml = :has_mathml")
                params["has_mathml"] = has_mathml
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            query = text(f"""
                SELECT 
                    q.*,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'id', h.id,
                                'hint_text_en', h.hint_text_en,
                                'hint_text_ko', h.hint_text_ko,
                                'hint_text_zh', h.hint_text_zh,
                                'hint_order', h.hint_order
                            ) ORDER BY h.hint_order
                        ) FILTER (WHERE h.id IS NOT NULL), 
                        '[]'::json
                    ) as hints
                FROM questions q
                LEFT JOIN question_hints h ON q.id = h.question_id
                WHERE {where_clause}
                GROUP BY q.id
                ORDER BY q.content_quality_score DESC, q.created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            results = self.db.execute(query, params).fetchall()
            
            questions = []
            for row in results:
                questions.append(QuestionResponse.from_db_row(row))
            
            return questions
            
        except Exception as e:
            logger.error(f"Error getting filtered questions: {e}")
            return []
    
    def search_questions(self, search_term: str, language: str = 'en', limit: int = 20) -> List[QuestionResponse]:
        """Search questions using full-text search"""
        try:
            if language == 'ko':
                search_column = "to_tsvector('korean', q.question_ko || ' ' || COALESCE(q.answer_ko, '') || ' ' || COALESCE(q.solution_ko, ''))"
            else:
                search_column = "to_tsvector('english', q.question_en || ' ' || COALESCE(q.answer_en, '') || ' ' || COALESCE(q.solution_en, ''))"
            
            query = text(f"""
                SELECT 
                    q.*,
                    ts_rank({search_column}, plainto_tsquery(:search_term)) as rank,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'id', h.id,
                                'hint_text_en', h.hint_text_en,
                                'hint_text_ko', h.hint_text_ko,
                                'hint_text_zh', h.hint_text_zh,
                                'hint_order', h.hint_order
                            ) ORDER BY h.hint_order
                        ) FILTER (WHERE h.id IS NOT NULL), 
                        '[]'::json
                    ) as hints
                FROM questions q
                LEFT JOIN question_hints h ON q.id = h.question_id
                WHERE {search_column} @@ plainto_tsquery(:search_term)
                GROUP BY q.id, rank
                ORDER BY rank DESC, q.content_quality_score DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(query, {
                "search_term": search_term,
                "limit": limit
            }).fetchall()
            
            questions = []
            for row in results:
                questions.append(QuestionResponse.from_db_row(row))
            
            return questions
            
        except Exception as e:
            logger.error(f"Error searching questions: {e}")
            return []
    
    def get_question_statistics(self) -> Dict[str, Any]:
        """Get comprehensive question statistics"""
        try:
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_questions,
                    COUNT(*) FILTER (WHERE has_mathml = TRUE) as mathml_questions,
                    COUNT(*) FILTER (WHERE translation_status_ko = 'complete') as korean_translated,
                    COUNT(*) FILTER (WHERE translation_status_zh = 'complete') as chinese_translated,
                    AVG(content_quality_score) as avg_content_quality,
                    AVG(math_accuracy_score) as avg_math_accuracy,
                    AVG(pedagogical_value_score) as avg_pedagogical_value,
                    AVG(accessibility_score) as avg_accessibility
                FROM questions
            """)
            
            result = self.db.execute(stats_query).fetchone()
            
            # Subject distribution
            subject_query = text("""
                SELECT subject, COUNT(*) as count
                FROM questions
                GROUP BY subject
                ORDER BY count DESC
            """)
            
            subject_results = self.db.execute(subject_query).fetchall()
            
            # Grade distribution
            grade_query = text("""
                SELECT grade_level, COUNT(*) as count
                FROM questions
                GROUP BY grade_level
                ORDER BY grade_level
            """)
            
            grade_results = self.db.execute(grade_query).fetchall()
            
            # Difficulty distribution
            difficulty_query = text("""
                SELECT difficulty_level, COUNT(*) as count
                FROM questions
                GROUP BY difficulty_level
                ORDER BY count DESC
            """)
            
            difficulty_results = self.db.execute(difficulty_query).fetchall()
            
            return {
                "overview": dict(result),
                "subject_distribution": [dict(row) for row in subject_results],
                "grade_distribution": [dict(row) for row in grade_results],
                "difficulty_distribution": [dict(row) for row in difficulty_results]
            }
            
        except Exception as e:
            logger.error(f"Error getting question statistics: {e}")
            return {}
'''
    
    def generate_adaptive_learning_service(self) -> str:
        """
        Generate adaptive learning service
        """
        return '''
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.student import Student, StudentProgress, LearningSession, QuestionAttempt
from schemas.adaptive import AdaptiveLearningRequest, LearningSessionCreate, QuestionAttemptCreate
import logging

logger = logging.getLogger(__name__)

class AdaptiveLearningService:
    """Service for adaptive learning functionality"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_learning_session(self, session_data: LearningSessionCreate) -> str:
        """Create a new learning session"""
        try:
            query = text("""
                INSERT INTO learning_sessions (
                    student_id, session_type, subject, grade_level,
                    initial_difficulty
                ) VALUES (
                    :student_id, :session_type, :subject, :grade_level,
                    :initial_difficulty
                ) RETURNING id
            """)
            
            result = self.db.execute(query, {
                "student_id": session_data.student_id,
                "session_type": session_data.session_type,
                "subject": session_data.subject,
                "grade_level": session_data.grade_level,
                "initial_difficulty": session_data.initial_difficulty
            })
            
            session_id = result.fetchone()[0]
            self.db.commit()
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating learning session: {e}")
            self.db.rollback()
            raise
    
    def record_question_attempt(self, attempt_data: QuestionAttemptCreate) -> Dict[str, Any]:
        """Record a question attempt and update adaptive learning state"""
        try:
            # Insert question attempt
            insert_query = text("""
                INSERT INTO question_attempts (
                    session_id, question_id, student_id, student_answer,
                    is_correct, time_spent_seconds, attempts_count,
                    difficulty_at_attempt, hints_used
                ) VALUES (
                    :session_id, :question_id, :student_id, :student_answer,
                    :is_correct, :time_spent_seconds, :attempts_count,
                    :difficulty_at_attempt, :hints_used
                ) RETURNING id
            """)
            
            result = self.db.execute(insert_query, {
                "session_id": attempt_data.session_id,
                "question_id": attempt_data.question_id,
                "student_id": attempt_data.student_id,
                "student_answer": attempt_data.student_answer,
                "is_correct": attempt_data.is_correct,
                "time_spent_seconds": attempt_data.time_spent_seconds,
                "attempts_count": attempt_data.attempts_count,
                "difficulty_at_attempt": attempt_data.difficulty_at_attempt,
                "hints_used": attempt_data.hints_used
            })
            
            attempt_id = result.fetchone()[0]
            
            # Calculate new difficulty
            difficulty_query = text("""
                SELECT calculate_difficulty_adjustment(
                    :student_id, :question_id, :is_correct, :time_spent_seconds
                ) as new_difficulty
            """)
            
            difficulty_result = self.db.execute(difficulty_query, {
                "student_id": attempt_data.student_id,
                "question_id": attempt_data.question_id,
                "is_correct": attempt_data.is_correct,
                "time_spent_seconds": attempt_data.time_spent_seconds
            })
            
            new_difficulty = difficulty_result.fetchone()[0]
            
            # Update student progress
            self._update_student_progress(
                attempt_data.student_id,
                attempt_data.question_id,
                attempt_data.is_correct,
                new_difficulty
            )
            
            self.db.commit()
            
            return {
                "attempt_id": attempt_id,
                "new_difficulty": new_difficulty,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error recording question attempt: {e}")
            self.db.rollback()
            raise
    
    def _update_student_progress(self, student_id: str, question_id: str, 
                                is_correct: bool, new_difficulty: float):
        """Update student progress based on question attempt"""
        try:
            # Get question subject and topics
            question_query = text("""
                SELECT subject, topics FROM questions WHERE id = :question_id
            """)
            
            question_result = self.db.execute(question_query, {"question_id": question_id}).fetchone()
            
            if not question_result:
                return
            
            subject = question_result.subject
            topics = question_result.topics
            
            # Update progress for each topic
            for topic in topics:
                upsert_query = text("""
                    INSERT INTO student_progress (
                        student_id, subject, topic, mastery_level,
                        questions_attempted, questions_correct,
                        current_difficulty, last_updated
                    ) VALUES (
                        :student_id, :subject, :topic, :mastery_level,
                        1, :correct_count, :current_difficulty, NOW()
                    )
                    ON CONFLICT (student_id, subject, topic)
                    DO UPDATE SET
                        questions_attempted = student_progress.questions_attempted + 1,
                        questions_correct = student_progress.questions_correct + :correct_count,
                        current_difficulty = :current_difficulty,
                        mastery_level = CASE 
                            WHEN student_progress.questions_attempted + 1 > 0 
                            THEN (student_progress.questions_correct + :correct_count)::DECIMAL / (student_progress.questions_attempted + 1)
                            ELSE 0
                        END,
                        last_updated = NOW()
                """)
                
                self.db.execute(upsert_query, {
                    "student_id": student_id,
                    "subject": subject,
                    "topic": topic,
                    "mastery_level": 1.0 if is_correct else 0.0,
                    "correct_count": 1 if is_correct else 0,
                    "current_difficulty": new_difficulty
                })
                
        except Exception as e:
            logger.error(f"Error updating student progress: {e}")
            raise
    
    def get_student_learning_analytics(self, student_id: str) -> Dict[str, Any]:
        """Get comprehensive learning analytics for a student"""
        try:
            # Overall performance
            performance_query = text("""
                SELECT 
                    COUNT(*) as total_attempts,
                    COUNT(*) FILTER (WHERE is_correct = TRUE) as correct_attempts,
                    AVG(time_spent_seconds) as avg_time_per_question,
                    AVG(difficulty_at_attempt) as avg_difficulty
                FROM question_attempts
                WHERE student_id = :student_id
            """)
            
            performance_result = self.db.execute(performance_query, {"student_id": student_id}).fetchone()
            
            # Subject-wise performance
            subject_query = text("""
                SELECT 
                    q.subject,
                    COUNT(*) as total_attempts,
                    COUNT(*) FILTER (WHERE qa.is_correct = TRUE) as correct_attempts,
                    AVG(qa.time_spent_seconds) as avg_time,
                    AVG(qa.difficulty_at_attempt) as avg_difficulty
                FROM question_attempts qa
                JOIN questions q ON qa.question_id = q.id
                WHERE qa.student_id = :student_id
                GROUP BY q.subject
                ORDER BY total_attempts DESC
            """)
            
            subject_results = self.db.execute(subject_query, {"student_id": student_id}).fetchall()
            
            # Topic-wise progress
            topic_query = text("""
                SELECT 
                    subject, topic, mastery_level, questions_attempted,
                    questions_correct, current_difficulty, learning_velocity
                FROM student_progress
                WHERE student_id = :student_id
                ORDER BY mastery_level DESC, questions_attempted DESC
            """)
            
            topic_results = self.db.execute(topic_query, {"student_id": student_id}).fetchall()
            
            # Recent sessions
            sessions_query = text("""
                SELECT 
                    id, session_type, subject, total_questions,
                    correct_answers, session_score, duration_minutes,
                    started_at, completed_at
                FROM learning_sessions
                WHERE student_id = :student_id
                ORDER BY started_at DESC
                LIMIT 10
            """)
            
            sessions_results = self.db.execute(sessions_query, {"student_id": student_id}).fetchall()
            
            return {
                "overall_performance": dict(performance_result),
                "subject_performance": [dict(row) for row in subject_results],
                "topic_progress": [dict(row) for row in topic_results],
                "recent_sessions": [dict(row) for row in sessions_results]
            }
            
        except Exception as e:
            logger.error(f"Error getting student analytics: {e}")
            return {}
'''
    
    def generate_api_routes(self) -> str:
        """
        Generate FastAPI routes for enhanced functionality
        """
        return '''
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from services.question_service import QuestionService
from services.adaptive_learning_service import AdaptiveLearningService
from schemas.question import QuestionResponse, PersonalizedQuestionRequest
from schemas.adaptive import LearningSessionCreate, QuestionAttemptCreate, LearningAnalyticsResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific question with all related data"""
    service = QuestionService(db)
    question = service.get_question_by_id(question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return question

@router.get("/questions", response_model=List[QuestionResponse])
async def get_questions(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    grade_level: Optional[int] = Query(None, description="Filter by grade level"),
    difficulty_level: Optional[str] = Query(None, description="Filter by difficulty level"),
    topics: Optional[List[str]] = Query(None, description="Filter by topics"),
    has_mathml: Optional[bool] = Query(None, description="Filter by MathML content"),
    limit: int = Query(20, ge=1, le=100, description="Number of questions to return"),
    offset: int = Query(0, ge=0, description="Number of questions to skip"),
    db: Session = Depends(get_db)
):
    """Get questions with advanced filtering"""
    service = QuestionService(db)
    questions = service.get_questions_by_filters(
        subject=subject,
        grade_level=grade_level,
        difficulty_level=difficulty_level,
        topics=topics,
        has_mathml=has_mathml,
        limit=limit,
        offset=offset
    )
    
    return questions

@router.get("/questions/search", response_model=List[QuestionResponse])
async def search_questions(
    q: str = Query(..., description="Search term"),
    language: str = Query("en", description="Search language (en, ko)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """Search questions using full-text search"""
    service = QuestionService(db)
    questions = service.search_questions(q, language, limit)
    
    return questions

@router.post("/questions/personalized", response_model=List[QuestionResponse])
async def get_personalized_questions(
    request: PersonalizedQuestionRequest,
    db: Session = Depends(get_db)
):
    """Get personalized questions based on student's learning profile"""
    service = QuestionService(db)
    questions = service.get_personalized_questions(request)
    
    return questions

@router.get("/questions/statistics")
async def get_question_statistics(
    db: Session = Depends(get_db)
):
    """Get comprehensive question statistics"""
    service = QuestionService(db)
    stats = service.get_question_statistics()
    
    return stats

# Adaptive Learning Routes

@router.post("/learning/sessions")
async def create_learning_session(
    session_data: LearningSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new learning session"""
    service = AdaptiveLearningService(db)
    session_id = service.create_learning_session(session_data)
    
    return {"session_id": session_id, "message": "Learning session created successfully"}

@router.post("/learning/attempts")
async def record_question_attempt(
    attempt_data: QuestionAttemptCreate,
    db: Session = Depends(get_db)
):
    """Record a question attempt and update adaptive learning state"""
    service = AdaptiveLearningService(db)
    result = service.record_question_attempt(attempt_data)
    
    return result

@router.get("/learning/analytics/{student_id}", response_model=LearningAnalyticsResponse)
async def get_student_analytics(
    student_id: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive learning analytics for a student"""
    service = AdaptiveLearningService(db)
    analytics = service.get_student_learning_analytics(student_id)
    
    return analytics

@router.get("/learning/progress/{student_id}")
async def get_student_progress(
    student_id: str,
    subject: Optional[str] = Query(None, description="Filter by subject"),
    db: Session = Depends(get_db)
):
    """Get student's learning progress"""
    service = AdaptiveLearningService(db)
    
    # This would be implemented in the service
    # For now, return a placeholder
    return {"message": "Student progress endpoint - to be implemented"}
'''
    
    def generate_schemas(self) -> str:
        """
        Generate Pydantic schemas for enhanced functionality
        """
        return '''
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
'''
    
    def create_backend_update_files(self):
        """Create all backend update files"""
        
        # Create services directory
        os.makedirs('backend_updates/services', exist_ok=True)
        os.makedirs('backend_updates/schemas', exist_ok=True)
        os.makedirs('backend_updates/routes', exist_ok=True)
        
        # Generate service files
        with open('backend_updates/services/question_service.py', 'w', encoding='utf-8') as f:
            f.write(self.generate_question_service())
        
        with open('backend_updates/services/adaptive_learning_service.py', 'w', encoding='utf-8') as f:
            f.write(self.generate_adaptive_learning_service())
        
        # Generate schema files
        with open('backend_updates/schemas/question.py', 'w', encoding='utf-8') as f:
            f.write(self.generate_schemas())
        
        # Generate route files
        with open('backend_updates/routes/questions.py', 'w', encoding='utf-8') as f:
            f.write(self.generate_api_routes())
        
        # Generate main app update
        main_app_update = '''
# Main FastAPI app updates
from fastapi import FastAPI
from routes.questions import router as questions_router
from routes.adaptive_learning import router as adaptive_router

app = FastAPI(
    title="DreamSeedAI API",
    description="Enhanced API with adaptive learning and multilingual support",
    version="2.0.0"
)

# Include routers
app.include_router(questions_router, prefix="/api/v2/questions", tags=["questions"])
app.include_router(adaptive_router, prefix="/api/v2/learning", tags=["adaptive_learning"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
'''
        
        with open('backend_updates/main.py', 'w', encoding='utf-8') as f:
            f.write(main_app_update)
        
        # Generate requirements update
        requirements_update = '''
# Updated requirements for enhanced backend
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
pydantic>=2.0.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-dotenv>=1.0.0
alembic>=1.12.0
'''
        
        with open('backend_updates/requirements.txt', 'w', encoding='utf-8') as f:
            f.write(requirements_update)
        
        print("✅ Backend update files created successfully!")
        print("📁 Files created in 'backend_updates/' directory:")
        print("   - services/question_service.py")
        print("   - services/adaptive_learning_service.py")
        print("   - schemas/question.py")
        print("   - routes/questions.py")
        print("   - main.py")
        print("   - requirements.txt")

def main():
    """Main function to create backend updates"""
    updater = BackendAPIUpdater()
    updater.create_backend_update_files()

if __name__ == '__main__':
    main()
