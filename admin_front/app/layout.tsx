'use client';

import { useEffect, useState } from 'react';
import './globals.css';
import { AppProviders } from './providers';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Load dark mode preference from localStorage
    const saved = localStorage.getItem('darkMode');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setDarkMode(saved === 'true' || (!saved && prefersDark));
  }, []);

  useEffect(() => {
    // Apply dark mode class to html element
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', String(darkMode));
  }, [darkMode]);

  return (
    <html lang="ko" className={darkMode ? 'dark' : ''}>
      <head>
        <title>DreamSeed Admin - CAT Dashboard</title>
        <meta name="description" content="DreamSeed 적응형 시험 대시보드" />
      </head>
      <body className="min-h-screen bg-slate-50 dark:bg-gray-900 text-slate-900 dark:text-gray-100 transition-colors">
        <AppProviders>
          {/* Dark mode toggle button */}
          <div className="fixed top-4 right-4 z-50">
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="rounded-lg bg-white dark:bg-gray-700 p-2 shadow-sm hover:shadow-md dark:hover:bg-gray-600 transition-all border border-slate-200 dark:border-gray-600"
              title={darkMode ? '라이트 모드로 전환' : '다크 모드로 전환'}
              aria-label="다크 모드 토글"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>
          
          <main className="flex-1 max-w-7xl mx-auto w-full py-6 px-4 sm:px-6 lg:px-8">
            {children}
          </main>
        </AppProviders>
      </body>
    </html>
  )
}
