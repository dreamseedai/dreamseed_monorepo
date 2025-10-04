#!/usr/bin/env python3
"""
DreamSeedAI Data Loader
Loads migrated data into PostgreSQL database with proper schema mapping
"""

import json
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DreamSeedAIDataLoader:
    """
    Loads migrated data into DreamSeedAI PostgreSQL database
    """
    
    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize data loader with database configuration
        
        Args:
            db_config: Database connection parameters
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            logger.info("Successfully connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Disconnected from database")
    
    def create_schema(self, schema_file: str):
        """
        Create database schema from SQL file
        
        Args:
            schema_file: Path to SQL schema file
        """
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            self.cursor.execute(schema_sql)
            self.connection.commit()
            logger.info("Database schema created successfully")
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            self.connection.rollback()
            raise
    
    def load_questions(self, questions_data: List[Dict[str, Any]], batch_size: int = 100):
        """
        Load questions data into database
        
        Args:
            questions_data: List of question dictionaries
            batch_size: Number of questions to insert per batch
        """
        logger.info(f"Loading {len(questions_data)} questions into database...")
        
        insert_query = """
        INSERT INTO questions (
            original_id, title, question_en, question_ko, question_zh,
            answer_en, answer_ko, answer_zh, solution_en, solution_ko, solution_zh,
            explanation_en, explanation_ko, explanation_zh,
            subject, category, grade_level, grade_code, education_level,
            difficulty_level, difficulty_score, adaptive_factor,
            topics, question_type, has_mathml, latex_expressions, math_complexity,
            content_quality_score, math_accuracy_score, pedagogical_value_score, accessibility_score,
            translation_status_en, translation_status_ko, translation_status_zh,
            source, version
        ) VALUES (
            %(original_id)s, %(title)s, %(question_en)s, %(question_ko)s, %(question_zh)s,
            %(answer_en)s, %(answer_ko)s, %(answer_zh)s, %(solution_en)s, %(solution_ko)s, %(solution_zh)s,
            %(explanation_en)s, %(explanation_ko)s, %(explanation_zh)s,
            %(subject)s, %(category)s, %(grade_level)s, %(grade_code)s, %(education_level)s,
            %(difficulty_level)s, %(difficulty_score)s, %(adaptive_factor)s,
            %(topics)s, %(question_type)s, %(has_mathml)s, %(latex_expressions)s, %(math_complexity)s,
            %(content_quality_score)s, %(math_accuracy_score)s, %(pedagogical_value_score)s, %(accessibility_score)s,
            %(translation_status_en)s, %(translation_status_ko)s, %(translation_status_zh)s,
            %(source)s, %(version)s
        ) RETURNING id
        """
        
        hint_insert_query = """
        INSERT INTO question_hints (question_id, hint_text_en, hint_text_ko, hint_text_zh, hint_order)
        VALUES (%(question_id)s, %(hint_text_en)s, %(hint_text_ko)s, %(hint_text_zh)s, %(hint_order)s)
        """
        
        adaptive_insert_query = """
        INSERT INTO adaptive_learning_metadata (
            question_id, prerequisites, learning_objectives, assessment_criteria,
            min_difficulty, max_difficulty, optimal_difficulty, success_indicators
        ) VALUES (
            %(question_id)s, %(prerequisites)s, %(learning_objectives)s, %(assessment_criteria)s,
            %(min_difficulty)s, %(max_difficulty)s, %(optimal_difficulty)s, %(success_indicators)s
        )
        """
        
        total_loaded = 0
        total_hints = 0
        total_adaptive = 0
        
        for i in range(0, len(questions_data), batch_size):
            batch = questions_data[i:i + batch_size]
            
            try:
                for question in batch:
                    # Prepare question data
                    question_data = {
                        'original_id': question.get('id'),
                        'title': question.get('title', ''),
                        'question_en': question.get('content', {}).get('question', {}).get('en', ''),
                        'question_ko': question.get('content', {}).get('question', {}).get('ko', ''),
                        'question_zh': question.get('content', {}).get('question', {}).get('zh', ''),
                        'answer_en': question.get('content', {}).get('answer', {}).get('en', ''),
                        'answer_ko': question.get('content', {}).get('answer', {}).get('ko', ''),
                        'answer_zh': question.get('content', {}).get('answer', {}).get('zh', ''),
                        'solution_en': question.get('content', {}).get('solution', {}).get('en', ''),
                        'solution_ko': question.get('content', {}).get('solution', {}).get('ko', ''),
                        'solution_zh': question.get('content', {}).get('solution', {}).get('zh', ''),
                        'explanation_en': question.get('content', {}).get('explanation', {}).get('en', ''),
                        'explanation_ko': question.get('content', {}).get('explanation', {}).get('ko', ''),
                        'explanation_zh': question.get('content', {}).get('explanation', {}).get('zh', ''),
                        'subject': question.get('metadata', {}).get('subject', 'mathematics'),
                        'category': question.get('metadata', {}).get('category', 'STEM'),
                        'grade_level': question.get('metadata', {}).get('grade_level', 10),
                        'grade_code': question.get('metadata', {}).get('grade_code', 'G10'),
                        'education_level': question.get('metadata', {}).get('education_level', 'high_school'),
                        'difficulty_level': question.get('metadata', {}).get('difficulty', {}).get('level', 'beginner'),
                        'difficulty_score': question.get('metadata', {}).get('difficulty', {}).get('score', 1),
                        'adaptive_factor': question.get('metadata', {}).get('difficulty', {}).get('adaptive_factor', 1.0),
                        'topics': question.get('metadata', {}).get('topics', []),
                        'question_type': question.get('metadata', {}).get('question_type', 'general'),
                        'has_mathml': question.get('math_content', {}).get('has_mathml', False),
                        'latex_expressions': question.get('math_content', {}).get('latex_expressions', []),
                        'math_complexity': question.get('math_content', {}).get('math_complexity', 'low'),
                        'content_quality_score': question.get('quality_metrics', {}).get('content_quality_score', 0.0),
                        'math_accuracy_score': question.get('quality_metrics', {}).get('math_accuracy_score', 0.0),
                        'pedagogical_value_score': question.get('quality_metrics', {}).get('pedagogical_value_score', 0.0),
                        'accessibility_score': question.get('quality_metrics', {}).get('accessibility_score', 0.0),
                        'translation_status_en': question.get('translation_status', {}).get('en', 'complete'),
                        'translation_status_ko': question.get('translation_status', {}).get('ko', 'pending'),
                        'translation_status_zh': question.get('translation_status', {}).get('zh', 'pending'),
                        'source': question.get('metadata', {}).get('source', 'mpcstudy.com'),
                        'version': question.get('version', '1.0')
                    }
                    
                    # Insert question
                    self.cursor.execute(insert_query, question_data)
                    question_id = self.cursor.fetchone()['id']
                    total_loaded += 1
                    
                    # Insert hints
                    hints = question.get('content', {}).get('hints', {}).get('en', [])
                    for idx, hint in enumerate(hints):
                        if hint and hint.strip():
                            hint_data = {
                                'question_id': question_id,
                                'hint_text_en': hint,
                                'hint_text_ko': '',
                                'hint_text_zh': '',
                                'hint_order': idx + 1
                            }
                            self.cursor.execute(hint_insert_query, hint_data)
                            total_hints += 1
                    
                    # Insert adaptive learning metadata
                    adaptive_data = question.get('adaptive_learning', {})
                    if adaptive_data:
                        adaptive_metadata = {
                            'question_id': question_id,
                            'prerequisites': adaptive_data.get('prerequisites', []),
                            'learning_objectives': adaptive_data.get('learning_objectives', []),
                            'assessment_criteria': adaptive_data.get('assessment_criteria', []),
                            'min_difficulty': adaptive_data.get('adaptive_difficulty_range', {}).get('min_difficulty', 1),
                            'max_difficulty': adaptive_data.get('adaptive_difficulty_range', {}).get('max_difficulty', 10),
                            'optimal_difficulty': adaptive_data.get('adaptive_difficulty_range', {}).get('optimal_difficulty', 5),
                            'success_indicators': adaptive_data.get('success_indicators', [])
                        }
                        self.cursor.execute(adaptive_insert_query, adaptive_metadata)
                        total_adaptive += 1
                
                # Commit batch
                self.connection.commit()
                logger.info(f"Loaded batch {i//batch_size + 1}: {len(batch)} questions")
                
            except Exception as e:
                logger.error(f"Error loading batch {i//batch_size + 1}: {e}")
                self.connection.rollback()
                raise
        
        logger.info(f"Successfully loaded {total_loaded} questions, {total_hints} hints, {total_adaptive} adaptive metadata records")
        return total_loaded, total_hints, total_adaptive
    
    def create_indexes(self):
        """Create additional indexes for performance"""
        indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_original_id ON questions(original_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_created_at ON questions(created_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_quality_composite ON questions(content_quality_score, math_accuracy_score, pedagogical_value_score);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_difficulty_range ON questions(difficulty_score, adaptive_factor);"
        ]
        
        for index_sql in indexes:
            try:
                self.cursor.execute(index_sql)
                self.connection.commit()
                logger.info(f"Created index: {index_sql.split()[5]}")
            except Exception as e:
                logger.warning(f"Index creation failed (may already exist): {e}")
    
    def validate_data(self) -> Dict[str, Any]:
        """
        Validate loaded data and return statistics
        
        Returns:
            Dictionary with validation statistics
        """
        validation_queries = {
            'total_questions': "SELECT COUNT(*) as count FROM questions;",
            'questions_by_subject': "SELECT subject, COUNT(*) as count FROM questions GROUP BY subject;",
            'questions_by_grade': "SELECT grade_level, COUNT(*) as count FROM questions GROUP BY grade_level ORDER BY grade_level;",
            'questions_by_difficulty': "SELECT difficulty_level, COUNT(*) as count FROM questions GROUP BY difficulty_level;",
            'mathml_questions': "SELECT COUNT(*) as count FROM questions WHERE has_mathml = TRUE;",
            'translation_status': "SELECT translation_status_ko, translation_status_zh, COUNT(*) as count FROM questions GROUP BY translation_status_ko, translation_status_zh;",
            'quality_distribution': """
                SELECT 
                    CASE 
                        WHEN content_quality_score >= 0.8 THEN 'high'
                        WHEN content_quality_score >= 0.5 THEN 'medium'
                        ELSE 'low'
                    END as quality_level,
                    COUNT(*) as count
                FROM questions 
                GROUP BY quality_level;
            """,
            'topics_distribution': """
                SELECT 
                    unnest(topics) as topic,
                    COUNT(*) as count
                FROM questions 
                GROUP BY topic 
                ORDER BY count DESC 
                LIMIT 20;
            """
        }
        
        results = {}
        
        for name, query in validation_queries.items():
            try:
                self.cursor.execute(query)
                if name in ['questions_by_subject', 'questions_by_grade', 'questions_by_difficulty', 
                           'translation_status', 'quality_distribution', 'topics_distribution']:
                    results[name] = [dict(row) for row in self.cursor.fetchall()]
                else:
                    results[name] = self.cursor.fetchone()['count']
            except Exception as e:
                logger.error(f"Validation query failed for {name}: {e}")
                results[name] = None
        
        return results
    
    def generate_loading_report(self, validation_results: Dict[str, Any], 
                              total_loaded: int, total_hints: int, total_adaptive: int) -> str:
        """
        Generate a comprehensive loading report
        
        Args:
            validation_results: Results from validate_data()
            total_loaded: Number of questions loaded
            total_hints: Number of hints loaded
            total_adaptive: Number of adaptive metadata records loaded
            
        Returns:
            Formatted report string
        """
        report = f"""
DreamSeedAI Data Loading Report
{'=' * 50}

Loading Summary:
- Questions Loaded: {total_loaded:,}
- Hints Loaded: {total_hints:,}
- Adaptive Learning Metadata: {total_adaptive:,}
- Loading Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Database Validation Results:
- Total Questions in DB: {validation_results.get('total_questions', 'N/A'):,}
- MathML Questions: {validation_results.get('mathml_questions', 'N/A'):,}

Subject Distribution:
"""
        
        if validation_results.get('questions_by_subject'):
            for subject in validation_results['questions_by_subject']:
                report += f"  - {subject['subject']}: {subject['count']:,}\n"
        
        report += "\nGrade Level Distribution:\n"
        if validation_results.get('questions_by_grade'):
            for grade in validation_results['questions_by_grade']:
                report += f"  - Grade {grade['grade_level']}: {grade['count']:,}\n"
        
        report += "\nDifficulty Distribution:\n"
        if validation_results.get('questions_by_difficulty'):
            for difficulty in validation_results['questions_by_difficulty']:
                report += f"  - {difficulty['difficulty_level']}: {difficulty['count']:,}\n"
        
        report += "\nTranslation Status:\n"
        if validation_results.get('translation_status'):
            for status in validation_results['translation_status']:
                report += f"  - KO: {status['translation_status_ko']}, ZH: {status['translation_status_zh']} - {status['count']:,}\n"
        
        report += "\nQuality Distribution:\n"
        if validation_results.get('quality_distribution'):
            for quality in validation_results['quality_distribution']:
                report += f"  - {quality['quality_level']}: {quality['count']:,}\n"
        
        report += "\nTop Topics:\n"
        if validation_results.get('topics_distribution'):
            for topic in validation_results['topics_distribution'][:10]:
                report += f"  - {topic['topic']}: {topic['count']:,}\n"
        
        return report

def main():
    """
    Main function to load data into DreamSeedAI database
    """
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'dreamseedai'),
        'user': os.getenv('DB_USER', 'dreamseedai'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }
    
    # Load questions data
    questions_file = 'enhanced_migrated_data/enhanced_dreamseed_questions.json'
    
    if not os.path.exists(questions_file):
        logger.error(f"Questions file not found: {questions_file}")
        return
    
    logger.info("Loading questions data...")
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    # Initialize data loader
    loader = DreamSeedAIDataLoader(db_config)
    
    try:
        # Connect to database
        loader.connect()
        
        # Create schema (uncomment if needed)
        # loader.create_schema('database_schema.sql')
        
        # Load questions
        total_loaded, total_hints, total_adaptive = loader.load_questions(questions_data)
        
        # Create additional indexes
        loader.create_indexes()
        
        # Validate data
        validation_results = loader.validate_data()
        
        # Generate and save report
        report = loader.generate_loading_report(validation_results, total_loaded, total_hints, total_adaptive)
        
        with open('data_loading_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        logger.info("Data loading completed successfully!")
        
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise
    finally:
        loader.disconnect()

if __name__ == '__main__':
    main()
