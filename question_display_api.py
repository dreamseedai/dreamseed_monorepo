"""
FastAPI 백엔드: 문제 표시 및 상호작용 API
기존 PHP runPopup.php를 FastAPI + PostgreSQL로 변환
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid
from datetime import datetime
import logging
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DreamSeedAI Question Display API",
    description="문제 표시 및 상호작용을 위한 FastAPI 백엔드",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 연결 설정
# 데이터베이스 연결 설정: env 변수 사용, 기본값 제공
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/dreamseed_db")

def get_db_connection():
    """데이터베이스 연결"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 연결 실패")

# Pydantic 모델들
class QuestionRequest(BaseModel):
    question_id: Optional[int] = None
    subject: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    keyword: Optional[str] = None

class QuestionResponse(BaseModel):
    id: str
    title: str
    content: str
    hint: Optional[str] = None
    solution: Optional[str] = None
    answer: Optional[str] = None
    resources: Optional[str] = None
    answer_type: int  # 1: 객관식, 2: 주관식
    examples: Optional[List[str]] = None
    metadata: Dict[str, Any]

class FavoriteRequest(BaseModel):
    question_id: str
    user_id: str
    subject: str
    grade: str
    category: str
    level: str

class NavigationResponse(BaseModel):
    current_question: QuestionResponse
    next_question_id: Optional[str] = None
    previous_question_id: Optional[str] = None
    total_questions: int
    current_position: int

# API 엔드포인트들

