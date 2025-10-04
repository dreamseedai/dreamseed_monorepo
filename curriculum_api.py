#!/usr/bin/env python3
"""
DreamSeedAI Curriculum API
API endpoints for curriculum-based question recommendations
"""

import json
import os
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pydantic models for API
class CurriculumRecommendationRequest(BaseModel):
    student_id: str
    country: str = Field(..., description="US or Canada")
    subject: str = Field(..., description="Mathematics, Physics, Chemistry, Biology")
    grade: str = Field(..., description="G9, G10, G11, G12")
    course: Optional[str] = Field(None, description="Specific course name")
    topic: Optional[str] = Field(None, description="Specific topic")
    limit: int = Field(default=10, ge=1, le=50, description="Number of questions to return")
    difficulty_preference: Optional[str] = Field(None, description="beginner, intermediate, advanced, expert")

class CurriculumProgressRequest(BaseModel):
    student_id: str
    country: str
    subject: str
    grade: str
    course: str
    topic: str
    question_id: str
    is_correct: bool
    time_spent_seconds: int

class CurriculumAnalyticsRequest(BaseModel):
    student_id: str
    country: str
    subject: Optional[str] = None
    grade: Optional[str] = None

class CurriculumQuestionResponse(BaseModel):
    question_id: str
    title: str
    confidence: float
    difficulty_level: str
    content_quality_score: float
    curriculum_alignment: float
    topic: str
    course: str

class CurriculumProgressResponse(BaseModel):
    subject: str
    grade: str
    course: str
    topic: str
    questions_attempted: int
    questions_correct: int
    mastery_level: float
    last_attempted: Optional[str]

class CurriculumAnalyticsResponse(BaseModel):
    overall_progress: Dict[str, Any]
    subject_progress: List[Dict[str, Any]]
    topic_progress: List[Dict[str, Any]]
    recommendations: List[str]

