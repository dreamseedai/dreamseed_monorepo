# Dashboard Routes Structure

교사/학부모/튜터용 대시보드 라우트 구조 및 컴포넌트 매핑

## Route Structure

### 1. Teacher Routes (교사용)

| Route | Component | Description |
|-------|-----------|-------------|
| `/teacher/dashboard/classes/:classId` | `TeacherClassDashboard` | 반 전체 시험 요약 및 학생 목록 |
| `/teacher/dashboard/students/:studentId` | `TeacherStudentDashboard` | 개별 학생 시험 히스토리 및 상세 분석 |

**API Endpoints:**
- `GET /api/dashboard/teacher/classes/{classId}/exams`
- `GET /api/dashboard/teacher/students/{studentId}/exams`

**Features:**
- 반 전체 평균 점수/등급 통계
- 학생별 최근 시험 결과
- 시험 타입별 필터링
- 학생 성적 추이 그래프
- θ (theta) 및 SE (standard error) 표시

---

### 2. Tutor Routes (튜터용)

| Route | Component | Description |
|-------|-----------|-------------|
| `/tutor/dashboard` | `TutorDashboard` | 담당 학생 전체 요약 |
| `/tutor/dashboard/students/:studentId` | `TutorStudentDashboard` | 개별 학생 시험 히스토리 |
| `/tutor/dashboard/classes/:classId` | `TutorClassDashboard` | 특정 반 시험 요약 (선택적) |

**API Endpoints:**
- `GET /api/dashboard/tutor/students/exams`
- `GET /api/dashboard/teacher/students/{studentId}/exams` (교사 API 재사용)
- `GET /api/dashboard/teacher/classes/{classId}/exams` (교사 API 재사용)

**Features:**
- 전체 학생 목록 및 최근 시험 요약
- 학생별 시험 횟수 및 평균 점수
- 전체 평균/최고/최저 점수 통계
- 학생 검색 및 정렬 기능
- 개별 학생 상세 분석

---

### 3. Parent Routes (학부모용)

| Route | Component | Description |
|-------|-----------|-------------|
| `/parent/dashboard` | `ParentDashboard` | 자녀 목록 (복수 자녀 지원) |
| `/parent/dashboard/children/:studentId` | `ParentChildDashboard` | 자녀 시험 히스토리 및 성적 분석 |

**API Endpoints:**
- `GET /api/dashboard/parent/children/{studentId}/exams`

**Features:**
- 자녀별 최근 시험 결과
- 점수/등급/백분위 표시
- 성적 추이 그래프 (간소화)
- θ/SE 기술 정보 숨김
- 시험 날짜 및 소요 시간 표시

---

### 4. Common Routes (공통)

| Route | Component | Description |
|-------|-----------|-------------|
| `/dashboard/exams/:examSessionId` | `ExamSessionDetail` | 시험 세션 상세 정보 |

**API Endpoints:**
- `GET /api/dashboard/exams/{examSessionId}`

**Features:**
- 시험 기본 정보 (타입, 날짜, 소요 시간)
- 점수/등급/백분위/θ/SE
- 문항별 응답 기록 (Attempt 목록)
- 정답/오답 시각화
- θ 변화 그래프

---

## Component Structure

### Frontend Component Hierarchy

```
src/
├── pages/
│   ├── teacher/
│   │   └── dashboard/
│   │       ├── classes/
│   │       │   └── [classId].tsx          → TeacherClassDashboard
│   │       └── students/
│   │           └── [studentId].tsx        → TeacherStudentDashboard
│   │
│   ├── tutor/
│   │   └── dashboard/
│   │       ├── index.tsx                  → TutorDashboard
│   │       ├── classes/
│   │       │   └── [classId].tsx          → TutorClassDashboard
│   │       └── students/
│   │           └── [studentId].tsx        → TutorStudentDashboard
│   │
│   ├── parent/
│   │   └── dashboard/
│   │       ├── index.tsx                  → ParentDashboard
│   │       └── children/
│   │           └── [studentId].tsx        → ParentChildDashboard
│   │
│   └── exam/
│       └── [examSessionId].tsx            → ExamSessionDetail
│
└── components/
    └── dashboard/
        ├── ScoreCard.tsx                  → 점수 카드 컴포넌트
        ├── GradeDistribution.tsx          → 등급 분포 차트
        ├── StudentList.tsx                → 학생 목록
        ├── ExamHistory.tsx                → 시험 히스토리 테이블
        ├── ThetaChart.tsx                 → θ 변화 그래프
        ├── StatisticsPanel.tsx            → 통계 패널
        └── AttemptList.tsx                → 문항별 응답 목록
```

---

## URL Examples

### Teacher Examples

```
/teacher/dashboard/classes/1
  → 수학 1반 전체 시험 요약

/teacher/dashboard/students/5
  → 김철수 학생의 시험 히스토리
```

