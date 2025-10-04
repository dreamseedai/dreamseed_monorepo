#!/usr/bin/env python3
"""
Final MathML Count Analysis
Based on the actual SQL dump analysis
"""

import re
import json
import os

def analyze_mathml_count():
    """
    Final comprehensive analysis of MathML in the SQL dump.
    """
    print("=" * 60)
    print("FINAL MATHML CONVERSION TARGET ANALYSIS")
    print("=" * 60)
    
    # Count total questions
    with open("mpcstudy_db.sql", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Count INSERT statements
    insert_count = len(re.findall(r'INSERT INTO `tbl_question`', content))
    
    # Count MathML tags
    mathml_count = len(re.findall(r'<math[^>]*>.*?</math>', content, re.DOTALL))
    
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
    
    # Count questions with MathML
    questions_with_mathml = 0
    for match in re.finditer(r'INSERT INTO `tbl_question` VALUES \((.*?)\);', content, re.DOTALL):
        values_str = match.group(1)
        if '<math' in values_str:
            questions_with_mathml += 1
    
    # Calculate average MathML per question
    avg_mathml_per_question = mathml_count / questions_with_mathml if questions_with_mathml > 0 else 0
    
    # Estimate conversion time (0.5 seconds per MathML tag)
    estimated_time_minutes = mathml_count * 0.5 / 60
    
    print(f"📊 DATABASE STATISTICS:")
    print(f"   Total questions: {insert_count:,}")
    print(f"   Questions with MathML: {questions_with_mathml:,}")
    print(f"   Total MathML tags: {mathml_count:,}")
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
    print(f"   Primary conversion target: {mathml_count:,} MathML tags")
    print(f"   Questions requiring conversion: {questions_with_mathml:,}")
    print(f"   Estimated conversion time: {estimated_time_minutes:.1f} minutes (at 0.5s per tag)")
    
    # Show some sample MathML
    print(f"\n📝 SAMPLE MATHML TAGS:")
    mathml_samples = re.findall(r'<math[^>]*>.*?</math>', content, re.DOTALL)
    for i, sample in enumerate(mathml_samples[:5], 1):
        print(f"   {i}. {sample[:100]}...")
    
    # Save results
    results = {
        "total_questions": insert_count,
        "questions_with_mathml": questions_with_mathml,
        "total_mathml_tags": mathml_count,
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
        "conversion_estimate": {
            "total_mathml_tags": mathml_count,
            "questions_to_convert": questions_with_mathml,
            "estimated_time_minutes": estimated_time_minutes
        }
    }
    
    with open("final_mathml_count_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Detailed results saved to: final_mathml_count_results.json")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    analyze_mathml_count()
