# DreamSeed CAT Dashboard - Integration Guide

## ✅ Completed Components

### 1. **Infrastructure** (Global Setup)
- ✅ `app/providers.tsx` - TanStack Query provider with 5min cache
- ✅ `app/layout.tsx` - Updated with `<AppProviders>` wrapper

### 2. **UI Component Library**
- ✅ `components/ui/Card.tsx` - Reusable card container with DreamSeed styling
- ✅ `components/ui/PageHeader.tsx` - Consistent page headers with title/subtitle/actions
- ✅ `components/ui/LoadingSpinner.tsx` - Loading and error state components

### 3. **API Client & Hooks**
- ✅ `lib/api/dashboard.ts` - Typed API client (4 endpoints)
- ✅ `lib/hooks/useDashboard.ts` - React Query hooks (4 hooks)

### 4. **Dashboard Pages**
- ✅ `app/teacher/classes/[classId]/page.tsx` - Teacher class overview
- ✅ `app/teacher/students/[studentId]/page.tsx` - Teacher student history
- ✅ `app/parent/children/[studentId]/page.tsx` - Parent child performance

### 5. **Dependencies**
- ✅ `@tanstack/react-query` ^5.62.0
- ✅ `clsx` ^2.1.1

---

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd /home/won/projects/dreamseed_monorepo/backend
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd /home/won/projects/dreamseed_monorepo/admin_front
npm run dev
```

### 3. Test URLs
- Teacher Class Dashboard: `http://localhost:3000/teacher/classes/1`
- Teacher Student History: `http://localhost:3000/teacher/students/1`
- Parent Child Performance: `http://localhost:3000/parent/children/1`

---

## 📋 API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/dashboard/teacher/classes/{id}` | GET | Get class exam summary |
| `/api/dashboard/teacher/students/{id}` | GET | Get student exam history |
| `/api/dashboard/parent/children/{id}` | GET | Get child exam results |
| `/api/dashboard/classes/{id}/statistics` | GET | Get class statistics |

---

## 🔐 Authentication Integration (TODO)

Currently, the API client has a `TODO` comment for authentication. To enable:

### Option 1: JWT Token (Recommended)
```typescript
// lib/api/dashboard.ts
const token = localStorage.getItem('access_token'); // or from your auth context
const response = await fetch(`${API_BASE_URL}${path}`, {
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,  // Uncomment this
  },
  credentials: 'include',
});
```

### Option 2: Session Cookie (Current)
The API client already includes `credentials: 'include'`, which sends cookies automatically. Ensure your backend:
- Sets `SameSite=None; Secure` for cross-origin requests
- Includes CORS headers with `Access-Control-Allow-Credentials: true`

---

## 🛡️ Route Protection

Add authentication middleware for teacher/parent routes:

### Example: Create Middleware
```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token');
  
  // Protect teacher routes
  if (request.nextUrl.pathname.startsWith('/teacher')) {
    if (!token) {
      return NextResponse.redirect(new URL('/login?role=teacher', request.url));
    }
    // TODO: Verify user role is 'teacher'
  }
  
  // Protect parent routes
  if (request.nextUrl.pathname.startsWith('/parent')) {
    if (!token) {
      return NextResponse.redirect(new URL('/login?role=parent', request.url));
    }
    // TODO: Verify user role is 'parent'
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/teacher/:path*', '/parent/:path*'],
};
```

---

## 🎨 Styling Patterns

### DreamSeed Design System
- **Cards**: `rounded-2xl shadow-sm hover:shadow-md bg-white dark:bg-gray-800`
- **Spacing**: `space-y-6` for page sections, `gap-4` for grids
- **Colors**:
  - Primary: `sky-600` / `sky-400` (dark mode)
  - Success: `green-600` / `green-400`
  - Warning: `yellow-600` / `yellow-400`
  - Error: `red-600` / `red-400`
- **Typography**:
  - Page Title: `text-2xl md:text-3xl font-bold`
  - Card Title: `text-base font-semibold`
  - Label: `text-xs font-semibold text-slate-500`

### Dark Mode Support
All components automatically support dark mode via Tailwind's `dark:` variants.

---

## 📊 Data Fetching Patterns

### React Query Configuration
```typescript
// app/providers.tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,      // 5 minutes
      refetchOnWindowFocus: false,   // Don't refetch on tab focus
      retry: 1,                       // Retry once on failure
    },
  },
});
```

