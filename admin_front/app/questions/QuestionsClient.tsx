'use client';

import Link from 'next/link';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Question, QuestionFilter, listQuestions, deleteQuestion, updateQuestion } from '../../lib/questions';
import { getApiMeta, ApiMeta } from '../../lib/meta';
import { Breadcrumbs } from '../../components/Breadcrumbs';
import { SearchBar } from '../../components/SearchBar';
import { ConfirmModal } from '../../components/ConfirmModal';
import { MathRenderer } from '../../components/MathRenderer';
import { route } from '../../lib/route';

export type InitialQuestionsPayload = {
  results: Question[];
  total: number;
  nextCursor?: string;
  filter: QuestionFilter;
};

export default function QuestionsClient({ initial }: { initial: InitialQuestionsPayload }) {
  const ID_SORT_MODE: 'native' | 'map-created_at' | 'hide' = (process.env.NEXT_PUBLIC_ID_SORT_MODE as any) || 'native';
  const effectiveIdField: 'id' | 'created_at' = ID_SORT_MODE === 'native' ? 'id' : 'created_at';
  
  console.log('[QuestionsClient] ID_SORT_MODE:', ID_SORT_MODE, 'effectiveIdField:', effectiveIdField);

  const [items, setItems] = useState<Question[]>(Array.isArray(initial?.results) ? initial.results : []);
  const [total, setTotal] = useState<number>(Number.isFinite(initial?.total as any) ? (initial.total as number) : 0);
  const [loading, setLoading] = useState(false);
  const [useKeyset, setUseKeyset] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | undefined>(initial?.nextCursor);
  const [undo, setUndo] = useState<{ id: number; prev: Question } | null>(null);
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const [meta, setMeta] = useState<ApiMeta | null>(null);
  const [filter, setFilter] = useState<QuestionFilter>(initial?.filter || { q: '', topic: '', topic_id: undefined, difficulty: '', status: '', page: 1, limit: 50, sortBy: 'updated_at', order: 'desc' });

  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [debouncedFilter, setDebouncedFilter] = useState(filter);
  useEffect(() => {
    const t = setTimeout(() => setDebouncedFilter(filter), 300);
    return () => clearTimeout(t);
  }, [filter]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const m = await getApiMeta();
        if (!cancelled) setMeta(m);
      } catch {}
    })();
    return () => { cancelled = true; };
  }, []);

  function parseFilterFromURL(sp: { get: (k: string) => string | null } | null): { f: QuestionFilter; keyset: boolean } {
    const fallback = { get: (_k: string) => null } as { get: (k: string) => string | null };
    const src = (sp ?? fallback);
    const qp = (k: string) => src.get(k) ?? '';
    const num = (k: string, d: number) => {
      const v = src.get(k); if (!v) return d; const n = Number(v); return Number.isFinite(n) && n > 0 ? n : d;
    };
    const desiredSort = ((qp('sort_by') || qp('sortBy')) as any) || 'updated_at';
    let normalizedSort: any = desiredSort;
    if (desiredSort === 'id') {
      if (ID_SORT_MODE === 'map-created_at') normalizedSort = 'created_at';
      else if (ID_SORT_MODE === 'hide') normalizedSort = 'updated_at';
    }
    const f: QuestionFilter = {
      q: qp('q'),
      topic: qp('topic'),
      topic_id: (() => { const v = qp('topic_id'); return v ? Number(v) : undefined; })(),
      difficulty: (qp('difficulty') as any) || '',
      status: (qp('status') as any) || '',
      page: num('page', 1),
      limit: (() => {
        const ps = src.get('page_size');
        if (ps && Number(ps) > 0) return Number(ps);
        return num('limit', 50);
      })(),
      sortBy: normalizedSort,
      order: (qp('order') as any) || 'desc',
    };
    const keyset = (src.get('useKeyset') ?? '') === '1';
    return { f, keyset };
  }

  function buildURLFromFilter(basePath: string | null, f: QuestionFilter, keyset: boolean): string {
    const base = basePath || '/questions';
    const sp = new URLSearchParams();
    if (f.q) sp.set('q', f.q);
    if (f.topic_id != null && String(f.topic_id)) sp.set('topic_id', String(f.topic_id));
    else if (f.topic) sp.set('topic', f.topic);
    if (f.difficulty) sp.set('difficulty', f.difficulty);
    if (f.status) sp.set('status', f.status);
  if (f.page && f.page !== 1) sp.set('page', String(f.page));
  if (f.limit && f.limit !== 50) sp.set('page_size', String(f.limit));
    if (f.sortBy && f.sortBy !== 'updated_at') sp.set('sort_by', f.sortBy);
    if (f.order && (f.sortBy && f.sortBy !== 'updated_at' || f.order !== 'desc')) sp.set('order', f.order);
    if (keyset) sp.set('useKeyset', '1');
    const qs = sp.toString();
    return qs ? `${base}?${qs}` : base;
  }

  function filtersEqual(a: QuestionFilter, b: QuestionFilter): boolean {
    return (
      (a.q || '') === (b.q || '') &&
      (a.topic || '') === (b.topic || '') &&
      String(a.topic_id || '') === String(b.topic_id || '') &&
      (a.difficulty || '') === (b.difficulty || '') &&
      (a.status || '') === (b.status || '') &&
      (a.page || 1) === (b.page || 1) &&
  (a.limit || 50) === (b.limit || 50) &&
      (a.sortBy || 'updated_at') === (b.sortBy || 'updated_at') &&
      (a.order || 'desc') === (b.order || 'desc')
    );
  }

  useEffect(() => {
    const { f: urlFilter, keyset } = parseFilterFromURL(searchParams as any);
    const same = filtersEqual(filter, urlFilter) && keyset === useKeyset;
    if (!same) {
      setFilter(urlFilter);
      setUseKeyset(keyset);
      setNextCursor(undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // state→URL sync 제거 (onClick에서 직접 router.replace 호출)
  // URL이 single source of truth이므로 불필요

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const { results, total, nextCursor: nextCur } = await listQuestions({ ...debouncedFilter });
        if (!cancelled) {
          setItems(results || []);
          setTotal(total || 0);
          setNextCursor(nextCur);
        }
      } catch (e) {
        console.error(e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [debouncedFilter, useKeyset]);

  useEffect(() => {
    try {
      if (undo) {
        const expiresAt = Date.now() + 5000;
        const payload = { id: undo.id, prev: undo.prev, expiresAt };
        sessionStorage.setItem('questions_undo', JSON.stringify(payload));
      } else {
        sessionStorage.removeItem('questions_undo');
      }
    } catch {}
  }, [undo]);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem('questions_undo');
      if (!raw) return;
      const data = JSON.parse(raw);
      if (data && data.expiresAt && Date.now() < data.expiresAt) {
        setUndo({ id: data.id, prev: data.prev });
        const delay = Math.max(0, data.expiresAt - Date.now());
        const t = setTimeout(() => setUndo(null), delay);
        return () => clearTimeout(t);
      } else {
        sessionStorage.removeItem('questions_undo');
      }
    } catch {}
  }, []);

  useEffect(() => {
    try {
      const spAny = (searchParams as any);
      const t = spAny?.get?.('toast') ?? null;
      if (t === 'deleted') {
        const warn = spAny?.get?.('warn') ?? null;
        const msg = warn ? '삭제되었습니다 (경고: 사용 이력이 있는 문항)' : '삭제되었습니다';
        setToast({ type: 'success', msg });
        window.setTimeout(() => setToast(null), 3000);
        const sp = new URLSearchParams(spAny ?? undefined);
        sp.delete('toast');
        sp.delete('warn');
        const next = `${pathname}?${sp.toString()}`.replace(/\?$/, '');
        try { router.replace(next as any); } catch {}
        try { if (typeof window !== 'undefined') window.history.replaceState(null, '', next); } catch {}
      }
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  function fmtUpdatedAt(q: Question, field: 'updated' | 'created' = 'updated'): string {
    const v = field === 'created' ? (q as any).created_at : (q.updated_at ?? q.created_at);
    if (!v && v !== 0) return '-';
    const ms = typeof v === 'string' ? Date.parse(v) : Math.round(Number(v) * 1000);
    if (!isFinite(ms)) return '-';
    try {
      const dt = new Date(ms);
      const Y = dt.getFullYear(), M = String(dt.getMonth()+1).padStart(2,'0'), D = String(dt.getDate()).padStart(2,'0');
      const h = String(dt.getHours()).padStart(2,'0'), m = String(dt.getMinutes()).padStart(2,'0');
      return `${Y}-${M}-${D} ${h}:${m}`;
    } catch { return new Date(ms).toISOString(); }
  }

  async function performDelete(id: string | number) {
    console.log('[DEBUG] performDelete called with id:', id);
    const numId = Number(id);
    const target = items.find(x => x.id === numId);
    if (!target) {
      console.log('[DEBUG] Target not found for id:', numId);
      return;
    }
    setDeleting(true);
    console.log('[DEBUG] Calling deleteQuestion API...');
    try {
      const result = await deleteQuestion(numId);
      console.log('[DEBUG] Delete result:', result);
      setUndo({ id: numId, prev: target });
      const { results, total, nextCursor } = await listQuestions({ ...debouncedFilter });
      setItems(results || []);
      setTotal(total || 0);
      setNextCursor(nextCursor);
      setToast({ type: 'success', msg: result.warning ? `삭제되었습니다 (경고: ${result.warning})` : '삭제되었습니다' });
      window.setTimeout(() => setToast(null), 3000);
      setTimeout(() => setUndo(null), 5000);
    } catch (e) {
      console.error('[DEBUG] Delete error:', e);
      setToast({ type: 'error', msg: '삭제 중 오류가 발생했습니다.' });
      window.setTimeout(() => setToast(null), 3000);
    } finally {
      setDeleting(false);
      setConfirmId(null);
    }
  }

  return (
    <section className="space-y-6 p-6 max-w-[1600px] mx-auto">
      <Breadcrumbs items={[{ label: '문항 목록' }]} />
      
      {meta?.legacy_readonly_enabled && (
        <div className="rounded-lg border border-yellow-300 dark:border-yellow-600 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-900 dark:text-yellow-200 px-4 py-3 text-sm shadow-sm">
          레거시 데이터 보기 모드가 활성화되어 있습니다. 목록/상세 조회는 "{meta.legacy_source}" 원본을 따릅니다. 편집/삭제 시 동기화 차이가 있을 수 있습니다.
        </div>
      )}
      
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent" data-testid="questions-heading">
            문항은행
          </h1>
          <span className="text-sm px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 font-semibold">
            {total.toLocaleString()}개
          </span>
        </div>
        <Link 
          href="/questions/new" 
          className="rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 px-5 py-2.5 text-white text-sm font-semibold shadow-lg hover:shadow-xl transition-all duration-200 flex items-center gap-2"
        >
          <span className="text-lg">➕</span>
          신규 문항 추가
        </Link>
      </div>

      <SearchBar
        value={filter}
        onChange={setFilter}
        searching={loading}
        onSubmit={() => {
          setDebouncedFilter(filter);
        }}
      />

      <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden shadow-lg bg-white dark:bg-gray-800">
        <table className="min-w-full text-sm">
          <thead className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-800 border-b border-gray-200 dark:border-gray-600">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-gray-200">
                {ID_SORT_MODE === 'hide' ? (
                  <span>ID</span>
                ) : (
                  <button
                    className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    onClick={() => {
                      // 다음 필터 상태 계산
                      const nextOrder: 'asc' | 'desc' = (filter.sortBy === effectiveIdField && filter.order === 'asc') ? 'desc' : 'asc';
                      const nextFilter: QuestionFilter = {
                        ...filter,
                        sortBy: effectiveIdField,
                        order: nextOrder,
                        page: 1,
                      };
                      // URL을 직접 업데이트 (URL이 source of truth)
                      const url = buildURLFromFilter(pathname, nextFilter, useKeyset);
                      router.replace(url, { scroll: false });
                      // useEffect([searchParams])가 자동으로 setFilter 처리
                    }}
                  >
                    ID{filter.sortBy === effectiveIdField ? (filter.order === 'desc' ? ' ▼' : ' ▲') : ''}
                  </button>
                )}
              </th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 dark:text-gray-200">Title</th>
              <th className="px-4 py-3 w-24 text-center font-semibold text-gray-700 dark:text-gray-200">Class</th>
              <th className="px-4 py-3 w-28 text-center font-semibold text-gray-700 dark:text-gray-200">Grade</th>
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">
                <button className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors" onClick={() => {
                  const nextOrder: 'asc' | 'desc' = filter.sortBy === 'difficulty' && filter.order === 'desc' ? 'asc' : 'desc';
                  const nextFilter: QuestionFilter = { ...filter, sortBy: 'difficulty', order: nextOrder, page: 1 };
                  router.replace(buildURLFromFilter(pathname, nextFilter, useKeyset), { scroll: false });
                }}>
                  난이도{filter.sortBy === 'difficulty' ? (filter.order === 'desc' ? ' ▼' : ' ▲') : ''}
                </button>
              </th>
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">
                <button
                  className="inline-flex items-center gap-1 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  onClick={() => {
                    const nextOrder: 'asc' | 'desc' = filter.order === 'desc' ? 'asc' : 'desc';
                    const nextFilter: QuestionFilter = { ...filter, sortBy: 'created_at', order: nextOrder, page: 1 };
                    router.replace(buildURLFromFilter(pathname, nextFilter, useKeyset), { scroll: false });
                  }}
                  title="생성일 정렬 토글"
                >
                  Created
                  <span className="text-xs">{filter.sortBy === 'created_at' ? (filter.order === 'desc' ? '▼' : '▲') : ''}</span>
                </button>
              </th>
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">
                <button
                  className="inline-flex items-center gap-1 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  onClick={() => {
                    const nextOrder: 'asc' | 'desc' = filter.order === 'desc' ? 'asc' : 'desc';
                    const nextFilter: QuestionFilter = { ...filter, sortBy: 'updated_at', order: nextOrder, page: 1 };
                    router.replace(buildURLFromFilter(pathname, nextFilter, useKeyset), { scroll: false });
                  }}
                  title="최근 수정일 정렬 토글"
                >
                  Modified
                  <span className="text-xs">{filter.sortBy === 'updated_at' ? (filter.order === 'desc' ? '▼' : '▲') : ''}</span>
                </button>
              </th>
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">
                <button className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors" onClick={() => {
                  const nextOrder: 'asc' | 'desc' = filter.sortBy === 'status' && filter.order === 'desc' ? 'asc' : 'desc';
                  const nextFilter: QuestionFilter = { ...filter, sortBy: 'status', order: nextOrder, page: 1 };
                  router.replace(buildURLFromFilter(pathname, nextFilter, useKeyset), { scroll: false });
                }}>
                  상태{filter.sortBy === 'status' ? (filter.order === 'desc' ? ' ▼' : ' ▲') : ''}
                </button>
              </th>
              <th className="px-4 py-3 text-center font-semibold text-gray-700 dark:text-gray-200">작업</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {items.map((q) => (
              <tr key={q.id} className="hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{q.id}</td>
                <td 
                  className="px-4 py-3 line-clamp-2 max-w-xl cursor-pointer group"
                  onDoubleClick={() => router.push(route(`/questions/${q.id}/edit`))}
                  title="더블클릭하여 편집"
                >
                  <div className="group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    <MathRenderer content={q.title || ''} />
                  </div>
                </td>
                <td className="px-4 py-3 text-center text-xs">
                  <span className="px-2 py-1 rounded bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 font-medium">
                    {(q as any).que_class || '-'}
                  </span>
                </td>
                <td className="px-4 py-3 text-center text-xs">
                  <span className="px-2 py-1 rounded bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-200 font-medium">
                    {(q as any).que_grade || '-'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={
                    `inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold shadow-sm ${
                      q.difficulty === 'easy' 
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200' 
                        : q.difficulty === 'medium' 
                        ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200' 
                        : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
                    }`
                  }>{q.difficulty}</span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600 dark:text-gray-400">{fmtUpdatedAt(q, 'created')}</td>
                <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-600 dark:text-gray-400">{fmtUpdatedAt(q)}</td>
                <td className="px-4 py-3">
                  <span className={
                    `inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${
                      q.status === 'published' 
                        ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200' 
                        : q.status === 'deleted' 
                        ? 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 line-through' 
                        : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
                    }`
                  }>{q.status || 'draft'}</span>
                </td>
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      console.log('[DEBUG] Delete button clicked for id:', q.id);
                      console.log('[DEBUG] meta?.legacy_readonly_enabled:', meta?.legacy_readonly_enabled);
                      if (!meta?.legacy_readonly_enabled) {
                        setConfirmId(q.id);
                        console.log('[DEBUG] confirmId set to:', q.id);
                      }
                    }}
                    className={`${
                      meta?.legacy_readonly_enabled 
                        ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed' 
                        : 'text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 hover:underline cursor-pointer'
                    } font-medium text-sm transition-colors`}
                    title={meta?.legacy_readonly_enabled ? '레거시 모드에서는 삭제할 수 없습니다.' : '삭제'}
                    disabled={!!meta?.legacy_readonly_enabled}
                  >삭제</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Range summary */}
      <div className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
        <span className="font-medium">
          {(() => {
            const page = filter.page ?? 1;
            const perPage = filter.limit ?? 50;
            const start = total === 0 ? 0 : (page - 1) * perPage + 1;
            const end = Math.min(start + (items?.length || 0) - 1, total);
            return `${start}–${end} / ${total.toLocaleString()}`;
          })()}
        </span>
        {loading && <span className="text-blue-600 dark:text-blue-400 animate-pulse">●</span>}
      </div>

      {!loading && items.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400" data-testid="no-results">
          <div className="text-4xl mb-2">📝</div>
          <div className="text-lg font-medium">결과 없음</div>
          <div className="text-sm mt-1">검색 조건을 변경해보세요</div>
        </div>
      )}

      {undo && (
        <div className="my-2 flex items-center justify-between text-sm bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg px-4 py-3 shadow-sm">
          <span className="text-amber-900 dark:text-amber-200">
            삭제됨: <strong>{(undo.prev.stem || undo.prev.title || '제목 없음').slice(0, 30)}...</strong>
          </span>
          <button
            className="text-amber-800 dark:text-amber-300 underline hover:text-amber-900 dark:hover:text-amber-100 font-medium transition-colors"
            data-testid="undo-button"
            onClick={async () => {
              const prev = undo.prev;
              const payload = {
                stem: prev.stem,
                options: prev.options,
                answer: prev.answer,
                difficulty: prev.difficulty,
                topic: prev.topic,
                tags: prev.tags,
                status: (prev.status ?? 'draft') as any,
                author: prev.author,
              };
              await updateQuestion(undo.id, payload);
              setUndo(null);
              try { sessionStorage.removeItem('questions_undo'); } catch {}
              const { results, total, nextCursor } = await listQuestions({ ...filter });
              setItems(results || []);
              setTotal(total || 0);
              setNextCursor(nextCursor);
            }}
          >Undo</button>
        </div>
      )}

      <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          {loading ? (
            <span className="text-blue-600 dark:text-blue-400 font-medium animate-pulse">로딩중…</span>
          ) : (
            <span className="font-medium">{total.toLocaleString()}개 결과</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer hover:text-gray-900 dark:hover:text-gray-100 transition-colors">
            <input data-testid="keyset-toggle" type="checkbox" className="rounded" checked={useKeyset} onChange={(e) => { setUseKeyset(e.target.checked); setNextCursor(undefined); setFilter(f => ({ ...f, page: 1 })); }} />
            <span className="text-xs font-medium">키셋(beta)</span>
          </label>
          {!useKeyset && (<>
          <button
            className="px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors font-medium"
            data-testid="prev-button"
            disabled={(filter.page ?? 1) <= 1 || loading}
            onClick={() => setFilter(f => ({ ...f, page: Math.max(1, (f.page ?? 1) - 1) }))}
          >이전</button>
          {(() => {
            const current = filter.page ?? 1;
            const perPage = filter.limit ?? 50;
            const totalPages = Math.max(1, Math.ceil(total / perPage));
            const windowSize = 5;
            let start = Math.max(1, current - Math.floor(windowSize / 2));
            let end = Math.min(totalPages, start + windowSize - 1);
            if (end - start + 1 < windowSize) start = Math.max(1, end - windowSize + 1);
            const pages = [] as number[];
            for (let p = start; p <= end; p++) pages.push(p);
            return (
              <div className="flex items-center gap-1" aria-label="페이지 이동">
                {start > 1 && (
                  <button className="px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" data-testid="page-btn-1" onClick={() => setFilter(f => ({ ...f, page: 1 }))}>1</button>
                )}
                {start > 2 && <span className="px-1 text-gray-400">…</span>}
                {pages.map(p => (
                  <button
                    key={p}
                    data-testid={`page-btn-${p}`}
                    className={`px-3 py-1.5 rounded-md border transition-colors font-medium ${
                      p === current 
                        ? 'bg-blue-600 text-white border-blue-600 shadow-md' 
                        : 'border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                    disabled={loading || p === current}
                    onClick={() => setFilter(f => ({ ...f, page: p }))}
                  >{p}</button>
                ))}
                {end < totalPages - 1 && <span className="px-1 text-gray-400">…</span>}
                {end < totalPages && (
                  <button className="px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" data-testid={`page-btn-${totalPages}`} onClick={() => setFilter(f => ({ ...f, page: totalPages }))}>{totalPages}</button>
                )}
              </div>
            );
          })()}
          <span className="text-xs" data-testid="page-number">페이지 {(filter.page ?? 1)}</span>
          <button
            className="px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors font-medium"
            data-testid="next-button"
            disabled={(filter.page ?? 1) * (filter.limit ?? 50) >= total || loading}
            onClick={() => setFilter(f => ({ ...f, page: (f.page ?? 1) + 1 }))}
          >다음</button>
          <select
            className="ml-2 h-9 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
            data-testid="page-size-select"
            value={filter.limit}
            onChange={(e) => setFilter(f => ({ ...f, limit: Number(e.target.value), page: 1 }))}
          >
            {[10,20,50,100].map(n => (<option key={n} value={n}>{n}/페이지</option>))}
          </select>
          </>)}
          {useKeyset && (
            <button
              className="px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 disabled:opacity-50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors font-medium"
              data-testid="keyset-next-button"
              disabled={!nextCursor || loading}
              onClick={() => {
                (async () => {
                  setLoading(true);
                  try {
                    const { results, total, nextCursor: nc } = await listQuestions({ ...filter, cursor: nextCursor });
                    setItems(results || []);
                    setTotal(total || 0);
                    setNextCursor(nc);
                  } catch (e) {
                    console.error(e);
                  } finally {
                    setLoading(false);
                  }
                })();
              }}
            >다음(키셋)</button>
          )}
        </div>
      </div>

      <ConfirmModal
        open={!!confirmId}
        title="삭제 확인"
        message={<span>정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.</span>}
        cancelLabel="취소"
        confirmLabel={deleting ? '삭제중…' : '삭제'}
        disabled={deleting}
        onCancel={() => {
          console.log('[DEBUG] Delete cancelled');
          setConfirmId(null);
        }}
        onConfirm={() => {
          console.log('[DEBUG] Delete confirmed for id:', confirmId);
          if (confirmId) performDelete(confirmId);
        }}
        testId="confirm-delete-dialog"
      />

      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-lg shadow-2xl backdrop-blur-sm ${
            toast.type === 'success' 
              ? 'bg-emerald-600/95 text-white border border-emerald-500' 
              : 'bg-rose-600/95 text-white border border-rose-500'
          } animate-in slide-in-from-bottom-5 duration-300`}
          data-testid="toast-generic"
        >
          <div className="flex items-center gap-2">
            <span className="text-lg">{toast.type === 'success' ? '✓' : '✕'}</span>
            <span className="font-medium">{toast.msg}</span>
          </div>
        </div>
      )}
    </section>
  );
}
