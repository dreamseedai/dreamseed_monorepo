#!/usr/bin/env python3
"""
데이터베이스 연결 테스트
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

# 환경변수 설정
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'dreamseed'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'password'

def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            port=os.environ['DB_PORT'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD']
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 테이블 존재 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("📊 데이터베이스 테이블 목록:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # questions 테이블 확인
        cursor.execute("SELECT COUNT(*) as count FROM questions;")
        question_count = cursor.fetchone()['count']
        print(f"\n📝 questions 테이블: {question_count}개 문제")
        
        # 샘플 문제 조회
        cursor.execute("""
            SELECT question_id, title, grade, subject, difficulty
            FROM questions 
            LIMIT 5;
        """)
        
        sample_questions = cursor.fetchall()
        print(f"\n🔍 샘플 문제 (최대 5개):")
        for q in sample_questions:
            print(f"  - {q['question_id']}: {q['title']} ({q['grade']}, {q['subject']}, {q['difficulty']})")
        
        cursor.close()
        conn.close()
        
        print("\n✅ 데이터베이스 연결 성공!")
        return True
        
    except Exception as e:
        print(f"\n❌ 데이터베이스 연결 실패: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()
