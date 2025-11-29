// portal_front/src/pages/ParentDashboard.tsx

import { useState } from "react";

export default function ParentDashboard() {
  const [child, setChild] = useState<string>("");

  return (
    <main className="p-8 space-y-8">
      {/* Header */}
      <header className="space-y-1">
        <h1 className="text-3xl font-semibold">Parent Dashboard</h1>
        <p className="text-gray-500">
          학부모용 간단한 MVP 대시보드입니다. (데이터 연결 예정)
        </p>
      </header>

      {/* Child selector */}
      <section className="border p-4 rounded-lg space-y-3">
        <h2 className="font-semibold text-lg">Select Child</h2>

        <select
          className="border rounded p-2 bg-white dark:bg-gray-800"
          value={child}
          onChange={(e) => setChild(e.target.value)}
        >
          <option value="">— Select —</option>
          <option value="child1">Example Child 1</option>
          <option value="child2">Example Child 2</option>
        </select>
      </section>

      {/* Summary Metrics */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Summary</h2>

        {!child ? (
          <p className="text-gray-500 text-sm">자녀를 선택해주세요.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <SummaryCard label="Current Ability (θ)" value="—" />
            <SummaryCard label="Recent Score" value="—" />
            <SummaryCard label="Study Time (This Month)" value="—" />
          </div>
        )}
      </section>

      {/* Progress Overview */}
      {child && (
        <section className="border rounded-lg p-4 space-y-3">
          <h2 className="font-semibold text-lg">Progress Overview</h2>
          <p className="text-gray-500 text-sm">
            향후 API 연결 예정. 현재는 placeholder입니다.
          </p>
          <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </section>
      )}

      {/* Recent Activity */}
      {child && (
        <section className="border rounded-lg p-4 space-y-3">
          <h2 className="font-semibold text-lg">Recent Activity</h2>
          <ul className="text-sm list-disc list-inside text-gray-700 dark:text-gray-300">
            <li>—</li>
            <li>—</li>
          </ul>
        </section>
      )}
    </main>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="border rounded-lg p-4 text-center">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
    </div>
  );
}
