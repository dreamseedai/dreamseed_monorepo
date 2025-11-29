# Phase 1.0 Alpha - Frontend Component Structure

**Project:** DreamSeed AI Platform  
**Framework:** Next.js 14 (App Router) or React + Vite  
**Date:** November 24, 2025  
**Status:** 📋 Design Complete  

> **Note:** This structure is designed for Next.js 14 App Router but is easily adaptable to React + Vite.

---

## 📁 Directory Structure

```
dreamseed_monorepo/
└── apps/
    └── student_front/                    # Frontend application
        ├── public/
        │   ├── logo.svg
        │   └── favicon.ico
        │
        ├── src/
        │   ├── app/                      # Next.js 14 App Router
        │   │   ├── layout.tsx            # Root layout (global nav, footer)
        │   │   ├── page.tsx              # Landing page (/)
        │   │   │
        │   │   ├── login/
        │   │   │   └── page.tsx          # Login page
        │   │   │
        │   │   ├── register/
        │   │   │   └── page.tsx          # Register page
        │   │   │
        │   │   ├── dashboard/
        │   │   │   ├── layout.tsx        # Protected layout (requires auth)
        │   │   │   └── page.tsx          # Student dashboard
        │   │   │
        │   │   └── exam/
        │   │       ├── layout.tsx        # Exam layout (minimal nav)
        │   │       ├── start/
        │   │       │   └── page.tsx      # Exam intro/start
        │   │       ├── question/
        │   │       │   └── page.tsx      # Question display
        │   │       └── result/
        │   │           └── page.tsx      # Result display
        │   │
        │   ├── components/               # Reusable components
        │   │   ├── ui/                   # Base UI components
        │   │   │   ├── Button.tsx
        │   │   │   ├── Card.tsx
        │   │   │   ├── Input.tsx
        │   │   │   ├── Loader.tsx
        │   │   │   ├── Badge.tsx
        │   │   │   ├── Toast.tsx
        │   │   │   └── ProgressBar.tsx
        │   │   │
        │   │   ├── auth/                 # Auth-specific components
        │   │   │   ├── LoginForm.tsx
        │   │   │   ├── RegisterForm.tsx
        │   │   │   └── ProtectedRoute.tsx
        │   │   │
        │   │   ├── exam/                 # Exam-specific components
        │   │   │   ├── QuestionCard.tsx
        │   │   │   ├── OptionButton.tsx
        │   │   │   ├── ExamProgressBar.tsx
        │   │   │   └── ResultCard.tsx
        │   │   │
        │   │   ├── dashboard/            # Dashboard components
        │   │   │   ├── RecentTestList.tsx
        │   │   │   ├── TestCard.tsx
        │   │   │   └── EmptyState.tsx
        │   │   │
        │   │   └── layout/               # Layout components
        │   │       ├── Header.tsx
        │   │       ├── Footer.tsx
        │   │       └── NavBar.tsx
        │   │
        │   ├── lib/                      # Utility libraries
        │   │   ├── api/                  # API client
        │   │   │   ├── client.ts         # Axios instance config
        │   │   │   ├── auth.ts           # Auth API methods
        │   │   │   └── exam.ts           # Exam API methods
        │   │   │
        │   │   ├── auth.ts               # Auth utilities (token management)
        │   │   ├── scoring.ts            # Score conversion utilities
        │   │   ├── types.ts              # TypeScript types
        │   │   └── utils.ts              # General utilities (classnames, etc.)
        │   │
        │   ├── hooks/                    # Custom React hooks
        │   │   ├── useAuth.ts            # Auth state management
        │   │   ├── useExam.ts            # Exam state management
        │   │   └── useToast.ts           # Toast notification hook
        │   │
        │   ├── context/                  # React Context providers
        │   │   ├── AuthContext.tsx       # Global auth state
        │   │   └── ExamContext.tsx       # Exam session state
        │   │
        │   └── styles/
        │       ├── globals.css           # Global styles + Tailwind imports
        │       └── theme.css             # Custom theme variables
        │
        ├── .env.local                    # Environment variables
        ├── .env.production               # Production env vars
        ├── next.config.js                # Next.js config
        ├── tailwind.config.js            # Tailwind config
        ├── tsconfig.json                 # TypeScript config
        └── package.json
```

---

## ⭐ Component Hierarchy & Flow

