# Portal Frontend Configuration Reference

**For Portal Developers**  
**Last Updated:** November 25, 2025  
**Phase:** 1.0 Week 2

---

## Overview

This document provides a quick reference for integrating role-specific frontend apps (student/parent/teacher/admin) into the DreamSeedAI portal hub using iframe-based architecture.

---

## Environment Variables

Create `apps/portal_front/.env.local`:

```bash
# Backend API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001/api

# Frontend Apps
NEXT_PUBLIC_STUDENT_APP_URL=http://localhost:3001
NEXT_PUBLIC_PARENT_APP_URL=http://localhost:3002
NEXT_PUBLIC_TEACHER_APP_URL=http://localhost:3003
NEXT_PUBLIC_ADMIN_APP_URL=http://localhost:3000
```

---

## App Registry Configuration

**File:** `apps/portal_front/src/config/apps.ts`

```typescript
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

---

## AppFrame Component (iframe + SSO)

**File:** `apps/portal_front/src/components/AppFrame.tsx`

```typescript
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

---

## Role-Based Router (Entry Point)

**File:** `apps/portal_front/src/app/portal/page.tsx`

```typescript
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

---

## Portal Route Pages

**File:** `apps/portal_front/src/app/portal/stu/page.tsx`

```typescript
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

**Repeat for:**
- `portal/parent/page.tsx`
- `portal/teacher/page.tsx`
- `portal/admin/page.tsx`

---

## Auth Client (API Integration)

**File:** `apps/portal_front/src/lib/authClient.ts`

```typescript
import { apiFetch } from "./apiClient";

export type User = {
  id: number;
  email: string;
  role: "student" | "parent" | "teacher" | "admin";
  full_name?: string;
  is_active: boolean;
};

export async function getCurrentUser(): Promise<User> {
  return apiFetch<User>("/auth/me", {}, true);
}
```

---

## URL Structure Summary

```
Portal Routes (apps/portal_front):
├── /portal              → Role router (auto-redirect)
├── /portal/stu          → Student iframe (3001)
├── /portal/parent       → Parent iframe (3002)
├── /portal/teacher      → Teacher iframe (3003)
└── /portal/admin        → Admin iframe (3000)

Student App Routes (apps/student_front):
├── /                    → Auto-redirect to /dashboard or /auth/login
├── /auth/login          → Login page
├── /auth/register       → Registration page
├── /dashboard           → Main student dashboard (protected)
├── /exams               → Exam list (protected)
├── /exams/[examId]      → Exam detail (Week 3)
├── /study-plan          → Study plan (protected)
├── /results             → Results history (protected)
└── /profile             → User profile (protected)
```

---

## Testing Checklist

### SSO Token Flow Test

```bash
# 1. Start all services
cd apps/portal_front && npm run dev         # Port 5172
cd apps/student_front && npm run dev        # Port 3001
docker compose -f docker-compose.phase0.5.yml up -d  # Backend

# 2. Portal Login
# Visit: http://localhost:5172/login
# Enter: student4@dreamseed.ai / TestPass123!
# Verify: localStorage.access_token is set

# 3. Navigate to Student Portal
# Visit: http://localhost:5172/portal/stu
# Verify: iframe loads student_front
# Check console: "[TokenSync] Received token from portal"

# 4. Student Dashboard
# Verify: Redirected to /dashboard
# Verify: User info displays in header
# Verify: Navigation works (Exams, Study Plan, etc.)

# 5. Logout
# Click "로그아웃" in student_front
# Verify: Redirected to /auth/login
# Verify: localStorage.access_token cleared
```

---

## Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| **Portal Configuration** | ⏸️ Not Started | `apps/portal_front/src/config/apps.ts` |
| **AppFrame Component** | ⏸️ Not Started | `apps/portal_front/src/components/AppFrame.tsx` |
| **Role Router** | ⏸️ Not Started | `apps/portal_front/src/app/portal/page.tsx` |
| **Portal Routes** | ⏸️ Not Started | `apps/portal_front/src/app/portal/{role}/page.tsx` |
| **Student App - TokenSync** | ✅ Complete | `apps/student_front/src/app/TokenSyncProvider.tsx` |
| **Student App - Protected Layout** | ✅ Complete | `apps/student_front/src/app/(protected)/layout.tsx` |
| **Student App - Dashboard** | ✅ Complete | `apps/student_front/src/app/(protected)/dashboard/page.tsx` |
| **Student App - Exams** | ✅ Complete | `apps/student_front/src/app/(protected)/exams/page.tsx` |
| **Backend CORS** | ✅ Complete | `backend/main.py` (port 3001 added) |

---

## Next Steps (Week 2 Completion)

### For Portal Team:
1. Create `config/apps.ts` with app registry
2. Create `components/AppFrame.tsx` with postMessage logic
3. Create `/portal` route with role-based redirects
4. Create `/portal/{role}` routes for each role
5. Test SSO token flow end-to-end

### For Student App Team (Already Done ✅):
1. ✅ TokenSyncProvider implemented
2. ✅ Protected layout with auth middleware
3. ✅ Dashboard page created
4. ✅ Exams page created
5. ✅ Root page auto-redirect

### For Backend Team:
1. ✅ CORS updated to include port 3001
2. ⏸️ (Optional) Add HttpOnly cookie support (Phase 1B)

---

## Production Migration (Phase 1B)

When moving to production, replace postMessage SSO with HttpOnly cookies:

### Backend Changes:
```python
# backend/app/api/routers/auth.py
@router.post("/login")
async def login(response: Response, ...):
    token = create_access_token(...)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        domain=".dreamseedai.com",  # Share across subdomains
        max_age=86400
    )
    return {"status": "ok"}
```

### Frontend Changes:
```typescript
// No more localStorage/postMessage needed
const response = await fetch("/api/auth/me", {
  credentials: "include"  // Send cookies automatically
});
```

---

## References

- **Full Design Document:** [PHASE1_PORTAL_INTEGRATION.md](./PHASE1_PORTAL_INTEGRATION.md)
- **Backend Auth API:** [PHASE1_API_CONTRACT.md](./PHASE1_API_CONTRACT.md)
- **Week 1 Auth Implementation:** [PHASE1_STATUS.md](./PHASE1_STATUS.md)

---

**Status:** Ready for Portal Implementation  
**Estimated Time:** 4-6 hours for portal team  
**Student App:** Already complete ✅
