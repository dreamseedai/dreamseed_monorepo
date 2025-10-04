#!/usr/bin/env python3
"""
Extract questions from MySQL dump and insert into PostgreSQL
"""

import re
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_questions_from_dump():
    """Extract questions from MySQL dump file"""
    
    dump_file = "/var/www/mpcstudy.com/mpcstudy_db.sql"
    
    logger.info(f"Reading MySQL dump: {dump_file}")
    
    with open(dump_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all INSERT statements for tbl_question
    insert_pattern = r"INSERT INTO `tbl_question` VALUES\s*([^;]+);"
    matches = re.findall(insert_pattern, content, re.MULTILINE | re.DOTALL)
    
    logger.info(f"Found {len(matches)} INSERT statement groups")
    
    questions = []
    
    for i, match in enumerate(matches):
        try:
            # Split by ),( to get individual rows
            rows = match.split('),(')
            
            for row in rows:
                # Clean up the row
                row = row.strip()
                if row.startswith('('):
                    row = row[1:]
                if row.endswith(')'):
                    row = row[:-1]
                
                # Parse values - handle quoted strings and NULL values
                values = []
                current_value = ""
                in_quotes = False
                quote_char = None
                i = 0
                
                while i < len(row):
                    char = row[i]
                    
                    if not in_quotes:
                        if char in ["'", '"']:
                            in_quotes = True
                            quote_char = char
                            current_value += char
                        elif char == ',':
                            values.append(current_value.strip())
                            current_value = ""
                        else:
                            current_value += char
                    else:
                        current_value += char
                        if char == quote_char:
                            # Check if it's escaped
                            if i + 1 < len(row) and row[i + 1] == quote_char:
                                current_value += row[i + 1]
                                i += 1
                            else:
                                in_quotes = False
                                quote_char = None
                    i += 1
                
                # Add the last value
                if current_value:
                    values.append(current_value.strip())
                
                if len(values) >= 19:  # Ensure we have enough fields
                    questions.append(values)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(matches)} INSERT statement groups")
                
        except Exception as e:
            logger.warning(f"Failed to process INSERT group {i}: {e}")
            continue
    
    logger.info(f"Successfully extracted {len(questions)} questions")
    return questions

def load_questions_to_db(questions):
    """Load questions into PostgreSQL database"""
    
    # Database configuration
    conn = psycopg2.connect(
        host="127.0.0.1",
        port="5432",
        database="dreamseed",
        user="postgres",
        password="DreamSeedAi@0908"
    )
    
    cursor = conn.cursor()
    
    total_loaded = 0
    
    for question in questions:
        try:
            # Insert into questions_enhanced table (matching existing schema)
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
                int(question[0]) if question[0] and question[0] != 'NULL' else None,  # que_id
                question[2] if question[2] and question[2] != 'NULL' else 'M',  # que_class
                question[6] if question[6] and question[6] != 'NULL' else 'G10',  # que_grade
                int(question[7]) if question[7] and question[7] != 'NULL' else 1,  # que_level
                int(question[3]) if question[3] and question[3] != 'NULL' else 0,  # que_category1
                int(question[4]) if question[4] and question[4] != 'NULL' else 0,  # que_category2
                int(question[5]) if question[5] and question[5] != 'NULL' else 0,  # que_category3
                int(question[14]) if question[14] and question[14] != 'NULL' else 0,  # que_answertype
                question[13] if question[13] and question[13] != 'NULL' else '',  # que_en_answerm
                question[8] if question[8] and question[8] != 'NULL' else '',  # que_en_title
                question[9] if question[9] and question[9] != 'NULL' else '',  # que_en_desc
                question[10] if question[10] and question[10] != 'NULL' else '',  # que_en_hint
                question[11] if question[11] and question[11] != 'NULL' else '',  # que_en_solution
                question[12] if question[12] and question[12] != 'NULL' else '',  # que_en_answers
                question[15] if question[15] and question[15] != 'NULL' else '',  # que_en_example
                question[16] if question[16] and question[16] != 'NULL' else '',  # que_en_resource
                question[17] if question[17] and question[17] != 'NULL' else '',  # que_createddate
                question[18] if question[18] and question[18] != 'NULL' else '',  # que_modifieddate
                int(question[1]) if question[1] and question[1] != 'NULL' else 1,  # que_status
            ]
            
            cursor.execute(insert_sql, processed_values)
            total_loaded += 1
            
            if total_loaded % 100 == 0:
                logger.info(f"Loaded {total_loaded} questions...")
                
        except Exception as e:
            logger.warning(f"Failed to load question {question[0] if question else 'unknown'}: {e}")
            continue
    
    conn.commit()
    logger.info(f"Successfully loaded {total_loaded} questions into database")
    
    # Verify the data
    cursor.execute("SELECT COUNT(*) FROM questions_enhanced")
    count = cursor.fetchone()[0]
    logger.info(f"Total questions in database: {count}")
    
    # Show sample questions
    cursor.execute("""
        SELECT que_id, que_en_title, que_grade, que_level 
        FROM questions_enhanced 
        WHERE que_en_title IS NOT NULL 
        LIMIT 5
    """)
    samples = cursor.fetchall()
    logger.info("Sample questions:")
    for sample in samples:
        logger.info(f"  ID: {sample[0]}, Title: {sample[1][:50]}..., Grade: {sample[2]}, Level: {sample[3]}")
    
    cursor.close()
    conn.close()

def main():
    """Main function"""
    logger.info("Starting question extraction and loading")
    
    # Extract questions from dump
    questions = extract_questions_from_dump()
    
    if not questions:
        logger.error("No questions extracted from dump file")
        return
    
    # Load questions to database
    load_questions_to_db(questions)
    
    logger.info("Question extraction and loading completed!")

if __name__ == "__main__":
    main()
