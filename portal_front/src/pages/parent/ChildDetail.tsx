// portal_front/src/pages/parent/ChildDetail.tsx

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// ---- Temporary Mock Child Detail Data (MVP) ----
// 추후 /api/parents/{parentId}/children/{childId} 로 교체
const MOCK_CHILD_DETAIL: Record<
  string,
  {
    id: string;
    name: string;
    grade: string;
    class_name: string;
    abilityTheta: string;
    recentScore: string;
    studyTime: string;
    abilityTrend: { label: string; value: number }[];
    strengths: string[];
    areasToImprove: string[];
    recentActivity: { date: string; description: string }[];
  }
> = {
  c1: {
    id: 'c1',
    name: '홍길동',
    grade: '중3',
    class_name: '수학 심화반',
    abilityTheta: 'θ = 0.25',
    recentScore: '89%',
    studyTime: '12h / month',
    abilityTrend: [
      { label: '4w ago', value: 0.0 },
      { label: '3w ago', value: 0.05 },
      { label: '2w ago', value: 0.12 },
      { label: '1w ago', value: 0.2 },
      { label: 'now', value: 0.25 },
    ],
    strengths: ['도형', '함수 응용', '논리적 사고력'],
    areasToImprove: ['확률', '통계'],
    recentActivity: [
      { date: '2025-11-10', description: '미분·적분 퀴즈 풀이 완료 (90%)' },
      { date: '2025-11-05', description: '극한 개념 복습 학습 완료' },
      { date: '2025-10-30', description: '수열 단원 평가 (88%)' },
    ],
  },
  c2: {
    id: 'c2',
    name: '이영희',
    grade: '중2',
    class_name: '수학 기본반',
    abilityTheta: 'θ = -0.15',
    recentScore: '71%',
    studyTime: '7h / month',
    abilityTrend: [
      { label: '4w ago', value: -0.3 },
      { label: '3w ago', value: -0.25 },
      { label: '2w ago', value: -0.2 },
      { label: '1w ago', value: -0.18 },
      { label: 'now', value: -0.15 },
    ],
    strengths: ['연산', '방정식'],
    areasToImprove: ['도형', '함수 개념'],
    recentActivity: [
      { date: '2025-11-10', description: '중간고사 대비 모의고사 풀이 (68%)' },
      { date: '2025-11-02', description: '함수 개념 동영상 시청' },
    ],
  },
};

export default function ParentChildDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const child = id ? MOCK_CHILD_DETAIL[id] : undefined;

  if (!child) {
    return (
      <main className="p-8 space-y-4">
        <h1 className="text-2xl font-semibold">Child Detail</h1>
        <p className="text-sm text-red-600">
          해당 자녀 정보를 찾을 수 없습니다. (API 연동 후 실제 데이터로 대체 예정)
        </p>
        <button
          onClick={() => navigate('/parent/dashboard')}
          className="mt-4 inline-flex items-center text-blue-600 underline text-sm"
        >
          ← Back to Parent Dashboard
        </button>
      </main>
    );
  }

  return (
    <main className="p-8 space-y-8">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold">{child.name}</h1>
          <p className="text-gray-500 text-sm">
            {child.grade} · {child.class_name}
          </p>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-gray-600">{child.abilityTheta}</span>
            <span className="text-gray-600">· Recent score {child.recentScore}</span>
            <span className="text-gray-600">· Study time {child.studyTime}</span>
          </div>
        </div>

        <div className="flex gap-3 text-sm">
          <button
            onClick={() => navigate('/parent/dashboard')}
            className="inline-flex items-center text-blue-600 underline"
          >
            ← Back to Parent Dashboard
          </button>
        </div>
      </header>

      {/* Main content grid */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Ability trend + strengths / areas */}
        <div className="space-y-6 lg:col-span-2">
          <div className="border rounded-lg p-4 space-y-3">
            <h2 className="font-semibold text-lg">Ability Trend (θ)</h2>
            <p className="text-xs text-gray-500 mb-2">
              예시 데이터입니다. 실제로는 /api/students/{id}/ability-history 와 연동됩니다.
            </p>
            <AbilityTrendChart data={child.abilityTrend} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border rounded-lg p-4 space-y-2">
              <h3 className="font-semibold text-md">Strengths</h3>
              <ul className="text-sm text-gray-700 space-y-1">
                {child.strengths.map((s, i) => (
                  <li key={i}>• {s}</li>
                ))}
              </ul>
            </div>
            <div className="border rounded-lg p-4 space-y-2">
              <h3 className="font-semibold text-md">Areas to Improve</h3>
              <ul className="text-sm text-gray-700 space-y-1">
                {child.areasToImprove.map((s, i) => (
                  <li key={i}>• {s}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Right: Recent Activity */}
        <div className="border rounded-lg p-4 space-y-3">
          <h2 className="font-semibold text-lg">Recent Activity</h2>
          <p className="text-xs text-gray-500">
            최근 학습 활동 로그입니다. 나중에 /api/students/{child.id}/activity 로 연동됩니다.
          </p>
          <ul className="divide-y text-sm">
            {child.recentActivity.map((a, idx) => (
              <li key={idx} className="py-2">
                <div className="font-medium">{a.description}</div>
                <div className="text-xs text-gray-500">{a.date}</div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <p className="text-xs text-gray-400">
        * This is an MVP UI. When parent/child APIs go live, replace mock data with real fetch logic.
      </p>
    </main>
  );
}

/**
 * AbilityTrendChart - 부모용도 teacher용과 동일한 SVG placeholder
 */
function AbilityTrendChart({
  data,
}: {
  data: { label: string; value: number }[];
}) {
  if (!data || data.length === 0) {
    return <p className="text-gray-500 text-sm">No trend data available (MVP).</p>;
  }

  const values = data.map((d) => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

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

        <path d={pathD} fill="none" stroke="#2563EB" strokeWidth={2} strokeLinecap="round" />

        {points.map((p, idx) => (
          <circle key={idx} cx={p.x} cy={p.y} r={3} fill="#2563EB" />
        ))}
      </svg>
      <div className="flex justify-between mt-2 text-xs text-gray-500">
        {points.map((p, idx) => (
          <span key={idx}>{p.label}</span>
        ))}
      </div>
    </div>
  );
}
