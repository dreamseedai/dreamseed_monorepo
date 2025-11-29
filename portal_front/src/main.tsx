// Note: We previously installed a global fetch() normalizer here.
// It caused unexpected API rewrites and noisy console errors in some environments.
// The app now relies on src/lib/api.ts for safe API path handling.
// If you need the old behavior, consider re-adding it behind a feature flag.

import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import { installCopyButtonAuto } from './lib/injectCopyButton';
import { ToastProvider } from './components/Toast';

// Ensure app settings: language fixed to English, country limited to US/CA
try {
  const PREFS_PREFIX = 'ds:prefs:';
  const existingKey = Object.keys(localStorage).find((k) => k.startsWith(PREFS_PREFIX));
  const key = existingKey || `${PREFS_PREFIX}default`;
  const raw = existingKey ? localStorage.getItem(existingKey || '') : null;
  let prefs: { language?: string; country?: string } = {};
  try { prefs = raw ? JSON.parse(raw) : {}; } catch {}
  const language = 'en';
  const country = (prefs.country === 'US' || prefs.country === 'CA') ? prefs.country : 'US';
  const next = JSON.stringify({ language, country });
  localStorage.setItem(key, next);
} catch {}

const container = document.getElementById('root');
if (!container) throw new Error('Root container not found');

createRoot(container).render(
  <React.StrictMode>
    <ToastProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ToastProvider>
  </React.StrictMode>
);

// register service worker
// Ensure any previously registered service workers are unregistered to avoid stale caches during design rollout
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then((regs) => {
    regs.forEach((r) => r.unregister());
  }).catch(() => {});
}

// Install global observer that adds a Copy button next to Retry/Restore/Helpful/Unhelpful controls
try { installCopyButtonAuto(); } catch {}


