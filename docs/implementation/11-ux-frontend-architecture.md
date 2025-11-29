# UX Layer: Frontend Architecture (React/Next.js)

**Implementation Guide 11 of 14**

This guide covers the frontend architecture for DreamSeedAI's UX layer, focusing on the React/Next.js implementation for student and parent interfaces.

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Next.js Configuration](#nextjs-configuration)
5. [Tailwind CSS Setup](#tailwind-css-setup)
6. [State Management](#state-management)
7. [Internationalization (i18n)](#internationalization-i18n)
8. [API Integration](#api-integration)
9. [Performance Optimization](#performance-optimization)
10. [Testing Strategy](#testing-strategy)

---

## Overview

### Goals

The UX layer serves as the bridge between users and AI capabilities, providing:

- **Intuitive User Experience**: Easy-to-use interfaces for students, teachers, and parents
- **Accessibility**: WCAG 2.1 AA compliance for inclusive design
- **Performance**: Fast page loads and smooth interactions
- **Responsive Design**: Optimized for desktop, tablet, and mobile
- **Globalization**: Multi-language support (English, Korean, Spanish, Chinese)

### Architecture Principles

- **Component-Based**: Reusable, modular UI components
- **Server-Side Rendering (SSR)**: Fast initial loads and SEO optimization
- **Progressive Enhancement**: Works without JavaScript, enhanced with it
- **Atomic Design**: UI organized from atoms → molecules → organisms → templates → pages

---

## Technology Stack

### Core Framework

- **React 18.3+**: Component-based UI library
- **Next.js 14+**: Full-stack React framework with App Router
- **TypeScript 5.3+**: Type-safe development

### Styling & UI

- **Tailwind CSS 3.4+**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **Framer Motion**: Animation library

### State Management

- **Zustand 4.4+**: Lightweight state management
- **React Query 5.0+**: Server state management

### Data Visualization

- **Chart.js 4.4+**: Simple charts (bar, line, pie)
- **D3.js 7.8+**: Complex custom visualizations

### Testing

- **Vitest**: Unit testing
- **Playwright**: E2E testing
- **Testing Library**: Component testing

---

## Project Structure

### Directory Layout

```
portal_front/
├── app/                        # Next.js 14 App Router
│   ├── [locale]/               # i18n routing
│   │   ├── (auth)/             # Auth route group
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── signup/
│   │   │       └── page.tsx
│   │   ├── (student)/          # Student route group
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx
│   │   │   ├── assessments/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx       # Assessment detail
│   │   │   │       └── take/
│   │   │   │           └── page.tsx   # Take test
│   │   │   └── tutor/
│   │   │       └── page.tsx
│   │   ├── (parent)/           # Parent route group
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx
│   │   │   └── children/
│   │   │       └── [childId]/
│   │   │           └── page.tsx
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Home page
│   ├── api/                    # API routes (optional)
│   │   └── webhooks/
│   │       └── stripe/
│   │           └── route.ts
│   └── globals.css             # Global styles
├── components/                 # React components
│   ├── ui/                     # Base UI components (Radix)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── features/               # Feature-specific components
│   │   ├── assessment/
│   │   │   ├── AssessmentCard.tsx
│   │   │   ├── QuestionDisplay.tsx
│   │   │   └── ProgressBar.tsx
│   │   ├── dashboard/
│   │   │   ├── RecentScores.tsx
│   │   │   ├── WeaknessAreas.tsx
│   │   │   └── GoalProgress.tsx
│   │   └── tutor/
│   │       ├── ChatInterface.tsx
│   │       ├── MessageBubble.tsx
│   │       └── SuggestedQuestions.tsx
│   ├── layouts/                # Layout components
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── Sidebar.tsx
│   └── providers/              # Context providers
│       ├── AuthProvider.tsx
│       ├── ThemeProvider.tsx
│       └── QueryProvider.tsx
├── lib/                        # Utility libraries
│   ├── api/                    # API client
│   │   ├── client.ts
│   │   ├── assessments.ts
│   │   ├── tutor.ts
│   │   └── auth.ts
│   ├── hooks/                  # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useAssessment.ts
│   │   └── useWebSocket.ts
│   ├── utils/                  # Utility functions
│   │   ├── cn.ts               # Class name merger
│   │   ├── formatters.ts
│   │   └── validators.ts
│   └── store/                  # Zustand stores
│       ├── authStore.ts
│       ├── assessmentStore.ts
│       └── tutorStore.ts
├── public/                     # Static assets
│   ├── images/
│   ├── icons/
│   └── locales/                # i18n JSON files
│       ├── en/
│       │   ├── common.json
│       │   └── dashboard.json
│       └── ko/
│           ├── common.json
│           └── dashboard.json
├── types/                      # TypeScript types
│   ├── api.ts
│   ├── assessment.ts
│   └── user.ts
├── middleware.ts               # Next.js middleware (auth, i18n)
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## Next.js Configuration

### next.config.js

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // i18n configuration
  i18n: {
    locales: ["en", "ko", "es", "zh"],
    defaultLocale: "en",
    localeDetection: true,
  },

  // Image optimization
  images: {
    domains: ["cdn.dreamseedai.com", "storage.googleapis.com"],
    formats: ["image/avif", "image/webp"],
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
  },

  // Security headers
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "origin-when-cross-origin",
          },
        ],
      },
    ];
  },

  // Redirects
  async redirects() {
    return [
      {
        source: "/home",
        destination: "/",
        permanent: true,
      },
    ];
  },
};

module.exports = nextConfig;
```

### Environment Variables (.env.local)

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://api.dreamseedai.com
NEXT_PUBLIC_WS_URL=wss://ws.dreamseedai.com

# Authentication
NEXTAUTH_URL=https://portal.dreamseedai.com
NEXTAUTH_SECRET=your-secret-key-here

# Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Feature Flags
NEXT_PUBLIC_ENABLE_AI_TUTOR=true
NEXT_PUBLIC_ENABLE_GAMIFICATION=true
```

### Middleware (Auth & i18n)

```typescript
// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";

const PUBLIC_PATHS = ["/login", "/signup", "/about"];
const LOCALES = ["en", "ko", "es", "zh"];
const DEFAULT_LOCALE = "en";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1. Locale handling
  const pathnameHasLocale = LOCALES.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (!pathnameHasLocale) {
    const locale = request.cookies.get("NEXT_LOCALE")?.value || DEFAULT_LOCALE;
    request.nextUrl.pathname = `/${locale}${pathname}`;
    return NextResponse.redirect(request.nextUrl);
  }

  // 2. Authentication check
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET,
  });

  const isPublicPath = PUBLIC_PATHS.some((path) => pathname.includes(path));

  if (!token && !isPublicPath) {
    const loginUrl = new URL(`/${request.nextUrl.locale}/login`, request.url);
    loginUrl.searchParams.set("callbackUrl", request.url);
    return NextResponse.redirect(loginUrl);
  }

  // 3. Role-based routing
  if (token) {
    const role = token.role as string;

    if (pathname.includes("/student") && role !== "student") {
      return NextResponse.redirect(
        new URL(`/${request.nextUrl.locale}/unauthorized`, request.url)
      );
    }

    if (pathname.includes("/parent") && role !== "parent") {
      return NextResponse.redirect(
        new URL(`/${request.nextUrl.locale}/unauthorized`, request.url)
      );
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\..*|api).*)",
  ],
};
```

---

## Tailwind CSS Setup

### tailwind.config.ts

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // DreamSeedAI brand colors
        dreamseed: {
          blue: "#0066CC",
          green: "#00CC66",
          orange: "#FF9933",
          purple: "#9933FF",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-roboto-mono)", "monospace"],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "slide-in-from-right": {
          from: { transform: "translateX(100%)" },
          to: { transform: "translateX(0)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.3s ease-out",
        "slide-in": "slide-in-from-right 0.3s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/typography")],
};

export default config;
```

### Global Styles (app/globals.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;

    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;

    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;

    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;

    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;

    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;

    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;

    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;

    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;

    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;

    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;

    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;

    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;

    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;

    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;

    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;

    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;

    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}

/* Custom utility classes */
@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
}
```

---

## State Management

### Zustand Store (Authentication)

```typescript
// lib/store/authStore.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: string;
  email: string;
  name: string;
  role: "student" | "teacher" | "parent" | "admin";
  avatar?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setUser: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      setUser: (user, token) =>
        set({
          user,
          token,
          isAuthenticated: true,
        }),

      logout: () =>
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "auth-storage",
      // Only persist token, not entire user object for security
      partialize: (state) => ({ token: state.token }),
    }
  )
);
```

### Zustand Store (Assessment)

```typescript
// lib/store/assessmentStore.ts
import { create } from "zustand";

