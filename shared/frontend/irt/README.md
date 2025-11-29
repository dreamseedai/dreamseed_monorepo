# Shared IRT Frontend Components

## MonthlyDriftReport

A reusable React component for displaying IRT drift monitoring across multiple projects (Portal, Univ, Parent, School).

### Usage

#### Portal (Vite + React)
```tsx
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'react-i18next';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function IrtDriftPage() {
  const { t } = useTranslation();
  
  return (
    <MonthlyDriftReport
      apiBaseUrl={import.meta.env.VITE_API_URL}
      t={t}
      CardComponent={Card}
      ButtonComponent={Button}
    />
  );
}
```

#### Univ/Parent/School (Next.js)
```tsx
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'next-i18next';

export default function IrtDriftPage() {
  const { t } = useTranslation('common');
  
  return (
    <MonthlyDriftReport
      apiBaseUrl={process.env.NEXT_PUBLIC_API_URL}
      t={t}
    />
  );
}
```

### Props

- **apiBaseUrl** (required): API base URL
  - Portal: `import.meta.env.VITE_API_URL`
  - Next.js: `process.env.NEXT_PUBLIC_API_URL`
  
- **t** (optional): Translation function `(key: string) => string`
  - If not provided, uses English defaults
  - i18n keys: `irt.drift.*` (title, alerts_for_window, download_pdf, loading, no_alerts, col.*)
  
- **CardComponent** (optional): Custom Card component
  - Falls back to plain `<div>` if not provided
  
- **ButtonComponent** (optional): Custom Button component
  - Falls back to plain `<button>` if not provided

### i18n Keys

```json
{
  "irt.drift.title": "Monthly IRT Drift",
  "irt.drift.alerts_for_window": "Alerts for window",
  "irt.drift.download_pdf": "Download PDF",
  "irt.drift.loading": "Loading...",
  "irt.drift.no_alerts": "No alerts.",
  "irt.drift.col.item": "Item",
  "irt.drift.col.metric": "Metric",
  "irt.drift.col.value": "Value",
  "irt.drift.col.threshold": "Threshold",
  "irt.drift.col.severity": "Severity",
  "irt.drift.col.message": "Message",
  "irt.drift.col.created": "Created"
}
```

### API Endpoints

- `GET /api/analytics/irt/drift/summary` - List calibration windows with alert counts
- `GET /api/analytics/irt/drift/alerts/{window_id}` - Get alerts for specific window
- `GET /api/analytics/irt/report/monthly?window_id={id}` - Download PDF report

### Styling

Uses Tailwind CSS classes. Override with custom CSS:

```css
.irt-drift-report { /* Main container */ }
.irt-drift-window-btn { /* Window selection buttons */ }
.irt-drift-download-btn { /* PDF download button */ }
```
