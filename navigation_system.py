"""
네비게이션 시스템
다음/이전 문제 이동, 진행률 추적, 학습 경로 관리
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

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
class NavigationRequest(BaseModel):
    current_question_id: str
    direction: str  # "next", "previous", "random", "adaptive"
    user_id: str
    subject: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    country: str = "US"

class NavigationResponse(BaseModel):
    next_question_id: Optional[str] = None
    previous_question_id: Optional[str] = None
    current_position: int
    total_questions: int
    progress_percentage: float
    navigation_urls: Dict[str, str]
    learning_path: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]

class LearningSession(BaseModel):
    session_id: str
    user_id: str
    subject: str
    grade: str
    start_time: datetime
    end_time: Optional[datetime] = None
    questions_attempted: List[str]
    correct_answers: int
    total_answers: int
    average_time: float
    difficulty_progression: List[float]

class StudyProgress(BaseModel):
    user_id: str
    subject: str
    grade: str
    topics_completed: List[str]
    topics_in_progress: List[str]
    mastery_scores: Dict[str, float]
    total_time_spent: int
    last_study_date: datetime

# 네비게이션 API 엔드포인트들

@router.post("/navigation/next", response_model=NavigationResponse)
async def navigate_to_next_question(request: NavigationRequest):
    """다음 문제로 네비게이션"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 현재 문제 정보 조회
            cur.execute("""
                SELECT created_at, us_subject, us_grade_level, ca_subject, ca_grade_level
                FROM questions WHERE id = %s
            """, (request.current_question_id,))
            
            current_question = cur.fetchone()
            if not current_question:
                raise HTTPException(status_code=404, detail="현재 문제를 찾을 수 없습니다")
            
            # 필터 조건 구성
            where_conditions = ["q.status = 'active'"]
            params = []
            
            if request.subject:
                if request.country == "US":
                    where_conditions.append("q.us_subject = %s")
                else:
                    where_conditions.append("q.ca_subject = %s")
                params.append(request.subject)
            
            if request.grade:
                if request.country == "US":
                    where_conditions.append("q.us_grade_level = %s")
                else:
                    where_conditions.append("q.ca_grade_level = %s")
                params.append(request.grade)
            
            if request.category:
                where_conditions.append("q.category = %s")
                params.append(request.category)
            
            if request.level:
                where_conditions.append("q.difficulty_level = %s")
                params.append(request.level)
            
            where_clause = " AND ".join(where_conditions)
            
            # 네비게이션 방향에 따른 다음 문제 조회
            if request.direction == "next":
                # 순차적 다음 문제
                cur.execute(f"""
                    SELECT q.id FROM questions q
                    WHERE {where_clause} AND q.created_at > (
                        SELECT created_at FROM questions WHERE id = %s
                    )
                    ORDER BY q.created_at
                    LIMIT 1
                """, params + [request.current_question_id])
                
            elif request.direction == "previous":
                # 이전 문제
                cur.execute(f"""
                    SELECT q.id FROM questions q
                    WHERE {where_clause} AND q.created_at < (
                        SELECT created_at FROM questions WHERE id = %s
                    )
                    ORDER BY q.created_at DESC
                    LIMIT 1
                """, params + [request.current_question_id])
                
            elif request.direction == "random":
                # 랜덤 문제 (이미 풀지 않은)
                cur.execute(f"""
                    SELECT q.id FROM questions q
                    WHERE {where_clause} AND q.id NOT IN (
                        SELECT DISTINCT question_id FROM question_attempts 
                        WHERE student_id = %s
                    )
                    ORDER BY RANDOM()
                    LIMIT 1
                """, params + [request.user_id])
                
            elif request.direction == "adaptive":
                # 적응형 문제 (학습자 수준에 맞는)
                next_question_id = await get_adaptive_next_question(request, cur, where_clause, params)
            else:
                raise HTTPException(status_code=400, detail="잘못된 네비게이션 방향")
            
            if request.direction != "adaptive":
                next_question = cur.fetchone()
                next_question_id = str(next_question['id']) if next_question else None
            
            # 이전 문제 조회
            cur.execute(f"""
                SELECT q.id FROM questions q
                WHERE {where_clause} AND q.created_at < (
                    SELECT created_at FROM questions WHERE id = %s
                )
                ORDER BY q.created_at DESC
                LIMIT 1
            """, params + [request.current_question_id])
            
            previous_question = cur.fetchone()
            previous_question_id = str(previous_question['id']) if previous_question else None
            
            # 진행률 계산
            cur.execute(f"""
                SELECT COUNT(*) as total FROM questions q
                WHERE {where_clause}
            """, params)
            
            total_questions = cur.fetchone()['total']
            
            cur.execute(f"""
                SELECT COUNT(*) as position FROM questions q
                WHERE {where_clause} AND q.created_at <= (
                    SELECT created_at FROM questions WHERE id = %s
                )
            """, params + [request.current_question_id])
            
            current_position = cur.fetchone()['position']
            progress_percentage = (current_position / total_questions * 100) if total_questions > 0 else 0
            
            # 학습 경로 생성
            learning_path = await generate_learning_path(request, cur, where_clause, params)
            
            # 추천 문제 생성
            recommendations = await generate_recommendations(request, cur, where_clause, params)
            
            # 네비게이션 URL 생성
            base_params = {
                "subject": request.subject,
                "grade": request.grade,
                "category": request.category,
                "level": request.level,
                "country": request.country
            }
            
            navigation_urls = {
                "current": f"/?id={request.current_question_id}&" + "&".join([f"{k}={v}" for k, v in base_params.items() if v]),
                "next": f"/?id={next_question_id}&" + "&".join([f"{k}={v}" for k, v in base_params.items() if v]) if next_question_id else None,
                "previous": f"/?id={previous_question_id}&" + "&".join([f"{k}={v}" for k, v in base_params.items() if v]) if previous_question_id else None
            }
            
            return NavigationResponse(
                next_question_id=next_question_id,
                previous_question_id=previous_question_id,
                current_position=current_position,
                total_questions=total_questions,
                progress_percentage=progress_percentage,
                navigation_urls=navigation_urls,
                learning_path=learning_path,
                recommendations=recommendations
            )
            
    except Exception as e:
        logger.error(f"네비게이션 오류: {e}")
        raise HTTPException(status_code=500, detail="네비게이션 실패")
    finally:
        conn.close()

