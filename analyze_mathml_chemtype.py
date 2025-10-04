#!/usr/bin/env python3
"""
MathML + ChemType Database Analysis Script
Analyzes both MathType and ChemType patterns in the SQL database dump
"""

import re
import os
import sys
from collections import defaultdict

def analyze_mathml_chemtype(sql_file_path):
    """Analyze both MathML and ChemType patterns in the SQL database dump"""
    
    print("=== MathML + ChemType 데이터베이스 분석 ===")
    print(f"분석 대상 파일: {sql_file_path}")
    print(f"파일 크기: {os.path.getsize(sql_file_path) / (1024*1024):.1f} MB")
    print()
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
        
        # 1. MathType 패턴 분석
        print("=== 1. MathType 패턴 분석 ===")
        math_type_patterns = {
            'wrs_chemistry': r'class=[\'"]wrs_chemistry[\'"]',
            'wrs_math': r'class=[\'"]wrs_math[\'"]',
            'wrs_physics': r'class=[\'"]wrs_physics[\'"]', 
            'wrs_biology': r'class=[\'"]wrs_biology[\'"]',
            'wrs_general': r'class=[\'"]wrs[\'"]',
            'wrs_equation': r'class=[\'"]wrs_equation[\'"]',
            'wrs_formula': r'class=[\'"]wrs_formula[\'"]'
        }
        
        math_type_counts = {}
        for pattern_name, pattern in math_type_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            math_type_counts[pattern_name] = len(matches)
            print(f"{pattern_name:15}: {len(matches):>6}개")
        
        # 2. ChemType 패턴 분석
        print("\n=== 2. ChemType 패턴 분석 ===")
        chem_type_patterns = {
            'wrs_chemistry': r'class=[\'"]wrs_chemistry[\'"]',
            'chem_equation': r'class=[\'"]chem_equation[\'"]',
            'chem_formula': r'class=[\'"]chem_formula[\'"]',
            'chemical_structure': r'class=[\'"]chemical_structure[\'"]',
            'molecule': r'class=[\'"]molecule[\'"]',
            'reaction': r'class=[\'"]reaction[\'"]',
            'chemml': r'<chemml[^>]*>',
            'chemical_notation': r'chemical_notation'
        }
        
        chem_type_counts = {}
        for pattern_name, pattern in chem_type_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            chem_type_counts[pattern_name] = len(matches)
            print(f"{pattern_name:20}: {len(matches):>6}개")
        
        # 3. 화학 관련 MathML 요소 분석
        print("\n=== 3. 화학 관련 MathML 요소 분석 ===")
        chemistry_elements = {
            'chemical_formulas': r'<msub><mi>[A-Z][a-z]?\d*</mi><mn>\d+</mn></msub>',  # H2O, CO2 등
            'chemical_bonds': r'<mo>[-=≡]</mo>',  # 단일, 이중, 삼중 결합
            'chemical_arrows': r'<mo>[→⇌⇄]</mo>',  # 화학 반응 화살표
            'subscripts': r'<msub>.*?</msub>',  # 아래첨자
            'superscripts': r'<msup>.*?</msup>',  # 위첨자
            'fractions': r'<mfrac>.*?</mfrac>',  # 분수
            'chemical_units': r'<mi>mol</mi>|<mi>g</mi>|<mi>L</mi>|<mi>atm</mi>',  # 화학 단위
            'temperature': r'<mi>°C</mi>|<mi>K</mi>',  # 온도
            'concentration': r'<mi>M</mi>|<mi>m</mi>',  # 농도
            'pressure': r'<mi>atm</mi>|<mi>Pa</mi>|<mi>torr</mi>',  # 압력
            'energy': r'<mi>J</mi>|<mi>cal</mi>|<mi>eV</mi>',  # 에너지
        }
        
        chemistry_counts = {}
        for element_name, pattern in chemistry_elements.items():
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            chemistry_counts[element_name] = len(matches)
            print(f"{element_name:20}: {len(matches):>6}개")
        
        # 4. 전체 MathML 태그 분석
        print("\n=== 4. 전체 MathML 태그 분석 ===")
        math_tags = re.findall(r'<math[^>]*>.*?</math>', content, re.IGNORECASE | re.DOTALL)
        print(f"전체 MathML 태그 수: {len(math_tags):,}개")
        
        # 5. 화학 관련 MathML 태그 분석
        print("\n=== 5. 화학 관련 MathML 태그 분석 ===")
        chemistry_mathml_tags = []
        for tag in math_tags:
            # 화학 관련 키워드가 포함된 MathML 태그 찾기
            if re.search(r'class=[\'"]wrs_chemistry[\'"]|H\d*O|CO\d*|NH\d*|CH\d*|mol|atm|°C|K|M\b|J\b|cal\b', tag, re.IGNORECASE):
                chemistry_mathml_tags.append(tag)
        
        print(f"화학 관련 MathML 태그: {len(chemistry_mathml_tags):,}개")
        
        # 6. 과목별 분석
        print("\n=== 6. 과목별 MathML 분석 ===")
        subjects = {
            'Math': r'[\'"]M[\'"]',
            'Physics': r'[\'"]P[\'"]',
            'Chemistry': r'[\'"]C[\'"]',
            'Biology': r'[\'"]B[\'"]'
        }
        
        # INSERT 문에서 과목별 분석
        insert_pattern = r'INSERT INTO `tbl_question`[^;]*?;'
        insert_matches = re.findall(insert_pattern, content, re.IGNORECASE | re.DOTALL)
        
        subject_mathml_counts = {}
        for subject, subject_pattern in subjects.items():
            count = 0
            for insert_match in insert_matches:
                if re.search(subject_pattern, insert_match, re.IGNORECASE) and re.search(r'<math[^>]*>', insert_match, re.IGNORECASE):
                    count += 1
            subject_mathml_counts[subject] = count
            print(f"{subject:10}: {count:>6}개")
        
        # 7. 샘플 화학 MathML 태그 출력
        print("\n=== 7. 화학 MathML 태그 샘플 ===")
        sample_chemistry_tags = chemistry_mathml_tags[:5] if chemistry_mathml_tags else []
        for i, tag in enumerate(sample_chemistry_tags, 1):
            print(f"화학 샘플 {i}: {tag[:200]}{'...' if len(tag) > 200 else ''}")
        
        # 8. 최종 요약
        print("\n=== 8. 최종 요약 ===")
        total_mathml_tags = len(math_tags)
        total_chemistry_mathml = len(chemistry_mathml_tags)
        total_math_type = sum(math_type_counts.values())
        total_chem_type = sum(chem_type_counts.values())
        
        print(f"📊 총 MathML 태그 수: {total_mathml_tags:,}개")
        print(f"🧪 화학 관련 MathML 태그: {total_chemistry_mathml:,}개")
        print(f"📐 MathType 사용 태그: {total_math_type:,}개")
        print(f"⚗️ ChemType 사용 태그: {total_chem_type:,}개")
        
        if total_mathml_tags > 0:
            chemistry_percentage = (total_chemistry_mathml / total_mathml_tags * 100)
            print(f"🧪 화학 관련 비율: {chemistry_percentage:.1f}%")
        
        # 9. 변환 대상 분류
        print("\n=== 9. 변환 대상 분류 ===")
        print(f"🎯 일반 MathML 변환 대상: {total_mathml_tags - total_chemistry_mathml:,}개")
        print(f"🧪 화학 MathML 변환 대상: {total_chemistry_mathml:,}개")
        print(f"📊 총 변환 대상: {total_mathml_tags:,}개")
        
        # 10. 배치 처리 추정
        print("\n=== 10. 배치 처리 추정 ===")
        if total_mathml_tags > 0:
            print(f"💡 일반 MathML (100개/배치): {(total_mathml_tags - total_chemistry_mathml) // 100 + 1}배치")
            print(f"💡 화학 MathML (100개/배치): {total_chemistry_mathml // 100 + 1}배치")
            print(f"💡 전체 (50개/배치): {total_mathml_tags // 50 + 1}배치")
        
        return {
            'total_mathml_tags': total_mathml_tags,
            'chemistry_mathml_tags': total_chemistry_mathml,
            'math_type_usage': total_math_type,
            'chem_type_usage': total_chem_type,
            'subject_counts': subject_mathml_counts,
            'chemistry_counts': chemistry_counts,
            'math_type_counts': math_type_counts,
            'chem_type_counts': chem_type_counts
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
    
    results = analyze_mathml_chemtype(sql_file)
    
    if results:
        print(f"\n✅ 분석 완료!")
        print(f"🎯 총 MathML 변환 대상: {results['total_mathml_tags']:,}개")
        print(f"🧪 화학 MathML 변환 대상: {results['chemistry_mathml_tags']:,}개")
    else:
        print("❌ 분석 실패")
        sys.exit(1)
