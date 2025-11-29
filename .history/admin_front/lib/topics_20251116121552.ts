export type Topic = {
  id: number;
  name: string;
  org_id?: number | null;
  parent_topic_id?: number | null;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8002';
const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX || '/api/admin';
const API_URL = API_BASE_URL + API_PREFIX;

function toTopics(list: any): Topic[] {
  if (Array.isArray(list)) {
    if (list.length === 0) return [];
    if (typeof list[0] === 'string') {
      // Legacy: strings only
      return (list as string[]).map((name, i) => ({ id: i + 1, name }));
    }
    return (list as any[])
      .map((t) => ({ id: Number(t?.id), name: String(t?.name ?? ''), org_id: t?.org_id ?? null, parent_topic_id: t?.parent_topic_id ?? null }))
      .filter((t) => Number.isFinite(t.id) && !!t.name);
  }
  return [];
}

export async function getTopics(options?: { subject?: string; orgId?: number; includeGlobal?: boolean }): Promise<Topic[]> {
  const sp = new URLSearchParams();
  if (options?.subject) sp.set('subject', options.subject);
  if (options?.orgId != null) sp.set('org_id', String(options.orgId));
  if (options?.includeGlobal != null) sp.set('include_global', String(!!options.includeGlobal));
  // Prefer new endpoint
  try {
    const res = await fetch(`${API_URL}/topics${sp.toString() ? `?${sp.toString()}` : ''}`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      return toTopics(data);
    }
  } catch {}
  // Fallback legacy
  try {
    const res = await fetch(`${API_URL}/questions/topics`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      return toTopics(data);
    }
  } catch {}
  return [];
}

export async function invalidateTopicsCache(): Promise<{ deleted_keys: number }> {
  const res = await fetch(`${API_PREFIX}/topics/cache/invalidate`, { method: 'POST', cache: 'no-store' });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const body = await res.json(); msg = body?.detail || body?.message || msg; } catch {}
    throw new Error(msg);
  }
  const body = await res.json().catch(() => ({}));
  const n = Number(body?.deleted_keys ?? 0);
  return { deleted_keys: Number.isFinite(n) ? n : 0 };
}