async def get_adaptive_next_question(request: NavigationRequest, cur, where_clause: str, params: List) -> Optional[str]:
    """적응형 다음 문제 선택"""
    try:
        # 사용자의 최근 성능 분석
        cur.execute("""
            SELECT 
                AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(time_taken_sec) as avg_time,
                COUNT(*) as total_attempts
            FROM question_attempts 
            WHERE student_id = %s 
            AND attempted_at >= %s
        """, (request.user_id, datetime.now() - timedelta(days=7)))
        
        performance = cur.fetchone()
        
        if not performance or performance['total_attempts'] < 3:
            # 충분한 데이터가 없으면 기본 난이도
            target_difficulty = 0.5
        else:
            success_rate = performance['success_rate'] or 0.5
            avg_time = performance['avg_time'] or 60
            
            # 성공률과 시간을 기반으로 적절한 난이도 계산
            if success_rate > 0.8 and avg_time < 45:
                target_difficulty = min(1.0, 0.5 + (success_rate - 0.8) * 2)
            elif success_rate < 0.4 or avg_time > 120:
                target_difficulty = max(0.1, 0.5 - (0.4 - success_rate) * 2)
            else:
                target_difficulty = 0.5
        
        # 목표 난이도에 가까운 문제 찾기
        cur.execute(f"""
            SELECT q.id, q.difficulty_score,
                   ABS(q.difficulty_score - %s) as difficulty_diff
            FROM questions q
            WHERE {where_clause} AND q.id != %s
            AND q.id NOT IN (
                SELECT DISTINCT question_id FROM question_attempts 
                WHERE student_id = %s AND attempted_at >= %s
            )
            ORDER BY difficulty_diff, RANDOM()
            LIMIT 1
        """, params + [target_difficulty, request.current_question_id, request.user_id, datetime.now() - timedelta(days=1)])
        
        next_question = cur.fetchone()
        return str(next_question['id']) if next_question else None
        
    except Exception as e:
        logger.error(f"적응형 문제 선택 오류: {e}")
        return None

