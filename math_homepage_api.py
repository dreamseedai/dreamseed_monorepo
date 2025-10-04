#!/usr/bin/env python3
"""
수학 문제 전용 홈페이지 API
기존 mpcstudy.com의 study-new.php를 FastAPI로 변환
수학(M) 문제만 표시하도록 구현
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import json

app = FastAPI(
    title="DreamSeedAI Math Homepage API",
    description="수학 문제 전용 홈페이지 API - 기존 mpcstudy.com study-new.php 변환",
    version="1.0.0",
)

# CORS 설정
from fastapi.middleware.cors import CORSMiddleware
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
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="dreamseed_db",
            user="dreamseed_user",
            password="password",
            cursor_factory=RealDictCursor
        )
        yield conn
    finally:
        if conn:
            conn.close()

# Pydantic 모델들
class GradeSelection(BaseModel):
    grade: str = Field(..., description="학년 (G06-G12, SAT, AP, U01)")
    subject: str = Field(default="M", description="과목 (M=수학만 지원)")

class CategoryResponse(BaseModel):
    category_id: str
    category_name: str
    question_count: int
    depth: int

class QuestionListRequest(BaseModel):
    grade: str
    subject: str = "M"
    category_id: Optional[str] = None
    level: str = "A"
    question_count: int = 10
    keyword: Optional[str] = None
    sequence_id: Optional[str] = None

# 수학 전용 홈페이지 HTML
MATH_HOMEPAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DreamSeedAI - Math Problems</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.6.0/dist/jquery.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        .grade-card {
            transition: transform 0.3s ease;
            cursor: pointer;
        }
        .grade-card:hover {
            transform: scale(1.05);
        }
        .subject-table {
            margin-top: 2rem;
        }
        .category-section {
            margin-top: 2rem;
            display: none;
        }
        .category-item {
            padding: 10px;
            border: 1px solid #ddd;
            margin: 5px 0;
            border-radius: 5px;
            background: #f8f9fa;
        }
        .category-item:hover {
            background: #e9ecef;
        }
        .search-section {
            margin-top: 3rem;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="text-center mb-5">
            <h1 class="display-4">DreamSeedAI</h1>
            <h2 class="text-muted">Mathematics Problems</h2>
            <p class="lead">Choose your grade to start solving math problems</p>
        </div>

        <!-- Grade Selection -->
        <div class="row mb-5">
            <div class="col-12">
                <h3 class="text-center mb-4">Choose Your Grade</h3>
                <div class="row">
                    <div class="col-md-2 col-sm-4 col-6 mb-3">
                        <div class="card grade-card text-center" onclick="selectGrade('G06')">
                            <div class="card-body">
                                <h5 class="card-title">Grade 6</h5>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-6 mb-3">
                        <div class="card grade-card text-center" onclick="selectGrade('G07')">
                            <div class="card-body">
                                <h5 class="card-title">Grade 7</h5>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-6 mb-3">
                        <div class="card grade-card text-center" onclick="selectGrade('G08')">
                            <div class="card-body">
                                <h5 class="card-title">Grade 8</h5>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-6 mb-3">
                        <div class="card grade-card text-center" onclick="selectGrade('G09')">
                            <div class="card-body">
                                <h5 class="card-title">Grade 9</h5>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-6 mb-3">
                        <div class="card grade-card text-center" onclick="selectGrade('G10')">
                            <div class="card-body">
                                <h5 class="card-title">Grade 10</h5>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-6 mb-3">
                        <div class="card grade-card text-center" onclick="selectGrade('G11')">
                            <div class="card-body">
                                <h5 class="card-title">Grade 11</h5>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-6 mb-3">
                        <div class="card grade-card text-center" onclick="selectGrade('G12')">
                            <div class="card-body">
                                <h5 class="card-title">Grade 12</h5>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-6 mb-3">
                        <div class="card grade-card text-center" onclick="selectGrade('SAT')">
                            <div class="card-body">
                                <h5 class="card-title">SAT</h5>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-4 col-6 mb-3">
                        <div class="card grade-card text-center" onclick="selectGrade('AP')">
                            <div class="card-body">
                                <h5 class="card-title">AP</h5>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Subject Selection (Math Only) -->
        <div class="subject-table" id="subjectTable" style="display: none;">
            <div class="row">
                <div class="col-12">
                    <h3 class="text-center mb-4">Select Subject</h3>
                    <div class="table-responsive">
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th>Grade</th>
                                    <th>Mathematics</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong id="selectedGrade">-</strong></td>
                                    <td class="text-center">
                                        <input type="radio" class="form-check-input" name="subject" value="M" checked>
                                        <label class="form-check-label ms-2">Mathematics</label>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="text-center mt-3">
                        <button class="btn btn-primary" onclick="loadCategories()">Load Categories</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Categories -->
        <div class="category-section" id="categorySection">
            <div class="row">
                <div class="col-12">
                    <h3 class="text-center mb-4">Select Category</h3>
                    <div id="categoryList"></div>
                </div>
            </div>
        </div>

        <!-- Search Section -->
        <div class="search-section">
            <div class="row">
                <div class="col-12">
                    <h4 class="text-center mb-4">Search by Keyword or Sequence ID</h4>
                    <form id="searchForm">
                        <div class="row">
                            <div class="col-md-4">
                                <select class="form-select" id="searchType">
                                    <option value="keyword">Keyword</option>
                                    <option value="sequence">Sequence ID</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <input type="text" class="form-control" id="searchInput" placeholder="Enter keyword or sequence ID">
                            </div>
                            <div class="col-md-2">
                                <button type="submit" class="btn btn-primary w-100">Search</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedGrade = '';
        let selectedSubject = 'M';

        function selectGrade(grade) {
            selectedGrade = grade;
            document.getElementById('selectedGrade').textContent = grade;
            document.getElementById('subjectTable').style.display = 'block';
            document.getElementById('categorySection').style.display = 'none';
            
            // Remove previous selections
            document.querySelectorAll('.grade-card').forEach(card => {
                card.classList.remove('border-primary');
            });
            
            // Highlight selected grade
            event.target.closest('.grade-card').classList.add('border-primary');
        }

        async function loadCategories() {
            if (!selectedGrade) {
                alert('Please select a grade first');
                return;
            }

            try {
                const response = await fetch(`/api/math/categories?grade=${selectedGrade}&subject=${selectedSubject}`);
                const categories = await response.json();
                
                displayCategories(categories);
                document.getElementById('categorySection').style.display = 'block';
            } catch (error) {
                console.error('Error loading categories:', error);
                alert('Error loading categories');
            }
        }

        function displayCategories(categories) {
            const categoryList = document.getElementById('categoryList');
            let html = '';
            
            categories.forEach(category => {
                html += `
                    <div class="category-item d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${category.category_name}</strong>
                            <span class="text-muted ms-2">(${category.question_count} questions)</span>
                        </div>
                        <button class="btn btn-sm btn-outline-primary" onclick="viewQuestions('${category.category_id}')">
                            View Questions
                        </button>
                    </div>
                `;
            });
            
            categoryList.innerHTML = html;
        }

        function viewQuestions(categoryId) {
            const params = new URLSearchParams({
                grade: selectedGrade,
                subject: selectedSubject,
                category_id: categoryId,
                level: 'A',
                question_count: '10'
            });
            
            window.location.href = `/api/math/questions?${params.toString()}`;
        }

        document.getElementById('searchForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const searchType = document.getElementById('searchType').value;
            const searchInput = document.getElementById('searchInput').value;
            
            if (!searchInput.trim()) {
                alert('Please enter a search term');
                return;
            }
            
            const params = new URLSearchParams({
                grade: selectedGrade || 'G09',
                subject: selectedSubject
            });
            
            if (searchType === 'keyword') {
                params.append('keyword', searchInput);
            } else {
                params.append('sequence_id', searchInput);
            }
            
            window.location.href = `/api/math/questions?${params.toString()}`;
        });

        // Auto-select from URL parameters
        document.addEventListener('DOMContentLoaded', function() {
            const urlParams = new URLSearchParams(window.location.search);
            const grade = urlParams.get('grade');
            const subject = urlParams.get('subject');
            
            if (grade) {
                selectGrade(grade);
                if (subject) {
                    selectedSubject = subject;
                }
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def math_homepage():
    """수학 전용 홈페이지"""
    return MATH_HOMEPAGE_HTML

@app.get("/api/math/categories")
async def get_math_categories(
    grade: str = Query(..., description="학년 (G06-G12, SAT, AP, U01)"),
    subject: str = Query(default="M", description="과목 (M=수학만 지원)")
):
    """수학 카테고리 조회"""
    if subject != "M":
        raise HTTPException(status_code=400, detail="Only Mathematics (M) is supported")
    
    # Mock data for demonstration
    # 실제 구현에서는 데이터베이스에서 조회
    mock_categories = {
        "G06": [
            {"category_id": "G06M001", "category_name": "Basic Arithmetic", "question_count": 45, "depth": 2},
            {"category_id": "G06M002", "category_name": "Fractions and Decimals", "question_count": 38, "depth": 2},
            {"category_id": "G06M003", "category_name": "Geometry Basics", "question_count": 32, "depth": 2},
        ],
        "G07": [
            {"category_id": "G07M001", "category_name": "Algebra Introduction", "question_count": 52, "depth": 2},
            {"category_id": "G07M002", "category_name": "Linear Equations", "question_count": 41, "depth": 2},
            {"category_id": "G07M003", "category_name": "Geometry", "question_count": 35, "depth": 2},
        ],
        "G08": [
            {"category_id": "G08M001", "category_name": "Quadratic Equations", "question_count": 48, "depth": 2},
            {"category_id": "G08M002", "category_name": "Functions", "question_count": 44, "depth": 2},
            {"category_id": "G08M003", "category_name": "Statistics", "question_count": 29, "depth": 2},
        ],
        "G09": [
            {"category_id": "G09M001", "category_name": "Advanced Algebra", "question_count": 56, "depth": 2},
            {"category_id": "G09M002", "category_name": "Trigonometry", "question_count": 42, "depth": 2},
            {"category_id": "G09M003", "category_name": "Coordinate Geometry", "question_count": 38, "depth": 2},
        ],
        "G10": [
            {"category_id": "G10M001", "category_name": "Pre-Calculus", "question_count": 61, "depth": 2},
            {"category_id": "G10M002", "category_name": "Advanced Functions", "question_count": 47, "depth": 2},
            {"category_id": "G10M003", "category_name": "Data Management", "question_count": 33, "depth": 2},
        ],
        "G11": [
            {"category_id": "G11M001", "category_name": "Calculus Introduction", "question_count": 58, "depth": 2},
            {"category_id": "G11M002", "category_name": "Vectors", "question_count": 45, "depth": 2},
            {"category_id": "G11M003", "category_name": "Probability", "question_count": 39, "depth": 2},
        ],
        "G12": [
            {"category_id": "G12M001", "category_name": "Advanced Calculus", "question_count": 64, "depth": 2},
            {"category_id": "G12M002", "category_name": "Linear Algebra", "question_count": 52, "depth": 2},
            {"category_id": "G12M003", "category_name": "Statistics and Probability", "question_count": 41, "depth": 2},
        ],
        "SAT": [
            {"category_id": "SATM001", "category_name": "SAT Math - Heart of Algebra", "question_count": 78, "depth": 2},
            {"category_id": "SATM002", "category_name": "SAT Math - Problem Solving", "question_count": 65, "depth": 2},
            {"category_id": "SATM003", "category_name": "SAT Math - Passport to Advanced Math", "question_count": 58, "depth": 2},
        ],
        "AP": [
            {"category_id": "APM001", "category_name": "AP Calculus AB", "question_count": 89, "depth": 2},
            {"category_id": "APM002", "category_name": "AP Calculus BC", "question_count": 95, "depth": 2},
            {"category_id": "APM003", "category_name": "AP Statistics", "question_count": 72, "depth": 2},
        ]
    }
    
    categories = mock_categories.get(grade, [])
    
    if not categories:
        raise HTTPException(status_code=404, detail=f"No categories found for grade {grade}")
    
    return categories

@app.get("/api/math/questions")
async def get_math_questions(
    grade: str = Query(..., description="학년"),
    subject: str = Query(default="M", description="과목"),
    category_id: Optional[str] = Query(None, description="카테고리 ID"),
    level: str = Query(default="A", description="난이도"),
    question_count: int = Query(default=10, description="문제 수"),
    keyword: Optional[str] = Query(None, description="키워드 검색"),
    sequence_id: Optional[str] = Query(None, description="시퀀스 ID")
):
    """수학 문제 목록 조회"""
    if subject != "M":
        raise HTTPException(status_code=400, detail="Only Mathematics (M) is supported")
    
    # Mock data for demonstration - Grade 11 specific questions
    mock_questions = [
        {
            "question_id": "G11Q001",
            "title": "Quadratic Equation Solving",
            "content": "Solve the quadratic equation: x² - 5x + 6 = 0",
            "difficulty": "Medium",
            "category": "G11M001",  # Advanced Algebra
            "category_name": "Advanced Algebra",
            "grade": grade,
            "subject": subject
        },
        {
            "question_id": "G11Q002", 
            "title": "Linear Function Graph",
            "content": "Graph the linear function: y = 2x + 3",
            "difficulty": "Easy",
            "category": "G11M001",  # Advanced Algebra
            "category_name": "Advanced Algebra",
            "grade": grade,
            "subject": subject
        },
        {
            "question_id": "G11Q003",
            "title": "Trigonometric Identity",
            "content": "Prove the identity: sin²θ + cos²θ = 1",
            "difficulty": "Hard",
            "category": "G11M002",  # Trigonometry
            "category_name": "Trigonometry",
            "grade": grade,
            "subject": subject
        },
        {
            "question_id": "G11Q004",
            "title": "Calculus Introduction",
            "content": "Find the derivative of f(x) = x³ + 2x² - 5x + 1",
            "difficulty": "Hard",
            "category": "G11M001",  # Advanced Algebra
            "category_name": "Advanced Algebra",
            "grade": grade,
            "subject": subject
        },
        {
            "question_id": "G11Q005",
            "title": "Vector Operations",
            "content": "Find the magnitude of vector v = (3, 4, 5)",
            "difficulty": "Medium",
            "category": "G11M002",  # Trigonometry
            "category_name": "Trigonometry",
            "grade": grade,
            "subject": subject
        }
    ]
    
    # 필터링 로직 (실제 구현에서는 데이터베이스 쿼리)
    filtered_questions = mock_questions
    
    if category_id:
        filtered_questions = [q for q in filtered_questions if q["category"] == category_id]
    
    if keyword:
        filtered_questions = [q for q in filtered_questions if keyword.lower() in q["title"].lower()]
    
    if sequence_id:
        filtered_questions = [q for q in filtered_questions if q["question_id"] == sequence_id]
    
    # 문제 수 제한
    filtered_questions = filtered_questions[:question_count]
    
    return {
        "total_count": len(filtered_questions),
        "questions": filtered_questions,
        "filters": {
            "grade": grade,
            "subject": subject,
            "category_id": category_id,
            "level": level,
            "keyword": keyword,
            "sequence_id": sequence_id
        }
    }

@app.get("/api/math/question/{question_id}")
async def get_math_question(question_id: str):
    """특정 수학 문제 조회"""
    # Mock data for demonstration
    mock_question = {
        "question_id": question_id,
        "title": "Quadratic Equation Solving",
        "content": """
        <p>Solve the following quadratic equation:</p>
        <math><msup><mi>x</mi><mn>2</mn></msup><mo>-</mo><mn>5</mn><mi>x</mi><mo>+</mo><mn>6</mn><mo>=</mo><mn>0</mn></math>
        <p>Show your work step by step.</p>
        """,
        "hint": "Use the quadratic formula or factoring method.",
        "solution": """
        <p>Using factoring method:</p>
        <p>x² - 5x + 6 = 0</p>
        <p>(x - 2)(x - 3) = 0</p>
        <p>Therefore: x = 2 or x = 3</p>
        """,
        "answer": "x = 2, 3",
        "difficulty": "Medium",
        "category": "Algebra",
        "grade": "G09",
        "subject": "M"
    }
    
    return mock_question

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
