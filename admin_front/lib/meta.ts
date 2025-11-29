export type ApiMeta = {
  legacy_readonly_enabled?: boolean;
  legacy_source?: string | null;
};

// Use environment variable for API base URL
const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8002/api/admin';

export async function getApiMeta(): Promise<ApiMeta | null> {
  try {
    const res = await fetch(`${API_URL}/meta`, { cache: "no-store" });
    if (!res.ok) {
      return null;
    }
    const data = (await res.json()) as any;
    return {
      legacy_readonly_enabled: !!data?.legacy_readonly_enabled,
      legacy_source: (data?.legacy_source as string) ?? null,
    };
  } catch {
    return null;
  }
}
