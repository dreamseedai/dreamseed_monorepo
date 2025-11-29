# Frontend Integration Guide

**Document**: 05_FRONTEND_INTEGRATION_GUIDE.md  
**Part of**: IRT System Documentation Series  
**Created**: 2025-11-05  
**Status**: ✅ Production Ready  

---

## Table of Contents

1. [Overview](#overview)
2. [MonthlyDriftReport Component](#monthlydriftreport-component)
3. [Integration Examples](#integration-examples)
4. [i18n Configuration](#i18n-configuration)
5. [Custom Styling](#custom-styling)
6. [Advanced Usage](#advanced-usage)
7. [Troubleshooting](#troubleshooting)
8. [한글 가이드 (Korean Guide)](#한글-가이드-korean-guide)

---

## Overview

### Available Components

| Component | Purpose | Framework |
|-----------|---------|-----------|
| `MonthlyDriftReport` | Display drift alerts and download reports | React/TypeScript |

### File Locations

```
shared/frontend/irt/
├── MonthlyDriftReport.tsx    # Main component
├── index.ts                   # Exports
├── README.md                  # Component docs
└── locales/
    ├── en.json               # English translations
    ├── ko.json               # Korean translations
    ├── zh-Hans.json          # Simplified Chinese
    └── zh-Hant.json          # Traditional Chinese
```

---

## MonthlyDriftReport Component

### Props Interface

```typescript
interface MonthlyDriftReportProps {
  // Required
  apiBaseUrl: string;          // API base URL
  t: (key: string) => string;  // Translation function
  
  // Optional - Custom components
  CardComponent?: React.ComponentType<{
    title?: string;
    children: React.ReactNode;
  }>;
  ButtonComponent?: React.ComponentType<{
    onClick?: () => void;
    children: React.ReactNode;
    variant?: string;
  }>;
  
  // Optional - Behavior
  defaultWindowId?: number;    // Default window to display
  autoRefresh?: boolean;       // Auto-refresh every N seconds
  refreshInterval?: number;    // Refresh interval (ms)
  
  // Optional - Styling
  className?: string;          // Custom CSS class
  theme?: 'light' | 'dark';    // Theme
}
```

---

### Basic Usage

```typescript
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'react-i18next';

function DriftPage() {
  const { t } = useTranslation();
  
  return (
    <MonthlyDriftReport
      apiBaseUrl="https://api.dreamseedai.com/api/irt"
      t={t}
    />
  );
}
```

---

### Features

#### 1. Window Selection
- Dropdown to select calibration window
- Shows window date range (e.g., "2024-10-01 to 2024-10-31")
- Displays alert counts (critical/high/medium)

#### 2. Alert Table
- Lists all drift alerts for selected window
- Columns: Item ID, Metric, Old Value, New Value, Delta, Severity
- Color-coded severity (red=critical, orange=high, yellow=medium)
- Sortable columns

#### 3. PDF Download
- Download monthly calibration report
- Button with loading state
- Error handling

#### 4. Loading States
- Skeleton loaders during data fetch
- Graceful error messages

---

## Integration Examples

### Example 1: Portal (Vite + React)

```typescript
// File: portal_front/src/pages/admin/IrtDriftPage.tsx

import React from 'react';
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'react-i18next';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function IrtDriftPage() {
  const { t } = useTranslation();
  
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">
        {t('irt.drift.page_title')}
      </h1>
      
      <MonthlyDriftReport
        apiBaseUrl={import.meta.env.VITE_API_BASE_URL + '/api/irt'}
        t={t}
        CardComponent={Card}
        ButtonComponent={Button}
        autoRefresh={true}
        refreshInterval={60000}  // Refresh every 60 seconds
        theme="light"
      />
    </div>
  );
}
```

**Route Configuration** (`portal_front/src/App.tsx`):
```typescript
import IrtDriftPage from './pages/admin/IrtDriftPage';

<Route path="/admin/irt/drift" element={<IrtDriftPage />} />
```

---

### Example 2: Next.js (App Router)

```typescript
// File: apps/examinee-frontend/app/admin/irt-drift/page.tsx

'use client';

import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'next-i18next';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function IrtDriftPage() {
  const { t } = useTranslation('common');
  
  return (
    <main className="container mx-auto py-8">
      <h1 className="text-4xl font-bold mb-8">
        IRT Parameter Drift Monitoring
      </h1>
      
      <MonthlyDriftReport
        apiBaseUrl={process.env.NEXT_PUBLIC_API_URL + '/api/irt'}
        t={t}
        CardComponent={Card}
        ButtonComponent={Button}
        className="mb-8"
      />
    </main>
  );
}
```

**Environment Variables** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=https://api.dreamseedai.com
```

---

### Example 3: Standalone (No UI Library)

```typescript
// File: portal_front/src/pages/DriftMonitoring.tsx

import React from 'react';
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'react-i18next';

// Simple Card component
const SimpleCard = ({ title, children }) => (
  <div className="border rounded-lg p-4 shadow-sm bg-white">
    {title && <h3 className="text-lg font-semibold mb-3">{title}</h3>}
    {children}
  </div>
);

// Simple Button component
const SimpleButton = ({ onClick, children, variant = 'primary' }) => {
  const baseClass = "px-4 py-2 rounded font-medium";
  const variantClass = variant === 'primary' 
    ? "bg-blue-600 text-white hover:bg-blue-700"
    : "bg-gray-200 text-gray-800 hover:bg-gray-300";
  
  return (
    <button 
      onClick={onClick} 
      className={`${baseClass} ${variantClass}`}
    >
      {children}
    </button>
  );
};

export default function DriftMonitoring() {
  const { t } = useTranslation();
  
  return (
    <div className="max-w-7xl mx-auto p-6">
      <MonthlyDriftReport
        apiBaseUrl="/api/irt"
        t={t}
        CardComponent={SimpleCard}
        ButtonComponent={SimpleButton}
      />
    </div>
  );
}
```

---

### Example 4: With Custom Filtering

```typescript
// File: portal_front/src/pages/DriftDashboard.tsx

import React, { useState } from 'react';
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'react-i18next';

export default function DriftDashboard() {
  const { t } = useTranslation();
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  
  return (
    <div className="p-6">
      {/* Custom Filter Controls */}
      <div className="mb-4 flex gap-4">
        <label className="flex items-center gap-2">
          Severity:
          <select 
            value={severityFilter} 
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="all">All</option>
            <option value="critical">Critical Only</option>
            <option value="high">High & Critical</option>
          </select>
        </label>
      </div>
      
      {/* Drift Report Component */}
      <MonthlyDriftReport
        apiBaseUrl="/api/irt"
        t={t}
        // Pass filter as query param
        apiBaseUrl={`/api/irt?severity=${severityFilter}`}
      />
    </div>
  );
}
```

---

## i18n Configuration

### Setting Up react-i18next (Vite)

**Install dependencies**:
```bash
npm install react-i18next i18next
```

**Configuration** (`portal_front/src/i18n/index.ts`):
```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Import translations
import enCommon from './locales/en/common.json';
import koCommon from './locales/ko/common.json';
import enIrt from '../../../shared/frontend/irt/locales/en.json';
import koIrt from '../../../shared/frontend/irt/locales/ko.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        common: enCommon,
        irt: enIrt
      },
      ko: {
        common: koCommon,
        irt: koIrt
      }
    },
    lng: 'en', // Default language
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    },
    ns: ['common', 'irt'],
    defaultNS: 'common'
  });

export default i18n;
```

**Main entry point** (`portal_front/src/main.tsx`):
```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import './i18n';  // Import i18n config
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

---

### Setting Up next-i18next (Next.js)

**Install dependencies**:
```bash
npm install next-i18next i18next react-i18next
```

**Configuration** (`apps/examinee-frontend/next-i18next.config.js`):
```javascript
module.exports = {
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'ko', 'zh-Hans', 'zh-Hant']
  },
  localePath: './public/locales'
};
```

**Copy translations** to `public/locales/`:
```bash
mkdir -p apps/examinee-frontend/public/locales/en
mkdir -p apps/examinee-frontend/public/locales/ko

cp shared/frontend/irt/locales/en.json \
   apps/examinee-frontend/public/locales/en/irt.json

cp shared/frontend/irt/locales/ko.json \
   apps/examinee-frontend/public/locales/ko/irt.json
```

**Next.js config** (`next.config.js`):
```javascript
const { i18n } = require('./next-i18next.config');

module.exports = {
  i18n,
  // ... other config
};
```

---

### Translation Keys

All IRT component translations use the `irt.drift.*` namespace:

```typescript
// Available keys
t('irt.drift.title')                    // "IRT Parameter Drift Monitoring"
t('irt.drift.select_window')            // "Select Calibration Window"
t('irt.drift.alerts_for_window')        // "Alerts for Window"
t('irt.drift.download_pdf')             // "Download PDF Report"
t('irt.drift.downloading')              // "Downloading..."
t('irt.drift.loading')                  // "Loading drift data..."
t('irt.drift.no_alerts')                // "No alerts for this window"
t('irt.drift.col.item_id')              // "Item ID"
t('irt.drift.col.metric')               // "Metric"
t('irt.drift.col.old_value')            // "Old Value"
t('irt.drift.col.new_value')            // "New Value"
t('irt.drift.col.delta')                // "Delta"
t('irt.drift.col.severity')             // "Severity"
```

---

## Custom Styling

### Tailwind CSS (Default)

The component uses Tailwind classes by default:

```typescript
<MonthlyDriftReport
  apiBaseUrl="/api/irt"
  t={t}
  className="max-w-6xl mx-auto"  // Add custom Tailwind classes
/>
```

---

### Custom Theme

```typescript
// Define custom theme
const darkTheme = {
  card: 'bg-gray-800 text-white',
  table: 'bg-gray-900',
  button: 'bg-blue-600 hover:bg-blue-700'
};

// Wrap component with theme provider
<div className={darkTheme.card}>
  <MonthlyDriftReport
    apiBaseUrl="/api/irt"
    t={t}
    theme="dark"
  />
</div>
```

---

### Severity Colors

Override severity colors with CSS:

```css
/* File: portal_front/src/styles/irt.css */

.severity-critical {
  @apply bg-red-100 text-red-800 border-red-200;
}

.severity-high {
  @apply bg-orange-100 text-orange-800 border-orange-200;
}

.severity-medium {
  @apply bg-yellow-100 text-yellow-800 border-yellow-200;
}
```

---

## Advanced Usage

### Example 1: Real-time Updates with WebSocket

```typescript
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function RealtimeDriftMonitor() {
  const { t } = useTranslation();
  const [wsData, setWsData] = useState(null);
  
  useEffect(() => {
    const ws = new WebSocket('wss://api.dreamseedai.com/ws/irt');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'drift_alert') {
        setWsData(data);
        // Trigger component refresh
      }
    };
    
    return () => ws.close();
  }, []);
  
  return (
    <div>
      {wsData && (
        <div className="bg-red-100 border border-red-400 p-4 mb-4">
          🚨 New critical alert: Item {wsData.item_id}
        </div>
      )}
      
      <MonthlyDriftReport
        apiBaseUrl="/api/irt"
        t={t}
        autoRefresh={true}
        refreshInterval={30000}
      />
    </div>
  );
}
```

---

### Example 2: Export to CSV

```typescript
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function DriftExport() {
  const { t } = useTranslation();
  const [alerts, setAlerts] = useState([]);
  
  const exportToCSV = () => {
    const csv = [
      ['Item ID', 'Metric', 'Old Value', 'New Value', 'Delta', 'Severity'],
      ...alerts.map(a => [
        a.item_id,
        a.metric,
        a.old_value,
        a.new_value,
        a.delta,
        a.severity
      ])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'drift_alerts.csv';
    a.click();
  };
  
  return (
    <div>
      <button onClick={exportToCSV}>Export to CSV</button>
      
      <MonthlyDriftReport
        apiBaseUrl="/api/irt"
        t={t}
        onDataLoad={(data) => setAlerts(data.alerts)}
      />
    </div>
  );
}
```

---

### Example 3: Multi-Project Dashboard

```typescript
// File: portal_front/src/pages/MultiProjectDrift.tsx

import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'react-i18next';

const projects = [
  { id: 'portal', name: 'Portal', apiUrl: 'https://api.portal.com' },
  { id: 'univ', name: 'University', apiUrl: 'https://api.univ.com' },
  { id: 'parent', name: 'Parent', apiUrl: 'https://api.parent.com' }
];

export default function MultiProjectDrift() {
  const { t } = useTranslation();
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
      {projects.map(project => (
        <div key={project.id}>
          <h2 className="text-2xl font-bold mb-4">{project.name}</h2>
          <MonthlyDriftReport
            apiBaseUrl={`${project.apiUrl}/api/irt`}
            t={t}
          />
        </div>
      ))}
    </div>
  );
}
```

---

## Troubleshooting

### Issue 1: Translation Keys Not Found

**Symptom**: Component shows `irt.drift.title` instead of "IRT Parameter Drift Monitoring"

**Solution**:
```typescript
// Check i18n configuration
import irtEn from '../../../shared/frontend/irt/locales/en.json';

i18n.init({
  resources: {
    en: {
      irt: irtEn  // ← Make sure this is loaded
    }
  }
});

// Verify translation function
const { t } = useTranslation('irt');  // ← Specify namespace
console.log(t('drift.title'));  // Should print translation
```

---

### Issue 2: API Calls Fail (CORS)

**Symptom**: Browser console shows CORS error

**Solution**:

**Backend** (`portal_api/main.py`):
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://portal.dreamseedai.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

**Frontend** (Vite proxy, `vite.config.ts`):
```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
```

---

### Issue 3: PDF Download Fails

**Symptom**: Download button doesn't work, 404 error

**Solution**:
```typescript
// Check API endpoint exists
fetch('/api/irt/report/monthly/12', {
  headers: { 'Authorization': `Bearer ${token}` }
})
  .then(res => {
    if (!res.ok) {
      console.error('API error:', res.status);
    }
    return res.blob();
  });

// Verify token is valid
const token = localStorage.getItem('token');
if (!token) {
  console.error('No auth token found');
}
```

---

### Issue 4: Component Doesn't Render

**Symptom**: Blank page, no errors

**Solution**:
```typescript
// Check required props
<MonthlyDriftReport
  apiBaseUrl="/api/irt"  // ← Required
  t={t}                  // ← Required
/>

// Verify t function works
console.log(typeof t);  // Should be 'function'
console.log(t('irt.drift.title'));  // Should print string

// Check network requests
// Open browser DevTools → Network tab
// Look for requests to /api/irt/drift/summary
```

---

## 한글 가이드 (Korean Guide)

### 컴포넌트 사용법

**기본 사용**:
```typescript
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'react-i18next';

function DriftPage() {
  const { t } = useTranslation();
  
  return (
    <MonthlyDriftReport
      apiBaseUrl="https://api.dreamseedai.com/api/irt"
      t={t}
    />
  );
}
```

---

### Props 설명

| Prop | 필수 | 설명 |
|------|------|------|
| `apiBaseUrl` | ✅ | API 기본 URL |
| `t` | ✅ | 번역 함수 (i18next) |
| `CardComponent` | ❌ | 커스텀 카드 컴포넌트 |
| `ButtonComponent` | ❌ | 커스텀 버튼 컴포넌트 |
| `autoRefresh` | ❌ | 자동 새로고침 활성화 |
| `refreshInterval` | ❌ | 새로고침 주기 (밀리초) |

---

### Portal (Vite) 통합

**1. 라우트 추가**:
```typescript
// portal_front/src/App.tsx
import IrtDriftPage from './pages/admin/IrtDriftPage';

<Route path="/admin/irt/drift" element={<IrtDriftPage />} />
```

**2. 페이지 생성**:
```typescript
// portal_front/src/pages/admin/IrtDriftPage.tsx
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'react-i18next';

export default function IrtDriftPage() {
  const { t } = useTranslation();
  
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">
        IRT 파라미터 드리프트 모니터링
      </h1>
      
      <MonthlyDriftReport
        apiBaseUrl="/api/irt"
        t={t}
      />
    </div>
  );
}
```

---

### Next.js 통합

**1. 페이지 생성**:
```typescript
// apps/examinee-frontend/app/admin/irt-drift/page.tsx
'use client';

import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'next-i18next';

export default function IrtDriftPage() {
  const { t } = useTranslation('common');
  
  return (
    <MonthlyDriftReport
      apiBaseUrl={process.env.NEXT_PUBLIC_API_URL + '/api/irt'}
      t={t}
    />
  );
}
```

**2. 환경 변수** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=https://api.dreamseedai.com
```

---

### i18n 설정

**Vite 프로젝트**:
```typescript
// portal_front/src/i18n/index.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import irtKo from '../../../shared/frontend/irt/locales/ko.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      ko: {
        irt: irtKo  // IRT 컴포넌트 번역 추가
      }
    },
    lng: 'ko',
    fallbackLng: 'en'
  });
```

---

### 문제 해결

**문제**: 번역이 안 됨 (`irt.drift.title` 텍스트 그대로 표시)
- **해결**: i18n 설정에 IRT 번역 파일 추가
- **확인**: `console.log(t('irt.drift.title'))`

**문제**: API 호출 실패 (CORS 오류)
- **해결**: 백엔드에 CORS 미들웨어 추가
- **또는**: Vite proxy 설정 (`vite.config.ts`)

**문제**: PDF 다운로드 안 됨
- **확인**: 토큰이 있는지 (`localStorage.getItem('token')`)
- **확인**: API 엔드포인트가 존재하는지 (`/api/irt/report/monthly/{id}`)

---

### 다음 단계

1. **컴포넌트 테스트**: 로컬 환경에서 작동 확인
2. **스타일 커스터마이징**: Tailwind 클래스 추가
3. **실시간 업데이트**: `autoRefresh` prop 사용
4. **다른 프로젝트 통합**: University, Parent, School 앱

---

**작성자**: DreamSeed AI Team  
**최종 업데이트**: 2025-11-05  
**관련 문서**: 04_API_INTEGRATION_GUIDE.md, shared/frontend/irt/README.md