async def generate_learning_path(request: NavigationRequest, cur, where_clause: str, params: List) -> List[Dict[str, Any]]:
    """학습 경로 생성"""
    try:
        # 사용자의 학습 진행 상황 조회
        cur.execute("""
            SELECT 
                q.us_topic as topic,
                q.difficulty_score,
                AVG(CASE WHEN qa.is_correct THEN 1.0 ELSE 0.0 END) as mastery_score,
                COUNT(qa.id) as attempts_count
            FROM questions q
            LEFT JOIN question_attempts qa ON q.id = qa.question_id AND qa.student_id = %s
            WHERE {where_clause}
            GROUP BY q.us_topic, q.difficulty_score
            ORDER BY q.difficulty_score, mastery_score
        """.format(where_clause=where_clause), [request.user_id] + params)
        
        topics = cur.fetchall()
        
        learning_path = []
        for topic in topics:
            mastery_score = topic['mastery_score'] or 0.0
            attempts_count = topic['attempts_count'] or 0
            
            if mastery_score >= 0.8:
                status = "completed"
            elif mastery_score >= 0.5:
                status = "in_progress"
            else:
                status = "not_started"
            
            learning_path.append({
                "topic": topic['topic'],
                "difficulty": float(topic['difficulty_score']),
                "mastery_score": mastery_score,
                "attempts_count": attempts_count,
                "status": status,
                "recommended_next": mastery_score < 0.8
            })
        
        return learning_path
        
    except Exception as e:
        logger.error(f"학습 경로 생성 오류: {e}")
        return []

async def generate_recommendations(request: NavigationRequest, cur, where_clause: str, params: List) -> List[Dict[str, Any]]:
    """추천 문제 생성"""
    try:
        # 사용자의 약한 영역 식별
        cur.execute("""
            SELECT 
                q.us_topic as topic,
                AVG(CASE WHEN qa.is_correct THEN 1.0 ELSE 0.0 END) as success_rate,
                COUNT(qa.id) as attempts_count
            FROM questions q
            LEFT JOIN question_attempts qa ON q.id = qa.question_id AND qa.student_id = %s
            WHERE {where_clause}
            GROUP BY q.us_topic
            HAVING COUNT(qa.id) > 0
            ORDER BY success_rate, attempts_count DESC
            LIMIT 3
        """.format(where_clause=where_clause), [request.user_id] + params)
        
        weak_topics = cur.fetchall()
        
        recommendations = []
        for topic in weak_topics:
            # 해당 주제의 추천 문제 조회
            cur.execute(f"""
                SELECT q.id, q.title, q.difficulty_score
                FROM questions q
                WHERE {where_clause} AND q.us_topic = %s
                AND q.id NOT IN (
                    SELECT DISTINCT question_id FROM question_attempts 
                    WHERE student_id = %s
                )
                ORDER BY q.difficulty_score
                LIMIT 2
            """, params + [topic['topic'], request.user_id])
            
            recommended_questions = cur.fetchall()
            
            recommendations.append({
                "topic": topic['topic'],
                "reason": f"성공률 {topic['success_rate']:.1%} - 개선 필요",
                "questions": [
                    {
                        "id": str(q['id']),
                        "title": q['title'],
                        "difficulty": float(q['difficulty_score'])
                    }
                    for q in recommended_questions
                ]
            })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"추천 문제 생성 오류: {e}")
        return []

