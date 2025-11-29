"""
문제 API - mock_api.py에서 마이그레이션
데이터는 backend/app/api/data/questions.json.gz에서 로드
"""

import json
import gzip
from pathlib import Path
from functools import lru_cache
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional

app = FastAPI(
    title="Question API",
    version="2.0.0",
    description="문제 조회 API (mock_api.py 마이그레이션)",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"
QUESTIONS_GZ = DATA_DIR / "questions.json.gz"
QUESTIONS_JSON = DATA_DIR / "questions.json"


@lru_cache(maxsize=1)
def load_questions() -> Dict:
    """문제 데이터 로드 (캐싱)"""
    try:
        # 압축 파일 우선 (9.3MB)
        if QUESTIONS_GZ.exists():
            with gzip.open(
                QUESTIONS_GZ, "rt", encoding="utf-8", errors="surrogatepass"
            ) as f:
                return json.load(f)
        # JSON 파일 (48MB)
        elif QUESTIONS_JSON.exists():
            with open(
                QUESTIONS_JSON, "r", encoding="utf-8", errors="surrogatepass"
            ) as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        return {}


@app.get("/")
def root():
    """API 정보"""
    questions = load_questions()
    return {
        "name": "Question API",
        "version": "2.0.0",
        "total_questions": len(questions),
        "data_source": (
            "questions.json.gz" if QUESTIONS_GZ.exists() else "questions.json"
        ),
        "endpoints": {
            "health": "/health",
            "question": "/questions/{question_id}",
            "list": "/questions",
            "stats": "/stats",
        },
    }


@app.get("/health")
def health():
    """Health check"""
    questions = load_questions()
    return {
        "status": "ok",
        "total_questions": len(questions),
        "data_source": (
            "questions.json.gz" if QUESTIONS_GZ.exists() else "questions.json"
        ),
    }


@app.get("/questions/{question_id}")
def get_question(question_id: str):
    """문제 ID로 조회"""
    questions = load_questions()
    if question_id not in questions:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
    return questions[question_id]


@app.get("/questions")
def list_questions(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(100, ge=1, le=1000, description="페이지 크기"),
    grade: Optional[str] = Query(None, description="학년 필터 (예: G10)"),
    subject: Optional[str] = Query(None, description="과목 필터 (예: M)"),
    original_id: Optional[int] = Query(None, description="원본 ID로 검색"),
):
    """문제 목록 조회 (페이지네이션 및 필터링)"""
    questions = load_questions()

    # original_id로 검색 (기존 호환성)
    if original_id:
        return {k: v for k, v in questions.items() if v.get("id") == original_id}

    # 필터링
    filtered = questions
    if grade:
        filtered = {k: v for k, v in filtered.items() if v.get("que_grade") == grade}
    if subject:
        filtered = {k: v for k, v in filtered.items() if v.get("que_class") == subject}

    # 페이지네이션
    start = (page - 1) * page_size
    end = start + page_size
    items = list(filtered.items())[start:end]

    return {
        "total": len(filtered),
        "page": page,
        "page_size": page_size,
        "data": dict(items),
    }


@app.get("/stats")
def get_stats():
    """통계 정보"""
    questions = load_questions()

    grades = {}
    subjects = {}
    levels = {}

    for q in questions.values():
        grade = q.get("que_grade", "Unknown")
        subject = q.get("que_class", "Unknown")
        level = q.get("que_level", 0)

        grades[grade] = grades.get(grade, 0) + 1
        subjects[subject] = subjects.get(subject, 0) + 1
        levels[level] = levels.get(level, 0) + 1

    return {
        "total_questions": len(questions),
        "by_grade": grades,
        "by_subject": subjects,
        "by_level": levels,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
