// Global fetch guard: normalize any same-origin API calls (even Request instances)
(function installGlobalFetchGuard() {
  const ORIGIN = window.location.origin.replace(/\/+$/, "");
  const HOST_RE = /^(?:https?:\/\/)?(?:www\.)?[^\/:\s]+\.[^\/:\s]+(?::\d+)?/i;

  const normalize = (raw: string): string => {
    // absolute → pathname+search+hash
    try {
      const u = new URL(raw, ORIGIN);
      raw = (u.pathname || "/") + (u.search || "") + (u.hash || "");
    } catch {}
    // drop accidental '<host>/' prefix
    raw = raw.replace(/^\/?(?:www\.)?[^\/:\s]+\.[^\/:\s]+(?::\d+)?(?=\/)/i, "");
    // ensure single /api prefix; remove leading 'api' once; collapse slashes (global)
    raw = ("/" + raw).replace(/\/+/, "/").replace(/^\/?api\/?/i, "/").replace(/\/+/, "/");
    const candidate = ("/api" + raw).replace(/\/+/, "/");
    // canonicalize recommend to no trailing slash
    return /^\/api\/recommend\/?$/i.test(candidate) ? "/api/recommend" : candidate;
  };

  const orig = window.fetch;
  window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
    const sameOrigin = (url: string) =>
      url.startsWith("/") ||
      url.startsWith(ORIGIN) ||
      (!/^https?:\/\//i.test(url) && !url.startsWith("//"));

    // Case A: Request instance
    if (input instanceof Request) {
      const req = input as Request;
      const url = req.url;
      if (sameOrigin(url) && (/\/api\//i.test(url) || HOST_RE.test(url))) {
        const nurl = normalize(url);
        const rClone = req.clone();
        const method = (init?.method || rClone.method || "GET").toUpperCase();
        const headers = new Headers(rClone.headers);
        const finalInit: RequestInit = {
          method,
          headers,
          body: (init?.body ?? (method !== "GET" && method !== "HEAD" ? rClone.body : undefined)) as any,
          cache: "no-store",
          credentials: rClone.credentials,
          mode: rClone.mode,
          redirect: rClone.redirect,
          referrer: rClone.referrer,
          referrerPolicy: rClone.referrerPolicy,
          integrity: rClone.integrity,
          keepalive: rClone.keepalive,
          signal: init?.signal ?? rClone.signal,
        };
        // POST 메서드 자동 설정 제거
        return orig(new Request(nurl, finalInit));
      }
      return orig(input, init);
    }

    // Case B: string/URL
    const url = typeof input === "string" ? input : (input as URL).toString();
    if (sameOrigin(url) && (/\/api\//i.test(url) || HOST_RE.test(url))) {
      const nurl = normalize(url);
      const finalInit: RequestInit = { cache: "no-store", ...init };
      // POST 메서드 자동 설정 제거
      return orig(nurl, finalInit);
    }
    return orig(input as any, init);
  };
})();

import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { BrowserRouter } from 'react-router-dom';
import './index.css';

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
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);

// register service worker
// Ensure any previously registered service workers are unregistered to avoid stale caches during design rollout
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then((regs) => {
    regs.forEach((r) => r.unregister());
  }).catch(() => {});
}