### Hook Usage Example
```typescript
const { data, isLoading, isError, error } = useTeacherClassExams(classId);

// Loading state
if (isLoading) return <LoadingSpinner />;

// Error state
if (isError) return <ErrorMessage message={error.message} />;

// Success state
if (!data) return <ErrorMessage message="No data" />;
return <div>{/* Render data */}</div>;
```

---

## 🔍 Testing Checklist

- [ ] Backend API endpoints return expected data format
- [ ] Frontend can connect to backend (check CORS)
- [ ] Authentication tokens are sent correctly
- [ ] Loading states appear during data fetching
- [ ] Error messages display when API fails
- [ ] Dark mode works correctly
- [ ] Mobile responsive layout works
- [ ] Links navigate correctly between pages
- [ ] Statistics calculate correctly

---

## 🐛 Troubleshooting

### Issue: "Cannot connect to API"
**Solution**: Ensure backend is running on port 8000 and CORS is configured:
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "401 Unauthorized"
**Solution**: Check authentication implementation:
1. Verify JWT token is being sent in `Authorization` header
2. Ensure session cookie is being sent with `credentials: 'include'`
3. Check backend auth middleware is configured correctly

### Issue: "Type errors in TypeScript"
**Solution**: Run `npm run build` to check for type errors:
```bash
cd admin_front
npm run build
```

### Issue: "React Query not refetching"
**Solution**: Check `staleTime` configuration. To force refetch:
```typescript
const { refetch } = useTeacherClassExams(classId);
// Call refetch() when needed
```

---

## 📈 Next Steps (Optional Enhancements)

### 1. Add Charts (Recharts)
```bash
npm install recharts
```

Add score trend charts to student pages:
```tsx
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

<LineChart data={scoreData}>
  <XAxis dataKey="date" />
  <YAxis />
  <Line type="monotone" dataKey="score" stroke="#0ea5e9" />
  <Tooltip />
</LineChart>
```

### 2. Add Pagination
For classes with many students:
```typescript
// lib/hooks/useDashboard.ts
export function useTeacherClassExams(classId: string, page = 1, limit = 20) {
  return useQuery({
    queryKey: ["teacher-class-exams", classId, page, limit],
    queryFn: () => getTeacherClassExams(classId, page, limit),
    enabled: !!classId,
  });
}
```

### 3. Add Search/Filter
```tsx
const [searchTerm, setSearchTerm] = useState("");
const filteredStudents = data.students.filter(s => 
  s.student_id.toLowerCase().includes(searchTerm.toLowerCase())
);
```

### 4. Add Export Functionality
```tsx
const exportToCSV = () => {
  const csv = data.students.map(s => 
    `${s.student_id},${s.latest_exam?.score},${s.latest_exam?.grade_letter}`
  ).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'class_results.csv';
  a.click();
};
```

---

## 📝 Architecture Summary

```
admin_front/
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── providers.tsx           # TanStack Query provider
│   ├── teacher/
│   │   ├── classes/[classId]/
│   │   │   └── page.tsx        # Class overview
│   │   └── students/[studentId]/
│   │       └── page.tsx        # Student history
│   └── parent/
│       └── children/[studentId]/
│           └── page.tsx        # Child performance
├── components/
│   └── ui/
│       ├── Card.tsx            # Reusable card container
│       ├── PageHeader.tsx      # Page header component
│       └── LoadingSpinner.tsx  # Loading/error states
└── lib/
    ├── api/
    │   └── dashboard.ts        # API client with types
    └── hooks/
        └── useDashboard.ts     # React Query hooks
```

### Data Flow
```
Page Component
    ↓ uses
React Query Hook (useDashboard.ts)
    ↓ calls
API Client (dashboard.ts)
    ↓ fetches from
FastAPI Backend (dashboard.py)
    ↓ returns
TypeScript Types → React Query Cache → UI Components
```

---

## 🎯 Phase 1 Complete!

✅ **Teacher Dashboard**: Class overview with student summaries  
✅ **Teacher Student View**: Individual student exam history with IRT data  
✅ **Parent Dashboard**: Child performance with percentile rankings  
✅ **Modern Architecture**: Next.js App Router + TanStack Query  
✅ **DreamSeed Design**: Consistent UI with dark mode support  
✅ **Type Safety**: Full TypeScript types across API/UI  

Ready for demo! 🚀