### 1. Landing Page Flow

```
app/page.tsx (Landing)
├── Header
│   ├── Logo
│   ├── NavBar
│   └── CTA Buttons (시작하기, 로그인)
├── Hero Section
│   ├── Heading: "AI 기반 능력 진단 테스트"
│   ├── Description
│   └── Primary CTA: "시작하기" → /register
└── Footer
    ├── Copyright
    └── Alpha Badge
```

---

### 2. Auth Flow

#### Register Page (`/register`)

```
app/register/page.tsx
└── <RegisterForm />
    ├── <Input /> (email)
    ├── <Input /> (password)
    ├── <Input /> (name)
    ├── Validation errors (inline)
    └── <Button /> (회원가입)
        → Success: Auto-login + redirect to /dashboard
        → Error: <Toast /> (error message)
```

**Component:** `components/auth/RegisterForm.tsx`

```tsx
export function RegisterForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const { register } = useAuth()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    try {
      await register({ email, password, name })
      router.push('/dashboard')
    } catch (error) {
      toast.error('회원가입에 실패했습니다')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <Input label="이메일" value={email} onChange={setEmail} />
      <Input label="비밀번호" type="password" value={password} onChange={setPassword} />
      <Input label="이름" value={name} onChange={setName} />
      <Button type="submit">회원가입</Button>
    </form>
  )
}
```

#### Login Page (`/login`)

```
app/login/page.tsx
└── <LoginForm />
    ├── <Input /> (email)
    ├── <Input /> (password)
    ├── "비밀번호 찾기" link (placeholder)
    └── <Button /> (로그인)
        → Success: redirect to /dashboard
        → Error: <Toast /> (401 error)
```

---

### 3. Dashboard Flow

```
app/dashboard/page.tsx
├── Protected by <ProtectedRoute />
├── Header
│   ├── User name
│   └── Logout button
├── Subject Selection
│   ├── <Card /> Math (enabled) → /exam/start?subject=math
│   ├── <Card /> English (disabled, "Coming Soon")
│   └── <Card /> Science (disabled, "Coming Soon")
└── <RecentTestList />
    ├── If tests exist: <TestCard /> × 3
    └── If empty: <EmptyState /> ("첫 진단 시작하기")
```

**Component:** `components/dashboard/RecentTestList.tsx`

```tsx
export function RecentTestList() {
  const { data: tests, isLoading } = useQuery({
    queryKey: ['exam-history'],
    queryFn: () => api.exam.getHistory()
  })

  if (isLoading) return <Loader />
  if (!tests || tests.length === 0) return <EmptyState />

  return (
    <div className="space-y-4">
      {tests.slice(0, 3).map(test => (
        <TestCard key={test.id} test={test} />
      ))}
    </div>
  )
}
```

---

### 4. Exam Flow

#### Step 1: Exam Start (`/exam/start`)

```
app/exam/start/page.tsx
└── <Card /> (Exam Intro)
    ├── Heading: "Math 진단 테스트"
    ├── Description: "예상 시간 10-20분, 10-20문항"
    ├── Warning: "중간에 나가면 결과 저장 안 됨"
    └── <Button /> (시작하기)
        → API: POST /api/adaptive/exams/start
        → Success: Save session_id → /exam/question
```

#### Step 2: Question Display (`/exam/question`)

```
app/exam/question/page.tsx
├── <ExamProgressBar /> (문항 X / ?)
├── <QuestionCard />
│   ├── Question text
│   └── <OptionButton /> × 4 (A, B, C, D)
│       → Selected: highlight style
├── <Button /> (다음)
│   → Disabled until option selected
│   → API: POST /api/adaptive/exams/{session_id}/submit-answer
│   → API: GET /api/adaptive/exams/{session_id}/next-item
│   → If finished=true: redirect to /exam/result
│   → Else: render next question
└── Error handling
    ├── Network error: <Toast /> + "다시 시도" button
    └── Timeout: "잠시 후 다시 시도해주세요"
```

**Component:** `components/exam/QuestionCard.tsx`