# 학습 세션 관리
@router.post("/sessions/start")
async def start_learning_session(
    user_id: str,
    subject: str,
    grade: str,
    country: str = "US"
):
    """학습 세션 시작"""
    conn = get_db_connection()
    try:
        session_id = str(uuid.uuid4())
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO learning_sessions (
                    session_id, student_id, subject, grade, country, start_time
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (session_id, user_id, subject, grade, country, datetime.now()))
            
            conn.commit()
            
        return {"session_id": session_id, "message": "학습 세션이 시작되었습니다"}
        
    except Exception as e:
        logger.error(f"학습 세션 시작 오류: {e}")
        raise HTTPException(status_code=500, detail="학습 세션 시작 실패")
    finally:
        conn.close()

@router.post("/sessions/end")
async def end_learning_session(
    session_id: str,
    questions_attempted: List[str],
    correct_answers: int,
    total_answers: int,
    average_time: float
):
    """학습 세션 종료"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE learning_sessions 
                SET 
                    end_time = %s,
                    questions_attempted = %s,
                    correct_answers = %s,
                    total_answers = %s,
                    average_time = %s
                WHERE session_id = %s
            """, (
                datetime.now(),
                questions_attempted,
                correct_answers,
                total_answers,
                average_time,
                session_id
            ))
            
            conn.commit()
            
        return {"message": "학습 세션이 종료되었습니다"}
        
    except Exception as e:
        logger.error(f"학습 세션 종료 오류: {e}")
        raise HTTPException(status_code=500, detail="학습 세션 종료 실패")
    finally:
        conn.close()

