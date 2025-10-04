import React, { useEffect, useRef, useState } from 'react';
import { api, getToken } from '../lib/api';
import PersonalizedPlan from './PersonalizedPlan';

type PlanCard = { title: string; slug?: string; summary?: string };

// naive in-memory cache per session
const planCache = new Map<string, PlanCard[]>();

export default function ProfileSelect({ onResult, onRequireLogin, onCountryChange }: { onResult: (cards: PlanCard[]) => void; onRequireLogin?: () => void; onCountryChange?: (country: 'US'|'CA') => void }) {
  const [country, setCountry] = useState<'US'|'CA'>('US');
  const [grade, setGrade] = useState<string>('G11');
  const [goal, setGoal] = useState<string>('SAT 1500+');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [toast, setToast] = useState<string>('');
  const [showPersonalizedPlan, setShowPersonalizedPlan] = useState(false);
  const runRef = useRef(0);

  const submit = async () => {
    const myRun = ++runRef.current;
    setLoading(true); setMsg('');
    setToast('Fetching recommendations…');

    // Auth gate: if not logged in, don't call recommend; ask login first
    const at = getToken();
    if (!at) {
      if (myRun === runRef.current) { setLoading(false); setToast(''); setMsg(''); }
      onRequireLogin && onRequireLogin();
      return;
    }

    // If authenticated, show personalized plan instead of old recommendations
    if (myRun === runRef.current) {
      setLoading(false);
      setToast('');
      setShowPersonalizedPlan(true);
      return;
    }

    try {
      const key = `${country}|${grade}|${goal}`;
      if (planCache.has(key)) { if (myRun === runRef.current) { onResult(planCache.get(key) || []); setToast(''); } return; }

      // Primary: GET /api/recommend (슬래시 없음)
      try {
        const r1 = await api<any>('recommend', { cache: 'no-store' });
        const arr = Array.isArray(r1) ? r1 : (r1?.items || r1?.results || r1?.cards || []);
        const mapped: PlanCard[] = (arr || []).slice(0, 8).map((it: any) => ({
          title: String(it?.title || it?.name || it?.label || 'Recommendation'),
          slug: it?.slug || it?.path || it?.url || '#',
          summary: it?.summary || it?.desc || it?.description || '',
        }));
        if (mapped.length > 0) {
          planCache.set(key, mapped);
          if (myRun === runRef.current) { onResult(mapped); setToast(''); }
          return;
        }
        throw Object.assign(new Error('[204] No Content'), { status: 204 });
      } catch (err: any) {
        const st = Number(err?.status ?? 0);
        if (st === 401 || st === 403) { onRequireLogin && onRequireLogin(); return; }
        if (st === 405) { if (myRun === runRef.current) { setMsg('Method not allowed (405).'); setToast(''); } return; }
        try {
          const qs = new URLSearchParams({ country, grade, goal });
          const r2 = await api<{ items?: PlanCard[] }>(`recommend/plan?${qs.toString()}`, { cache: 'no-store' });
          const items = r2.items || [];
          if (items.length > 0) planCache.set(key, items);
          if (myRun === runRef.current) { onResult(items); setToast(''); }
        } catch {
          if (myRun === runRef.current) { setToast(''); setMsg('Recommendations are temporarily unavailable. Please try again.'); onResult([]); }
        }
      }
    } finally {
      if (myRun === runRef.current) setLoading(false);
    }
  };

  useEffect(() => {
    const handler = () => { if (!loading) { void submit(); } };
    window.addEventListener('plan:retry', handler);
    return () => window.removeEventListener('plan:retry', handler);
  }, [loading]);

  const onCountryChanged = (val: 'US'|'CA') => { setCountry(val); onCountryChange && onCountryChange(val); };

  // If showing personalized plan, render that instead
  if (showPersonalizedPlan) {
    return <PersonalizedPlan />;
  }

  return (
    <div id="profile" className="border rounded p-3" style={{ maxWidth: 960, margin: '16px auto' }} aria-busy={loading}>
      <div className="flex gap-3 items-end" style={{ display: 'flex', gap: 12, alignItems: 'end', flexWrap: 'wrap' }}>
        <label>Country
          <select value={country} onChange={e=>onCountryChanged(e.target.value as any)} className="border p-1" style={{ marginLeft: 6 }} aria-label="Country">
            <option value="US">US</option>
            <option value="CA">CA</option>
          </select>
        </label>
        <label>Grade
          <select value={grade} onChange={e=>setGrade(e.target.value)} className="border p-1" style={{ marginLeft: 6 }} aria-label="Grade">
            {['G9','G10','G11','G12'].map(g => <option key={g} value={g}>{g}</option>)}
          </select>
        </label>
        <label>Goal
          <input value={goal} onChange={e=>setGoal(e.target.value)} className="border p-1" style={{ marginLeft: 6 }} aria-label="Goal" />
        </label>
        <button
          type="button"
          onClick={(e)=>{ e.preventDefault(); e.stopPropagation(); void submit(); }}
          disabled={loading}
          aria-label="View My Strategy"
          className="border px-4 py-2 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-600"
        >
          {loading ? 'Loading…' : 'View My Strategy'}
        </button>
        {msg && <span className="text-sm" style={{ color:'#dc2626' }}>{msg}</span>}
      </div>
      {toast && <div className="mt-2 text-sm text-slate-700 dark:text-slate-200">{toast}</div>}
    </div>
  );
}
