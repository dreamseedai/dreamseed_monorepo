#!/usr/bin/env python3
"""
Ultimate MySQL Dump Parser for mpcstudy.com data
Handles complex INSERT statements with MathML and HTML content
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import csv

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
    # New fields for DreamSeedAI
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

class UltimateMySQLDumpParser:
    def __init__(self, dump_file_path: str):
        self.dump_file_path = dump_file_path
        self.problems = []
        
    def parse_value(self, value_str: str) -> str:
        """Parse a single value from the INSERT statement"""
        if not value_str or value_str.upper() == 'NULL':
            return ''
        
        # Remove surrounding quotes if present
        if value_str.startswith("'") and value_str.endswith("'"):
            value_str = value_str[1:-1]
        
        # Unescape common MySQL escape sequences
        value_str = value_str.replace("\\'", "'")
        value_str = value_str.replace('\\"', '"')
        value_str = value_str.replace('\\\\', '\\')
        value_str = value_str.replace('\\n', '\n')
        value_str = value_str.replace('\\r', '\r')
        value_str = value_str.replace('\\t', '\t')
        
        return value_str
    
    def parse_insert_statement(self, insert_statement: str) -> List[ProblemData]:
        """Parse a complete INSERT statement into ProblemData objects"""
        problems = []
        
        # Find the VALUES part
        values_match = re.search(r'VALUES\s*(.+);?$', insert_statement, re.DOTALL | re.IGNORECASE)
        if not values_match:
            logging.warning("No VALUES found in INSERT statement")
            return problems
        
        values_content = values_match.group(1).strip()
        
        # Split by ),( to get individual rows
        # This is more reliable than trying to parse nested parentheses
        rows = []
        current_row = ""
        paren_count = 0
        in_quotes = False
        escape_next = False
        
        for char in values_content:
            if escape_next:
                current_row += char
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                current_row += char
                continue
                
            if char == "'" and not escape_next:
                in_quotes = not in_quotes
                current_row += char
                continue
                
            if not in_quotes:
                if char == '(':
                    paren_count += 1
                    if paren_count == 1:
                        current_row = ""
                        continue
                elif char == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        rows.append(current_row)
                        current_row = ""
                        continue
            
            current_row += char
        
        logging.info(f"Found {len(rows)} rows to parse")
        
        # Parse each row
        for i, row in enumerate(rows):
            if not row.strip():
                continue
                
            try:
                # Split by comma, but be careful with quoted strings
                values = []
                current_value = ""
                in_quotes = False
                escape_next = False
                
                for char in row:
                    if escape_next:
                        current_value += char
                        escape_next = False
                        continue
                        
                    if char == '\\':
                        escape_next = True
                        current_value += char
                        continue
                        
                    if char == "'" and not escape_next:
                        in_quotes = not in_quotes
                        current_value += char
                        continue
                        
                    if char == ',' and not in_quotes:
                        values.append(current_value.strip())
                        current_value = ""
                        continue
                    
                    current_value += char
                
                # Add the last value
                if current_value.strip():
                    values.append(current_value.strip())
                
                # We expect 18 columns based on the schema
                if len(values) < 18:
                    logging.warning(f"Row {i+1}: Expected 18 columns, got {len(values)}")
                    continue
                
                # Parse values
                parsed_values = [self.parse_value(v) for v in values[:18]]
                
                # Create ProblemData object
                problem = ProblemData(
                    que_id=int(parsed_values[0]) if parsed_values[0] else 0,
                    que_class=int(parsed_values[1]) if parsed_values[1] else 0,
                    que_grade=parsed_values[2],
                    que_level=int(parsed_values[3]) if parsed_values[3] else 0,
                    que_category1=int(parsed_values[4]) if parsed_values[4] else 0,
                    que_category2=int(parsed_values[5]) if parsed_values[5] else 0,
                    que_category3=parsed_values[6],
                    que_en_title=parsed_values[7],
                    que_en_desc=parsed_values[8],
                    que_en_hint=parsed_values[9],
                    que_en_solution=parsed_values[10],
                    que_en_answers=parsed_values[11],
                    que_en_answerm=parsed_values[12],
                    que_answertype=int(parsed_values[13]) if parsed_values[13] else 0,
                    que_en_example=parsed_values[14],
                    que_en_resource=parsed_values[15],
                    que_createddate=parsed_values[16],
                    que_modifieddate=parsed_values[17]
                )
                
                problems.append(problem)
                
                if len(problems) % 100 == 0:
                    logging.info(f"Parsed {len(problems)} problems...")
                    
            except Exception as e:
                logging.error(f"Error parsing row {i+1}: {e}")
                continue
        
        return problems
    
    def extract_problems(self) -> List[ProblemData]:
        """Extract all problems from the MySQL dump file"""
        logging.info(f"Reading dump file: {self.dump_file_path}")
        
        with open(self.dump_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Find all INSERT statements for tbl_question
        insert_pattern = re.compile(
            r'INSERT INTO `tbl_question` VALUES\s*(.+?);',
            re.DOTALL | re.IGNORECASE
        )
        
        matches = insert_pattern.findall(content)
        logging.info(f"Found {len(matches)} INSERT statements")
        
        all_problems = []
        for i, match in enumerate(matches):
            logging.info(f"Processing INSERT statement {i+1}/{len(matches)}")
            problems = self.parse_insert_statement(f"INSERT INTO `tbl_question` VALUES {match};")
            all_problems.extend(problems)
        
        logging.info(f"Successfully extracted {len(all_problems)} problems")
        return all_problems
    
    def save_to_csv(self, problems: List[ProblemData], output_file: str):
        """Save problems to CSV file"""
        logging.info(f"Saving {len(problems)} problems to {output_file}")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'que_id', 'que_class', 'que_grade', 'que_level', 'que_category1', 'que_category2', 'que_category3',
                'que_en_title', 'que_en_desc', 'que_en_hint', 'que_en_solution', 'que_en_answers', 'que_en_answerm',
                'que_answertype', 'que_en_example', 'que_en_resource', 'que_createddate', 'que_modifieddate'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for problem in problems:
                writer.writerow({
                    'que_id': problem.que_id,
                    'que_class': problem.que_class,
                    'que_grade': problem.que_grade,
                    'que_level': problem.que_level,
                    'que_category1': problem.que_category1,
                    'que_category2': problem.que_category2,
                    'que_category3': problem.que_category3,
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
                    'que_modifieddate': problem.que_modifieddate
                })
        
        logging.info(f"CSV file saved: {output_file}")

def main():
    dump_file = "/var/www/mpcstudy.com/mpcstudy_db.sql"
    parser = UltimateMySQLDumpParser(dump_file)
    
    # Extract problems
    problems = parser.extract_problems()
    
    if problems:
        # Save to CSV
        parser.save_to_csv(problems, "/tmp/mpcstudy_problems.csv")
        
        # Print sample
        logging.info("Sample problems:")
        for i, problem in enumerate(problems[:3]):
            logging.info(f"Problem {i+1}: ID={problem.que_id}, Title={problem.que_en_title[:50]}...")
            logging.info(f"  Grade: {problem.que_grade}, Level: {problem.que_level}")
            logging.info(f"  Categories: {problem.que_category1}/{problem.que_category2}/{problem.que_category3}")
    else:
        logging.error("No problems extracted!")

if __name__ == "__main__":
    main()
