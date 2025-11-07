import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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

const api = (path: string) => `${import.meta.env.VITE_API_URL}${path}`;

export default function MonthlyDriftReport() {
  const [wins, setWins] = useState<WindowSummary[]>([]);
  const [selected, setSelected] = useState<number | undefined>();
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(api('/api/analytics/irt/drift/summary'))
      .then(r => r.json())
      .then(setWins);
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    fetch(api(`/api/analytics/irt/drift/alerts/${selected}`))
      .then(r => r.json())
      .then(setAlerts)
      .finally(() => setLoading(false));
  }, [selected]);

  const downloadPDF = () => {
    if (!selected) return;
    const url = api(`/api/analytics/irt/report/monthly?window_id=${selected}`);
    window.open(url, '_blank');
  };

  return (
    <div className="p-6 grid gap-4">
      <Card className="p-4">
        <h2 className="text-xl font-semibold mb-2">Monthly IRT Drift</h2>
        <div className="flex gap-2 flex-wrap">
          {wins.map(w => (
            <Button
              key={w.window_id}
              variant={w.window_id === selected ? 'default' : 'secondary'}
              onClick={() => setSelected(w.window_id)}
            >
              {w.label} ({w.n_alerts})
            </Button>
          ))}
        </div>
      </Card>

      {selected && (
        <Card className="p-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Alerts for window #{selected}</h3>
            <Button onClick={downloadPDF}>Download PDF</Button>
          </div>
          {loading ? (
            <div className="py-10">Loading...</div>
          ) : (
            <div className="mt-4 overflow-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left border-b">
                    <th className="p-2">Item</th>
                    <th className="p-2">Metric</th>
                    <th className="p-2">Value</th>
                    <th className="p-2">Threshold</th>
                    <th className="p-2">Severity</th>
                    <th className="p-2">Message</th>
                    <th className="p-2">Created</th>
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
              {alerts.length === 0 && <div className="py-6">No alerts.</div>}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
