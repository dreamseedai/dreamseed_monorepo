#!/usr/bin/env python3
"""
실제 PostgreSQL 데이터를 사용하는 수학 문제 API
mpcstudy.com 스타일 + 실제 데이터
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import re
from html import unescape
from postgresql_connection import db_connection
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DreamSeedAI Math Problem Display (Real Data)",
    description="실제 PostgreSQL 데이터를 사용하는 mpcstudy.com 스타일 수학 문제 표시 시스템",
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
                # 실제로는 더 복잡한 변환 로직이 필요할 수 있음
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

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 데이터베이스 연결"""
    logger.info("데이터베이스 연결 시도...")
    if db_connection.connect():
        logger.info("PostgreSQL 데이터베이스 연결 성공")
    else:
        logger.warning("PostgreSQL 데이터베이스 연결 실패 - Mock 데이터 사용")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 데이터베이스 연결 해제"""
    db_connection.disconnect()

@app.get("/", response_class=HTMLResponse)
async def math_problem_display():
    """수학 문제 표시 페이지 (mpcstudy.com 스타일)"""
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
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <!-- Question List -->
            <div class="question-list">
                <h3 class="mb-4">
                    <i class="fas fa-database"></i> DreamSeedAI Math Problems (Real Data)
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
    """수학 문제 목록 조회 (실제 PostgreSQL 데이터)"""
    try:
        # PostgreSQL에서 실제 데이터 조회
        questions = db_connection.get_math_questions(
            grade=grade,
            subject=subject,
            category_id=category_id,
            limit=limit,
            offset=offset
        )
        
        # 수학 표현식 처리
        processed_questions = []
        for question in questions:
            processed_question = question.copy()
            processed_question['content'] = math_renderer.process_content(question.get('content', ''))
            processed_question['solution'] = math_renderer.process_content(question.get('solution', ''))
            processed_question['answer'] = math_renderer.process_content(question.get('answer', ''))
            
            # 힌트 처리
            hints = question.get('hints', '')
            if hints:
                try:
                    if isinstance(hints, str):
                        hints_list = json.loads(hints) if hints.startswith('[') else [hints]
                    else:
                        hints_list = hints
                    processed_question['hints'] = [math_renderer.process_content(hint) for hint in hints_list]
                except:
                    processed_question['hints'] = [math_renderer.process_content(hints)]
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
            }
        }
        
    except Exception as e:
        logger.error(f"수학 문제 조회 오류: {e}")
        return {
            "error": f"데이터베이스 조회 중 오류가 발생했습니다: {str(e)}",
            "total_count": 0,
            "problems": []
        }

@app.get("/api/math/problem/{question_id}")
async def get_single_problem(question_id: str):
    """단일 수학 문제 조회 (실제 PostgreSQL 데이터)"""
    try:
        question = db_connection.get_question_by_id(question_id)
        
        if not question:
            raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다")
        
        # 수학 표현식 처리
        question['content'] = math_renderer.process_content(question.get('content', ''))
        question['solution'] = math_renderer.process_content(question.get('solution', ''))
        question['answer'] = math_renderer.process_content(question.get('answer', ''))
        
        # 힌트 처리
        hints = question.get('hints', '')
        if hints:
            try:
                if isinstance(hints, str):
                    hints_list = json.loads(hints) if hints.startswith('[') else [hints]
                else:
                    hints_list = hints
                question['hints'] = [math_renderer.process_content(hint) for hint in hints_list]
            except:
                question['hints'] = [math_renderer.process_content(hints)]
        else:
            question['hints'] = []
        
        return question
        
    except Exception as e:
        logger.error(f"수학 문제 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"문제 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/math/categories")
async def get_categories(
    grade: str = Query(None, description="학년"),
    subject: str = Query(None, description="과목")
):
    """카테고리 목록 조회 (실제 PostgreSQL 데이터)"""
    try:
        categories = db_connection.get_categories(grade=grade, subject=subject)
        return {
            "total_count": len(categories),
            "categories": categories
        }
        
    except Exception as e:
        logger.error(f"카테고리 조회 오류: {e}")
        return {
            "error": f"카테고리 조회 중 오류가 발생했습니다: {str(e)}",
            "total_count": 0,
            "categories": []
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 DreamSeedAI Math Problem Display (Real Data) 시작...")
    print("📊 PostgreSQL + TipTap + MathLive 조합")
    print("🌐 http://localhost:8004 에서 확인하세요")
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
