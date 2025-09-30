import { useEffect, useState } from "react";
import { api, getToken } from "../lib/api";

type ExpiringItem = {
  user_id: number;
  email: string;
  status?: string;
  current_period_end?: string;
  days_left?: number;
  subscription_id?: string;
  customer_id?: string;
};

export default function ExpiringCard() {
  const [items, setItems] = useState<ExpiringItem[]>([]);
  const [error, setError] = useState<string>("");
  const [hidden, setHidden] = useState<boolean>(false);

  const load = async () => {
    try {
      if (!getToken()) {
        setItems([]);
        setError("");
        return;
      }
      const r = await api(`/billing/stripe/expiring?days=3&limit=10`);
      const items = (r as any)?.items as ExpiringItem[] | undefined;
      setItems(items || []);
      setError("");
    } catch (e: any) {
      if (String(e?.message || "").includes("[403]")) {
        setHidden(true);
        setError("");
      } else if (String(e?.message || "").includes("[404]")) {
        setHidden(true);
        setError("");
      } else {
        setError(e.message || "error");
      }
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (hidden) return null;
  return (
    <div className="border rounded p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">Expiring in 3 days</h3>
        <button className="border px-2 py-1 text-sm" onClick={load}>Refresh</button>
      </div>
      {error && <div className="text-red-600 text-sm">{error}</div>}
      {items.length === 0 ? (
        <div className="text-sm text-gray-500">No upcoming expirations.</div>
      ) : (
        <ul className="space-y-1 text-sm">
          {items.map((it) => (
            <li key={it.user_id} className="flex justify-between">
              <span>{it.email}</span>
              <span>{it.status ?? "-"} · {it.days_left ?? "?"}d</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}