### Tutor Examples

```
/tutor/dashboard
  → 담당 학생 전체 요약 (15명)

/tutor/dashboard/students/5
  → 김철수 학생의 상세 분석

/tutor/dashboard/classes/1
  → 수학 1반 요약 (선택적)
```

### Parent Examples

```
/parent/dashboard
  → 자녀 목록 (김철수, 김영희)

/parent/dashboard/children/5
  → 김철수의 시험 히스토리
```

### Common Examples

```
/dashboard/exams/123
  → 시험 세션 123번 상세 정보
```

---

## API to Component Mapping

| Component | API Endpoint | Data |
|-----------|--------------|------|
| `TeacherClassDashboard` | `GET /api/dashboard/teacher/classes/{classId}/exams` | 반 정보, 학생 목록, 시험 목록 |
| `TeacherStudentDashboard` | `GET /api/dashboard/teacher/students/{studentId}/exams` | 학생 정보, 시험 히스토리, 통계 |
| `TutorDashboard` | `GET /api/dashboard/tutor/students/exams` | 전체 학생 목록, 최근 시험, 통계 |
| `TutorStudentDashboard` | `GET /api/dashboard/teacher/students/{studentId}/exams` | 학생 정보, 시험 히스토리 |
| `TutorClassDashboard` | `GET /api/dashboard/teacher/classes/{classId}/exams` | 반 정보, 학생 목록 |
| `ParentDashboard` | (자체 구현 or 학생 목록 API) | 자녀 목록 |
| `ParentChildDashboard` | `GET /api/dashboard/parent/children/{studentId}/exams` | 자녀 시험 히스토리, 간소화된 통계 |
| `ExamSessionDetail` | `GET /api/dashboard/exams/{examSessionId}` | 시험 상세, 문항 응답 |

---

## Data Flow

### Teacher: Class Dashboard Flow

```
User → /teacher/dashboard/classes/1
  ↓
TeacherClassDashboard Component
  ↓
GET /api/dashboard/teacher/classes/1/exams
  ↓
Response:
  - class_id, name, subject
  - student_count
  - exam_sessions[] (최근 50개)
  - students[] (각 학생의 latest_exam 포함)
  ↓
Render:
  - ScoreCard (평균 점수)
  - GradeDistribution (등급 분포 차트)
  - StudentList (학생별 최근 시험)
```

### Tutor: All Students Flow

```
User → /tutor/dashboard
  ↓
TutorDashboard Component
  ↓
GET /api/dashboard/tutor/students/exams
  ↓
Response:
  - tutor_id
  - students[] (각 학생의 latest_exam 포함)
  - statistics (전체 평균, 최고/최저)
  ↓
Render:
  - StatisticsPanel (전체 통계)
  - StudentList (필터/정렬 가능)
  - 학생 클릭 → /tutor/dashboard/students/:id
```

### Parent: Child Dashboard Flow

```
User → /parent/dashboard/children/5
  ↓
ParentChildDashboard Component
  ↓
GET /api/dashboard/parent/children/5/exams
  ↓
Response:
  - student_id, name, grade
  - exams[] (θ/SE 제외)
  - statistics (평균, 추이)
  ↓
Render:
  - ScoreCard (최근 점수)
  - ExamHistory (시험 목록, 간소화)
  - TrendChart (성적 추이)
```

---

## Navigation Structure

### Teacher Navigation

```
Dashboard
├── Classes
│   ├── 수학 1반 → /teacher/dashboard/classes/1
│   ├── 수학 2반 → /teacher/dashboard/classes/2
│   └── ...
└── Students
    ├── 김철수 → /teacher/dashboard/students/5
    ├── 이영희 → /teacher/dashboard/students/6
    └── ...
```

### Tutor Navigation

```
Dashboard
├── All Students → /tutor/dashboard
├── Classes (Optional)
│   └── 수학 특강반 → /tutor/dashboard/classes/1
└── Recent Exams
    └── (시험 클릭 → /dashboard/exams/:id)
```

### Parent Navigation

```
Dashboard
└── My Children
    ├── 김철수 → /parent/dashboard/children/5
    └── 김영희 → /parent/dashboard/children/6
```

---

## Responsive Design

### Desktop (≥1024px)
- 사이드바 네비게이션 (고정)
- 2-3 컬럼 레이아웃
- 차트 및 그래프 전체 표시

### Tablet (768px-1023px)
- 접을 수 있는 사이드바
- 2 컬럼 레이아웃
- 차트 크기 조정

### Mobile (<768px)
- 하단 탭 네비게이션
- 1 컬럼 레이아웃
- 차트 최소화 또는 스와이프

---

## Permissions Matrix

