import { useEffect, useState } from 'react';
import { getBillingStatus } from '../lib/billing';

export default function SuccessPage(){
  const [status, setStatus] = useState<null | boolean>(null);
  useEffect(()=>{ getBillingStatus().then(r=>setStatus(!!(r as any)?.subscribed)).catch(()=>setStatus(false)); },[]);
  return (
    <div className="p-6">
      <h2 className="text-xl font-bold">Payment Success</h2>
      <p className="mt-2">Session: {new URLSearchParams(location.search).get('session_id')}</p>
      <p className="mt-2">Subscribed: {status===null ? '...' : String(status)}</p>
    </div>
  );
}


