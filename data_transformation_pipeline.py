#!/usr/bin/env python3
"""
DreamSeedAI Data Transformation Pipeline
========================================

This script transforms mpcstudy.com problem data into DreamSeedAI's personalized learning format.
It handles:
1. Schema mapping and standardization
2. MathML to LaTeX conversion for TipTap + MathLive
3. AI-powered content enhancement
4. Multilingual support preparation
5. ETL pipeline for data loading

Author: DreamSeedAI Team
Date: 2024
"""

import re
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProblemData:
    """Structure for transformed problem data"""
    que_id: int
    que_class: str
    que_grade: str
    que_level: int
    que_en_title: str
    que_en_desc: str
    que_en_hint: str
    que_en_solution: str
    que_en_answers: str
    que_en_answerm: str
    que_answertype: int
    que_category1: int
    que_category2: int
    que_category3: int
    que_en_example: str
    que_en_resource: str
    que_createddate: str
    que_modifieddate: str
    que_status: int
    # Enhanced fields for DreamSeedAI
    que_ko_title: Optional[str] = None
    que_ko_desc: Optional[str] = None
    que_ko_hint: Optional[str] = None
    que_ko_solution: Optional[str] = None
    que_ko_answers: Optional[str] = None
    que_zh_title: Optional[str] = None
    que_zh_desc: Optional[str] = None
    que_zh_hint: Optional[str] = None
    que_zh_solution: Optional[str] = None
    que_zh_answers: Optional[str] = None
    que_answer_basic: Optional[str] = None
    que_answer_standard: Optional[str] = None
    que_answer_deep: Optional[str] = None
    que_difficulty_score: Optional[float] = None
    que_avg_time_sec: Optional[int] = None
    que_correct_rate: Optional[float] = None
    que_ai_generated_hint: Optional[str] = None
    que_ai_generated_solution: Optional[str] = None
    que_ai_generated_deep_solution: Optional[str] = None

