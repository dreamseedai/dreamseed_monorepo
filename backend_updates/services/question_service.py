
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
