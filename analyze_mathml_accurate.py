#!/usr/bin/env python3
"""
Accurate MathML Database Analysis Script
More precise analysis of MathML patterns in the SQL database dump
"""

import re
import os
import sys
from collections import defaultdict

def analyze_mathml_accurate(sql_file_path):
    """More accurate analysis of MathML patterns in the SQL database dump"""
    
    print("=== 정확한 MathML 데이터베이스 분석 ===")
    print(f"분석 대상 파일: {sql_file_path}")
    print(f"파일 크기: {os.path.getsize(sql_file_path) / (1024*1024):.1f} MB")
    print()
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
        
        # 1. 전체 MathML 태그 수 계산
        print("=== 1. 전체 MathML 태그 분석 ===")
        math_tags = re.findall(r'<math[^>]*>.*?</math>', content, re.IGNORECASE | re.DOTALL)
        print(f"전체 MathML 태그 수: {len(math_tags):,}개")
        
        # 2. MathType 클래스별 분석
        print("\n=== 2. MathType 클래스별 분석 ===")
        math_type_patterns = {
            'wrs_chemistry': r'class=[\'"]wrs_chemistry[\'"]',
            'wrs_math': r'class=[\'"]wrs_math[\'"]',
            'wrs_physics': r'class=[\'"]wrs_physics[\'"]', 
            'wrs_biology': r'class=[\'"]wrs_biology[\'"]',
            'wrs_general': r'class=[\'"]wrs[\'"]'
        }
        
        math_type_counts = {}
        for pattern_name, pattern in math_type_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            math_type_counts[pattern_name] = len(matches)
            print(f"{pattern_name:15}: {len(matches):>6}개")
        
        # 3. MathML이 포함된 INSERT 문 분석
        print("\n=== 3. INSERT 문 분석 ===")
        
        # INSERT 문을 찾되, 더 정확한 패턴 사용
        insert_pattern = r'INSERT INTO `tbl_question`[^;]*?;'
        insert_matches = re.findall(insert_pattern, content, re.IGNORECASE | re.DOTALL)
        print(f"총 INSERT 문 수: {len(insert_matches):,}개")
        
        # MathML이 포함된 INSERT 문 찾기
        mathml_inserts = []
        for insert_match in insert_matches:
            if re.search(r'<math[^>]*>', insert_match, re.IGNORECASE):
                mathml_inserts.append(insert_match)
        
        print(f"MathML이 포함된 INSERT 문: {len(mathml_inserts):,}개")
        
        # 4. 과목별 분석 (INSERT 문에서)
        print("\n=== 4. 과목별 MathML 분석 ===")
        subjects = {
            'Math': r'[\'"]M[\'"]',
            'Physics': r'[\'"]P[\'"]',
            'Chemistry': r'[\'"]C[\'"]',
            'Biology': r'[\'"]B[\'"]'
        }
        
        subject_mathml_counts = {}
        for subject, subject_pattern in subjects.items():
            count = 0
            for insert_match in mathml_inserts:
                if re.search(subject_pattern, insert_match, re.IGNORECASE):
                    count += 1
            subject_mathml_counts[subject] = count
            print(f"{subject:10}: {count:>6}개")
        
        # 5. 학년별 분석
        print("\n=== 5. 학년별 MathML 분석 ===")
        grades = ['G09', 'G10', 'G11', 'G12']
        grade_mathml_counts = {}
        for grade in grades:
            count = 0
            grade_pattern = rf'[\'"]{grade}[\'"]'
            for insert_match in mathml_inserts:
                if re.search(grade_pattern, insert_match, re.IGNORECASE):
                    count += 1
            grade_mathml_counts[grade] = count
            print(f"{grade:10}: {count:>6}개")
        
        # 6. MathML 요소별 분석
        print("\n=== 6. MathML 요소별 분석 ===")
        mathml_elements = {
            'mfrac': r'<mfrac[^>]*>',
            'msup': r'<msup[^>]*>',
            'msub': r'<msub[^>]*>',
            'mi': r'<mi[^>]*>',
            'mn': r'<mn[^>]*>',
            'mo': r'<mo[^>]*>',
            'mtable': r'<mtable[^>]*>',
            'mtr': r'<mtr[^>]*>',
            'mtd': r'<mtd[^>]*>',
            'msqrt': r'<msqrt[^>]*>',
            'mfenced': r'<mfenced[^>]*>',
            'mover': r'<mover[^>]*>',
            'munder': r'<munder[^>]*>',
            'mrow': r'<mrow[^>]*>',
            'mstyle': r'<mstyle[^>]*>'
        }
        
        element_counts = {}
        for element, pattern in mathml_elements.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            element_counts[element] = len(matches)
            print(f"{element:10}: {len(matches):>8}개")
        
        # 7. 샘플 MathML 태그 출력
        print("\n=== 7. MathML 태그 샘플 ===")
        sample_tags = math_tags[:3] if math_tags else []
        for i, tag in enumerate(sample_tags, 1):
            print(f"샘플 {i}: {tag[:200]}{'...' if len(tag) > 200 else ''}")
        
        # 8. 최종 요약
        print("\n=== 8. 최종 요약 ===")
        total_mathml_tags = len(math_tags)
        total_mathml_inserts = len(mathml_inserts)
        total_math_type = sum(math_type_counts.values())
        
        print(f"📊 총 MathML 태그 수: {total_mathml_tags:,}개")
        print(f"📊 MathML이 포함된 INSERT 문: {total_mathml_inserts:,}개")
        print(f"📊 MathType 사용 태그: {total_math_type:,}개")
        
        if total_mathml_tags > 0:
            math_type_percentage = (total_math_type / total_mathml_tags * 100)
            print(f"📊 MathType 사용률: {math_type_percentage:.1f}%")
        
        # 9. 변환 대상 추정
        print("\n=== 9. 변환 대상 추정 ===")
        print(f"🎯 MathML to MathLive 변환 대상: {total_mathml_tags:,}개")
        print(f"🎯 MathType 기반 변환 대상: {total_math_type:,}개")
        
        if total_mathml_tags > 0:
            print(f"💡 예상 변환 시간 (100개/배치): {total_mathml_tags // 100 + 1}배치")
            print(f"💡 예상 변환 시간 (50개/배치): {total_mathml_tags // 50 + 1}배치")
        
        return {
            'total_mathml_tags': total_mathml_tags,
            'mathml_inserts': total_mathml_inserts,
            'math_type_usage': total_math_type,
            'subject_counts': subject_mathml_counts,
            'grade_counts': grade_mathml_counts,
            'element_counts': element_counts
        }
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    sql_file = "mpcstudy_db.sql"
    
    if not os.path.exists(sql_file):
        print(f"오류: {sql_file} 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    results = analyze_mathml_accurate(sql_file)
    
    if results:
        print(f"\n✅ 분석 완료!")
        print(f"🎯 MathML 변환 대상: {results['total_mathml_tags']:,}개")
    else:
        print("❌ 분석 실패")
        sys.exit(1)
