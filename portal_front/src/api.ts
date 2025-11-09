import { resolveLanguage } from "./lib/langDetect";

export const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8012";

export function getToken() {
  return localStorage.getItem("access_token") || "";
}
export function setToken(t: string) {
  if (t) localStorage.setItem("access_token", t);
}

async function raw(path: string, opts: RequestInit = {}) {
  const headers = new Headers(opts.headers || {});
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  
  // 언어 헤더 추가 (X-Lang)
  if (!headers.has("X-Lang")) {
    const lang = resolveLanguage();
    headers.set("X-Lang", lang);
  }
  
  return fetch(`${API_BASE}${path}`, {
    ...opts,
    headers,
    credentials: "include",
  });
}

export async function api(path: string, opts: RequestInit = {}) {
  let headers = new Headers(opts.headers || {});
  const at = getToken();
  if (at) headers.set("Authorization", `Bearer ${at}`);

  let res = await raw(path, { ...opts, headers });
  if (res.status === 401) {
    const r2 = await raw("/auth/refresh", { method: "POST" });
    if (r2.ok) {
      const j = await r2.json().catch(() => ({}));
      if (j?.access_token) {
        setToken(j.access_token);
        headers = new Headers(opts.headers || {});
        if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
        headers.set("Authorization", `Bearer ${j.access_token}`);
        res = await raw(path, { ...opts, headers });
      }
    }
  }
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`[${res.status}] ${res.statusText} ${txt}`);
  }
  return res.json();
}

export async function getContent(id: number) {
  return api(`/content/${id}`);
}
export async function updateContent(id: number, body: any) {
  return api(`/content/${id}`, { method: "PUT", body: JSON.stringify(body) });
}
export async function deleteContent(id: number) {
  return api(`/content/${id}`, { method: "DELETE" });
}