# Database connection function
def get_db_connection():
    """Get database connection"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'dreamseedai'),
        'user': os.getenv('DB_USER', 'dreamseedai'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }
    
    connection = psycopg2.connect(**db_config)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        yield cursor
    finally:
        cursor.close()
        connection.close()

# FastAPI app
app = FastAPI(
    title="DreamSeedAI Curriculum API",
    description="API for curriculum-based question recommendations and progress tracking",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "DreamSeedAI Curriculum API is running", "version": "1.0.0"}

@app.post("/curriculum/recommendations", response_model=List[CurriculumQuestionResponse])
async def get_curriculum_recommendations(
    request: CurriculumRecommendationRequest,
    db = Depends(get_db_connection)
):
    """
    Get curriculum-based question recommendations for a student
    """
    try:
        # Build query based on request parameters
        if request.country == 'US':
            base_query = """
                SELECT 
                    q.id as question_id,
                    q.title,
                    q.us_curriculum_confidence as confidence,
                    q.difficulty_level,
                    q.content_quality_score,
                    q.us_curriculum_alignment as curriculum_alignment,
                    q.us_curriculum_topic as topic,
                    q.us_curriculum_course as course
                FROM questions q
                WHERE q.us_curriculum_grade = %(grade)s
                AND q.us_curriculum_subject = %(subject)s
                AND q.us_curriculum_confidence >= 0.7
            """
            params = {
                'grade': request.grade,
                'subject': request.subject,
                'limit': request.limit
            }
        else:  # Canada
            base_query = """
                SELECT 
                    q.id as question_id,
                    q.title,
                    q.canada_curriculum_confidence as confidence,
                    q.difficulty_level,
                    q.content_quality_score,
                    q.canada_curriculum_alignment as curriculum_alignment,
                    q.canada_curriculum_topic as topic,
                    q.canada_curriculum_course as course
                FROM questions q
                WHERE q.canada_curriculum_grade = %(grade)s
                AND q.canada_curriculum_subject = %(subject)s
                AND q.canada_curriculum_confidence >= 0.7
            """
            params = {
                'grade': request.grade,
                'subject': request.subject,
                'limit': request.limit
            }
        
        # Add optional filters
        if request.course:
            base_query += " AND course = %(course)s"
            params['course'] = request.course
        
        if request.topic:
            base_query += " AND topic = %(topic)s"
            params['topic'] = request.topic
        
        if request.difficulty_preference:
            base_query += " AND q.difficulty_level = %(difficulty)s"
            params['difficulty'] = request.difficulty_preference
        
        # Add ordering and limit
        base_query += """
            ORDER BY confidence DESC, content_quality_score DESC
            LIMIT %(limit)s
        """
        
        db.execute(base_query, params)
        results = db.fetchall()
        
        # Convert to response format
        recommendations = []
        for row in results:
            recommendations.append(CurriculumQuestionResponse(
                question_id=str(row['question_id']),
                title=row['title'],
                confidence=float(row['confidence']),
                difficulty_level=row['difficulty_level'],
                content_quality_score=float(row['content_quality_score']),
                curriculum_alignment=float(row['curriculum_alignment']) if row['curriculum_alignment'] else 0.0,
                topic=row['topic'],
                course=row['course']
            ))
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting curriculum recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/curriculum/progress")
async def update_curriculum_progress(
    request: CurriculumProgressRequest,
    db = Depends(get_db_connection)
):
    """
    Update student's curriculum progress
    """
    try:
        # Update curriculum progress using the database function
        update_query = """
            SELECT update_curriculum_progress(
                %(student_id)s::uuid,
                %(country)s,
                %(subject)s,
                %(grade)s,
                %(course)s,
                %(topic)s,
                %(is_correct)s
            )
        """
        
        db.execute(update_query, {
            'student_id': request.student_id,
            'country': request.country,
            'subject': request.subject,
            'grade': request.grade,
            'course': request.course,
            'topic': request.topic,
            'is_correct': request.is_correct
        })
        
        return {"message": "Curriculum progress updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating curriculum progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/curriculum/progress/{student_id}", response_model=List[CurriculumProgressResponse])
async def get_curriculum_progress(
    student_id: str,
    country: str = Query(..., description="US or Canada"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    grade: Optional[str] = Query(None, description="Filter by grade"),
    db = Depends(get_db_connection)
):
    """
    Get student's curriculum progress
    """
    try:
        query = """
            SELECT 
                subject,
                grade,
                course,
                topic,
                questions_attempted,
                questions_correct,
                mastery_level,
                last_attempted
            FROM curriculum_progress
            WHERE student_id = %(student_id)s
            AND country = %(country)s
        """
        
        params = {
            'student_id': student_id,
            'country': country
        }
        
        if subject:
            query += " AND subject = %(subject)s"
            params['subject'] = subject
        
        if grade:
            query += " AND grade = %(grade)s"
            params['grade'] = grade
        
        query += " ORDER BY mastery_level DESC, questions_attempted DESC"
        
        db.execute(query, params)
        results = db.fetchall()
        
        progress = []
        for row in results:
            progress.append(CurriculumProgressResponse(
                subject=row['subject'],
                grade=row['grade'],
                course=row['course'],
                topic=row['topic'],
                questions_attempted=row['questions_attempted'],
                questions_correct=row['questions_correct'],
                mastery_level=float(row['mastery_level']),
                last_attempted=row['last_attempted'].isoformat() if row['last_attempted'] else None
            ))
        
        return progress
        
    except Exception as e:
        logger.error(f"Error getting curriculum progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/curriculum/analytics", response_model=CurriculumAnalyticsResponse)
async def get_curriculum_analytics(
    request: CurriculumAnalyticsRequest,
    db = Depends(get_db_connection)
):
    """
    Get comprehensive curriculum analytics for a student
    """
    try:
        # Overall progress
        overall_query = """
            SELECT 
                COUNT(*) as total_topics,
                SUM(questions_attempted) as total_attempts,
                SUM(questions_correct) as total_correct,
                AVG(mastery_level) as avg_mastery
            FROM curriculum_progress
            WHERE student_id = %(student_id)s
            AND country = %(country)s
        """
        
        params = {
            'student_id': request.student_id,
            'country': request.country
        }
        
        if request.subject:
            overall_query += " AND subject = %(subject)s"
            params['subject'] = request.subject
        
        if request.grade:
            overall_query += " AND grade = %(grade)s"
            params['grade'] = request.grade
        
        db.execute(overall_query, params)
        overall_result = db.fetchone()
        
        # Subject progress
        subject_query = """
            SELECT 
                subject,
                COUNT(*) as topics_covered,
                SUM(questions_attempted) as total_attempts,
                SUM(questions_correct) as total_correct,
                AVG(mastery_level) as avg_mastery
            FROM curriculum_progress
            WHERE student_id = %(student_id)s
            AND country = %(country)s
        """
        
        if request.subject:
            subject_query += " AND subject = %(subject)s"
        
        if request.grade:
            subject_query += " AND grade = %(grade)s"
        
        subject_query += " GROUP BY subject ORDER BY avg_mastery DESC"
        
        db.execute(subject_query, params)
        subject_results = db.fetchall()
        
        # Topic progress
        topic_query = """
            SELECT 
                subject,
                grade,
                course,
                topic,
                questions_attempted,
                questions_correct,
                mastery_level,
                last_attempted
            FROM curriculum_progress
            WHERE student_id = %(student_id)s
            AND country = %(country)s
        """
        
        if request.subject:
            topic_query += " AND subject = %(subject)s"
        
        if request.grade:
            topic_query += " AND grade = %(grade)s"
        
        topic_query += " ORDER BY mastery_level DESC, questions_attempted DESC LIMIT 20"
        
        db.execute(topic_query, params)
        topic_results = db.fetchall()
        
        # Generate recommendations
        recommendations = []
        if overall_result and overall_result['avg_mastery'] < 0.7:
            recommendations.append("Focus on topics with lower mastery levels")
        
        if subject_results:
            weak_subjects = [s['subject'] for s in subject_results if s['avg_mastery'] < 0.6]
            if weak_subjects:
                recommendations.append(f"Consider additional practice in: {', '.join(weak_subjects)}")
        
        return CurriculumAnalyticsResponse(
            overall_progress=dict(overall_result) if overall_result else {},
            subject_progress=[dict(row) for row in subject_results],
            topic_progress=[dict(row) for row in topic_results],
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error getting curriculum analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/curriculum/standards")
async def get_curriculum_standards(
    country: str = Query(..., description="US or Canada"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    grade: Optional[str] = Query(None, description="Filter by grade"),
    db = Depends(get_db_connection)
):
    """
    Get curriculum standards for a country
    """
    try:
        query = """
            SELECT 
                country,
                subject,
                grade,
                course,
                topic,
                description,
                difficulty_level
            FROM curriculum_standards
            WHERE country = %(country)s
        """
        
        params = {'country': country}
        
        if subject:
            query += " AND subject = %(subject)s"
            params['subject'] = subject
        
        if grade:
            query += " AND grade = %(grade)s"
            params['grade'] = grade
        
        query += " ORDER BY subject, grade, course, topic"
        
        db.execute(query, params)
        results = db.fetchall()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"Error getting curriculum standards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/curriculum/statistics")
async def get_curriculum_statistics(
    country: Optional[str] = Query(None, description="US or Canada"),
    db = Depends(get_db_connection)
):
    """
    Get curriculum classification statistics
    """
    try:
        if country == 'US':
            query = """
                SELECT 
                    us_curriculum_grade as grade,
                    us_curriculum_subject as subject,
                    us_curriculum_course as course,
                    COUNT(*) as question_count,
                    AVG(us_curriculum_confidence) as avg_confidence
                FROM questions
                WHERE us_curriculum_grade IS NOT NULL
                GROUP BY us_curriculum_grade, us_curriculum_subject, us_curriculum_course
                ORDER BY grade, subject, course
            """
        elif country == 'Canada':
            query = """
                SELECT 
                    canada_curriculum_grade as grade,
                    canada_curriculum_subject as subject,
                    canada_curriculum_course as course,
                    COUNT(*) as question_count,
                    AVG(canada_curriculum_confidence) as avg_confidence
                FROM questions
                WHERE canada_curriculum_grade IS NOT NULL
                GROUP BY canada_curriculum_grade, canada_curriculum_subject, canada_curriculum_course
                ORDER BY grade, subject, course
            """
        else:
            # Both countries
            query = """
                SELECT 
                    'US' as country,
                    us_curriculum_grade as grade,
                    us_curriculum_subject as subject,
                    us_curriculum_course as course,
                    COUNT(*) as question_count,
                    AVG(us_curriculum_confidence) as avg_confidence
                FROM questions
                WHERE us_curriculum_grade IS NOT NULL
                GROUP BY us_curriculum_grade, us_curriculum_subject, us_curriculum_course
                
                UNION ALL
                
                SELECT 
                    'Canada' as country,
                    canada_curriculum_grade as grade,
                    canada_curriculum_subject as subject,
                    canada_curriculum_course as course,
                    COUNT(*) as question_count,
                    AVG(canada_curriculum_confidence) as avg_confidence
                FROM questions
                WHERE canada_curriculum_grade IS NOT NULL
                GROUP BY canada_curriculum_grade, canada_curriculum_subject, canada_curriculum_course
                
                ORDER BY country, grade, subject, course
            """
        
        db.execute(query)
        results = db.fetchall()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"Error getting curriculum statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
