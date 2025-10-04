#!/usr/bin/env python3
"""
DreamSeedAI Math 버튼 연결 문제 빠른 해결 스크립트
현재 상태 진단 및 수정 방안 제시
"""

import os
import re
from pathlib import Path

def diagnose_current_state():
    """현재 상태 진단"""
    print("🔍 DreamSeedAI Math 버튼 연결 문제 진단")
    print("=" * 60)
    
    # 1. 라우팅 파일 찾기
    print("\n1. 라우팅 파일 검색:")
    routing_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if any(pattern in file.lower() for pattern in ['route', 'router', 'app']):
                if file.endswith(('.tsx', '.jsx', '.ts', '.js')):
                    routing_files.append(os.path.join(root, file))
    
    for file in routing_files[:5]:  # 처음 5개만 표시
        print(f"   📄 {file}")
    
    # 2. Math 버튼 관련 코드 찾기
    print("\n2. Math 버튼 관련 코드 검색:")
    math_references = []
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.tsx', '.jsx', '.ts', '.js')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'Math' in content and ('button' in content.lower() or 'link' in content.lower()):
                            math_references.append((file_path, content))
                except:
                    continue
    
    for file_path, content in math_references[:3]:  # 처음 3개만 표시
        print(f"   📄 {file_path}")
        # Math 관련 라인 찾기
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'Math' in line and ('button' in line.lower() or 'link' in line.lower()):
                print(f"      라인 {i+1}: {line.strip()}")
    
    # 3. 가이드 페이지 경로 찾기
    print("\n3. 가이드 페이지 경로 검색:")
    guide_paths = []
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.tsx', '.jsx', '.ts', '.js')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'guides' in content and 'math' in content.lower():
                            guide_paths.append((file_path, content))
                except:
                    continue
    
    for file_path, content in guide_paths[:3]:
        print(f"   📄 {file_path}")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'guides' in line and 'math' in line.lower():
                print(f"      라인 {i+1}: {line.strip()}")

def generate_fix_suggestions():
    """수정 방안 제시"""
    print("\n🔧 수정 방안 제시")
    print("=" * 60)
    
    print("\n1. 즉시 적용 가능한 수정:")
    print("   📝 Math 버튼 클릭 핸들러 수정")
    print("   " + "="*50)
    print("   // 수정 전")
    print("   const handleMathClick = () => {")
    print("     navigate('/guides/us/math');")
    print("   };")
    print("")
    print("   // 수정 후")
    print("   const handleMathClick = () => {")
    print("     navigate('/math/select-grade');")
    print("   };")
    
    print("\n2. 새 라우트 추가:")
    print("   📝 routes.tsx 또는 App.tsx에 추가")
    print("   " + "="*50)
    print("   {")
    print("     path: '/math',")
    print("     element: <MathGradeSelection />,")
    print("     children: [")
    print("       {")
    print("         path: 'select-grade',")
    print("         element: <GradeSelection />")
    print("       },")
    print("       {")
    print("         path: 'categories/:grade',")
    print("         element: <CategorySelection />")
    print("       }")
    print("     ]")
    print("   }")
    
    print("\n3. 새 컴포넌트 생성:")
    print("   📝 components/math/MathGradeSelection.tsx")
    print("   " + "="*50)
    print("   import React from 'react';")
    print("   import { useNavigate } from 'react-router-dom';")
    print("")
    print("   export const MathGradeSelection = () => {")
    print("     const navigate = useNavigate();")
    print("     const grades = ['G06', 'G07', 'G08', 'G09', 'G10', 'G11', 'G12', 'SAT', 'AP'];")
    print("")
    print("     return (")
    print("       <div className='math-grade-selection'>")
    print("         <h2>Choose Your Grade</h2>")
    print("         <div className='grade-grid'>")
    print("           {grades.map(grade => (")
    print("             <div key={grade} className='grade-card'")
    print("                  onClick={() => navigate(`/math/categories/${grade}`)}>")
    print("               <h3>{grade}</h3>")
    print("               <p>Mathematics</p>")
    print("             </div>")
    print("           ))}")
    print("         </div>")
    print("       </div>")
    print("     );")
    print("   };")