```tsx
export function QuestionCard({ item, onAnswer }: QuestionCardProps) {
  const [selectedChoice, setSelectedChoice] = useState<number | null>(null)

  return (
    <Card>
      <h2 className="text-lg font-semibold mb-4">{item.question_text}</h2>
      <div className="space-y-2">
        {item.choices.map(choice => (
          <OptionButton
            key={choice.id}
            choice={choice}
            selected={selectedChoice === choice.id}
            onClick={() => setSelectedChoice(choice.id)}
          />
        ))}
      </div>
      <Button
        disabled={selectedChoice === null}
        onClick={() => onAnswer(selectedChoice!)}
      >
        다음
      </Button>
    </Card>
  )
}
```

#### Step 3: Results (`/exam/result`)

```
app/exam/result/page.tsx
├── API: GET /api/adaptive/exams/{session_id}/results
└── <ResultCard />
    ├── Score: 67/100 (large display)
    ├── <Badge /> (Level: Intermediate)
    ├── Grade: B
    ├── Feedback: "중급 수준. 함수 문제 연습 추천"
    ├── Stats (optional):
    │   ├── Total items: 12
    │   ├── Correct: 8
    │   └── Accuracy: 67%
    └── Buttons:
        ├── <Button /> (다시 테스트하기) → /exam/start
        └── <Button /> (대시보드) → /dashboard
```

---

## 🎨 UI Component Library (Tailwind-based)

### Base Components (`components/ui/`)

#### Button.tsx
```tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  onClick?: () => void
  children: ReactNode
}

export function Button({ variant = 'primary', size = 'md', ... }: ButtonProps) {
  const baseStyles = 'rounded-lg font-semibold transition-colors'
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    outline: 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50'
  }
  // ...
}
```

#### Card.tsx
```tsx
export function Card({ children, className }: CardProps) {
  return (
    <div className={cn('bg-white rounded-lg shadow-md p-6', className)}>
      {children}
    </div>
  )
}
```

#### Input.tsx
```tsx
export function Input({ label, error, ...props }: InputProps) {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-2">{label}</label>
      <input
        className={cn(
          'w-full px-4 py-2 border rounded-lg',
          error ? 'border-red-500' : 'border-gray-300'
        )}
        {...props}
      />
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  )
}
```

---

## 🔌 API Client Structure (`lib/api/`)

### client.ts (Axios Instance)

```typescript
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor: Add JWT token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: Handle 401
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### auth.ts (Auth API Methods)

```typescript
import { apiClient } from './client'

export const authApi = {
  register: async (data: RegisterRequest) => {
    const response = await apiClient.post('/api/auth/register', data)
    return response.data
  },

  login: async (data: LoginRequest) => {
    const response = await apiClient.post('/api/auth/login', data)
    const { access_token } = response.data
    localStorage.setItem('token', access_token)
    return response.data
  },

  logout: () => {
    localStorage.removeItem('token')
  }
}
```

### exam.ts (Exam API Methods)

```typescript
export const examApi = {
  startExam: async (poolId: number) => {
    const response = await apiClient.post('/api/adaptive/exams/start', {
      pool_id: poolId
    })
    return response.data // { session_id, initial_theta }
  },

  getNextItem: async (sessionId: string) => {
    const response = await apiClient.get(
      `/api/adaptive/exams/${sessionId}/next-item`
    )
    return response.data // { item_id, question_text, choices }
  },

  submitAnswer: async (sessionId: string, itemId: number, choiceId: number) => {
    const response = await apiClient.post(
      `/api/adaptive/exams/${sessionId}/submit-answer`,
      { item_id: itemId, choice_id: choiceId }
    )
    return response.data // { is_correct, new_theta, se }
  },

  getResults: async (sessionId: string) => {
    const response = await apiClient.get(
      `/api/adaptive/exams/${sessionId}/results`
    )
    return response.data // { theta, score, grade, level, feedback }
  },

  getHistory: async () => {
    const response = await apiClient.get('/api/adaptive/exams/history')
    return response.data // [{ id, date, subject, score, level }]
  }
}
```

---

## 🪝 Custom Hooks

### useAuth.ts

```typescript
export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      // Decode JWT or fetch user info
      // setUser(decodedUser)
    }
    setIsLoading(false)
  }, [])

  const register = async (data: RegisterRequest) => {
    const response = await authApi.register(data)
    const { access_token } = await authApi.login({
      email: data.email,
      password: data.password
    })
    localStorage.setItem('token', access_token)
    // setUser from token
  }

  const login = async (data: LoginRequest) => {
    const response = await authApi.login(data)
    // setUser from token
  }

  const logout = () => {
    authApi.logout()
    setUser(null)
  }

  return { user, isLoading, register, login, logout }
}
```

### useExam.ts

```typescript
export function useExam(sessionId: string) {
  const [currentItem, setCurrentItem] = useState<Item | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isFinished, setIsFinished] = useState(false)

  const fetchNextItem = async () => {
    setIsLoading(true)
    try {
      const item = await examApi.getNextItem(sessionId)
      if (item.finished) {
        setIsFinished(true)
      } else {
        setCurrentItem(item)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const submitAnswer = async (itemId: number, choiceId: number) => {
    const response = await examApi.submitAnswer(sessionId, itemId, choiceId)
    if (response.finished) {
      setIsFinished(true)
    } else {
      await fetchNextItem()
    }
  }

  return { currentItem, isLoading, isFinished, fetchNextItem, submitAnswer }
}
```

---

## 🎨 Tailwind Theme Configuration

### tailwind.config.js

```javascript
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          // ... blue scale
          600: '#2563eb', // Main brand color
          700: '#1d4ed8'
        },
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif']
      }
    }
  },
  plugins: []
}
```

---

## 📝 TypeScript Types (`lib/types.ts`)

```typescript
// Auth types
export interface User {
  id: string
  email: string
  name: string
  role: 'student' | 'teacher' | 'admin'
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
}