class MathMLConverter:
    """Converts MathML to LaTeX for TipTap + MathLive integration"""
    
    def __init__(self):
        self.mathml_to_latex_map = {
            # Basic elements
            'mi': lambda elem: elem.text or '',
            'mn': lambda elem: elem.text or '',
            'mo': lambda elem: elem.text or '',
            'mtext': lambda elem: elem.text or '',
            'mspace': lambda elem: ' ',
            
            # Fractions
            'mfrac': self._convert_fraction,
            'mover': self._convert_over,
            'munder': self._convert_under,
            'munderover': self._convert_underover,
            
            # Superscripts and subscripts
            'msup': self._convert_superscript,
            'msub': self._convert_subscript,
            'msubsup': self._convert_subsup,
            
            # Roots and radicals
            'msqrt': self._convert_sqrt,
            'mroot': self._convert_root,
            
            # Limits and integrals
            'munder': self._convert_under,
            'mover': self._convert_over,
            
            # Matrices and tables
            'mtable': self._convert_table,
            'mtr': self._convert_table_row,
            'mtd': self._convert_table_cell,
            
            # Fences and delimiters
            'mfenced': self._convert_fenced,
            'menclose': self._convert_enclose,
            
            # Operators
            'munderover': self._convert_underover,
        }
    
    def convert_mathml_to_latex(self, mathml_content: str) -> str:
        """Convert MathML content to LaTeX format"""
        if not mathml_content or '<math' not in mathml_content:
            return mathml_content
            
        try:
            # Extract MathML content
            mathml_match = re.search(r'<math[^>]*>(.*?)</math>', mathml_content, re.DOTALL)
            if not mathml_match:
                return mathml_content
                
            mathml_xml = f"<root>{mathml_match.group(1)}</root>"
            root = ET.fromstring(mathml_xml)
            
            latex = self._convert_element(root)
            return latex.strip()
            
        except ET.ParseError as e:
            logger.warning(f"Failed to parse MathML: {e}")
            return mathml_content
        except Exception as e:
            logger.error(f"Error converting MathML to LaTeX: {e}")
            return mathml_content
    
    def _convert_element(self, element) -> str:
        """Convert a MathML element to LaTeX"""
        tag = element.tag
        
        if tag in self.mathml_to_latex_map:
            return self.mathml_to_latex_map[tag](element)
        elif element.text:
            return element.text
        else:
            # Recursively convert children
            children_latex = ''.join(self._convert_element(child) for child in element)
            return children_latex
    
    def _convert_fraction(self, element) -> str:
        """Convert mfrac to LaTeX fraction"""
        children = list(element)
        if len(children) >= 2:
            numerator = self._convert_element(children[0])
            denominator = self._convert_element(children[1])
            return f"\\frac{{{numerator}}}{{{denominator}}}"
        return ""
    
    def _convert_superscript(self, element) -> str:
        """Convert msup to LaTeX superscript"""
        children = list(element)
        if len(children) >= 2:
            base = self._convert_element(children[0])
            sup = self._convert_element(children[1])
            return f"{{{base}}}^{{{sup}}}"
        return ""
    
    def _convert_subscript(self, element) -> str:
        """Convert msub to LaTeX subscript"""
        children = list(element)
        if len(children) >= 2:
            base = self._convert_element(children[0])
            sub = self._convert_element(children[1])
            return f"{{{base}}}_{{{sub}}}"
        return ""
    
    def _convert_subsup(self, element) -> str:
        """Convert msubsup to LaTeX subscript and superscript"""
        children = list(element)
        if len(children) >= 3:
            base = self._convert_element(children[0])
            sub = self._convert_element(children[1])
            sup = self._convert_element(children[2])
            return f"{{{base}}}_{{{sub}}}^{{{sup}}}"
        return ""
    
    def _convert_sqrt(self, element) -> str:
        """Convert msqrt to LaTeX square root"""
        children = list(element)
        if children:
            content = self._convert_element(children[0])
            return f"\\sqrt{{{content}}}"
        return ""
    
    def _convert_root(self, element) -> str:
        """Convert mroot to LaTeX nth root"""
        children = list(element)
        if len(children) >= 2:
            content = self._convert_element(children[0])
            index = self._convert_element(children[1])
            return f"\\sqrt[{index}]{{{content}}}"
        return ""
    
    def _convert_under(self, element) -> str:
        """Convert munder to LaTeX under"""
        children = list(element)
        if len(children) >= 2:
            base = self._convert_element(children[0])
            under = self._convert_element(children[1])
            return f"\\underset{{{under}}}{{{base}}}"
        return ""
    
    def _convert_over(self, element) -> str:
        """Convert mover to LaTeX over"""
        children = list(element)
        if len(children) >= 2:
            base = self._convert_element(children[0])
            over = self._convert_element(children[1])
            return f"\\overset{{{over}}}{{{base}}}"
        return ""
    
    def _convert_underover(self, element) -> str:
        """Convert munderover to LaTeX under and over"""
        children = list(element)
        if len(children) >= 3:
            base = self._convert_element(children[0])
            under = self._convert_element(children[1])
            over = self._convert_element(children[2])
            return f"\\overset{{{over}}}{{\\underset{{{under}}}{{{base}}}}}"
        return ""
    
    def _convert_table(self, element) -> str:
        """Convert mtable to LaTeX matrix"""
        rows = []
        for row in element:
            if row.tag == 'mtr':
                cells = []
                for cell in row:
                    if cell.tag == 'mtd':
                        cells.append(self._convert_element(cell))
                rows.append(' & '.join(cells))
        
        if rows:
            return f"\\begin{{matrix}}\n" + " \\\\\n".join(rows) + "\n\\end{{matrix}}"
        return ""
    
    def _convert_table_row(self, element) -> str:
        """Convert mtr to LaTeX table row"""
        cells = []
        for cell in element:
            if cell.tag == 'mtd':
                cells.append(self._convert_element(cell))
        return ' & '.join(cells)
    
    def _convert_table_cell(self, element) -> str:
        """Convert mtd to LaTeX table cell"""
        return self._convert_element(element)
    
    def _convert_fenced(self, element) -> str:
        """Convert mfenced to LaTeX delimiters"""
        open_delim = element.get('open', '(')
        close_delim = element.get('close', ')')
        separators = element.get('separators', ',')
        
        children = list(element)
        if children:
            content = separators.join(self._convert_element(child) for child in children)
            return f"\\left{open_delim}{content}\\right{close_delim}"
        return f"\\left{open_delim}\\right{close_delim}"
    
    def _convert_enclose(self, element) -> str:
        """Convert menclose to LaTeX enclosure"""
        notation = element.get('notation', '')
        content = self._convert_element(element)
        
        if notation == 'updiagonalstrike':
            return f"\\cancel{{{content}}}"
        elif notation == 'downdiagonalstrike':
            return f"\\bcancel{{{content}}}"
        else:
            return content

