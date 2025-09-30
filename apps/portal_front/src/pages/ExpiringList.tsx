import { useEffect, useState } from "react";
import { api, getToken } from "../lib/api";

export default function ExpiringListPage(){
  const [rows, setRows] = useState<any[]>([]);
  const [days, setDays] = useState(3);
  const [limit, setLimit] = useState(200);
  const load = async () => {
    if (!getToken()) { setRows([]); return; }
    try {
      const r = await api(`/billing/stripe/expiring?days=${days}&limit=${limit}`);
      const items = (r as any)?.items as any[] | undefined;
      setRows(items || []);
    } catch (e: any) {
      // 403/404는 조용히 처리 (권한/미구현)
      if (String(e?.message || "").match(/\[(403|404)\]/)) {
        setRows([]);
      } else {
        throw e;
      }
    }
  };
  useEffect(()=>{ load(); },[]);
  return (
    <div className="p-4">
      <h2 className="font-semibold mb-2">Expiring Subscriptions</h2>
      <div className="flex gap-2 mb-3 items-end">
        <label className="text-sm">Days <input className="border p-1 w-16" type="number" value={days} onChange={e=>setDays(+e.target.value)} /></label>
        <label className="text-sm">Limit <input className="border p-1 w-20" type="number" value={limit} onChange={e=>setLimit(+e.target.value)} /></label>
        <button className="border px-2 py-1" onClick={load}>Reload</button>
      </div>
      <table className="w-full text-sm border">
        <thead className="bg-gray-50">
          <tr>
            <th className="border p-1">Email</th>
            <th className="border p-1">Status</th>
            <th className="border p-1">Days Left</th>
            <th className="border p-1">Period End (UTC)</th>
            <th className="border p-1">Subscription</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r:any)=> (
            <tr key={r.user_id}>
              <td className="border p-1">{r.email}</td>
              <td className="border p-1">{r.status ?? "-"}</td>
              <td className="border p-1">{r.days_left ?? "-"}</td>
              <td className="border p-1">{r.current_period_end ?? "-"}</td>
              <td className="border p-1">{r.subscription_id ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
