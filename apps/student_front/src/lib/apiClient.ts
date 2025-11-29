/**
 * Common API client for DreamSeed Auth Frontend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE_URL) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  includeAuth: boolean = false
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  // Merge existing headers from options
  if (options.headers) {
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => {
        headers[key] = value;
      });
    } else if (Array.isArray(options.headers)) {
      options.headers.forEach(([key, value]) => {
        headers[key] = value;
      });
    } else {
      const headerObj = options.headers as Record<string, string>;
      Object.entries(headerObj).forEach(([key, value]) => {
        headers[key] = value;
      });
    }
  }

  if (includeAuth) {
    const token =
      typeof window !== "undefined"
        ? window.localStorage.getItem("access_token")
        : null;
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      if (typeof data === "object" && data !== null && "detail" in data) {
        const d = (data as { detail?: string }).detail;
        detail = d ?? JSON.stringify(data);
      } else {
        detail = JSON.stringify(data);
      }
    } catch {
      detail = res.statusText;
    }
    throw new Error(`API error: ${res.status} ${detail}`);
  }

  return res.json() as Promise<T>;
}