class ContentEnhancer:
    """Enhances content with AI-generated explanations and hints"""
    
    def __init__(self):
        self.difficulty_keywords = {
            'easy': ['basic', 'simple', 'fundamental', 'introductory'],
            'medium': ['intermediate', 'standard', 'typical', 'common'],
            'hard': ['advanced', 'complex', 'challenging', 'difficult', 'sophisticated']
        }
    
    def generate_ai_hint(self, problem_text: str, solution: str) -> str:
        """Generate AI-powered hint for the problem"""
        # This would integrate with your LLM service
        # For now, return a placeholder
        return f"💡 Hint: Break down this problem step by step. Consider the key concepts involved."
    
    def generate_ai_solution(self, problem_text: str, original_solution: str) -> str:
        """Generate enhanced AI solution"""
        # This would integrate with your LLM service
        return f"🤖 AI-Enhanced Solution: {original_solution[:100]}..."
    
    def generate_deep_solution(self, problem_text: str, solution: str) -> str:
        """Generate deep, comprehensive solution"""
        # This would integrate with your LLM service
        return f"🧠 Deep Analysis: This problem demonstrates advanced mathematical concepts..."
    
    def calculate_difficulty_score(self, problem_text: str, solution: str) -> float:
        """Calculate difficulty score based on content analysis"""
        text_lower = problem_text.lower()
        solution_lower = solution.lower()
        
        score = 0.5  # Base score
        
        # Check for difficulty indicators
        for level, keywords in self.difficulty_keywords.items():
            for keyword in keywords:
                if keyword in text_lower or keyword in solution_lower:
                    if level == 'easy':
                        score -= 0.1
                    elif level == 'hard':
                        score += 0.2
        
        # Check for mathematical complexity
        complex_patterns = [
            r'\\frac', r'\\sqrt', r'\\sum', r'\\int', r'\\lim',
            r'\\begin\{matrix\}', r'\\begin\{cases\}'
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, problem_text + solution):
                score += 0.1
        
        return max(0.1, min(1.0, score))

