/**
 * IRT Drift Monitoring Dashboard
 * =================================
 * React component for viewing drift alerts, parameter trends, and item calibration history
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  ResponsiveContainer 
} from 'recharts';
import { AlertCircle, TrendingUp, TrendingDown, Activity } from 'lucide-react';

// Types
interface DriftAlert {
  id: number;
  item_id: number;
  item_id_str?: string;
  bank_id: string;
  window_id: number;
  window_label: string;
  metric: string;
  value?: number;
  threshold?: number;
  severity: 'low' | 'medium' | 'high';
  message?: string;
  created_at: string;
}

interface CalibrationHistory {
  window_label: string;
  start_at: string;
  a_hat?: number;
  b_hat: number;
  c_hat?: number;
  drift_flag?: string;
}

interface IRTStats {
  total_items: number;
  items_with_params: number;
  anchor_items: number;
  total_windows: number;
  active_alerts: {
    high: number;
    medium: number;
    low: number;
    total: number;
  };
}

// Severity badge component
const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const variants: Record<string, string> = {
    high: 'destructive',
    medium: 'warning',
    low: 'secondary',
  };
  
  return (
    <Badge variant={variants[severity] as any}>
      {severity.toUpperCase()}
    </Badge>
  );
};

// Main Dashboard Component
export const IrtDriftDashboard: React.FC = () => {
  const [stats, setStats] = useState<IRTStats | null>(null);
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [selectedItem, setSelectedItem] = useState<number | null>(null);
  const [itemHistory, setItemHistory] = useState<CalibrationHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch stats and alerts
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch stats
        const statsRes = await fetch('/api/v1/irt/stats/summary');
        const statsData = await statsRes.json();
        setStats(statsData);

        // Fetch active alerts
        const alertsRes = await fetch('/api/v1/irt/drift-alerts?active_only=true');
        const alertsData = await alertsRes.json();
        setAlerts(alertsData);
      } catch (error) {
        console.error('Failed to fetch IRT data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Fetch item history when item selected
  useEffect(() => {
    if (!selectedItem) return;

    const fetchHistory = async () => {
      try {
        const res = await fetch(`/api/v1/irt/items/${selectedItem}/history`);
        const data = await res.json();
        setItemHistory(data);
      } catch (error) {
        console.error('Failed to fetch item history:', error);
      }
    };

    fetchHistory();
  }, [selectedItem]);

  // Resolve alert
  const handleResolveAlert = async (alertId: number) => {
    try {
      await fetch(`/api/v1/irt/drift-alerts/${alertId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolved: true }),
      });
      
      // Remove from UI
      setAlerts(alerts.filter(a => a.id !== alertId));
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  if (loading) {
    return <div className="p-8">Loading IRT dashboard...</div>;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold mb-6">IRT Drift Monitoring</h1>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Items
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_items || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.items_with_params || 0} with parameters
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Anchor Items
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.anchor_items || 0}</div>
            <p className="text-xs text-muted-foreground">
              Stable reference items
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats?.active_alerts.total || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_alerts.high || 0} high severity
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Calibration Windows
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_windows || 0}</div>
            <p className="text-xs text-muted-foreground">
              Time periods analyzed
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="alerts">
            Drift Alerts
            {alerts.length > 0 && (
              <Badge variant="destructive" className="ml-2">
                {alerts.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="trends">Parameter Trends</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
            </CardHeader>
            <CardContent>
              {stats && stats.active_alerts.total === 0 ? (
                <Alert>
                  <Activity className="h-4 w-4" />
                  <AlertTitle>All systems operational</AlertTitle>
                  <AlertDescription>
                    No parameter drift detected. All items are stable.
                  </AlertDescription>
                </Alert>
              ) : (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Drift Detected</AlertTitle>
                  <AlertDescription>
                    {stats?.active_alerts.total} items require attention.
                    {stats && stats.active_alerts.high > 0 && (
                      <span className="font-semibold"> {stats.active_alerts.high} high severity.</span>
                    )}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Alerts Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {alerts.slice(0, 5).map(alert => (
                  <div key={alert.id} className="flex items-center justify-between p-2 border-b last:border-0">
                    <div className="flex-1">
                      <div className="font-medium">
                        Item {alert.item_id_str || alert.item_id} ({alert.bank_id})
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {alert.metric}: {alert.value?.toFixed(3) || 'N/A'}
                      </div>
                    </div>
                    <SeverityBadge severity={alert.severity} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Active Drift Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <p className="text-muted-foreground">No active alerts. ✓</p>
              ) : (
                <div className="space-y-4">
                  {alerts.map(alert => (
                    <div key={alert.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h4 className="font-semibold">
                            Item {alert.item_id_str || alert.item_id}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            Bank: {alert.bank_id} | Window: {alert.window_label}
                          </p>
                        </div>
                        <SeverityBadge severity={alert.severity} />
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 mb-2">
                        <div>
                          <span className="text-sm font-medium">Metric:</span>
                          <span className="ml-2">{alert.metric}</span>
                        </div>
                        <div>
                          <span className="text-sm font-medium">Value:</span>
                          <span className="ml-2">{alert.value?.toFixed(3) || 'N/A'}</span>
                        </div>
                      </div>
                      
                      {alert.message && (
                        <p className="text-sm text-muted-foreground mb-2">
                          {alert.message}
                        </p>
                      )}
                      
                      <div className="flex gap-2">
                        <button
                          onClick={() => setSelectedItem(alert.item_id)}
                          className="text-sm text-blue-600 hover:underline"
                        >
                          View History
                        </button>
                        <button
                          onClick={() => handleResolveAlert(alert.id)}
                          className="text-sm text-green-600 hover:underline"
                        >
                          Resolve
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Parameter Trends</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedItem && itemHistory.length > 0 ? (
                <div>
                  <h4 className="mb-4">Item {selectedItem} - Difficulty (b) Parameter</h4>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={itemHistory}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="window_label" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="b_hat" 
                        stroke="#3498db" 
                        strokeWidth={2}
                        name="Difficulty (b)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-muted-foreground">
                  Select an item from the Alerts tab to view parameter trends.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default IrtDriftDashboard;
