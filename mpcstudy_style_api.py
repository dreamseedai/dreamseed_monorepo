#!/usr/bin/env python3
"""
mpcstudy.com 스타일 수학 문제 표시 API
PostgreSQL + TipTap + MathLive 조합
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import re
from html import unescape

app = FastAPI(
    title="DreamSeedAI Math Problem Display (mpcstudy.com Style)",
    description="mpcstudy.com과 동일한 스타일의 수학 문제 표시 시스템",
    version="1.0.0",
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

# mpcstudy.com 스타일 수학 문제 데이터
MOCK_MATH_PROBLEMS = [
    {
        "question_id": "G11Q001",
        "title": "Quadratic Equation Solving",
        "class": "Mathematics",
        "grade": "Grade 11",
        "level": "Advanced",
        "unique_id": "0",
        "problem": """
        <p>다음 이차방정식을 풀어보세요:</p>
        <div class="math-expression">$$x^2 - 5x + 6 = 0$$</div>
        <p>해를 구하는 과정을 단계별로 설명하세요.</p>
        """,
        "hints": [
            "인수분해 방법: 이차방정식을 두 개의 일차식의 곱으로 나타내세요.",
            "근의 공식: $x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$ 공식을 사용하세요."
        ],
        "solution": """
        <div class="step-solution">
            <span class="step-number">1</span>
            <strong>인수분해를 이용한 방법:</strong><br>
            $$x^2 - 5x + 6 = (x-2)(x-3) = 0$$
            <p>따라서 $x = 2$ 또는 $x = 3$</p>
        </div>
        <div class="step-solution">
            <span class="step-number">2</span>
            <strong>근의 공식을 이용한 방법:</strong><br>
            $$x = \\frac{5 \\pm \\sqrt{25-24}}{2} = \\frac{5 \\pm 1}{2}$$
            <p>따라서 $x = 3$ 또는 $x = 2$</p>
        </div>
        """,
        "answer": "$x = 2$ 또는 $x = 3$",
        "difficulty": "Medium",
        "category": "G11M001"
    },
    {
        "question_id": "G11Q002",
        "title": "Trigonometric Functions",
        "class": "Mathematics",
        "grade": "Grade 11",
        "level": "Advanced",
        "unique_id": "1",
        "problem": """
        <p>다음 삼각함수 방정식을 풀어보세요:</p>
        <div class="math-expression">$$\\sin^2\\theta + \\cos^2\\theta = 1$$</div>
        <p>이 항등식이 성립함을 증명하세요.</p>
        """,
        "hints": [
            "단위원에서 점의 좌표를 생각해보세요.",
            "피타고라스 정리를 사용하세요."
        ],
        "solution": """
        <div class="step-solution">
            <span class="step-number">1</span>
            <strong>단위원에서의 점:</strong><br>
            <p>단위원에서 점 $P(\\cos\\theta, \\sin\\theta)$를 생각하면:</p>
            $$x^2 + y^2 = 1$$
        </div>
        <div class="step-solution">
            <span class="step-number">2</span>
            <strong>피타고라스 정리 적용:</strong><br>
            <p>따라서:</p>
            $$\\cos^2\\theta + \\sin^2\\theta = 1$$
            <p>이것이 피타고라스 정리의 삼각함수 형태입니다.</p>
        </div>
        """,
        "answer": "항등식이 성립함을 증명했습니다.",
        "difficulty": "Hard",
        "category": "G11M002"
    },
    {
        "question_id": "G11Q003",
        "title": "Calculus - Derivatives",
        "class": "Mathematics",
        "grade": "Grade 11",
        "level": "Advanced",
        "unique_id": "2",
        "problem": """
        <p>다음 함수의 도함수를 구하세요:</p>
        <div class="math-expression">$$f(x) = x^3 + 2x^2 - 5x + 1$$</div>
        <p>미분 공식을 사용하여 계산하세요.</p>
        """,
        "hints": [
            "각 항을 개별적으로 미분하세요.",
            "상수항의 도함수는 0입니다."
        ],
        "solution": """
        <div class="step-solution">
            <span class="step-number">1</span>
            <strong>각 항을 개별적으로 미분:</strong><br>
            $$\\frac{d}{dx}(x^3) = 3x^2$$
            $$\\frac{d}{dx}(2x^2) = 4x$$
            $$\\frac{d}{dx}(-5x) = -5$$
            $$\\frac{d}{dx}(1) = 0$$
        </div>
        <div class="step-solution">
            <span class="step-number">2</span>
            <strong>결과 합산:</strong><br>
            <p>따라서:</p>
            $$f'(x) = 3x^2 + 4x - 5$$
        </div>
        """,
        "answer": "$f'(x) = 3x^2 + 4x - 5$",
        "difficulty": "Hard",
        "category": "G11M001"
    }
]

@app.get("/", response_class=HTMLResponse)
async def mpcstudy_style_demo():
    """mpcstudy.com 스타일 데모 페이지"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DreamSeedAI - Math Problem Display (mpcstudy.com Style)</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free/css/all.min.css" rel="stylesheet">
        
        <!-- MathJax for rendering -->
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <script>
            window.MathJax = {
                tex: {
                    inlineMath: [['$', '$'], ['\\(', '\\)']],
                    displayMath: [['$$', '$$'], ['\\[', '\\]']]
                },
                svg: {
                    fontCache: 'global'
                }
            };
        </script>
        
        <style>
            /* mpcstudy.com 스타일 */
            .problem-container {
                background: #ffffff;
                border: 2px solid #007bff;
                border-radius: 10px;
                padding: 20px;
                margin: 20px auto;
                max-width: 900px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .problem-header {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
            }
            
            .problem-info {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            
            .problem-meta {
                font-size: 14px;
                color: #6c757d;
            }
            
            .problem-meta strong {
                color: #495057;
            }
            
            .problem-content {
                background: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 20px;
                margin: 15px 0;
                min-height: 200px;
            }
            
            .problem-section {
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background: #f8f9fa;
            }
            
            .problem-section h5 {
                color: #007bff;
                margin-bottom: 15px;
                border-bottom: 2px solid #007bff;
                padding-bottom: 5px;
            }
            
            .answer-section {
                background: #e8f5e8;
                border: 1px solid #28a745;
                border-radius: 5px;
                padding: 15px;
                margin: 15px 0;
            }
            
            .answer-section h5 {
                color: #28a745;
                margin-bottom: 15px;
            }
            
            .action-buttons {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }
            
            .btn-group-custom {
                display: flex;
                gap: 10px;
            }
            
            .btn-custom {
                padding: 8px 16px;
                border-radius: 5px;
                border: 1px solid #007bff;
                background: #007bff;
                color: white;
                text-decoration: none;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .btn-custom:hover {
                background: #0056b3;
                color: white;
            }
            
            .btn-secondary-custom {
                background: #6c757d;
                border-color: #6c757d;
            }
            
            .btn-secondary-custom:hover {
                background: #545b62;
            }
            
            .btn-success-custom {
                background: #28a745;
                border-color: #28a745;
            }
            
            .btn-success-custom:hover {
                background: #1e7e34;
            }
            
            .btn-danger-custom {
                background: #dc3545;
                border-color: #dc3545;
            }
            
            .btn-danger-custom:hover {
                background: #c82333;
            }
            
            .math-expression {
                background: #e3f2fd;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
                text-align: center;
                font-size: 18px;
            }
            
            .step-solution {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 5px;
                padding: 15px;
                margin: 10px 0;
            }
            
            .step-number {
                background: #007bff;
                color: white;
                border-radius: 50%;
                width: 25px;
                height: 25px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-right: 10px;
                font-weight: bold;
            }
            
            .favorite-btn {
                background: #ffc107;
                border-color: #ffc107;
                color: #212529;
            }
            
            .favorite-btn:hover {
                background: #e0a800;
                color: #212529;
            }
            
            .favorite-btn.favorited {
                background: #dc3545;
                border-color: #dc3545;
                color: white;
            }
            
            .favorite-btn.favorited:hover {
                background: #c82333;
            }
            
            .close-btn {
                position: absolute;
                top: 10px;
                right: 10px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                cursor: pointer;
            }
            
            .close-btn:hover {
                background: #c82333;
            }
            
            .problem-navigation {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 20px 0;
                padding: 15px;
                background: #e9ecef;
                border-radius: 5px;
            }
            
            .nav-btn {
                padding: 8px 16px;
                border: 1px solid #6c757d;
                background: white;
                color: #6c757d;
                text-decoration: none;
                border-radius: 5px;
                cursor: pointer;
            }
            
            .nav-btn:hover {
                background: #6c757d;
                color: white;
            }
            
            .nav-btn:disabled {
                background: #f8f9fa;
                color: #6c757d;
                cursor: not-allowed;
            }
            
            .question-list {
                margin: 20px 0;
            }
            
            .question-item {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                margin: 10px 0;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .question-item:hover {
                background: #e9ecef;
                border-color: #007bff;
            }
            
            .question-item h6 {
                color: #007bff;
                margin-bottom: 5px;
            }
            
            .question-meta {
                font-size: 12px;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <!-- Question List -->
            <div class="question-list">
                <h3 class="mb-4">
                    <i class="fas fa-list"></i> Math Problems (mpcstudy.com Style)
                </h3>
                <div id="questionList">
                    <!-- 문제 목록이 여기에 동적으로 로드됩니다 -->
                </div>
            </div>
            
            <!-- Problem Display Container -->
            <div class="problem-container" id="problemContainer" style="display: none;">
                <button class="close-btn" onclick="closeProblem()" title="닫기">
                    <i class="fas fa-times"></i>
                </button>
                
                <!-- Problem Header -->
                <div class="problem-header">
                    <div class="problem-info">
                        <div class="problem-meta">
                            <strong>Class:</strong> <span id="problemClass">Mathematics</span> | 
                            <strong>Grade:</strong> <span id="problemGrade">Grade 11</span> | 
                            <strong>Level:</strong> <span id="problemLevel">Advanced</span> | 
                            <strong>Unique ID:</strong> <span id="questionId">G11Q001</span>
                        </div>
                    </div>
                </div>
                
                <!-- Problem Content -->
                <div class="problem-content">
                    <div class="problem-section">
                        <h5><i class="fas fa-question-circle"></i> Problem</h5>
                        <div id="problemText">
                            <!-- 문제 내용이 여기에 표시됩니다 -->
                        </div>
                    </div>
                    
                    <!-- Hints Section -->
                    <div class="problem-section" id="hintsSection" style="display: none;">
                        <h5><i class="fas fa-lightbulb"></i> Hints</h5>
                        <div id="hintsContent">
                            <!-- 힌트 내용이 여기에 표시됩니다 -->
                        </div>
                    </div>
                    
                    <!-- Solution Section -->
                    <div class="problem-section" id="solutionSection" style="display: none;">
                        <h5><i class="fas fa-check-circle"></i> Solution</h5>
                        <div id="solutionContent">
                            <!-- 해답 내용이 여기에 표시됩니다 -->
                        </div>
                    </div>
                    
                    <!-- Answer Section -->
                    <div class="answer-section">
                        <h5><i class="fas fa-key"></i> Answer</h5>
                        <div id="answerContent">
                            <!-- 정답이 여기에 표시됩니다 -->
                        </div>
                    </div>
                </div>
                
                <!-- Action Buttons -->
                <div class="action-buttons">
                    <div class="btn-group-custom">
                        <button class="btn-custom" onclick="showHints()">
                            <i class="fas fa-lightbulb"></i> Show Hints
                        </button>
                        <button class="btn-custom" onclick="showSolution()">
                            <i class="fas fa-check-circle"></i> Show Solution
                        </button>
                        <button class="btn-custom btn-success-custom" onclick="markSolved()">
                            <i class="fas fa-check"></i> Solved
                        </button>
                    </div>
                    <div class="btn-group-custom">
                        <button class="btn-custom favorite-btn" id="favoriteBtn" onclick="toggleFavorite()">
                            <i class="fas fa-heart"></i> Save to My Favorites
                        </button>
                        <button class="btn-custom btn-secondary-custom" onclick="finishProblem()">
                            <i class="fas fa-flag-checkered"></i> Finish
                        </button>
                    </div>
                </div>
                
                <!-- Navigation -->
                <div class="problem-navigation">
                    <button class="nav-btn" onclick="previousProblem()" id="prevBtn">
                        <i class="fas fa-chevron-left"></i> Previous
                    </button>
                    <span id="problemCounter">Problem 1 of 3</span>
                    <button class="nav-btn" onclick="nextProblem()" id="nextBtn">
                        Next <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- JavaScript -->
        <script>
            let problems = [];
            let currentProblemIndex = 0;
            let isFavorited = false;
            
            // 문제 목록 로드
            async function loadQuestions() {
                try {
                    const response = await fetch('/api/math/problems');
                    const data = await response.json();
                    problems = data.problems;
                    displayQuestionList();
                } catch (error) {
                    console.error('문제 로딩 오류:', error);
                }
            }
            
            // 문제 목록 표시
            function displayQuestionList() {
                const container = document.getElementById('questionList');
                container.innerHTML = '';
                
                problems.forEach((problem, index) => {
                    const questionItem = document.createElement('div');
                    questionItem.className = 'question-item';
                    questionItem.onclick = () => openProblem(index);
                    questionItem.innerHTML = `
                        <h6>${problem.title}</h6>
                        <div class="question-meta">
                            ${problem.class} | ${problem.grade} | ${problem.level} | ID: ${problem.question_id}
                        </div>
                    `;
                    container.appendChild(questionItem);
                });
            }
            
            // 문제 열기
            function openProblem(index) {
                currentProblemIndex = index;
                displayProblem(index);
                document.getElementById('questionList').style.display = 'none';
                document.getElementById('problemContainer').style.display = 'block';
            }
            
            // 문제 표시
            function displayProblem(index) {
                const problem = problems[index];
                document.getElementById('problemClass').textContent = problem.class;
                document.getElementById('problemGrade').textContent = problem.grade;
                document.getElementById('problemLevel').textContent = problem.level;
                document.getElementById('questionId').textContent = problem.question_id;
                document.getElementById('problemText').innerHTML = problem.problem;
                document.getElementById('hintsContent').innerHTML = problem.hints.map((hint, i) => 
                    `<div class="step-solution"><span class="step-number">${i+1}</span>${hint}</div>`
                ).join('');
                document.getElementById('solutionContent').innerHTML = problem.solution;
                document.getElementById('answerContent').innerHTML = `<div class="math-expression">${problem.answer}</div>`;
                document.getElementById('problemCounter').textContent = `Problem ${index + 1} of ${problems.length}`;
                
                // 이전/다음 버튼 상태 업데이트
                document.getElementById('prevBtn').disabled = index === 0;
                document.getElementById('nextBtn').disabled = index === problems.length - 1;
                
                // 섹션 숨기기
                document.getElementById('hintsSection').style.display = 'none';
                document.getElementById('solutionSection').style.display = 'none';
                
                // MathJax 렌더링
                MathJax.typesetPromise();
            }
            
            // 힌트 표시
            function showHints() {
                const hintsSection = document.getElementById('hintsSection');
                hintsSection.style.display = hintsSection.style.display === 'none' ? 'block' : 'none';
                MathJax.typesetPromise([hintsSection]);
            }
            
            // 해답 표시
            function showSolution() {
                const solutionSection = document.getElementById('solutionSection');
                solutionSection.style.display = solutionSection.style.display === 'none' ? 'block' : 'none';
                MathJax.typesetPromise([solutionSection]);
            }
            
            // 해결됨 표시
            function markSolved() {
                alert('문제가 해결되었습니다! 🎉');
            }
            
            // 즐겨찾기 토글
            function toggleFavorite() {
                isFavorited = !isFavorited;
                const btn = document.getElementById('favoriteBtn');
                if (isFavorited) {
                    btn.classList.add('favorited');
                    btn.innerHTML = '<i class="fas fa-heart"></i> Remove from Favorites';
                } else {
                    btn.classList.remove('favorited');
                    btn.innerHTML = '<i class="fas fa-heart"></i> Save to My Favorites';
                }
            }
            
            // 문제 완료
            function finishProblem() {
                alert('문제를 완료했습니다! 다음 문제로 넘어가세요.');
            }
            
            // 이전 문제
            function previousProblem() {
                if (currentProblemIndex > 0) {
                    currentProblemIndex--;
                    displayProblem(currentProblemIndex);
                }
            }
            
            // 다음 문제
            function nextProblem() {
                if (currentProblemIndex < problems.length - 1) {
                    currentProblemIndex++;
                    displayProblem(currentProblemIndex);
                }
            }
            
            // 문제 닫기
            function closeProblem() {
                document.getElementById('problemContainer').style.display = 'none';
                document.getElementById('questionList').style.display = 'block';
            }
            
            // 페이지 로드 시 문제 목록 로드
            document.addEventListener('DOMContentLoaded', loadQuestions);
        </script>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/math/problems")
async def get_math_problems():
    """수학 문제 목록 조회 (mpcstudy.com 스타일)"""
    return {
        "total_count": len(MOCK_MATH_PROBLEMS),
        "problems": MOCK_MATH_PROBLEMS
    }

@app.get("/api/math/problem/{question_id}")
async def get_single_problem(question_id: str):
    """단일 수학 문제 조회 (mpcstudy.com 스타일)"""
    problem = next((p for p in MOCK_MATH_PROBLEMS if p['question_id'] == question_id), None)
    
    if not problem:
        raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다")
    
    return problem

if __name__ == "__main__":
    import uvicorn
    print("🚀 DreamSeedAI Math Problem Display (mpcstudy.com Style) 시작...")
    print("📊 PostgreSQL + TipTap + MathLive 조합")
    print("🌐 http://localhost:8003 에서 확인하세요")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
