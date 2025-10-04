#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os

def analyze_mathml_per_question():
    """문제별 MathML 개수 분석"""
    
    print("=== 문제별 MathML 개수 분석 ===")
    
    # SQL 파일 읽기
    sql_file = "mpcstudy_db.sql"
    if not os.path.exists(sql_file):
        print(f"❌ {sql_file} 파일을 찾을 수 없습니다.")
        return
    
    with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # INSERT 문에서 문제 추출
    insert_pattern = r'INSERT INTO `tbl_question` VALUES \((.*?)\);'
    inserts = re.findall(insert_pattern, content, re.DOTALL)
    
    print(f"총 문제 수: {len(inserts)}개")
    
    mathml_count_per_question = []
    total_mathml = 0
    questions_with_mathml = 0
    
    # 각 문제별로 MathML 개수 분석
    for i, insert in enumerate(inserts):
        # MathML 태그 개수 세기
        mathml_tags = re.findall(r'<math[^>]*>.*?</math>', insert, re.DOTALL)
        mathml_count = len(mathml_tags)
        mathml_count_per_question.append(mathml_count)
        total_mathml += mathml_count
        
        if mathml_count > 0:
            questions_with_mathml += 1
            if mathml_count > 10:  # MathML이 많은 문제만 출력
                print(f"문제 {i+1}: {mathml_count}개 MathML")
                # 문제 ID 추출 시도
                id_match = re.search(r'^(\d+)', insert.strip())
                if id_match:
                    print(f"  문제 ID: {id_match.group(1)}")
                print(f"  샘플: {mathml_tags[0][:100]}...")
                print()
    
    print(f"\n=== 통계 ===")
    if mathml_count_per_question:
        print(f"평균 MathML/문제: {total_mathml/len(mathml_count_per_question):.1f}개")
        print(f"최대 MathML/문제: {max(mathml_count_per_question)}개")
        print(f"최소 MathML/문제: {min(mathml_count_per_question)}개")
        print(f"MathML이 있는 문제: {questions_with_mathml}개")
        print(f"MathML이 있는 문제 비율: {questions_with_mathml/len(mathml_count_per_question)*100:.1f}%")
        
        # MathML 개수별 분포
        print(f"\n=== MathML 개수별 분포 ===")
        distribution = {}
        for count in mathml_count_per_question:
            if count == 0:
                key = "0개"
            elif count <= 5:
                key = "1-5개"
            elif count <= 10:
                key = "6-10개"
            elif count <= 20:
                key = "11-20개"
            elif count <= 50:
                key = "21-50개"
            else:
                key = "50개 이상"
            distribution[key] = distribution.get(key, 0) + 1
        
        for key, count in sorted(distribution.items()):
            print(f"{key}: {count}개 문제 ({count/len(mathml_count_per_question)*100:.1f}%)")
    
    # 변환 대상 추정
    print(f"\n=== 변환 대상 추정 ===")
    print(f"총 MathML 태그 수: {total_mathml:,}개")
    print(f"MathML이 있는 문제 수: {questions_with_mathml:,}개")
    print(f"평균 MathML/문제: {total_mathml/questions_with_mathml if questions_with_mathml > 0 else 0:.1f}개")
    
    # 배치 처리 예상
    if total_mathml > 0:
        batch_100 = (total_mathml + 99) // 100
        batch_50 = (total_mathml + 49) // 50
        print(f"\n=== 배치 처리 예상 ===")
        print(f"100개/배치: {batch_100}배치")
        print(f"50개/배치: {batch_50}배치")
        print(f"10개/배치: {(total_mathml + 9) // 10}배치")

if __name__ == "__main__":
    analyze_mathml_per_question()
