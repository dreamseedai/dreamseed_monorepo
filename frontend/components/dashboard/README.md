# Dashboard Components

Frontend React/TypeScript 컴포넌트 - CAT 대시보드

## Components

### 1. TeacherClassDashboard.tsx
- **경로**: `/teacher/dashboard/classes/:classId`
- **API**: `GET /api/dashboard/teacher/classes/{classId}/exams`
- **기능**: 반 전체 시험 요약, 학생별 최근 시험 결과

### 2. TeacherStudentDashboard.tsx
- **경로**: `/teacher/dashboard/students/:studentId`
- **API**: `GET /api/dashboard/teacher/students/{studentId}/exams`
- **기능**: 개별 학생 시험 히스토리, θ 추이 그래프

### 3. TutorDashboard.tsx
- **경로**: `/tutor/dashboard`
- **API**: `GET /api/dashboard/tutor/students/exams`
- **기능**: 전체 학생 요약, 검색/정렬, 카드 뷰

### 4. ParentChildDashboard.tsx
- **경로**: `/parent/dashboard/children/:studentId`
- **API**: `GET /api/dashboard/parent/children/{studentId}/exams`
- **기능**: 자녀 시험 히스토리 (간소화 버전, θ/SE 제외)

## Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "typescript": "^5.0.0"
  }
}
```

## Usage

### Installation

```bash
npm install react react-router-dom axios
npm install -D @types/react typescript
```

### Router Setup

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import {
  TeacherClassDashboard,
  TeacherStudentDashboard,
  TutorDashboard,
  ParentChildDashboard,
} from './components/dashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Teacher Routes */}
        <Route 
          path="/teacher/dashboard/classes/:classId" 
          element={<TeacherClassDashboard />} 
        />
        <Route 
          path="/teacher/dashboard/students/:studentId" 
          element={<TeacherStudentDashboard />} 
        />
        
        {/* Tutor Routes */}
        <Route 
          path="/tutor/dashboard" 
          element={<TutorDashboard />} 
        />
        <Route 
          path="/tutor/dashboard/students/:studentId" 
          element={<TeacherStudentDashboard />} 
        />
        
        {/* Parent Routes */}
        <Route 
          path="/parent/dashboard/children/:studentId" 
          element={<ParentChildDashboard />} 
        />
      </Routes>
    </BrowserRouter>
  );
}
```

## Features

### Common Features
- ✅ 로딩 상태 표시
- ✅ 에러 처리
- ✅ 반응형 디자인 (Tailwind CSS)
- ✅ 인증 토큰 자동 전송

### Teacher/Tutor Features
- ✅ θ (Theta) 값 표시
- ✅ Standard Error 표시
- ✅ 등급 분포 시각화
- ✅ 학생별 상세 분석

### Parent Features
- ✅ 간소화된 점수 표시
- ✅ 백분위 기반 설명
- ✅ 성적 추이 그래프
- ✅ 기술 정보 숨김 (θ/SE)

## Styling

Tailwind CSS 사용:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

`tailwind.config.js`:
```js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

## API Integration

`axios` 인스턴스 설정 예시:

```ts
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

## Type Definitions

모든 컴포넌트에 TypeScript 타입 정의 포함:
- API 응답 타입
- Props 타입
- State 타입

## Testing

```bash
npm install -D @testing-library/react @testing-library/jest-dom
```

테스트 예시:
```tsx
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { TeacherClassDashboard } from './TeacherClassDashboard';

test('renders class dashboard', async () => {
  render(
    <BrowserRouter>
      <TeacherClassDashboard />
    </BrowserRouter>
  );
  
  await waitFor(() => {
    expect(screen.getByText(/반 평균 점수/i)).toBeInTheDocument();
  });
});
```

## Notes

- 모든 컴포넌트는 독립적으로 작동 가능
- API 엔드포인트 변경 시 각 컴포넌트 수정 필요
- 인증 토큰은 `localStorage`에서 자동 로드
- Next.js 사용 시 `react-router-dom` → `next/router`로 변경 필요

## Related Documentation

- [Dashboard Routes](../../backend/docs/DASHBOARD_ROUTES.md)
- [Dashboard API](../../backend/docs/DASHBOARD_API.md)
- [API Responses](../../backend/docs/DASHBOARD_API_RESPONSES.md)