| Route | Teacher | Tutor | Parent | Student |
|-------|---------|-------|--------|---------|
| `/teacher/dashboard/classes/:classId` | ✅ | ✅ | ❌ | ❌ |
| `/teacher/dashboard/students/:studentId` | ✅ | ✅ | ❌ | ❌ |
| `/tutor/dashboard` | ❌ | ✅ | ❌ | ❌ |
| `/tutor/dashboard/students/:studentId` | ❌ | ✅ | ❌ | ❌ |
| `/tutor/dashboard/classes/:classId` | ❌ | ✅ | ❌ | ❌ |
| `/parent/dashboard` | ❌ | ❌ | ✅ | ❌ |
| `/parent/dashboard/children/:studentId` | ❌ | ❌ | ✅ | ❌ |
| `/dashboard/exams/:examSessionId` | ✅ | ✅ | ✅ | ✅ |

**Notes:**
- Teacher/Tutor: 자신의 학생만
- Parent: 자신의 자녀만
- Student: 자신의 시험만

---

## Implementation Checklist

### Backend (✅ Completed)
- [x] Dashboard API 구현
- [x] 교사/튜터 API
- [x] 학부모 API
- [x] 공통 시험 상세 API
- [x] score_utils 통합
- [x] 권한 검증
- [x] 테스트 작성 (5/5 passing)

### Frontend (🔄 To Do)
- [ ] 라우트 설정 (Next.js/React Router)
- [ ] TeacherClassDashboard 컴포넌트
- [ ] TeacherStudentDashboard 컴포넌트
- [ ] TutorDashboard 컴포넌트
- [ ] TutorStudentDashboard 컴포넌트
- [ ] TutorClassDashboard 컴포넌트
- [ ] ParentDashboard 컴포넌트
- [ ] ParentChildDashboard 컴포넌트
- [ ] ExamSessionDetail 컴포넌트
- [ ] 공통 컴포넌트 (ScoreCard, Charts 등)
- [ ] API 클라이언트 함수
- [ ] 인증/권한 미들웨어
- [ ] 반응형 디자인
- [ ] E2E 테스트

### Documentation (✅ Completed)
- [x] API 문서 (DASHBOARD_API.md)
- [x] 라우트 구조 (DASHBOARD_ROUTES.md)

---

## Next Steps

1. **Frontend 프레임워크 선택**
   - Next.js 13+ (App Router)
   - React Router 6+
   - Remix

2. **UI 라이브러리 선택**
   - Material-UI
   - Ant Design
   - Chakra UI
   - shadcn/ui

3. **차트 라이브러리**
   - Recharts (추천)
   - Chart.js
   - Victory

4. **상태 관리**
   - React Query (추천, API 캐싱)
   - Zustand
   - Redux Toolkit

5. **타입 안정성**
   - TypeScript 필수
   - API 응답 타입 정의
   - Zod로 런타임 검증

---

## Example Code Snippets

### API Client (TypeScript)

```typescript
// lib/api/dashboard.ts
import axios from 'axios';

export interface ExamSummary {
  exam_session_id: number;
  score: number;
  grade_numeric: number;
  grade_letter: string;
  percentile: number;
}

export interface ClassDashboardData {
  class_id: number;
  name: string;
  student_count: number;
  exam_sessions: ExamSummary[];
  students: StudentSummary[];
}

export const getTeacherClassDashboard = async (
  classId: number
): Promise<ClassDashboardData> => {
  const { data } = await axios.get(
    `/api/dashboard/teacher/classes/${classId}/exams`
  );
  return data;
};

export const getTutorAllStudents = async (): Promise<TutorDashboardData> => {
  const { data } = await axios.get('/api/dashboard/tutor/students/exams');
  return data;
};

export const getParentChildExams = async (
  studentId: number
): Promise<ParentDashboardData> => {
  const { data } = await axios.get(
    `/api/dashboard/parent/children/${studentId}/exams`
  );
  return data;
};
```

### React Component (with React Query)

```typescript
// pages/teacher/dashboard/classes/[classId].tsx
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { getTeacherClassDashboard } from '@/lib/api/dashboard';
import { ScoreCard, StudentList } from '@/components/dashboard';

export default function TeacherClassDashboard() {
  const { classId } = useParams();
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['teacher-class', classId],
    queryFn: () => getTeacherClassDashboard(Number(classId)),
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading class data</div>;

  return (
    <div className="dashboard-container">
      <h1>{data.name}</h1>
      <ScoreCard 
        avgScore={calculateAverage(data.exam_sessions)}
        studentCount={data.student_count}
      />
      <StudentList students={data.students} />
    </div>
  );
}
```

---

## Related Documentation

- [Dashboard API Documentation](./DASHBOARD_API.md)
- [Authentication Guide](./AUTH_IMPLEMENTATION_GUIDE.md)
- [Frontend Development Setup](./DEV_ENVIRONMENT_VSCODE.md)

---

**Last Updated:** 2024-11-20
**Status:** Backend ✅ Complete | Frontend 🔄 Pending
