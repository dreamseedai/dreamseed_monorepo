#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os

def analyze_questions_mathml():
    """문제별 MathML 분석"""
    
    print("=== 문제별 MathML 분석 ===")
    
    # SQL 파일 읽기
    sql_file = "mpcstudy_db.sql"
    if not os.path.exists(sql_file):
        print(f"❌ {sql_file} 파일을 찾을 수 없습니다.")
        return
    
    with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # INSERT 문에서 문제 추출 (더 정확한 패턴)
    insert_pattern = r'INSERT INTO `tbl_question` VALUES \((.*?)\);'
    inserts = re.findall(insert_pattern, content, re.DOTALL)
    
    print(f"총 INSERT 문 수: {len(inserts)}")
    
    mathml_count_per_question = []
    total_mathml = 0
    questions_with_mathml = 0
    
    # 처음 100개 문제 분석
    sample_size = min(100, len(inserts))
    
    for i, insert in enumerate(inserts[:sample_size]):
        # MathML 태그 개수 세기
        mathml_tags = re.findall(r'<math[^>]*>.*?</math>', insert, re.DOTALL)
        mathml_count = len(mathml_tags)
        mathml_count_per_question.append(mathml_count)
        total_mathml += mathml_count
        
        if mathml_count > 0:
            questions_with_mathml += 1
            if mathml_count > 3:  # MathML이 많은 문제만 출력
                print(f"문제 {i+1}: {mathml_count}개 MathML")
                # 문제 ID 추출 시도
                id_match = re.search(r'^(\d+)', insert.strip())
                if id_match:
                    print(f"  문제 ID: {id_match.group(1)}")
                print(f"  샘플: {mathml_tags[0][:100]}...")
                print()
    
    print(f"\n=== 통계 (샘플 {sample_size}개 문제) ===")
    if mathml_count_per_question:
        print(f"평균 MathML/문제: {total_mathml/len(mathml_count_per_question):.1f}개")
        print(f"최대 MathML/문제: {max(mathml_count_per_question)}개")
        print(f"최소 MathML/문제: {min(mathml_count_per_question)}개")
        print(f"MathML이 있는 문제: {questions_with_mathml}개")
        print(f"MathML 비율: {questions_with_mathml/len(mathml_count_per_question)*100:.1f}%")
    
    # 전체 데이터베이스에서 MathML이 있는 문제 수 추정
    print(f"\n=== 전체 데이터베이스 추정 ===")
    if questions_with_mathml > 0:
        estimated_total_questions = len(inserts)
        estimated_questions_with_mathml = int(estimated_total_questions * (questions_with_mathml / sample_size))
        print(f"전체 문제 수: {estimated_total_questions:,}개")
        print(f"MathML이 있는 문제 수 (추정): {estimated_questions_with_mathml:,}개")
        print(f"MathML이 있는 문제 비율: {estimated_questions_with_mathml/estimated_total_questions*100:.1f}%")
    
    # MathML 태그 분포 분석
    print(f"\n=== MathML 태그 분포 ===")
    all_mathml_tags = []
    for insert in inserts[:sample_size]:
        mathml_tags = re.findall(r'<math[^>]*>.*?</math>', insert, re.DOTALL)
        all_mathml_tags.extend(mathml_tags)
    
    if all_mathml_tags:
        print(f"샘플에서 발견된 MathML 태그: {len(all_mathml_tags)}개")
        
        # MathML 요소별 분석
        elements = {}
        for tag in all_mathml_tags:
            # 주요 MathML 요소들 찾기
            for element in ['mfrac', 'msup', 'msub', 'mi', 'mn', 'mo', 'mtable', 'mtr', 'mtd', 'msqrt', 'mfenced']:
                count = len(re.findall(f'<{element}[^>]*>', tag))
                elements[element] = elements.get(element, 0) + count
        
        print("주요 MathML 요소:")
        for element, count in sorted(elements.items(), key=lambda x: x[1], reverse=True):
            print(f"  {element}: {count:,}개")

if __name__ == "__main__":
    analyze_questions_mathml()
