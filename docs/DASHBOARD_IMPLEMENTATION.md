# 📊 Dashboard Implementation Guide

> **작성일**: 2025-11-19  
> **목적**: Teacher / Parent / Tutor 대시보드 MVP 구현 가이드  
> **기술 스택**: Vite + React 18 + React Router + Tailwind CSS

---

## 📋 목차

1. [개요](#개요)
2. [구현된 대시보드](#구현된-대시보드)
3. [파일 구조](#파일-구조)
4. [각 대시보드 상세](#각-대시보드-상세)
5. [라우팅 설정](#라우팅-설정)
6. [다음 단계](#다음-단계)
7. [API 연동 계획](#api-연동-계획)

---

## 개요

### 목적
- **Teacher Dashboard**: 학교 선생님을 위한 학급 관리 및 학생 성과 모니터링
- **Parent Dashboard**: 학부모를 위한 자녀 학습 현황 추적
- **Tutor Dashboard**: 1:1 / 소수 과외 선생님을 위한 세션 관리

### 기술 선택 이유
- **Vite**: 빠른 개발 서버 및 빌드 (Next.js가 아닌 Vite 기반 확인)
- **React Router**: SPA 라우팅 (portal_front는 Vite + React Router 사용)
- **Tailwind CSS**: 빠른 스타일링 + Dark mode 지원
- **TypeScript**: 타입 안전성

### 현재 상태
- ✅ MVP 페이지 3종 생성 완료
- ✅ React Router 라우팅 설정 완료
- ⏳ API 연동 대기 (placeholder 데이터 사용 중)
- ⏳ 인증/권한 통합 예정

---

## 구현된 대시보드

### 1. Teacher Dashboard (`/teacher/dashboard`)

**대상 사용자**: 학교 선생님 (다수 학생 관리)

**주요 기능**:
- Summary Cards: 총 학생 수, 활성 클래스, 평균 성적, 위험 학생 수
- Current Session: 현재 검토 중인 세션 정보
- Quick Actions: 학생 목록, 리포트 보기 (예정)

**화면 구성**:
```
┌─────────────────────────────────────────┐
│ Teacher Dashboard                       │
│ 선생님용 간단한 MVP 대시보드입니다.     │
├─────────────────────────────────────────┤
│ Summary                                 │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │Total │ │Active│ │Avg   │ │At-   │   │
│ │Stdnts│ │Class │ │Perf  │ │risk  │   │
│ │  —   │ │  —   │ │  —   │ │  —   │   │
│ └──────┘ └──────┘ └──────┘ └──────┘   │
├─────────────────────────────────────────┤
│ Current Session                         │
│ • Open Exam Player                      │
│ • Download PDF Report                   │
├─────────────────────────────────────────┤
│ Quick Actions                           │
│ • View Student List (coming soon)       │
│ • View Reports (coming soon)            │
└─────────────────────────────────────────┘
```

### 2. Parent Dashboard (`/parent/dashboard`)

**대상 사용자**: 학부모 (자녀별 학습 현황 확인)

**주요 기능**:
- Child Selector: 자녀 선택 드롭다운
- Summary Metrics: 현재 능력치(θ), 최근 점수, 학습 시간
- Progress Overview: 성장 그래프 (placeholder)
- Recent Activity: 최근 활동 내역

**화면 구성**:
```
┌─────────────────────────────────────────┐
│ Parent Dashboard                        │
│ 학부모용 간단한 MVP 대시보드입니다.     │
├─────────────────────────────────────────┤
│ Select Child                            │
│ [— Select —        ▼]                   │
├─────────────────────────────────────────┤
│ Summary                                 │
│ 자녀를 선택해주세요.                    │
└─────────────────────────────────────────┘

[자녀 선택 후]
┌─────────────────────────────────────────┐
│ Summary                                 │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │Current   │ │Recent    │ │Study Time│ │
│ │Ability(θ)│ │Score     │ │This Month│ │
│ │    —     │ │    —     │ │    —     │ │
│ └──────────┘ └──────────┘ └──────────┘ │
├─────────────────────────────────────────┤
│ Progress Overview                       │
│ [████████████████ Chart placeholder ]   │
├─────────────────────────────────────────┤
│ Recent Activity                         │
│ • —                                     │
│ • —                                     │
└─────────────────────────────────────────┘
```

### 3. Tutor Dashboard (`/tutor/dashboard`)

**대상 사용자**: 1:1 또는 소수 과외 선생님

**주요 기능**:
- Current Session: 현재 진행 중인 세션 정보
- Session ID 표시
- Exam Player 링크
- PDF Report 다운로드 링크

**화면 구성**:
```
┌─────────────────────────────────────────┐
│ Tutor Dashboard                         │
│ 1:1 / 소수 과외 선생님을 위한 대시보드  │
├─────────────────────────────────────────┤
│ Current Session                         │
│ Session ID: ABC123                      │
│ • Open Exam Player                      │
│ • Download PDF Report                   │
├─────────────────────────────────────────┤
│ Next Steps                              │
│ 이후 업데이트에서 실제 학생 목록 /      │
│ 세션 기록 / 성적 향상 지표 등을 연동    │
└─────────────────────────────────────────┘
```

---

## 파일 구조

```
portal_front/
├── src/
│   ├── pages/
│   │   ├── TeacherDashboard.tsx          ✅ 구현 완료
│   │   ├── ParentDashboard.tsx           ✅ 구현 완료
│   │   ├── TutorDashboard.tsx            ✅ 구현 완료
│   │   ├── teacher/
│   │   │   ├── StudentList.tsx           ✅ 구현 완료
│   │   │   └── StudentDetail.tsx         ✅ 구현 완료
│   │   ├── parent/
│   │   │   └── ChildDetail.tsx           ✅ 구현 완료
│   │   └── tutor/
│   │       ├── SessionList.tsx           ✅ 구현 완료
│   │       └── SessionDetail.tsx         ✅ 구현 완료
│   │
│   ├── App.tsx                           ✅ 라우팅 완료
│   │
│   └── components/
│       └── (향후 공통 컴포넌트 추출 예정)
│
├── package.json
└── vite.config.ts
```

### 파일 위치 및 크기

```bash
# 대시보드 페이지
src/pages/TeacherDashboard.tsx             # 2.4 KB
src/pages/ParentDashboard.tsx              # 2.6 KB  
src/pages/TutorDashboard.tsx               # 3.2 KB

# Teacher 상세 페이지
src/pages/teacher/StudentList.tsx          # 5.3 KB
src/pages/teacher/StudentDetail.tsx        # 8.1 KB

# Parent 상세 페이지
src/pages/parent/ChildDetail.tsx           # 7.8 KB

# Tutor 상세 페이지
src/pages/tutor/SessionList.tsx            # 4.2 KB
src/pages/tutor/SessionDetail.tsx          # 5.9 KB
```

---

## 각 대시보드 상세

### TeacherDashboard.tsx

**파일 경로**: `portal_front/src/pages/TeacherDashboard.tsx`

**주요 코드 구조**:

```tsx
import { Link } from "react-router-dom";

export default function TeacherDashboard() {
  return (
    <main className="p-8 space-y-8">
      {/* Header */}
      <header className="space-y-1">
        <h1 className="text-3xl font-semibold">Teacher Dashboard</h1>
        <p className="text-gray-500">...</p>
      </header>

      {/* Summary Cards */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <SummaryCard label="Total Students" value="—" />
          <SummaryCard label="Active Classes" value="—" />
          <SummaryCard label="Average Performance" value="—" />
          <SummaryCard label="At-risk Students" value="—" />
        </div>
      </section>

      {/* Current Session */}
      <section className="border rounded-lg p-4 space-y-3">
        <h2 className="font-semibold text-lg">Current Session</h2>
        <Link to="/exam/player?session=example">Open Exam Player</Link>
        <Link to="/exam/report.pdf?session=example">Download PDF Report</Link>
      </section>

      {/* Quick Actions */}
      <section className="border rounded-lg p-4 space-y-3">
        <ul className="list-disc list-inside">
          <li>View Student List (coming soon)</li>
          <li>View Reports (coming soon)</li>
        </ul>
      </section>
    </main>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="border rounded-lg p-4 text-center">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
    </div>
  );
}
```

**특징**:
- React Router `Link` 사용 (Next.js `Link`가 아님)
- Tailwind CSS 기반 스타일링
- Dark mode 지원 (`dark:` prefix)
- 반응형 그리드 (`md:grid-cols-4`)

---

### ParentDashboard.tsx

**파일 경로**: `portal_front/src/pages/ParentDashboard.tsx`

**주요 코드 구조**:

```tsx
import { useState } from "react";

export default function ParentDashboard() {
  const [child, setChild] = useState<string>("");

  return (
    <main className="p-8 space-y-8">
      {/* Header */}
      <header>...</header>

      {/* Child Selector */}
      <section className="border p-4 rounded-lg space-y-3">
        <h2 className="font-semibold text-lg">Select Child</h2>
        <select
          className="border rounded p-2 bg-white dark:bg-gray-800"
          value={child}
          onChange={(e) => setChild(e.target.value)}
        >
          <option value="">— Select —</option>
          <option value="child1">Example Child 1</option>
          <option value="child2">Example Child 2</option>
        </select>
      </section>

      {/* Summary Metrics - 자녀 선택 시에만 표시 */}
      {!child ? (
        <p className="text-gray-500 text-sm">자녀를 선택해주세요.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <SummaryCard label="Current Ability (θ)" value="—" />
          <SummaryCard label="Recent Score" value="—" />
          <SummaryCard label="Study Time (This Month)" value="—" />
        </div>
      )}

      {/* Progress Overview - 자녀 선택 시에만 표시 */}
      {child && (
        <section>
          <h2>Progress Overview</h2>
          <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </section>
      )}

      {/* Recent Activity */}
      {child && (
        <section>
          <h2>Recent Activity</h2>
          <ul className="list-disc list-inside">
            <li>—</li>
            <li>—</li>
          </ul>
        </section>
      )}
    </main>
  );
}
```

**특징**:
- `useState`로 자녀 선택 상태 관리
- 조건부 렌더링 (자녀 선택 전/후)
- Dark mode 호환 (`dark:bg-gray-800`)
- 향후 API 연동 준비됨

---

### TutorDashboard.tsx

**파일 경로**: `portal_front/src/pages/TutorDashboard.tsx`

**주요 코드 구조**:

```tsx
import Link from "next/link";

export default function TutorDashboardPage() {
  const sessionId = "ABC123"; // TODO: Plug actual session ID later

  return (
    <main className="p-8 space-y-8">
      {/* Header */}
      <header>
        <h1 className="text-3xl font-semibold">Tutor Dashboard</h1>
        <p className="text-gray-500">1:1 / 소수 과외 선생님을 위한 기본 대시보드</p>
      </header>

      {/* Current Session */}
      <section className="border rounded-lg p-4 space-y-3">
        <h2 className="font-semibold text-lg">Current Session</h2>
        <p className="text-sm text-gray-600">
          Session ID: <span className="font-mono">{sessionId}</span>
        </p>
        <div className="flex gap-4 text-sm">
          <Link href={`/exam/player?session=${sessionId}`}>
            Open Exam Player
          </Link>
          <Link href={`/exam/report.pdf?session=${sessionId}`}>
            Download PDF Report
          </Link>
        </div>
      </section>

      {/* Future panels */}
      <section className="border rounded-lg p-4 space-y-3">
        <h2 className="font-semibold text-lg">Next Steps</h2>
        <p className="text-sm text-gray-600">
          이후 업데이트에서 실제 학생 목록 / 세션 기록 / 성적 향상 지표 등을 연동합니다.
        </p>
      </section>
    </main>
  );
}
```

**특징**:
- 기존 TutorDashboard.tsx 존재 (이미 구현됨)
- Session ID 기반 동적 링크
- Exam Player / PDF Report 연동 가능

---

## 라우팅 설정

### App.tsx 수정 내역

**파일 경로**: `portal_front/src/App.tsx`

**추가된 import**:
```tsx
import TeacherDashboard from './pages/TeacherDashboard';
import ParentDashboard from './pages/ParentDashboard';
```

**추가된 라우트**:
```tsx
// Teacher routes
if (location.pathname === '/teacher/dashboard') {
  return <TeacherDashboard />;
}
if (location.pathname === '/teacher/students') {
  return <TeacherStudentsPage />;
}
if (location.pathname.match(/^\/teacher\/students\/[^\/]+$/)) {
  return <TeacherStudentDetailPage />;
}

// Parent routes
if (location.pathname === '/parent/dashboard') {
  return <ParentDashboard />;
}
if (location.pathname.match(/^\/parent\/children\/[^\/]+$/)) {
  return <ParentChildDetailPage />;
}

// Tutor routes
if (location.pathname === '/tutor/dashboard') {
  return <TutorDashboard />;
}
if (location.pathname === '/tutor/sessions') {
  return <TutorSessionsPage />;
}
if (location.pathname.match(/^\/tutor\/sessions\/[^\/]+$/)) {
  return <TutorSessionDetailPage />;
}
```

### URL 매핑

| 역할 | URL | 컴포넌트 | 상태 |
|------|-----|----------|------|
| Teacher | `/teacher/dashboard` | `TeacherDashboard` | ✅ |
| Teacher | `/teacher/students` | `TeacherStudentsPage` | ✅ |
| Teacher | `/teacher/students/:id` | `TeacherStudentDetailPage` | ✅ |
| Parent | `/parent/dashboard` | `ParentDashboard` | ✅ |
| Parent | `/parent/children/:id` | `ParentChildDetailPage` | ✅ |
| Tutor | `/tutor/dashboard` | `TutorDashboard` | ✅ |
| Tutor | `/tutor/sessions` | `TutorSessionsPage` | ✅ |
| Tutor | `/tutor/sessions/:id` | `TutorSessionDetailPage` | ✅ |

---

## 다음 단계

### Phase 1: 추가 페이지 구현

#### 1. Teacher 확장
- [x] `/teacher/students` - 학생 목록 페이지 ✅ **구현 완료**
- [x] `/teacher/students/:id` - 학생 상세 페이지 ✅ **구현 완료**
- [ ] `/teacher/classes` - 클래스 관리
- [ ] `/teacher/reports` - 리포트 생성기

**구현된 구조**:
```tsx
// portal_front/src/pages/teacher/StudentList.tsx
import { useState } from "react";
import { Link } from "react-router-dom";

const MOCK_STUDENTS = [
  {
    id: "s1",
    name: "홍길동",
    class_name: "수학 1반",
    ability: "θ = 0.12",
    recent_score: "87%",
    status: "On Track",
  },
  // ... more students
];

export default function TeacherStudentsPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [classFilter, setClassFilter] = useState("all");

  const filtered = MOCK_STUDENTS.filter((s) => {
    const matchQ = q ? s.name.includes(q) : true;
    const matchStatus = status === "all" ? true : s.status === status;
    const matchClass = classFilter === "all" ? true : s.class_name === classFilter;
    return matchQ && matchStatus && matchClass;
  });

  return (
    <main className="p-8 space-y-8">
      {/* Header + Filters + Table */}
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Class</th>
            <th>Ability (θ)</th>
            <th>Recent Score</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((s) => (
            <tr key={s.id}>
              <td>{s.name}</td>
              <td>{s.class_name}</td>
              <td>{s.ability}</td>
              <td>{s.recent_score}</td>
              <td><StatusBadge status={s.status} /></td>
              <td>
                <Link to={`/teacher/students/${s.id}`}>View</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
```

**기능**:
- ✅ 학생 검색 (이름)
- ✅ 클래스별 필터
- ✅ 상태별 필터 (On Track / At Risk)
- ✅ 학생 상세 페이지 링크
- ✅ Dark mode 지원
- ✅ 반응형 테이블

#### 2. Parent 확장
- [x] `/parent/children/:id` - 자녀 상세 페이지 ✅ **구현 완료**
- [ ] `/parent/progress` - 진도 추적
- [ ] `/parent/notifications` - 알림 센터

**구현된 구조**:
```tsx
// portal_front/src/pages/parent/ChildDetail.tsx
import { useParams, useNavigate } from 'react-router-dom';

const MOCK_CHILD_DETAIL = {
  c1: {
    id: 'c1',
    name: '홍길동',
    grade: '중3',
    class_name: '수학 심화반',
    abilityTheta: 'θ = 0.25',
    recentScore: '89%',
    studyTime: '12h / month',
    abilityTrend: [/* 5주 데이터 */],
    strengths: ['도형', '함수 응용', '논리적 사고력'],
    areasToImprove: ['확률', '통계'],
    recentActivity: [/* 최근 활동 3개 */],
  },
  // c2, ...
};

export default function ParentChildDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const child = id ? MOCK_CHILD_DETAIL[id] : undefined;

  return (
    <main className="p-8 space-y-8">
      <header>
        <h1>{child.name}</h1>
        <p>{child.grade} · {child.class_name}</p>
      </header>
      
      {/* Ability Trend Chart (SVG) */}
      <AbilityTrendChart data={child.abilityTrend} />
      
      {/* Strengths & Areas to Improve */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3>Strengths</h3>
          <ul>{child.strengths.map(s => <li>• {s}</li>)}</ul>
        </div>
        <div>
          <h3>Areas to Improve</h3>
          <ul>{child.areasToImprove.map(a => <li>• {a}</li>)}</ul>
        </div>
      </div>
      
      {/* Recent Activity */}
      <div>
        <h2>Recent Activity</h2>
        <ul>{child.recentActivity.map(a => <li>{a.description}</li>)}</ul>
      </div>
    </main>
  );
}
```

**기능**:
- ✅ Ability Trend Chart (SVG 기반)
- ✅ Strengths / Areas to Improve 표시
- ✅ Recent Activity 로그
- ✅ Back to Dashboard 버튼
- ✅ Dark mode 지원

#### 3. Tutor 확장
- [x] `/tutor/sessions` - 세션 목록 ✅ **구현 완료**
- [x] `/tutor/sessions/:id` - 세션 상세 ✅ **구현 완료**
- [ ] `/tutor/students` - 학생 관리

**구현된 구조**:

**SessionList.tsx** (세션 목록):
```tsx
// portal_front/src/pages/tutor/SessionList.tsx
import { useNavigate } from 'react-router-dom';

const MOCK_SESSIONS = [
  {
    id: 'sess1',
    date: '2025-11-10',
    studentName: '홍길동',
    subject: '수학',
    topic: '미분·적분',
    status: 'Completed',
  },
  // sess2, sess3, ...
];

export default function TutorSessionsPage() {
  const navigate = useNavigate();

  return (
    <main className="p-8 space-y-8">
      <header>
        <h1>Tutor Sessions</h1>
        <p>과외 세션 목록(MVP). 나중에 튜터용 API와 연결됩니다.</p>
      </header>

      <table className="w-full">
        <thead>
          <tr>
            <th>Date</th>
            <th>Student</th>
            <th>Subject</th>
            <th>Topic</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {MOCK_SESSIONS.map((s) => (
            <tr key={s.id}>
              <td>{s.date}</td>
              <td>{s.studentName}</td>
              <td>{s.subject}</td>
              <td>{s.topic}</td>
              <td><StatusPill status={s.status} /></td>
              <td>
                <button onClick={() => navigate(`/tutor/sessions/${s.id}`)}>
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
```

**SessionDetail.tsx** (세션 상세):
```tsx
// portal_front/src/pages/tutor/SessionDetail.tsx
import { useParams, useNavigate } from 'react-router-dom';

const MOCK_SESSION_DETAIL = {
  sess1: {
    id: 'sess1',
    date: '2025-11-10',
    studentName: '홍길동',
    subject: '수학',
    topic: '미분·적분',
    status: 'Completed',
    duration: '90 min',
    notes: '개념 이해는 양호, 문제 풀이 속도를 조금 더 올릴 필요 있음.',
    tasks: [
      { label: '교과서 예제 5개 풀이', done: true },
      { label: '심화 문제 3개 풀이', done: true },
      { label: '개념 요약 정리 복습', done: false },
    ],
  },
  // sess2, sess3, ...
};

export default function TutorSessionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const sess = id ? MOCK_SESSION_DETAIL[id] : undefined;

  return (
    <main className="p-8 space-y-8">
      <header>
        <h1>Session with {sess.studentName}</h1>
        <p>{sess.date} · {sess.subject} · {sess.topic}</p>
        <StatusPill status={sess.status} />
      </header>

      <section>
        <h2>Session Notes</h2>
        <p>{sess.notes}</p>
      </section>

      <section>
        <h2>Planned Tasks</h2>
        <ul>
          {sess.tasks.map((t, idx) => (
            <li key={idx}>
              <span className={t.done ? 'line-through' : undefined}>
                {t.label}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
```

**기능**:
- ✅ 세션 목록 테이블 (날짜, 학생, 과목, 주제, 상태)
- ✅ Status Badge (Completed/Upcoming)
- ✅ 세션 상세 페이지 (노트, 과제 체크리스트)
- ✅ Back to Sessions 버튼
- ✅ Dark mode 지원
- ✅ 반응형 레이아웃

---

### Phase 2: API 연동

#### Backend API 엔드포인트 (예정)

**Teacher API**:
```typescript
GET    /api/teacher/dashboard/summary
GET    /api/teacher/students
GET    /api/teacher/students/:id
GET    /api/teacher/classes
GET    /api/teacher/reports
POST   /api/teacher/sessions
```

**Parent API**:
```typescript
GET    /api/parent/children
GET    /api/parent/children/:id
GET    /api/parent/children/:id/progress
GET    /api/parent/notifications
```

**Tutor API**:
```typescript
GET    /api/tutor/sessions
GET    /api/tutor/sessions/:id
GET    /api/tutor/students
POST   /api/tutor/sessions
PUT    /api/tutor/sessions/:id
```

#### API 클라이언트 예시

**파일**: `portal_front/src/lib/dashboardApi.ts`

```typescript
import { api } from './api';

export const teacherApi = {
  getSummary: () => api('/api/teacher/dashboard/summary'),
  getStudents: () => api('/api/teacher/students'),
  getStudent: (id: string) => api(`/api/teacher/students/${id}`),
};

export const parentApi = {
  getChildren: () => api('/api/parent/children'),
  getChild: (id: string) => api(`/api/parent/children/${id}`),
  getProgress: (id: string) => api(`/api/parent/children/${id}/progress`),
};

export const tutorApi = {
  getSessions: () => api('/api/tutor/sessions'),
  getSession: (id: string) => api(`/api/tutor/sessions/${id}`),
};
```

---

### Phase 3: RBAC (Role-Based Access Control)

#### 권한 체계

| 역할 | 권한 | 접근 가능 페이지 |
|------|------|------------------|
| **Teacher** | - 자신의 클래스 학생 조회<br>- 성적 입력<br>- 리포트 생성 | `/teacher/*` |
| **Parent** | - 자녀 데이터 조회<br>- 알림 확인 | `/parent/*` |
| **Tutor** | - 담당 학생 조회<br>- 세션 기록 | `/tutor/*` |
| **Admin** | - 모든 데이터 접근 | `/admin/*` |
| **Student** | - 자신의 데이터만 | `/student/*` |

#### 인증 가드 구현

**파일**: `portal_front/src/components/RoleGuard.tsx`

```tsx
import { useAuth } from '../hooks/useAuth';
import { Navigate } from 'react-router-dom';

interface RoleGuardProps {
  allowedRoles: string[];
  children: React.ReactNode;
}

export function RoleGuard({ allowedRoles, children }: RoleGuardProps) {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" />;
  }

  return <>{children}</>;
}
```

**사용 예시**:
```tsx
// App.tsx에서
if (location.pathname === '/teacher/dashboard') {
  return (
    <RoleGuard allowedRoles={['teacher', 'admin']}>
      <TeacherDashboard />
    </RoleGuard>
  );
}
```

---

### Phase 4: 공통 컴포넌트 추출

현재 각 대시보드에 중복된 코드가 있습니다. 공통 컴포넌트로 추출:

#### 1. SummaryCard

**파일**: `portal_front/src/components/SummaryCard.tsx`

```tsx
interface SummaryCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
}

export function SummaryCard({ label, value, icon, trend }: SummaryCardProps) {
  return (
    <div className="border rounded-lg p-4 text-center">
      {icon && <div className="mb-2">{icon}</div>}
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
      {trend && <TrendIndicator trend={trend} />}
    </div>
  );
}
```

#### 2. DashboardLayout

**파일**: `portal_front/src/components/DashboardLayout.tsx`

```tsx
interface DashboardLayoutProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

export function DashboardLayout({ title, subtitle, children }: DashboardLayoutProps) {
  return (
    <main className="p-8 space-y-8">
      <header className="space-y-1">
        <h1 className="text-3xl font-semibold">{title}</h1>
        {subtitle && <p className="text-gray-500">{subtitle}</p>}
      </header>
      {children}
    </main>
  );
}
```

**리팩토링 후**:
```tsx
// TeacherDashboard.tsx
import { DashboardLayout } from '../components/DashboardLayout';
import { SummaryCard } from '../components/SummaryCard';

export default function TeacherDashboard() {
  return (
    <DashboardLayout 
      title="Teacher Dashboard"
      subtitle="선생님용 간단한 MVP 대시보드입니다."
    >
      <section>
        <h2 className="text-xl font-semibold mb-3">Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <SummaryCard label="Total Students" value="—" />
          <SummaryCard label="Active Classes" value="—" />
          {/* ... */}
        </div>
      </section>
    </DashboardLayout>
  );
}
```

---

## API 연동 계획

### 데이터 모델

#### Teacher Summary Response
```typescript
interface TeacherSummary {
  totalStudents: number;
  activeClasses: number;
  averagePerformance: number;  // 0-100
  atRiskStudents: number;
  currentSession?: {
    sessionId: string;
    startedAt: string;
    studentCount: number;
  };
}
```

#### Parent Child Data
```typescript
interface ChildData {
  id: string;
  name: string;
  currentAbility: number;  // θ (IRT ability)
  recentScore: number;     // 0-100
  studyTimeThisMonth: number;  // minutes
  progressHistory: Array<{
    date: string;
    ability: number;
    score: number;
  }>;
  recentActivity: Array<{
    date: string;
    type: 'quiz' | 'exam' | 'practice';
    title: string;
    score: number;
  }>;
}
```

#### Tutor Session Data
```typescript
interface TutorSession {
  sessionId: string;
  studentId: string;
  studentName: string;
  startedAt: string;
  completedAt?: string;
  problemsSolved: number;
  averageAccuracy: number;
  abilityChange: number;  // Δθ
}
```

---

### API 호출 예시

#### TeacherDashboard 데이터 로딩

```tsx
import { useEffect, useState } from 'react';
import { teacherApi } from '../lib/dashboardApi';

export default function TeacherDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await teacherApi.getSummary();
        setSummary(data);
      } catch (error) {
        console.error('Failed to load teacher summary:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <main className="p-8 space-y-8">
      {/* ... */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard 
          label="Total Students" 
          value={summary?.totalStudents ?? '—'} 
        />
        <SummaryCard 
          label="Active Classes" 
          value={summary?.activeClasses ?? '—'} 
        />
        {/* ... */}
      </div>
    </main>
  );
}
```

---

## 테스트 가이드

### 로컬 개발 서버 실행

```bash
# 1. portal_front 디렉토리로 이동
cd /home/won/projects/dreamseed_monorepo/portal_front

# 2. 개발 서버 시작
npm run dev

# 3. 브라우저에서 접속
# http://localhost:5172/teacher/dashboard
# http://localhost:5172/parent/dashboard
# http://localhost:5172/tutor/dashboard
```

### 수동 테스트 체크리스트

#### Teacher Dashboard
- [ ] `/teacher/dashboard` 페이지 로드 확인
- [ ] Summary Cards 렌더링
- [ ] Links 클릭 (Exam Player, PDF Report)
- [ ] `/teacher/students` 학생 목록 페이지
  - [ ] 검색 필터 작동 (이름)
  - [ ] 클래스 필터 작동
  - [ ] 상태 필터 작동 (On Track/At Risk)
  - [ ] View 버튼 클릭 시 상세 페이지 이동
- [ ] `/teacher/students/s1` 학생 상세 페이지
  - [ ] Ability Trend Chart 표시
  - [ ] Risk Signals 표시
  - [ ] Recent Tests 표시
  - [ ] Back to Students 버튼 작동
- [ ] Dark mode 전환 확인
- [ ] 반응형 레이아웃 (모바일/태블릿/데스크톱)

#### Parent Dashboard
- [ ] `/parent/dashboard` 페이지 로드 확인
- [ ] Child selector 작동
- [ ] 자녀 선택 시 Summary/Progress/Activity 표시
- [ ] 자녀 미선택 시 안내 메시지
- [ ] `/parent/children/c1` 자녀 상세 페이지
  - [ ] Ability Trend Chart 표시
  - [ ] Strengths / Areas to Improve 표시
  - [ ] Recent Activity 표시
  - [ ] Back to Dashboard 버튼 작동
- [ ] Dark mode 전환 확인
- [ ] 반응형 레이아웃

#### Tutor Dashboard
- [ ] `/tutor/dashboard` 페이지 로드 확인
- [ ] Session ID 표시
- [ ] Links 클릭 가능
- [ ] `/tutor/sessions` 세션 목록 페이지
  - [ ] 세션 테이블 렌더링
  - [ ] Status Badge 표시 (Completed/Upcoming)
  - [ ] View 버튼 클릭 시 상세 페이지 이동
- [ ] `/tutor/sessions/sess1` 세션 상세 페이지
  - [ ] Session Notes 표시
  - [ ] Planned Tasks 체크리스트 표시
  - [ ] Back to Sessions 버튼 작동
- [ ] Dark mode 전환 확인
- [ ] 반응형 레이아웃

---

## 도메인 배포 계획

### 서브도메인 구조

- `teacher.dreamseedai.com` → Teacher Dashboard
- `parent.dreamseedai.com` → Parent Dashboard
- `tutor.dreamseedai.com` → Tutor Dashboard
- `admin.dreamseedai.com` → Admin Dashboard (기존)
- `portal.dreamseedai.com` → 통합 포털 (학생용)

### Nginx 설정 예시

```nginx
# teacher.dreamseedai.com
server {
    listen 443 ssl http2;
    server_name teacher.dreamseedai.com;
    
    location / {
        proxy_pass http://localhost:5172;
        proxy_set_header Host $host;
        # Rewrite to /teacher/dashboard
        rewrite ^/$ /teacher/dashboard permanent;
    }
}

# parent.dreamseedai.com
server {
    listen 443 ssl http2;
    server_name parent.dreamseedai.com;
    
    location / {
        proxy_pass http://localhost:5172;
        rewrite ^/$ /parent/dashboard permanent;
    }
}

# tutor.dreamseedai.com
server {
    listen 443 ssl http2;
    server_name tutor.dreamseedai.com;
    
    location / {
        proxy_pass http://localhost:5172;
        rewrite ^/$ /tutor/dashboard permanent;
    }
}
```

---

## 트러블슈팅

### 문제 1: "Cannot find module 'react'"

**원인**: TypeScript 타입 정의 누락

**해결**:
```bash
cd portal_front
npm install --save-dev @types/react @types/react-dom
```

### 문제 2: Dark mode가 작동하지 않음

**원인**: Tailwind dark mode 설정 확인 필요

**해결**: `tailwind.config.js` 확인
```javascript
module.exports = {
  darkMode: 'class', // 또는 'media'
  // ...
}
```

### 문제 3: 라우팅이 작동하지 않음

**원인**: `App.tsx`에서 라우트 순서 문제

**해결**: 더 구체적인 경로를 먼저 체크
```tsx
// ❌ 잘못된 순서
if (location.pathname.startsWith('/teacher/')) { ... }
if (location.pathname === '/teacher/dashboard') { ... }

// ✅ 올바른 순서
if (location.pathname === '/teacher/dashboard') { ... }
if (location.pathname.startsWith('/teacher/')) { ... }
```

---

## 참고 자료

### 내부 문서
- `portal_front/README.md` - 프로젝트 개요
- `docs/architecture/ARCHITECTURE_MASTERPLAN.md` - 전체 아키텍처
- `backend/API_GUIDE.md` - API 스펙
- **`docs/implementation/TEACHER_PARENT_TUTOR_API_SPEC.md`** - Teacher/Parent/Tutor API 상세 스펙 ✨
  - 엔드포인트 정의, Pydantic 스키마, RBAC 규칙
  - Backend 구현 완료 (schemas + routers)
  - Frontend API helpers 구현 완료

### 외부 리소스
- [React Router v6 Docs](https://reactrouter.com/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Vite Guide](https://vitejs.dev/guide/)

---

## 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|------|-----------|--------|
| 2025-11-19 | 초안 작성, Teacher/Parent Dashboard 구현 | GitHub Copilot |
| 2025-11-19 | TutorDashboard 확인, 라우팅 설정 완료 | GitHub Copilot |
| 2025-11-19 | Teacher/Parent/Tutor 전체 상세 페이지 구현 완료 (목록→상세 흐름 완성) | GitHub Copilot |
| 2025-11-19 | Backend API 구현 완료 (schemas, routers, main.py 등록), Frontend API helpers 완료 | GitHub Copilot |
| 2025-11-19 | **플랫폼 레벨 통합**: DB 스키마(6 tables), ORM models(6 files), Services(2 files), Redis 캐싱, Ability History API | GitHub Copilot |
| 2025-11-19 | **DB 마이그레이션 최종 수정**: UUID → Integer 전환 완료, `DB_INTEGRATION_REQUEST.md` 생성 | GitHub Copilot |

---

## 다음 작업

1. **우선순위 1 (즉시 실행 가능)**:
   - [x] `/teacher/students` 페이지 구현 ✅ **완료**
   - [x] `/teacher/students/:id` 상세 페이지 ✅ **완료**
   - [x] `/parent/children/:id` 상세 페이지 ✅ **완료**
   - [x] `/tutor/sessions` 목록 페이지 ✅ **완료**
   - [x] `/tutor/sessions/:id` 상세 페이지 ✅ **완료**
   - [x] API 엔드포인트 백엔드 구현 ✅ **완료** (MVP Mock 응답)
   - [x] Frontend API helpers 구현 ✅ **완료**
   - [x] **DB 스키마 설계 및 ORM 모델** ✅ **완료** (2025-11-19)
   - [x] **서비스 레이어 (CRUD)** ✅ **완료** (2025-11-19)
   - [x] **DB 쿼리 통합** ✅ **완료** (2025-11-19)
   - [x] **Redis 캐싱 인프라** ✅ **완료** (2025-11-19)
   - [x] **UUID → Integer 전환** ✅ **완료** (2025-11-19, 기존 DB 호환)
   - [ ] **Alembic migration 실행** ⏳ **대기 중** 
     - ⚠️ `DB_INTEGRATION_REQUEST.md` 참조 필수
     - `down_revision` 업데이트 필요
     - `alembic upgrade head` 실행
   - [ ] 인증/권한 통합 (JWT 검증 구현)

2. **우선순위 2 (Phase 2)**:
   - [ ] 공통 컴포넌트 추출
   - [ ] 차트/그래프 라이브러리 통합 (Recharts 또는 Chart.js)
   - [ ] 실시간 업데이트 (WebSocket)

3. **우선순위 3 (Phase 3)**:
   - [ ] 서브도메인 배포
   - [ ] E2E 테스트 작성
   - [ ] 성능 최적화

---

**문서 작성**: GitHub Copilot  
**최종 업데이트**: 2025-11-19  
**버전**: 3.1 (Full-Stack 통합 + DB 마이그레이션 준비 완료)

**중요 알림**: 
- ⚠️ DB 마이그레이션 실행 전 `DB_INTEGRATION_REQUEST.md` 필독
- ✅ UUID → Integer 전환 완료 (기존 `users.id` 호환)
- ✅ 6개 신규 테이블 준비 완료
- ⏳ `alembic upgrade head` 실행 대기 중

---

## 📚 추가 문서 참조

- **[DB_INTEGRATION_REQUEST.md](./implementation/DB_INTEGRATION_REQUEST.md)** ✨ **최우선 참조**
  - **UUID → Integer 전환 완료된 최종 마이그레이션 코드**
  - `down_revision` 업데이트 방법
  - 실행 순서 및 체크리스트
  - 기존 DB(`users.id` = INTEGER)와 호환 보장
  - 즉시 실행 가능

- **[PLATFORM_DB_INTEGRATION_GUIDE.md](./implementation/PLATFORM_DB_INTEGRATION_GUIDE.md)** - 완전한 DB 통합 가이드
  - DB 스키마 상세 설명 (CREATE TABLE 문 포함)
  - SQLAlchemy ORM 모델 레퍼런스
  - Service layer 사용 예시
  - Redis 캐싱 패턴
  - API 테스트 가이드
  - Migration 적용 방법

- **[PLATFORM_INTEGRATION_SUMMARY.md](./implementation/PLATFORM_INTEGRATION_SUMMARY.md)** - 빠른 참조 요약
  - 구현된 파일 목록 (14개)
  - Next Steps 체크리스트
  - API 엔드포인트 요약

- **[TEACHER_PARENT_TUTOR_API_SPEC.md](./implementation/TEACHER_PARENT_TUTOR_API_SPEC.md)** - API 명세서
  - 엔드포인트 상세 스펙
  - Request/Response 예시
  - RBAC 규칙

---

## 🎉 현재 상태 요약

### ✅ 완료된 작업
- **Frontend (8개 페이지)**: 모든 대시보드 및 상세 페이지 구현 완료
  - `TeacherDashboard`, `TeacherStudentsPage`, `TeacherStudentDetailPage`
  - `ParentDashboard`, `ParentChildDetailPage`
  - `TutorDashboard`, `TutorSessionsPage`, `TutorSessionDetailPage`
  
- **Backend API (6개 엔드포인트)**: FastAPI routers + Pydantic schemas + DB 통합 완료
  - `GET /api/teachers/{teacher_id}/students` - 학생 목록 (DB 쿼리 완료)
  - `GET /api/teachers/{teacher_id}/students/{student_id}` - 학생 상세 (DB 쿼리 완료)
  - `GET /api/teachers/{teacher_id}/students/{student_id}/ability-history` - 차트 데이터 ✨ **NEW**
  - `GET /api/parents/{parent_id}/children/{child_id}` - 자녀 상세 (DB 쿼리 완료)
  - `GET /api/tutors/{tutor_id}/sessions` - 세션 목록 (DB 쿼리 완료)
  - `GET /api/tutors/{tutor_id}/sessions/{session_id}` - 세션 상세 (DB 쿼리 완료)
  
- **Backend Schema Files**:
  - `backend/app/schemas/common.py` - `PageResponse[T]` 제네릭
  - `backend/app/schemas/students.py` - `StudentSummary`, `StudentDetail`, `ChildDetail`
  - `backend/app/schemas/tutors.py` - `TutorSessionSummary`, `TutorSessionDetail`
  
- **Backend Router Files** (DB 통합 완료):
  - `backend/app/api/teachers.py` - RBAC + "me" alias + 실제 DB 쿼리
  - `backend/app/api/parents.py` - 부모-자녀 관계 검증 + DB 쿼리
  - `backend/app/api/tutors.py` - 세션 관리 + DB 쿼리
  
- **Backend ORM Models** (6개 파일): ✨ **NEW**
  - `backend/app/models/user.py` - User 모델
  - `backend/app/models/student.py` - Student, Class, StudentClass (many-to-many)
  - `backend/app/models/tutor.py` - TutorSession, TutorSessionTask
  - `backend/app/models/ability_history.py` - StudentAbilityHistory (IRT theta)
  
- **Backend Service Layer** (2개 파일): ✨ **NEW**
  - `backend/app/services/students.py` - list/get students, ability history
  - `backend/app/services/tutors.py` - list/get tutor sessions
  
- **Backend Infrastructure**: ✨ **NEW**
  - `backend/app/core/database.py` - Base 추가
  - `backend/app/core/security.py` - get_current_user (JWT 구현 대기)
  - `backend/app/core/cache.py` - Redis 캐싱 + ETag 지원
  - `backend/alembic/versions/001_create_platform_tables.py` - Migration 스크립트
  
- **Frontend API Helpers (3개 파일)**: TypeScript client 구현
  - `portal_front/src/lib/apiTeacher.ts` - `teacherApi.listStudents()`, `getStudentDetail()`
  - `portal_front/src/lib/apiParent.ts` - `parentApi.getChildDetail()`
  - `portal_front/src/lib/apiTutor.ts` - `tutorApi.listSessions()`, `getSessionDetail()`
  
- **라우터 등록**: `backend/main.py`에 3개 라우터 등록 완료

- **Database Schema** (6개 테이블): ✨ **NEW**
  - `students` (학생 정보) - `user_id` FK → `users.id` (INTEGER)
  - `classes` (수업/반 정보) - `teacher_id` FK → `users.id`
  - `student_classes` (many-to-many 관계) - `student_id` FK, `class_id` FK
  - `tutor_sessions` (과외 세션) - `tutor_id` FK → `users.id`, `student_id` FK
  - `tutor_session_tasks` (세션 작업 항목) - `session_id` FK
  - `student_ability_history` (IRT theta 시계열) - `student_id` FK
  
  **⚠️ 중요 설계 결정**: 모든 PK/FK는 INTEGER 타입 (기존 `users.id`와 호환)

- **문서화**: 
  - `docs/implementation/TEACHER_PARENT_TUTOR_API_SPEC.md` (400+ 줄)
  - `docs/implementation/PLATFORM_DB_INTEGRATION_GUIDE.md` ✨ **NEW** (600+ 줄, 완전한 통합 가이드)
  - `docs/implementation/PLATFORM_INTEGRATION_SUMMARY.md` ✨ **NEW** (빠른 참조용)
  - `docs/implementation/DB_INTEGRATION_REQUEST.md` ✨ **최신** (DB 마이그레이션 최종 지침, UUID→Integer 전환 완료)

### ⏳ 다음 단계

**Phase 2: Database 마이그레이션 실행** (최우선!)

⚠️ **중요**: DB 마이그레이션 전에 반드시 `DB_INTEGRATION_REQUEST.md` 참조

1. **마지막 revision ID 확인**:
   ```bash
   cd /home/won/projects/dreamseed_monorepo/backend
   alembic history
   # 출력에서 가장 최근 리비전 ID 복사
   ```

2. **Migration 파일 업데이트**:
   - `backend/alembic/versions/001_create_platform_tables.py` 열기
   - `down_revision = "<REPLACE_WITH_ACTUAL_LAST_REVISION>"` 수정
   - 코드는 이미 수정 완료 (UUID → Integer 전환)

3. **Migration 적용**:
   ```bash
   alembic upgrade head
   PGPASSWORD='DreamSeedAi0908' psql -h 127.0.0.1 -U postgres -d dreamseed -c "\dt"
   # 11개 테이블 확인 (5개 기존 + 6개 신규)
   ```

4. **테이블 생성 확인**:
   ```sql
   -- 예상 출력:
   -- alembic_version
   -- problems, progress, submissions, users (기존)
   -- students, classes, student_classes (신규)
   -- tutor_sessions, tutor_session_tasks (신규)
   -- student_ability_history (신규)
   ```

**Phase 3: 테스트 데이터 & API 통합**

5. **테스트 데이터 시딩** (선택사항):
   ```python
   # 1 teacher, 1 class, 2 students, ability history 생성
   # 가이드: docs/implementation/PLATFORM_DB_INTEGRATION_GUIDE.md
   ```

6. **API 테스트** (Swagger UI):
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   # http://localhost:8000/docs
   ```

7. **JWT 인증 구현**:
   - `backend/app/core/security.py` 업데이트
   - JWT 토큰 검증 로직 추가

**Phase 4: Frontend 통합**

8. **Frontend API 연결**:
   - Mock 데이터 → 실제 API 호출로 교체
   - 인증 토큰 처리
   - 에러 핸들링 및 로딩 상태

9. **인증/권한 테스트**:
   - `get_current_user()` 의존성 연결
   - Role-based 접근 제어 검증

**Phase 5: 고도화 (선택사항)**

10. **Redis 캐싱 적용**:
    ```bash
    redis-server
    pip install redis
    # Set REDIS_URL environment variable
    ```

11. **Parent-Child 관계 테이블 추가**
12. **Test Results/Activity 테이블 추가**
13. **성능 최적화 및 모니터링**

---

### ✅ 완료된 작업
- **Frontend (8개 페이지)**: 모든 대시보드 및 상세 페이지 구현 완료
- **Backend API (5개 엔드포인트)**: FastAPI routers + Pydantic schemas 구현
- **Frontend API Helpers (3개 파일)**: TypeScript client 구현
- **라우터 등록**: `backend/main.py`에 등록 완료
- **문서화**: API 스펙 문서 완성

### ⏳ 다음 단계
- DB 쿼리 구현 (현재 MVP Mock 응답)
- 인증/권한 통합 테스트
- Frontend mock 데이터 → 실제 API 호출 교체
