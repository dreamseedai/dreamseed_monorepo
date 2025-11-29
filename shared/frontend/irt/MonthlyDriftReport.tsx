import React, { useEffect, useState } from 'react';

type WindowSummary = {
  window_id: number;
  label: string;
  start_at: string;
  end_at: string;
  n_items: number;
  n_alerts: number;
  alerts_by_metric: Record<string, number>;
};

type DriftAlert = {
  item_id: number;
  window_id: number;
  metric: string;
  value: number;
  threshold: number;
  severity: 'low' | 'medium' | 'high';
  message: string;
  created_at: string;
};

interface MonthlyDriftReportProps {
  /** API base URL (e.g., import.meta.env.VITE_API_URL or process.env.NEXT_PUBLIC_API_URL) */
  apiBaseUrl: string;
  /** Translation function (key: string) => string. For labels and column headers. */
  t?: (key: string) => string;
  /** Optional Card component for layout. If not provided, uses plain div. */
  CardComponent?: React.ComponentType<{ children: React.ReactNode; className?: string }>;
  /** Optional Button component. If not provided, uses plain button. */
  ButtonComponent?: React.ComponentType<{
    children: React.ReactNode;
    onClick?: () => void;
    variant?: string;
    className?: string;
  }>;
}

const defaultT = (key: string) => {
  const translations: Record<string, string> = {
    'irt.drift.title': 'Monthly IRT Drift',
    'irt.drift.alerts_for_window': 'Alerts for window',
    'irt.drift.download_pdf': 'Download PDF',
    'irt.drift.loading': 'Loading...',
    'irt.drift.no_alerts': 'No alerts.',
    'irt.drift.col.item': 'Item',
    'irt.drift.col.metric': 'Metric',
    'irt.drift.col.value': 'Value',
    'irt.drift.col.threshold': 'Threshold',
    'irt.drift.col.severity': 'Severity',
    'irt.drift.col.message': 'Message',
    'irt.drift.col.created': 'Created',
  };
  return translations[key] || key;
};

export default function MonthlyDriftReport({
  apiBaseUrl,
  t = defaultT,
  CardComponent,
  ButtonComponent,
}: MonthlyDriftReportProps) {
  const [wins, setWins] = useState<WindowSummary[]>([]);
  const [selected, setSelected] = useState<number | undefined>();
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [loading, setLoading] = useState(false);

  const Card = CardComponent || (({ children, className }: any) => (
    <div className={className}>{children}</div>
  ));

  const Button = ButtonComponent || (({ children, onClick, variant, className }: any) => (
    <button onClick={onClick} className={className} data-variant={variant}>
      {children}
    </button>
  ));

  useEffect(() => {
    fetch(`${apiBaseUrl}/api/analytics/irt/drift/summary`)
      .then(r => r.json())
      .then(setWins)
      .catch(err => console.error('Failed to fetch drift summary:', err));
  }, [apiBaseUrl]);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    fetch(`${apiBaseUrl}/api/analytics/irt/drift/alerts/${selected}`)
      .then(r => r.json())
      .then(setAlerts)
      .catch(err => console.error('Failed to fetch alerts:', err))
      .finally(() => setLoading(false));
  }, [selected, apiBaseUrl]);

  const downloadPDF = () => {
    if (!selected) return;
    const url = `${apiBaseUrl}/api/analytics/irt/report/monthly?window_id=${selected}`;
    window.open(url, '_blank');
  };

  return (
    <div className="irt-drift-report p-6 grid gap-4">
      <Card className="p-4">
        <h2 className="text-xl font-semibold mb-2">{t('irt.drift.title')}</h2>
        <div className="flex gap-2 flex-wrap">
          {wins.map(w => (
            <Button
              key={w.window_id}
              variant={w.window_id === selected ? 'default' : 'secondary'}
              onClick={() => setSelected(w.window_id)}
              className="irt-drift-window-btn"
            >
              {w.label} ({w.n_alerts})
            </Button>
          ))}
        </div>
      </Card>

      {selected && (
        <Card className="p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">
              {t('irt.drift.alerts_for_window')} #{selected}
            </h3>
            <Button onClick={downloadPDF} className="irt-drift-download-btn">
              {t('irt.drift.download_pdf')}
            </Button>
          </div>
          {loading ? (
            <div className="py-10 text-center">{t('irt.drift.loading')}</div>
          ) : (
            <div className="mt-4 overflow-auto">
              <table className="min-w-full text-sm border-collapse">
                <thead>
                  <tr className="text-left border-b">
                    <th className="p-2">{t('irt.drift.col.item')}</th>
                    <th className="p-2">{t('irt.drift.col.metric')}</th>
                    <th className="p-2">{t('irt.drift.col.value')}</th>
                    <th className="p-2">{t('irt.drift.col.threshold')}</th>
                    <th className="p-2">{t('irt.drift.col.severity')}</th>
                    <th className="p-2">{t('irt.drift.col.message')}</th>
                    <th className="p-2">{t('irt.drift.col.created')}</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map(a => (
                    <tr
                      key={`${a.item_id}-${a.metric}-${a.created_at}`}
                      className="border-b"
                    >
                      <td className="p-2">{a.item_id}</td>
                      <td className="p-2">{a.metric}</td>
                      <td className="p-2">{a.value?.toFixed(3)}</td>
                      <td className="p-2">{a.threshold}</td>
                      <td className="p-2 capitalize">{a.severity}</td>
                      <td className="p-2">{a.message}</td>
                      <td className="p-2">{new Date(a.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {alerts.length === 0 && (
                <div className="py-6 text-center">{t('irt.drift.no_alerts')}</div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
