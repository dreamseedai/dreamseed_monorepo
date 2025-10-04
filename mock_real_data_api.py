#!/usr/bin/env python3
"""
Mock 데이터를 사용하는 실제 데이터 스타일 API
PostgreSQL 스타일 + 실제 변환된 데이터 시뮬레이션
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import re
from html import unescape
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DreamSeedAI Math Problem Display (Mock Real Data)",
    description="실제 변환된 데이터를 시뮬레이션하는 mpcstudy.com 스타일 수학 문제 표시 시스템",
    version="1.0.0",
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

class MathRenderingSystem:
    """수학 표현식 렌더링 시스템"""
    
    def __init__(self):
        self.mathml_pattern = re.compile(r'<math[^>]*>.*?</math>', re.DOTALL)
        self.latex_pattern = re.compile(r'\$([^$]+)\$')
        
    def process_content(self, content: str) -> str:
        """콘텐츠의 모든 수학 표현식을 처리"""
        if not content:
            return content
            
        try:
            # 1. MathML 태그 처리
            content = self._process_mathml_tags(content)
            
            # 2. LaTeX 표현식 처리
            content = self._process_latex_expressions(content)
            
            # 3. HTML 엔티티 디코딩
            content = unescape(content)
            
            return content
            
        except Exception as e:
            logger.error(f"수학 표현식 처리 오류: {e}")
            return content
    
    def _process_mathml_tags(self, content: str) -> str:
        """MathML 태그를 LaTeX로 변환"""
        def convert_mathml(match):
            mathml_str = match.group(0)
            try:
                # MathML을 LaTeX로 변환 (간단한 변환)
                return f'<span class="math-latex">$${mathml_str}$$</span>'
            except Exception as e:
                logger.error(f"MathML 변환 오류: {e}")
                return f'<span class="math-error">MathML 변환 실패</span>'
        
        return self.mathml_pattern.sub(convert_mathml, content)
    
    def _process_latex_expressions(self, content: str) -> str:
        """LaTeX 표현식을 MathLive 호환 형식으로 변환"""
        def convert_latex(match):
            latex_str = match.group(1)
            return f'<span class="math-latex" data-latex="{latex_str}">$${latex_str}$$</span>'
        
        return self.latex_pattern.sub(convert_latex, content)

# 수학 렌더링 시스템 인스턴스
math_renderer = MathRenderingSystem()

# 실제 변환된 데이터를 시뮬레이션하는 Mock 데이터
MOCK_REAL_DATA = [
    {
        "question_id": "Q001",
        "title": "이차방정식의 해 구하기",
        "content": """
        <p>다음 이차방정식을 풀어보세요:</p>
        <div class="math-expression">$$x^2 - 5x + 6 = 0$$</div>
        <p>해를 구하는 과정을 단계별로 설명하세요.</p>
        <p><strong>조건:</strong></p>
        <ul>
            <li>인수분해 방법을 사용하세요</li>
            <li>근의 공식도 확인해보세요</li>
        </ul>
        """,
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
        "hints": [
            "이차방정식 $ax^2 + bx + c = 0$에서 $a = 1$, $b = -5$, $c = 6$입니다.",
            "인수분해: 두 수의 합이 $-5$, 곱이 $6$인 두 수를 찾으세요.",
            "근의 공식: $x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$를 사용하세요."
        ],
        "answer": "$x = 2$ 또는 $x = 3$",
        "difficulty": "Medium",
        "grade": "G11",
        "subject": "M",
        "category_id": "G11M001",
        "category_name": "Advanced Algebra",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    {
        "question_id": "Q002",
        "title": "삼각함수 항등식 증명",
        "content": """
        <p>다음 삼각함수 항등식을 증명하세요:</p>
        <div class="math-expression">$$\\sin^2\\theta + \\cos^2\\theta = 1$$</div>
        <p>단위원을 이용하여 증명하세요.</p>
        <p><strong>힌트:</strong> 피타고라스 정리를 사용하세요.</p>
        """,
        "solution": """
        <div class="step-solution">
            <span class="step-number">1</span>
            <strong>단위원에서의 점:</strong><br>
            <p>단위원에서 각도 $\\theta$에 해당하는 점을 $P(\\cos\\theta, \\sin\\theta)$라고 하면:</p>
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
        "hints": [
            "단위원의 반지름이 1이므로 $x^2 + y^2 = 1$입니다.",
            "점 $P$의 좌표는 $(\\cos\\theta, \\sin\\theta)$입니다.",
            "피타고라스 정리: $a^2 + b^2 = c^2$에서 $c = 1$입니다."
        ],
        "answer": "항등식이 성립함을 증명했습니다.",
        "difficulty": "Hard",
        "grade": "G11",
        "subject": "M",
        "category_id": "G11M002",
        "category_name": "Trigonometry",
        "created_at": "2024-01-16T14:20:00Z",
        "updated_at": "2024-01-16T14:20:00Z"
    },
    {
        "question_id": "Q003",
        "title": "미분법 - 도함수 구하기",
        "content": """
        <p>다음 함수의 도함수를 구하세요:</p>
        <div class="math-expression">$$f(x) = x^3 + 2x^2 - 5x + 1$$</div>
        <p>미분 공식을 사용하여 계산하세요.</p>
        <p><strong>미분 공식:</strong></p>
        <ul>
            <li>$\\frac{d}{dx}(x^n) = nx^{n-1}$</li>
            <li>$\\frac{d}{dx}(c) = 0$ (상수항)</li>
        </ul>
        """,
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
        "hints": [
            "각 항을 개별적으로 미분하세요.",
            "상수항의 도함수는 0입니다.",
            "미분의 선형성: $(f + g)' = f' + g'$를 사용하세요."
        ],
        "answer": "$f'(x) = 3x^2 + 4x - 5$",
        "difficulty": "Hard",
        "grade": "G11",
        "subject": "M",
        "category_id": "G11M001",
        "category_name": "Advanced Algebra",
        "created_at": "2024-01-17T09:15:00Z",
        "updated_at": "2024-01-17T09:15:00Z"
    },
    {
        "question_id": "Q004",
        "title": "벡터의 크기와 내적",
        "content": """
        <p>다음 벡터의 크기를 구하세요:</p>
        <div class="math-expression">$$\\vec{v} = (3, 4, 5)$$</div>
        <p>벡터의 내적을 이용하여 다른 벡터와의 각도를 구하세요.</p>
        <p><strong>벡터 공식:</strong></p>
        <ul>
            <li>벡터의 크기: $|\\vec{v}| = \\sqrt{v_1^2 + v_2^2 + v_3^2}$</li>
            <li>내적: $\\vec{a} \\cdot \\vec{b} = a_1b_1 + a_2b_2 + a_3b_3$</li>
        </ul>
        """,
        "solution": """
        <div class="step-solution">
            <span class="step-number">1</span>
            <strong>벡터의 크기:</strong><br>
            $$|\\vec{v}| = \\sqrt{3^2 + 4^2 + 5^2} = \\sqrt{9 + 16 + 25} = \\sqrt{50} = 5\\sqrt{2}$$
        </div>
        <div class="step-solution">
            <span class="step-number">2</span>
            <strong>내적 계산:</strong><br>
            <p>벡터 $\\vec{u} = (1, 0, 0)$과의 내적:</p>
            $$\\vec{v} \\cdot \\vec{u} = 3 \\cdot 1 + 4 \\cdot 0 + 5 \\cdot 0 = 3$$
        </div>
        """,
        "hints": [
            "벡터의 각 성분을 제곱하여 더한 후 제곱근을 구하세요.",
            "내적 공식을 사용하여 두 벡터의 내적을 계산하세요.",
            "각도는 $\\cos\\theta = \\frac{\\vec{a} \\cdot \\vec{b}}{|\\vec{a}||\\vec{b}|}$로 구할 수 있습니다."
        ],
        "answer": "$|\\vec{v}| = 5\\sqrt{2}$",
        "difficulty": "Medium",
        "grade": "G11",
        "subject": "M",
        "category_id": "G11M002",
        "category_name": "Trigonometry",
        "created_at": "2024-01-18T16:45:00Z",
        "updated_at": "2024-01-18T16:45:00Z"
    },
    {
        "question_id": "Q005",
        "title": "로그함수의 성질",
        "content": """
        <p>다음 로그함수의 성질을 이용하여 값을 구하세요:</p>
        <div class="math-expression">$$\\log_2(8) + \\log_2(4) = \\log_2(?)$$</div>
        <p>로그의 성질을 사용하여 계산하세요.</p>
        <p><strong>로그의 성질:</strong></p>
        <ul>
            <li>$\\log_a(xy) = \\log_a(x) + \\log_a(y)$</li>
            <li>$\\log_a(x^n) = n\\log_a(x)$</li>
        </ul>
        """,
        "solution": """
        <div class="step-solution">
            <span class="step-number">1</span>
            <strong>로그의 성질 적용:</strong><br>
            $$\\log_2(8) + \\log_2(4) = \\log_2(8 \\times 4) = \\log_2(32)$$
        </div>
        <div class="step-solution">
            <span class="step-number">2</span>
            <strong>값 계산:</strong><br>
            $$\\log_2(32) = \\log_2(2^5) = 5$$
        </div>
        """,
        "hints": [
            "로그의 곱셈 성질을 사용하세요: $\\log_a(xy) = \\log_a(x) + \\log_a(y)$",
            "$8 = 2^3$, $4 = 2^2$임을 이용하세요.",
            "로그의 거듭제곱 성질: $\\log_a(x^n) = n\\log_a(x)$를 사용하세요."
        ],
        "answer": "$\\log_2(32) = 5$",
        "difficulty": "Medium",
        "grade": "G11",
        "subject": "M",
        "category_id": "G11M001",
        "category_name": "Advanced Algebra",
        "created_at": "2024-01-19T11:30:00Z",
        "updated_at": "2024-01-19T11:30:00Z"
    }
]