def create_implementation_files():
    """구현 파일 생성"""
    print("\n📁 구현 파일 생성")
    print("=" * 60)
    
    # 1. MathGradeSelection 컴포넌트
    math_component = '''import React from 'react';
import { useNavigate } from 'react-router-dom';
import './MathGradeSelection.css';

export const MathGradeSelection = () => {
  const navigate = useNavigate();
  const grades = [
    { id: 'G06', name: 'Grade 6' },
    { id: 'G07', name: 'Grade 7' },
    { id: 'G08', name: 'Grade 8' },
    { id: 'G09', name: 'Grade 9' },
    { id: 'G10', name: 'Grade 10' },
    { id: 'G11', name: 'Grade 11' },
    { id: 'G12', name: 'Grade 12' },
    { id: 'SAT', name: 'SAT' },
    { id: 'AP', name: 'AP' }
  ];

  const handleGradeClick = (gradeId: string) => {
    navigate(`/math/categories/${gradeId}`);
  };

  return (
    <div className="math-grade-selection">
      <div className="container">
        <h1 className="page-title">DreamSeedAI Mathematics</h1>
        <p className="page-subtitle">Choose your grade to start solving math problems</p>
        
        <div className="grade-grid">
          {grades.map(grade => (
            <div 
              key={grade.id} 
              className="grade-card"
              onClick={() => handleGradeClick(grade.id)}
            >
              <h3>{grade.name}</h3>
              <p>Mathematics</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
'''
    
    # 2. CSS 파일
    css_content = '''.math-grade-selection {
  padding: 2rem 0;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.page-title {
  text-align: center;
  color: white;
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.page-subtitle {
  text-align: center;
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.2rem;
  margin-bottom: 3rem;
}

.grade-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.grade-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.grade-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.grade-card h3 {
  color: #333;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.grade-card p {
  color: #666;
  font-size: 1rem;
  margin: 0;
}

@media (max-width: 768px) {
  .grade-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .grade-card {
    padding: 1.5rem;
  }
  
  .page-title {
    font-size: 2rem;
  }
}
'''
    
    # 3. API 서비스 파일
    api_service = '''// services/mathApi.ts
export interface Category {
  category_id: string;
  category_name: string;
  question_count: number;
  depth: number;
}

export interface Question {
  question_id: string;
  title: string;
  content: string;
  difficulty: string;
  category: string;
  grade: string;
  subject: string;
}

export const mathApi = {
  async getCategories(grade: string): Promise<Category[]> {
    try {
      const response = await fetch(`/api/math/categories?grade=${grade}`);
      if (!response.ok) {
        throw new Error('Failed to fetch categories');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching categories:', error);
      return [];
    }
  },

  async getQuestions(grade: string, categoryId?: string, keyword?: string): Promise<{total_count: number, questions: Question[]}> {
    try {
      const params = new URLSearchParams({ grade });
      if (categoryId) params.append('category_id', categoryId);
      if (keyword) params.append('keyword', keyword);
      
      const response = await fetch(`/api/math/questions?${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch questions');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching questions:', error);
      return { total_count: 0, questions: [] };
    }
  },

  async getQuestion(questionId: string): Promise<Question | null> {
    try {
      const response = await fetch(`/api/math/question/${questionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch question');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching question:', error);
      return null;
    }
  }
};
'''
    
    # 파일 생성
    files_to_create = [
        ('components/math/MathGradeSelection.tsx', math_component),
        ('components/math/MathGradeSelection.css', css_content),
        ('services/mathApi.ts', api_service)
    ]
    
    for file_path, content in files_to_create:
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 파일 생성
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"   ✅ {file_path} 생성 완료")
        except Exception as e:
            print(f"   ❌ {file_path} 생성 실패: {e}")

def main():
    """메인 함수"""
    print("🚀 DreamSeedAI Math 버튼 연결 문제 빠른 해결")
    print("=" * 60)
    
    # 1. 현재 상태 진단
    diagnose_current_state()
    
    # 2. 수정 방안 제시
    generate_fix_suggestions()
    
    # 3. 구현 파일 생성
    create_implementation_files()
    
    print("\n" + "=" * 60)
    print("🎉 Math 버튼 연결 문제 해결 가이드 완료!")
    print("\n📋 다음 단계:")
    print("  1. 현재 라우팅 파일에서 Math 버튼 연결 경로 수정")
    print("  2. 생성된 컴포넌트 파일들을 프로젝트에 추가")
    print("  3. 라우터에 새 경로 추가")
    print("  4. API 연동 테스트")
    print("  5. UI/UX 미세 조정")
    
    print("\n💡 핵심 포인트:")
    print("  - Math 버튼 → /math/select-grade로 연결")
    print("  - 학년 선택 → 카테고리 선택 → 문제 목록 → 문제 표시")
    print("  - 기존 mpcstudy.com과 유사한 사용자 경험 제공")

if __name__ == "__main__":
    main()
