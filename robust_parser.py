#!/usr/bin/env python3
"""
Robust MySQL dump parser that can handle extremely long INSERT statements
that may span multiple lines in the dump file.
"""

import re
import json

def parse_mysql_dump(dump_file_path, table_name='tbl_question'):
    """
    Parse MySQL dump file and extract INSERT statements for a specific table.
    This handles multi-line INSERT statements by reading the entire file
    and matching based on the complete SQL statement pattern.
    """
    print(f"Reading dump file: {dump_file_path}")
    
    # Read the entire file
    with open(dump_file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    print(f"File size: {len(content)} characters")
    
    # Pattern to match INSERT statements for the specified table
    # The dump file has the columns list first, then VALUES
    # Format: INSERT INTO `table` (`col1`, `col2`, ...) VALUES (...);
    pattern = rf'INSERT INTO `{table_name}` \([^)]+\) VALUES (.+?);'
    
    print(f"Searching for INSERT statements for table: {table_name}")
    
    # Find all INSERT statements
    matches = re.finditer(pattern, content, re.DOTALL)
    
    results = []
    count = 0
    
    for match in matches:
        count += 1
        values_str = match.group(1)
        
        # Parse the VALUES part to extract individual records
        # Each record is enclosed in parentheses and separated by commas
        # This is a simplified parser - for production, you'd want a proper SQL parser
        
        # For now, let's just extract the first few fields to verify it's working
        # We'll store the raw values string for further processing
        results.append({
            'raw_values': values_str,
            'length': len(values_str)
        })
        
        if count <= 3:
            print(f"\nINSERT statement {count}:")
            print(f"  Length: {len(values_str)} characters")
            print(f"  First 200 chars: {values_str[:200]}...")
    
    print(f"\nTotal INSERT statements found: {count}")
    
    return results

def extract_records_from_values(values_str):
    """
    Extract individual records from a VALUES string.
    This is a more sophisticated parser that handles nested parentheses,
    quoted strings, and escaped characters.
    """
    records = []
    current_record = []
    current_field = []
    in_quotes = False
    quote_char = None
    paren_depth = 0
    escape_next = False
    
    i = 0
    while i < len(values_str):
        char = values_str[i]
        
        if escape_next:
            current_field.append(char)
            escape_next = False
            i += 1
            continue
        
        if char == '\\':
            escape_next = True
            current_field.append(char)
            i += 1
            continue
        
        if char in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = char
            current_field.append(char)
        elif char == quote_char and in_quotes:
            # Check if it's escaped (doubled quote)
            if i + 1 < len(values_str) and values_str[i + 1] == quote_char:
                current_field.append(char)
                current_field.append(char)
                i += 2
                continue
            else:
                in_quotes = False
                current_field.append(char)
        elif char == '(' and not in_quotes:
            paren_depth += 1
            if paren_depth > 1:
                current_field.append(char)
        elif char == ')' and not in_quotes:
            paren_depth -= 1
            if paren_depth == 0:
                # End of current record
                if current_field:
                    current_record.append(''.join(current_field).strip())
                if current_record:
                    records.append(current_record)
                current_record = []
                current_field = []
            else:
                current_field.append(char)
        elif char == ',' and not in_quotes and paren_depth == 1:
            # Field separator
            current_record.append(''.join(current_field).strip())
            current_field = []
        else:
            current_field.append(char)
        
        i += 1
    
    return records

if __name__ == '__main__':
    dump_file = '/var/www/mpcstudy.com/mpcstudy_db.sql'
    table_name = 'tbl_question'
    
    print("=" * 80)
    print("MySQL Dump Parser - Robust Version")
    print("=" * 80)
    
    # Parse the dump file
    results = parse_mysql_dump(dump_file, table_name)
    
    if results:
        print(f"\nSuccessfully found {len(results)} INSERT statements")
        print("\nProcessing first INSERT statement to extract records...")
        
        # Try to parse the first INSERT statement
        first_insert = results[0]['raw_values']
        
        print("\nAttempting to extract individual records...")
        records = extract_records_from_values(first_insert)
        
        print(f"Found {len(records)} records in first INSERT statement")
        
        if records:
            print("\nFirst record fields:")
            for i, field in enumerate(records[0][:5]):  # Show first 5 fields
                print(f"  Field {i}: {field[:100]}...")
    else:
        print("\nNo INSERT statements found!")

