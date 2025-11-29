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

  const [items, setItems] = useState<Question[]>(Array.isArray(initial?.results) ? initial.results : []);
  const [total, setTotal] = useState<number>(Number.isFinite(initial?.total as any) ? (initial.total as number) : 0);
  const [loading, setLoading] = useState(false);
  const [useKeyset, setUseKeyset] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | undefined>(initial?.nextCursor);
  const [undo, setUndo] = useState<{ id: string; prev: Question } | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
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

  useEffect(() => {
    const currentParsed = parseFilterFromURL(searchParams as any);
    const target = buildURLFromFilter(pathname, filter, useKeyset);
    const current = buildURLFromFilter(pathname, currentParsed.f, currentParsed.keyset);
    if (target !== current) {
      try { router.replace(target as any); } catch {}
      try { if (typeof window !== 'undefined') window.history.replaceState(null, '', target); } catch {}
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter, useKeyset, pathname]);

  useEffect(() => {
    try {
      const sp = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '');
      const { f: urlFilter, keyset } = parseFilterFromURL(sp as any);
      const same = filtersEqual(filter, urlFilter) && keyset === useKeyset;
      if (!same) {
        setFilter(urlFilter);
        setUseKeyset(keyset);
        setNextCursor(undefined);
      }
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  function fmtUpdatedAt(q: Question): string {
    const v = q.updated_at ?? q.created_at;
    if (!v && v !== 0) return '-';
    const ms = typeof v === 'string' ? Date.parse(v) : Math.round(Number(v) * 1000);
    if (!isFinite(ms)) return '-';
    try { return new Date(ms).toLocaleString('ko-KR', { hour12: false }); } catch { return new Date(ms).toISOString(); }
  }

  async function performDelete(id: string | number) {
    const target = items.find(x => x.id === Number(id));
    if (!target) return;
    setDeleting(true);
    try {
      const result = await deleteQuestion(Number(id));
      setUndo({ id, prev: target });
      const { results, total, nextCursor } = await listQuestions({ ...debouncedFilter });
      setItems(results || []);
      setTotal(total || 0);
      setNextCursor(nextCursor);
      setToast({ type: 'success', msg: result.warning ? `삭제되었습니다 (경고: ${result.warning})` : '삭제되었습니다' });
      window.setTimeout(() => setToast(null), 3000);
      setTimeout(() => setUndo(null), 5000);
    } catch (e) {
      console.error(e);
      setToast({ type: 'error', msg: '삭제 중 오류가 발생했습니다.' });
      window.setTimeout(() => setToast(null), 3000);
    } finally {
      setDeleting(false);
      setConfirmId(null);
    }
  }

  return (
    <section className="space-y-4">
      <Breadcrumbs items={[{ label: '문항 목록' }]} />
      {meta?.legacy_readonly_enabled && (
        <div className="rounded-md border border-yellow-300 bg-yellow-50 text-yellow-900 px-3 py-2 text-sm">
          레거시 데이터 보기 모드가 활성화되어 있습니다. 목록/상세 조회는 "{meta.legacy_source}" 원본을 따릅니다. 편집/삭제 시 동기화 차이가 있을 수 있습니다.
        </div>
      )}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold" data-testid="questions-heading">문항은행</h1>
        <Link href="/questions/new" className="rounded bg-blue-600 px-3 py-1.5 text-white text-sm">신규 문항 추가</Link>
      </div>

      <SearchBar
        value={filter}
        onChange={setFilter}
        searching={loading}
        onSubmit={() => {
          setDebouncedFilter(filter);
        }}
      />

  <div className="rounded border overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left">
                {ID_SORT_MODE === 'hide' ? (
                  <span>ID</span>
                ) : (
                  <button
                    className="hover:underline"
                    onClick={() => setFilter(f => ({
                      ...f,
                      sortBy: effectiveIdField,
                      order: (f.sortBy === effectiveIdField && f.order === 'desc') ? 'asc' : 'desc',
                      page: 1,
                    }))}
                  >
                    ID{filter.sortBy === effectiveIdField ? (filter.order === 'desc' ? ' ▼' : ' ▲') : ''}
                  </button>
                )}
              </th>
              <th className="px-3 py-2 text-left">Title</th>
              <th className="px-3 py-2">
                <button className="hover:underline" onClick={() => setFilter(f => ({ ...f, sortBy: 'topic', order: (f.sortBy === 'topic' && f.order === 'desc') ? 'asc' : 'desc', page: 1 }))}>
                  분류{filter.sortBy === 'topic' ? (filter.order === 'desc' ? ' ▼' : ' ▲') : ''}
                </button>
              </th>
              <th className="px-3 py-2">
                <button className="hover:underline" onClick={() => setFilter(f => ({ ...f, sortBy: 'difficulty', order: f.sortBy === 'difficulty' && f.order === 'desc' ? 'asc' : 'desc', page: 1 }))}>
                  난이도{filter.sortBy === 'difficulty' ? (filter.order === 'desc' ? ' ▼' : ' ▲') : ''}
                </button>
              </th>
              <th className="px-3 py-2">
                <button
                  className="inline-flex items-center gap-1 hover:underline"
                  onClick={() => setFilter(f => ({ ...f, sortBy: 'updated_at', order: f.order === 'desc' ? 'asc' : 'desc', page: 1 }))}
                  title="최근 수정일 정렬 토글"
                >
                  최근 수정일
                  <span className="text-xs text-gray-500">{filter.sortBy === 'updated_at' ? (filter.order === 'desc' ? '▼' : '▲') : ''}</span>
                </button>
              </th>
              <th className="px-3 py-2">
                <button className="hover:underline" onClick={() => setFilter(f => ({ ...f, sortBy: 'status', order: f.sortBy === 'status' && f.order === 'desc' ? 'asc' : 'desc', page: 1 }))}>
                  상태{filter.sortBy === 'status' ? (filter.order === 'desc' ? ' ▼' : ' ▲') : ''}
                </button>
              </th>
              <th className="px-3 py-2">작업</th>
            </tr>
          </thead>
          <tbody>
            {items.map((q) => (
              <tr key={q.id} className="border-t">
                <td className="px-3 py-2">{q.id}</td>
                <td 
                  className="px-3 py-2 line-clamp-2 max-w-xl cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                  onDoubleClick={() => router.push(route(`/questions/${q.id}/edit`))}
                  title="더블클릭하여 편집"
                >
                  <MathRenderer content={q.title || ''} />
                </td>
                <td className="px-3 py-2">{q.topic || '-'}</td>
                <td className="px-3 py-2">
                  <span className={
                    `inline-flex items-center px-2 py-0.5 rounded text-xs ${q.difficulty === 'easy' ? 'bg-green-100 text-green-800' : q.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`
                  }>{q.difficulty}</span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap">{fmtUpdatedAt(q)}</td>
                <td className="px-3 py-2">
                  <span className={
                    `inline-flex items-center px-2 py-0.5 rounded text-xs ${q.status === 'published' ? 'bg-blue-100 text-blue-800' : q.status === 'deleted' ? 'bg-gray-200 text-gray-700 line-through' : 'bg-slate-100 text-slate-700'}`
                  }>{q.status || 'draft'}</span>
                </td>
                <td className="px-3 py-2 text-center">
                  <button
                    onClick={() => setConfirmId(q.id)}
                    className={`${meta?.legacy_readonly_enabled ? 'text-gray-400 cursor-not-allowed' : 'text-red-600 hover:underline'}`}
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
      <div className="text-sm text-slate-600">
        {(() => {
          const page = filter.page ?? 1;
          const perPage = filter.limit ?? 50;
          const start = total === 0 ? 0 : (page - 1) * perPage + 1;
          const end = Math.min(start + (items?.length || 0) - 1, total);
          return (
            <span>
              Showing {start}–{end} of {total} items
            </span>
          );
        })()}
      </div>

      {!loading && items.length === 0 && (
        <div className="text-sm text-gray-600" data-testid="no-results">결과 없음</div>
      )}

      {undo && (
        <div className="my-2 flex items-center justify-between text-sm bg-amber-50 border border-amber-200 rounded px-3 py-2">
          <span>삭제됨: {undo.prev.stem.slice(0, 30)}...</span>
          <button
            className="text-amber-800 underline"
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

      <div className="flex items-center justify-between text-xs text-gray-600">
        <div>{loading ? '로딩중…' : `${total}개 결과`}</div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1 mr-3">
            <input data-testid="keyset-toggle" type="checkbox" checked={useKeyset} onChange={(e) => { setUseKeyset(e.target.checked); setNextCursor(undefined); setFilter(f => ({ ...f, page: 1 })); }} />
            <span>키셋(beta)</span>
          </label>
          {!useKeyset && (<>
          <button
            className="px-2 py-1 rounded border disabled:opacity-50"
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
                  <button className="px-2 py-1 rounded border" data-testid="page-btn-1" onClick={() => setFilter(f => ({ ...f, page: 1 }))}>1</button>
                )}
                {start > 2 && <span className="px-1">…</span>}
                {pages.map(p => (
                  <button
                    key={p}
                    data-testid={`page-btn-${p}`}
                    className={`px-2 py-1 rounded border ${p === current ? 'bg-blue-600 text-white border-blue-600' : 'hover:bg-gray-50'}`}
                    disabled={loading || p === current}
                    onClick={() => setFilter(f => ({ ...f, page: p }))}
                  >{p}</button>
                ))}
                {end < totalPages - 1 && <span className="px-1">…</span>}
                {end < totalPages && (
                  <button className="px-2 py-1 rounded border" data-testid={`page-btn-${totalPages}`} onClick={() => setFilter(f => ({ ...f, page: totalPages }))}>{totalPages}</button>
                )}
              </div>
            );
          })()}
          <span data-testid="page-number">페이지 {(filter.page ?? 1)}</span>
          <button
            className="px-2 py-1 rounded border disabled:opacity-50"
            data-testid="next-button"
            disabled={(filter.page ?? 1) * (filter.limit ?? 50) >= total || loading}
            onClick={() => setFilter(f => ({ ...f, page: (f.page ?? 1) + 1 }))}
          >다음</button>
          <select
            className="ml-2 h-7 rounded border bg-white"
            data-testid="page-size-select"
            value={filter.limit}
            onChange={(e) => setFilter(f => ({ ...f, limit: Number(e.target.value), page: 1 }))}
          >
            {[10,20,50,100].map(n => (<option key={n} value={n}>{n}/페이지</option>))}
          </select>
          </>)}
          {useKeyset && (
            <button
              className="px-2 py-1 rounded border disabled:opacity-50"
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
        onCancel={() => setConfirmId(null)}
        onConfirm={() => confirmId && performDelete(confirmId)}
        testId="confirm-delete-dialog"
      />

      {toast && (
        <div
          className={`fixed bottom-4 right-4 z-50 px-3 py-2 rounded shadow ${toast.type === 'success' ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white'}`}
          data-testid="toast-generic"
        >
          {toast.msg}
        </div>
      )}
    </section>
  );
}
