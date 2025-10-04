# DreamSeedAI Math 버튼 연결 문제 해결 액션 플랜

## 🎯 문제 정의
- **현재 상황**: Math 버튼 클릭 시 "Guide: math" 페이지 표시
- **목표**: 학년별 수학 문제 선택 페이지로 연결
- **기대 결과**: mpcstudy.com의 study-new.php와 유사한 사용자 경험

## 📋 단계별 해결 방안

### 1단계: 라우팅 확인 및 수정 🔗

#### 1.1 현재 라우팅 상태 파악
```bash
# 프론트엔드 라우팅 파일 확인
- routes.tsx 또는 router.js
- 현재 Math 버튼의 href/onClick 설정 확인
- 가이드 페이지 경로 (/guides/us/math) 확인
```

#### 1.2 라우팅 수정
```typescript
// 수정 전
<Link to="/guides/us/math">Math</Link>

// 수정 후  
<Link to="/math/select-grade">Math</Link>
// 또는
<Link to="/math">Math</Link>
```

#### 1.3 새 라우트 추가
```typescript
// routes.tsx에 추가
{
  path: "/math",
  element: <MathGradeSelection />,
  children: [
    {
      path: "select-grade",
      element: <GradeSelection />
    },
    {
      path: "categories/:grade",
      element: <CategorySelection />
    },
    {
      path: "questions/:grade/:category",
      element: <QuestionList />
    }
  ]
}
```

### 2단계: 컴포넌트 구조 파악 및 수정 🏗️

#### 2.1 현재 컴포넌트 분석
```typescript
// Home.tsx 또는 메인 컴포넌트에서
const handleMathClick = () => {
  // 현재: navigate('/guides/us/math')
  // 수정: navigate('/math/select-grade')
}
```

#### 2.2 새 컴포넌트 생성
```typescript
// components/math/MathGradeSelection.tsx
export const MathGradeSelection = () => {
  const grades = ['G06', 'G07', 'G08', 'G09', 'G10', 'G11', 'G12', 'SAT', 'AP'];
  
  return (
    <div className="math-grade-selection">
      <h2>Choose Your Grade</h2>
      <div className="grade-grid">
        {grades.map(grade => (
          <GradeCard key={grade} grade={grade} />
        ))}
      </div>
    </div>
  );
};
```

#### 2.3 컴포넌트 연결
```typescript
// App.tsx 또는 메인 라우터에서
import { MathGradeSelection } from './components/math/MathGradeSelection';
import { CategorySelection } from './components/math/CategorySelection';
import { QuestionList } from './components/math/QuestionList';
```

### 3단계: API·데이터 연동 🔌

#### 3.1 기존 API 활용
```typescript
// services/mathApi.ts
export const mathApi = {
  getCategories: async (grade: string) => {
    const response = await fetch(`/api/math/categories?grade=${grade}`);
    return response.json();
  },
  
  getQuestions: async (grade: string, categoryId?: string) => {
    const params = new URLSearchParams({ grade });
    if (categoryId) params.append('category_id', categoryId);
    
    const response = await fetch(`/api/math/questions?${params}`);
    return response.json();
  }
};
```

#### 3.2 데이터 연동 구현
```typescript
// components/math/CategorySelection.tsx
export const CategorySelection = () => {
  const { grade } = useParams();
  const [categories, setCategories] = useState([]);
  
  useEffect(() => {
    mathApi.getCategories(grade).then(setCategories);
  }, [grade]);
  
  return (
    <div className="category-selection">
      {categories.map(category => (
        <CategoryCard key={category.category_id} category={category} />
      ))}
    </div>
  );
};
```

### 4단계: UI/UX 설계 🎨

#### 4.1 사용자 플로우 설계
```
홈페이지 → Math 버튼 클릭 → 학년 선택 → 카테고리 선택 → 문제 목록 → 문제 표시
```