export interface LoginRequest {
  email: string
  password: string
}

// Exam types
export interface ExamSession {
  session_id: string
  pool_id: number
  initial_theta: number
  created_at: string
}

export interface Item {
  item_id: number
  question_text: string
  choices: Choice[]
}

export interface Choice {
  choice_id: number
  choice_text: string
}

export interface SubmitAnswerResponse {
  is_correct: boolean
  new_theta: number
  se: number
  finished: boolean
}

export interface ExamResult {
  session_id: string
  theta: number
  score: number // 0-100
  grade: string // A, B, C, D, F
  level: 'Basic' | 'Intermediate' | 'Advanced'
  feedback: string
  total_items: number
  correct_items: number
}

export interface ExamHistory {
  session_id: string
  date: string
  subject: string
  score: number
  level: string
}
```

---

## 🚀 Next Steps

### 1. Project Initialization

**Option A: Next.js 14**
```bash
cd /home/won/projects/dreamseed_monorepo/apps
npx create-next-app@latest student_front \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*"
```

**Option B: React + Vite**
```bash
cd /home/won/projects/dreamseed_monorepo/apps
npm create vite@latest student_front -- --template react-ts
cd student_front
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. Install Dependencies

```bash
npm install axios
npm install @tanstack/react-query  # For API state management
npm install react-hook-form        # For form validation
npm install clsx tailwind-merge    # For className utilities
npm install lucide-react           # For icons
```

### 3. Create Base Structure

```bash
mkdir -p src/{components/{ui,auth,exam,dashboard,layout},lib/{api},hooks,context,styles}
```

---

## 📊 Component vs. Existing Backend

| Frontend Component | Backend API Endpoint | Status |
|--------------------|----------------------|--------|
| LoginForm | `POST /api/auth/login` | ❌ Not implemented |
| RegisterForm | `POST /api/auth/register` | ❌ Not implemented |
| ExamStart | `POST /api/adaptive/exams/start` | ✅ Ready (Phase 0.5) |
| QuestionCard | `GET /api/adaptive/exams/{id}/next-item` | ✅ Ready (Phase 0.5) |
| OptionButton | `POST /api/adaptive/exams/{id}/submit-answer` | ✅ Ready (Phase 0.5) |
| ResultCard | `GET /api/adaptive/exams/{id}/results` | ✅ Ready (Phase 0.5) |
| RecentTestList | `GET /api/adaptive/exams/history` | ❌ Not implemented |

**Missing APIs (Week 1 Priority):**
- Auth endpoints (register, login)
- Exam history endpoint

---

**Status:** 📋 **DESIGN COMPLETE - READY FOR IMPLEMENTATION**  
**Next Step:** Choose framework (Next.js vs Vite) by Nov 26  
**Related Docs:** [PHASE1_TASK_BREAKDOWN.md](./PHASE1_TASK_BREAKDOWN.md)  

---

**End of Frontend Component Structure**
