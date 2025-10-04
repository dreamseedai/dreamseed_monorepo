#!/usr/bin/env python3
"""
Working parser for mpcstudy.com MySQL dump
Handles the actual format found in the dump file
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

class WorkingParser:
    def __init__(self, dump_file_path: str):
        self.dump_file_path = dump_file_path

    def parse_sql_values(self, values_str: str) -> List[str]:
        """
        Parse SQL VALUES string into individual values.
        Handles quoted strings, escaped quotes, and NULL values.
        """
        values = []
        current_value = []
        in_quotes = False
        escape_next = False
        
        i = 0
        while i < len(values_str):
            char = values_str[i]
            
            if escape_next:
                current_value.append(char)
                escape_next = False
            elif char == '\\' and in_quotes:
                escape_next = True
                current_value.append(char)
            elif char == "'" and not escape_next:
                in_quotes = not in_quotes
                current_value.append(char)
            elif char == ',' and not in_quotes:
                # End of current value
                value_str = ''.join(current_value).strip()
                if value_str.upper() == 'NULL':
                    values.append(None)
                else:
                    # Remove surrounding quotes if present
                    if value_str.startswith("'") and value_str.endswith("'"):
                        value_str = value_str[1:-1]
                    values.append(value_str)
                current_value = []
            else:
                current_value.append(char)
            
            i += 1
        
        # Add the last value
        if current_value:
            value_str = ''.join(current_value).strip()
            if value_str.upper() == 'NULL':
                values.append(None)
            else:
                if value_str.startswith("'") and value_str.endswith("'"):
                    value_str = value_str[1:-1]
                values.append(value_str)
        
        return values

    def extract_problems(self) -> List[ProblemData]:
        """
        Extract problem data from the MySQL dump file.
        """
        all_problems = []
        
        logging.info(f"Reading dump file: {self.dump_file_path}")
        
        with open(self.dump_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Look for INSERT INTO `tbl_question` VALUES
                if line.startswith("INSERT INTO `tbl_question` VALUES"):
                    logging.info(f"Found INSERT statement at line {line_num}")
                    
                    # Extract the VALUES part
                    values_start = line.find("VALUES") + 6  # Skip "VALUES"
                    values_part = line[values_start:].strip()
                    
                    # Remove trailing semicolon if present
                    if values_part.endswith(';'):
                        values_part = values_part[:-1]
                    
                    # Parse the values
                    try:
                        values = self.parse_sql_values(values_part)
                        
                        if len(values) == len(TBL_QUESTION_COLUMNS):
                            # Create ProblemData object
                            row_dict = dict(zip(TBL_QUESTION_COLUMNS, values))
                            
                            problem = ProblemData(
                                que_id=int(row_dict["que_id"]) if row_dict["que_id"] else 0,
                                que_class=int(row_dict["que_class"]) if row_dict["que_class"] else 0,
                                que_grade=str(row_dict["que_grade"]) if row_dict["que_grade"] else "",
                                que_level=int(row_dict["que_level"]) if row_dict["que_level"] else 0,
                                que_category1=int(row_dict["que_category1"]) if row_dict["que_category1"] else 0,
                                que_category2=int(row_dict["que_category2"]) if row_dict["que_category2"] else 0,
                                que_category3=str(row_dict["que_category3"]) if row_dict["que_category3"] else "",
                                que_en_title=str(row_dict["que_en_title"]) if row_dict["que_en_title"] else "",
                                que_en_desc=str(row_dict["que_en_desc"]) if row_dict["que_en_desc"] else "",
                                que_en_hint=str(row_dict["que_en_hint"]) if row_dict["que_en_hint"] else "",
                                que_en_solution=str(row_dict["que_en_solution"]) if row_dict["que_en_solution"] else "",
                                que_en_answers=str(row_dict["que_en_answers"]) if row_dict["que_en_answers"] else "",
                                que_en_answerm=str(row_dict["que_en_answerm"]) if row_dict["que_en_answerm"] else "",
                                que_answertype=int(row_dict["que_answertype"]) if row_dict["que_answertype"] else 0,
                                que_en_example=str(row_dict["que_en_example"]) if row_dict["que_en_example"] else "",
                                que_en_resource=str(row_dict["que_en_resource"]) if row_dict["que_en_resource"] else "",
                                que_createddate=str(row_dict["que_createddate"]) if row_dict["que_createddate"] else "",
                                que_modifieddate=str(row_dict["que_modifieddate"]) if row_dict["que_modifieddate"] else ""
                            )
                            
                            all_problems.append(problem)
                            logging.info(f"Successfully parsed problem ID: {problem.que_id}")
                            
                        else:
                            logging.warning(f"Line {line_num}: Expected {len(TBL_QUESTION_COLUMNS)} columns, got {len(values)}")
                            
                    except Exception as e:
                        logging.error(f"Line {line_num}: Error parsing values: {e}")
                        continue
                
                # Progress indicator
                if line_num % 10000 == 0:
                    logging.info(f"Processed {line_num} lines, found {len(all_problems)} problems so far")
        
        logging.info(f"Successfully extracted {len(all_problems)} problems")
        return all_problems

if __name__ == "__main__":
    dump_file = "/var/www/mpcstudy.com/mpcstudy_db.sql"
    parser = WorkingParser(dump_file)
    problems = parser.extract_problems()
    
    if problems:
        logging.info(f"Successfully extracted {len(problems)} problems!")
        for i, problem in enumerate(problems[:3]):  # Show first 3 problems
            logging.info(f"Problem {i+1}: ID={problem.que_id}, Title={problem.que_en_title[:50]}...")
    else:
        logging.error("No problems extracted!")