@app.get("/api/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str):
    """특정 문제 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 문제 기본 정보 조회
            cur.execute("""
                SELECT 
                    q.id,
                    q.title,
                    qc.question as content,
                    qc.hint,
                    qc.standard_solution as solution,
                    qc.answer,
                    qc.resources,
                    q.answer_type,
                    q.difficulty_score,
                    q.us_grade_level,
                    q.us_subject,
                    q.us_topic,
                    q.ca_grade_level,
                    q.ca_subject,
                    q.ca_topic
                FROM questions q
                LEFT JOIN question_content qc ON q.id = qc.question_id
                WHERE q.id = %s AND q.status = 'active'
            """, (question_id,))
            
            question = cur.fetchone()
            if not question:
                raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다")
            
            # 객관식 예시 조회
            examples = None
            if question['answer_type'] == 1:
                cur.execute("""
                    SELECT example_text FROM question_examples 
                    WHERE question_id = %s ORDER BY example_order
                """, (question_id,))
                examples = [row['example_text'] for row in cur.fetchall()]
            
            return QuestionResponse(
                id=str(question['id']),
                title=question['title'],
                content=question['content'] or "",
                hint=question['hint'],
                solution=question['solution'],
                answer=question['answer'],
                resources=question['resources'],
                answer_type=question['answer_type'],
                examples=examples,
                metadata={
                    "difficulty_score": float(question['difficulty_score']) if question['difficulty_score'] else 0.5,
                    "us_grade_level": question['us_grade_level'],
                    "us_subject": question['us_subject'],
                    "us_topic": question['us_topic'],
                    "ca_grade_level": question['ca_grade_level'],
                    "ca_subject": question['ca_subject'],
                    "ca_topic": question['ca_topic']
                }
            )
    except Exception as e:
        logger.error(f"문제 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="문제 조회 실패")
    finally:
        conn.close()

@app.get("/api/questions", response_model=NavigationResponse)
async def get_question_with_navigation(
    question_id: Optional[str] = None,
    subject: Optional[str] = None,
    grade: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    keyword: Optional[str] = None
):
    """문제와 네비게이션 정보 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 필터 조건 구성
            where_conditions = ["q.status = 'active'"]
            params = []
            
            if subject:
                where_conditions.append("(q.us_subject = %s OR q.ca_subject = %s)")
                params.extend([subject, subject])
            if grade:
                where_conditions.append("(q.us_grade_level = %s OR q.ca_grade_level = %s)")
                params.extend([grade, grade])
            if category:
                where_conditions.append("q.category = %s")
                params.append(category)
            if level:
                where_conditions.append("q.difficulty_level = %s")
                params.append(level)
            if keyword:
                where_conditions.append("(qc.question ILIKE %s OR q.title ILIKE %s)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            where_clause = " AND ".join(where_conditions)
            
            # 현재 문제 조회
            if question_id:
                cur.execute(f"""
                    SELECT 
                        q.id,
                        q.title,
                        qc.question as content,
                        qc.hint,
                        qc.standard_solution as solution,
                        qc.answer,
                        qc.resources,
                        q.answer_type,
                        q.difficulty_score,
                        q.us_grade_level,
                        q.us_subject,
                        q.us_topic,
                        q.ca_grade_level,
                        q.ca_subject,
                        q.ca_topic
                    FROM questions q
                    LEFT JOIN question_content qc ON q.id = qc.question_id
                    WHERE q.id = %s AND {where_clause}
                """, [question_id] + params)
            else:
                # 첫 번째 문제 조회
                cur.execute(f"""
                    SELECT 
                        q.id,
                        q.title,
                        qc.question as content,
                        qc.hint,
                        qc.standard_solution as solution,
                        qc.answer,
                        qc.resources,
                        q.answer_type,
                        q.difficulty_score,
                        q.us_grade_level,
                        q.us_subject,
                        q.us_topic,
                        q.ca_grade_level,
                        q.ca_subject,
                        q.ca_topic
                    FROM questions q
                    LEFT JOIN question_content qc ON q.id = qc.question_id
                    WHERE {where_clause}
                    ORDER BY q.created_at
                    LIMIT 1
                """, params)
            
            current_question = cur.fetchone()
            if not current_question:
                raise HTTPException(status_code=404, detail="조건에 맞는 문제를 찾을 수 없습니다")
            
            # 다음 문제 조회
            cur.execute(f"""
                SELECT q.id FROM questions q
                LEFT JOIN question_content qc ON q.id = qc.question_id
                WHERE {where_clause} AND q.created_at > (
                    SELECT created_at FROM questions WHERE id = %s
                )
                ORDER BY q.created_at
                LIMIT 1
            """, params + [current_question['id']])
            
            next_question = cur.fetchone()
            next_question_id = str(next_question['id']) if next_question else None
            
            # 이전 문제 조회
            cur.execute(f"""
                SELECT q.id FROM questions q
                LEFT JOIN question_content qc ON q.id = qc.question_id
                WHERE {where_clause} AND q.created_at < (
                    SELECT created_at FROM questions WHERE id = %s
                )
                ORDER BY q.created_at DESC
                LIMIT 1
            """, params + [current_question['id']])
            
            previous_question = cur.fetchone()
            previous_question_id = str(previous_question['id']) if previous_question else None
            
            # 전체 문제 수 조회
            cur.execute(f"""
                SELECT COUNT(*) as total FROM questions q
                LEFT JOIN question_content qc ON q.id = qc.question_id
                WHERE {where_clause}
            """, params)
            
            total_row = cur.fetchone() or {}
            total_val = total_row['total'] if isinstance(total_row, dict) and 'total' in total_row else 0
            total_questions = int(total_val or 0)
            
            # 현재 위치 계산
            cur.execute(f"""
                SELECT COUNT(*) as position FROM questions q
                LEFT JOIN question_content qc ON q.id = qc.question_id
                WHERE {where_clause} AND q.created_at <= (
                    SELECT created_at FROM questions WHERE id = %s
                )
            """, params + [current_question['id']])
            
            pos_row = cur.fetchone() or {}
            pos_val = pos_row['position'] if isinstance(pos_row, dict) and 'position' in pos_row else 1
            current_position = int(pos_val or 1)
            
            # 객관식 예시 조회
            examples = None
            if current_question['answer_type'] == 1:
                cur.execute("""
                    SELECT example_text FROM question_examples 
                    WHERE question_id = %s ORDER BY example_order
                """, (current_question['id'],))
                examples = [row['example_text'] for row in cur.fetchall()]
            
            return NavigationResponse(
                current_question=QuestionResponse(
                    id=str(current_question['id']),
                    title=current_question['title'],
                    content=current_question['content'] or "",
                    hint=current_question['hint'],
                    solution=current_question['solution'],
                    answer=current_question['answer'],
                    resources=current_question['resources'],
                    answer_type=current_question['answer_type'],
                    examples=examples,
                    metadata={
                        "difficulty_score": float(current_question['difficulty_score']) if current_question['difficulty_score'] else 0.5,
                        "us_grade_level": current_question['us_grade_level'],
                        "us_subject": current_question['us_subject'],
                        "us_topic": current_question['us_topic'],
                        "ca_grade_level": current_question['ca_grade_level'],
                        "ca_subject": current_question['ca_subject'],
                        "ca_topic": current_question['ca_topic']
                    }
                ),
                next_question_id=next_question_id,
                previous_question_id=previous_question_id,
                total_questions=total_questions,
                current_position=current_position
            )
    except Exception as e:
        logger.error(f"문제 네비게이션 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="문제 조회 실패")
    finally:
        conn.close()

@app.post("/api/favorites")
async def save_to_favorites(favorite: FavoriteRequest):
    """문제를 즐겨찾기에 저장"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO student_favorites (
                    student_id, question_id, subject, grade, category, 
                    level, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (student_id, question_id) DO NOTHING
            """, (
                favorite.user_id,
                favorite.question_id,
                favorite.subject,
                favorite.grade,
                favorite.category,
                favorite.level,
                datetime.now()
            ))
            conn.commit()
            return {"message": "즐겨찾기에 저장되었습니다"}
    except Exception as e:
        logger.error(f"즐겨찾기 저장 오류: {e}")
        raise HTTPException(status_code=500, detail="즐겨찾기 저장 실패")
    finally:
        conn.close()

@app.get("/api/favorites/{user_id}")
async def get_favorites(user_id: str):
    """사용자의 즐겨찾기 목록 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    sf.question_id,
                    sf.subject,
                    sf.grade,
                    sf.category,
                    sf.level,
                    sf.created_at,
                    q.title
                FROM student_favorites sf
                JOIN questions q ON sf.question_id = q.id
                WHERE sf.student_id = %s
                ORDER BY sf.created_at DESC
            """, (user_id,))
            
            favorites = cur.fetchall()
            return [dict(fav) for fav in favorites]
    except Exception as e:
        logger.error(f"즐겨찾기 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="즐겨찾기 조회 실패")
    finally:
        conn.close()

@app.post("/api/attempts")
async def record_attempt(
    question_id: str,
    user_id: str,
    is_correct: bool,
    time_taken_sec: int,
    answer: Optional[str] = None
):
    """문제 풀이 시도 기록"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO question_attempts (
                    question_id, student_id, is_correct, time_taken_sec, 
                    answer, attempted_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                question_id,
                user_id,
                is_correct,
                time_taken_sec,
                answer,
                datetime.now()
            ))
            conn.commit()
            return {"message": "시도 기록이 저장되었습니다"}
    except Exception as e:
        logger.error(f"시도 기록 저장 오류: {e}")
        raise HTTPException(status_code=500, detail="시도 기록 저장 실패")
    finally:
        conn.close()

@app.get("/api/curriculum/standards")
async def get_curriculum_standards(country: str = "US"):
    """교과과정 표준 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT DISTINCT 
                    grade_level, subject, course, topic
                FROM curriculum_standards 
                WHERE country = %s
                ORDER BY grade_level, subject, course, topic
            """, (country,))
            
            standards = cur.fetchall()
            return [dict(std) for std in standards]
    except Exception as e:
        logger.error(f"교과과정 표준 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="교과과정 표준 조회 실패")
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
