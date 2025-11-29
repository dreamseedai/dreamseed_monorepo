# Dashboard UI Implementation Guide

## 📋 Overview

교사/학부모 대시보드 프론트엔드 UI 구현 완료.

**구현 위치**: `admin_front/components/dashboard/`
- `TeacherClassDashboard.tsx` (420 lines) - 교사용 반 전체 요약
- `TeacherStudentDashboard.tsx` (450 lines) - 교사용 학생 개별 히스토리
- `ParentChildDashboard.tsx` (480 lines) - 학부모용 자녀 시험 결과

**기술 스택**: React + TypeScript + Next.js + Tailwind CSS

---

## 🎨 Component Architecture

### 1. TeacherClassDashboard

**Purpose**: 교사가 반 전체 시험 요약을 확인

**Features**:
- ✅ 반 평균 점수 카드
- ✅ 등급 분포 미리보기
- ✅ 학생별 최근 시험 결과 테이블
- ✅ 학생 상세 페이지로 이동 링크

**API**: `GET /api/dashboard/teacher/classes/{classId}/exams`

**Props**:
```typescript
interface TeacherClassDashboardProps {
  classId: number;
}
```

**Usage**:
```tsx
import { TeacherClassDashboard } from "@/components/dashboard";

export default function ClassDashboardPage({ params }: { params: { classId: string } }) {
  return <TeacherClassDashboard classId={parseInt(params.classId)} />;
}
```

### 2. TeacherStudentDashboard

**Purpose**: 교사가 개별 학생의 시험 히스토리를 상세 조회

**Features**:
- ✅ 학생 통계 (총 시험 수, 평균, 최근 점수, 점수 추이)
- ✅ 시험 히스토리 테이블 (날짜, 점수, 등급, θ, SE)
- ✅ 상태 뱃지 (완료, 진행중, 중단)
- ✅ 점수 변화 트렌드 표시

**API**: `GET /api/dashboard/teacher/students/{studentId}/exams`

**Props**:
```typescript
interface TeacherStudentDashboardProps {
  studentId: number;
}
```

**Usage**:
```tsx
import { TeacherStudentDashboard } from "@/components/dashboard";

export default function StudentDashboardPage({ params }: { params: { studentId: string } }) {
  return <TeacherStudentDashboard studentId={parseInt(params.studentId)} />;
}
```

### 3. ParentChildDashboard

**Purpose**: 학부모가 자녀의 시험 결과를 확인

**Features**:
- ✅ 최근 시험 결과 하이라이트 (점수, 등급, 석차)
- ✅ 요약 통계 (총 시험 수, 평균, 성적 변화)
- ✅ 시험 기록 테이블
- ✅ 백분위 석차 표시 ("상위 22.7%")
- ✅ 등급별 색상 뱃지

**API**: `GET /api/dashboard/parent/children/{studentId}/exams`

**Props**:
```typescript
interface ParentChildDashboardProps {
  studentId: number;
}
```

**Usage**:
```tsx
import { ParentChildDashboard } from "@/components/dashboard";

export default function ChildDashboardPage({ params }: { params: { studentId: string } }) {
  return <ParentChildDashboard studentId={parseInt(params.studentId)} />;
}
```

---

## 🛣️ Next.js App Router Setup

### Directory Structure

```
admin_front/
├── app/
│   ├── teacher/
│   │   └── dashboard/
│   │       ├── classes/
│   │       │   └── [classId]/
│   │       │       └── page.tsx          # TeacherClassDashboard
│   │       └── students/
│   │           └── [studentId]/
│   │               └── page.tsx          # TeacherStudentDashboard
│   └── parent/
│       └── dashboard/
│           └── children/
│               └── [studentId]/
│                   └── page.tsx          # ParentChildDashboard
└── components/
    └── dashboard/
        ├── TeacherClassDashboard.tsx     ✅ Created
        ├── TeacherStudentDashboard.tsx   ✅ Created
        ├── ParentChildDashboard.tsx      ✅ Created
        └── index.ts                      ✅ Created
```

### Route Examples