#### 4.2 UI 컴포넌트 설계
```typescript
// 학년 선택 카드
const GradeCard = ({ grade }) => (
  <div className="grade-card" onClick={() => navigate(`/math/categories/${grade}`)}>
    <h3>{grade}</h3>
    <p>Mathematics</p>
  </div>
);

// 카테고리 선택 카드  
const CategoryCard = ({ category }) => (
  <div className="category-card" onClick={() => navigate(`/math/questions/${grade}/${category.category_id}`)}>
    <h4>{category.category_name}</h4>
    <p>{category.question_count} questions</p>
  </div>
);
```

#### 4.3 반응형 디자인
```css
/* styles/math.css */
.grade-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  padding: 2rem;
}

@media (max-width: 768px) {
  .grade-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    padding: 1rem;
  }
}
```

### 5단계: 단계별 구현 및 테스트 🧪

#### 5.1 구현 순서
1. **라우팅 수정** → Math 버튼 연결 경로 변경
2. **기본 페이지 생성** → 학년 선택 페이지 생성
3. **API 연동** → 카테고리 및 문제 데이터 로드
4. **UI 완성** → 스타일링 및 반응형 디자인
5. **테스트** → 전체 플로우 검증

#### 5.2 테스트 체크리스트
```typescript
// 테스트 시나리오
const testScenarios = [
  {
    name: "Math 버튼 클릭",
    action: "홈페이지에서 Math 버튼 클릭",
    expected: "학년 선택 페이지로 이동"
  },
  {
    name: "학년 선택",
    action: "G09 학년 카드 클릭", 
    expected: "G09 수학 카테고리 목록 표시"
  },
  {
    name: "카테고리 선택",
    action: "Advanced Algebra 카테고리 클릭",
    expected: "해당 카테고리 문제 목록 표시"
  },
  {
    name: "문제 표시",
    action: "문제 클릭",
    expected: "TipTap + MathLive로 문제 표시"
  }
];
```

## 🚀 즉시 실행 가능한 액션

### A. 현재 상태 진단
```bash
# 1. 현재 라우팅 파일 확인
find . -name "routes.*" -o -name "router.*" -o -name "App.*"

# 2. Math 버튼 컴포넌트 찾기
grep -r "Math" --include="*.tsx" --include="*.jsx" .

# 3. 가이드 페이지 경로 확인
grep -r "guides/us/math" .
```

### B. 빠른 수정 (임시)
```typescript
// Home.tsx에서 Math 버튼 클릭 핸들러 수정
const handleMathClick = () => {
  // 임시: 새 탭에서 구현된 수학 홈페이지 열기
  window.open('http://localhost:8001/', '_blank');
  
  // 또는: 기존 가이드 페이지 대신 새 페이지로 이동
  // navigate('/math/select-grade');
};
```

### C. 점진적 구현
```typescript
// 1단계: 기본 라우팅만 수정
// 2단계: 간단한 학년 선택 페이지 생성
// 3단계: API 연동 추가
// 4단계: UI/UX 개선
// 5단계: 고급 기능 추가 (검색, 필터링 등)
```

## 📊 성공 지표

### 기능적 지표
- ✅ Math 버튼 클릭 시 학년 선택 페이지로 이동
- ✅ 학년 선택 후 카테고리 목록 표시
- ✅ 카테고리 선택 후 문제 목록 표시
- ✅ 문제 클릭 후 문제 표시 페이지로 이동

### 사용자 경험 지표
- ✅ 페이지 로딩 시간 < 2초
- ✅ 모바일 반응형 디자인
- ✅ 직관적인 네비게이션
- ✅ 기존 mpcstudy.com과 유사한 사용성

## 🎯 최종 목표

**"사용자가 DreamSeedAI 홈페이지에서 Math 버튼을 클릭했을 때, 
기존 mpcstudy.com의 study-new.php와 같은 학년별 수학 문제 선택 
경험을 제공하는 것"**

이 액션 플랜을 따라 진행하시면 Math 버튼 연결 문제를 체계적으로 해결할 수 있을 것입니다! 🚀
