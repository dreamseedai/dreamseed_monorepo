"""
통합된 문제 표시 시스템
FastAPI + TipTap + MathLive + PostgreSQL 조합으로 기존 PHP 시스템을 완전히 대체
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid
from datetime import datetime
import logging
from math_rendering_system import math_renderer, process_math_content

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DreamSeedAI Integrated Question System",
    description="통합된 문제 표시 및 상호작용 시스템",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

# 데이터베이스 연결 설정
DATABASE_URL = "postgresql://username:password@localhost:5432/dreamseed_db"

def get_db_connection():
    """데이터베이스 연결"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 연결 실패")

# Pydantic 모델들
class QuestionDisplayRequest(BaseModel):
    question_id: Optional[str] = None
    subject: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    keyword: Optional[str] = None
    country: str = "US"  # US 또는 CA

class ProcessedQuestionResponse(BaseModel):
    id: str
    title: str
    content: str
    hint: Optional[str] = None
    solution: Optional[str] = None
    answer: Optional[str] = None
    resources: Optional[str] = None
    answer_type: int
    examples: Optional[List[str]] = None
    metadata: Dict[str, Any]
    math_expressions: List[Dict[str, Any]]
    processed_content: str

class QuestionNavigationResponse(BaseModel):
    current_question: ProcessedQuestionResponse
    next_question_id: Optional[str] = None
    previous_question_id: Optional[str] = None
    total_questions: int
    current_position: int
    navigation_urls: Dict[str, str]

# 메인 문제 표시 페이지
@app.get("/", response_class=HTMLResponse)
async def question_display_page(
    id: Optional[str] = None,
    subject: Optional[str] = None,
    grade: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    keyword: Optional[str] = None,
    country: str = "US"
):
    """문제 표시 메인 페이지"""
    try:
        # HTML 템플릿 로드
        with open("question_display_frontend.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # URL 파라미터를 JavaScript로 전달
        params = {
            "id": id,
            "subject": subject,
            "grade": grade,
            "category": category,
            "level": level,
            "keyword": keyword,
            "country": country
        }
        
        # JavaScript 초기화 코드 삽입
        init_script = f"""
        <script>
            window.initialParams = {json.dumps(params)};
        </script>
        """
        
        html_content = html_content.replace("</head>", f"{init_script}</head>")
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"페이지 로드 오류: {e}")
        return HTMLResponse(content=f"<h1>오류 발생</h1><p>{str(e)}</p>", status_code=500)

# 수학 콘텐츠 처리 API
@app.post("/api/process-math-content")
async def process_math_content_api(request: Dict[str, str]):
    """수학 콘텐츠 처리 API"""
    try:
        content = request.get("content", "")
        processed_content = process_math_content(content)
        expressions = math_renderer.extract_math_expressions(content)
        
        return {
            "original_content": content,
            "processed_content": processed_content,
            "math_expressions": [
                {
                    "original": expr.original,
                    "latex": expr.latex,
                    "type": expr.expression_type,
                    "confidence": expr.confidence
                }
                for expr in expressions
            ]
        }
    except Exception as e:
        logger.error(f"수학 콘텐츠 처리 오류: {e}")
        raise HTTPException(status_code=500, detail="수학 콘텐츠 처리 실패")

