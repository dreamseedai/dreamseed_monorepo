"""
FastAPI 백엔드: 문제 표시 및 상호작용 API
기존 PHP runPopup.php를 FastAPI + PostgreSQL로 변환
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from typing import Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid
from datetime import datetime
import logging
import os
from shared.reporting import generate_report
import io
import csv

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
USE_SHADOW_BANK = os.getenv("USE_SHADOW_BANK", "false").lower() in ("1","true","yes")

def get_db_connection():
    """데이터베이스 연결"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 연결 실패")


def _table_exists(conn, table_name: str) -> bool:
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
                """,
                (table_name,),
            )
            row = cur.fetchone()
            return bool(row and row[0])
    except Exception:
        return False

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

# Reporting models
class SessionItem(BaseModel):
    id: str | int
    a: float
    b: float
    c: Optional[float] = 0.0
    topic: Optional[str] = None
    correct: bool
    time_spent_sec: Optional[int] = 0
    solution: Optional[str] = None


class ReportRequest(BaseModel):
    session_id: Optional[str] = None
    exam_id: Optional[int] = None
    user_id: Optional[int] = None
    items: List[SessionItem]
    estimator: Optional[str] = "mle"
    prior: Optional[Dict[str, Any]] = None
    scaling: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    theta: float
    se: float
    ci: Dict[str, Any]
    percentile: float
    scaled_score: Optional[int] = None
    topic_breakdown: Dict[str, Dict[str, float]]
    items_review: List[Dict[str, Any]]
    recommendations: List[str]

# API 엔드포인트들

@app.get("/api/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str):
    """특정 문제 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 문제 기본 정보 조회
            # If shadow bank is enabled and exists, prefer IRT params from there
            if USE_SHADOW_BANK and _table_exists(conn, "item_bank_shadow"):
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
                        s.irt_a, s.irt_b, s.irt_c
                    FROM questions q
                    LEFT JOIN question_content qc ON q.id = qc.question_id
                    LEFT JOIN item_bank_shadow s ON s.id::text = q.id::text
                    WHERE q.id = %s AND q.status = 'active'
                """, (question_id,))
            else:
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
                        q.irt_a, q.irt_b, q.irt_c
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
            
            # Prepare IRT params with safe conversion
            _irt_a = question.get('irt_a') if isinstance(question, dict) else None
            _irt_b = question.get('irt_b') if isinstance(question, dict) else None
            _irt_c = question.get('irt_c') if isinstance(question, dict) else None
            irt_a_val = float(_irt_a) if _irt_a is not None else None
            irt_b_val = float(_irt_b) if _irt_b is not None else None
            irt_c_val = float(_irt_c) if _irt_c is not None else None

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
                    "ca_topic": question['ca_topic'],
                    "irt_a": irt_a_val,
                    "irt_b": irt_b_val,
                    "irt_c": irt_c_val
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

@app.post("/api/sessions/{session_id}/report", response_model=ReportResponse)
async def create_session_report(session_id: str, req: ReportRequest):
    """세션 리포트를 생성하고(선택적으로) 요약을 저장합니다.

    - θ, SE/CI, 스케일 점수, 주제별 분석, 추천을 계산합니다.
    - exam_sessions 테이블이 존재하면 세션 요약을 upsert 합니다.
    """
    try:
        payload = {
            "items": [it.dict() for it in req.items],
            "estimator": (req.estimator or "mle").lower(),
            "prior": req.prior or {},
            "scaling": req.scaling or {},
        }
        rep = generate_report(payload)
    except Exception as e:
        logger.error(f"리포트 생성 오류: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # optional persistence
    conn = None
    try:
        conn = get_db_connection()
        if _table_exists(conn, "exam_sessions"):
            with conn.cursor() as cur:
                # Safe extracts with defaults
                theta_val = float(rep.get("theta") or 0.0)
                se_val = float(rep.get("se") or 0.0)
                final_score_val = rep.get("scaled_score")
                final_score_int = int(final_score_val) if final_score_val is not None else None

                cur.execute(
                    """
                    INSERT INTO exam_sessions (session_id, exam_id, user_id, end_time, ability_estimate, standard_error, final_score, completed)
                    VALUES (%s, %s, %s, NOW(), %s, %s, %s, TRUE)
                    ON CONFLICT (session_id)
                    DO UPDATE SET
                        end_time = EXCLUDED.end_time,
                        ability_estimate = EXCLUDED.ability_estimate,
                        standard_error = EXCLUDED.standard_error,
                        final_score = EXCLUDED.final_score,
                        completed = TRUE
                    """,
                    (
                        session_id,
                        req.exam_id,
                        req.user_id,
                        theta_val,
                        se_val,
                        final_score_int,
                    ),
                )
                conn.commit()
        # Save full JSON report if table exists
        if _table_exists(conn, "exam_reports"):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO exam_reports (session_id, exam_id, user_id, report_json)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (session_id)
                    DO UPDATE SET report_json = EXCLUDED.report_json
                    """,
                    (
                        session_id,
                        req.exam_id,
                        req.user_id,
                        json.dumps(rep),
                    ),
                )
                conn.commit()
    except Exception as e:
        logger.warning(f"exam_sessions upsert skipped: {e}")
    finally:
        if conn:
            conn.close()

    return ReportResponse(**rep)  # type: ignore[arg-type]