interface Question {
  id: string;
  content: string;
  options: string[];
  difficulty: number;
}

interface AssessmentState {
  sessionId: string | null;
  currentQuestion: Question | null;
  currentQuestionIndex: number;
  totalQuestions: number;
  responses: Record<string, number>;
  estimatedAbility: number | null;
  timeRemaining: number | null;

  // Actions
  startAssessment: (sessionId: string, totalQuestions: number) => void;
  setCurrentQuestion: (question: Question, index: number) => void;
  submitResponse: (questionId: string, response: number) => void;
  updateAbility: (ability: number) => void;
  updateTimeRemaining: (seconds: number) => void;
  endAssessment: () => void;
}

export const useAssessmentStore = create<AssessmentState>((set) => ({
  sessionId: null,
  currentQuestion: null,
  currentQuestionIndex: 0,
  totalQuestions: 0,
  responses: {},
  estimatedAbility: null,
  timeRemaining: null,

  startAssessment: (sessionId, totalQuestions) =>
    set({
      sessionId,
      totalQuestions,
      currentQuestionIndex: 0,
      responses: {},
      estimatedAbility: 0,
    }),

  setCurrentQuestion: (question, index) =>
    set({
      currentQuestion: question,
      currentQuestionIndex: index,
    }),

  submitResponse: (questionId, response) =>
    set((state) => ({
      responses: { ...state.responses, [questionId]: response },
    })),

  updateAbility: (ability) =>
    set({
      estimatedAbility: ability,
    }),

  updateTimeRemaining: (seconds) =>
    set({
      timeRemaining: seconds,
    }),

  endAssessment: () =>
    set({
      sessionId: null,
      currentQuestion: null,
      currentQuestionIndex: 0,
      totalQuestions: 0,
      responses: {},
      estimatedAbility: null,
      timeRemaining: null,
    }),
}));
```

---

## Internationalization (i18n)

### next-i18next Configuration

```javascript
// next-i18next.config.js
module.exports = {
  i18n: {
    defaultLocale: "en",
    locales: ["en", "ko", "es", "zh"],
  },
  reloadOnPrerender: process.env.NODE_ENV === "development",
};
```

### Translation Files

```json
// public/locales/en/common.json
{
  "nav": {
    "dashboard": "Dashboard",
    "assessments": "Assessments",
    "tutor": "AI Tutor",
    "reports": "Reports",
    "settings": "Settings"
  },
  "auth": {
    "login": "Log In",
    "logout": "Log Out",
    "signup": "Sign Up",
    "email": "Email",
    "password": "Password",
    "forgotPassword": "Forgot Password?"
  },
  "common": {
    "loading": "Loading...",
    "error": "An error occurred",
    "save": "Save",
    "cancel": "Cancel",
    "submit": "Submit",
    "next": "Next",
    "previous": "Previous",
    "finish": "Finish"
  }
}
```

```json
// public/locales/ko/common.json
{
  "nav": {
    "dashboard": "대시보드",
    "assessments": "평가",
    "tutor": "AI 튜터",
    "reports": "리포트",
    "settings": "설정"
  },
  "auth": {
    "login": "로그인",
    "logout": "로그아웃",
    "signup": "회원가입",
    "email": "이메일",
    "password": "비밀번호",
    "forgotPassword": "비밀번호를 잊으셨나요?"
  },
  "common": {
    "loading": "로딩 중...",
    "error": "오류가 발생했습니다",
    "save": "저장",
    "cancel": "취소",
    "submit": "제출",
    "next": "다음",
    "previous": "이전",
    "finish": "완료"
  }
}
```

### Using Translations in Components

```typescript
// app/[locale]/dashboard/page.tsx
import { useTranslation } from "next-i18next";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

