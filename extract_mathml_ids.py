#!/usr/bin/env python3
"""
mpcstudy_db.sql에서 MathML이 있는 문제 ID 추출 스크립트
"""

import sqlite3
import json
import os
from datetime import datetime

def analyze_database_structure(db_path):
    """데이터베이스 구조 분석"""
    print("🔍 데이터베이스 구조 분석 중...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 테이블 목록 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"📊 발견된 테이블: {[table[0] for table in tables]}")
    
    # 각 테이블의 컬럼 정보 조회
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print(f"\n📋 {table_name} 테이블 구조:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    conn.close()

def extract_mathml_ids(db_path, output_file="mathml_ids.json"):
    """MathML이 있는 문제 ID 추출"""
    print(f"\n📝 MathML ID 추출 시작...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # MathML이 있는 문제 조회
    query = """
    SELECT 
        id,
        question_id,
        subject,
        grade,
        title,
        LENGTH(mathml) as mathml_length,
        CASE 
            WHEN mathml IS NULL THEN 'NULL'
            WHEN mathml = '' THEN 'EMPTY'
            WHEN mathml = '<math></math>' THEN 'EMPTY_MATH'
            WHEN LENGTH(mathml) <= 10 THEN 'TOO_SHORT'
            ELSE 'VALID'
        END as mathml_status
    FROM questions 
    WHERE mathml IS NOT NULL 
    AND mathml != '' 
    AND mathml != '<math></math>'
    AND LENGTH(mathml) > 10
    ORDER BY id
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # 결과를 딕셔너리로 변환
    mathml_data = []
    for row in results:
        mathml_data.append({
            'id': row[0],
            'question_id': row[1],
            'subject': row[2],
            'grade': row[3],
            'title': row[4],
            'mathml_length': row[5],
            'mathml_status': row[6]
        })
    
    # 통계 정보
    total_count = len(mathml_data)
    subject_stats = {}
    grade_stats = {}
    length_stats = {'short': 0, 'medium': 0, 'long': 0}
    
    for item in mathml_data:
        # 과목별 통계
        subject = item['subject']
        subject_stats[subject] = subject_stats.get(subject, 0) + 1
        
        # 학년별 통계
        grade = item['grade']
        grade_stats[grade] = grade_stats.get(grade, 0) + 1
        
        # 길이별 통계
        length = item['mathml_length']
        if length < 50:
            length_stats['short'] += 1
        elif length < 200:
            length_stats['medium'] += 1
        else:
            length_stats['long'] += 1
    
    # 결과 저장
    result = {
        'extraction_time': datetime.now().isoformat(),
        'total_count': total_count,
        'statistics': {
            'by_subject': subject_stats,
            'by_grade': grade_stats,
            'by_length': length_stats
        },
        'data': mathml_data
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    conn.close()
    
    print(f"✅ {total_count}개 MathML ID 추출 완료")
    print(f"📁 결과 저장: {output_file}")
    
    # 통계 출력
    print(f"\n📊 통계 정보:")
    print(f"  - 총 개수: {total_count}")
    print(f"  - 과목별: {subject_stats}")
    print(f"  - 학년별: {grade_stats}")
    print(f"  - 길이별: {length_stats}")
    
    return result

def find_optimal_batch_size(mathml_data, test_sizes=[5, 10, 20, 30, 50, 100]):
    """최적 배치 크기 찾기"""
    print(f"\n🔬 최적 배치 크기 분석...")
    
    total_count = len(mathml_data)
    
    print(f"📊 배치 크기별 분석:")
    print(f"{'배치크기':<8} {'배치수':<6} {'마지막배치':<8} {'효율성':<8}")
    print("-" * 40)
    
    for batch_size in test_sizes:
        num_batches = (total_count + batch_size - 1) // batch_size
        last_batch_size = total_count % batch_size if total_count % batch_size != 0 else batch_size
        
        # 효율성 점수 (마지막 배치가 너무 작으면 비효율적)
        efficiency = 1.0 - (batch_size - last_batch_size) / batch_size if last_batch_size < batch_size else 1.0
        
        print(f"{batch_size:<8} {num_batches:<6} {last_batch_size:<8} {efficiency:.2f}")
    
    # 추천 배치 크기
    recommended = 50  # API 제한과 효율성의 균형
    print(f"\n💡 추천 배치 크기: {recommended}")
    print(f"   - API 제한 고려 (분당 60회)")
    print(f"   - 메모리 효율성")
    print(f"   - 에러 복구 용이성")

def main():
    """메인 실행 함수"""
    db_path = "mpcstudy_db.sql"
    
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
    
    # 1. 데이터베이스 구조 분석
    analyze_database_structure(db_path)
    
    # 2. MathML ID 추출
    result = extract_mathml_ids(db_path)
    
    # 3. 최적 배치 크기 분석
    find_optimal_batch_size(result['data'])
    
    print(f"\n🎯 다음 단계:")
    print(f"1. mathml_ids.json 파일 확인")
    print(f"2. 추천 배치 크기로 변환 실행")
    print(f"3. 진행 상황 모니터링")

if __name__ == "__main__":
    main()
