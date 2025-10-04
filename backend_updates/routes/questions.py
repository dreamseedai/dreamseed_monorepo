
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
