// portal_front/src/pages/tutor/SessionDetail.tsx

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// /tutor/sessions 페이지와 동일한 기준의 mock detail
const MOCK_SESSION_DETAIL: Record<
  string,
  {
    id: string;
    date: string;
    studentName: string;
    subject: string;
    topic: string;
    status: 'Completed' | 'Upcoming';
    duration: string;
    notes: string;
    tasks: { label: string; done: boolean }[];
  }
> = {
  sess1: {
    id: 'sess1',
    date: '2025-11-10',
    studentName: '홍길동',
    subject: '수학',
    topic: '미분·적분',
    status: 'Completed',
    duration: '90 min',
    notes: '개념 이해는 양호, 문제 풀이 속도를 조금 더 올릴 필요 있음.',
    tasks: [
      { label: '교과서 예제 5개 풀이', done: true },
      { label: '심화 문제 3개 풀이', done: true },
      { label: '개념 요약 정리 복습', done: false },
    ],
  },
  sess2: {
    id: 'sess2',
    date: '2025-11-08',
    studentName: '이영희',
    subject: '수학',
    topic: '함수 개념',
    status: 'Upcoming',
    duration: '60 min',
    notes: '함수 개념 재정리 및 그래프 해석 연습 예정.',
    tasks: [
      { label: '이전 세션 복습 체크', done: false },
      { label: '새 예제 풀이 준비', done: false },
    ],
  },
  sess3: {
    id: 'sess3',
    date: '2025-11-05',
    studentName: 'Tom',
    subject: '영어',
    topic: 'Reading',
    status: 'Completed',
    duration: '75 min',
    notes: 'Reading comprehension 향상. Vocabulary 추가 학습 필요.',
    tasks: [
      { label: 'Passage 3개 읽기', done: true },
      { label: 'Vocabulary quiz', done: true },
      { label: 'Writing exercise', done: true },
    ],
  },
};

export default function TutorSessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const sess = id ? MOCK_SESSION_DETAIL[id] : undefined;

  if (!sess) {
    return (
      <main className="p-8 space-y-4">
        <h1 className="text-2xl font-semibold">Session Detail</h1>
        <p className="text-sm text-red-600">
          해당 세션 정보를 찾을 수 없습니다. (API 연동 후 실제 데이터로 대체 예정)
        </p>
        <button
          onClick={() => navigate('/tutor/sessions')}
          className="mt-4 inline-flex items-center text-blue-600 underline text-sm"
        >
          ← Back to Sessions
        </button>
      </main>
    );
  }

  return (
    <main className="p-8 space-y-8">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold">Session with {sess.studentName}</h1>
          <p className="text-gray-500 text-sm">
            {sess.date} · {sess.subject} · {sess.topic}
          </p>
          <div className="flex items-center gap-2 text-sm">
            <StatusPill status={sess.status} />
            <span className="text-gray-600">· Duration {sess.duration}</span>
          </div>
        </div>

        <div className="flex gap-3 text-sm">
          <button
            onClick={() => navigate('/tutor/sessions')}
            className="inline-flex items-center text-blue-600 underline"
          >
            ← Back to Sessions
          </button>
        </div>
      </header>

      {/* Main content */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Notes */}
        <div className="border rounded-lg p-4 space-y-3 lg:col-span-2">
          <h2 className="font-semibold text-lg">Session Notes</h2>
          <p className="text-sm text-gray-700 whitespace-pre-line">{sess.notes}</p>
        </div>

        {/* Tasks */}
        <div className="border rounded-lg p-4 space-y-3">
          <h2 className="font-semibold text-lg">Planned Tasks</h2>
          <ul className="text-sm space-y-2">
            {sess.tasks.map((t, idx) => (
              <li key={idx} className="flex items-center gap-2">
                <span
                  className={`inline-flex w-3 h-3 rounded-full ${
                    t.done ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                ></span>
                <span className={t.done ? 'line-through text-gray-400' : undefined}>
                  {t.label}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <p className="text-xs text-gray-400">
        * This is an MVP UI. When tutor/session APIs go live, replace mock data with real fetch logic.
      </p>
    </main>
  );
}

function StatusPill({ status }: { status: 'Completed' | 'Upcoming' }) {
  const color =
    status === 'Upcoming'
      ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
      : 'bg-green-100 text-green-800 border-green-200';
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium ${color}`}
    >
      {status}
    </span>
  );
}
