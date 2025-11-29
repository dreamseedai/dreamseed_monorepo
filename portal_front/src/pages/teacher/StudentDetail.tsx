// portal_front/src/pages/teacher/StudentDetail.tsx

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// ---- Temporary Mock Detail Data (MVP) ----
// 나중에 /api/teachers/{teacherId}/students/{studentId} 에서 가져오도록 교체
const MOCK_STUDENT_DETAIL: Record<
  string,
  {
    id: string;
    name: string;
    class_name: string;
    status: 'On Track' | 'At Risk';
    abilityTheta: string;
    recentScore: string;
    recentTests: { date: string; name: string; score: string }[];
    abilityTrend: { label: string; value: number }[]; // 간단한 추이 (예: 최근 5주)
    riskFlags: string[];
  }
> = {
  s1: {
    id: 's1',
    name: '홍길동',
    class_name: '수학 1반',
    status: 'On Track',
    abilityTheta: 'θ = 0.12',
    recentScore: '87%',
    recentTests: [
      { date: '2025-11-10', name: '미분·적분 퀴즈', score: '90%' },
      { date: '2025-11-05', name: '극한 개념 테스트', score: '85%' },
      { date: '2025-10-30', name: '수열 단원평가', score: '88%' },
    ],
    abilityTrend: [
      { label: '4w ago', value: -0.2 },
      { label: '3w ago', value: -0.05 },
      { label: '2w ago', value: 0.0 },
      { label: '1w ago', value: 0.08 },
      { label: 'now', value: 0.12 },
    ],
    riskFlags: ['최근 결석 없음', '추세 안정적'],
  },
  s2: {
    id: 's2',
    name: '이영희',
    class_name: '수학 1반',
    status: 'At Risk',
    abilityTheta: 'θ = -0.35',
    recentScore: '62%',
    recentTests: [
      { date: '2025-11-10', name: '미분·적분 퀴즈', score: '58%' },
      { date: '2025-11-05', name: '극한 개념 테스트', score: '65%' },
      { date: '2025-10-30', name: '수열 단원평가', score: '63%' },
    ],
    abilityTrend: [
      { label: '4w ago', value: -0.1 },
      { label: '3w ago', value: -0.15 },
      { label: '2w ago', value: -0.25 },
      { label: '1w ago', value: -0.3 },
      { label: 'now', value: -0.35 },
    ],
    riskFlags: ['최근 4주 연속 하락', '평균 점수 70% 이하'],
  },
  s3: {
    id: 's3',
    name: 'Tom',
    class_name: '수학 2반',
    status: 'On Track',
    abilityTheta: 'θ = 0.25',
    recentScore: '92%',
    recentTests: [
      { date: '2025-11-12', name: '벡터 응용 퀴즈', score: '95%' },
      { date: '2025-11-07', name: '기하 단원평가', score: '90%' },
      { date: '2025-11-01', name: '삼각함수 테스트', score: '91%' },
    ],
    abilityTrend: [
      { label: '4w ago', value: 0.15 },
      { label: '3w ago', value: 0.18 },
      { label: '2w ago', value: 0.20 },
      { label: '1w ago', value: 0.23 },
      { label: 'now', value: 0.25 },
    ],
    riskFlags: ['우수 학생', '상향 추세 지속'],
  },
};

