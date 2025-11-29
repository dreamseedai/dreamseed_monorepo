"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { QuestionForm } from "../../../../components/QuestionForm";
import { ConfirmModal } from "../../../../components/ConfirmModal";
import { Question, QuestionInput, getQuestion, getQuestionWithSource, updateQuestion, deleteQuestion } from "../../../../lib/questions";
import { route } from "../../../../lib/route";
import { Breadcrumbs } from "../../../../components/Breadcrumbs";
import { getApiMeta, ApiMeta } from "../../../../lib/meta";

export default function EditQuestionPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [q, setQ] = useState<Question | null>(null);
  const [stale, setStale] = useState<string | null>(null);
  const [source, setSource] = useState<string | undefined>(undefined);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [meta, setMeta] = useState<ApiMeta | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        console.log('[EditPage] start load, id =', params.id);
        setLoading(true);
        setError(null);
        const { question, source } = await getQuestionWithSource(params.id);
        console.log('[EditPage] got question =', question, 'source =', source);
        if (!question) {
          if (!cancelled) {
            setQ(null);
            setSource(source);
            setError("해당 문항을 찾을 수 없습니다.");
            setLoading(false);
          }
          return;
        }
        // Ensure required fields for QuestionForm validation
        const normalized = {
          ...question,
          options: Array.isArray(question.options) && question.options.length >= 2 
            ? question.options 
            : ['보기 1', '보기 2', '보기 3', '보기 4'],
          answer: typeof question.answer === 'number' && question.answer >= 0 
            ? question.answer 
            : 0,
          tags: Array.isArray(question.tags) ? question.tags : [],
        };
        if (!cancelled) { 
          setQ(normalized); 
          setSource(source); 
          setLoading(false);
          console.log('[EditPage] setLoading(false) - success');
        }
      } catch (e) {
        console.error('[EditPage] load error =', e);
        if (!cancelled) {
          setError("문항을 불러오는 중 오류가 발생했습니다.");
          setLoading(false);
          console.log('[EditPage] setLoading(false) - error');
        }
      }
    };
    load();
    return () => { cancelled = true; };
  }, [params.id]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try { const m = await getApiMeta(); if (!cancelled) setMeta(m); } catch {}
    })();
    return () => { cancelled = true; };
  }, []);


  if (loading) {
    return (
      <section className="p-4 text-sm text-gray-600">
        로딩중...
      </section>
    );
  }

  if (error && !q) {
    return (
      <section className="p-4 text-sm text-red-600">
        {error}
      </section>
    );
  }

  if (!q) {
    return (
      <section className="p-4 text-sm text-gray-600">
        문항 데이터를 찾을 수 없습니다.
      </section>
    );
  }
  const readOnly = !!(meta?.legacy_readonly_enabled && (source?.startsWith('legacy')));

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <Breadcrumbs items={[{ label: '문항 목록', href: '/questions' }, { label: '편집' }]} />
        <button onClick={() => !readOnly && setConfirmOpen(true)} className={`text-sm ${readOnly ? 'text-gray-400 cursor-not-allowed' : 'text-red-600'}`} title={readOnly ? '레거시 모드에서는 삭제할 수 없습니다.' : undefined}>삭제</button>
      </div>
      {/* Header info box (image preview removed as requested) */}
      <div className="rounded border border-gray-200 bg-white p-3 text-sm grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <div className="text-gray-500">문항 ID</div>
          <div className="font-medium">{q.id}</div>
        </div>
        <div>
          <div className="text-gray-500">등록일</div>
          <div className="font-medium">{q.created_at ? new Date(q.created_at).toLocaleString() : '-'}</div>
        </div>
        <div>
          <div className="text-gray-500">수정일</div>
          <div className="font-medium">{q.updated_at ? new Date(q.updated_at).toLocaleString() : '-'}</div>
        </div>
      </div>
      {meta?.legacy_readonly_enabled && (
        <div className="rounded-md border border-yellow-300 bg-yellow-50 text-yellow-900 px-3 py-2 text-sm">
          레거시 데이터 보기 모드: 이 문항은 레거시 원본에서 조회되었을 수 있습니다. 편집/삭제는 SeedTest 데이터와 동기화 상황에 따라 제한될 수 있습니다.
        </div>
      )}
      <h1 className="text-xl font-semibold">문항 편집</h1>
      {readOnly && (
        <div className="rounded-md border border-yellow-300 bg-yellow-50 text-yellow-900 px-3 py-2 text-sm">
          레거시 읽기 전용 모드: 이 문항은 레거시 원본에서 조회되었습니다. 편집/삭제가 비활성화되었습니다.
        </div>
      )}
      {stale && (
        <div className="rounded border border-amber-300 bg-amber-50 text-amber-900 p-3 text-sm">
          <div className="flex items-center justify-between gap-2">
            <span>{stale}</span>
            <button
              className="px-2 py-1 text-xs rounded bg-amber-600 text-white hover:bg-amber-700"
              onClick={async () => {
                try {
                  const fresh = await getQuestion(params.id);
                  if (fresh) setQ(fresh);
                } catch (e) { console.error(e); }
                setStale(null);
              }}
            >새로고침</button>
          </div>
        </div>
      )}
      <QuestionForm
        initial={q}
        disabled={readOnly}
        onSubmit={async (data: QuestionInput) => {
          if (readOnly) return; // guard
          try {
            await updateQuestion(q.id, data);
            router.push(route('/questions'));
          } catch (e: any) {
            const msg = String(e?.message || '');
            if (msg.includes('412') || msg.includes('etag_mismatch')) {
              setStale('다른 곳에서 문항이 수정되었습니다. 새로고침 후 다시 시도하세요.');
              return;
            }
            throw e;
          }
        }}
      />
      

      <ConfirmModal
        open={confirmOpen}
        title="삭제 확인"
        message={<span>정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.</span>}
        cancelLabel="취소"
        confirmLabel={deleting ? '삭제중…' : '삭제'}
        disabled={deleting}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={async () => {
          setDeleting(true);
          try {
            const result = await deleteQuestion(q.id);
            const qs = result.warning ? '?toast=deleted&warn=1' : '?toast=deleted';
            router.push((route('/questions') + qs) as any);
          } catch (e) {
            const msg = String((e as any)?.message || '');
            if (msg.includes('412') || msg.includes('etag_mismatch')) {
              setStale('리소스가 변경되어 삭제에 실패했습니다. 새로고침 후 다시 시도하세요.');
            } else {
              console.error(e);
            }
            setDeleting(false);
            setConfirmOpen(false);
          }
        }}
        testId="confirm-delete-dialog"
      />
    </section>
  );
}