# 통합된 문제 조회 API
@app.get("/api/questions/processed/{question_id}", response_model=ProcessedQuestionResponse)
async def get_processed_question(question_id: str):
    """수학 콘텐츠가 처리된 문제 조회"""
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
                    q.ca_topic,
                    q.created_at
                FROM questions q
                LEFT JOIN question_content qc ON q.id = qc.question_id
                WHERE q.id = %s AND q.status = 'active'
            """, (question_id,))
            
            question = cur.fetchone()
            if not question:
                raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다")
            
            # 수학 콘텐츠 처리
            processed_content = process_math_content(question['content'] or "")
            processed_hint = process_math_content(question['hint'] or "") if question['hint'] else None
            processed_solution = process_math_content(question['solution'] or "") if question['solution'] else None
            processed_answer = process_math_content(question['answer'] or "") if question['answer'] else None
            processed_resources = process_math_content(question['resources'] or "") if question['resources'] else None
            
            # 수학 표현식 추출
            all_content = f"{question['content'] or ''} {question['hint'] or ''} {question['solution'] or ''} {question['answer'] or ''} {question['resources'] or ''}"
            math_expressions = math_renderer.extract_math_expressions(all_content)
            
            # 객관식 예시 조회 및 처리
            examples = None
            if question['answer_type'] == 1:
                cur.execute("""
                    SELECT example_text FROM question_examples 
                    WHERE question_id = %s ORDER BY example_order
                """, (question_id,))
                examples = [process_math_content(row['example_text']) for row in cur.fetchall()]
            
            return ProcessedQuestionResponse(
                id=str(question['id']),
                title=question['title'],
                content=processed_content,
                hint=processed_hint,
                solution=processed_solution,
                answer=processed_answer,
                resources=processed_resources,
                answer_type=question['answer_type'],
                examples=examples,
                metadata={
                    "difficulty_score": float(question['difficulty_score']) if question['difficulty_score'] else 0.5,
                    "us_grade_level": question['us_grade_level'],
                    "us_subject": question['us_subject'],
                    "us_topic": question['us_topic'],
                    "ca_grade_level": question['ca_grade_level'],
                    "ca_subject": question['ca_subject'],
                    "ca_topic": question['ca_topic'],
                    "created_at": question['created_at'].isoformat() if question['created_at'] else None
                },
                math_expressions=[
                    {
                        "original": expr.original,
                        "latex": expr.latex,
                        "type": expr.expression_type,
                        "confidence": expr.confidence
                    }
                    for expr in math_expressions
                ],
                processed_content=processed_content
            )
    except Exception as e:
        logger.error(f"처리된 문제 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="문제 조회 실패")
    finally:
        conn.close()

# 네비게이션과 함께 처리된 문제 조회
@app.get("/api/questions/processed", response_model=QuestionNavigationResponse)
async def get_processed_question_with_navigation(
    question_id: Optional[str] = None,
    subject: Optional[str] = None,
    grade: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    keyword: Optional[str] = None,
    country: str = "US"
):
    """네비게이션과 함께 처리된 문제 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 필터 조건 구성
            where_conditions = ["q.status = 'active'"]
            params = []
            
            if subject:
                if country == "US":
                    where_conditions.append("q.us_subject = %s")
                else:
                    where_conditions.append("q.ca_subject = %s")
                params.append(subject)
            
            if grade:
                if country == "US":
                    where_conditions.append("q.us_grade_level = %s")
                else:
                    where_conditions.append("q.ca_grade_level = %s")
                params.append(grade)
            
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
                        q.ca_topic,
                        q.created_at
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
                        q.ca_topic,
                        q.created_at
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
            
            total_questions = cur.fetchone()['total']
            
            # 현재 위치 계산
            cur.execute(f"""
                SELECT COUNT(*) as position FROM questions q
                LEFT JOIN question_content qc ON q.id = qc.question_id
                WHERE {where_clause} AND q.created_at <= (
                    SELECT created_at FROM questions WHERE id = %s
                )
            """, params + [current_question['id']])
            
            current_position = cur.fetchone()['position']
            
            # 수학 콘텐츠 처리
            processed_content = process_math_content(current_question['content'] or "")
            processed_hint = process_math_content(current_question['hint'] or "") if current_question['hint'] else None
            processed_solution = process_math_content(current_question['solution'] or "") if current_question['solution'] else None
            processed_answer = process_math_content(current_question['answer'] or "") if current_question['answer'] else None
            processed_resources = process_math_content(current_question['resources'] or "") if current_question['resources'] else None
            
            # 수학 표현식 추출
            all_content = f"{current_question['content'] or ''} {current_question['hint'] or ''} {current_question['solution'] or ''} {current_question['answer'] or ''} {current_question['resources'] or ''}"
            math_expressions = math_renderer.extract_math_expressions(all_content)
            
            # 객관식 예시 조회 및 처리
            examples = None
            if current_question['answer_type'] == 1:
                cur.execute("""
                    SELECT example_text FROM question_examples 
                    WHERE question_id = %s ORDER BY example_order
                """, (current_question['id'],))
                examples = [process_math_content(row['example_text']) for row in cur.fetchall()]
            
            # 네비게이션 URL 생성
            base_params = {
                "subject": subject,
                "grade": grade,
                "category": category,
                "level": level,
                "keyword": keyword,
                "country": country
            }
            
            navigation_urls = {
                "current": f"/?id={current_question['id']}&" + "&".join([f"{k}={v}" for k, v in base_params.items() if v]),
                "next": f"/?id={next_question_id}&" + "&".join([f"{k}={v}" for k, v in base_params.items() if v]) if next_question_id else None,
                "previous": f"/?id={previous_question_id}&" + "&".join([f"{k}={v}" for k, v in base_params.items() if v]) if previous_question_id else None
            }
            
            return QuestionNavigationResponse(
                current_question=ProcessedQuestionResponse(
                    id=str(current_question['id']),
                    title=current_question['title'],
                    content=processed_content,
                    hint=processed_hint,
                    solution=processed_solution,
                    answer=processed_answer,
                    resources=processed_resources,
                    answer_type=current_question['answer_type'],
                    examples=examples,
                    metadata={
                        "difficulty_score": float(current_question['difficulty_score']) if current_question['difficulty_score'] else 0.5,
                        "us_grade_level": current_question['us_grade_level'],
                        "us_subject": current_question['us_subject'],
                        "us_topic": current_question['us_topic'],
                        "ca_grade_level": current_question['ca_grade_level'],
                        "ca_subject": current_question['ca_subject'],
                        "ca_topic": current_question['ca_topic'],
                        "created_at": current_question['created_at'].isoformat() if current_question['created_at'] else None
                    },
                    math_expressions=[
                        {
                            "original": expr.original,
                            "latex": expr.latex,
                            "type": expr.expression_type,
                            "confidence": expr.confidence
                        }
                        for expr in math_expressions
                    ],
                    processed_content=processed_content
                ),
                next_question_id=next_question_id,
                previous_question_id=previous_question_id,
                total_questions=total_questions,
                current_position=current_position,
                navigation_urls=navigation_urls
            )
    except Exception as e:
        logger.error(f"네비게이션 문제 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="문제 조회 실패")
    finally:
        conn.close()

# 수학 표현식 검증 API
@app.post("/api/validate-math")
async def validate_math_expression_api(request: Dict[str, str]):
    """수학 표현식 검증 API"""
    try:
        expression = request.get("expression", "")
        result = math_renderer.validate_math_expression(expression)
        return result
    except Exception as e:
        logger.error(f"수학 표현식 검증 오류: {e}")
        raise HTTPException(status_code=500, detail="수학 표현식 검증 실패")

# 수학 표현식 미리보기 API
@app.post("/api/math-preview")
async def math_preview_api(request: Dict[str, str]):
    """수학 표현식 미리보기 API"""
    try:
        expression = request.get("expression", "")
        preview_html = math_renderer.get_math_preview(expression)
        return {"preview_html": preview_html}
    except Exception as e:
        logger.error(f"수학 표현식 미리보기 오류: {e}")
        raise HTTPException(status_code=500, detail="수학 표현식 미리보기 실패")

# 기존 API들도 유지 (호환성을 위해)
from question_display_api import (
    save_to_favorites, get_favorites, record_attempt, get_curriculum_standards
)

# API 라우트 등록
app.include_router(save_to_favorites.router, prefix="/api", tags=["favorites"])
app.include_router(get_favorites.router, prefix="/api", tags=["favorites"])
app.include_router(record_attempt.router, prefix="/api", tags=["attempts"])
app.include_router(get_curriculum_standards.router, prefix="/api", tags=["curriculum"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
