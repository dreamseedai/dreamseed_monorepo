'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { QuestionForm } from '../../../components/QuestionForm';
import { Breadcrumbs } from '../../../components/Breadcrumbs';
import { createQuestion } from '../../../lib/questions';

export default function NewQuestionPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initialForm = {
    id: 0,
    title: '',
    stem: '',
    explanation: '',
    hint: '',
    resource: '',
    answer_text: '',
    options: ['', '', '', ''],
    answer: 0,
    difficulty: 'medium' as 'easy' | 'medium' | 'hard',
    topic: '',
    topic_id: null,
    tags: [],
    status: 'draft' as 'draft' | 'published' | 'deleted',
    author: '',
    created_at: '',
    updated_at: '',
  };

  async function handleSave(data: any) {
    console.log('[DEBUG] New question handleSave:', data);
    setSaving(true);
    setError(null);
    
    try {
      const payload = {
        title: data.title || '새 문항',
        stem: data.stem || '',
        difficulty: data.difficulty || 'medium',
        topic: data.topic || '수학',
      };
      
      console.log('[DEBUG] Creating question with payload:', payload);
      const result = await createQuestion(payload);
      console.log('[DEBUG] Create result:', result);
      
      if (result && result.id) {
        // 생성 성공 - 편집 페이지로 이동
        router.push(`/questions/${result.id}/edit`);
      } else {
        setError('문항 생성에 실패했습니다.');
      }
    } catch (e: any) {
      console.error('[DEBUG] Create error:', e);
      setError(e.message || '저장 중 오류가 발생했습니다.');
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    router.push('/questions');
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
        initialForm={initialForm}
        onSave={handleSave}
        onCancel={handleCancel}
        saving={saving}
      />
    </div>
  );
}
