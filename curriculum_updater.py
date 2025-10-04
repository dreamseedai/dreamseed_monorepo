#!/usr/bin/env python3
"""
DreamSeedAI Curriculum Updater
Updates database with curriculum classification results
"""

import json
import os
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CurriculumUpdater:
    """
    Updates database with curriculum classification results
    """
    
    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize updater with database configuration
        
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
    
    def apply_schema_updates(self, schema_file: str):
        """
        Apply curriculum schema updates
        
        Args:
            schema_file: Path to SQL schema update file
        """
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            self.cursor.execute(schema_sql)
            self.connection.commit()
            logger.info("Curriculum schema updates applied successfully")
        except Exception as e:
            logger.error(f"Failed to apply schema updates: {e}")
            self.connection.rollback()
            raise
    
    def update_question_curriculum(self, classification_results: List[Dict[str, Any]]):
        """
        Update questions with curriculum classification results
        
        Args:
            classification_results: List of classification results from GPT
        """
        logger.info(f"Updating {len(classification_results)} questions with curriculum classifications...")
        
        update_query = """
        UPDATE questions SET
            us_curriculum_grade = %(us_grade)s,
            us_curriculum_subject = %(us_subject)s,
            us_curriculum_course = %(us_course)s,
            us_curriculum_topic = %(us_topic)s,
            us_curriculum_confidence = %(us_confidence)s,
            us_curriculum_difficulty = %(us_difficulty)s,
            us_curriculum_alignment = %(us_alignment)s,
            canada_curriculum_grade = %(canada_grade)s,
            canada_curriculum_subject = %(canada_subject)s,
            canada_curriculum_course = %(canada_course)s,
            canada_curriculum_topic = %(canada_topic)s,
            canada_curriculum_confidence = %(canada_confidence)s,
            canada_curriculum_difficulty = %(canada_difficulty)s,
            canada_curriculum_alignment = %(canada_alignment)s,
            curriculum_classification_notes = %(notes)s
        WHERE original_id = %(original_id)s
        """
        
        insert_mapping_query = """
        INSERT INTO curriculum_mappings (
            question_id, country, subject, grade, course, topic,
            confidence_score, difficulty_level, alignment_score, classification_reasoning
        ) VALUES (
            (SELECT id FROM questions WHERE original_id = %(original_id)s),
            %(country)s, %(subject)s, %(grade)s, %(course)s, %(topic)s,
            %(confidence)s, %(difficulty)s, %(alignment)s, %(reasoning)s
        ) ON CONFLICT (question_id, country) DO UPDATE SET
            subject = EXCLUDED.subject,
            grade = EXCLUDED.grade,
            course = EXCLUDED.course,
            topic = EXCLUDED.topic,
            confidence_score = EXCLUDED.confidence_score,
            difficulty_level = EXCLUDED.difficulty_level,
            alignment_score = EXCLUDED.alignment_score,
            classification_reasoning = EXCLUDED.classification_reasoning
        """
        
        updated_count = 0
        mapping_count = 0
        
        for result in classification_results:
            if 'error' in result:
                logger.warning(f"Skipping result with error: {result.get('error')}")
                continue
            
            original_id = result.get('original_question_id')
            if not original_id:
                logger.warning("No original_question_id found in result")
                continue
            
            try:
                # Update main questions table
                update_data = {
                    'original_id': original_id,
                    'us_grade': None,
                    'us_subject': None,
                    'us_course': None,
                    'us_topic': None,
                    'us_confidence': None,
                    'us_difficulty': None,
                    'us_alignment': None,
                    'canada_grade': None,
                    'canada_subject': None,
                    'canada_course': None,
                    'canada_topic': None,
                    'canada_confidence': None,
                    'canada_difficulty': None,
                    'canada_alignment': None,
                    'notes': result.get('reasoning', '')
                }
                
                # US Classification
                if result.get('us_classification'):
                    us_class = result['us_classification']
                    update_data.update({
                        'us_grade': us_class.get('grade'),
                        'us_subject': us_class.get('subject'),
                        'us_course': us_class.get('course'),
                        'us_topic': us_class.get('topic'),
                        'us_confidence': us_class.get('confidence'),
                        'us_difficulty': result.get('difficulty_assessment', {}).get('us_difficulty'),
                        'us_alignment': result.get('curriculum_alignment', {}).get('us_alignment')
                    })
                
                # Canada Classification
                if result.get('canada_classification'):
                    canada_class = result['canada_classification']
                    update_data.update({
                        'canada_grade': canada_class.get('grade'),
                        'canada_subject': canada_class.get('subject'),
                        'canada_course': canada_class.get('course'),
                        'canada_topic': canada_class.get('topic'),
                        'canada_confidence': canada_class.get('confidence'),
                        'canada_difficulty': result.get('difficulty_assessment', {}).get('canada_difficulty'),
                        'canada_alignment': result.get('curriculum_alignment', {}).get('canada_alignment')
                    })
                
                self.cursor.execute(update_query, update_data)
                updated_count += 1
                
                # Insert detailed mappings
                if result.get('us_classification'):
                    us_class = result['us_classification']
                    mapping_data = {
                        'original_id': original_id,
                        'country': 'US',
                        'subject': us_class.get('subject'),
                        'grade': us_class.get('grade'),
                        'course': us_class.get('course'),
                        'topic': us_class.get('topic'),
                        'confidence': us_class.get('confidence'),
                        'difficulty': result.get('difficulty_assessment', {}).get('us_difficulty'),
                        'alignment': result.get('curriculum_alignment', {}).get('us_alignment'),
                        'reasoning': result.get('reasoning', '')
                    }
                    self.cursor.execute(insert_mapping_query, mapping_data)
                    mapping_count += 1
                
                if result.get('canada_classification'):
                    canada_class = result['canada_classification']
                    mapping_data = {
                        'original_id': original_id,
                        'country': 'Canada',
                        'subject': canada_class.get('subject'),
                        'grade': canada_class.get('grade'),
                        'course': canada_class.get('course'),
                        'topic': canada_class.get('topic'),
                        'confidence': canada_class.get('confidence'),
                        'difficulty': result.get('difficulty_assessment', {}).get('canada_difficulty'),
                        'alignment': result.get('curriculum_alignment', {}).get('canada_alignment'),
                        'reasoning': result.get('reasoning', '')
                    }
                    self.cursor.execute(insert_mapping_query, mapping_data)
                    mapping_count += 1
                
            except Exception as e:
                logger.error(f"Error updating question {original_id}: {e}")
                self.connection.rollback()
                raise
        
        self.connection.commit()
        logger.info(f"Successfully updated {updated_count} questions and {mapping_count} curriculum mappings")
        
        return updated_count, mapping_count
    
    def validate_curriculum_updates(self) -> Dict[str, Any]:
        """
        Validate curriculum updates and return statistics
        
        Returns:
            Validation statistics
        """
        validation_queries = {
            'total_questions_with_us_curriculum': """
                SELECT COUNT(*) as count 
                FROM questions 
                WHERE us_curriculum_grade IS NOT NULL
            """,
            'total_questions_with_canada_curriculum': """
                SELECT COUNT(*) as count 
                FROM questions 
                WHERE canada_curriculum_grade IS NOT NULL
            """,
            'us_curriculum_distribution': """
                SELECT 
                    us_curriculum_grade as grade,
                    us_curriculum_subject as subject,
                    COUNT(*) as count
                FROM questions 
                WHERE us_curriculum_grade IS NOT NULL
                GROUP BY us_curriculum_grade, us_curriculum_subject
                ORDER BY grade, subject
            """,
            'canada_curriculum_distribution': """
                SELECT 
                    canada_curriculum_grade as grade,
                    canada_curriculum_subject as subject,
                    COUNT(*) as count
                FROM questions 
                WHERE canada_curriculum_grade IS NOT NULL
                GROUP BY canada_curriculum_grade, canada_curriculum_subject
                ORDER BY grade, subject
            """,
            'confidence_distribution': """
                SELECT 
                    CASE 
                        WHEN us_curriculum_confidence >= 0.9 THEN 'high'
                        WHEN us_curriculum_confidence >= 0.7 THEN 'medium'
                        WHEN us_curriculum_confidence >= 0.5 THEN 'low'
                        ELSE 'very_low'
                    END as confidence_level,
                    COUNT(*) as count
                FROM questions 
                WHERE us_curriculum_confidence IS NOT NULL
                GROUP BY confidence_level
                ORDER BY confidence_level
            """,
            'curriculum_mappings_count': """
                SELECT 
                    country,
                    COUNT(*) as count
                FROM curriculum_mappings
                GROUP BY country
            """,
            'curriculum_standards_count': """
                SELECT 
                    country,
                    subject,
                    COUNT(*) as count
                FROM curriculum_standards
                GROUP BY country, subject
                ORDER BY country, subject
            """
        }
        
        results = {}
        
        for name, query in validation_queries.items():
            try:
                self.cursor.execute(query)
                if name in ['us_curriculum_distribution', 'canada_curriculum_distribution', 
                           'confidence_distribution', 'curriculum_mappings_count', 'curriculum_standards_count']:
                    results[name] = [dict(row) for row in self.cursor.fetchall()]
                else:
                    results[name] = self.cursor.fetchone()['count']
            except Exception as e:
                logger.error(f"Validation query failed for {name}: {e}")
                results[name] = None
        
        return results
    
    def generate_curriculum_report(self, validation_results: Dict[str, Any], 
                                 updated_count: int, mapping_count: int) -> str:
        """
        Generate comprehensive curriculum update report
        
        Args:
            validation_results: Results from validate_curriculum_updates()
            updated_count: Number of questions updated
            mapping_count: Number of curriculum mappings created
            
        Returns:
            Formatted report string
        """
        report = f"""
DreamSeedAI Curriculum Classification Update Report
{'=' * 60}

Update Summary:
- Questions Updated: {updated_count:,}
- Curriculum Mappings Created: {mapping_count:,}
- Update Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Database Validation Results:
- Questions with US Curriculum: {validation_results.get('total_questions_with_us_curriculum', 'N/A'):,}
- Questions with Canada Curriculum: {validation_results.get('total_questions_with_canada_curriculum', 'N/A'):,}

US Curriculum Distribution:
"""
        
        if validation_results.get('us_curriculum_distribution'):
            for item in validation_results['us_curriculum_distribution']:
                report += f"  - {item['grade']} {item['subject']}: {item['count']:,}\n"
        
        report += "\nCanada Curriculum Distribution:\n"
        if validation_results.get('canada_curriculum_distribution'):
            for item in validation_results['canada_curriculum_distribution']:
                report += f"  - {item['grade']} {item['subject']}: {item['count']:,}\n"
        
        report += "\nConfidence Distribution:\n"
        if validation_results.get('confidence_distribution'):
            for item in validation_results['confidence_distribution']:
                report += f"  - {item['confidence_level']}: {item['count']:,}\n"
        
        report += "\nCurriculum Mappings:\n"
        if validation_results.get('curriculum_mappings_count'):
            for item in validation_results['curriculum_mappings_count']:
                report += f"  - {item['country']}: {item['count']:,}\n"
        
        report += "\nCurriculum Standards:\n"
        if validation_results.get('curriculum_standards_count'):
            for item in validation_results['curriculum_standards_count']:
                report += f"  - {item['country']} {item['subject']}: {item['count']:,}\n"
        
        return report
    
    def create_curriculum_recommendations(self, student_id: str, country: str, 
                                        subject: str, grade: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Create curriculum-based question recommendations for a student
        
        Args:
            student_id: Student ID
            country: 'US' or 'Canada'
            subject: Subject name
            grade: Grade level
            limit: Number of recommendations
            
        Returns:
            List of recommended questions
        """
        try:
            query = """
                SELECT * FROM get_curriculum_questions(
                    %(country)s, %(subject)s, %(grade)s, NULL, NULL, %(limit)s
                )
            """
            
            self.cursor.execute(query, {
                'country': country,
                'subject': subject,
                'grade': grade,
                'limit': limit
            })
            
            recommendations = [dict(row) for row in self.cursor.fetchall()]
            
            # Store recommendations in database
            if recommendations:
                insert_query = """
                    INSERT INTO curriculum_recommendations (
                        student_id, country, subject, grade, recommended_questions,
                        recommendation_score, expires_at
                    ) VALUES (
                        %(student_id)s, %(country)s, %(subject)s, %(grade)s,
                        %(questions)s, %(score)s, NOW() + INTERVAL '7 days'
                    )
                """
                
                question_ids = [str(rec['question_id']) for rec in recommendations]
                avg_confidence = sum(rec['confidence'] for rec in recommendations) / len(recommendations)
                
                self.cursor.execute(insert_query, {
                    'student_id': student_id,
                    'country': country,
                    'subject': subject,
                    'grade': grade,
                    'questions': question_ids,
                    'score': avg_confidence
                })
                
                self.connection.commit()
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error creating curriculum recommendations: {e}")
            return []

def main():
    """
    Main function to update curriculum classifications
    """
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'dreamseedai'),
        'user': os.getenv('DB_USER', 'dreamseedai'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }
    
    # Load classification results
    classification_file = 'curriculum_classification_results_20241001_203000.json'  # Update with actual filename
    
    if not os.path.exists(classification_file):
        logger.error(f"Classification results file not found: {classification_file}")
        return
    
    logger.info("Loading classification results...")
    with open(classification_file, 'r', encoding='utf-8') as f:
        classification_results = json.load(f)
    
    # Initialize updater
    updater = CurriculumUpdater(db_config)
    
    try:
        # Connect to database
        updater.connect()
        
        # Apply schema updates
        updater.apply_schema_updates('curriculum_schema_update.sql')
        
        # Update questions with curriculum classifications
        updated_count, mapping_count = updater.update_question_curriculum(classification_results)
        
        # Validate updates
        validation_results = updater.validate_curriculum_updates()
        
        # Generate and save report
        report = updater.generate_curriculum_report(validation_results, updated_count, mapping_count)
        
        with open('curriculum_update_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        logger.info("Curriculum update completed successfully!")
        
    except Exception as e:
        logger.error(f"Curriculum update failed: {e}")
        raise
    finally:
        updater.disconnect()

if __name__ == '__main__':
    main()
