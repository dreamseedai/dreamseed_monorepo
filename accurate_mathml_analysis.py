#!/usr/bin/env python3
"""
Accurate MathML Analysis
Based on the actual SQL dump analysis
"""

import re
import json
import os

def analyze_mathml_accurate():
    """
    Accurate analysis of MathML in the SQL dump.
    """
    print("=" * 60)
    print("ACCURATE MATHML CONVERSION TARGET ANALYSIS")
    print("=" * 60)
    
    with open("mpcstudy_db.sql", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Count total questions
    total_questions = len(re.findall(r'INSERT INTO `tbl_question`.*?VALUES', content))
    
    # Count MathML tags
    mathml_tags = re.findall(r'<math[^>]*>.*?</math>', content, re.DOTALL)
    total_mathml_tags = len(mathml_tags)
    
    # Count questions with MathML
    insert_matches = re.findall(r'INSERT INTO `tbl_question`.*?VALUES.*?;', content, re.DOTALL)
    questions_with_mathml = sum(1 for match in insert_matches if '<math' in match)
    
    # Count wrs classes
    wrs_chemistry = len(re.findall(r'class="wrs_chemistry"', content))
    wrs_math = len(re.findall(r'class="wrs_math"', content))
    wrs_physics = len(re.findall(r'class="wrs_physics"', content))
    wrs_biology = len(re.findall(r'class="wrs_biology"', content))
    wrs_general = len(re.findall(r'class="wrs_general"', content))
    
    # Count by subject (from the data we saw)
    math_subjects = len(re.findall(r"',1,'M',", content))
    physics_subjects = len(re.findall(r"',1,'P',", content))
    chemistry_subjects = len(re.findall(r"',1,'C',", content))
    biology_subjects = len(re.findall(r"',1,'B',", content))
    
    # Calculate average MathML per question with MathML
    avg_mathml_per_question = total_mathml_tags / questions_with_mathml if questions_with_mathml > 0 else 0
    
    # Estimate conversion time (0.5 seconds per MathML tag)
    estimated_time_minutes = total_mathml_tags * 0.5 / 60
    
    print(f"📊 DATABASE STATISTICS:")
    print(f"   Total questions: {total_questions:,}")
    print(f"   Questions with MathML: {questions_with_mathml:,}")
    print(f"   Total MathML tags: {total_mathml_tags:,}")
    print(f"   Average MathML per question: {avg_mathml_per_question:.2f}")
    
    print(f"\n📚 SUBJECT BREAKDOWN:")
    print(f"   Math (M): {math_subjects:,}")
    print(f"   Physics (P): {physics_subjects:,}")
    print(f"   Chemistry (C): {chemistry_subjects:,}")
    print(f"   Biology (B): {biology_subjects:,}")
    
    print(f"\n🏷️  WRS CLASS ANALYSIS:")
    print(f"   wrs_chemistry: {wrs_chemistry:,}")
    print(f"   wrs_math: {wrs_math:,}")
    print(f"   wrs_physics: {wrs_physics:,}")
    print(f"   wrs_biology: {wrs_biology:,}")
    print(f"   wrs_general: {wrs_general:,}")
    total_wrs = wrs_chemistry + wrs_math + wrs_physics + wrs_biology + wrs_general
    print(f"   Total WRS classes: {total_wrs:,}")
    
    print(f"\n🎯 CONVERSION TARGETS:")
    print(f"   Primary conversion target: {total_mathml_tags:,} MathML tags")
    print(f"   Questions requiring conversion: {questions_with_mathml:,}")
    print(f"   Estimated conversion time: {estimated_time_minutes:.1f} minutes (at 0.5s per tag)")
    
    # Show some sample MathML
    print(f"\n📝 SAMPLE MATHML TAGS:")
    for i, sample in enumerate(mathml_tags[:5], 1):
        print(f"   {i}. {sample[:100]}...")
    
    # Analyze MathML complexity
    simple_mathml = 0
    complex_mathml = 0
    chemistry_mathml = 0
    
    for mathml in mathml_tags:
        # Simple MathML (basic fractions, powers, etc.)
        if any(tag in mathml for tag in ['<mfrac>', '<msup>', '<msub>', '<mi>', '<mn>']):
            if any(tag in mathml for tag in ['<munderover>', '<mtable>', '<mtr>', '<mtd>', '<munder>', '<mover>']):
                complex_mathml += 1
            else:
                simple_mathml += 1
        
        # Check for chemistry content
        if any(pattern in mathml.lower() for pattern in ['h2o', 'co2', 'nh3', 'c6h6', 'benzene', 'reaction', '→', '⇌']):
            chemistry_mathml += 1
    
    print(f"\n🧮 MATHML COMPLEXITY ANALYSIS:")
    print(f"   Simple MathML: {simple_mathml:,}")
    print(f"   Complex MathML: {complex_mathml:,}")
    print(f"   Chemistry MathML: {chemistry_mathml:,}")
    
    # Save results
    results = {
        "total_questions": total_questions,
        "questions_with_mathml": questions_with_mathml,
        "total_mathml_tags": total_mathml_tags,
        "average_mathml_per_question": avg_mathml_per_question,
        "subject_breakdown": {
            "math": math_subjects,
            "physics": physics_subjects,
            "chemistry": chemistry_subjects,
            "biology": biology_subjects
        },
        "wrs_classes": {
            "wrs_chemistry": wrs_chemistry,
            "wrs_math": wrs_math,
            "wrs_physics": wrs_physics,
            "wrs_biology": wrs_biology,
            "wrs_general": wrs_general,
            "total": total_wrs
        },
        "mathml_complexity": {
            "simple": simple_mathml,
            "complex": complex_mathml,
            "chemistry": chemistry_mathml
        },
        "conversion_estimate": {
            "total_mathml_tags": total_mathml_tags,
            "questions_to_convert": questions_with_mathml,
            "estimated_time_minutes": estimated_time_minutes
        }
    }
    
    with open("accurate_mathml_analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Detailed results saved to: accurate_mathml_analysis_results.json")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    analyze_mathml_accurate()
