// portal_front/src/pages/TeacherDashboard.tsx

import { Link } from "react-router-dom";

export default function TeacherDashboard() {
  return (
    <main className="p-8 space-y-8">
      {/* Header */}
      <header className="space-y-1">
        <h1 className="text-3xl font-semibold">Teacher Dashboard</h1>
        <p className="text-gray-500">
          선생님용 간단한 MVP 대시보드입니다. (데이터 연결 예정)
        </p>
      </header>

      {/* Summary Cards */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Summary</h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <SummaryCard label="Total Students" value="—" />
          <SummaryCard label="Active Classes" value="—" />
          <SummaryCard label="Average Performance" value="—" />
          <SummaryCard label="At-risk Students" value="—" />
        </div>
      </section>

      {/* Current Session */}
      <section className="border rounded-lg p-4 space-y-3">
        <h2 className="font-semibold text-lg">Current Session</h2>

        <p className="text-sm text-gray-600">
          Here you will see the active session a teacher is reviewing.
        </p>

        <div className="flex gap-4 text-sm">
          <Link
            to="/exam/player?session=example"
            className="text-blue-600 underline"
          >
            Open Exam Player
          </Link>

          <Link
            to="/exam/report.pdf?session=example"
            className="text-blue-600 underline"
          >
            Download PDF Report
          </Link>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="border rounded-lg p-4 space-y-3">
        <h2 className="font-semibold text-lg">Quick Actions</h2>

        <ul className="list-disc list-inside text-sm text-gray-700 dark:text-gray-300 space-y-1">
          <li>
            <span className="text-gray-500">View Student List (coming soon)</span>
          </li>
          <li>
            <span className="text-gray-500">View Reports (coming soon)</span>
          </li>
        </ul>
      </section>
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