export default function DashboardPage() {
  const { t } = useTranslation("common");

  return (
    <div>
      <h1>{t("nav.dashboard")}</h1>
      {/* ... */}
    </div>
  );
}

export async function getStaticProps({ locale }: { locale: string }) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common", "dashboard"])),
    },
  };
}
```

---

## API Integration

### API Client (Axios)

```typescript
// lib/api/client.ts
import axios, { AxiosInstance, AxiosError } from "axios";
import { useAuthStore } from "@/lib/store/authStore";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor: Add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = useAuthStore.getState().token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor: Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Unauthorized: Clear auth and redirect to login
          useAuthStore.getState().logout();
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get<T>(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }
}

export const apiClient = new APIClient();
```

### React Query Setup

```typescript
// components/providers/QueryProvider.tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### API Hooks (React Query)

```typescript
// lib/api/assessments.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "./client";

export interface Assessment {
  id: string;
  title: string;
  description: string;
  totalQuestions: number;
  estimatedTime: number;
  difficulty: string;
}

export interface AssessmentSession {
  sessionId: string;
  assessmentId: string;
  currentQuestionIndex: number;
  estimatedAbility: number;
  timeRemaining: number;
}

// Fetch all assessments
export function useAssessments() {
  return useQuery({
    queryKey: ["assessments"],
    queryFn: () => apiClient.get<Assessment[]>("/api/assessments"),
  });
}

// Fetch single assessment
export function useAssessment(id: string) {
  return useQuery({
    queryKey: ["assessments", id],
    queryFn: () => apiClient.get<Assessment>(`/api/assessments/${id}`),
    enabled: !!id,
  });
}

// Start assessment session
export function useStartAssessment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (assessmentId: string) =>
      apiClient.post<AssessmentSession>("/api/assessments/start", {
        assessmentId,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assessments"] });
    },
  });
}

// Submit answer
export function useSubmitAnswer() {
  return useMutation({
    mutationFn: ({
      sessionId,
      questionId,
      response,
    }: {
      sessionId: string;
      questionId: string;
      response: number;
    }) =>
      apiClient.post(`/api/assessments/${sessionId}/submit`, {
        questionId,
        response,
      }),
  });
}
```

