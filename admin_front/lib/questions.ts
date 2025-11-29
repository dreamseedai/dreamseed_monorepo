export type Question = {
  id: number;  // Changed from string to number (MySQL integer ID)
  title?: string;
  stem: string;
  explanation?: string;
  hint?: string; // optional rich text
  resource?: string; // optional rich text (references, links)
  answer_text?: string; // optional rich text (written answer)
  options: string[];
  answer: number; // index
  difficulty: 'easy' | 'medium' | 'hard';
  topic?: string;
  topic_id?: number | null;
  tags: string[];
  status: 'draft' | 'published' | 'deleted';
  author?: string;
  discrimination?: number;
  guessing?: number;
  created_at?: number | string;
  updated_at?: number | string;
};

export type QuestionInput = Omit<Question, 'id'>;

export type QuestionFilter = {
  q?: string;
  topic?: string;
  topic_id?: number | string;
  difficulty?: '' | 'easy' | 'medium' | 'hard';
  status?: '' | 'draft' | 'published' | 'deleted';
  page?: number;
  limit?: number;
  sortBy?: 'id' | 'updated_at' | 'created_at' | 'difficulty' | 'topic' | 'status';
  order?: 'asc' | 'desc';
};

// Use environment variable for API base URL
// Development: http://localhost:8002/api/admin
// Production: https://dreamseedai.com/api/admin
const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8002/api/admin';
const UPLOAD_MODE = process.env.NEXT_PUBLIC_UPLOAD_MODE || '';

console.log('[questions.ts] API_URL =', API_URL, '(from env:', process.env.NEXT_PUBLIC_API_BASE_URL, ')');

// Lightweight ETag store (per-session)
const _etagById = new Map<number, string>();

function _setEtag(id: number, etag: string | null) {
  if (!id) return;
  if (etag && etag.trim()) _etagById.set(Number(id), etag.trim());
}
function _getEtag(id: number): string | undefined {
  return _etagById.get(Number(id));
}
function _clearEtag(id: number) {
  _etagById.delete(Number(id));
}

function _randomId(prefix: string): string {
  try {
    // browser/edge runtimes
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const g: any = globalThis as any;
    if (g?.crypto?.randomUUID) return `${prefix}-${g.crypto.randomUUID()}`;
  } catch {}
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body?.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export async function listQuestions(filter: QuestionFilter & { cursor?: string }): Promise<{ results: Question[]; total: number; nextCursor?: string }> {
  const params = new URLSearchParams();
  if (filter.q) params.set('q', filter.q);
  // Prefer topic_id if provided; fallback to legacy topic name
  if (filter.topic_id != null && String(filter.topic_id)) params.set('topic_id', String(filter.topic_id));
  else if (filter.topic) params.set('topic', filter.topic);
  if (filter.difficulty) params.set('difficulty', filter.difficulty);
  if (filter.status) params.set('status', filter.status);
  params.set('page', String(filter.page ?? 1));
  // API expects page_size instead of limit
  params.set('page_size', String(filter.limit ?? 20));
  params.set('sort_by', String(filter.sortBy ?? 'updated_at'));
  params.set('order', String(filter.order ?? 'desc'));
  if (filter.cursor) params.set('cursor', filter.cursor);
  const raw = await http<{ 
    results?: Question[];
    questions?: Question[];  // New API format
    data?: Record<string, Question>; 
    total?: number;
    total_count?: number;  // New API format
    next_cursor_opaque?: string;
  }>(`${API_URL}/questions?${params.toString()}`);
  
  // Handle multiple response formats
  let results: Question[] = [];
  if (raw.results) {
    results = raw.results;
  } else if (raw.questions) {
    // New API format
    results = raw.questions;
  } else if (raw.data) {
    // Convert object to array
    results = Object.values(raw.data);
  }
  
  const total = raw.total ?? raw.total_count ?? 0;
  
  return { results, total, nextCursor: raw.next_cursor_opaque };
}

export async function getTopics(subject?: string): Promise<string[]> {
  // Prefer new endpoint /topics; fallback to legacy /questions/topics
  const mk = (list: any): string[] => {
    if (Array.isArray(list)) {
      if (list.length === 0) return [];
      if (typeof list[0] === 'string') return list as string[];
      return (list as any[]).map((t) => String(t?.name ?? t)).filter(Boolean);
    }
    return [];
  };
  try {
    const sp = new URLSearchParams();
    if (subject) sp.set('subject', subject);
    const res = await fetch(`${API_URL}/topics${sp.toString() ? `?${sp.toString()}` : ''}`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      return mk(data);
    }
  } catch {}
  // Fallback to legacy path
  try {
    const data = await http<any[]>(`${API_URL}/questions/topics`);
    return mk(data);
  } catch {
    return [];
  }
}

export async function getQuestion(id: number | string): Promise<Question | null> {
  try {
    const res = await fetch(`${API_URL}/questions/${id}`, { cache: 'no-store' });
    if (!res.ok) {
      if (res.status === 404) return null;
      let msg = `HTTP ${res.status}`;
      try {
        const b = await res.json();
        msg = b?.detail || msg;
      } catch {}
      throw new Error(msg);
    }
    _setEtag(Number(id), res.headers.get('etag'));
    return (await res.json()) as Question;
  } catch (e: any) {
    if (String(e?.message || '').includes('404')) return null;
    throw e;
  }
}

export async function getQuestionWithSource(id: number | string): Promise<{ question: Question | null; source?: string }> {
  const url = `${API_URL}/questions/${id}`;
  console.log('[getQuestionWithSource] API_URL =', API_URL);
  console.log('[getQuestionWithSource] url =', url);
  try {
    const res = await fetch(url, { cache: 'no-store' });
    console.log('[getQuestionWithSource] status =', res.status);
    if (!res.ok) {
      if (res.status === 404) return { question: null };
      let msg = `HTTP ${res.status}`;
      try {
        const b = await res.json();
        msg = b?.detail || msg;
      } catch {}
      throw new Error(msg);
    }
    const source = res.headers.get('x-data-source') || undefined;
    _setEtag(Number(id), res.headers.get('etag'));
    const q = (await res.json()) as Question;
    console.log('[getQuestionWithSource] question =', q);
    return { question: q, source };
  } catch (e: any) {
    console.error('[getQuestionWithSource] fetch error =', e);
    if (String(e?.message || '').includes('404')) return { question: null };
    throw e;
  }
}

export async function createQuestion(input: QuestionInput): Promise<Question> {
  const idem = _randomId('q-create');
  const res = await fetch(`${API_URL}/questions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': idem,
    },
    body: JSON.stringify(input),
    cache: 'no-store',
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body?.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  const q = (await res.json()) as Question;
  const etag = res.headers.get('etag');
  if (q?.id && etag) _setEtag(Number(q.id), etag);
  return q;
}

export async function updateQuestion(id: number | string, input: QuestionInput): Promise<Question | null> {
  try {
    const idem = _randomId('q-update');
    const etag = _getEtag(Number(id));
    const res = await fetch(`${API_URL}/questions/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': idem,
        ...(etag ? { 'If-Match': etag } : {}),
      },
      body: JSON.stringify(input),
      cache: 'no-store',
    });
    if (!res.ok) {
      if (res.status === 404) return null;
      let msg = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        msg = body?.detail || msg;
      } catch {}
      throw new Error(msg);
    }
    _setEtag(Number(id), res.headers.get('etag'));
    return (await res.json()) as Question;
  } catch (e: any) {
    if (String(e?.message || '').includes('404')) return null;
    throw e;
  }
}

