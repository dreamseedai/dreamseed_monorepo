#!/usr/bin/env python3
"""
Line-based MySQL dump parser for extremely long INSERT statements.
This handles single-line INSERT statements that contain multiple records.
"""

import re
import json

def parse_mysql_dump_line_by_line(dump_file_path, table_name='tbl_question'):
    """
    Parse MySQL dump file line by line to extract INSERT statements.
    Each INSERT statement is assumed to be on a single line.
    """
    print(f"Reading dump file line by line: {dump_file_path}")
    
    insert_statements = []
    line_number = 0
    
    with open(dump_file_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line_number += 1
            
            # Check if this line contains an INSERT statement for our table
            if f'INSERT INTO `{table_name}`' in line:
                print(f"\nFound INSERT statement at line {line_number}")
                print(f"Line length: {len(line)} characters")
                
                # Extract the VALUES part
                # Format: INSERT INTO `table` (`cols...`) VALUES (data...);
                match = re.search(rf'INSERT INTO `{table_name}` \([^)]+\) VALUES (.+);', line)
                
                if match:
                    values_part = match.group(1)
                    print(f"Values part length: {len(values_part)} characters")
                    print(f"First 200 chars: {values_part[:200]}...")
                    
                    # Now parse the individual records
                    # Each record is enclosed in parentheses: (...),(...),...
                    records = parse_records_from_values(values_part)
                    print(f"Found {len(records)} records")
                    
                    insert_statements.append({
                        'line_number': line_number,
                        'values': values_part,
                        'records': records
                    })
                else:
                    print("WARNING: Could not extract VALUES part!")
    
    print(f"\nTotal INSERT statements found: {len(insert_statements)}")
    return insert_statements

def parse_records_from_values(values_str):
    """
    Parse individual records from the VALUES string.
    Records are separated by ),( and each record is enclosed in parentheses.
    """
    records = []
    
    # Use a simple split approach first to count records
    # We'll look for the pattern ),(  which separates records
    # But we need to be careful about ),( appearing inside string values
    
    depth = 0
    current_record_start = 0
    in_string = False
    string_char = None
    escape_next = False
    i = 0
    
    while i < len(values_str):
        char = values_str[i]
        
        if escape_next:
            escape_next = False
            i += 1
            continue
        
        if char == '\\':
            escape_next = True
            i += 1
            continue
        
        # Handle string literals
        if char in ('"', "'"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                # Check if it's escaped by doubling
                if i + 1 < len(values_str) and values_str[i + 1] == char:
                    i += 2  # Skip the doubled quote
                    continue
                else:
                    in_string = False
                    string_char = None
        
        # Track parentheses depth (only outside strings)
        elif not in_string:
            if char == '(':
                depth += 1
                if depth == 1:
                    current_record_start = i + 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    # End of a record
                    record_str = values_str[current_record_start:i]
                    records.append(record_str)
                    
                    # Skip past the comma if there is one
                    if i + 1 < len(values_str) and values_str[i + 1] == ',':
                        i += 1
        
        i += 1
    
    return records

def parse_field_from_record(record_str):
    """
    Parse individual fields from a record string.
    Fields are separated by commas (outside quotes).
    """
    fields = []
    current_field_start = 0
    in_string = False
    string_char = None
    escape_next = False
    i = 0
    
    while i < len(record_str):
        char = record_str[i]
        
        if escape_next:
            escape_next = False
            i += 1
            continue
        
        if char == '\\':
            escape_next = True
            i += 1
            continue
        
        # Handle string literals
        if char in ('"', "'"):
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                # Check if it's escaped by doubling
                if i + 1 < len(record_str) and record_str[i + 1] == char:
                    i += 2
                    continue
                else:
                    in_string = False
                    string_char = None
        
        # Field separator (only outside strings)
        elif not in_string and char == ',':
            field = record_str[current_record_start:i].strip()
            fields.append(field)
            current_record_start = i + 1
        
        i += 1
    
    # Don't forget the last field
    if current_record_start < len(record_str):
        field = record_str[current_record_start:].strip()
        fields.append(field)
    
    return fields

if __name__ == '__main__':
    dump_file = '/var/www/mpcstudy.com/mpcstudy_db.sql'
    table_name = 'tbl_question'
    
    print("=" * 80)
    print("MySQL Dump Parser - Line-Based Version")
    print("=" * 80)
    
    # Parse the dump file
    insert_statements = parse_mysql_dump_line_by_line(dump_file, table_name)
    
    if insert_statements:
        print(f"\n{'=' * 80}")
        print("Processing first record from first INSERT statement...")
        print("=" * 80)
        
        first_statement = insert_statements[0]
        if first_statement['records']:
            first_record = first_statement['records'][0]
            print(f"\nFirst record length: {len(first_record)} characters")
            print(f"First 500 chars: {first_record[:500]}...")
            
            # Try to parse fields
            print("\nParsing fields from first record...")
            fields = parse_field_from_record(first_record)
            print(f"Found {len(fields)} fields")
            
            # Show first few fields
            for i, field in enumerate(fields[:10]):
                print(f"  Field {i}: {field[:100]}...")
        
        # Calculate total records
        total_records = sum(len(stmt['records']) for stmt in insert_statements)
        print(f"\n{'=' * 80}")
        print(f"Total records across all INSERT statements: {total_records}")
        print("=" * 80)
    else:
        print("\nNo INSERT statements found!")