| URL | Component | Description |
|-----|-----------|-------------|
| `/teacher/dashboard/classes/1` | TeacherClassDashboard | 1반 전체 요약 |
| `/teacher/dashboard/students/5` | TeacherStudentDashboard | 학생 5번 히스토리 |
| `/parent/dashboard/children/5` | ParentChildDashboard | 자녀 5번 성적 |

---

## 📄 Page Implementation Examples

### 1. Teacher Class Dashboard Page

```tsx
// app/teacher/dashboard/classes/[classId]/page.tsx
"use client";

import { TeacherClassDashboard } from "@/components/dashboard";

export default function TeacherClassPage({
  params,
}: {
  params: { classId: string };
}) {
  const classId = parseInt(params.classId);

  if (isNaN(classId)) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">잘못된 반 ID입니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TeacherClassDashboard classId={classId} />
    </div>
  );
}
```

### 2. Teacher Student Dashboard Page

```tsx
// app/teacher/dashboard/students/[studentId]/page.tsx
"use client";

import { TeacherStudentDashboard } from "@/components/dashboard";

export default function TeacherStudentPage({
  params,
}: {
  params: { studentId: string };
}) {
  const studentId = parseInt(params.studentId);

  if (isNaN(studentId)) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">잘못된 학생 ID입니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TeacherStudentDashboard studentId={studentId} />
    </div>
  );
}
```

### 3. Parent Child Dashboard Page

```tsx
// app/parent/dashboard/children/[studentId]/page.tsx
"use client";

import { ParentChildDashboard } from "@/components/dashboard";

export default function ParentChildPage({
  params,
}: {
  params: { studentId: string };
}) {
  const studentId = parseInt(params.studentId);

  if (isNaN(studentId)) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">잘못된 학생 ID입니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <ParentChildDashboard studentId={studentId} />
    </div>
  );
}
```

---

## 🎨 UI/UX Features

### Design System

