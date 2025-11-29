// portal_front/src/pages/teacher/StudentList.tsx

import { useState } from "react";
import { Link } from "react-router-dom";

// ---- Temporary Mock Data (MVP) ----
// Later replace with: api(`/teachers/${teacherId}/students?...`)
const MOCK_STUDENTS = [
  {
    id: "s1",
    name: "홍길동",
    class_name: "수학 1반",
    ability: "θ = 0.12",
    recent_score: "87%",
    status: "On Track",
  },
  {
    id: "s2",
    name: "이영희",
    class_name: "수학 1반",
    ability: "θ = -0.35",
    recent_score: "62%",
    status: "At Risk",
  },
  {
    id: "s3",
    name: "Tom",
    class_name: "영어 2반",
    ability: "θ = 0.55",
    recent_score: "93%",
    status: "On Track",
  },
];

export default function TeacherStudentsPage() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [classFilter, setClassFilter] = useState("all");

  // simple filtering logic for mock data
  const filtered = MOCK_STUDENTS.filter((s) => {
    const matchQ = q ? s.name.includes(q) : true;
    const matchStatus = status === "all" ? true : s.status === status;
    const matchClass =
      classFilter === "all" ? true : s.class_name === classFilter;
    return matchQ && matchStatus && matchClass;
  });

  return (
    <main className="p-8 space-y-8">
      {/* Header */}
      <header className="space-y-1">
        <h1 className="text-3xl font-semibold">Students</h1>
        <p className="text-gray-500 text-sm">
          선생님용 학생 목록(MVP). 실제 API 연동 전까지는 정적 mock 데이터를 사용합니다.
        </p>
      </header>

      {/* Filters */}
      <section className="border p-4 rounded-lg space-y-4">
        <h2 className="font-semibold text-lg">Filters</h2>

        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by name…"
            className="border rounded p-2 w-full md:w-1/3 bg-white dark:bg-gray-800"
          />

          {/* Class filter (placeholder) */}
          <select
            className="border rounded p-2 w-full md:w-1/4 bg-white dark:bg-gray-800"
            value={classFilter}
            onChange={(e) => setClassFilter(e.target.value)}
          >
            <option value="all">All Classes</option>
            <option value="수학 1반">수학 1반</option>
            <option value="영어 2반">영어 2반</option>
          </select>

          {/* Status filter */}
          <select
            className="border rounded p-2 w-full md:w-1/4 bg-white dark:bg-gray-800"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="On Track">On Track</option>
            <option value="At Risk">At Risk</option>
          </select>
        </div>
      </section>

      {/* Table */}
      <section className="border rounded-lg p-4 space-y-4">
        <h2 className="font-semibold text-lg">Student List</h2>

        {filtered.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No students found. (교사 API 연결 시 실제 학생 목록이 여기에 표시됩니다.)
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b text-left text-sm text-gray-600 dark:text-gray-400">
                  <th className="py-2">Name</th>
                  <th className="py-2">Class</th>
                  <th className="py-2">Ability (θ)</th>
                  <th className="py-2">Recent Score</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Actions</th>
                </tr>
              </thead>

              <tbody>
                {filtered.map((s) => (
                  <tr key={s.id} className="border-b text-sm">
                    <td className="py-2">{s.name}</td>
                    <td className="py-2">{s.class_name}</td>
                    <td className="py-2">{s.ability}</td>
                    <td className="py-2">{s.recent_score}</td>
                    <td className="py-2">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="py-2">
                      <Link
                        to={`/teacher/students/${s.id}`}
                        className="text-blue-600 underline"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Footer note */}
      <p className="text-xs text-gray-400">
        * This is an MVP UI. When /api/teachers/{"{id}"}/students goes live,
        replace mock data with real fetch logic.
      </p>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "At Risk"
      ? "bg-red-200 text-red-800 dark:bg-red-900 dark:text-red-200"
      : "bg-green-200 text-green-800 dark:bg-green-900 dark:text-green-200";
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${color}`}>
      {status}
    </span>
  );
}
