#!/usr/bin/env python3
"""
Simple Data Loader for DreamSeedAI
==================================

This script directly loads problem data from the MySQL dump into PostgreSQL
using a simpler approach.
"""

import re
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_questions_enhanced_table(cursor):
    """Check if questions_enhanced table exists and is ready for data"""
    cursor.execute("SELECT COUNT(*) FROM questions_enhanced")
    count = cursor.fetchone()[0]
    logger.info(f"questions_enhanced table exists with {count} records")

def extract_and_load_problems():
    """Extract problems from MySQL dump and load into PostgreSQL"""
    
    # Database configuration
    db_config = {
        'host': '127.0.0.1',
        'port': 5432,
        'database': 'dreamseed',
        'user': 'postgres',
        'password': 'DreamSeedAi@0908'
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Create table
        create_questions_enhanced_table(cursor)
        
        # Read MySQL dump file
        dump_file_path = '/var/www/mpcstudy.com/mpcstudy_db.sql'
        logger.info(f"Reading MySQL dump: {dump_file_path}")
        
        with open(dump_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find INSERT statements
        insert_pattern = r'INSERT INTO.*?tbl_question.*?VALUES\s*((?:\([^)]+\),?\s*)+);'
        matches = re.findall(insert_pattern, content, re.DOTALL | re.IGNORECASE)
        
        logger.info(f"Found {len(matches)} INSERT statement groups")
        
        total_loaded = 0
        
        for i, match in enumerate(matches):
            try:
                # Split by ),( to get individual rows
                rows = re.split(r'\),\s*\(', match)
                
                for row in rows:
                    # Clean up the row
                    row = row.strip()
                    if row.startswith('('):
                        row = row[1:]
                    if row.endswith(')'):
                        row = row[:-1]
                    
                    if not row:
                        continue
                    
                    # Parse the row values (simplified approach)
                    values = parse_row_values(row)
                    
                    if len(values) >= 19:  # Ensure we have enough fields
                        # Insert into database (matching existing schema)
                        insert_sql = """
                        INSERT INTO questions_enhanced (
                            que_id, que_class, que_grade, que_level, que_category1, que_category2, que_category3,
                            que_answertype, que_en_answerm, que_en_title, que_en_desc, que_en_hint,
                            que_en_solution, que_en_answers, que_en_example, que_en_resource,
                            que_createddate, que_modifieddate, que_status
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (que_id) DO NOTHING
                        """
                        
                        # Convert values to appropriate types (matching existing schema order)
                        processed_values = [
                            int(values[0]) if values[0] and values[0] != 'NULL' else None,  # que_id
                            values[2] if values[2] and values[2] != 'NULL' else 'M',  # que_class
                            values[6] if values[6] and values[6] != 'NULL' else 'G10',  # que_grade
                            int(values[7]) if values[7] and values[7] != 'NULL' else 1,  # que_level
                            int(values[3]) if values[3] and values[3] != 'NULL' else 0,  # que_category1
                            int(values[4]) if values[4] and values[4] != 'NULL' else 0,  # que_category2
                            int(values[5]) if values[5] and values[5] != 'NULL' else 0,  # que_category3
                            int(values[14]) if values[14] and values[14] != 'NULL' else 0,  # que_answertype
                            values[13] if values[13] and values[13] != 'NULL' else '',  # que_en_answerm
                            values[8] if values[8] and values[8] != 'NULL' else '',  # que_en_title
                            values[9] if values[9] and values[9] != 'NULL' else '',  # que_en_desc
                            values[10] if values[10] and values[10] != 'NULL' else '',  # que_en_hint
                            values[11] if values[11] and values[11] != 'NULL' else '',  # que_en_solution
                            values[12] if values[12] and values[12] != 'NULL' else '',  # que_en_answers
                            values[15] if values[15] and values[15] != 'NULL' else '',  # que_en_example
                            values[16] if values[16] and values[16] != 'NULL' else '',  # que_en_resource
                            values[17] if values[17] and values[17] != 'NULL' else '',  # que_createddate
                            values[18] if values[18] and values[18] != 'NULL' else '',  # que_modifieddate
                            int(values[1]) if values[1] and values[1] != 'NULL' else 1,  # que_status
                        ]
                        
                        cursor.execute(insert_sql, processed_values)
                        total_loaded += 1
                        
                        if total_loaded % 100 == 0:
                            logger.info(f"Loaded {total_loaded} problems...")
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(matches)} INSERT statement groups")
                    
            except Exception as e:
                logger.warning(f"Failed to process INSERT group {i}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Successfully loaded {total_loaded} problems into database")
        
        # Verify the data
        cursor.execute("SELECT COUNT(*) FROM questions_enhanced")
        count = cursor.fetchone()[0]
        logger.info(f"Total problems in database: {count}")
        
        # Show sample data
        cursor.execute("SELECT que_id, que_en_title, que_grade, que_level FROM questions_enhanced LIMIT 5")
        samples = cursor.fetchall()
        logger.info("Sample problems:")
        for sample in samples:
            logger.info(f"  ID: {sample[0]}, Title: {sample[1][:50]}..., Grade: {sample[2]}, Level: {sample[3]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to load problems: {e}")
        raise

def parse_row_values(row_string):
    """Parse a row string into individual values"""
    values = []
    current_value = ""
    in_quotes = False
    quote_char = None
    paren_count = 0
    i = 0
    
    while i < len(row_string):
        char = row_string[i]
        
        if char in ["'", '"'] and not in_quotes:
            in_quotes = True
            quote_char = char
            current_value += char
        elif char == quote_char and in_quotes:
            if i > 0 and row_string[i-1] == '\\':
                current_value += char
            else:
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
        
        i += 1
    
    if current_value.strip():
        values.append(current_value.strip())
    
    return values

def main():
    """Main function"""
    logger.info("Starting simple data loader for DreamSeedAI")
    extract_and_load_problems()
    logger.info("Data loading completed!")

if __name__ == "__main__":
    main()
