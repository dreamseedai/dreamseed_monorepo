/**
 * TeacherStudentDashboard.tsx
 * 
 * 교사용 개별 학생 시험 히스토리
 * 
 * Features:
 * - 학생의 모든 시험 결과 조회
 * - 점수, 등급, theta, SE 상세 정보
 * - 시험 추이 분석 (점수 변화)
 * 
 * API: GET /api/dashboard/teacher/students/{studentId}/exams
 */

import React, { useEffect, useState } from "react";
import Link from "next/link";

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Types
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

type ExamItem = {
  exam_session_id: number;
  exam_type: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  theta: number | null;
  standard_error: number | null;
  score: number | null;
  grade_numeric: number | null;
  grade_letter: string | null;
};

type StudentExamHistory = {
  student_id: number;
  exams: ExamItem[];
};

interface TeacherStudentDashboardProps {
  studentId: number;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Helper Functions
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getExamTypeLabel = (examType: string): string => {
  const labels: { [key: string]: string } = {
    placement: "배치고사",
    practice: "연습",
    mock: "모의고사",
    official: "정규시험",
  };
  return labels[examType] || examType;
};

const getStatusBadge = (status: string): JSX.Element => {
  const badges: { [key: string]: { color: string; label: string } } = {
    completed: { color: "bg-green-100 text-green-800", label: "완료" },
    in_progress: { color: "bg-yellow-100 text-yellow-800", label: "진행중" },
    abandoned: { color: "bg-gray-100 text-gray-800", label: "중단" },
  };

  const badge = badges[status] || {
    color: "bg-gray-100 text-gray-800",
    label: status,
  };

  return (
    <span
      className={`inline-block px-2 py-1 text-xs font-semibold rounded-full ${badge.color}`}
    >
      {badge.label}
    </span>
  );
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Component
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export const TeacherStudentDashboard: React.FC<
  TeacherStudentDashboardProps
> = ({ studentId }) => {
  const [data, setData] = useState<StudentExamHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(
          `/api/dashboard/teacher/students/${studentId}/exams`,
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
        console.error("Error fetching student history:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

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

  const latest = data.exams[0];
  const completedExams = data.exams.filter((e) => e.status === "completed");

  const scores = completedExams
    .map((e) => e.score)
    .filter((s): s is number => s !== null);

  const avgScore =
    scores.length > 0
      ? scores.reduce((a, b) => a + b, 0) / scores.length
      : null;

  // Score trend (improvement/decline)
  const scoreTrend =
    scores.length >= 2
      ? scores[0] - scores[scores.length - 1]
      : null;

  // ─────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────

  return (
    <div className="p-6 space-y-6">
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Header */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <header className="space-y-2">
        <div className="flex items-center gap-2">
          <Link
            href="/teacher/dashboard"
            className="text-gray-500 hover:text-gray-700"
          >
            ← 돌아가기
          </Link>
        </div>
        <h1 className="text-3xl font-bold text-gray-900">
          학생 {data.student_id} 시험 히스토리
        </h1>
        {latest && (
          <p className="text-sm text-gray-600">
            최근 시험 ({getExamTypeLabel(latest.exam_type)}):{" "}
            {latest.score != null ? (
              <>
                <span className="font-semibold">{latest.score.toFixed(1)}점</span>{" "}
                · 등급: <span className="font-semibold">{latest.grade_letter}</span>
              </>
            ) : (
              <span className="text-gray-400">점수 없음</span>
            )}
          </p>
        )}
      </header>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Summary Cards */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Exams */}
        <div className="border border-gray-200 rounded-xl p-4 shadow-sm bg-white">
          <h2 className="text-xs font-semibold text-gray-500 mb-1">
            총 시험 수
          </h2>
          <p className="text-2xl font-bold text-gray-900">
            {data.exams.length}
            <span className="text-sm text-gray-500 ml-1">건</span>
          </p>
        </div>

        {/* Average Score */}
        <div className="border border-gray-200 rounded-xl p-4 shadow-sm bg-white">
          <h2 className="text-xs font-semibold text-gray-500 mb-1">
            평균 점수
          </h2>
          <p className="text-2xl font-bold text-blue-600">
            {avgScore !== null ? avgScore.toFixed(1) : "-"}
            <span className="text-sm text-gray-500 ml-1">점</span>
          </p>
        </div>

        {/* Latest Score */}
        <div className="border border-gray-200 rounded-xl p-4 shadow-sm bg-white">
          <h2 className="text-xs font-semibold text-gray-500 mb-1">
            최근 점수
          </h2>
          <p className="text-2xl font-bold text-green-600">
            {latest?.score !== null && latest?.score !== undefined
              ? latest.score.toFixed(1)
              : "-"}
            <span className="text-sm text-gray-500 ml-1">점</span>
          </p>
        </div>

        {/* Score Trend */}
        <div className="border border-gray-200 rounded-xl p-4 shadow-sm bg-white">
          <h2 className="text-xs font-semibold text-gray-500 mb-1">
            점수 추이
          </h2>
          {scoreTrend !== null ? (
            <p
              className={`text-2xl font-bold ${
                scoreTrend > 0
                  ? "text-green-600"
                  : scoreTrend < 0
                  ? "text-red-600"
                  : "text-gray-600"
              }`}
            >
              {scoreTrend > 0 ? "+" : ""}
              {scoreTrend.toFixed(1)}
              <span className="text-sm text-gray-500 ml-1">
                {scoreTrend > 0 ? "↑" : scoreTrend < 0 ? "↓" : "→"}
              </span>
            </p>
          ) : (
            <p className="text-2xl font-bold text-gray-400">-</p>
          )}
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Exam History Table */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="border border-gray-200 rounded-xl p-6 shadow-sm bg-white">
        <h2 className="text-xl font-semibold mb-4 text-gray-900">시험 목록</h2>

        {data.exams.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr className="text-left">
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    날짜
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    유형
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    상태
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    점수
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    등급
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    θ (Theta)
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    SE
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.exams.map((e) => (
                  <tr
                    key={e.exam_session_id}
                    className="border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors"
                  >
                    <td className="py-3 px-4 text-gray-900">
                      {formatDate(e.ended_at || e.started_at)}
                    </td>
                    <td className="py-3 px-4 text-gray-700">
                      {getExamTypeLabel(e.exam_type)}
                    </td>
                    <td className="py-3 px-4">{getStatusBadge(e.status)}</td>
                    <td className="py-3 px-4">
                      {e.score != null ? (
                        <span className="font-semibold text-gray-900">
                          {e.score.toFixed(1)}점
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {e.grade_letter ? (
                        <>
                          <span className="font-semibold text-gray-900">
                            {e.grade_letter}
                          </span>{" "}
                          {e.grade_numeric != null && (
                            <span className="text-xs text-gray-400">
                              ({e.grade_numeric}등급)
                            </span>
                          )}
                        </>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-gray-700">
                      {e.theta != null ? e.theta.toFixed(2) : "-"}
                    </td>
                    <td className="py-3 px-4 font-mono text-gray-500">
                      {e.standard_error != null
                        ? e.standard_error.toFixed(2)
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>시험 기록이 없습니다.</p>
          </div>
        )}
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Info Card */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="border border-blue-200 rounded-xl p-4 bg-blue-50">
        <p className="text-sm text-blue-800">
          💡 <strong>θ (Theta)</strong>는 IRT 능력 추정치이며,{" "}
          <strong>SE (Standard Error)</strong>는 추정 정확도입니다. SE가 낮을수록
          더 정확한 측정입니다.
        </p>
      </section>
    </div>
  );
};

export default TeacherStudentDashboard;
