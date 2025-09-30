import { useEffect, useState } from 'react';
import { listStripeEvents } from '../lib/billing';

export default function BillingEventsPage(){
  const [rows, setRows] = useState<any[]>([]);
  const [afterId, setAfterId] = useState<number|undefined>(undefined);

  const load = async (reset=false) => {
    const data = (await listStripeEvents({ limit: 20, after_id: reset ? undefined : afterId })) as any[];
    setRows(reset ? data : [...rows, ...data]);
    if (data && data.length) setAfterId(data[data.length - 1].id as number);
  };

  useEffect(()=>{ void load(true); },[]);

  return (
    <div className="p-4">
      <h2 className="font-semibold mb-2">Stripe Events</h2>
      <button className="border px-2 py-1 mb-3" onClick={()=>void load(false)}>Load more</button>
      <div className="space-y-2">
        {rows.map((r:any)=>(
          <div key={r.id} className="border rounded p-2 text-sm">
            <div className="font-medium">#{r.id} — {r.event_type} — {String(r.processed)}</div>
            <div className="opacity-70">evt={r.event_id} sub={r.subscription_id ?? '-'} cust={r.customer_id ?? '-'}</div>
            <div className="opacity-70">status={r.status ?? '-'} amount={r.amount_total ?? '-'} {r.currency ?? ''}</div>
            <div className="opacity-50">at: {r.received_at}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
