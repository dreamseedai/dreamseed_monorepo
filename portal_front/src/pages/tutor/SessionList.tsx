// portal_front/src/pages/tutor/SessionList.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';

// 나중에 /api/tutors/{id}/sessions 로 교체할 수 있는 mock 데이터
const MOCK_SESSIONS = [
  {
    id: 'sess1',
    date: '2025-11-10',
    studentName: '홍길동',
    subject: '수학',
    topic: '미분·적분',
    status: 'Completed',
  },
  {
    id: 'sess2',
    date: '2025-11-08',
    studentName: '이영희',
    subject: '수학',
    topic: '함수 개념',
    status: 'Upcoming',
  },
  {
    id: 'sess3',
    date: '2025-11-05',
    studentName: 'Tom',
    subject: '영어',
    topic: 'Reading',
    status: 'Completed',
  },
];

export default function TutorSessionsPage() {
  const navigate = useNavigate();

  return (
    <main className="p-8 space-y-8">
      {/* Header */}
      <header className="space-y-1">
        <h1 className="text-3xl font-semibold">Tutor Sessions</h1>
        <p className="text-gray-500 text-sm">
          과외 세션 목록(MVP). 나중에 튜터용 API와 연결됩니다.
        </p>
      </header>

      {/* Sessions table */}
      <section className="border rounded-lg p-4 space-y-4">
        <h2 className="font-semibold text-lg">Session List</h2>

        {MOCK_SESSIONS.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No sessions yet. 학생과의 학습 세션이 생성되면 여기 표시됩니다.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b text-left text-gray-600 dark:text-gray-400">
                  <th className="py-2">Date</th>
                  <th className="py-2">Student</th>
                  <th className="py-2">Subject</th>
                  <th className="py-2">Topic</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_SESSIONS.map((s) => (
                  <tr key={s.id} className="border-b hover:bg-gray-50 dark:hover:bg-slate-800">
                    <td className="py-2">{s.date}</td>
                    <td className="py-2">{s.studentName}</td>
                    <td className="py-2">{s.subject}</td>
                    <td className="py-2">{s.topic}</td>
                    <td className="py-2">
                      <StatusPill status={s.status} />
                    </td>
                    <td className="py-2">
                      <button
                        onClick={() => navigate(`/tutor/sessions/${s.id}`)}
                        className="text-blue-600 underline"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="text-xs text-gray-400">
        * This is an MVP. When tutor/session APIs go live, replace mock data with real fetch logic.
      </p>
    </main>
  );
}

function StatusPill({ status }: { status: string }) {
  const isUpcoming = status === 'Upcoming';
  const color = isUpcoming
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
