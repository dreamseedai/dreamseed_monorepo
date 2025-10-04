#!/usr/bin/env python3
"""
Final robust data extractor for mpcstudy.com MySQL dump
Handles complex INSERT statements with nested parentheses and multi-line content
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProblemData:
    """Data structure for extracted problem information"""
    que_id: int
    que_class: str
    que_grade: int
    que_level: int
    que_subject: str
    que_type: int
    que_title: str
    que_desc: str
    que_hint: str
    que_solution: str
    que_answers: str
    que_answerm: str
    que_answertype: int
    que_category1: str
    que_category2: str
    que_category3: str
    que_example: str
    que_resource: str
    que_createddate: str
    que_modifieddate: str

class FinalMySQLDumpParser:
    """Robust parser for MySQL dump files with complex INSERT statements"""
    
    def __init__(self, dump_file_path: str):
        self.dump_file_path = dump_file_path
        self.problems: List[ProblemData] = []
        
    def extract_problems_from_dump(self) -> List[ProblemData]:
        """Extract problem data from MySQL dump file"""
        logger.info(f"Parsing MySQL dump: {self.dump_file_path}")
        
        try:
            with open(self.dump_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                
            # Find all INSERT statements for tbl_question
            insert_statements = self._find_insert_statements(content)
            logger.info(f"Found {len(insert_statements)} INSERT statement groups")
            
            # Parse each INSERT statement
            for i, statement in enumerate(insert_statements):
                try:
                    problems = self._parse_insert_statement(statement)
                    self.problems.extend(problems)
                    if i % 100 == 0:  # Log progress every 100 statements
                        logger.info(f"Processed {i+1}/{len(insert_statements)} INSERT statements")
                except Exception as e:
                    logger.warning(f"Failed to parse INSERT statement {i+1}: {e}")
                    continue
                    
            logger.info(f"Successfully extracted {len(self.problems)} problems")
            return self.problems
            
        except Exception as e:
            logger.error(f"Failed to extract problems from dump: {e}")
            return []
    
    def _find_insert_statements(self, content: str) -> List[str]:
        """Find all INSERT statements for tbl_question table"""
        # Look for INSERT INTO `tbl_question` statements
        pattern = r'INSERT INTO `tbl_question` VALUES\s*([^;]+);'
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        
        # Clean up the matches - remove extra whitespace and newlines
        statements = []
        for match in matches:
            # Remove extra whitespace but preserve the structure
            cleaned = re.sub(r'\s+', ' ', match.strip())
            statements.append(cleaned)
            
        return statements
    
    def _parse_insert_statement(self, statement: str) -> List[ProblemData]:
        """Parse a single INSERT statement and extract problem data"""
        problems = []
        
        # Split by ),( to get individual rows
        # But we need to be careful about nested parentheses
        rows = self._split_insert_values(statement)
        
        for row in rows:
            try:
                problem = self._parse_single_row(row)
                if problem:
                    problems.append(problem)
            except Exception as e:
                logger.debug(f"Failed to parse row: {e}")
                continue
                
        return problems
    
    def _split_insert_values(self, statement: str) -> List[str]:
        """Split INSERT VALUES by ),( while respecting nested parentheses"""
        rows = []
        current_row = ""
        paren_count = 0
        in_string = False
        escape_next = False
        
        i = 0
        while i < len(statement):
            char = statement[i]
            
            if escape_next:
                current_row += char
                escape_next = False
            elif char == '\\':
                current_row += char
                escape_next = True
            elif char == "'" and not escape_next:
                in_string = not in_string
                current_row += char
            elif not in_string:
                if char == '(':
                    paren_count += 1
                    current_row += char
                elif char == ')':
                    paren_count -= 1
                    current_row += char
                    
                    # Check if this is the end of a row
                    if paren_count == 0 and current_row.strip():
                        rows.append(current_row.strip())
                        current_row = ""
                else:
                    current_row += char
            else:
                current_row += char
                
            i += 1
            
        # Add the last row if it exists
        if current_row.strip():
            rows.append(current_row.strip())
            
        return rows
    
    def _parse_single_row(self, row: str) -> Optional[ProblemData]:
        """Parse a single row of INSERT VALUES"""
        # Remove outer parentheses
        if row.startswith('(') and row.endswith(')'):
            row = row[1:-1]
        
        # Split by comma, but respect quoted strings
        values = self._split_by_comma_respecting_quotes(row)
        
        if len(values) < 20:  # Expected number of columns
            logger.debug(f"Row has insufficient columns: {len(values)}")
            return None
            
        try:
            # Map values to ProblemData fields
            problem = ProblemData(
                que_id=int(values[0]) if values[0] else 0,
                que_class=values[1] if values[1] else '',
                que_grade=int(values[2]) if values[2] else 0,
                que_level=int(values[3]) if values[3] else 0,
                que_subject=values[4] if values[4] else '',
                que_type=int(values[5]) if values[5] else 0,
                que_title=values[6] if values[6] else '',
                que_desc=values[7] if values[7] else '',
                que_hint=values[8] if values[8] else '',
                que_solution=values[9] if values[9] else '',
                que_answers=values[10] if values[10] else '',
                que_answerm=values[11] if values[11] else '',
                que_answertype=int(values[12]) if values[12] else 0,
                que_category1=values[13] if values[13] else '',
                que_category2=values[14] if values[14] else '',
                que_category3=values[15] if values[15] else '',
                que_example=values[16] if values[16] else '',
                que_resource=values[17] if values[17] else '',
                que_createddate=values[18] if values[18] else '',
                que_modifieddate=values[19] if values[19] else ''
            )
            return problem
            
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to parse row values: {e}")
            return None
    
    def _split_by_comma_respecting_quotes(self, text: str) -> List[str]:
        """Split text by comma while respecting quoted strings"""
        values = []
        current_value = ""
        in_string = False
        escape_next = False
        
        i = 0
        while i < len(text):
            char = text[i]
            
            if escape_next:
                current_value += char
                escape_next = False
            elif char == '\\':
                current_value += char
                escape_next = True
            elif char == "'" and not escape_next:
                in_string = not in_string
                current_value += char
            elif char == ',' and not in_string:
                values.append(current_value.strip())
                current_value = ""
            else:
                current_value += char
                
            i += 1
            
        # Add the last value
        if current_value.strip():
            values.append(current_value.strip())
            
        return values

def main():
    """Main function to run the data extraction"""
    dump_file = "/var/www/mpcstudy.com/mpcstudy_db.sql"
    
    parser = FinalMySQLDumpParser(dump_file)
    problems = parser.extract_problems_from_dump()
    
    if problems:
        logger.info(f"Successfully extracted {len(problems)} problems")
        
        # Show sample of extracted data
        for i, problem in enumerate(problems[:3]):
            logger.info(f"Sample problem {i+1}:")
            logger.info(f"  ID: {problem.que_id}")
            logger.info(f"  Title: {problem.que_title[:100]}...")
            logger.info(f"  Grade: {problem.que_grade}")
            logger.info(f"  Level: {problem.que_level}")
            logger.info(f"  Subject: {problem.que_subject}")
            logger.info("---")
    else:
        logger.warning("No problems extracted")

if __name__ == "__main__":
    main()