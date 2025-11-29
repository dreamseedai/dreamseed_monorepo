# Phase 1 Portal Integration & Role-Based Routing Design

**Document Version:** 1.0  
**Date:** November 25, 2025  
**Phase:** 1.0 Week 2 (Frontend Setup)  
**Status:** Design Complete, Implementation Ready

---

## 1. Executive Summary

This document defines the complete architecture for integrating the newly created `apps/student_front` into the DreamSeedAI portal ecosystem, establishing patterns for role-based routing, SSO token sharing, and multi-app orchestration.

**Key Decisions:**
- Portal Frontend acts as the **Role-Based Hub** (iframe orchestration)
- Each role (student/parent/teacher/admin) has its own dedicated frontend app
- SSO achieved via **localStorage + postMessage** (Phase 1A) → **HttpOnly cookies** (Phase 1B+)
- URL structure follows RESTful `/portal/{role}` pattern

---

## 2. Architecture Overview

### 2.1 Three-Layer Frontend Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Site (Landing)                      │
│  https://dreamseedai.com/                                   │
│  - Public landing page                                      │
│  - Role selector (/role-select)                             │
│  - Common auth pages (/login, /register)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Portal Frontend (Hub)                       │
│  https://dreamseedai.com/portal                             │
│  - Role-based routing                                       │
│  - Common navigation/header                                 │
│  - SSO token distribution                                   │
│  - iframe orchestration                                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Student App   │  │ Parent App    │  │ Teacher App   │
│ /portal/stu   │  │ /portal/parent│  │ /portal/teacher│
│ (port 3001)   │  │ (port 3002)   │  │ (port 3003)   │
└───────────────┘  └───────────────┘  └───────────────┘
```

### 2.2 Backend (Already Complete ✅)

**Auth API:** `http://localhost:8001/api`

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - JWT login (OAuth2 form)
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

**Roles:** `student`, `parent`, `teacher`, `admin`

### 2.3 Frontend Components

| Component | Location | Port | Purpose |
|-----------|----------|------|---------|
| **Portal Frontend** | `apps/portal_front/` | 5172 | Role-based hub, iframe orchestration |
| **Student Frontend** | `apps/student_front/` | 3001 | Student dashboard, exams, study plan |
| **Parent Frontend** | `apps/parent_front/` | 3002 | (Future) Child monitoring, reports |
| **Teacher Frontend** | `apps/teacher_front/` | 3003 | (Future) Class management, grading |
| **Admin Frontend** | `apps/admin_front/` | 3000 | (Existing) System administration |

---

## 3. URL Structure Design

### 3.1 Main Site (DreamSeedAI Landing)

```
https://dreamseedai.com/
├── /                    → Landing page
├── /role-select         → "I am a student/parent/teacher" selector
├── /login               → Common login (redirects to /portal after auth)
├── /register            → Common registration (with role selection)
└── /about               → About DreamSeedAI
```

### 3.2 Portal Hub (Role-Based Routing)

```
https://dreamseedai.com/portal
├── /portal              → Entry point (requires auth)
│   │                     - Checks /api/auth/me
│   │                     - Redirects based on role:
│   │                       • student → /portal/stu
│   │                       • parent → /portal/parent
│   │                       • teacher → /portal/teacher
│   │                       • admin → /portal/admin
│
├── /portal/stu          → Student dashboard (iframe: student_front)
├── /portal/parent       → Parent dashboard (iframe: parent_front)
├── /portal/teacher      → Teacher dashboard (iframe: teacher_front)
└── /portal/admin        → Admin dashboard (iframe: admin_front)
```

**Portal Role Routing Logic:**

```typescript
// Pseudo-code for /portal entry point
async function handlePortalEntry() {
  const user = await getCurrentUser(); // GET /api/auth/me
  
  switch (user.role) {
    case "student":
      redirect("/portal/stu");
      break;
    case "parent":
      redirect("/portal/parent");
      break;
    case "teacher":
      redirect("/portal/teacher");
      break;
    case "admin":
      redirect("/portal/admin");
      break;
    default:
      // No role assigned
      redirect("/role-select");
  }
}
```