@app.get("/api/sessions/{session_id}/report", response_model=ReportResponse)
async def get_session_report(session_id: str):
    """Retrieve a previously saved report if available."""
    conn = None
    try:
        conn = get_db_connection()
        if not _table_exists(conn, "exam_reports"):
            raise HTTPException(status_code=404, detail="report not found")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT report_json FROM exam_reports WHERE session_id = %s", (session_id,))
            row = cur.fetchone()
            if not row or not row.get("report_json"):
                raise HTTPException(status_code=404, detail="report not found")
            data = row["report_json"] if isinstance(row["report_json"], dict) else json.loads(row["report_json"])  # type: ignore
            return ReportResponse(**data)  # type: ignore[arg-type]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"리포트 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="리포트 조회 실패")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.post("/api/admin/calibration/preview")
async def calibration_preview(file: UploadFile = File(...), x_admin_key: Optional[str] = None):
    """Parse a diff CSV and return preview metrics for reviewers.

    Expected columns: item_id, old_a, old_b, old_c, new_a, new_b, new_c, delta_a, delta_b, delta_c
    """
    try:
        # Simple header-based auth via environment variable
        required = os.getenv("ADMIN_API_KEY")
        if required and x_admin_key != required:
            raise HTTPException(status_code=403, detail="forbidden")
        content = await file.read()
        f = io.StringIO(content.decode("utf-8"))
        reader = csv.DictReader(f)
        n = 0
        da_sum = db_sum = dc_sum = 0.0
        da_abs = db_abs = dc_abs = 0.0
        flagged = 0
        for row in reader:
            n += 1
            try:
                a = float(row.get("new_a") or 0.0)
                da = float(row.get("delta_a") or 0.0)
                db = float(row.get("delta_b") or 0.0)
                dc = float(row.get("delta_c") or 0.0)
            except Exception:
                continue
            da_sum += da; db_sum += db; dc_sum += dc
            da_abs += abs(da); db_abs += abs(db); dc_abs += abs(dc)
            if a < 0.2 or a < 0:  # low or negative discrimination
                flagged += 1
        if n == 0:
            return {"items_changed": 0, "mean_delta": {"a": 0, "b": 0, "c": 0}, "mean_abs_delta": {"a": 0, "b": 0, "c": 0}, "flagged_items": 0}
        return {
            "items_changed": n,
            "mean_delta": {"a": da_sum / n, "b": db_sum / n, "c": dc_sum / n},
            "mean_abs_delta": {"a": da_abs / n, "b": db_abs / n, "c": dc_abs / n},
            "flagged_items": flagged
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
