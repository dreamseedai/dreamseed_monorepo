import React, { useEffect, useState } from 'react';
import UserStatus from './UserStatus';
import LanguageSelector from './LanguageSelector';
import { useLanguage } from '../contexts/LanguageContext';

export default function Header() {
  const [dark, setDark] = useState(false);
  const { t } = useLanguage();

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
            <a href="/" className="text-slate-600 dark:text-slate-300 no-underline">{t('nav.home')}</a>
            <a href="/guides/us" className="text-slate-600 dark:text-slate-300 no-underline">{t('nav.guides')}</a>
            <a href="/guides/ca" className="text-slate-600 dark:text-slate-300 no-underline">{t('nav.guides')}</a>
            <a href="/pricing" className="text-slate-600 dark:text-slate-300 no-underline">{t('nav.plans')}</a>
            <a href="/saved" className="text-slate-600 dark:text-slate-300 no-underline">{t('nav.saved')}</a>
            <a href="/content/list" className="text-slate-600 dark:text-slate-300 no-underline">{t('nav.content')}</a>
          </nav>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <LanguageSelector />
          <button aria-label="Toggle dark mode" onClick={() => setDark(v=>!v)} className="border px-2 py-1 rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-600">
            {dark ? 'Light' : 'Dark'}
          </button>
          <a href="/login" className="border px-2 py-1 rounded-md text-sm no-underline">{t('nav.login')}</a>
          <UserStatus />
        </div>
      </div>
    </div>
  );
}