**Colors**:
- Primary: Blue (#2563eb)
- Success: Green (#16a34a)
- Warning: Yellow (#eab308)
- Error: Red (#dc2626)
- Grades: A(Green), B(Blue), C(Yellow), D(Orange), F(Red)

**Typography**:
- Headings: font-bold
- Body: text-sm
- Numbers: font-mono (for theta/SE)

**Components**:
- Cards: rounded-xl with shadow-sm
- Tables: hover:bg-gray-50 transition
- Badges: rounded-full with color coding
- Loading: animate-spin spinner
- Error: red-50 background with border

### Responsive Design

```tsx
// Mobile-first approach with Tailwind
<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
  {/* Stacks on mobile, 3 columns on desktop */}
</div>
```

### Loading States

```tsx
if (loading) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}
```

### Error Handling

```tsx
if (error) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <h3 className="text-red-800 font-semibold mb-2">오류 발생</h3>
      <p className="text-red-600 text-sm">{error}</p>
    </div>
  );
}
```

---

## 🔧 Configuration

### 1. API Base URL

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDashboardData(endpoint: string) {
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      // TODO: Add authentication
      // Authorization: `Bearer ${getToken()}`,
    },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.statusText}`);
  }

  return res.json();
}
```

### 2. Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. TypeScript Types

```typescript
// types/dashboard.ts
export type ExamSummary = {
  exam_session_id: number;
  student_id: number;
  exam_type: string;
  ended_at: string | null;
  score: number | null;
  grade_numeric: number | null;
  grade_letter: string | null;
};

export type ClassExamSummary = {
  class_id: number;
  name: string;
  subject: string;
  student_count: number;
  exam_summary: ExamSummary[];
  students: StudentSummary[];
};

// ... more types
```

---

## 🧪 Testing

### Manual Testing Checklist

**Teacher Class Dashboard**:
- [ ] Displays class name and subject
- [ ] Shows correct student count
- [ ] Calculates average score correctly
- [ ] Displays grade distribution
- [ ] Student table shows all students
- [ ] "상세 보기" link navigates correctly
- [ ] Loading spinner appears during fetch
- [ ] Error message displays on API failure

**Teacher Student Dashboard**:
- [ ] Displays student ID
- [ ] Shows all exam history
- [ ] Calculates statistics correctly (avg, trend)
- [ ] Formats dates properly
- [ ] Status badges display with correct colors
- [ ] Theta and SE values are formatted correctly
- [ ] "돌아가기" link works

**Parent Child Dashboard**:
- [ ] Latest exam highlight displays correctly
- [ ] Percentile rank calculates properly ("상위 X%")
- [ ] Grade badges show correct colors
- [ ] Score trend shows correct arrow (↑/↓/→)
- [ ] Table displays all exams
- [ ] Info card explains CAT system

### Component Testing Example

```typescript
// __tests__/dashboard/TeacherClassDashboard.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import { TeacherClassDashboard } from "@/components/dashboard";

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        class_id: 1,
        name: "고1-1반",
        subject: "수학",
        student_count: 25,
        exam_summary: [],
        students: [],
      }),
  })
) as jest.Mock;

describe("TeacherClassDashboard", () => {
  it("renders class name and subject", async () => {
    render(<TeacherClassDashboard classId={1} />);

    await waitFor(() => {
      expect(screen.getByText("고1-1반")).toBeInTheDocument();
      expect(screen.getByText("(수학)")).toBeInTheDocument();
    });
  });

  it("displays loading spinner initially", () => {
    render(<TeacherClassDashboard classId={1} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
```

---

## 🚀 Deployment

### Build & Deploy Steps

```bash
cd admin_front

# Install dependencies
npm install

# Build for production
npm run build

# Start production server
npm start

# Or deploy to Vercel
vercel --prod
```

### Environment Variables (Production)

```bash
# Production API endpoint
NEXT_PUBLIC_API_URL=https://api.dreamseed.ai
```

### Performance Optimization

**1. Code Splitting**:
```tsx
// Lazy load dashboard components
const TeacherClassDashboard = dynamic(
  () => import("@/components/dashboard/TeacherClassDashboard"),
  { loading: () => <LoadingSpinner /> }
);
```

**2. Data Caching**:
```typescript
// Use SWR for automatic caching
import useSWR from "swr";

const { data, error } = useSWR(
  `/api/dashboard/teacher/classes/${classId}/exams`,
  fetcher
);
```

**3. Image Optimization**:
```tsx
import Image from "next/image";

<Image
  src="/icons/grade-a.svg"
  width={32}
  height={32}
  alt="Grade A"
/>
```

---

## 📊 Wireframes

### Teacher Class Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  고1-1반 (수학)                                              │
│  학생 수: 25명 · 최근 시험 수: 50건                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 반 평균 점수 │  │  총 시험 수  │  │  등급 분포  │        │
│  │   68.5점    │  │    50건     │  │  1등급: 3명 │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  학생별 최근 시험 요약                                       │
│  ┌─────┬────────┬────────┬────────┬──────────┐          │
│  │학생ID│최근점수│최근등급│응시횟수│          │          │
│  ├─────┼────────┼────────┼────────┼──────────┤          │
│  │  1  │ 88.5점 │ A (2등급)│   3   │ 상세보기→│          │
│  │  2  │ 75.3점 │ B (3등급)│   2   │ 상세보기→│          │
│  └─────┴────────┴────────┴────────┴──────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Teacher Student Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  ← 돌아가기                                                  │
│  학생 1 시험 히스토리                                         │
│  최근 시험: 88.5점 · 등급: A                                 │
├─────────────────────────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                  │
│  │총시험수│  │평균점수│  │최근점수│  │점수추이│                  │
│  │  3건  │  │ 82.3점│  │ 88.5점│  │ +6.2↑│                  │
│  └──────┘  └──────┘  └──────┘  └──────┘                  │
├─────────────────────────────────────────────────────────────┤
│  시험 목록                                                   │
│  ┌──────┬────┬────┬────┬────┬─────┬────┐              │
│  │ 날짜 │유형│상태│점수│등급│θ(Theta)│SE │              │
│  ├──────┼────┼────┼────┼────┼─────┼────┤              │
│  │11/20 │모의│완료│88.5│ A │ 0.75│0.35│              │
│  │11/15 │연습│완료│82.3│ B │ 0.52│0.38│              │
│  └──────┴────┴────┴────┴────┴─────┴────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Parent Child Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  자녀 학업 현황                                              │
│  학생 ID: 1                                                 │
├─────────────────────────────────────────────────────────────┤
│  🎯 최근 시험 결과 (하이라이트)                              │
│  ┌──────────┬──────────┬──────────┬──────────┐          │
│  │ 시험날짜  │   점수   │   등급   │   석차   │          │
│  │ 11/20    │  88.5점  │ [A] 2등급│ 상위18%  │          │
│  └──────────┴──────────┴──────────┴──────────┘          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 총 시험 수│  │  평균 점수│  │  성적 변화│              │
│  │   3건    │  │  82.3점  │  │  +6.2↑  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
├─────────────────────────────────────────────────────────────┤
│  시험 기록                                                   │
│  ┌──────┬────────┬────┬────┬────────┐                  │
│  │ 날짜 │시험종류│점수│등급│  석차  │                  │
│  ├──────┼────────┼────┼────┼────────┤                  │
│  │11/20 │ 모의고사│88.5│ A │상위18% │ [최신]          │
│  │11/15 │  연습  │82.3│ B │상위23% │                  │
│  └──────┴────────┴────┴────┴────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Next Steps

### High Priority

1. **Create Page Files** ⚠️
   ```bash
   # Create directory structure
   mkdir -p admin_front/app/teacher/dashboard/classes/[classId]
   mkdir -p admin_front/app/teacher/dashboard/students/[studentId]
   mkdir -p admin_front/app/parent/dashboard/children/[studentId]
   
   # Create page.tsx files (see examples above)
   ```

2. **Add Authentication** ⚠️
   ```typescript
   // lib/auth.ts
   export function getAuthToken(): string | null {
     return localStorage.getItem("auth_token");
   }
   
   // Update fetch calls to include token
   headers: {
     Authorization: `Bearer ${getAuthToken()}`,
   }
   ```

3. **Test with Real Data**
   - Start backend server (`uvicorn main:app --reload`)
   - Seed test data (teachers, students, exams)
   - Navigate to `/teacher/dashboard/classes/1`
   - Verify data displays correctly

### Medium Priority

4. **Add Charts** (Optional)
   ```bash
   npm install recharts
   ```
   
   ```tsx
   import { LineChart, Line, XAxis, YAxis } from "recharts";
   
   <LineChart data={scoreHistory}>
     <Line type="monotone" dataKey="score" stroke="#2563eb" />
   </LineChart>
   ```

5. **Add Filters & Search**
   - Filter by exam type (placement/practice/mock)
   - Date range picker
   - Search students by name

6. **Export Features**
   - Export to Excel
   - Print friendly view
   - PDF report generation

### Low Priority

7. **Real-time Updates**
   - WebSocket for live exam progress
   - Push notifications for new results

8. **Advanced Analytics**
   - Topic-level performance
   - Comparison with class average
   - Personalized recommendations

---

## 📞 Support

**Component Location**: `admin_front/components/dashboard/`

**Backend API**: See `docs/implementation/DASHBOARD_API_SUMMARY.md`

**Styling**: Tailwind CSS utility classes

**Icons**: Consider adding Heroicons or Lucide React

---

## ✅ Summary

**Dashboard UI 구현 완료** (Ready for Integration):

**Components** (3 files, ~1,350 lines):
- ✅ TeacherClassDashboard.tsx - 반 전체 요약 (420 lines)
- ✅ TeacherStudentDashboard.tsx - 학생 히스토리 (450 lines)
- ✅ ParentChildDashboard.tsx - 자녀 성적 (480 lines)
- ✅ index.ts - Export file

**Features**:
- ✅ Responsive design (mobile-first)
- ✅ Loading & error states
- ✅ Color-coded grade badges
- ✅ Score trend indicators
- ✅ Percentile rank display
- ✅ CAT system explanations
- ✅ Clean, modern UI with Tailwind

**Integration Status**:
- ✅ Components created
- ⏳ Page files pending (3 files needed)
- ⏳ Authentication pending
- ⏳ API proxy configuration pending

**Next Steps**:
1. Create page.tsx files in app/ directory
2. Configure API base URL
3. Add authentication headers
4. Test with real data

**Production Status**: 🟡 **NEEDS PAGE ROUTING SETUP**

Total CAT system deliverables:
- **Backend**: Redis + Score Utils + Dashboard API (~2,880 lines)
- **Frontend**: Dashboard Components (~1,350 lines)
- **Grand Total**: 11 files, ~4,230 lines ✅
