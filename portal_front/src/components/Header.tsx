import React, { useEffect, useState } from 'react';
import UserStatus from './UserStatus';

export default function Header() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const html = document.documentElement;
    if (dark) html.classList.add('dark'); else html.classList.remove('dark');
  }, [dark]);
  return (
    <div style={{ position: 'sticky', top: 0, zIndex: 10 }} className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <a href="/" className="no-underline font-bold text-slate-900 dark:text-slate-100">DreamSeedAI</a>
          <nav role="navigation" aria-label="Primary" className="hidden sm:flex gap-3 text-sm">
            <a href="/" className="text-slate-600 dark:text-slate-300 no-underline">Home</a>
            <a href="/guides/us" className="text-slate-600 dark:text-slate-300 no-underline">US Guides</a>
            <a href="/guides/ca" className="text-slate-600 dark:text-slate-300 no-underline">CA Guides</a>
            <a href="/content/list" className="text-slate-600 dark:text-slate-300 no-underline">Content</a>
          </nav>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button aria-label="Toggle dark mode" onClick={() => setDark(v=>!v)} className="border px-2 py-1 rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-600">
            {dark ? 'Light' : 'Dark'}
          </button>
          <a href="/login" className="border px-2 py-1 rounded-md text-sm no-underline">Login</a>
          <UserStatus />
        </div>
      </div>
    </div>
  );
}


