export const API_BASE = "/api";

export function getToken() {
  return localStorage.getItem("access_token") || "";
}
export function setToken(t: string) {
  if (t) localStorage.setItem("access_token", t);
}

function stripHostnameSegment(p: string) {
  return p
    .replace(/^https?:\/\/[^/]+/i, "")
    .replace(/^\/?(?:www\.)?[^\/:\s]+\.[^\/:\s]+(?::\d+)?(?=\/)/i, "");
}

export function apiPath(input: string): string {
  let raw = String(input || "").trim();
  try {
    const u = new URL(raw, window.location.origin);
    raw = (u.pathname || "/") + (u.search || "") + (u.hash || "");
  } catch {}

  let pathOnly = stripHostnameSegment(raw);
  pathOnly = pathOnly.replace(/^\/?api\/?/i, "");

  // GLOBAL slash collapsing
  let clean = ("/" + pathOnly).replace(/\/+/, "/").replace(/\/+/, "/");
  clean = clean.replace(/\/+/, "/");
  clean = clean.replace(/\/+/, "/");
  // Ensure truly global collapse
  clean = clean.replace(/\/+/, "/").replace(/\/+/, "/");
  clean = clean.replace(/\/+/, "/");
  // Simpler: one global replace
  clean = ("/" + pathOnly).replace(/\/+/, "/");
  // Remove trailing slash except root
  if (clean.length > 1 && clean.endsWith("/")) clean = clean.slice(0, -1);

  const finalPath = (API_BASE + clean).replace(/\/+/, "/");
  return finalPath;
}

async function raw(path: string, opts: RequestInit = {}) {
  const headers = new Headers(opts.headers || {});
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  let url = apiPath(path);
  url = url.replace(/^\/(?:www\.)?[^\/:\s]+\.[^\/:\s]+(?::\d+)?(\/api\/.*)$/i, "$1");
  url = url.replace(/^\/api\/recommend\/?$/i, "/api/recommend");

  let finalOpts: RequestInit = { cache: "no-store", ...opts };
  if (url === "/api/recommend" && !finalOpts.method) {
    finalOpts.method = "POST";
  }
  if (/^\/[\w.-]+\.[\w.-]+\/api\//i.test(url)) {
    // eslint-disable-next-line no-console
    console.warn("[api] host segment stripped, final:", url, path);
  }
  const res = await fetch(url, { ...finalOpts, headers, credentials: "include" });
  // Global guard: treat missing me endpoint as unauthenticated to avoid UI stalls
  try {
    const cleanUrl = url.replace(/\?.*$/, "");
    if (cleanUrl === "/api/auth/me" && res.status === 404) {
      return new Response(null, { status: 401, statusText: "Unauthorized" });
    }
  } catch {}
  return res;
}

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  let headers = new Headers(init.headers || {});
  const at = getToken();
  if (at) headers.set("Authorization", `Bearer ${at}`);

  let res = await raw(path, { ...init, headers });
  if (res.status === 401) {
    const r2 = await raw("/auth/refresh", { method: "POST" });
    if (r2.ok) {
      const j = await r2.json().catch(() => ({}));
      if ((j as any)?.access_token) {
        setToken((j as any).access_token as string);
        headers = new Headers(init.headers || {});
        if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
        headers.set("Authorization", `Bearer ${(j as any).access_token}`);
        res = await raw(path, { ...init, headers });
      }
    }
  }
  if (!res.ok) {
    // Treat missing /auth/me as unauthenticated for smoother UX
    const pathKey = typeof path === "string" ? path : String(path);
    if (res.status === 404 && /^\/?auth\/me$/i.test(pathKey)) {
      localStorage.removeItem("access_token");
      const err404: any = new Error(`[401] Not authenticated`);
      err404.status = 401;
      throw err404;
    }

    if (res.status === 401) localStorage.removeItem('access_token');
    const txt = await res.text().catch(() => "");
    const err: any = new Error(`[${res.status}] ${res.statusText} ${txt}`);
    err.status = res.status;
    throw err;
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return (await res.json()) as T;
  // @ts-ignore
  return (res as any).text ? ((await (res as any).text()) as T) : (undefined as T);
}