### 3.3 Student Frontend Internal Routes

```
http://localhost:3001 (dev) | https://student.dreamseedai.com (prod)
├── /                         → Auto-redirect based on auth
│   │                          - If logged in → /dashboard
│   │                          - If not → /auth/login
│
├── /auth/
│   ├── login                 → Login form
│   └── register              → Registration form
│
├── /dashboard                → Student main dashboard
│   └── widgets:
│       - Upcoming exams
│       - Recent results
│       - Study plan progress
│
├── /exams                    → Exam list page
│   └── /exams/[examId]       → Exam detail + start exam
│       └── /exams/[examId]/session/[sessionId]  → Active exam session (CAT)
│
├── /study-plan               → Personalized study plan
├── /results                  → Exam history & results
├── /profile                  → Account settings
└── /aptitude                 → (Phase 2) Aptitude assessment
```

**Route Groups (Next.js App Router):**

```
apps/student_front/src/app/
├── (public)/
│   └── auth/
│       ├── login/page.tsx
│       └── register/page.tsx
│
├── (protected)/              ← Requires authentication
│   ├── layout.tsx            ← Auth check middleware
│   ├── dashboard/page.tsx
│   ├── exams/
│   │   ├── page.tsx
│   │   └── [examId]/page.tsx
│   ├── study-plan/page.tsx
│   ├── results/page.tsx
│   └── profile/page.tsx
│
└── page.tsx                  → Root (auto-redirect logic)
```

---

## 4. SSO Token Sharing Strategy

### 4.1 Phase 1A: localStorage + postMessage (Current Implementation)

**Context:**
- Portal and student_front run on different ports (dev environment)
- Backend doesn't use HttpOnly cookies yet
- Need to share JWT token across iframe boundary

**Flow:**

```
┌──────────────┐                    ┌──────────────────┐
│   Portal     │                    │  Student App     │
│  (5172)      │                    │    (3001)        │
└──────────────┘                    └──────────────────┘
       │                                     │
       │ 1. User logs in                    │
       │    POST /api/auth/login            │
       ├────────────────────────────────────►
       │                                     │
       │ 2. Store token in localStorage     │
       │    localStorage.setItem(...)       │
       │                                     │
       │ 3. Load student app in iframe      │
       │    <iframe src="http://...3001">   │
       │                                     │
       │ 4. postMessage token to iframe     │
       ├─────────────────────────────────────►
       │    {type: "SET_TOKEN", token}      │
       │                                     │
       │                                     │ 5. Store token
       │                                     │    localStorage.setItem(...)
       │                                     │
       │                                     │ 6. Call /api/auth/me
       │                                     │    with Authorization header
       │                                     ├───────────► Backend
```

### 4.2 Phase 1B+: HttpOnly Cookie-Based SSO (Future)

**Migration Plan (Phase 1B or Phase 2):**

1. **Backend Changes:**
   ```python
   # backend/app/api/routers/auth.py
   @router.post("/login")
   async def login(response: Response, ...):
       # Generate JWT
       token = create_access_token(...)
       
       # Set HttpOnly cookie
       response.set_cookie(
           key="access_token",
           value=token,
           httponly=True,
           secure=True,  # HTTPS only
           samesite="lax",
           domain=".dreamseedai.com",  # Share across subdomains
           max_age=86400  # 24 hours
       )
       
       return {"status": "ok"}
   ```

2. **Frontend Changes:**
   ```typescript
   // No more localStorage/postMessage needed
   const response = await fetch("/api/auth/me", {
     credentials: "include"  // Send cookies automatically
   });
   ```

