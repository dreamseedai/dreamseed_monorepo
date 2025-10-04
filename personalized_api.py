"""
DreamSeedAI Personalized Educational API
Enhanced API endpoints for personalized content delivery and user management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json

from app.database import get_db
from app.auth import get_current_user
from app.models import User, UserProfile

# Pydantic models for API requests/responses
class UserProfileUpdate(BaseModel):
    preferred_subjects: Optional[List[str]] = Field(None, description="List of preferred subjects")
    difficulty_preference: Optional[int] = Field(None, ge=1, le=5, description="Difficulty preference 1-5")
    learning_style: Optional[str] = Field(None, description="Learning style preference")
    study_goals: Optional[List[str]] = Field(None, description="Study goals and objectives")
    time_zone: Optional[str] = Field(None, description="User's timezone")
    notification_preferences: Optional[Dict[str, bool]] = Field(None, description="Notification preferences")

class QuestionResponse(BaseModel):
    id: int
    title: str
    description: str
    hint: Optional[str] = None
    solution: Optional[str] = None
    answers: Optional[str] = None
    difficulty_level: int
    estimated_time: Optional[int] = None
    subject: str
    grade: str
    difficulty_tags: List[str] = []
    learning_objectives: List[str] = []
    mathml_content: Optional[str] = None
    tiptap_content: Optional[Dict[str, Any]] = None

class PersonalizedQuestionsResponse(BaseModel):
    questions: List[QuestionResponse]
    total_count: int
    user_preferences: Dict[str, Any]
    recommendation_algorithm: str
    generated_at: datetime

class PerformanceSubmission(BaseModel):
    question_id: int
    is_correct: bool
    time_spent: int
    hints_used: int = 0
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5)
    confidence_level: Optional[int] = Field(None, ge=1, le=5)

class LearningAnalytics(BaseModel):
    user_id: int
    total_questions_attempted: int
    correct_answers: int
    accuracy_percentage: float
    avg_time_per_question: Optional[float]
    avg_mastery_level: Optional[float]
    grade_code: Optional[str]
    preferred_subjects: Optional[List[str]]
    country: Optional[str]

# Create router
router = APIRouter(prefix="/api/personalized", tags=["personalized"])

@router.get("/profile", response_model=Dict[str, Any])
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's personalized profile and preferences"""
    try:
        # Get user profile with educational preferences
        profile = db.execute(text("""
            SELECT 
                up.*,
                u.email,
                u.created_at as user_created_at
            FROM users_profile up
            JOIN users u ON up.user_id = u.id
            WHERE up.user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Convert to dictionary
        profile_dict = dict(profile._mapping)
        
        # Parse JSON fields
        if profile_dict.get('notification_preferences'):
            profile_dict['notification_preferences'] = json.loads(profile_dict['notification_preferences'])
        
        return profile_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user profile: {str(e)}")

@router.post("/profile", response_model=Dict[str, Any])
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's personalized profile and preferences"""
    try:
        # Prepare update data
        update_data = {}
        
        if profile_update.preferred_subjects is not None:
            update_data['preferred_subjects'] = profile_update.preferred_subjects
        
        if profile_update.difficulty_preference is not None:
            update_data['difficulty_preference'] = profile_update.difficulty_preference
        
        if profile_update.learning_style is not None:
            update_data['learning_style'] = profile_update.learning_style
        
        if profile_update.study_goals is not None:
            update_data['study_goals'] = profile_update.study_goals
        
        if profile_update.time_zone is not None:
            update_data['time_zone'] = profile_update.time_zone
        
        if profile_update.notification_preferences is not None:
            update_data['notification_preferences'] = json.dumps(profile_update.notification_preferences)
        
        update_data['updated_at'] = datetime.utcnow()
        
        # Update profile
        if update_data:
            db.execute(text("""
                UPDATE users_profile 
                SET 
                    preferred_subjects = COALESCE(:preferred_subjects, preferred_subjects),
                    difficulty_preference = COALESCE(:difficulty_preference, difficulty_preference),
                    learning_style = COALESCE(:learning_style, learning_style),
                    study_goals = COALESCE(:study_goals, study_goals),
                    time_zone = COALESCE(:time_zone, time_zone),
                    notification_preferences = COALESCE(:notification_preferences, notification_preferences),
                    updated_at = :updated_at
                WHERE user_id = :user_id
            """), {**update_data, "user_id": current_user.id})
            
            db.commit()
        
        # Return updated profile
        return await get_user_profile(current_user, db)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating user profile: {str(e)}")

@router.get("/questions", response_model=PersonalizedQuestionsResponse)
async def get_personalized_questions(
    limit: int = Query(10, ge=1, le=50, description="Number of questions to return"),
    subject_filter: Optional[str] = Query(None, description="Filter by subject (M, B, P)"),
    difficulty_filter: Optional[int] = Query(None, ge=1, le=5, description="Filter by difficulty level"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized questions based on user profile and preferences"""
    try:
        # Get user profile for personalization
        profile = db.execute(text("""
            SELECT preferred_subjects, difficulty_preference, grade_code, country
            FROM users_profile 
            WHERE user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Build personalized query
        query_params = {
            "user_id": current_user.id,
            "limit": limit,
            "preferred_subjects": profile.preferred_subjects or [],
            "difficulty_preference": profile.difficulty_preference or 2
        }
        
        # Base query with personalization logic
        base_query = """
            SELECT 
                qe.id,
                qe.que_en_title as title,
                qe.que_en_desc as description,
                qe.que_en_hint as hint,
                qe.que_en_solution as solution,
                qe.que_en_answers as answers,
                qe.que_level as difficulty_level,
                qe.que_estimated_time as estimated_time,
                qe.que_class as subject,
                qe.que_grade as grade,
                qe.que_difficulty_tags as difficulty_tags,
                qe.que_learning_objectives as learning_objectives,
                qe.que_mathml_content as mathml_content,
                qe.que_tiptap_content as tiptap_content,
                -- Calculate relevance score
                CASE 
                    WHEN :preferred_subjects @> ARRAY[qe.que_class::TEXT] THEN 0.8
                    ELSE 0.4
                END +
                CASE 
                    WHEN qe.que_level BETWEEN (:difficulty_preference - 1) AND (:difficulty_preference + 1) THEN 0.2
                    ELSE 0.0
                END as relevance_score
            FROM questions_enhanced qe
            WHERE qe.que_status = 1
            AND qe.que_en_title IS NOT NULL
        """
        
        # Add filters
        if subject_filter:
            base_query += " AND qe.que_class = :subject_filter"
            query_params["subject_filter"] = subject_filter
        
        if difficulty_filter:
            base_query += " AND qe.que_level = :difficulty_filter"
            query_params["difficulty_filter"] = difficulty_filter
        
        # Add ordering and limit
        base_query += """
            ORDER BY relevance_score DESC, qe.que_level ASC
            LIMIT :limit
        """
        
        # Execute query
        questions = db.execute(text(base_query), query_params).fetchall()
        
        # Convert to response format
        question_responses = []
        for q in questions:
            question_responses.append(QuestionResponse(
                id=q.id,
                title=q.title or "",
                description=q.description or "",
                hint=q.hint,
                solution=q.solution,
                answers=q.answers,
                difficulty_level=q.difficulty_level or 1,
                estimated_time=q.estimated_time,
                subject=q.subject or "M",
                grade=q.grade or "G08",
                difficulty_tags=q.difficulty_tags or [],
                learning_objectives=q.learning_objectives or [],
                mathml_content=q.mathml_content,
                tiptap_content=q.tiptap_content
            ))
        
        return PersonalizedQuestionsResponse(
            questions=question_responses,
            total_count=len(question_responses),
            user_preferences={
                "preferred_subjects": profile.preferred_subjects,
                "difficulty_preference": profile.difficulty_preference,
                "grade_code": profile.grade_code,
                "country": profile.country
            },
            recommendation_algorithm="v1.0",
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving personalized questions: {str(e)}")

@router.post("/performance", response_model=Dict[str, Any])
async def submit_performance(
    performance: PerformanceSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit user performance data for a question"""
    try:
        # Insert performance record
        db.execute(text("""
            INSERT INTO user_performance (
                user_id, question_id, is_correct, time_spent, 
                hints_used, difficulty_rating, confidence_level,
                attempt_date
            ) VALUES (
                :user_id, :question_id, :is_correct, :time_spent,
                :hints_used, :difficulty_rating, :confidence_level,
                NOW()
            )
            ON CONFLICT (user_id, question_id, attempt_date) 
            DO UPDATE SET
                attempt_count = user_performance.attempt_count + 1,
                is_correct = EXCLUDED.is_correct,
                time_spent = EXCLUDED.time_spent,
                hints_used = EXCLUDED.hints_used,
                difficulty_rating = EXCLUDED.difficulty_rating,
                confidence_level = EXCLUDED.confidence_level
        """), {
            "user_id": current_user.id,
            "question_id": performance.question_id,
            "is_correct": performance.is_correct,
            "time_spent": performance.time_spent,
            "hints_used": performance.hints_used,
            "difficulty_rating": performance.difficulty_rating,
            "confidence_level": performance.confidence_level
        })
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Performance data recorded successfully",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error recording performance: {str(e)}")

@router.get("/analytics", response_model=LearningAnalytics)
async def get_learning_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's learning analytics and progress"""
    try:
        # Get analytics using the view we created
        analytics = db.execute(text("""
            SELECT * FROM user_learning_analytics 
            WHERE user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not analytics:
            # Return empty analytics for new users
            return LearningAnalytics(
                user_id=current_user.id,
                total_questions_attempted=0,
                correct_answers=0,
                accuracy_percentage=0.0,
                avg_time_per_question=None,
                avg_mastery_level=None,
                grade_code=None,
                preferred_subjects=None,
                country=None
            )
        
        return LearningAnalytics(
            user_id=analytics.user_id,
            total_questions_attempted=analytics.total_questions_attempted or 0,
            correct_answers=analytics.correct_answers or 0,
            accuracy_percentage=analytics.accuracy_percentage or 0.0,
            avg_time_per_question=analytics.avg_time_per_question,
            avg_mastery_level=analytics.avg_mastery_level,
            grade_code=analytics.grade_code,
            preferred_subjects=analytics.preferred_subjects,
            country=analytics.country
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analytics: {str(e)}")

@router.get("/recommendations", response_model=Dict[str, Any])
async def get_learning_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered learning recommendations"""
    try:
        # Get active recommendations
        recommendations = db.execute(text("""
            SELECT 
                lr.*,
                qe.que_en_title,
                qe.que_class,
                qe.que_level,
                qe.que_estimated_time
            FROM learning_recommendations lr
            LEFT JOIN questions_enhanced qe ON qe.id = ANY(lr.recommended_questions)
            WHERE lr.user_id = :user_id 
            AND lr.is_active = true 
            AND lr.expires_at > NOW()
            ORDER BY lr.generated_at DESC
            LIMIT 1
        """), {"user_id": current_user.id}).fetchone()
        
        if not recommendations:
            # Generate new recommendations using the function
            new_recommendations = db.execute(text("""
                SELECT * FROM get_personalized_questions(:user_id, 10)
            """), {"user_id": current_user.id}).fetchall()
            
            if new_recommendations:
                # Store recommendations
                question_ids = [r.question_id for r in new_recommendations]
                db.execute(text("""
                    INSERT INTO learning_recommendations (
                        user_id, recommended_questions, algorithm_version,
                        confidence_score, generated_at, expires_at
                    ) VALUES (
                        :user_id, :question_ids, 'v1.0',
                        0.8, NOW(), NOW() + INTERVAL '7 days'
                    )
                """), {
                    "user_id": current_user.id,
                    "question_ids": question_ids
                })
                db.commit()
                
                return {
                    "recommendations": [
                        {
                            "question_id": r.question_id,
                            "title": r.title,
                            "difficulty_level": r.difficulty_level,
                            "estimated_time": r.estimated_time,
                            "subject": r.subject,
                            "grade": r.grade,
                            "relevance_score": r.relevance_score
                        } for r in new_recommendations
                    ],
                    "algorithm_version": "v1.0",
                    "confidence_score": 0.8,
                    "generated_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(days=7)
                }
        
        return {
            "recommendations": [],
            "message": "No recommendations available",
            "algorithm_version": "v1.0"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question_details(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific question"""
    try:
        question = db.execute(text("""
            SELECT 
                qe.id,
                qe.que_en_title as title,
                qe.que_en_desc as description,
                qe.que_en_hint as hint,
                qe.que_en_solution as solution,
                qe.que_en_answers as answers,
                qe.que_level as difficulty_level,
                qe.que_estimated_time as estimated_time,
                qe.que_class as subject,
                qe.que_grade as grade,
                qe.que_difficulty_tags as difficulty_tags,
                qe.que_learning_objectives as learning_objectives,
                qe.que_mathml_content as mathml_content,
                qe.que_tiptap_content as tiptap_content
            FROM questions_enhanced qe
            WHERE qe.id = :question_id AND qe.que_status = 1
        """), {"question_id": question_id}).fetchone()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        return QuestionResponse(
            id=question.id,
            title=question.title or "",
            description=question.description or "",
            hint=question.hint,
            solution=question.solution,
            answers=question.answers,
            difficulty_level=question.difficulty_level or 1,
            estimated_time=question.estimated_time,
            subject=question.subject or "M",
            grade=question.grade or "G08",
            difficulty_tags=question.difficulty_tags or [],
            learning_objectives=question.learning_objectives or [],
            mathml_content=question.mathml_content,
            tiptap_content=question.tiptap_content
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving question: {str(e)}")