export default function TeacherStudentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const student = id ? MOCK_STUDENT_DETAIL[id] : undefined;

  if (!student) {
    return (
      <main className="p-8 space-y-4">
        <h1 className="text-2xl font-semibold">Student Detail</h1>
        <p className="text-sm text-red-600">
          해당 학생 정보를 찾을 수 없습니다. (API 연동 후 실제 데이터로 대체 예정)
        </p>
        <button
          onClick={() => navigate('/teacher/students')}
          className="mt-4 inline-flex items-center text-blue-600 underline text-sm"
        >
          ← Back to Students
        </button>
      </main>
    );
  }

  return (
    <main className="p-8 space-y-8">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold">{student.name}</h1>
          <p className="text-gray-500 text-sm">Class: {student.class_name}</p>
          <div className="flex items-center gap-2 text-sm">
            <StatusBadge status={student.status} />
            <span className="text-gray-500">{student.abilityTheta}</span>
            <span className="text-gray-500">· Recent score {student.recentScore}</span>
          </div>
        </div>

        <div className="flex gap-3 text-sm">
          <button
            onClick={() => navigate('/teacher/students')}
            className="inline-flex items-center text-blue-600 underline"
          >
            ← Back to Students
          </button>
        </div>
      </header>

      {/* Main content grid */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Ability trend + risk flags */}
        <div className="space-y-6 lg:col-span-2">
          <div className="border rounded-lg p-4 space-y-3">
            <h2 className="font-semibold text-lg">Ability Trend (θ)</h2>
            <p className="text-xs text-gray-500 mb-2">
              실제 데이터 연동 전까지는 예시 값입니다. 나중에 /api/students/{id}/ability-history로 연결 예정.
            </p>
            <AbilityTrendChart data={student.abilityTrend} />
          </div>

          <div className="border rounded-lg p-4 space-y-3">
            <h2 className="font-semibold text-lg">Risk Signals</h2>
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
              {student.riskFlags.map((rf, i) => (
                <li key={i}>{rf}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right: Recent tests */}
        <div className="border rounded-lg p-4 space-y-3">
          <h2 className="font-semibold text-lg">Recent Tests</h2>
          <p className="text-xs text-gray-500">
            최근 평가 기록입니다. 후에 /api/students/{student.id}/performance와 연동합니다.
          </p>
          <ul className="divide-y text-sm">
            {student.recentTests.map((t, idx) => (
              <li key={idx} className="py-2 flex flex-col">
                <span className="font-medium">{t.name}</span>
                <span className="text-gray-500 text-xs">
                  {t.date} · {t.score}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Footer note */}
      <p className="text-xs text-gray-400">
        * This is an MVP UI. When teacher/student APIs go live, replace mock data with real fetch logic.
      </p>
    </main>
  );
}

function StatusBadge({ status }: { status: 'On Track' | 'At Risk' }) {
  const isRisk = status === 'At Risk';
  const color = isRisk
    ? 'bg-red-100 text-red-800 border-red-200'
    : 'bg-green-100 text-green-800 border-green-200';
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium ${color}`}
    >
      {status}
    </span>
  );
}

/**
 * AbilityTrendChart
 * - 간단한 SVG 기반 placeholder 라인 차트
 * - 실제 데이터 연동 전까지 시각적 구조만 제공
 */
function AbilityTrendChart({
  data,
}: {
  data: { label: string; value: number }[];
}) {
  if (!data || data.length === 0) {
    return <p className="text-gray-500 text-sm">No trend data available (MVP).</p>;
  }

  // value 범위 계산 (간단히 min/max만)
  const values = data.map((d) => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  // SVG 크기
  const width = 280;
  const height = 120;
  const paddingX = 16;
  const paddingY = 10;

  const points = data.map((d, idx) => {
    const x = paddingX + (idx / Math.max(data.length - 1, 1)) * (width - paddingX * 2);
    const normalized = (d.value - min) / range;
    const y = height - paddingY - normalized * (height - paddingY * 2);
    return { x, y, label: d.label, value: d.value };
  });

  const pathD = points.map((p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ');

  return (
    <div className="w-full overflow-x-auto">
      <svg width={width} height={height} className="border rounded bg-white dark:bg-slate-900">
        {/* 축/배경 (간단히) */}
        <line
          x1={paddingX}
          y1={height - paddingY}
          x2={width - paddingX}
          y2={height - paddingY}
          stroke="#CBD5E1"
          strokeWidth={1}
        />
        <line
          x1={paddingX}
          y1={paddingY}
          x2={paddingX}
          y2={height - paddingY}
          stroke="#CBD5E1"
          strokeWidth={1}
        />

        {/* 라인 */}
        <path d={pathD} fill="none" stroke="#2563EB" strokeWidth={2} strokeLinecap="round" />

        {/* 포인트 */}
        {points.map((p, idx) => (
          <g key={idx}>
            <circle cx={p.x} cy={p.y} r={3} fill="#2563EB" />
          </g>
        ))}
      </svg>

      {/* 라벨 */}
      <div className="flex justify-between mt-2 text-xs text-gray-500">
        {points.map((p, idx) => (
          <span key={idx}>{p.label}</span>
        ))}
      </div>
    </div>
  );
}
