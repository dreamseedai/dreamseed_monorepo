#!/usr/bin/env python3
"""
PostgreSQL + TipTap + MathLive 수학 문제 렌더링 데모
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import re
from html import unescape
from sympy.parsing.mathml import parse_mathml
from sympy.printing.latex import latex
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DreamSeedAI Math Rendering System",
    description="PostgreSQL + TipTap + MathLive 수학 문제 렌더링 시스템",
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
                # MathML을 SymPy 표현식으로 파싱
                expr = parse_mathml(mathml_str)
                # LaTeX로 변환
                latex_str = latex(expr)
                return f'<span class="math-latex" data-latex="{latex_str}">$${latex_str}$$</span>'
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

# Mock 데이터베이스 연결 (실제로는 PostgreSQL 사용)
def get_db_connection():
    """데이터베이스 연결 (Mock)"""
    # 실제 환경에서는 PostgreSQL 연결
    # return psycopg2.connect("postgresql://user:password@localhost/dreamseed")
    return None

# Mock 수학 문제 데이터
MOCK_MATH_QUESTIONS = [
    {
        "question_id": "G11Q001",
        "title": "Quadratic Equation Solving",
        "content": """
        <p>다음 이차방정식을 풀어보세요:</p>
        <p>$$x^2 - 5x + 6 = 0$$</p>
        <p>해를 구하는 과정을 단계별로 설명하세요.</p>
        """,
        "solution": """
        <p><strong>해결 과정:</strong></p>
        <p>1. 인수분해를 이용한 방법:</p>
        <p>$$x^2 - 5x + 6 = (x-2)(x-3) = 0$$</p>
        <p>따라서 $x = 2$ 또는 $x = 3$</p>
        <p>2. 근의 공식을 이용한 방법:</p>
        <p>$$x = \\frac{5 \\pm \\sqrt{25-24}}{2} = \\frac{5 \\pm 1}{2}$$</p>
        <p>따라서 $x = 3$ 또는 $x = 2$</p>
        """,
        "difficulty": "Medium",
        "category": "G11M001",
        "grade": "G11",
        "subject": "M"
    },
    {
        "question_id": "G11Q002",
        "title": "Trigonometric Functions",
        "content": """
        <p>다음 삼각함수 방정식을 풀어보세요:</p>
        <p>$$\\sin^2\\theta + \\cos^2\\theta = 1$$</p>
        <p>이 항등식이 성립함을 증명하세요.</p>
        """,
        "solution": """
        <p><strong>증명:</strong></p>
        <p>단위원에서 점 $P(\\cos\\theta, \\sin\\theta)$를 생각하면:</p>
        <p>$$x^2 + y^2 = 1$$</p>
        <p>따라서:</p>
        <p>$$\\cos^2\\theta + \\sin^2\\theta = 1$$</p>
        <p>이것이 피타고라스 정리의 삼각함수 형태입니다.</p>
        """,
        "difficulty": "Hard",
        "category": "G11M002",
        "grade": "G11",
        "subject": "M"
    },
    {
        "question_id": "G11Q003",
        "title": "Calculus - Derivatives",
        "content": """
        <p>다음 함수의 도함수를 구하세요:</p>
        <p>$$f(x) = x^3 + 2x^2 - 5x + 1$$</p>
        <p>미분 공식을 사용하여 계산하세요.</p>
        """,
        "solution": """
        <p><strong>해결 과정:</strong></p>
        <p>각 항을 개별적으로 미분합니다:</p>
        <p>$$\\frac{d}{dx}(x^3) = 3x^2$$</p>
        <p>$$\\frac{d}{dx}(2x^2) = 4x$$</p>
        <p>$$\\frac{d}{dx}(-5x) = -5$$</p>
        <p>$$\\frac{d}{dx}(1) = 0$$</p>
        <p>따라서:</p>
        <p>$$f'(x) = 3x^2 + 4x - 5$$</p>
        """,
        "difficulty": "Hard",
        "category": "G11M001",
        "grade": "G11",
        "subject": "M"
    }
]

@app.get("/", response_class=HTMLResponse)
async def math_rendering_demo():
    """수학 문제 렌더링 데모 페이지"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DreamSeedAI Math Rendering Demo</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free/css/all.min.css" rel="stylesheet">
        
        <!-- MathLive CSS -->
        <link rel="stylesheet" href="https://unpkg.com/mathlive/dist/mathlive-static.css">
        
        <!-- TipTap CSS -->
        <link rel="stylesheet" href="https://unpkg.com/@tiptap/core@2.1.13/dist/index.css">
        <link rel="stylesheet" href="https://unpkg.com/@tiptap/extension-math@2.1.13/dist/index.css">
        
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
            .math-container {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }
            .math-latex {
                background: #e3f2fd;
                padding: 2px 6px;
                border-radius: 4px;
                margin: 0 2px;
                display: inline-block;
            }
            .math-error {
                background: #ffebee;
                color: #c62828;
                padding: 2px 6px;
                border-radius: 4px;
            }
            .question-card {
                margin-bottom: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .solution-section {
                background: #f1f8e9;
                border-left: 4px solid #4caf50;
                padding: 15px;
                margin-top: 15px;
            }
            .math-input {
                width: 100%;
                min-height: 50px;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Times New Roman', serif;
            }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <div class="col-12">
                    <div class="jumbotron bg-primary text-white p-5 mb-4">
                        <h1 class="display-4">
                            <i class="fas fa-calculator"></i> DreamSeedAI Math Rendering System
                        </h1>
                        <p class="lead">PostgreSQL + TipTap + MathLive 조합으로 구현된 수학 문제 렌더링 시스템</p>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-8">
                    <div id="questions-container">
                        <!-- 수학 문제들이 여기에 동적으로 로드됩니다 -->
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-edit"></i> MathLive 입력 테스트</h5>
                        </div>
                        <div class="card-body">
                            <p>수학 표현식을 입력해보세요:</p>
                            <div id="math-input" class="math-input"></div>
                            <button class="btn btn-primary mt-2" onclick="renderMathInput()">
                                <i class="fas fa-play"></i> 렌더링
                            </button>
                            <div id="math-output" class="mt-3"></div>
                        </div>
                    </div>
                    
                    <div class="card mt-3">
                        <div class="card-header">
                            <h5><i class="fas fa-info-circle"></i> 시스템 정보</h5>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li><strong>데이터베이스:</strong> PostgreSQL</li>
                                <li><strong>에디터:</strong> TipTap</li>
                                <li><strong>수학 입력:</strong> MathLive</li>
                                <li><strong>수학 렌더링:</strong> MathJax</li>
                                <li><strong>백엔드:</strong> FastAPI</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- MathLive JavaScript -->
        <script type="module">
            import { MathfieldElement } from 'https://unpkg.com/mathlive/dist/mathlive-element.mjs';
            
            // MathLive 요소 등록
            customElements.define('math-field', MathfieldElement);
            
            // MathLive 입력 필드 초기화
            const mathInput = document.getElementById('math-input');
            const mathField = document.createElement('math-field');
            mathField.style.width = '100%';
            mathField.style.minHeight = '50px';
            mathField.style.border = '1px solid #ddd';
            mathField.style.borderRadius = '4px';
            mathField.style.padding = '10px';
            mathInput.appendChild(mathField);
            
            // 전역 함수로 등록
            window.renderMathInput = function() {
                const latex = mathField.getValue();
                const output = document.getElementById('math-output');
                output.innerHTML = `<p><strong>입력된 LaTeX:</strong></p><p>$$${latex}$$</p>`;
                MathJax.typesetPromise([output]);
            };
        </script>

        <!-- 수학 문제 로딩 스크립트 -->
        <script>
            async function loadMathQuestions() {
                try {
                    const response = await fetch('/api/math/questions');
                    const data = await response.json();
                    
                    const container = document.getElementById('questions-container');
                    container.innerHTML = '';
                    
                    data.questions.forEach((question, index) => {
                        const questionCard = createQuestionCard(question, index + 1);
                        container.appendChild(questionCard);
                    });
                    
                    // MathJax 렌더링
                    MathJax.typesetPromise([container]);
                    
                } catch (error) {
                    console.error('수학 문제 로딩 오류:', error);
                }
            }
            
            function createQuestionCard(question, number) {
                const card = document.createElement('div');
                card.className = 'card question-card';
                card.innerHTML = `
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">문제 ${number}: ${question.title}</h5>
                        <span class="badge bg-${getDifficultyColor(question.difficulty)}">${question.difficulty}</span>
                    </div>
                    <div class="card-body">
                        <div class="math-container">
                            ${question.content}
                        </div>
                        <button class="btn btn-outline-primary btn-sm" onclick="toggleSolution(${question.question_id})">
                            <i class="fas fa-eye"></i> 해답 보기
                        </button>
                        <div id="solution-${question.question_id}" class="solution-section" style="display: none;">
                            ${question.solution}
                        </div>
                    </div>
                `;
                return card;
            }
            
            function getDifficultyColor(difficulty) {
                switch(difficulty) {
                    case 'Easy': return 'success';
                    case 'Medium': return 'warning';
                    case 'Hard': return 'danger';
                    default: return 'secondary';
                }
            }
            
            function toggleSolution(questionId) {
                const solution = document.getElementById(`solution-${questionId}`);
                if (solution.style.display === 'none') {
                    solution.style.display = 'block';
                    MathJax.typesetPromise([solution]);
                } else {
                    solution.style.display = 'none';
                }
            }
            
            // 페이지 로드 시 수학 문제 로드
            document.addEventListener('DOMContentLoaded', loadMathQuestions);
        </script>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/math/questions")
async def get_math_questions():
    """수학 문제 목록 조회 (PostgreSQL + TipTap + MathLive)"""
    try:
        # 실제 환경에서는 PostgreSQL에서 데이터 조회
        # conn = get_db_connection()
        # cursor = conn.cursor(cursor_factory=RealDictCursor)
        # cursor.execute("SELECT * FROM questions WHERE grade = %s AND subject = %s", (grade, subject))
        # questions = cursor.fetchall()
        
        # Mock 데이터 사용
        questions = MOCK_MATH_QUESTIONS
        
        # 수학 표현식 처리 (TipTap + MathLive 호환)
        processed_questions = []
        for question in questions:
            processed_question = question.copy()
            processed_question['content'] = math_renderer.process_content(question['content'])
            processed_question['solution'] = math_renderer.process_content(question['solution'])
            processed_questions.append(processed_question)
        
        return {
            "total_count": len(processed_questions),
            "questions": processed_questions,
            "system_info": {
                "database": "PostgreSQL",
                "editor": "TipTap",
                "math_input": "MathLive",
                "math_rendering": "MathJax",
                "backend": "FastAPI"
            }
        }
        
    except Exception as e:
        logger.error(f"수학 문제 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"수학 문제 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/math/question/{question_id}")
async def get_single_question(question_id: str):
    """단일 수학 문제 조회"""
    try:
        # 실제 환경에서는 PostgreSQL에서 조회
        # conn = get_db_connection()
        # cursor = conn.cursor(cursor_factory=RealDictCursor)
        # cursor.execute("SELECT * FROM questions WHERE question_id = %s", (question_id,))
        # question = cursor.fetchone()
        
        # Mock 데이터에서 조회
        question = next((q for q in MOCK_MATH_QUESTIONS if q['question_id'] == question_id), None)
        
        if not question:
            raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다")
        
        # 수학 표현식 처리
        question['content'] = math_renderer.process_content(question['content'])
        question['solution'] = math_renderer.process_content(question['solution'])
        
        return question
        
    except Exception as e:
        logger.error(f"수학 문제 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"수학 문제 조회 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 DreamSeedAI Math Rendering System 시작...")
    print("📊 PostgreSQL + TipTap + MathLive 조합")
    print("🌐 http://localhost:8002 에서 확인하세요")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
