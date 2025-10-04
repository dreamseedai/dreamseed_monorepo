#!/usr/bin/env python3
"""
Robust Data Extractor for DreamSeedAI
=====================================

This script provides a more robust parser for extracting problem data
from the mpcstudy.com MySQL dump file, handling complex data formats.
"""

import re
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProblemData:
    """Structure for problem data"""
    que_id: int
    que_status: int
    que_class: str
    que_category1: int
    que_category2: int
    que_category3: int
    que_grade: str
    que_level: int
    que_en_title: str
    que_en_desc: str
    que_en_hint: str
    que_en_solution: str
    que_en_answers: str
    que_en_answerm: str
    que_answertype: int
    que_en_example: str
    que_en_resource: str
    que_createddate: str
    que_modifieddate: str

class RobustMySQLDumpParser:
    """Robust MySQL dump parser for problem data extraction"""
    
    def __init__(self, dump_file_path: str):
        self.dump_file_path = dump_file_path
        self.problems = []
    
    def extract_problems(self) -> List[ProblemData]:
        """Extract problem data from MySQL dump with robust parsing"""
        logger.info(f"Parsing MySQL dump: {self.dump_file_path}")
        
        try:
            with open(self.dump_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find all INSERT statements for tbl_question
            insert_pattern = r'INSERT INTO.*?`tbl_question`.*?VALUES\s*((?:\([^)]+\),?\s*)+);'
            matches = re.findall(insert_pattern, content, re.DOTALL | re.IGNORECASE)
            
            logger.info(f"Found {len(matches)} INSERT statement groups")
            
            total_parsed = 0
            for i, match in enumerate(matches):
                try:
                    # Split by ),( to get individual rows
                    rows = re.split(r'\),\s*\(', match)
                    
                    for row in rows:
                        try:
                            # Clean up the row
                            row = row.strip()
                            if row.startswith('('):
                                row = row[1:]
                            if row.endswith(')'):
                                row = row[:-1]
                            if row:
                                problem = self._parse_single_row(row)
                                if problem:
                                    self.problems.append(problem)
                                    total_parsed += 1
                                    
                                    if total_parsed % 100 == 0:
                                        logger.info(f"Parsed {total_parsed} problems...")
                                        
                        except Exception as e:
                            logger.debug(f"Failed to parse row: {e}")
                            continue
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(matches)} INSERT statement groups")
                        
                except Exception as e:
                    logger.warning(f"Failed to process INSERT statement group {i}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(self.problems)} problems")
            return self.problems
            
        except Exception as e:
            logger.error(f"Failed to extract problems: {e}")
            return []
    
    def _parse_single_row(self, row: str) -> Optional[ProblemData]:
        """Parse a single row with robust error handling"""
        try:
            # Use a more sophisticated parsing approach
            values = self._parse_values_advanced(row)
            
            if len(values) < 19:  # Need at least 19 fields
                return None
            
            # Safely convert values with defaults
            problem_data = ProblemData(
                que_id=self._safe_int(values[0], 0),
                que_status=self._safe_int(values[1], 1),
                que_class=self._safe_str(values[2], 'M'),
                que_category1=self._safe_int(values[3], 0),
                que_category2=self._safe_int(values[4], 0),
                que_category3=self._safe_int(values[5], 0),
                que_grade=self._safe_str(values[6], 'G10'),
                que_level=self._safe_int(values[7], 1),
                que_en_title=self._safe_str(values[8], ''),
                que_en_desc=self._safe_str(values[9], ''),
                que_en_hint=self._safe_str(values[10], ''),
                que_en_solution=self._safe_str(values[11], ''),
                que_en_answers=self._safe_str(values[12], ''),
                que_en_answerm=self._safe_str(values[13], ''),
                que_answertype=self._safe_int(values[14], 0),
                que_en_example=self._safe_str(values[15], ''),
                que_en_resource=self._safe_str(values[16], ''),
                que_createddate=self._safe_str(values[17], ''),
                que_modifieddate=self._safe_str(values[18], ''),
            )
            
            return problem_data
            
        except Exception as e:
            logger.debug(f"Failed to parse row: {e}")
            return None
    
    def _parse_values_advanced(self, values_string: str) -> List[str]:
        """Advanced parsing of VALUES string with better handling of complex data"""
        values = []
        current_value = ""
        in_quotes = False
        quote_char = None
        paren_count = 0
        i = 0
        
        while i < len(values_string):
            char = values_string[i]
            
            if char in ["'", '"'] and not in_quotes:
                # Start of quoted string
                in_quotes = True
                quote_char = char
                current_value += char
            elif char == quote_char and in_quotes:
                # Check if it's escaped
                if i > 0 and values_string[i-1] == '\\':
                    current_value += char
                else:
                    # End of quoted string
                    in_quotes = False
                    quote_char = None
                    current_value += char
            elif char == '(' and not in_quotes:
                paren_count += 1
                current_value += char
            elif char == ')' and not in_quotes:
                paren_count -= 1
                current_value += char
            elif char == ',' and not in_quotes and paren_count == 0:
                # End of value
                values.append(current_value.strip())
                current_value = ""
            else:
                current_value += char
            
            i += 1
        
        # Add the last value
        if current_value.strip():
            values.append(current_value.strip())
        
        return values
    
    def _safe_int(self, value: str, default: int = 0) -> int:
        """Safely convert string to int with default"""
        if not value or value == 'NULL' or value == '':
            return default
        try:
            # Remove quotes if present
            clean_value = value.strip("'\"")
            return int(clean_value)
        except (ValueError, TypeError):
            return default
    
    def _safe_str(self, value: str, default: str = '') -> str:
        """Safely convert string with default"""
        if not value or value == 'NULL':
            return default
        try:
            # Remove quotes if present
            clean_value = value.strip("'\"")
            # Decode HTML entities
            clean_value = clean_value.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            return clean_value
        except (ValueError, TypeError):
            return default
    
    def save_to_csv(self, output_file: str):
        """Save extracted problems to CSV file"""
        if not self.problems:
            logger.warning("No problems to save")
            return
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'que_id', 'que_status', 'que_class', 'que_category1', 'que_category2', 'que_category3',
                    'que_grade', 'que_level', 'que_en_title', 'que_en_desc', 'que_en_hint', 'que_en_solution',
                    'que_en_answers', 'que_en_answerm', 'que_answertype', 'que_en_example', 'que_en_resource',
                    'que_createddate', 'que_modifieddate'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for problem in self.problems:
                    writer.writerow({
                        'que_id': problem.que_id,
                        'que_status': problem.que_status,
                        'que_class': problem.que_class,
                        'que_category1': problem.que_category1,
                        'que_category2': problem.que_category2,
                        'que_category3': problem.que_category3,
                        'que_grade': problem.que_grade,
                        'que_level': problem.que_level,
                        'que_en_title': problem.que_en_title,
                        'que_en_desc': problem.que_en_desc,
                        'que_en_hint': problem.que_en_hint,
                        'que_en_solution': problem.que_en_solution,
                        'que_en_answers': problem.que_en_answers,
                        'que_en_answerm': problem.que_en_answerm,
                        'que_answertype': problem.que_answertype,
                        'que_en_example': problem.que_en_example,
                        'que_en_resource': problem.que_en_resource,
                        'que_createddate': problem.que_createddate,
                        'que_modifieddate': problem.que_modifieddate,
                    })
            
            logger.info(f"Saved {len(self.problems)} problems to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save to CSV: {e}")
    
    def load_to_database(self, db_config: Dict):
        """Load extracted problems directly to PostgreSQL database"""
        try:
            # Connect to database
            conn = psycopg2.connect(**db_config)
            conn.autocommit = False
            cursor = conn.cursor()
            
            # Create questions_enhanced table
            self._create_questions_enhanced_table(cursor)
            
            # Insert problems in batches
            batch_size = 100
            for i in range(0, len(self.problems), batch_size):
                batch = self.problems[i:i + batch_size]
                self._insert_problem_batch(cursor, batch)
                logger.info(f"Inserted batch {i//batch_size + 1}/{(len(self.problems)-1)//batch_size + 1}")
            
            conn.commit()
            logger.info(f"Successfully loaded {len(self.problems)} problems into database")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to load to database: {e}")
            raise
    
    def _create_questions_enhanced_table(self, cursor):
        """Create the enhanced questions table"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS questions_enhanced (
            id SERIAL PRIMARY KEY,
            que_id INTEGER,
            que_class CHAR(1),
            que_grade VARCHAR(3),
            que_level INTEGER,
            que_en_title TEXT,
            que_en_desc TEXT,
            que_en_hint TEXT,
            que_en_solution TEXT,
            que_en_answers TEXT,
            que_en_answerm CHAR(1),
            que_answertype INTEGER,
            que_category1 INTEGER,
            que_category2 INTEGER,
            que_category3 INTEGER,
            que_en_example TEXT,
            que_en_resource TEXT,
            que_createddate VARCHAR(14),
            que_modifieddate VARCHAR(14),
            que_status INTEGER DEFAULT 1,
            -- Enhanced fields for DreamSeedAI
            que_ko_title TEXT,
            que_ko_desc TEXT,
            que_ko_hint TEXT,
            que_ko_solution TEXT,
            que_ko_answers TEXT,
            que_zh_title TEXT,
            que_zh_desc TEXT,
            que_zh_hint TEXT,
            que_zh_solution TEXT,
            que_zh_answers TEXT,
            que_answer_basic TEXT,
            que_answer_standard TEXT,
            que_answer_deep TEXT,
            que_difficulty_score FLOAT,
            que_avg_time_sec INTEGER,
            que_correct_rate FLOAT,
            que_last_reviewed TIMESTAMP,
            que_review_count INTEGER DEFAULT 0,
            que_ai_generated_hint TEXT,
            que_ai_generated_solution TEXT,
            que_ai_generated_deep_solution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_que_id ON questions_enhanced(que_id);
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_grade ON questions_enhanced(que_grade);
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_level ON questions_enhanced(que_level);
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_category ON questions_enhanced(que_category1, que_category2, que_category3);
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_difficulty ON questions_enhanced(que_difficulty_score);
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_status ON questions_enhanced(que_status);
        """
        
        cursor.execute(create_table_sql)
        logger.info("Created questions_enhanced table with indexes")
    
    def _insert_problem_batch(self, cursor, problems: List[ProblemData]):
        """Insert a batch of problems"""
        insert_sql = """
        INSERT INTO questions_enhanced (
            que_id, que_class, que_grade, que_level, que_en_title, que_en_desc, que_en_hint,
            que_en_solution, que_en_answers, que_en_answerm, que_answertype,
            que_category1, que_category2, que_category3, que_en_example, que_en_resource,
            que_createddate, que_modifieddate, que_status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        for problem in problems:
            cursor.execute(insert_sql, (
                problem.que_id, problem.que_status, problem.que_class, problem.que_grade, problem.que_level,
                problem.que_en_title, problem.que_en_desc, problem.que_en_hint, problem.que_en_solution,
                problem.que_en_answers, problem.que_en_answerm, problem.que_answertype, problem.que_category1,
                problem.que_category2, problem.que_category3, problem.que_en_example, problem.que_en_resource,
                problem.que_createddate, problem.que_modifieddate
            ))
    
    def get_sample_problems(self, count: int = 5) -> List[ProblemData]:
        """Get a sample of problems for inspection"""
        return self.problems[:count] if self.problems else []

def main():
    """Main function to test the parser"""
    dump_file_path = '/var/www/mpcstudy.com/mpcstudy_db.sql'
    
    parser = RobustMySQLDumpParser(dump_file_path)
    problems = parser.extract_problems()
    
    if problems:
        logger.info(f"Extracted {len(problems)} problems")
        
        # Show sample problems
        samples = parser.get_sample_problems(3)
        for i, problem in enumerate(samples):
            logger.info(f"Sample problem {i+1}:")
            logger.info(f"  ID: {problem.que_id}")
            logger.info(f"  Title: {problem.que_en_title[:100]}...")
            logger.info(f"  Grade: {problem.que_grade}")
            logger.info(f"  Level: {problem.que_level}")
            logger.info(f"  Class: {problem.que_class}")
            logger.info("---")
        
        # Save to CSV for inspection
        parser.save_to_csv('/tmp/mpcstudy_problems_robust.csv')
        
        # Load to database
        db_config = {
            'host': '127.0.0.1',
            'port': 5432,
            'database': 'dreamseed',
            'user': 'postgres',
            'password': 'DreamSeedAi@0908'
        }
        
        logger.info("Loading problems to database...")
        parser.load_to_database(db_config)
        
    else:
        logger.warning("No problems extracted")

if __name__ == "__main__":
    main()
