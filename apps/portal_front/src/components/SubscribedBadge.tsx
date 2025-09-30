import { useEffect, useState } from 'react';
import { getBillingStatus } from '../lib/billing';
import { manageSubscription } from '../lib/pay';

export default function SubscribedBadge(){
  const [sub, setSub] = useState<boolean | null>(null);
  const load = async ()=>{
    try { const r = await getBillingStatus(); setSub(!!(r as any)?.subscribed); }
    catch { setSub(null); }
  };
  useEffect(()=>{ void load(); const t = setInterval(()=>void load(), 60000); return ()=>clearInterval(t); },[]);
  const label = sub === null ? '…' : sub ? 'Subscribed ✅' : 'Free ❌';
  return (
    <div className="flex items-center gap-2">
      <span className={`px-2 py-1 rounded text-sm ${sub? 'bg-green-100 text-green-700':'bg-gray-100 text-gray-600'}`}>{label}</span>
      <button className="border px-2 py-1 rounded text-sm" onClick={manageSubscription}>Manage Subscription</button>
    </div>
  );
}