3. **Benefits:**
   - True SSO across all subdomains (portal.dreamseedai.com, student.dreamseedai.com)
   - XSS protection (JavaScript can't access token)
   - Simpler architecture (no postMessage)
   - Industry standard

**Timeline:** Defer to Phase 1B (Week 5-6) or Phase 2.0

---

## 5. Implementation Guide

### 5.1 Portal Frontend Setup

#### A. Environment Variables

```bash
# apps/portal_front/.env.local

# Backend API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api

# Frontend Apps
NEXT_PUBLIC_STUDENT_APP_URL=http://localhost:3001
NEXT_PUBLIC_PARENT_APP_URL=http://localhost:3002
NEXT_PUBLIC_TEACHER_APP_URL=http://localhost:3003
NEXT_PUBLIC_ADMIN_APP_URL=http://localhost:3000
```

#### B. App Configuration

```typescript
// apps/portal_front/src/config/apps.ts

export type PortalAppConfig = {
  id: string;
  label: string;
  path: string;            // Portal internal path
  iframeSrc: string;       // Target app URL
  roles: string[];         // Allowed roles
};

export const PORTAL_APPS: PortalAppConfig[] = [
  {
    id: "student",
    label: "학생 대시보드",
    path: "/portal/stu",
    iframeSrc: process.env.NEXT_PUBLIC_STUDENT_APP_URL ?? "http://localhost:3001",
    roles: ["student"],
  },
  {
    id: "parent",
    label: "학부모 대시보드",
    path: "/portal/parent",
    iframeSrc: process.env.NEXT_PUBLIC_PARENT_APP_URL ?? "http://localhost:3002",
    roles: ["parent"],
  },
  {
    id: "teacher",
    label: "교사 대시보드",
    path: "/portal/teacher",
    iframeSrc: process.env.NEXT_PUBLIC_TEACHER_APP_URL ?? "http://localhost:3003",
    roles: ["teacher"],
  },
  {
    id: "admin",
    label: "관리자 대시보드",
    path: "/portal/admin",
    iframeSrc: process.env.NEXT_PUBLIC_ADMIN_APP_URL ?? "http://localhost:3000",
    roles: ["admin"],
  },
];
```

#### C. AppFrame Component (iframe Wrapper)

```typescript
// apps/portal_front/src/components/AppFrame.tsx

"use client";

import { useEffect, useRef } from "react";

type AppFrameProps = {
  src: string;
  appId: string;
};

export function AppFrame({ src, appId }: AppFrameProps) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  useEffect(() => {
    // Get token from localStorage
    const token =
      typeof window !== "undefined"
        ? window.localStorage.getItem("access_token")
        : null;

    if (!token) {
      console.warn("[AppFrame] No access_token found in localStorage");
      return;
    }

    // Wait for iframe to load
    const iframe = iframeRef.current;
    if (!iframe) return;

    const handleLoad = () => {
      if (iframe.contentWindow) {
        console.log(`[AppFrame] Sending token to ${appId}...`);
        iframe.contentWindow.postMessage(
          {
            type: "SET_TOKEN",
            token,
            source: "portal",
          },
          "*" // TODO: Restrict to specific origin in production
        );
      }
    };

    iframe.addEventListener("load", handleLoad);
    return () => iframe.removeEventListener("load", handleLoad);
  }, [src, appId]);

  return (
    <iframe
      ref={iframeRef}
      src={src}
      title={`${appId} application`}
      className="h-[calc(100vh-60px)] w-full border-0"
      sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
    />
  );
}
```

#### D. Portal Route Pages

```typescript
// apps/portal_front/src/app/portal/stu/page.tsx

import { AppFrame } from "@/components/AppFrame";
import { PORTAL_APPS } from "@/config/apps";

export default function StudentPortalPage() {
  const app = PORTAL_APPS.find((a) => a.id === "student");
  
  if (!app) {
    return <div className="p-4 text-red-500">Student app not configured.</div>;
  }

  return <AppFrame src={app.iframeSrc} appId={app.id} />;
}
```

```typescript
// apps/portal_front/src/app/portal/page.tsx

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser } from "@/lib/authClient";

export default function PortalEntryPage() {
  const router = useRouter();

  useEffect(() => {
    async function checkRole() {
      try {
        const user = await getCurrentUser();
        
        // Route based on role
        switch (user.role) {
          case "student":
            router.replace("/portal/stu");
            break;
          case "parent":
            router.replace("/portal/parent");
            break;
          case "teacher":
            router.replace("/portal/teacher");
            break;
          case "admin":
            router.replace("/portal/admin");
            break;
          default:
            // No valid role
            router.replace("/role-select");
        }
      } catch (error) {
        // Not authenticated
        router.replace("/login");
      }
    }

    checkRole();
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-gray-500">역할 확인 중...</div>
    </div>
  );
}
```

### 5.2 Student Frontend Setup

#### A. TokenSyncProvider (SSO Token Receiver)

```typescript
// apps/student_front/src/app/TokenSyncProvider.tsx

"use client";

import { useEffect } from "react";

export function TokenSyncProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    function handleMessage(e: MessageEvent) {
      // TODO: In production, verify e.origin === "https://portal.dreamseedai.com"
      if (!e.data || typeof e.data !== "object") return;

      if (e.data.type === "SET_TOKEN" && e.data.token) {
        console.log("[TokenSync] Received token from portal");
        window.localStorage.setItem("access_token", e.data.token);
        
        // Optional: Trigger a re-render or state update
        window.dispatchEvent(new Event("token-updated"));
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return <>{children}</>;
}
```

#### B. Update Root Layout

```typescript
// apps/student_front/src/app/layout.tsx

import "./globals.css";
import type { Metadata } from "next";
import { TokenSyncProvider } from "./TokenSyncProvider";

export const metadata: Metadata = {
  title: "DreamSeed Student",
  description: "Student frontend for DreamSeedAI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50">
        <TokenSyncProvider>
          {children}
        </TokenSyncProvider>
      </body>
    </html>
  );
}
```

#### C. Protected Route Layout

```typescript
// apps/student_front/src/app/(protected)/layout.tsx

"use client";

import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getCurrentUser, User } from "@/lib/authClient";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null | "loading">("loading");

  useEffect(() => {
    async function checkAuth() {
      const token =
        typeof window !== "undefined"
          ? window.localStorage.getItem("access_token")
          : null;

      if (!token) {
        console.warn("[ProtectedLayout] No token, redirecting to login");
        router.replace("/auth/login?redirect=" + encodeURIComponent(pathname));
        return;
      }

      try {
        const userData = await getCurrentUser();
        
        // Ensure user is a student
        if (userData.role !== "student") {
          console.error("[ProtectedLayout] User is not a student");
          window.localStorage.removeItem("access_token");
          router.replace("/auth/login?error=invalid_role");
          return;
        }

        setUser(userData);
      } catch (error) {
        console.error("[ProtectedLayout] Auth check failed:", error);
        window.localStorage.removeItem("access_token");
        router.replace("/auth/login");
      }
    }

    checkAuth();

    // Listen for token updates from portal
    const handleTokenUpdate = () => {
      checkAuth();
    };

    window.addEventListener("token-updated", handleTokenUpdate);
    return () => window.removeEventListener("token-updated", handleTokenUpdate);
  }, [router, pathname]);

  if (user === "loading") {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-sm text-gray-500">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="text-lg font-semibold text-blue-600">
            DreamSeed Student
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user && typeof user === "object" && user.email}
            </span>
            <button
              onClick={() => {
                window.localStorage.removeItem("access_token");
                router.push("/auth/login");
              }}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              로그아웃
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
```

#### D. Dashboard Page Skeleton

```typescript
// apps/student_front/src/app/(protected)/dashboard/page.tsx

import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">학생 대시보드</h1>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-3">
        <Link
          href="/exams"
          className="block rounded-lg border bg-white p-6 hover:border-blue-500 hover:shadow-md"
        >
          <div className="text-3xl">📝</div>
          <h3 className="mt-2 font-semibold">시험 보기</h3>
          <p className="mt-1 text-sm text-gray-500">
            진단 평가 및 학습 평가 응시
          </p>
        </Link>

        <Link
          href="/study-plan"
          className="block rounded-lg border bg-white p-6 hover:border-blue-500 hover:shadow-md"
        >
          <div className="text-3xl">📚</div>
          <h3 className="mt-2 font-semibold">학습 계획</h3>
          <p className="mt-1 text-sm text-gray-500">
            개인화된 학습 플랜 확인
          </p>
        </Link>

        <Link
          href="/results"
          className="block rounded-lg border bg-white p-6 hover:border-blue-500 hover:shadow-md"
        >
          <div className="text-3xl">📊</div>
          <h3 className="mt-2 font-semibold">성적 분석</h3>
          <p className="mt-1 text-sm text-gray-500">
            시험 결과 및 추이 분석
          </p>
        </Link>
      </div>

      {/* Upcoming Exams */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold">다가오는 시험</h2>
        <div className="mt-4 text-sm text-gray-500">
          예정된 시험이 없습니다.
        </div>
      </div>

      {/* Recent Results */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold">최근 결과</h2>
        <div className="mt-4 text-sm text-gray-500">
          아직 응시한 시험이 없습니다.
        </div>
      </div>
    </div>
  );
}
```

#### E. Exams Page Skeleton

```typescript
// apps/student_front/src/app/(protected)/exams/page.tsx

export default function ExamsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">시험 목록</h1>

      {/* Filter Tabs */}
      <div className="flex gap-4 border-b">
        <button className="border-b-2 border-blue-600 px-4 py-2 text-sm font-medium text-blue-600">
          전체
        </button>
        <button className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">
          수학
        </button>
        <button className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">
          영어
        </button>
        <button className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">
          과학
        </button>
      </div>

      {/* Exam Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border bg-white p-6">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold">수학 진단 평가</h3>
              <p className="mt-1 text-sm text-gray-500">
                CAT 적응형 평가 (약 10-15문항)
              </p>
            </div>
            <span className="rounded bg-blue-100 px-2 py-1 text-xs font-medium text-blue-700">
              Math
            </span>
          </div>
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-600">예상 소요 시간: 20분</div>
            <button className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              시작하기
            </button>
          </div>
        </div>

        {/* More exam cards... */}
      </div>
    </div>
  );
}
```

---

## 6. CORS Configuration

### Backend CORS Update (Required!)

```python
# backend/main.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5172",  # Portal frontend
        "http://localhost:3001",  # Student frontend (NEW)
        "http://localhost:3002",  # Parent frontend
        "http://localhost:3003",  # Teacher frontend
        "http://localhost:3000",  # Admin frontend
        "http://localhost:3030",  # Existing
        "http://localhost:3031",  # Existing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 7. Testing Checklist

### 7.1 SSO Token Flow Test

- [ ] Portal: Login at `http://localhost:5172/login`
- [ ] Portal: Verify `localStorage.access_token` is set
- [ ] Portal: Navigate to `/portal/stu`
- [ ] Student App: Verify `postMessage` received in console
- [ ] Student App: Verify `localStorage.access_token` is set
- [ ] Student App: Verify `/dashboard` loads without redirect
- [ ] Student App: Verify user info displays correctly
- [ ] Student App: Test logout clears token

### 7.2 Protected Routes Test

- [ ] Student App: Clear `localStorage.access_token`
- [ ] Student App: Visit `/dashboard` directly
- [ ] Verify: Redirects to `/auth/login`
- [ ] Login again
- [ ] Verify: Redirects back to `/dashboard`

### 7.3 Role-Based Routing Test

- [ ] Portal: Login as student
- [ ] Portal: Visit `/portal`
- [ ] Verify: Auto-redirects to `/portal/stu`
- [ ] Portal: Manually visit `/portal/teacher`
- [ ] Verify: Access denied (role check)

---

## 8. Week 3 Preview: Exam Flow Routes

### 8.1 Exam Session Routes (Week 3 Implementation)

```
/exams/[examId]/session/[sessionId]
└── Components:
    ├── QuestionDisplay       ← Render question + choices
    ├── AnswerOptions         ← Multiple choice radio buttons
    ├── ProgressBar           ← Question N of M
    ├── Timer                 ← Optional time limit
    ├── SubmitButton          ← Submit answer
    └── CAT Controller        ← Handle /api/adaptive/* calls
```

### 8.2 API Integration Points

```typescript
// Week 3: Connect to backend CAT API

// 1. Start Exam
POST /api/adaptive/exams/{exam_id}/start
→ { session_id, first_item, initial_theta }

// 2. Submit Answer (loop)
POST /api/adaptive/exams/{session_id}/submit
Body: { choice_id }
→ { is_correct, next_item, new_theta, se, finished }

// 3. Get Results
GET /api/adaptive/exams/{session_id}/results
→ { theta, score_100, percentile, grade, recommendations }
```

---

## 9. File Structure Summary

```
dreamseed_monorepo/
├── apps/
│   ├── portal_front/               ← Role-based hub
│   │   ├── .env.local              ← App URLs
│   │   ├── src/
│   │   │   ├── config/apps.ts      ← Portal app registry
│   │   │   ├── components/AppFrame.tsx  ← iframe + postMessage
│   │   │   └── app/
│   │   │       └── portal/
│   │   │           ├── page.tsx    ← Role router
│   │   │           ├── stu/page.tsx
│   │   │           ├── parent/page.tsx
│   │   │           ├── teacher/page.tsx
│   │   │           └── admin/page.tsx
│   │
│   └── student_front/              ← Student-specific app
│       ├── .env.local              ← API base URL
│       ├── src/
│       │   ├── app/
│       │   │   ├── TokenSyncProvider.tsx  ← SSO receiver
│       │   │   ├── layout.tsx      ← Root layout
│       │   │   ├── page.tsx        ← Auto-redirect
│       │   │   ├── (public)/
│       │   │   │   └── auth/       ← Login, register
│       │   │   └── (protected)/    ← Auth required
│       │   │       ├── layout.tsx  ← Auth middleware
│       │   │       ├── dashboard/  ← Main dashboard
│       │   │       ├── exams/      ← Exam list + detail
│       │   │       ├── study-plan/
│       │   │       ├── results/
│       │   │       └── profile/
│       │   └── lib/
│       │       ├── apiClient.ts
│       │       └── authClient.ts
│
└── backend/
    └── app/
        └── api/routers/auth.py     ← Already complete ✅
```

---

## 10. Success Metrics

### Week 2 Completion Criteria (50% → 100%)

- [x] Next.js project created ✅
- [x] Auth pages implemented ✅
- [x] API client ready ✅
- [ ] **TokenSyncProvider implemented**
- [ ] **Protected route layout created**
- [ ] **Dashboard page skeleton**
- [ ] **Exams page skeleton**
- [ ] **CORS configured in backend**
- [ ] **End-to-end SSO flow tested**

### Phase 1A Completion Criteria (40% → 60%)

- [ ] Portal integration complete
- [ ] All role-based routes working
- [ ] Week 3: Exam flow implementation
- [ ] Week 4: Production deployment

---

## 11. Next Actions

### Immediate (This Session)

1. **Implement TokenSyncProvider** in `student_front`
2. **Create protected layout** with auth middleware
3. **Create dashboard skeleton** page
4. **Create exams skeleton** page
5. **Update backend CORS** to include port 3001
6. **Test SSO flow** end-to-end

### Week 3 (Exam Flow)

1. Implement `/exams/[examId]/session/[sessionId]` page
2. Create CAT API integration layer
3. Build question display component
4. Add progress tracking
5. Implement results page

### Week 4 (Deployment)

1. Production server setup
2. Domain configuration (dreamseedai.com)
3. SSL certificates
4. Docker Compose deployment
5. Beta tester onboarding (5-10 users)
6. 🎉 Alpha Launch (December 22, 2025)

---

## 12. References

- **Backend Auth API:** [PHASE1_API_CONTRACT.md](./PHASE1_API_CONTRACT.md)
- **Week 1 Completion:** [PHASE1_STATUS.md](./PHASE1_STATUS.md)
- **Phase 1 Backlog:** [PHASE1_INITIAL_BACKLOG.md](./PHASE1_INITIAL_BACKLOG.md)
- **Alpha Checklist:** [PHASE1_ALPHA_CHECKLIST.md](./PHASE1_ALPHA_CHECKLIST.md)

---

**Document Status:** Ready for Implementation  
**Approval Required:** No (internal design)  
**Next Review:** After Week 2 completion