---

## Performance Optimization

### Code Splitting & Lazy Loading

```typescript
// app/[locale]/dashboard/page.tsx
import dynamic from "next/dynamic";
import { Suspense } from "react";

// Lazy load heavy components
const AssessmentChart = dynamic(
  () => import("@/components/features/dashboard/AssessmentChart"),
  {
    loading: () => <div>Loading chart...</div>,
    ssr: false, // Disable SSR for client-only components
  }
);

const AITutorWidget = dynamic(
  () => import("@/components/features/tutor/TutorWidget"),
  {
    loading: () => <div>Loading AI Tutor...</div>,
  }
);

export default function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>

      <Suspense fallback={<div>Loading...</div>}>
        <AssessmentChart />
      </Suspense>

      <Suspense fallback={<div>Loading AI Tutor...</div>}>
        <AITutorWidget />
      </Suspense>
    </div>
  );
}
```

### Image Optimization

```typescript
// components/features/dashboard/ProfileAvatar.tsx
import Image from "next/image";

export function ProfileAvatar({ src, name }: { src: string; name: string }) {
  return (
    <div className="relative h-12 w-12">
      <Image
        src={src}
        alt={`${name}'s avatar`}
        fill
        sizes="(max-width: 768px) 48px, 48px"
        className="rounded-full object-cover"
        priority={false} // Set to true for above-the-fold images
      />
    </div>
  );
}
```

### Font Optimization

```typescript
// app/[locale]/layout.tsx
import { Inter, Roboto_Mono } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const robotoMono = Roboto_Mono({
  subsets: ["latin"],
  variable: "--font-roboto-mono",
  display: "swap",
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${robotoMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
```

### Memoization & useMemo

```typescript
// components/features/dashboard/RecentScores.tsx
import { useMemo } from "react";

interface Score {
  id: string;
  value: number;
  date: string;
}

export function RecentScores({ scores }: { scores: Score[] }) {
  // Expensive calculation: Only recompute when scores change
  const averageScore = useMemo(() => {
    if (scores.length === 0) return 0;
    return scores.reduce((sum, score) => sum + score.value, 0) / scores.length;
  }, [scores]);

  const sortedScores = useMemo(() => {
    return [...scores].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    );
  }, [scores]);

  return (
    <div>
      <h3>Average Score: {averageScore.toFixed(1)}</h3>
      <ul>
        {sortedScores.map((score) => (
          <li key={score.id}>
            {score.value} - {score.date}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Testing Strategy

### Unit Testing with Vitest

```typescript
// components/ui/button.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { Button } from "./button";

describe("Button", () => {
  it("renders with text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("calls onClick when clicked", async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    await userEvent.click(screen.getByText("Click me"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("is disabled when disabled prop is true", () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByText("Click me")).toBeDisabled();
  });
});
```

### E2E Testing with Playwright

```typescript
// e2e/assessment.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Assessment Flow", () => {
  test("student can start and complete assessment", async ({ page }) => {
    // Login
    await page.goto("/login");
    await page.fill('input[name="email"]', "student@example.com");
    await page.fill('input[name="password"]', "password123");
    await page.click('button[type="submit"]');

    // Navigate to assessments
    await page.click("text=Assessments");
    await expect(page).toHaveURL(/.*assessments/);

    // Start assessment
    await page.click("text=Start Test");
    await expect(page.locator("h2")).toContainText("Question 1");

    // Answer question
    await page.click('button:has-text("Option A")');
    await page.click("text=Submit");

    // Verify next question loads
    await expect(page.locator("h2")).toContainText("Question 2");
  });
});
```

### Component Testing

```typescript
// components/features/assessment/QuestionDisplay.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { QuestionDisplay } from "./QuestionDisplay";

describe("QuestionDisplay", () => {
  const mockQuestion = {
    id: "1",
    content: "What is 2 + 2?",
    options: ["3", "4", "5", "6"],
  };

  it("renders question and options", () => {
    render(<QuestionDisplay question={mockQuestion} onSubmit={vi.fn()} />);

    expect(screen.getByText("What is 2 + 2?")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("calls onSubmit with selected answer", async () => {
    const handleSubmit = vi.fn();
    render(<QuestionDisplay question={mockQuestion} onSubmit={handleSubmit} />);

    await userEvent.click(screen.getByText("4"));
    await userEvent.click(screen.getByRole("button", { name: /submit/i }));

    expect(handleSubmit).toHaveBeenCalledWith(1); // Index of selected option
  });
});
```

---

## Best Practices

### 1. Component Organization

- **Atomic Design**: Organize components from atoms → molecules → organisms → templates → pages
- **Single Responsibility**: Each component should do one thing well
- **Prop Types**: Use TypeScript interfaces for all props

### 2. Performance

- **Code Splitting**: Use `dynamic()` for heavy components
- **Memoization**: Use `useMemo` and `useCallback` for expensive computations
- **Image Optimization**: Always use Next.js `Image` component
- **Font Loading**: Use `next/font` for optimized font loading

### 3. Accessibility

- **Semantic HTML**: Use proper HTML5 elements
- **ARIA Labels**: Add `aria-label` for icon buttons
- **Keyboard Navigation**: Ensure all interactive elements are keyboard accessible
- **Color Contrast**: Maintain WCAG AA color contrast ratios

### 4. State Management

- **Local State**: Use `useState` for component-specific state
- **Global State**: Use Zustand for app-wide state (auth, theme)
- **Server State**: Use React Query for API data
- **Form State**: Use React Hook Form for complex forms

### 5. Error Handling

- **Error Boundaries**: Wrap components in error boundaries
- **Loading States**: Show loading indicators for async operations
- **Error Messages**: Display user-friendly error messages
- **Retry Logic**: Implement retry for failed API calls

---

## Next Steps

Continue to:

- **[Guide 12: Student Interface](./12-ux-student-interface.md)** - Student dashboard and assessment UI
- **[Guide 13: Teacher & Admin Console](./13-ux-teacher-admin-console.md)** - R Shiny implementation
- **[Guide 14: Accessibility & Performance](./14-ux-accessibility-performance.md)** - WCAG compliance and optimization

---

**Last Updated**: November 9, 2025  
**Version**: 1.0  
**Author**: DreamSeedAI Development Team
