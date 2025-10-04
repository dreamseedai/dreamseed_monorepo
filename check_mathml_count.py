#!/usr/bin/env python3
"""
현재 데이터베이스에서 MathML이 있는 문제 개수 확인
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime

def check_mathml_count():
    """데이터베이스에서 MathML 개수 확인"""
    print("🔍 데이터베이스에서 MathML 개수 확인 중...")
    
    # 데이터베이스 연결 설정
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'dreamseed'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✅ 데이터베이스 연결 성공")
        
        # 테이블 목록 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"📊 발견된 테이블: {[table['table_name'] for table in tables]}")
        
        # questions 테이블이 있는지 확인
        questions_table = any(table['table_name'] == 'questions' for table in tables)
        
        if not questions_table:
            print("❌ questions 테이블을 찾을 수 없습니다.")
            return
        
        # MathML이 있는 문제 개수 확인
        queries = {
            'total_questions': "SELECT COUNT(*) as count FROM questions",
            'mathml_not_null': "SELECT COUNT(*) as count FROM questions WHERE mathml IS NOT NULL",
            'mathml_not_empty': "SELECT COUNT(*) as count FROM questions WHERE mathml IS NOT NULL AND mathml != ''",
            'mathml_valid': """
                SELECT COUNT(*) as count 
                FROM questions 
                WHERE mathml IS NOT NULL 
                AND mathml != '' 
                AND mathml != '<math></math>'
                AND LENGTH(mathml) > 10
            """,
            'by_subject': """
                SELECT subject, COUNT(*) as count 
                FROM questions 
                WHERE mathml IS NOT NULL 
                AND mathml != '' 
                AND mathml != '<math></math>'
                AND LENGTH(mathml) > 10
                GROUP BY subject 
                ORDER BY subject
            """,
            'by_grade': """
                SELECT grade, COUNT(*) as count 
                FROM questions 
                WHERE mathml IS NOT NULL 
                AND mathml != '' 
                AND mathml != '<math></math>'
                AND LENGTH(mathml) > 10
                GROUP BY grade 
                ORDER BY grade
            """,
            'mathml_length_stats': """
                SELECT 
                    MIN(LENGTH(mathml)) as min_length,
                    MAX(LENGTH(mathml)) as max_length,
                    AVG(LENGTH(mathml)) as avg_length
                FROM questions 
                WHERE mathml IS NOT NULL 
                AND mathml != '' 
                AND mathml != '<math></math>'
                AND LENGTH(mathml) > 10
            """
        }
        
        results = {}
        
        for query_name, query in queries.items():
            try:
                cursor.execute(query)
                if query_name in ['by_subject', 'by_grade']:
                    results[query_name] = cursor.fetchall()
                else:
                    results[query_name] = cursor.fetchone()
            except Exception as e:
                print(f"⚠️ {query_name} 쿼리 실행 실패: {e}")
                results[query_name] = None
        
        # 결과 출력
        print(f"\n📊 MathML 통계:")
        print(f"=" * 50)
        
        if results['total_questions']:
            print(f"📝 총 문제 수: {results['total_questions']['count']:,}")
        
        if results['mathml_not_null']:
            print(f"📐 MathML NULL이 아닌 문제: {results['mathml_not_null']['count']:,}")
        
        if results['mathml_not_empty']:
            print(f"📐 MathML 비어있지 않은 문제: {results['mathml_not_empty']['count']:,}")
        
        if results['mathml_valid']:
            print(f"✅ 변환 가능한 MathML 문제: {results['mathml_valid']['count']:,}")
        
        if results['by_subject']:
            print(f"\n📚 과목별 MathML 문제:")
            for row in results['by_subject']:
                print(f"  - {row['subject']}: {row['count']:,}개")
        
        if results['by_grade']:
            print(f"\n🎓 학년별 MathML 문제:")
            for row in results['by_grade']:
                print(f"  - {row['grade']}: {row['count']:,}개")
        
        if results['mathml_length_stats']:
            stats = results['mathml_length_stats']
            print(f"\n📏 MathML 길이 통계:")
            print(f"  - 최소 길이: {stats['min_length']}자")
            print(f"  - 최대 길이: {stats['max_length']}자")
            print(f"  - 평균 길이: {stats['avg_length']:.1f}자")
        
        # 변환 가능한 문제 ID 추출
        if results['mathml_valid'] and results['mathml_valid']['count'] > 0:
            print(f"\n🔍 변환 가능한 문제 ID 추출 중...")
            
            cursor.execute("""
                SELECT id, question_id, subject, grade, title, LENGTH(mathml) as mathml_length
                FROM questions 
                WHERE mathml IS NOT NULL 
                AND mathml != '' 
                AND mathml != '<math></math>'
                AND LENGTH(mathml) > 10
                ORDER BY id
                LIMIT 10
            """)
            
            sample_ids = cursor.fetchall()
            
            print(f"📋 샘플 ID (처음 10개):")
            for row in sample_ids:
                print(f"  - ID: {row['id']}, Question: {row['question_id']}, Subject: {row['subject']}, Grade: {row['grade']}")
        
        # 결과를 JSON으로 저장
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_questions': results['total_questions']['count'] if results['total_questions'] else 0,
            'mathml_not_null': results['mathml_not_null']['count'] if results['mathml_not_null'] else 0,
            'mathml_not_empty': results['mathml_not_empty']['count'] if results['mathml_not_empty'] else 0,
            'mathml_valid': results['mathml_valid']['count'] if results['mathml_valid'] else 0,
            'by_subject': {row['subject']: row['count'] for row in results['by_subject']} if results['by_subject'] else {},
            'by_grade': {row['grade']: row['count'] for row in results['by_grade']} if results['by_grade'] else {}
        }
        
        with open('mathml_count_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 상세 결과 저장: mathml_count_summary.json")
        
        cursor.close()
        conn.close()
        
        return summary
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

if __name__ == "__main__":
    check_mathml_count()
