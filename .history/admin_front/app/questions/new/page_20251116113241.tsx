'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { QuestionForm } from '../../../components/QuestionForm';
import { Breadcrumbs } from '../../../components/Breadcrumbs';
import { createQuestion, QuestionInput } from '../../../lib/questions';

export default function NewQuestionPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initialForm: QuestionInput = {
    title: '',
    stem: '',
    explanation: '',
    hint: '',
    resource: '',
    answer_text: '',
    options: ['', '', '', ''],
    answer: 0,
    difficulty: 'medium',
    topic: '',
    topic_id: null,
    tags: [],
    status: 'draft',
    author: '',
    created_at: '',
    updated_at: '',
  };

  async function handleSubmit(data: QuestionInput) {
    console.log('[DEBUG] New question handleSubmit:', data);
    setSaving(true);
    setError(null);
    
    try {
      // 모든 필드를 백엔드로 전송
      const payload = {
        title: data.title || '새 문항',
        stem: data.stem || '',
        difficulty: data.difficulty || 'medium',
        topic: data.topic || '수학',
        explanation: data.explanation || '',
        hint: data.hint || '',
        resource: data.resource || '',
        answer_text: data.answer_text || '',
        options: data.options || [],
        answer: data.answer ?? 0,
        tags: data.tags || [],
      };
      
      console.log('[DEBUG] Creating question with payload:', payload);
      const res = await fetch('http://localhost:8002/api/admin/questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        console.error('[DEBUG] Server error:', errorText);
        throw new Error(`HTTP ${res.status}: ${errorText}`);
      }
      
      const result = await res.json();
      console.log('[DEBUG] Create result:', result);
      
      if (result && result.id) {
        // 생성 성공 - 편집 페이지로 이동
        router.push(`/questions/${result.id}/edit`);
      } else {
        setError('문항 생성에 실패했습니다.');
        setSaving(false);
      }
    } catch (e: any) {
      console.error('[DEBUG] Create error:', e);
      setError(e.message || '저장 중 오류가 발생했습니다.');
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <Breadcrumbs
        items={[
          { label: '문항 목록', href: '/questions' },
          { label: '신규 문항 추가' },
        ]}
      />
      
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">신규 문항 추가</h1>
      </div>

      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 text-red-900 px-4 py-3">
          {error}
        </div>
      )}

      <QuestionForm
        initial={initialForm}
        onSubmit={handleSubmit}
        disabled={saving}
      />
    </div>
  );
}
