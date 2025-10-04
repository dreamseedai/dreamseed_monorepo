#!/usr/bin/env python3
"""
Final MathML Analysis Script
Analyzes the mpcstudy_db.sql dump to count MathML conversion targets accurately.
"""

import re
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_mathml_final(sql_dump_path="mpcstudy_db.sql"):
    """
    Final comprehensive analysis of MathML in the SQL dump.
    """
    # Regex patterns
    mathml_regex = re.compile(r'<math[^>]*>.*?</math>', re.DOTALL)
    insert_question_regex = re.compile(r'INSERT INTO `tbl_question` VALUES \((.*?)\);', re.DOTALL)
    
    # Counters
    total_questions = 0
    questions_with_mathml = 0
    total_mathml_tags = 0
    wrs_chemistry_count = 0
    wrs_math_count = 0
    wrs_physics_count = 0
    wrs_biology_count = 0
    wrs_general_count = 0
    
    # Subject-wise counters
    math_subjects = 0
    physics_subjects = 0
    chemistry_subjects = 0
    biology_subjects = 0
    
    # MathML complexity counters
    simple_mathml = 0  # Basic fractions, powers, etc.
    complex_mathml = 0  # Integrals, matrices, etc.
    chemistry_mathml = 0  # Chemical formulas, reactions
    
    # Sample data for analysis
    sample_mathml = []
    question_mathml_counts = {}
    
    if not os.path.exists(sql_dump_path):
        logger.error(f"SQL dump file '{sql_dump_path}' not found.")
        return
    
    logger.info(f"Starting comprehensive MathML analysis of '{sql_dump_path}'...")
    
    with open(sql_dump_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            if "INSERT INTO `tbl_question`" in line:
                total_questions += 1
                
                # Extract the VALUES part
                match = insert_question_regex.search(line)
                if match:
                    values_str = match.group(1)
                    
                    # Parse the VALUES string more carefully
                    # Split by comma, but handle quoted strings properly
                    fields = []
                    current_field = []
                    in_quotes = False
                    quote_char = None
                    
                    i = 0
                    while i < len(values_str):
                        char = values_str[i]
                        
                        if not in_quotes:
                            if char in ["'", '"']:
                                in_quotes = True
                                quote_char = char
                                current_field.append(char)
                            elif char == ',':
                                fields.append(''.join(current_field).strip())
                                current_field = []
                            else:
                                current_field.append(char)
                        else:
                            current_field.append(char)
                            if char == quote_char and (i == 0 or values_str[i-1] != '\\'):
                                in_quotes = False
                                quote_char = None
                        
                        i += 1
                    
                    # Add the last field
                    if current_field:
                        fields.append(''.join(current_field).strip())
                    
                    # Extract relevant fields (based on the structure we saw)
                    if len(fields) >= 19:  # Ensure we have enough fields
                        que_id = fields[0].strip("'\"")
                        que_class = fields[2].strip("'\"")  # M, P, C, B
                        que_grade = fields[6].strip("'\"")  # G09, G10, G11, G12, U01, etc.
                        que_en_solution = fields[11].strip("'\"")  # Solution field
                        
                        # Count by subject
                        if que_class == 'M':
                            math_subjects += 1
                        elif que_class == 'P':
                            physics_subjects += 1
                        elif que_class == 'C':
                            chemistry_subjects += 1
                        elif que_class == 'B':
                            biology_subjects += 1
                        
                        # Find MathML in the solution
                        if que_en_solution and que_en_solution != 'NULL':
                            # Unescape the content
                            solution_content = que_en_solution.replace("\\'", "'").replace('\\"', '"')
                            
                            mathml_matches = mathml_regex.findall(solution_content)
                            
                            if mathml_matches:
                                questions_with_mathml += 1
                                num_mathml_in_question = len(mathml_matches)
                                total_mathml_tags += num_mathml_in_question
                                question_mathml_counts[que_id] = num_mathml_in_question
                                
                                # Collect samples
                                if len(sample_mathml) < 10:
                                    sample_mathml.extend(mathml_matches[:2])  # Take first 2 from each question
                                
                                # Analyze each MathML tag
                                for mathml_tag in mathml_matches:
                                    # Check for wrs classes
                                    if 'class="wrs_chemistry"' in mathml_tag:
                                        wrs_chemistry_count += 1
                                    elif 'class="wrs_math"' in mathml_tag:
                                        wrs_math_count += 1
                                    elif 'class="wrs_physics"' in mathml_tag:
                                        wrs_physics_count += 1
                                    elif 'class="wrs_biology"' in mathml_tag:
                                        wrs_biology_count += 1
                                    elif 'class="wrs_general"' in mathml_tag:
                                        wrs_general_count += 1
                                    
                                    # Categorize by complexity
                                    if any(tag in mathml_tag for tag in ['<mfrac>', '<msup>', '<msub>', '<mi>', '<mn>']):
                                        if any(tag in mathml_tag for tag in ['<munderover>', '<mtable>', '<mtr>', '<mtd>', '<munder>', '<mover>']):
                                            complex_mathml += 1
                                        else:
                                            simple_mathml += 1
                                    
                                    # Check for chemistry content
                                    if any(pattern in mathml_tag.lower() for pattern in ['h2o', 'co2', 'nh3', 'c6h6', 'benzene', 'reaction', '→', '⇌']):
                                        chemistry_mathml += 1
                
                # Progress update
                if total_questions % 1000 == 0:
                    logger.info(f"Processed {total_questions} questions...")
    
    # Generate comprehensive report
    logger.info("=" * 60)
    logger.info("FINAL MATHML CONVERSION TARGET ANALYSIS")
    logger.info("=" * 60)
    
    logger.info(f"📊 DATABASE STATISTICS:")
    logger.info(f"   Total questions: {total_questions:,}")
    logger.info(f"   Questions with MathML: {questions_with_mathml:,}")
    logger.info(f"   Total MathML tags: {total_mathml_tags:,}")
    
    if questions_with_mathml > 0:
        logger.info(f"   Average MathML per question: {total_mathml_tags / questions_with_mathml:.2f}")
    
    logger.info(f"\n📚 SUBJECT BREAKDOWN:")
    logger.info(f"   Math (M): {math_subjects:,}")
    logger.info(f"   Physics (P): {physics_subjects:,}")
    logger.info(f"   Chemistry (C): {chemistry_subjects:,}")
    logger.info(f"   Biology (B): {biology_subjects:,}")
    
    logger.info(f"\n🏷️  WRS CLASS ANALYSIS:")
    logger.info(f"   wrs_chemistry: {wrs_chemistry_count:,}")
    logger.info(f"   wrs_math: {wrs_math_count:,}")
    logger.info(f"   wrs_physics: {wrs_physics_count:,}")
    logger.info(f"   wrs_biology: {wrs_biology_count:,}")
    logger.info(f"   wrs_general: {wrs_general_count:,}")
    total_wrs = wrs_chemistry_count + wrs_math_count + wrs_physics_count + wrs_biology_count + wrs_general_count
    logger.info(f"   Total WRS classes: {total_wrs:,}")
    
    logger.info(f"\n🧮 MATHML COMPLEXITY ANALYSIS:")
    logger.info(f"   Simple MathML: {simple_mathml:,}")
    logger.info(f"   Complex MathML: {complex_mathml:,}")
    logger.info(f"   Chemistry MathML: {chemistry_mathml:,}")
    
    logger.info(f"\n🎯 CONVERSION TARGETS:")
    logger.info(f"   Primary conversion target: {total_mathml_tags:,} MathML tags")
    logger.info(f"   Questions requiring conversion: {questions_with_mathml:,}")
    logger.info(f"   Estimated conversion time: {total_mathml_tags * 0.5 / 60:.1f} minutes (at 0.5s per tag)")
    
    # Show sample MathML
    logger.info(f"\n📝 SAMPLE MATHML TAGS:")
    for i, sample in enumerate(sample_mathml[:5], 1):
        logger.info(f"   {i}. {sample[:100]}...")
    
    # Show questions with most MathML
    logger.info(f"\n📈 TOP QUESTIONS BY MATHML COUNT:")
    sorted_questions = sorted(question_mathml_counts.items(), key=lambda x: x[1], reverse=True)
    for q_id, count in sorted_questions[:10]:
        logger.info(f"   Question {q_id}: {count} MathML tags")
    
    # Save detailed results
    results = {
        "total_questions": total_questions,
        "questions_with_mathml": questions_with_mathml,
        "total_mathml_tags": total_mathml_tags,
        "subject_breakdown": {
            "math": math_subjects,
            "physics": physics_subjects,
            "chemistry": chemistry_subjects,
            "biology": biology_subjects
        },
        "wrs_classes": {
            "wrs_chemistry": wrs_chemistry_count,
            "wrs_math": wrs_math_count,
            "wrs_physics": wrs_physics_count,
            "wrs_biology": wrs_biology_count,
            "wrs_general": wrs_general_count
        },
        "mathml_complexity": {
            "simple": simple_mathml,
            "complex": complex_mathml,
            "chemistry": chemistry_mathml
        },
        "conversion_estimate": {
            "total_mathml_tags": total_mathml_tags,
            "questions_to_convert": questions_with_mathml,
            "estimated_time_minutes": total_mathml_tags * 0.5 / 60
        }
    }
    
    with open("final_mathml_analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n💾 Detailed results saved to: final_mathml_analysis_results.json")
    logger.info("=" * 60)
    
    return results

if __name__ == "__main__":
    analyze_mathml_final()
