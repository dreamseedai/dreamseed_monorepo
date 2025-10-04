#!/usr/bin/env python3
"""
MathML Database Analysis Script
Analyzes the mpcstudy_db.sql file to count all MathML conversion targets
"""

import re
import os
import sys
from collections import defaultdict

def analyze_mathml_patterns(sql_file_path):
    """Analyze MathML patterns in the SQL database dump"""
    
    print("=== MathML 데이터베이스 분석 시작 ===")
    print(f"분석 대상 파일: {sql_file_path}")
    print(f"파일 크기: {os.path.getsize(sql_file_path) / (1024*1024):.1f} MB")
    print()
    
    # MathML 패턴 정의
    patterns = {
        'wrs_chemistry': r'wrs_chemistry',
        'wrs_math': r'wrs_math', 
        'wrs_physics': r'wrs_physics',
        'wrs_biology': r'wrs_biology',
        'wrs_general': r'wrs',
        'math_xmlns': r'<math[^>]*xmlns[^>]*>',
        'math_tag': r'<math[^>]*>',
        'mathml_content': r'<math[^>]*>.*?</math>',
        'mfrac': r'<mfrac[^>]*>',
        'msup': r'<msup[^>]*>',
        'msub': r'<msub[^>]*>',
        'mi': r'<mi[^>]*>',
        'mn': r'<mn[^>]*>',
        'mo': r'<mo[^>]*>',
        'mtext': r'<mtext[^>]*>',
        'mtable': r'<mtable[^>]*>',
        'mtr': r'<mtr[^>]*>',
        'mtd': r'<mtd[^>]*>',
        'msqrt': r'<msqrt[^>]*>',
        'mroot': r'<mroot[^>]*>',
        'mfenced': r'<mfenced[^>]*>',
        'mover': r'<mover[^>]*>',
        'munder': r'<munder[^>]*>',
        'munderover': r'<munderover[^>]*>',
        'menclose': r'<menclose[^>]*>',
        'mspace': r'<mspace[^>]*>',
        'mstyle': r'<mstyle[^>]*>',
        'mrow': r'<mrow[^>]*>',
        'semantics': r'<semantics[^>]*>',
        'annotation': r'<annotation[^>]*>',
        'annotation-xml': r'<annotation-xml[^>]*>',
    }
    
    results = {}
    total_mathml_entries = 0
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            
        print("=== 패턴별 분석 결과 ===")
        
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            count = len(matches)
            results[pattern_name] = count
            print(f"{pattern_name:20}: {count:>6}개")
            
        # MathML이 포함된 행 수 계산
        mathml_lines = 0
        with open(sql_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                if re.search(r'<math[^>]*>', line, re.IGNORECASE):
                    mathml_lines += 1
        
        print(f"{'mathml_lines':20}: {mathml_lines:>6}개")
        
        # INSERT 문에서 MathML이 포함된 레코드 수 계산
        insert_pattern = r'INSERT INTO `tbl_question`[^;]*;'
        insert_matches = re.findall(insert_pattern, content, re.IGNORECASE | re.DOTALL)
        
        mathml_records = 0
        for insert_match in insert_matches:
            if re.search(r'<math[^>]*>', insert_match, re.IGNORECASE):
                mathml_records += 1
        
        print(f"{'mathml_records':20}: {mathml_records:>6}개")
        
        # 총 MathML 태그 수 계산 (중복 제거)
        all_math_tags = re.findall(r'<math[^>]*>.*?</math>', content, re.IGNORECASE | re.DOTALL)
        unique_math_tags = set(all_math_tags)
        
        print(f"{'unique_math_tags':20}: {len(unique_math_tags):>6}개")
        
        # 과목별 분석
        print("\n=== 과목별 MathML 분석 ===")
        subjects = {
            'Math': r'que_class.*?[\'"]M[\'"]',
            'Physics': r'que_class.*?[\'"]P[\'"]', 
            'Chemistry': r'que_class.*?[\'"]C[\'"]',
            'Biology': r'que_class.*?[\'"]B[\'"]'
        }
        
        for subject, subject_pattern in subjects.items():
            subject_mathml_count = 0
            for insert_match in insert_matches:
                if re.search(subject_pattern, insert_match, re.IGNORECASE) and re.search(r'<math[^>]*>', insert_match, re.IGNORECASE):
                    subject_mathml_count += 1
            print(f"{subject:10}: {subject_mathml_count:>6}개")
        
        # 학년별 분석
        print("\n=== 학년별 MathML 분석 ===")
        grades = ['G09', 'G10', 'G11', 'G12']
        for grade in grades:
            grade_mathml_count = 0
            grade_pattern = rf'que_grade.*?[\'"]{grade}[\'"]'
            for insert_match in insert_matches:
                if re.search(grade_pattern, insert_match, re.IGNORECASE) and re.search(r'<math[^>]*>', insert_match, re.IGNORECASE):
                    grade_mathml_count += 1
            print(f"{grade:10}: {grade_mathml_count:>6}개")
        
        # MathType 클래스별 분석
        print("\n=== MathType 클래스별 분석 ===")
        math_type_classes = ['wrs_chemistry', 'wrs_math', 'wrs_physics', 'wrs_biology']
        for class_name in math_type_classes:
            class_count = 0
            for insert_match in insert_matches:
                if re.search(rf'class=[\'"]{class_name}[\'"]', insert_match, re.IGNORECASE):
                    class_count += 1
            print(f"{class_name:15}: {class_count:>6}개")
        
        # 최종 요약
        print("\n=== 최종 요약 ===")
        print(f"총 MathML이 포함된 레코드 수: {mathml_records:,}개")
        print(f"고유한 MathML 태그 수: {len(unique_math_tags):,}개")
        print(f"MathML이 포함된 행 수: {mathml_lines:,}개")
        
        # MathType 사용률 계산
        math_type_total = sum(results[pattern] for pattern in ['wrs_chemistry', 'wrs_math', 'wrs_physics', 'wrs_biology', 'wrs_general'])
        math_type_percentage = (math_type_total / mathml_records * 100) if mathml_records > 0 else 0
        print(f"MathType 사용률: {math_type_percentage:.1f}%")
        
        return {
            'total_records': mathml_records,
            'unique_tags': len(unique_math_tags),
            'mathml_lines': mathml_lines,
            'math_type_usage': math_type_percentage,
            'patterns': results
        }
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return None

if __name__ == "__main__":
    sql_file = "mpcstudy_db.sql"
    
    if not os.path.exists(sql_file):
        print(f"오류: {sql_file} 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    results = analyze_mathml_patterns(sql_file)
    
    if results:
        print(f"\n✅ 분석 완료!")
        print(f"📊 총 MathML 변환 대상: {results['total_records']:,}개")
    else:
        print("❌ 분석 실패")
        sys.exit(1)
