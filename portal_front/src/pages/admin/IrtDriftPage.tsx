// Portal project usage example
import { MonthlyDriftReport } from '@/shared/frontend/irt';
import { useTranslation } from 'react-i18next';

export default function IrtDriftPage() {
  const { t } = useTranslation();
  
  return (
    <div className="container mx-auto">
      <MonthlyDriftReport
        apiBaseUrl={import.meta.env.VITE_API_URL || 'http://localhost:8000'}
        t={t}
      />
    </div>
  );
}