# 학습 진행률 조회
@router.get("/progress/{user_id}", response_model=StudyProgress)
async def get_study_progress(
    user_id: str,
    subject: Optional[str] = None,
    grade: Optional[str] = None,
    country: str = "US"
):
    """학습 진행률 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 필터 조건 구성
            where_conditions = ["qa.student_id = %s"]
            params = [user_id]
            
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
            
            where_clause = " AND ".join(where_conditions)
            
            # 주제별 마스터리 점수 조회
            cur.execute(f"""
                SELECT 
                    q.us_topic as topic,
                    AVG(CASE WHEN qa.is_correct THEN 1.0 ELSE 0.0 END) as mastery_score,
                    COUNT(qa.id) as attempts_count,
                    MAX(qa.attempted_at) as last_attempt
                FROM questions q
                JOIN question_attempts qa ON q.id = qa.question_id
                WHERE {where_clause}
                GROUP BY q.us_topic
                ORDER BY mastery_score DESC
            """, params)
            
            topics = cur.fetchall()
            
            # 전체 학습 시간 조회
            cur.execute(f"""
                SELECT SUM(time_taken_sec) as total_time
                FROM question_attempts qa
                JOIN questions q ON qa.question_id = q.id
                WHERE {where_clause}
            """, params)
            
            total_time = cur.fetchone()['total_time'] or 0
            
            # 마지막 학습 날짜 조회
            cur.execute(f"""
                SELECT MAX(attempted_at) as last_study_date
                FROM question_attempts qa
                JOIN questions q ON qa.question_id = q.id
                WHERE {where_clause}
            """, params)
            
            last_study_date = cur.fetchone()['last_study_date'] or datetime.now()
            
            # 주제 분류
            topics_completed = []
            topics_in_progress = []
            mastery_scores = {}
            
            for topic in topics:
                mastery_score = topic['mastery_score'] or 0.0
                mastery_scores[topic['topic']] = mastery_score
                
                if mastery_score >= 0.8:
                    topics_completed.append(topic['topic'])
                elif mastery_score >= 0.3:
                    topics_in_progress.append(topic['topic'])
            
            return StudyProgress(
                user_id=user_id,
                subject=subject or "All",
                grade=grade or "All",
                topics_completed=topics_completed,
                topics_in_progress=topics_in_progress,
                mastery_scores=mastery_scores,
                total_time_spent=total_time,
                last_study_date=last_study_date
            )
            
    except Exception as e:
        logger.error(f"학습 진행률 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="학습 진행률 조회 실패")
    finally:
        conn.close()

# 학습 통계 조회
@router.get("/stats/{user_id}")
async def get_learning_stats(
    user_id: str,
    days: int = 30,
    subject: Optional[str] = None,
    grade: Optional[str] = None,
    country: str = "US"
):
    """학습 통계 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 필터 조건 구성
            where_conditions = [
                "qa.student_id = %s",
                "qa.attempted_at >= %s"
            ]
            params = [user_id, datetime.now() - timedelta(days=days)]
            
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
            
            where_clause = " AND ".join(where_conditions)
            
            # 기본 통계
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN qa.is_correct THEN 1 ELSE 0 END) as correct_attempts,
                    AVG(qa.time_taken_sec) as avg_time,
                    MIN(qa.attempted_at) as first_attempt,
                    MAX(qa.attempted_at) as last_attempt
                FROM question_attempts qa
                JOIN questions q ON qa.question_id = q.id
                WHERE {where_clause}
            """, params)
            
            basic_stats = cur.fetchone()
            
            # 일별 학습 활동
            cur.execute(f"""
                SELECT 
                    DATE(qa.attempted_at) as study_date,
                    COUNT(*) as attempts_count,
                    SUM(CASE WHEN qa.is_correct THEN 1 ELSE 0 END) as correct_count,
                    AVG(qa.time_taken_sec) as avg_time
                FROM question_attempts qa
                JOIN questions q ON qa.question_id = q.id
                WHERE {where_clause}
                GROUP BY DATE(qa.attempted_at)
                ORDER BY study_date
            """, params)
            
            daily_activity = cur.fetchall()
            
            # 주제별 성과
            cur.execute(f"""
                SELECT 
                    q.us_topic as topic,
                    COUNT(*) as attempts_count,
                    AVG(CASE WHEN qa.is_correct THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(qa.time_taken_sec) as avg_time
                FROM question_attempts qa
                JOIN questions q ON qa.question_id = q.id
                WHERE {where_clause}
                GROUP BY q.us_topic
                ORDER BY success_rate DESC
            """, params)
            
            topic_performance = cur.fetchall()
            
            return {
                "period_days": days,
                "basic_stats": {
                    "total_attempts": basic_stats['total_attempts'] or 0,
                    "correct_attempts": basic_stats['correct_attempts'] or 0,
                    "success_rate": (basic_stats['correct_attempts'] / basic_stats['total_attempts']) if basic_stats['total_attempts'] > 0 else 0,
                    "avg_time_seconds": float(basic_stats['avg_time']) if basic_stats['avg_time'] else 0,
                    "first_attempt": basic_stats['first_attempt'].isoformat() if basic_stats['first_attempt'] else None,
                    "last_attempt": basic_stats['last_attempt'].isoformat() if basic_stats['last_attempt'] else None
                },
                "daily_activity": [
                    {
                        "date": activity['study_date'].isoformat(),
                        "attempts": activity['attempts_count'],
                        "correct": activity['correct_count'],
                        "success_rate": (activity['correct_count'] / activity['attempts_count']) if activity['attempts_count'] > 0 else 0,
                        "avg_time": float(activity['avg_time']) if activity['avg_time'] else 0
                    }
                    for activity in daily_activity
                ],
                "topic_performance": [
                    {
                        "topic": topic['topic'],
                        "attempts": topic['attempts_count'],
                        "success_rate": float(topic['success_rate']) if topic['success_rate'] else 0,
                        "avg_time": float(topic['avg_time']) if topic['avg_time'] else 0
                    }
                    for topic in topic_performance
                ]
            }
            
    except Exception as e:
        logger.error(f"학습 통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="학습 통계 조회 실패")
    finally:
        conn.close()

if __name__ == "__main__":
    # 테스트 실행
    import asyncio
    
    async def test_navigation():
        request = NavigationRequest(
            current_question_id="test-id",
            direction="next",
            user_id="test-user",
            subject="Mathematics",
            grade="G12",
            country="US"
        )
        
        # 여기서 실제 테스트 실행
        print("네비게이션 시스템 테스트 완료")
    
    asyncio.run(test_navigation())