export type DeleteResult = { ok: boolean; warning?: string };

export async function deleteQuestion(id: number | string): Promise<DeleteResult> {
  // Accept either legacy { ok: boolean } or new { message: string, warning?: string } shapes
  const idem = _randomId('q-delete');
  const etag = _getEtag(Number(id));
  const res = await fetch(`${API_URL}/questions/${id}`, {
    method: 'DELETE',
    headers: {
      ...(etag ? { 'If-Match': etag } : {}),
      'Idempotency-Key': idem,
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body?.detail || body?.message || msg;
    } catch {}
    throw new Error(msg);
  }
  // Try header-based warning first
  const headerWarning = res.headers.get('x-warning') || res.headers.get('warning') || undefined;
  try {
    const body: any = await res.json();
    if (typeof body?.ok === 'boolean') return { ok: !!body.ok, warning: body?.warning || headerWarning };
    if (typeof body?.message === 'string') return { ok: true, warning: body?.warning || headerWarning };
  } catch {
    // Some servers might return 204 No Content in the future; treat success as true
    _clearEtag(Number(id));
    return { ok: true, warning: headerWarning };
  }
  _clearEtag(Number(id));
  return { ok: true, warning: headerWarning };
}

export async function uploadImage(file: File): Promise<{ url: string; filename: string; content_type: string; size: number }> {
  // Optional presigned upload path (S3)
  if (UPLOAD_MODE.toLowerCase() === 'presigned') {
    try {
      const presignRes = await fetch(`${API_URL}/uploads/images/presign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, content_type: file.type || 'application/octet-stream' }),
      });
      if (presignRes.ok) {
        const presigned = await presignRes.json();
        const { url, fields, public_url } = presigned;
        const form = new FormData();
        Object.entries(fields || {}).forEach(([k, v]) => form.append(k, String(v)));
        form.append('file', file);
        const s3Res = await fetch(url, { method: 'POST', body: form });
        if (!s3Res.ok) {
          throw new Error(`S3 upload failed ${s3Res.status}`);
        }
        // Return a shape compatible with previous caller expectations
        return { url: public_url, filename: file.name, content_type: file.type || 'application/octet-stream', size: file.size };
      }
      // If presign endpoint returns an error, fall through to backend upload
    } catch (e) {
      // Fall back
    }
  }

  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_URL}/uploads/images`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body?.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}
