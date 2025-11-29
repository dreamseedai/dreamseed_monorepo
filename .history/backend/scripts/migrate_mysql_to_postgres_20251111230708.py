#!/usr/bin/env python3
"""
MySQL에서 PostgreSQL로 문제 데이터 마이그레이션

Source: MySQL mpcstudy_db.tbl_question (18,898 문제)
Target: PostgreSQL dreamseed.problems
"""
import sys
import uuid
from datetime import datetime
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# MySQL 연결 설정
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '0908',
    'database': 'mpcstudy_db',
    'charset': 'utf8mb4'
}

# PostgreSQL 연결 설정
POSTGRES_URL = "postgresql+psycopg2://postgres:DreamSeedAi0908@127.0.0.1:5432/dreamseed"

def get_category_from_codes(cat1, cat2, cat3):
    """MySQL 카테고리 코드를 PostgreSQL 카테고리 문자열로 변환"""
    # 간단한 매핑 (실제 매핑 규칙에 따라 조정 필요)
    category_map = {
        1: "대수",
        2: "기하",
        3: "해석",
        4: "확률/통계",
        5: "수학",
    }
    return category_map.get(cat1, "수학")

def migrate_problems():
    """MySQL에서 PostgreSQL로 문제 마이그레이션"""
    
    # MySQL 연결
    mysql_conn = pymysql.connect(**MYSQL_CONFIG)
    mysql_cursor = mysql_conn.cursor(pymysql.cursors.DictCursor)
    
    # PostgreSQL 연결
    pg_engine = create_engine(POSTGRES_URL)
    
    try:
        # MySQL에서 문제 조회
        mysql_cursor.execute("""
            SELECT 
                que_id,
                que_status,
                que_class,
                que_category1,
                que_category2,
                que_category3,
                que_grade,
                que_level,
                que_en_title,
                que_en_desc,
                que_en_hint,
                que_en_solution,
                que_en_answers,
                que_en_answerm,
                que_answertype,
                que_createddate,
                que_modifieddate
            FROM tbl_question
            WHERE que_status = 1
            ORDER BY que_id
        """)
        
        questions = mysql_cursor.fetchall()
        print(f"✅ MySQL에서 {len(questions)}개 문제 조회 완료")
        
        # PostgreSQL에 삽입
        inserted = 0
        skipped = 0
        
        with pg_engine.connect() as pg_conn:
            for q in questions:
                # 각 문제마다 새 트랜잭션 시작
                trans = pg_conn.begin()
                try:
                    # UUID 생성
                    problem_id = uuid.uuid4()
                    
                    # 카테고리 변환
                    category = get_category_from_codes(
                        q['que_category1'], 
                        q['que_category2'], 
                        q['que_category3']
                    )
                    
                    # 난이도 (문자열로 변환)
                    difficulty = str(min(max(q['que_level'] or 5, 1), 10))
                    
                    # 메타데이터 구성 (JSON 직렬화)
                    import json
                    metadata = {
                        'mysql_id': q['que_id'],
                        'class': q['que_class'] or '',
                        'category1': q['que_category1'] or 0,
                        'category2': q['que_category2'] or 0,
                        'category3': q['que_category3'] or 0,
                        'grade': q['que_grade'] or '',
                        'answer_type': q['que_answertype'] or 0,
                        'correct_answer': q['que_en_answerm'] or '',
                        'answer_choices': q['que_en_answers'] or ''
                    }
                    metadata_json = json.dumps(metadata)
                    
                    # PostgreSQL에 삽입
                    pg_conn.execute(text("""
                        INSERT INTO problems (
                            id, title, description, difficulty, 
                            category, metadata, created_at
                        ) VALUES (
                            :id, :title, :description, :difficulty, :category, 
                            CAST(:metadata AS jsonb), NOW()
                        )
                    """), {
                        'id': str(problem_id),
                        'title': q['que_en_title'] or f"Problem {q['que_id']}",
                        'description': q['que_en_desc'] or "",
                        'difficulty': difficulty,
                        'category': category,
                        'metadata': str(metadata).replace("'", '"')
                    })
                    
                    inserted += 1
                    trans.commit()  # 성공 시 커밋
                    
                    if inserted % 1000 == 0:
                        print(f"  진행 중: {inserted}개 삽입됨...")
                    
                except Exception as e:
                    trans.rollback()  # 실패 시 롤백
                    print(f"  ⚠️  문제 ID {q['que_id']} 건너뜀: {str(e)[:100]}")
                    skipped += 1
                    continue
        
        print(f"\n✅ 마이그레이션 완료!")
        print(f"   - 삽입: {inserted}개")
        print(f"   - 건너뜀: {skipped}개")
        
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        sys.exit(1)
    finally:
        mysql_cursor.close()
        mysql_conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MySQL → PostgreSQL 문제 마이그레이션")
    print("=" * 60)
    
    # 확인
    response = input("\n18,898개 문제를 마이그레이션하시겠습니까? (yes/no): ")
    if response.lower() != 'yes':
        print("취소되었습니다.")
        sys.exit(0)
    
    migrate_problems()
