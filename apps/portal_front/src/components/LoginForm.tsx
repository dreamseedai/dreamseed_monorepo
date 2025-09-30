'use client';

import type React from "react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from 'react-router-dom';
import { api, getToken } from "../lib/api";

export default function LoginForm() {
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const formRef = useRef<HTMLFormElement | null>(null);
  const [diag, setDiag] = useState("");
  const [diagRunning, setDiagRunning] = useState(false);
  const [probePath, setProbePath] = useState("/api/version");
  const [debugAuth, setDebugAuth] = useState(false);

  useEffect(() => {
    try {
      const search = new URLSearchParams(window.location.search);
      setDebugAuth(search.get("debugauth") === "1");
      if (search.get("autologin") === "1") {
        // 기본 값으로 자동 제출
        setTimeout(() => {
          formRef.current?.requestSubmit();
        }, 0);
      }
    } catch {}
  }, []);

  const runDiagnostics = async () => {
    if (diagRunning) return;
    setDiagRunning(true);
    const lines: string[] = [];
    try {
      const token = getToken();
      lines.push(`[env] origin=${window.location.origin}`);
      lines.push(`[token] ${token ? `present len=${token.length}` : 'absent'}`);

      // __ok
      try {
        const r = await fetch("/api/__ok", { credentials: "include" });
        const ct = r.headers.get("content-type") || "";
        const t = await r.text().catch(() => "");
        lines.push(`[GET /api/__ok] ${r.status} ${r.statusText} ct=${ct}`);
        lines.push(t.slice(0, 200));
      } catch (e: any) {
        lines.push(`[GET /api/__ok] error: ${e?.message ?? e}`);
      }

      // version
      try {
        const r = await fetch("/api/version", { credentials: "include" });
        const ct = r.headers.get("content-type") || "";
        const t = await r.text().catch(() => "");
        lines.push(`[GET /api/version] ${r.status} ${r.statusText} ct=${ct}`);
        lines.push(t.slice(0, 200));
      } catch (e: any) {
        lines.push(`[GET /api/version] error: ${e?.message ?? e}`);
      }

      // me via wrapper (adds Authorization)
      try {
        const me = await api<any>("/auth/me");
        lines.push(`[api('/auth/me')] ok: ${JSON.stringify(me).slice(0, 200)}`);
      } catch (e: any) {
        lines.push(`[api('/auth/me')] error: ${e?.message ?? e}`);
      }
    } finally {
      setDiag(lines.join("\n"));
      setDiagRunning(false);
    }
  };

  const runProbe = async () => {
    setDiagRunning(true);
    const lines: string[] = [];
    try {
      const url = probePath || "/api/auth/me";
      const r = await fetch(url, { credentials: "include" });
      const ct = r.headers.get("content-type") || "";
      const t = await r.text().catch(() => "");
      lines.push(`[GET ${url}] ${r.status} ${r.statusText} ct=${ct}`);
      lines.push(t.slice(0, 500));
    } catch (e: any) {
      lines.push(`[GET ${probePath}] error: ${e?.message ?? e}`);
    } finally {
      setDiag((prev) => (prev ? prev + "\n\n" : "") + lines.join("\n"));
      setDiagRunning(false);
    }
  };

  const onSubmit: React.FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    setMsg("");
    setLoading(true);
    try {
      const log: string[] = [];
      const logPush = (s: string) => { log.push(s); setDiag(log.join("\n")); };
      logPush("[auth] start");
      const fd = new FormData(e.currentTarget);
      const email = String(fd.get("email") ?? "");
      const password = String(fd.get("password") ?? "");
      if (!email || !password) {
        setMsg("이메일/비밀번호를 입력하세요.");
        return;
      }

      const r = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      logPush(`[auth] POST /api/auth/login -> ${r.status} ${r.statusText}`);
      if (!r.ok) {
        setMsg(`[${r.status}] 로그인 실패`);
        logPush(`[auth] login failed`);
        return;
      }
      const j = await r.json();
      logPush(`[auth] login json keys: ${Object.keys(j || {}).join(',')}`);
      if (!j?.access_token) {
        setMsg("토큰 미수신");
        logPush(`[auth] no access_token`);
        return;
      }
      localStorage.setItem("access_token", j.access_token);
      logPush(`[auth] token stored (len=${String(j.access_token).length})`);

      // me 확인은 디버그 모드에서만 시도(시간 절약)
      if (debugAuth) {
        try {
          const me = await api<any>("/auth/me");
          logPush(`[auth] api('/auth/me') -> ok ${JSON.stringify(me).slice(0,200)}`);
        } catch (e: any) {
          logPush(`[auth] api('/auth/me') error: ${e?.message ?? e}`);
        }
      }

      try { window.dispatchEvent(new Event('auth:changed')); } catch {}
      setMsg("로그인 성공");
      const before = window.location.pathname;
      const sp = new URLSearchParams(window.location.search);
      const next = sp.get('next') || '/';
      if (debugAuth) { try { logPush(`[auth] navigate to ${next}`); } catch {} }
      setTimeout(() => { navigate(next); }, 0);
      // Fallback: 강제 이동 (라우터 미적용/캐시 이슈 대비)
      setTimeout(() => {
        if (window.location.pathname === before) {
          if (debugAuth) { try { logPush(`[auth] fallback hard redirect to ${next}`); } catch {} }
          window.location.assign(next);
        }
      }, 300);
      // 성공 후 이동이 필요하면 App Router 기준으로:
      // import { useRouter } from 'next/navigation'
      // const router = useRouter();
      // router.push('/');
      // 또는 window.location.href = '/';
    } catch (err: any) {
      setMsg(`에러: ${err?.message ?? err}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <form ref={formRef} onSubmit={onSubmit} className="flex gap-2 items-end">
      <div className="flex flex-col">
        <label>Email</label>
        <input
          name="email"
          type="email"
          autoComplete="username"
          defaultValue="you@example.com"
          className="border p-1"
        />
      </div>
      <div className="flex flex-col">
        <label>Password</label>
        <input
          name="password"
          type="password"
          autoComplete="current-password"
          defaultValue="Test1234!"
          className="border p-1"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              (e.currentTarget.form as HTMLFormElement)?.requestSubmit();
            }
          }}
        />
      </div>
      <button type="submit" disabled={loading} className="border px-2 py-1">
        {loading ? "로그인 중..." : "Login"}
      </button>
        <span className="text-sm ml-2">{msg}</span>
      </form>

      <div style={{ marginTop: 12, fontSize: 12 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
          <button type="button" onClick={runDiagnostics} disabled={diagRunning} className="border px-2 py-1">
            진단 실행
          </button>
          <input
            type="text"
            value={probePath}
            onChange={(e) => setProbePath(e.target.value)}
            placeholder="/api/... 경로 입력"
            className="border p-1"
            style={{ width: 280 }}
          />
          <button type="button" onClick={runProbe} disabled={diagRunning} className="border px-2 py-1">
            Probe
          </button>
        </div>
        {diag && (
          <pre style={{ background: '#0f172a', color: '#e2e8f0', padding: 8, borderRadius: 6, whiteSpace: 'pre-wrap' }}>{diag}</pre>
        )}
      </div>
    </>
  );
}
