/**
 * TeacherClassDashboard.tsx
 * 
 * 교사용 반 단위 대시보드
 * 
 * Features:
 * - 반 전체 시험 요약 (평균 점수, 등급 분포)
 * - 학생별 최근 시험 결과 테이블
 * - 학생 상세 페이지로 이동
 * 
 * API: GET /api/dashboard/teacher/classes/{classId}/exams
 */

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Types
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

type ExamSummaryItem = {
  exam_session_id: number;
  student_id: number;
  exam_type: string;
  ended_at: string | null;
  score: number | null;
  grade_numeric: number | null;
  grade_letter: string | null;
};

type StudentSummary = {
  student_id: number;
  latest_exam: {
    exam_session_id: number;
    ended_at: string | null;
    score: number | null;
    grade_numeric: number | null;
    grade_letter: string | null;
  } | null;
  exam_count: number;
};

type ClassExamSummary = {
  class_id: number;
  name: string;
  subject: string;
  student_count: number;
  exam_summary: ExamSummaryItem[];
  students: StudentSummary[];
};

interface TeacherClassDashboardProps {
  classId: number;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Component
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export const TeacherClassDashboard: React.FC<TeacherClassDashboardProps> = ({
  classId,
}) => {
  const [data, setData] = useState<ClassExamSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(
          `/api/dashboard/teacher/classes/${classId}/exams`,
          {
            headers: {
              "Content-Type": "application/json",
              // TODO: Add authentication header
              // Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!res.ok) {
          throw new Error(`Failed to fetch data: ${res.statusText}`);
        }

        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error("Error fetching class dashboard:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId]);

  // ─────────────────────────────────────────────────────────────
  // Loading & Error States
  // ─────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-semibold mb-2">오류 발생</h3>
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-gray-600">데이터가 없습니다.</p>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────
  // Calculate Statistics
  // ─────────────────────────────────────────────────────────────

  const scores = data.exam_summary
    .map((e) => e.score)
    .filter((s): s is number => typeof s === "number");

  const avgScore =
    scores.length > 0
      ? scores.reduce((a, b) => a + b, 0) / scores.length
      : null;

  // Grade distribution
  const gradeDistribution: { [grade: number]: number } = {};
  data.exam_summary.forEach((e) => {
    if (e.grade_numeric !== null) {
      gradeDistribution[e.grade_numeric] =
        (gradeDistribution[e.grade_numeric] || 0) + 1;
    }
  });

  // ─────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────

  return (
    <div className="p-6 space-y-6">
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Header */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-gray-900">
          {data.name}{" "}
          <span className="text-lg text-gray-500 font-normal">
            ({data.subject})
          </span>
        </h1>
        <p className="text-sm text-gray-600">
          학생 수: <span className="font-semibold">{data.student_count}명</span>{" "}
          · 최근 시험 수:{" "}
          <span className="font-semibold">{data.exam_summary.length}건</span>
        </p>
      </header>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Summary Cards */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Average Score */}
        <div className="border border-gray-200 rounded-xl p-6 shadow-sm bg-white hover:shadow-md transition-shadow">
          <h2 className="text-sm font-semibold text-gray-500 mb-2">
            반 평균 점수
          </h2>
          <p className="text-4xl font-bold text-blue-600">
            {avgScore !== null ? avgScore.toFixed(1) : "-"}
            <span className="text-lg text-gray-500 ml-2">점</span>
          </p>
        </div>

        {/* Total Exams */}
        <div className="border border-gray-200 rounded-xl p-6 shadow-sm bg-white hover:shadow-md transition-shadow">
          <h2 className="text-sm font-semibold text-gray-500 mb-2">
            총 시험 수
          </h2>
          <p className="text-4xl font-bold text-green-600">
            {data.exam_summary.length}
            <span className="text-lg text-gray-500 ml-2">건</span>
          </p>
        </div>

        {/* Grade Distribution Preview */}
        <div className="border border-gray-200 rounded-xl p-6 shadow-sm bg-white hover:shadow-md transition-shadow">
          <h2 className="text-sm font-semibold text-gray-500 mb-2">
            등급 분포
          </h2>
          <div className="text-sm text-gray-600 space-y-1">
            {Object.keys(gradeDistribution).length > 0 ? (
              <>
                {Object.entries(gradeDistribution)
                  .sort(([a], [b]) => Number(a) - Number(b))
                  .slice(0, 3)
                  .map(([grade, count]) => (
                    <div key={grade} className="flex justify-between">
                      <span>{grade}등급:</span>
                      <span className="font-semibold">{count}명</span>
                    </div>
                  ))}
                {Object.keys(gradeDistribution).length > 3 && (
                  <div className="text-xs text-gray-400">외 다수...</div>
                )}
              </>
            ) : (
              <p className="text-gray-400">데이터 없음</p>
            )}
          </div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Student Summary Table */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="border border-gray-200 rounded-xl p-6 shadow-sm bg-white">
        <h2 className="text-xl font-semibold mb-4 text-gray-900">
          학생별 최근 시험 요약
        </h2>

        {data.students.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr className="text-left">
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    학생 ID
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    최근 시험 점수
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    최근 등급
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    응시 횟수
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700"></th>
                </tr>
              </thead>
              <tbody>
                {data.students.map((s) => {
                  const latest = s.latest_exam;
                  return (
                    <tr
                      key={s.student_id}
                      className="border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors"
                    >
                      <td className="py-3 px-4 text-gray-900">
                        {s.student_id}
                      </td>
                      <td className="py-3 px-4">
                        {latest?.score != null ? (
                          <span className="font-semibold text-gray-900">
                            {latest.score.toFixed(1)} 점
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {latest?.grade_letter ? (
                          <>
                            <span className="font-semibold text-gray-900">
                              {latest.grade_letter}
                            </span>{" "}
                            {latest.grade_numeric != null && (
                              <span className="text-gray-400 text-xs">
                                ({latest.grade_numeric}등급)
                              </span>
                            )}
                          </>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-gray-900">
                        {s.exam_count}
                      </td>
                      <td className="py-3 px-4">
                        <Link
                          href={`/teacher/dashboard/students/${s.student_id}`}
                          className="text-blue-600 hover:text-blue-800 hover:underline text-sm font-medium"
                        >
                          상세 보기 →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>학생 데이터가 없습니다.</p>
          </div>
        )}
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Info Card */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="border border-blue-200 rounded-xl p-4 bg-blue-50">
        <p className="text-sm text-blue-800">
          💡 <strong>CAT(Computerized Adaptive Testing)</strong> 기반 시험으로
          학생별 최적 난이도 문항을 출제합니다. 각 학생의 세부 성적은 위
          테이블에서 "상세 보기"를 클릭하여 확인하세요.
        </p>
      </section>
    </div>
  );
};

export default TeacherClassDashboard;
