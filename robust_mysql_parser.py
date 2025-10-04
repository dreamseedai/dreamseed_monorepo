#!/usr/bin/env python3
"""
Robust MySQL Dump Parser for mpcstudy.com data
This parser handles the complex multi-line INSERT statements with MathML content
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class ProblemData:
    que_id: int
    que_class: int
    que_grade: str
    que_level: int
    que_category1: int
    que_category2: int
    que_category3: str
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
    # New fields for DreamSeedAI, initialized as None or default values
    que_ko_title: Optional[str] = None
    que_zh_title: Optional[str] = None
    que_answer_basic: Optional[str] = None
    que_answer_standard: Optional[str] = None
    que_answer_deep: Optional[str] = None
    que_difficulty_score: Optional[float] = None
    que_avg_time_sec: Optional[int] = None
    que_correct_rate: Optional[float] = None
    que_ai_generated_hint: Optional[str] = None
    que_ai_generated_solution: Optional[str] = None
    que_ai_generated_deep_solution: Optional[str] = None
    que_difficulty_tags: List[str] = field(default_factory=list)
    que_learning_objectives: List[str] = field(default_factory=list)
    que_prerequisites: List[str] = field(default_factory=list)
    que_estimated_time: Optional[int] = None
    que_mathml_content: Optional[str] = None
    que_tiptap_content: Optional[str] = None

# Define the columns for tbl_question based on the provided schema
TBL_QUESTION_COLUMNS = [
    "que_id", "que_class", "que_grade", "que_level", "que_category1", "que_category2",
    "que_category3", "que_en_title", "que_en_desc", "que_en_hint", "que_en_solution",
    "que_en_answers", "que_en_answerm", "que_answertype", "que_en_example",
    "que_en_resource", "que_createddate", "que_modifieddate"
]

class RobustMySQLParser:
    def __init__(self, dump_file_path: str):
        self.dump_file_path = dump_file_path

    def _parse_sql_value(self, value_str: str) -> str:
        """
        Parse a single SQL value, handling quotes and escaping
        """
        value_str = value_str.strip()
        
        # Handle NULL values
        if value_str.upper() == 'NULL':
            return None
            
        # Handle quoted strings
        if value_str.startswith("'") and value_str.endswith("'"):
            # Remove outer quotes and unescape
            inner = value_str[1:-1]
            # Handle escaped quotes
            inner = inner.replace("\\'", "'")
            inner = inner.replace("\\\"", "\"")
            inner = inner.replace("\\\\", "\\")
            return inner
            
        # Handle unquoted values (numbers, etc.)
        return value_str

    def _parse_values_tuple(self, tuple_str: str) -> List[str]:
        """
        Parse a single VALUES tuple like (1,2,'text','more text')
        """
        values = []
        current_value = ""
        in_quotes = False
        quote_char = None
        i = 0
        
        # Skip the opening parenthesis
        if tuple_str.startswith('('):
            tuple_str = tuple_str[1:]
        # Skip the closing parenthesis
        if tuple_str.endswith(')'):
            tuple_str = tuple_str[:-1]
            
        while i < len(tuple_str):
            char = tuple_str[i]
            
            if not in_quotes:
                if char in ["'", '"']:
                    in_quotes = True
                    quote_char = char
                    current_value += char
                elif char == ',':
                    values.append(self._parse_sql_value(current_value))
                    current_value = ""
                else:
                    current_value += char
            else:
                current_value += char
                if char == quote_char:
                    # Check if it's escaped
                    if i > 0 and tuple_str[i-1] == '\\':
                        # This is an escaped quote, continue
                        pass
                    else:
                        # This is the end of the quoted string
                        in_quotes = False
                        quote_char = None
            
            i += 1
        
        # Add the last value
        if current_value:
            values.append(self._parse_sql_value(current_value))
            
        return values

    def _extract_insert_statements(self) -> List[str]:
        """
        Extract INSERT statements by reading the entire file and using regex
        """
        logging.info(f"Reading dump file: {self.dump_file_path}")
        
        with open(self.dump_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Use regex to find all INSERT statements for tbl_question
        # This pattern matches INSERT INTO `tbl_question` VALUES followed by any content until );
        pattern = r'INSERT INTO `tbl_question` VALUES\s*([^;]+);'
        matches = re.findall(pattern, content, re.DOTALL)
        
        logging.info(f"Found {len(matches)} INSERT statements")
        return matches

    def _parse_insert_statement(self, values_str: str) -> List[ProblemData]:
        """
        Parse a single INSERT statement's values string into ProblemData objects
        """
        problems = []
        
        # Split into individual tuples
        # This is tricky because tuples can contain commas inside quoted strings
        tuples = []
        current_tuple = ""
        paren_count = 0
        in_quotes = False
        quote_char = None
        i = 0
        
        while i < len(values_str):
            char = values_str[i]
            
            if not in_quotes:
                if char in ["'", '"']:
                    in_quotes = True
                    quote_char = char
                elif char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        # End of tuple
                        current_tuple += char
                        tuples.append(current_tuple.strip())
                        current_tuple = ""
                        # Skip comma if present
                        i += 1
                        while i < len(values_str) and values_str[i] in [',', ' ', '\n', '\t']:
                            i += 1
                        continue
                        
            else:
                if char == quote_char:
                    # Check if it's escaped
                    if i > 0 and values_str[i-1] == '\\':
                        pass  # Escaped quote
                    else:
                        in_quotes = False
                        quote_char = None
            
            current_tuple += char
            i += 1
        
        # Parse each tuple
        for tuple_str in tuples:
            try:
                values = self._parse_values_tuple(tuple_str)
                
                if len(values) != len(TBL_QUESTION_COLUMNS):
                    logging.warning(f"Column count mismatch. Expected {len(TBL_QUESTION_COLUMNS)}, got {len(values)}")
                    continue
                
                # Create ProblemData object
                problem = ProblemData(
                    que_id=int(values[0]) if values[0] else 0,
                    que_class=int(values[1]) if values[1] else 0,
                    que_grade=str(values[2]) if values[2] else "",
                    que_level=int(values[3]) if values[3] else 0,
                    que_category1=int(values[4]) if values[4] else 0,
                    que_category2=int(values[5]) if values[5] else 0,
                    que_category3=str(values[6]) if values[6] else "",
                    que_en_title=str(values[7]) if values[7] else "",
                    que_en_desc=str(values[8]) if values[8] else "",
                    que_en_hint=str(values[9]) if values[9] else "",
                    que_en_solution=str(values[10]) if values[10] else "",
                    que_en_answers=str(values[11]) if values[11] else "",
                    que_en_answerm=str(values[12]) if values[12] else "",
                    que_answertype=int(values[13]) if values[13] else 0,
                    que_en_example=str(values[14]) if values[14] else "",
                    que_en_resource=str(values[15]) if values[15] else "",
                    que_createddate=str(values[16]) if values[16] else "",
                    que_modifieddate=str(values[17]) if values[17] else ""
                )
                problems.append(problem)
                
            except Exception as e:
                logging.error(f"Error parsing tuple: {e}")
                logging.error(f"Tuple: {tuple_str[:200]}...")
                continue
        
        return problems

    def extract_problems(self) -> List[ProblemData]:
        """
        Main method to extract all problems from the MySQL dump
        """
        all_problems = []
        insert_statements = self._extract_insert_statements()
        
        for i, statement in enumerate(insert_statements):
            logging.info(f"Processing INSERT statement {i+1}/{len(insert_statements)}")
            problems = self._parse_insert_statement(statement)
            all_problems.extend(problems)
            
            if (i + 1) % 10 == 0:
                logging.info(f"Processed {i+1} statements, extracted {len(all_problems)} problems so far")
        
        logging.info(f"Successfully extracted {len(all_problems)} problems total")
        return all_problems

if __name__ == "__main__":
    dump_file = "/var/www/mpcstudy.com/mpcstudy_db.sql"
    parser = RobustMySQLParser(dump_file)
    problems = parser.extract_problems()
    
    if not problems:
        logging.error("No problems extracted!")
    else:
        logging.info(f"Successfully extracted {len(problems)} problems")
        for i, problem in enumerate(problems[:5]):
            logging.info(f"Problem {i+1}: ID={problem.que_id}, Title={problem.que_en_title[:50]}...")
