/**
 * ParentChildDashboard.tsx
 * 
 * 학부모용 자녀 시험 히스토리
 * 
 * Features:
 * - 자녀의 모든 시험 결과 조회
 * - 점수, 등급, 퍼센타일 정보
 * - 간단한 점수 추이 표시
 * 
 * API: GET /api/dashboard/parent/children/{studentId}/exams
 */

import React, { useEffect, useState } from "react";

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Types
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

type ParentExam = {
  exam_session_id: number;
  exam_type: string;
  date: string;
  score: number | null;
  grade_numeric: number | null;
  grade_letter: string | null;
  percentile: number | null;
};

type ParentChildExams = {
  student_id: number;
  exams: ParentExam[];
};

interface ParentChildDashboardProps {
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

const getGradeBadgeColor = (grade: string): string => {
  const colors: { [key: string]: string } = {
    A: "bg-green-100 text-green-800",
    B: "bg-blue-100 text-blue-800",
    C: "bg-yellow-100 text-yellow-800",
    D: "bg-orange-100 text-orange-800",
    F: "bg-red-100 text-red-800",
  };
  return colors[grade] || "bg-gray-100 text-gray-800";
};

const getPercentileRank = (percentile: number): string => {
  const topPercent = 100 - percentile;
  return `상위 ${topPercent.toFixed(1)}%`;
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Component
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export const ParentChildDashboard: React.FC<ParentChildDashboardProps> = ({
  studentId,
}) => {
  const [data, setData] = useState<ParentChildExams | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(
          `/api/dashboard/parent/children/${studentId}/exams`,
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
        console.error("Error fetching child exams:", err);
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

  const scores = data.exams
    .map((e) => e.score)
    .filter((s): s is number => s !== null);

  const avgScore =
    scores.length > 0
      ? scores.reduce((a, b) => a + b, 0) / scores.length
      : null;

  // Score trend
  const scoreTrend =
    scores.length >= 2 ? scores[0] - scores[scores.length - 1] : null;

  // ─────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────

  return (
    <div className="p-6 space-y-6">
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Header */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">
          자녀 학업 현황
        </h1>
        <p className="text-sm text-gray-600">
          학생 ID: <span className="font-semibold">{data.student_id}</span>
        </p>
      </header>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Latest Exam Highlight */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {latest && (
        <section className="border-2 border-blue-300 rounded-xl p-6 bg-gradient-to-r from-blue-50 to-indigo-50 shadow-lg">
          <h2 className="text-lg font-semibold text-gray-700 mb-3">
            🎯 최근 시험 결과
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Date */}
            <div>
              <p className="text-xs text-gray-500 mb-1">시험 날짜</p>
              <p className="text-sm font-semibold text-gray-900">
                {formatDate(latest.date)}
              </p>
            </div>

            {/* Score */}
            <div>
              <p className="text-xs text-gray-500 mb-1">점수</p>
              <p className="text-2xl font-bold text-blue-600">
                {latest.score !== null ? `${latest.score.toFixed(1)}점` : "-"}
              </p>
            </div>

            {/* Grade */}
            <div>
              <p className="text-xs text-gray-500 mb-1">등급</p>
              {latest.grade_letter ? (
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-block px-3 py-1 text-lg font-bold rounded-lg ${getGradeBadgeColor(
                      latest.grade_letter
                    )}`}
                  >
                    {latest.grade_letter}
                  </span>
                  {latest.grade_numeric && (
                    <span className="text-sm text-gray-500">
                      ({latest.grade_numeric}등급)
                    </span>
                  )}
                </div>
              ) : (
                <span className="text-gray-400">-</span>
              )}
            </div>

            {/* Percentile */}
            <div>
              <p className="text-xs text-gray-500 mb-1">석차</p>
              <p className="text-lg font-semibold text-green-600">
                {latest.percentile !== null
                  ? getPercentileRank(latest.percentile)
                  : "-"}
              </p>
            </div>
          </div>
        </section>
      )}

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Summary Cards */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Total Exams */}
        <div className="border border-gray-200 rounded-xl p-4 shadow-sm bg-white">
          <h2 className="text-sm font-semibold text-gray-500 mb-1">
            총 시험 수
          </h2>
          <p className="text-3xl font-bold text-gray-900">
            {data.exams.length}
            <span className="text-base text-gray-500 ml-1">건</span>
          </p>
        </div>

        {/* Average Score */}
        <div className="border border-gray-200 rounded-xl p-4 shadow-sm bg-white">
          <h2 className="text-sm font-semibold text-gray-500 mb-1">
            평균 점수
          </h2>
          <p className="text-3xl font-bold text-blue-600">
            {avgScore !== null ? avgScore.toFixed(1) : "-"}
            <span className="text-base text-gray-500 ml-1">점</span>
          </p>
        </div>

        {/* Score Trend */}
        <div className="border border-gray-200 rounded-xl p-4 shadow-sm bg-white">
          <h2 className="text-sm font-semibold text-gray-500 mb-1">
            성적 변화
          </h2>
          {scoreTrend !== null ? (
            <div className="flex items-baseline gap-2">
              <p
                className={`text-3xl font-bold ${
                  scoreTrend > 0
                    ? "text-green-600"
                    : scoreTrend < 0
                    ? "text-red-600"
                    : "text-gray-600"
                }`}
              >
                {scoreTrend > 0 ? "+" : ""}
                {scoreTrend.toFixed(1)}
              </p>
              <span
                className={`text-2xl ${
                  scoreTrend > 0
                    ? "text-green-600"
                    : scoreTrend < 0
                    ? "text-red-600"
                    : "text-gray-600"
                }`}
              >
                {scoreTrend > 0 ? "↑" : scoreTrend < 0 ? "↓" : "→"}
              </span>
            </div>
          ) : (
            <p className="text-3xl font-bold text-gray-400">-</p>
          )}
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Exam History Table */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="border border-gray-200 rounded-xl p-6 shadow-sm bg-white">
        <h2 className="text-xl font-semibold mb-4 text-gray-900">
          시험 기록
        </h2>

        {data.exams.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr className="text-left">
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    날짜
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    시험 종류
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    점수
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    등급
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    석차
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.exams.map((e, idx) => (
                  <tr
                    key={e.exam_session_id}
                    className={`border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors ${
                      idx === 0 ? "bg-blue-50" : ""
                    }`}
                  >
                    <td className="py-3 px-4 text-gray-900">
                      {formatDate(e.date)}
                      {idx === 0 && (
                        <span className="ml-2 text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">
                          최신
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-gray-700">
                      {getExamTypeLabel(e.exam_type)}
                    </td>
                    <td className="py-3 px-4">
                      {e.score !== null ? (
                        <span className="font-semibold text-gray-900">
                          {e.score.toFixed(1)}점
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {e.grade_letter ? (
                        <div className="flex items-center gap-2">
                          <span
                            className={`inline-block px-2 py-1 text-sm font-bold rounded ${getGradeBadgeColor(
                              e.grade_letter
                            )}`}
                          >
                            {e.grade_letter}
                          </span>
                          {e.grade_numeric && (
                            <span className="text-xs text-gray-400">
                              ({e.grade_numeric}등급)
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {e.percentile !== null ? (
                        <span className="font-medium text-green-600">
                          {getPercentileRank(e.percentile)}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
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
      <section className="border border-green-200 rounded-xl p-4 bg-green-50">
        <p className="text-sm text-green-800">
          💡 <strong>CAT(컴퓨터 적응형 시험)</strong>은 학생의 실력에 맞춰
          문제 난이도를 자동 조절하여 정확한 실력 측정을 제공합니다. 석차는
          같은 난이도 기준으로 환산된 백분위 순위입니다.
        </p>
      </section>
    </div>
  );
};

export default ParentChildDashboard;
