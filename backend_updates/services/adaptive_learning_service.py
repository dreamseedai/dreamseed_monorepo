
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
