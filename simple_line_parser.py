#!/usr/bin/env python3
"""
Simple line-by-line parser for mpcstudy.com data
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

class SimpleLineParser:
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
    
    def extract_problems(self) -> List[ProblemData]:
        """Extract all problems from the MySQL dump file"""
        logging.info(f"Reading dump file: {self.dump_file_path}")
        
        problems = []
        in_insert = False
        current_values = ""
        brace_count = 0
        
        with open(self.dump_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Check if this line starts an INSERT statement
                if line.startswith("INSERT INTO `tbl_question` VALUES"):
                    logging.info(f"Found INSERT statement at line {line_num}")
                    in_insert = True
                    # Extract the VALUES part
                    values_start = line.find("VALUES") + 6
                    current_values = line[values_start:].strip()
                    brace_count = current_values.count('(') - current_values.count(')')
                    continue
                
                # If we're in an INSERT statement, continue collecting
                if in_insert:
                    current_values += " " + line
                    brace_count += line.count('(') - line.count(')')
                    
                    # If we've closed all braces, we're done with this INSERT
                    if brace_count <= 0 and line.endswith(';'):
                        logging.info(f"Completed INSERT statement at line {line_num}")
                        # Parse this INSERT statement
                        insert_problems = self.parse_insert_values(current_values)
                        problems.extend(insert_problems)
                        in_insert = False
                        current_values = ""
                        brace_count = 0
                        
                        if len(problems) % 1000 == 0:
                            logging.info(f"Parsed {len(problems)} problems so far...")
        
        logging.info(f"Successfully extracted {len(problems)} problems")
        return problems
    
    def parse_insert_values(self, values_str: str) -> List[ProblemData]:
        """Parse the VALUES part of an INSERT statement"""
        problems = []
        
        # Remove the semicolon at the end
        if values_str.endswith(';'):
            values_str = values_str[:-1]
        
        # Split by ),( to get individual rows
        # This is a simple approach that should work for most cases
        rows = []
        current_row = ""
        paren_count = 0
        in_quotes = False
        escape_next = False
        
        for char in values_str:
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
                    
            except Exception as e:
                logging.error(f"Error parsing row {i+1}: {e}")
                continue
        
        return problems
    
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
    parser = SimpleLineParser(dump_file)
    
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