@app.get("/", response_class=HTMLResponse)
async def math_problem_display():
    """수학 문제 표시 페이지 (mpcstudy.com 스타일 + 실제 데이터)"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DreamSeedAI - Math Problem Display (Real Data)</title>
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
            
            .loading {
                text-align: center;
                padding: 20px;
                color: #6c757d;
            }
            
            .error {
                background: #f8d7da;
                color: #721c24;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            
            .data-info {
                background: #d1ecf1;
                color: #0c5460;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <!-- Data Info -->
            <div class="data-info">
                <h5><i class="fas fa-database"></i> 실제 변환된 데이터 시뮬레이션</h5>
                <p>이 페이지는 PostgreSQL에서 변환된 실제 수학 문제 데이터를 시뮬레이션합니다.</p>
                <p><strong>데이터 소스:</strong> mpcstudy.com → PostgreSQL → DreamSeedAI</p>
            </div>
            
            <!-- Question List -->
            <div class="question-list">
                <h3 class="mb-4">
                    <i class="fas fa-list"></i> DreamSeedAI Math Problems (Real Data)
                </h3>
                <div id="questionList">
                    <div class="loading">
                        <i class="fas fa-spinner fa-spin"></i> 문제를 불러오는 중...
                    </div>
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
                            <strong>Unique ID:</strong> <span id="questionId">Q001</span>
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
                    <span id="problemCounter">Problem 1 of 5</span>
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
                    
                    if (data.error) {
                        document.getElementById('questionList').innerHTML = `
                            <div class="error">
                                <i class="fas fa-exclamation-triangle"></i> ${data.error}
                            </div>
                        `;
                        return;
                    }
                    
                    problems = data.problems || [];
                    displayQuestionList();
                } catch (error) {
                    console.error('문제 로딩 오류:', error);
                    document.getElementById('questionList').innerHTML = `
                        <div class="error">
                            <i class="fas fa-exclamation-triangle"></i> 문제를 불러오는 중 오류가 발생했습니다.
                        </div>
                    `;
                }
            }
            
            // 문제 목록 표시
            function displayQuestionList() {
                const container = document.getElementById('questionList');
                
                if (problems.length === 0) {
                    container.innerHTML = `
                        <div class="error">
                            <i class="fas fa-info-circle"></i> 표시할 문제가 없습니다.
                        </div>
                    `;
                    return;
                }
                
                container.innerHTML = '';
                
                problems.forEach((problem, index) => {
                    const questionItem = document.createElement('div');
                    questionItem.className = 'question-item';
                    questionItem.onclick = () => openProblem(index);
                    questionItem.innerHTML = `
                        <h6>${problem.title || '제목 없음'}</h6>
                        <div class="question-meta">
                            ${problem.subject || 'M'} | ${problem.grade || 'G11'} | ${problem.difficulty || 'Medium'} | ID: ${problem.question_id}
                        </div>
                        <div class="question-meta">
                            카테고리: ${problem.category_name || 'Unknown'} | 생성일: ${new Date(problem.created_at).toLocaleDateString()}
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
                
                // 헤더 정보 업데이트
                document.getElementById('problemClass').textContent = problem.subject || 'Mathematics';
                document.getElementById('problemGrade').textContent = problem.grade || 'Grade 11';
                document.getElementById('problemLevel').textContent = problem.difficulty || 'Advanced';
                document.getElementById('questionId').textContent = problem.question_id;
                
                // 문제 내용 업데이트
                document.getElementById('problemText').innerHTML = problem.content || '<p>문제 내용이 없습니다.</p>';
                
                // 힌트 업데이트
                const hints = problem.hints || [];
                document.getElementById('hintsContent').innerHTML = hints.map((hint, i) => 
                    `<div class="step-solution"><span class="step-number">${i+1}</span>${hint}</div>`
                ).join('');
                
                // 해답 업데이트
                document.getElementById('solutionContent').innerHTML = problem.solution || '<p>해답이 없습니다.</p>';
                
                // 정답 업데이트
                document.getElementById('answerContent').innerHTML = 
                    `<div class="math-expression">${problem.answer || '정답이 없습니다.'}</div>`;
                
                // 카운터 업데이트
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
async def get_math_problems(
    grade: str = Query(None, description="학년"),
    subject: str = Query(None, description="과목"),
    category_id: str = Query(None, description="카테고리 ID"),
    limit: int = Query(10, description="문제 수"),
    offset: int = Query(0, description="오프셋")
):
    """수학 문제 목록 조회 (실제 변환된 데이터 시뮬레이션)"""
    try:
        # Mock 데이터에서 필터링
        filtered_questions = MOCK_REAL_DATA.copy()
        
        if grade:
            filtered_questions = [q for q in filtered_questions if q.get('grade') == grade]
        
        if subject:
            filtered_questions = [q for q in filtered_questions if q.get('subject') == subject]
        
        if category_id:
            filtered_questions = [q for q in filtered_questions if q.get('category_id') == category_id]
        
        # 페이징 적용
        start_idx = offset
        end_idx = offset + limit
        paginated_questions = filtered_questions[start_idx:end_idx]
        
        # 수학 표현식 처리
        processed_questions = []
        for question in paginated_questions:
            processed_question = question.copy()
            processed_question['content'] = math_renderer.process_content(question.get('content', ''))
            processed_question['solution'] = math_renderer.process_content(question.get('solution', ''))
            processed_question['answer'] = math_renderer.process_content(question.get('answer', ''))
            
            # 힌트 처리
            hints = question.get('hints', [])
            if hints:
                processed_question['hints'] = [math_renderer.process_content(hint) for hint in hints]
            else:
                processed_question['hints'] = []
            
            processed_questions.append(processed_question)
        
        return {
            "total_count": len(processed_questions),
            "problems": processed_questions,
            "filters": {
                "grade": grade,
                "subject": subject,
                "category_id": category_id,
                "limit": limit,
                "offset": offset
            },
            "data_source": "PostgreSQL (Simulated)",
            "conversion_info": "mpcstudy.com → PostgreSQL → DreamSeedAI"
        }
        
    except Exception as e:
        logger.error(f"수학 문제 조회 오류: {e}")
        return {
            "error": f"데이터 조회 중 오류가 발생했습니다: {str(e)}",
            "total_count": 0,
            "problems": []
        }

@app.get("/api/math/problem/{question_id}")
async def get_single_problem(question_id: str):
    """단일 수학 문제 조회 (실제 변환된 데이터 시뮬레이션)"""
    try:
        question = next((q for q in MOCK_REAL_DATA if q['question_id'] == question_id), None)
        
        if not question:
            raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다")
        
        # 수학 표현식 처리
        question['content'] = math_renderer.process_content(question.get('content', ''))
        question['solution'] = math_renderer.process_content(question.get('solution', ''))
        question['answer'] = math_renderer.process_content(question.get('answer', ''))
        
        # 힌트 처리
        hints = question.get('hints', [])
        if hints:
            question['hints'] = [math_renderer.process_content(hint) for hint in hints]
        else:
            question['hints'] = []
        
        return question
        
    except Exception as e:
        logger.error(f"수학 문제 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"문제 조회 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 DreamSeedAI Math Problem Display (Mock Real Data) 시작...")
    print("📊 PostgreSQL + TipTap + MathLive 조합")
    print("🌐 http://localhost:8005 에서 확인하세요")
    uvicorn.run(app, host="0.0.0.0", port=8005, log_level="info")
