"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { QuestionInput, uploadImage } from "../lib/questions";
import { Topic, getTopics, invalidateTopicsCache } from "../lib/topics";
import dynamic from 'next/dynamic';

// RichTextEditor는 클라이언트 전용 컴포넌트 (TinyMCE 때문)
const RichTextEditor = dynamic(
  () => import('./RichTextEditor').then((mod) => mod.RichTextEditor),
  { ssr: false, loading: () => <div className="border rounded p-4 text-sm text-gray-500">에디터 로딩중...</div> }
);

type ExtendedForm = QuestionInput & {
  title?: string; // UI-only
  explanation?: string; // UI-only
  hint?: string; // UI-only
  resource?: string; // UI-only
  answer_text?: string; // UI-only
  discrimination?: number; // UI-only
  guessing?: number; // UI-only
  difficulty_param?: number; // UI-only (IRT b)
};

export function QuestionForm({ initial, onSubmit, disabled }: { initial?: QuestionInput; onSubmit: (q: QuestionInput) => void; disabled?: boolean }) {
  const defaultForm: ExtendedForm = { stem: "", options: ["", ""], answer: 0, difficulty: "medium", topic: "", tags: [], status: "draft", topic_id: undefined, hint: "", resource: "", answer_text: "" } as any;
  const [form, setForm] = useState<ExtendedForm>(() => {
    const initialForm = initial || defaultForm;
    return {
      ...initialForm,
      stem: initialForm.stem || "",
      options: Array.isArray(initialForm.options) && initialForm.options.length > 0 ? initialForm.options : ["", ""]
    };
  });
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [topicsLoading, setTopicsLoading] = useState<boolean>(false);
  const [orgId, setOrgId] = useState<string>("");
  const [includeGlobal, setIncludeGlobal] = useState<boolean>(true);
  const initialSnapshotRef = useRef<string>("");
  const [dirty, setDirty] = useState(false);
  const stemRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    window.setTimeout(() => setToast(null), 3000);
  };

  const canRemove = (form.options?.length ?? 0) > 2;
  const addOption = () => setForm({ ...form, options: [...(form.options || []), ""] });
  const removeOption = (idx: number) => {
    if ((form.options?.length ?? 0) <= 2) return;
    const next = (form.options || []).filter((_, i) => i !== idx);
    let nextAnswer = form.answer;
    if (idx === form.answer) nextAnswer = 0; // reset to first if removed correct answer
    else if (idx < form.answer) nextAnswer = Math.max(0, form.answer - 1);
    setForm({ ...form, options: next, answer: nextAnswer });
  };

  const errors = useMemo(() => {
    const errs: string[] = [];
    if (!form.stem.trim()) errs.push("문항 내용을 입력하세요.");
    if (!Array.isArray(form.options) || form.options.length < 2) errs.push("보기는 최소 2개 이상이어야 합니다.");
    const trimmed = (form.options || []).map(s => String(s || "").trim());
    if (trimmed.some(s => !s)) errs.push("빈 보기(공백만 포함)를 제거하세요.");
    const uniq = new Set(trimmed);
    if (uniq.size !== trimmed.length) errs.push("중복된 보기가 있습니다.");
    if (form.answer < 0 || form.answer >= trimmed.length) errs.push("정답을 선택하세요.");
    if (trimmed.length >= 2 && (form.answer >= 0 && form.answer < trimmed.length) && !trimmed[form.answer]) {
      errs.push("정답으로 빈 보기를 선택할 수 없습니다.");
    }
    // Numeric validation for IRT parameters
    if (form.discrimination !== undefined) {
      if (!Number.isFinite(form.discrimination)) errs.push("변별도 a는 숫자여야 합니다.");
      else if ((form.discrimination as number) <= 0) errs.push("변별도 a는 0보다 커야 합니다.");
    }
    if (form.difficulty_param !== undefined) {
      if (!Number.isFinite(form.difficulty_param)) errs.push("난이도 파라미터 b는 숫자여야 합니다.");
    }
    if (form.guessing !== undefined) {
      if (!Number.isFinite(form.guessing)) errs.push("추측도 c는 숫자여야 합니다.");
      else if ((form.guessing as number) < 0 || (form.guessing as number) >= 1) errs.push("추측도 c는 0 이상 1 미만이어야 합니다.");
    }
    return errs;
  }, [form.stem, form.options, form.answer, form.discrimination, form.difficulty_param, form.guessing]);

  // Inline recommended-range warnings
  const aWarn = Number.isFinite(form.discrimination as number) && (form.discrimination as number) !== undefined && ((form.discrimination as number) < 0.5 || (form.discrimination as number) > 2.5);
  const bWarn = Number.isFinite(form.difficulty_param as number) && (form.difficulty_param as number) !== undefined && ((form.difficulty_param as number) < -3 || (form.difficulty_param as number) > 3);
  const cWarn = Number.isFinite(form.guessing as number) && (form.guessing as number) !== undefined && ((form.guessing as number) < 0 || (form.guessing as number) > 0.35);

  const isValid = errors.length === 0;

  const submit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (disabled) return;
    if (!isValid) return;
    const payload: QuestionInput = {
      // Persist extended fields when backend supports them; extra keys are ignored safely otherwise
      ...(form.title ? { title: form.title } : {} as any),
      stem: form.stem,
      ...(form.explanation ? { explanation: form.explanation } : {} as any),
      ...(form.hint ? { hint: form.hint } : {} as any),
      ...(form.resource ? { resource: form.resource } : {} as any),
      ...(form.answer_text ? { answer_text: form.answer_text } : {} as any),
      options: form.options,
      answer: form.answer,
      difficulty: form.difficulty,
      // Prefer topic_id; include legacy topic name for compatibility where helpful
      ...(form.topic_id != null ? { topic_id: form.topic_id as any } : {}),
      ...(form.topic ? { topic: form.topic } : {}),
      tags: form.tags,
      status: form.status,
      author: form.author,
      ...(form.discrimination !== undefined ? { discrimination: form.discrimination } : {} as any),
      ...(form.guessing !== undefined ? { guessing: form.guessing } : {} as any),
      ...(form.difficulty_param !== undefined ? { difficulty_param: form.difficulty_param } : {} as any),
    };
    onSubmit(payload);
  };

  // Snapshot initial on mount/update
  useEffect(() => {
    const snap = JSON.stringify(initial || { stem: "", options: ["", ""], answer: 0, difficulty: "medium", topic: "", tags: [], status: "draft", topic_id: undefined, hint: "", resource: "", answer_text: "" });
    initialSnapshotRef.current = snap;
    
    // Update form when initial changes
    if (initial) {
      const updatedForm = {
        ...initial,
        options: Array.isArray(initial.options) && initial.options.length > 0 ? initial.options : ["", ""]
      };
      setForm(updatedForm as ExtendedForm);
    }
  }, [initial]);

  // Dirty detection
  useEffect(() => {
    const current = JSON.stringify({
      title: form.title || undefined,
      stem: form.stem,
      explanation: form.explanation || undefined,
      options: form.options,
      answer: form.answer,
      difficulty: form.difficulty,
      topic: form.topic,
      topic_id: (form as any).topic_id,
      tags: form.tags,
      status: form.status,
      author: form.author,
      hint: form.hint,
      resource: form.resource,
      answer_text: form.answer_text,
      discrimination: form.discrimination,
      guessing: form.guessing,
      difficulty_param: form.difficulty_param,
    });
    setDirty(current !== initialSnapshotRef.current);
  }, [form]);

  // beforeunload warning when dirty
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
        return "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  // Autofocus
  useEffect(() => {
    stemRef.current?.focus();
  }, []);

  // Determine role from cookie (client-only). Admins can edit IRT fields; others see read-only.
  useEffect(() => {
    try {
      const m = document.cookie.match(/(?:^|; )role=([^;]+)/);
      const v = m ? decodeURIComponent(m[1]) : '';
      setIsAdmin(v === 'admin');
    } catch {
      setIsAdmin(false);
    }
  }, []);

  // Fetch topics (with optional admin scoping)
  const refreshTopics = async () => {
    setTopicsLoading(true);
    try {
      const opts: any = {};
      if (isAdmin && orgId) {
        const n = Number(orgId);
        if (Number.isFinite(n)) opts.orgId = n;
        opts.includeGlobal = includeGlobal;
      }
      const t = await getTopics(opts);
      setTopics(t);
    } catch (e) {
      console.warn('토픽 로드 실패', e);
    } finally {
      setTopicsLoading(false);
    }
  };

  useEffect(() => {
    refreshTopics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  // Insert helper for markdown/HTML into stem at cursor
  const insertIntoStem = (snippet: string) => {
    const ta = stemRef.current;
    if (!ta) {
      setForm({ ...form, stem: (form.stem || '') + snippet });
      return;
    }
    const start = ta.selectionStart ?? ta.value.length;
    const end = ta.selectionEnd ?? ta.value.length;
    const before = form.stem.slice(0, start);
    const after = form.stem.slice(end);
    const next = before + snippet + after;
    setForm({ ...form, stem: next });
    // restore caret after inserted snippet
    requestAnimationFrame(() => {
      try {
        const pos = start + snippet.length;
        ta.setSelectionRange(pos, pos);
        ta.focus();
      } catch {}
    });
  };

  const handleInsertImageByUrl = () => {
    const url = typeof window !== 'undefined' ? window.prompt('이미지 URL을 입력하세요') : '';
    if (!url) return;
    const alt = typeof window !== 'undefined' ? window.prompt('대체 텍스트(ALT)를 입력하세요 (선택)') : '';
    const altText = (alt || 'image').replace(/\]|\[/g, '');
    const snippet = `\n\n![${altText}](${url})\n\n`;
    insertIntoStem(snippet);
    showToast('success', '이미지 URL이 삽입되었습니다.');
  };

  const handleInsertImageByFile = () => {
    fileInputRef.current?.click();
  };

  const onImageFileSelected: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const file = e.target.files?.[0];
    e.currentTarget.value = '';
    if (!file) return;
    try {
      const resp = await uploadImage(file);
      const alt = typeof window !== 'undefined' ? window.prompt('대체 텍스트(ALT)를 입력하세요 (선택)') : '';
      const altText = (alt || file.name || 'image').replace(/\]|\[/g, '');
      const snippet = `\n\n![${altText}](${resp.url})\n\n`;
      insertIntoStem(snippet);
      showToast('success', '이미지 업로드 성공');
    } catch (err: any) {
      // Fallback to Base64 embed if upload fails
      try {
        const reader = new FileReader();
        reader.onload = () => {
          const dataUrl = String(reader.result || '');
          if (!dataUrl.startsWith('data:')) return;
          const alt = typeof window !== 'undefined' ? window.prompt('대체 텍스트(ALT)를 입력하세요 (선택)') : '';
          const altText = (alt || file.name || 'image').replace(/\]|\[/g, '');
          const snippet = `\n\n![${altText}](${dataUrl})\n\n`;
          insertIntoStem(snippet);
          showToast('error', '업로드 실패: Base64로 삽입되었습니다.');
        };
        reader.readAsDataURL(file);
      } catch {}
    }
  };

  return (
    <form className="space-y-6" onSubmit={submit} onKeyDown={(e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        submit();
      }
    }}>
      {disabled && (
        <div className="rounded-md border border-yellow-300 bg-yellow-50 text-yellow-900 px-3 py-2 text-sm">
          읽기 전용 모드: 저장이 비활성화되었습니다.
        </div>
      )}

      {/* Legacy-style table layout */}
      <div className="overflow-x-auto rounded border border-gray-200">
        <table className="min-w-full text-sm">
          <tbody className="divide-y divide-gray-100">
            {/* 1) 메타 */}
            <tr>
              <th className="w-36 bg-gray-50 text-left px-3 py-2 text-gray-600 align-top">메타</th>
              <td className="px-3 py-2">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <div>
                    <label className="block text-xs text-gray-700">난이도</label>
                    <select
                      className="mt-1 w-full rounded-md border border-gray-300 bg-white p-2 text-sm focus:border-blue-500 focus:outline-none"
                      value={form.difficulty}
                      onChange={(e) => setForm({ ...form, difficulty: e.target.value as any })}
                    >
                      <option value="easy">쉬움</option>
                      <option value="medium">보통</option>
                      <option value="hard">어려움</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-700">주제</label>
                    <div className="flex gap-2 items-center">
                      <select
                        className="mt-1 w-full rounded-md border border-gray-300 bg-white p-2 text-sm focus:border-blue-500 focus:outline-none"
                        value={(form as any).topic_id ?? ''}
                        onChange={(e) => {
                          const val = e.target.value;
                          const id = val === '' ? undefined : Number(val);
                          const found = topics.find(t => t.id === id);
                          setForm({ ...form, topic_id: id as any, topic: found?.name || '' } as any);
                        }}
                      >
                        <option value="">선택…</option>
                        {topics.map(t => (
                          <option key={t.id} value={t.id}>{t.name}</option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => refreshTopics()}
                        className="mt-1 rounded border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
                        title="토픽 새로고침"
                      >새로고침</button>
                    </div>
                    {topicsLoading && <div className="text-[11px] text-gray-500 mt-1">토픽 로딩중…</div>}
                    {isAdmin && (
                      <div className="mt-2 flex flex-wrap items-end gap-2 text-[11px] text-gray-700">
                        <label className="flex items-center gap-1">
                          <span>Org ID</span>
                          <input
                            type="number"
                            className="w-24 rounded border px-1 py-0.5"
                            value={orgId}
                            onChange={(e) => setOrgId(e.target.value)}
                          />
                        </label>
                        <label className="flex items-center gap-1">
                          <input type="checkbox" checked={includeGlobal} onChange={(e) => setIncludeGlobal(e.target.checked)} />
                          <span>글로벌 포함</span>
                        </label>
                        <button
                          type="button"
                          className="ml-auto rounded border px-2 py-1 text-[11px] hover:bg-gray-50"
                          onClick={async () => {
                            try {
                              const res = await invalidateTopicsCache();
                              showToast('success', `캐시 무효화됨 (${res.deleted_keys})`);
                            } catch (e: any) {
                              showToast('error', `캐시 무효화 실패: ${e?.message || '오류'}`);
                            } finally {
                              refreshTopics();
                            }
                          }}
                        >토픽 캐시 무효화</button>
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-xs text-gray-700">태그(콤마)</label>
                    <input
                      className="mt-1 w-full rounded-md border border-gray-300 bg-white p-2 text-sm focus:border-blue-500 focus:outline-none"
                      value={(form.tags || []).join(", ")}
                      onChange={(e) => setForm({ ...form, tags: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-700">상태</label>
                    <select
                      className="mt-1 w-full rounded-md border border-gray-300 bg-white p-2 text-sm focus:border-blue-500 focus:outline-none"
                      value={form.status}
                      onChange={(e) => setForm({ ...form, status: e.target.value as any })}
                    >
                      <option value="draft">초안</option>
                      <option value="published">게시</option>
                    </select>
                  </div>
                </div>

                {/* IRT 안내 및 필드 */}
                <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <div className="sm:col-span-2 lg:col-span-3">
                    <div className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-[12px] text-amber-900 flex items-center gap-2" role="note" aria-live="polite" data-testid="irt-guide">
                      <div className="relative inline-block group">
                        <button
                          type="button"
                          className="leading-none cursor-help select-none"
                          aria-describedby="irt-tooltip"
                          title="모수 설명"
                        >
                          ✱
                        </button>
                        <div
                          id="irt-tooltip"
                          role="tooltip"
                          className="absolute left-0 mt-2 w-80 rounded-md border border-amber-200 bg-white p-3 text-[12px] text-gray-800 shadow-lg invisible opacity-0 group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100 transition"
                        >
                          <div className="font-semibold mb-1">문항 모수(IRT) 안내</div>
                          <ul className="list-disc pl-4 space-y-0.5">
                            <li>변별도 a: 0.5 ~ 2.5 권장 (0 이상)</li>
                            <li>난이도 b: -3 ~ 3 권장</li>
                            <li>추측도 c: 0.00 ~ 0.35 권장</li>
                          </ul>
                          <div className="mt-2 text-[11px] text-gray-500">충분한 데이터로 자동 보정됩니다. 필요한 경우만 신중히 조정하세요.</div>
                        </div>
                      </div>
                      <span>
                        문항 모수(난이도 b, 변별도 a, 추측도 c)는 충분한 데이터로 자동 보정됩니다. 필요한 경우에만 신중히 조정하세요.
                        <a href="/docs/irt" target="_blank" rel="noopener noreferrer" className="ml-2 underline text-amber-900 hover:text-amber-800" title="문항 모수 가이드 자세히 보기">자세히</a>
                      </span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-700">변별도 a (선택)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="5"
                      className="mt-1 w-full rounded-md border border-gray-300 bg-white p-2 text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                      value={form.discrimination ?? ""}
                      onChange={(e) => setForm({ ...form, discrimination: e.target.value === '' ? undefined : Number(e.target.value) })}
                      data-testid="input-a"
                      disabled={!isAdmin || disabled}
                    />
                    <p className="mt-1 text-[11px] text-gray-500">권장 범위: 0.5 ~ 2.5</p>
                    {aWarn && <p className="mt-0.5 text-[11px] text-amber-700" data-testid="warn-a">권장 범위를 벗어났습니다.</p>}
                    {!isAdmin && <p className="mt-0.5 text-[11px] text-amber-700" data-testid="irt-readonly-a">관리자만 편집할 수 있습니다 (읽기 전용)</p>}
                  </div>
                  <div>
                    <label className="block text-xs text-gray-700">난이도 b (선택)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="-10"
                      max="10"
                      className="mt-1 w-full rounded-md border border-gray-300 bg-white p-2 text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                      value={form.difficulty_param ?? ""}
                      onChange={(e) => setForm({ ...form, difficulty_param: e.target.value === '' ? undefined : Number(e.target.value) })}
                      data-testid="input-b"
                      disabled={!isAdmin || disabled}
                    />
                    <p className="mt-1 text-[11px] text-gray-500">권장 범위: -3 ~ 3</p>
                    {bWarn && <p className="mt-0.5 text-[11px] text-amber-700" data-testid="warn-b">권장 범위를 벗어났습니다.</p>}
                    {!isAdmin && <p className="mt-0.5 text-[11px] text-amber-700" data-testid="irt-readonly-b">관리자만 편집할 수 있습니다 (읽기 전용)</p>}
                  </div>
                  <div>
                    <label className="block text-xs text-gray-700">추측도 c (선택)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      className="mt-1 w-full rounded-md border border-gray-300 bg-white p-2 text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                      value={form.guessing ?? ""}
                      onChange={(e) => setForm({ ...form, guessing: e.target.value === '' ? undefined : Number(e.target.value) })}
                      data-testid="input-c"
                      disabled={!isAdmin || disabled}
                    />
                    <p className="mt-1 text-[11px] text-gray-500">권장 범위: 0.00 ~ 0.35</p>
                    {cWarn && <p className="mt-0.5 text-[11px] text-amber-700" data-testid="warn-c">권장 범위를 벗어났습니다.</p>}
                    {!isAdmin && <p className="mt-0.5 text-[11px] text-amber-700" data-testid="irt-readonly-c">관리자만 편집할 수 있습니다 (읽기 전용)</p>}
                  </div>
                </div>
              </td>
            </tr>
            {/* 2) 제목 */}
            <tr>
              <th className="bg-gray-50 text-left px-3 py-2 text-gray-600 align-top">제목</th>
              <td className="px-3 py-2">
                <RichTextEditor
                  value={form.title || ""}
                  onChange={(value) => setForm({ ...form, title: value })}
                  placeholder="예: 이차방정식의 근과 계수 관계"
                  autoHeight
                  minHeight={80}
                  disabled={disabled}
                />
                <p className="mt-1 text-[11px] text-gray-500">제목은 간결하게 작성하세요. 필요 시 굵게/기울임, 수식 등을 사용할 수 있습니다.</p>
              </td>
            </tr>
            {/* 3) 본문 내용 */}
            <tr>
              <th className="bg-gray-50 text-left px-3 py-2 text-gray-600 align-top">본문 내용</th>
              <td className="px-3 py-2">
                <RichTextEditor
                  value={form.stem}
                  onChange={(value) => setForm({ ...form, stem: value })}
                  placeholder="문항 본문을 입력하세요"
                  autoHeight
                  minHeight={120}
                  disabled={disabled}
                />
                <p className="mt-1 text-[11px] text-gray-500">본문은 HTML/MathML을 사용할 수 있습니다. 수식 버튼을 클릭하여 수학 수식을 삽입하세요.</p>
              </td>
            </tr>
            {/* 4) 해설 (선택) */}
            <tr>
              <th className="bg-gray-50 text-left px-3 py-2 text-gray-600 align-top">해설 (선택)</th>
              <td className="px-3 py-2">
                <RichTextEditor
                  value={form.explanation || ""}
                  onChange={(value) => setForm({ ...form, explanation: value })}
                  placeholder="정답 풀이와 해설을 작성하세요"
                  autoHeight
                  minHeight={100}
                  disabled={disabled}
                />
              </td>
            </tr>
            {/* 5) 보기 / 정답 */}
            <tr>
              <th className="bg-gray-50 text-left px-3 py-2 text-gray-600 align-top">보기 / 정답</th>
              <td className="px-3 py-2">
                <div className="space-y-3">
                  {form.options.map((opt, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <input
                        type="radio"
                        name="answer"
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                        checked={form.answer === i}
                        onChange={() => setForm({ ...form, answer: i })}
                        aria-label={`정답 선택 ${i + 1}`}
                      />
                      <input
                        className="flex-1 rounded-md border border-gray-300 bg-white p-2 text-sm focus:border-blue-500 focus:outline-none"
                        placeholder={`선지 ${i + 1}`}
                        value={opt}
                        onChange={(e) => {
                          const next = [...form.options];
                          next[i] = e.target.value;
                          setForm({ ...form, options: next });
                        }}
                      />
                      {canRemove && (
                        <button
                          type="button"
                          onClick={() => removeOption(i)}
                          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
                          aria-label={`선지 ${i + 1} 삭제`}
                        >
                          -
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                {errors.length > 0 && (
                  <ul className="mt-2 list-disc pl-5 text-xs text-red-600">
                    {errors.map((e, idx) => (<li key={idx}>{e}</li>))}
                  </ul>
                )}
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={addOption}
                    className="rounded-md border border-dashed border-gray-300 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
                  >
                    + 보기 추가
                  </button>
                </div>
              </td>
            </tr>
            {/* 6) 힌트 */}
            <tr>
              <th className="bg-gray-50 text-left px-3 py-2 text-gray-600 align-top">힌트 (선택)</th>
              <td className="px-3 py-2">
                <RichTextEditor
                  value={form.hint || ""}
                  onChange={(value) => setForm({ ...form, hint: value })}
                  placeholder="풀이에 도움이 되는 힌트를 작성하세요"
                  autoHeight
                  minHeight={100}
                  disabled={disabled}
                />
              </td>
            </tr>
            {/* 7) 자료/리소스 */}
            <tr>
              <th className="bg-gray-50 text-left px-3 py-2 text-gray-600 align-top">자료/리소스 (선택)</th>
              <td className="px-3 py-2">
                <RichTextEditor
                  value={form.resource || ""}
                  onChange={(value) => setForm({ ...form, resource: value })}
                  placeholder="참고 자료, 링크, 추가 이미지 등을 입력하세요"
                  autoHeight
                  minHeight={100}
                  disabled={disabled}
                />
              </td>
            </tr>
            {/* 8) 정답 서술 */}
            <tr>
              <th className="bg-gray-50 text-left px-3 py-2 text-gray-600 align-top">정답 서술 (선택)</th>
              <td className="px-3 py-2">
                <RichTextEditor
                  value={form.answer_text || ""}
                  onChange={(value) => setForm({ ...form, answer_text: value })}
                  placeholder="정답을 간단히 서술하거나 추가 설명을 입력하세요"
                  autoHeight
                  minHeight={100}
                  disabled={disabled}
                />
                <p className="mt-1 text-[11px] text-gray-500">주의: 위 입력은 정답 선택(라디오 버튼)과 별도입니다.</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between pt-2">
        <div className="text-xs text-gray-500">필수: 본문, 보기 2개 이상, 정답 1개 선택</div>
        <button
          disabled={disabled || !isValid}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          저장
        </button>
      </div>

      {dirty && (
        <div className="fixed bottom-4 right-4 rounded bg-amber-100 text-amber-900 text-xs px-3 py-2 shadow pointer-events-none">
          저장되지 않은 변경 사항이 있습니다.
        </div>
      )}
      {toast && (
        <div
          className={
            `fixed bottom-4 right-4 z-50 rounded px-3 py-2 text-xs shadow ` +
            (toast.type === 'success' ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white')
          }
          role="status"
          data-testid="toast-upload"
        >
          {toast.msg}
        </div>
      )}
    </form>
  );
}