class DataTransformer:
    """Main data transformation class"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.mathml_converter = MathMLConverter()
        self.content_enhancer = ContentEnhancer()
        
        # Grade mapping from mpcstudy to DreamSeedAI
        self.grade_mapping = {
            'G9': 'G9',
            'G10': 'G10', 
            'G11': 'G11',
            'G12': 'G12'
        }
        
        # Category mapping
        self.category_mapping = {
            'M': 'Mathematics',
            'S': 'Science',
            'E': 'English',
            'H': 'History'
        }
    
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def extract_problems_from_mysql_dump(self, dump_file_path: str) -> List[Dict]:
        """Extract problem data from MySQL dump file"""
        problems = []
        
        try:
            with open(dump_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find INSERT statements for tbl_question
            insert_pattern = r'INSERT INTO.*?tbl_question.*?VALUES\s*\((.*?)\);'
            matches = re.findall(insert_pattern, content, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                # Parse the values (this is simplified - real parsing would be more complex)
                values = self._parse_insert_values(match)
                if values and len(values) >= 20:  # Ensure we have enough fields
                    problem_data = {
                        'que_id': int(values[0]) if values[0] else 0,
                        'que_status': int(values[1]) if values[1] else 1,
                        'que_class': values[2] if values[2] else 'M',
                        'que_category1': int(values[3]) if values[3] else 0,
                        'que_category2': int(values[4]) if values[4] else 0,
                        'que_category3': int(values[5]) if values[5] else 0,
                        'que_grade': values[6] if values[6] else 'G10',
                        'que_level': int(values[7]) if values[7] else 1,
                        'que_en_title': values[8] if values[8] else '',
                        'que_en_desc': values[9] if values[9] else '',
                        'que_en_hint': values[10] if values[10] else '',
                        'que_en_solution': values[11] if values[11] else '',
                        'que_en_answers': values[12] if values[12] else '',
                        'que_en_answerm': values[13] if values[13] else '',
                        'que_answertype': int(values[14]) if values[14] else 0,
                        'que_en_example': values[15] if values[15] else '',
                        'que_en_resource': values[16] if values[16] else '',
                        'que_createddate': values[17] if values[17] else '',
                        'que_modifieddate': values[18] if values[18] else '',
                    }
                    problems.append(problem_data)
            
            logger.info(f"Extracted {len(problems)} problems from MySQL dump")
            return problems
            
        except Exception as e:
            logger.error(f"Failed to extract problems from dump: {e}")
            return []
    
    def _parse_insert_values(self, values_string: str) -> List[str]:
        """Parse INSERT VALUES string (simplified implementation)"""
        # This is a simplified parser - in production, use a proper SQL parser
        values = []
        current_value = ""
        in_quotes = False
        quote_char = None
        paren_count = 0
        
        for char in values_string:
            if char in ["'", '"'] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_value += char
            elif char == quote_char and in_quotes:
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
                values.append(current_value.strip())
                current_value = ""
            else:
                current_value += char
        
        if current_value.strip():
            values.append(current_value.strip())
        
        return values
    
    def transform_problem(self, raw_problem: Dict) -> ProblemData:
        """Transform a single problem to DreamSeedAI format"""
        try:
            # Convert MathML to LaTeX
            desc_latex = self.mathml_converter.convert_mathml_to_latex(raw_problem.get('que_en_desc', ''))
            solution_latex = self.mathml_converter.convert_mathml_to_latex(raw_problem.get('que_en_solution', ''))
            answers_latex = self.mathml_converter.convert_mathml_to_latex(raw_problem.get('que_en_answers', ''))
            
            # Generate AI-enhanced content
            ai_hint = self.content_enhancer.generate_ai_hint(
                raw_problem.get('que_en_desc', ''),
                raw_problem.get('que_en_solution', '')
            )
            
            ai_solution = self.content_enhancer.generate_ai_solution(
                raw_problem.get('que_en_desc', ''),
                raw_problem.get('que_en_solution', '')
            )
            
            deep_solution = self.content_enhancer.generate_deep_solution(
                raw_problem.get('que_en_desc', ''),
                raw_problem.get('que_en_solution', '')
            )
            
            # Calculate difficulty score
            difficulty_score = self.content_enhancer.calculate_difficulty_score(
                raw_problem.get('que_en_desc', ''),
                raw_problem.get('que_en_solution', '')
            )
            
            return ProblemData(
                que_id=raw_problem.get('que_id', 0),
                que_class=raw_problem.get('que_class', 'M'),
                que_grade=self.grade_mapping.get(raw_problem.get('que_grade', 'G10'), 'G10'),
                que_level=raw_problem.get('que_level', 1),
                que_en_title=raw_problem.get('que_en_title', ''),
                que_en_desc=desc_latex,
                que_en_hint=raw_problem.get('que_en_hint', ''),
                que_en_solution=solution_latex,
                que_en_answers=answers_latex,
                que_en_answerm=raw_problem.get('que_en_answerm', ''),
                que_answertype=raw_problem.get('que_answertype', 0),
                que_category1=raw_problem.get('que_category1', 0),
                que_category2=raw_problem.get('que_category2', 0),
                que_category3=raw_problem.get('que_category3', 0),
                que_en_example=raw_problem.get('que_en_example', ''),
                que_en_resource=raw_problem.get('que_en_resource', ''),
                que_createddate=raw_problem.get('que_createddate', ''),
                que_modifieddate=raw_problem.get('que_modifieddate', ''),
                que_status=raw_problem.get('que_status', 1),
                que_ai_generated_hint=ai_hint,
                que_ai_generated_solution=ai_solution,
                que_ai_generated_deep_solution=deep_solution,
                que_difficulty_score=difficulty_score,
                que_avg_time_sec=300,  # Default 5 minutes
                que_correct_rate=0.7,  # Default 70% correct rate
            )
            
        except Exception as e:
            logger.error(f"Failed to transform problem {raw_problem.get('que_id', 'unknown')}: {e}")
            raise
    
    def load_transformed_data(self, problems: List[ProblemData]):
        """Load transformed problems into DreamSeedAI database"""
        try:
            # Create questions_enhanced table if it doesn't exist
            self._create_questions_enhanced_table()
            
            # Insert problems in batches
            batch_size = 100
            for i in range(0, len(problems), batch_size):
                batch = problems[i:i + batch_size]
                self._insert_problem_batch(batch)
                logger.info(f"Inserted batch {i//batch_size + 1}/{(len(problems)-1)//batch_size + 1}")
            
            self.conn.commit()
            logger.info(f"Successfully loaded {len(problems)} problems into database")
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to load transformed data: {e}")
            raise
    
    def _create_questions_enhanced_table(self):
        """Create the enhanced questions table"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS questions_enhanced (
            que_id SERIAL PRIMARY KEY,
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
            -- Multilingual support
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
            -- Enhanced content
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
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_grade ON questions_enhanced(que_grade);
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_level ON questions_enhanced(que_level);
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_category ON questions_enhanced(que_category1, que_category2, que_category3);
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_difficulty ON questions_enhanced(que_difficulty_score);
        CREATE INDEX IF NOT EXISTS idx_questions_enhanced_status ON questions_enhanced(que_status);
        """
        
        self.cursor.execute(create_table_sql)
        logger.info("Created questions_enhanced table with indexes")
    
    def _insert_problem_batch(self, problems: List[ProblemData]):
        """Insert a batch of problems"""
        insert_sql = """
        INSERT INTO questions_enhanced (
            que_class, que_grade, que_level, que_en_title, que_en_desc, que_en_hint,
            que_en_solution, que_en_answers, que_en_answerm, que_answertype,
            que_category1, que_category2, que_category3, que_en_example, que_en_resource,
            que_createddate, que_modifieddate, que_status,
            que_ai_generated_hint, que_ai_generated_solution, que_ai_generated_deep_solution,
            que_difficulty_score, que_avg_time_sec, que_correct_rate
        ) VALUES (
            %(que_class)s, %(que_grade)s, %(que_level)s, %(que_en_title)s, %(que_en_desc)s, %(que_en_hint)s,
            %(que_en_solution)s, %(que_en_answers)s, %(que_en_answerm)s, %(que_answertype)s,
            %(que_category1)s, %(que_category2)s, %(que_category3)s, %(que_en_example)s, %(que_en_resource)s,
            %(que_createddate)s, %(que_modifieddate)s, %(que_status)s,
            %(que_ai_generated_hint)s, %(que_ai_generated_solution)s, %(que_ai_generated_deep_solution)s,
            %(que_difficulty_score)s, %(que_avg_time_sec)s, %(que_correct_rate)s
        )
        """
        
        problem_dicts = []
        for problem in problems:
            problem_dict = {
                'que_class': problem.que_class,
                'que_grade': problem.que_grade,
                'que_level': problem.que_level,
                'que_en_title': problem.que_en_title,
                'que_en_desc': problem.que_en_desc,
                'que_en_hint': problem.que_en_hint,
                'que_en_solution': problem.que_en_solution,
                'que_en_answers': problem.que_en_answers,
                'que_en_answerm': problem.que_en_answerm,
                'que_answertype': problem.que_answertype,
                'que_category1': problem.que_category1,
                'que_category2': problem.que_category2,
                'que_category3': problem.que_category3,
                'que_en_example': problem.que_en_example,
                'que_en_resource': problem.que_en_resource,
                'que_createddate': problem.que_createddate,
                'que_modifieddate': problem.que_modifieddate,
                'que_status': problem.que_status,
                'que_ai_generated_hint': problem.que_ai_generated_hint,
                'que_ai_generated_solution': problem.que_ai_generated_solution,
                'que_ai_generated_deep_solution': problem.que_ai_generated_deep_solution,
                'que_difficulty_score': problem.que_difficulty_score,
                'que_avg_time_sec': problem.que_avg_time_sec,
                'que_correct_rate': problem.que_correct_rate,
            }
            problem_dicts.append(problem_dict)
        
        self.cursor.executemany(insert_sql, problem_dicts)
    
    def run_transformation_pipeline(self, dump_file_path: str):
        """Run the complete transformation pipeline"""
        logger.info("Starting DreamSeedAI data transformation pipeline")
        
        try:
            # Connect to database
            self.connect_to_database()
            
            # Extract problems from MySQL dump
            logger.info("Extracting problems from MySQL dump...")
            raw_problems = self.extract_problems_from_mysql_dump(dump_file_path)
            
            if not raw_problems:
                logger.warning("No problems found in dump file")
                return
            
            # Transform problems
            logger.info("Transforming problems...")
            transformed_problems = []
            for i, raw_problem in enumerate(raw_problems):
                try:
                    transformed = self.transform_problem(raw_problem)
                    transformed_problems.append(transformed)
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"Transformed {i + 1}/{len(raw_problems)} problems")
                        
                except Exception as e:
                    logger.error(f"Failed to transform problem {i}: {e}")
                    continue
            
            # Load transformed data
            logger.info("Loading transformed data into database...")
            self.load_transformed_data(transformed_problems)
            
            logger.info("Data transformation pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        finally:
            if hasattr(self, 'conn'):
                self.conn.close()

def main():
    """Main function to run the transformation pipeline"""
    
    # Database configuration
    db_config = {
        'host': '127.0.0.1',
        'port': 5432,
        'database': 'dreamseed',
        'user': 'postgres',
        'password': 'DreamSeedAi@0908'
    }
    
    # Path to MySQL dump file
    dump_file_path = '/var/www/mpcstudy.com/mpcstudy_db.sql'
    
    # Create transformer and run pipeline
    transformer = DataTransformer(db_config)
    transformer.run_transformation_pipeline(dump_file_path)

if __name__ == "__main__":
    main()
