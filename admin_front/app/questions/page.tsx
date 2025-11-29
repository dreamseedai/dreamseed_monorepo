import QuestionsClient, { InitialQuestionsPayload } from './QuestionsClient';
import { listQuestions, QuestionFilter } from '../../lib/questions';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

function parseInitialFilter(searchParams: Record<string, string | string[] | undefined>): QuestionFilter {
  const qp = (k: string) => {
    const v = searchParams?.[k];
    if (Array.isArray(v)) return v[0] ?? '';
    return v ?? '';
  };
  const num = (k: string, d: number) => {
    const v = qp(k);
    if (!v) return d;
    const n = Number(v);
    return Number.isFinite(n) && n > 0 ? n : d;
  };
  const desiredSort = (qp('sort_by') || qp('sortBy') || 'updated_at') as any;
  const normalizedSort = desiredSort;
  return {
    q: qp('q'),
    topic: qp('topic'),
    topic_id: (() => { const v = qp('topic_id'); return v ? Number(v) : undefined; })(),
    difficulty: (qp('difficulty') as any) || '',
    status: (qp('status') as any) || '',
    page: num('page', 1),
    limit: (() => { const ps = qp('page_size'); return ps && Number(ps) > 0 ? Number(ps) : num('limit', 50); })(),
    sortBy: normalizedSort,
    order: (qp('order') as any) || 'desc',
  };
}

export default async function QuestionsPage({ searchParams }: { searchParams: Record<string, string | string[] | undefined> }) {
  const filter = parseInitialFilter(searchParams);
  const params = new URLSearchParams();
  if (filter.q) params.set('q', filter.q);
  if (filter.topic_id != null && String(filter.topic_id)) params.set('topic_id', String(filter.topic_id));
  else if (filter.topic) params.set('topic', filter.topic);
  params.set('page', String(filter.page ?? 1));
  params.set('page_size', String(filter.limit ?? 20));
  params.set('sort_by', String(filter.sortBy ?? 'updated_at'));
  params.set('order', String(filter.order ?? 'desc'));

  let initial: InitialQuestionsPayload = { results: [], total: 0, filter };
  try {
    console.log('[QuestionsPage SSR] Fetching with filter:', filter);
    const data = await listQuestions({ ...filter });
    console.log('[QuestionsPage SSR] Got data:', { total: data.total, resultCount: data.results?.length });
    initial = { results: data.results || [], total: data.total || 0, nextCursor: data.nextCursor, filter };
  } catch (e) {
    console.error('[QuestionsPage SSR] Error:', e);
    // keep fallback empty results to maintain consistent SSR/CSR markup
  }

  return <QuestionsClient initial={initial} />;
}

