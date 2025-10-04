#!/usr/bin/env python3
"""
Improved MySQL Dump Parser for DreamSeedAI
==========================================

This script provides a more robust parser for extracting problem data
from the mpcstudy.com MySQL dump file.
"""

import re
import json
import logging
from typing import List, Dict, Optional
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MySQLDumpParser:
    """Robust MySQL dump parser for problem data extraction"""
    
    def __init__(self, dump_file_path: str):
        self.dump_file_path = dump_file_path
        self.problems = []
    
    def extract_problems(self) -> List[Dict]:
        """Extract problem data from MySQL dump"""
        logger.info(f"Parsing MySQL dump: {self.dump_file_path}")
        
        try:
            with open(self.dump_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the CREATE TABLE statement to understand the structure
            table_structure = self._extract_table_structure(content)
            logger.info(f"Table structure: {table_structure}")
            
            # Extract INSERT statements
            insert_statements = self._extract_insert_statements(content)
            logger.info(f"Found {len(insert_statements)} INSERT statements")
            
            # Parse each INSERT statement
            for i, statement in enumerate(insert_statements):
                try:
                    problems = self._parse_insert_statement(statement, table_structure)
                    self.problems.extend(problems)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Parsed {i + 1}/{len(insert_statements)} INSERT statements")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse INSERT statement {i}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(self.problems)} problems")
            return self.problems
            
        except Exception as e:
            logger.error(f"Failed to extract problems: {e}")
            return []
    
    def _extract_table_structure(self, content: str) -> List[str]:
        """Extract column names from CREATE TABLE statement"""
        # Find CREATE TABLE statement for tbl_question
        create_pattern = r'CREATE TABLE.*?tbl_question.*?\((.*?)\)'
        match = re.search(create_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not match:
            logger.warning("Could not find CREATE TABLE statement for tbl_question")
            return []
        
        table_def = match.group(1)
        
        # Extract column names (simplified - just get the first word of each line)
        columns = []
        for line in table_def.split('\n'):
            line = line.strip()
            if line and not line.startswith('PRIMARY KEY') and not line.startswith('KEY'):
                # Extract column name (first word before space or parenthesis)
                col_match = re.match(r'`?(\w+)`?', line)
                if col_match:
                    columns.append(col_match.group(1))
        
        logger.info(f"Extracted columns: {columns}")
        return columns
    
    def _extract_insert_statements(self, content: str) -> List[str]:
        """Extract all INSERT statements for tbl_question"""
        # More flexible pattern to match INSERT statements
        insert_pattern = r'INSERT INTO.*?tbl_question.*?VALUES\s*\((.*?)\);'
        matches = re.findall(insert_pattern, content, re.DOTALL | re.IGNORECASE)
        
        # Also try to find multi-row INSERT statements
        multi_insert_pattern = r'INSERT INTO.*?tbl_question.*?VALUES\s*((?:\([^)]+\),?\s*)+);'
        multi_matches = re.findall(multi_insert_pattern, content, re.DOTALL | re.IGNORECASE)
        
        all_statements = []
        
        # Process single-row INSERTs
        for match in matches:
            all_statements.append(f"({match})")
        
        # Process multi-row INSERTs
        for match in multi_matches:
            # Split by ),( to get individual rows
            rows = re.split(r'\),\s*\(', match)
            for row in rows:
                # Clean up the row
                row = row.strip()
                if row.startswith('('):
                    row = row[1:]
                if row.endswith(')'):
                    row = row[:-1]
                if row:
                    all_statements.append(f"({row})")
        
        return all_statements
    
    def _parse_insert_statement(self, statement: str, columns: List[str]) -> List[Dict]:
        """Parse a single INSERT statement into problem dictionaries"""
        problems = []
        
        try:
            # Remove outer parentheses
            if statement.startswith('(') and statement.endswith(')'):
                statement = statement[1:-1]
            
            # Parse values using a more robust approach
            values = self._parse_values_robust(statement)
            
            if len(values) >= len(columns):
                # Create problem dictionary
                problem = {}
                for i, column in enumerate(columns):
                    if i < len(values):
                        value = values[i].strip()
                        # Remove quotes if present
                        if value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        elif value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        
                        # Convert to appropriate type
                        if column in ['que_id', 'que_status', 'que_category1', 'que_category2', 'que_category3', 
                                    'que_level', 'que_answertype']:
                            try:
                                problem[column] = int(value) if value and value != 'NULL' else 0
                            except ValueError:
                                problem[column] = 0
                        else:
                            problem[column] = value if value != 'NULL' else ''
                
                problems.append(problem)
            
        except Exception as e:
            logger.warning(f"Failed to parse statement: {e}")
        
        return problems
    
    def _parse_values_robust(self, values_string: str) -> List[str]:
        """Robust parsing of VALUES string"""
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
    
    def save_to_csv(self, output_file: str):
        """Save extracted problems to CSV file"""
        if not self.problems:
            logger.warning("No problems to save")
            return
        
        try:
            # Get all unique keys from all problems
            all_keys = set()
            for problem in self.problems:
                all_keys.update(problem.keys())
            
            fieldnames = sorted(list(all_keys))
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.problems)
            
            logger.info(f"Saved {len(self.problems)} problems to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save to CSV: {e}")
    
    def get_sample_problems(self, count: int = 5) -> List[Dict]:
        """Get a sample of problems for inspection"""
        return self.problems[:count] if self.problems else []

def main():
    """Main function to test the parser"""
    dump_file_path = '/var/www/mpcstudy.com/mpcstudy_db.sql'
    
    parser = MySQLDumpParser(dump_file_path)
    problems = parser.extract_problems()
    
    if problems:
        logger.info(f"Extracted {len(problems)} problems")
        
        # Show sample problems
        samples = parser.get_sample_problems(3)
        for i, problem in enumerate(samples):
            logger.info(f"Sample problem {i+1}:")
            logger.info(f"  ID: {problem.get('que_id', 'N/A')}")
            logger.info(f"  Title: {problem.get('que_en_title', 'N/A')[:100]}...")
            logger.info(f"  Grade: {problem.get('que_grade', 'N/A')}")
            logger.info(f"  Level: {problem.get('que_level', 'N/A')}")
            logger.info("---")
        
        # Save to CSV for inspection
        parser.save_to_csv('/tmp/mpcstudy_problems.csv')
        
    else:
        logger.warning("No problems extracted")

if __name__ == "__main__":
    main()
