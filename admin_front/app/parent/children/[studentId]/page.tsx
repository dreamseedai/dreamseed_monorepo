"use client";

/**
 * Parent Child Dashboard Page
 * 
 * Route: /parent/children/[studentId]
 * 
 * Shows:
 * - Child's latest exam highlight
 * - All exam history with scores, grades, percentiles
 * - Performance statistics
 */

import { useParams } from "next/navigation";
import { useParentChildExams } from "@/lib/hooks/useDashboard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { LoadingSpinner, ErrorMessage } from "@/components/ui/LoadingSpinner";

export default function ParentChildDashboardPage() {
  const params = useParams<{ studentId: string }>();
  const studentId = params?.studentId;
  const { data, isLoading, isError, error } = useParentChildExams(studentId);

  if (isLoading) return <LoadingSpinner />;
  if (isError)
    return (
      <ErrorMessage
        message={error instanceof Error ? error.message : "데이터를 불러올 수 없습니다."}
      />
    );
  if (!data) return <ErrorMessage message="데이터가 없습니다." />;

  const latest = data.exams[0];
  const scores = data.exams
    .map((e) => e.score)
    .filter((s): s is number => s !== null);
  const avgScore =
    scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : null;
  const scoreTrend =
    scores.length >= 2 ? scores[0] - scores[scores.length - 1] : null;

  // Format exam type
  const getExamTypeLabel = (type: string) => {
    const labels: { [key: string]: string } = {
      placement: "배치고사",
      practice: "연습",
      mock: "모의고사",
      official: "정규시험",
    };
    return labels[type] || type;
  };

  // Grade badge color
  const getGradeBadgeColor = (grade: string) => {
    const colors: { [key: string]: string } = {
      A: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
      B: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
      C: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
      D: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
      F: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    };
    return colors[grade] || "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
  };

  // Percentile rank
  const getPercentileRank = (percentile: number) => {
    const topPercent = 100 - percentile;
    return `상위 ${topPercent.toFixed(1)}%`;
  };

  return (
    <div className="space-y-6">
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Page Header */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <PageHeader
        title="자녀 학업 현황"
        subtitle={`학생 ID: ${data.student_id}`}
        rightSlot={
          <span className="text-xs rounded-full bg-slate-100 dark:bg-gray-700 px-3 py-1.5 text-slate-600 dark:text-gray-300 font-medium">
            DreamSeed CAT · 학부모 대시보드
          </span>
        }
      />

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Latest Exam Highlight */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {latest && (
        <Card className="border-2 border-sky-300 dark:border-sky-700 bg-gradient-to-r from-sky-50 to-indigo-50 dark:from-sky-950 dark:to-indigo-950">
          <h2 className="text-base font-semibold text-slate-700 dark:text-gray-200 mb-3">
            🎯 최근 시험 결과
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Date */}
            <div>
              <p className="text-xs text-slate-500 dark:text-gray-400 mb-1">
                시험 날짜
              </p>
              <p className="text-sm font-semibold text-slate-900 dark:text-gray-100">
                {new Date(latest.date).toLocaleDateString("ko-KR")}
              </p>
            </div>

            {/* Score */}
            <div>
              <p className="text-xs text-slate-500 dark:text-gray-400 mb-1">점수</p>
              <p className="text-2xl font-bold text-sky-600 dark:text-sky-400">
                {latest.score !== null ? `${latest.score.toFixed(1)}점` : "-"}
              </p>
            </div>

            {/* Grade */}
            <div>
              <p className="text-xs text-slate-500 dark:text-gray-400 mb-1">등급</p>
              {latest.grade_letter ? (
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-block px-3 py-1 text-base font-bold rounded-lg ${getGradeBadgeColor(
                      latest.grade_letter
                    )}`}
                  >
                    {latest.grade_letter}
                  </span>
                  {latest.grade_numeric && (
                    <span className="text-sm text-slate-500 dark:text-gray-400">
                      ({latest.grade_numeric}등급)
                    </span>
                  )}
                </div>
              ) : (
                <span className="text-slate-400 dark:text-gray-500">-</span>
              )}
            </div>

            {/* Percentile */}
            <div>
              <p className="text-xs text-slate-500 dark:text-gray-400 mb-1">석차</p>
              <p className="text-base font-semibold text-green-600 dark:text-green-400">
                {latest.percentile !== null
                  ? getPercentileRank(latest.percentile)
                  : "-"}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Summary Cards */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Total Exams */}
        <Card>
          <h2 className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-2">
            총 시험 수
          </h2>
          <p className="text-3xl font-semibold text-slate-900 dark:text-gray-100">
            {data.exams.length}
            <span className="text-base text-slate-400 dark:text-gray-500 ml-1">건</span>
          </p>
        </Card>

        {/* Average Score */}
        <Card>
          <h2 className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-2">
            평균 점수
          </h2>
          <p className="text-3xl font-semibold text-sky-600 dark:text-sky-400">
            {avgScore !== null ? avgScore.toFixed(1) : "-"}
            <span className="text-base text-slate-400 dark:text-gray-500 ml-1">점</span>
          </p>
        </Card>

        {/* Score Trend */}
        <Card>
          <h2 className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-2">
            성적 변화
          </h2>
          {scoreTrend !== null ? (
            <div className="flex items-baseline gap-2">
              <p
                className={`text-3xl font-semibold ${
                  scoreTrend > 0
                    ? "text-green-600 dark:text-green-400"
                    : scoreTrend < 0
                    ? "text-red-600 dark:text-red-400"
                    : "text-slate-600 dark:text-gray-400"
                }`}
              >
                {scoreTrend > 0 ? "+" : ""}
                {scoreTrend.toFixed(1)}
              </p>
              <span
                className={`text-2xl ${
                  scoreTrend > 0
                    ? "text-green-600 dark:text-green-400"
                    : scoreTrend < 0
                    ? "text-red-600 dark:text-red-400"
                    : "text-slate-600 dark:text-gray-400"
                }`}
              >
                {scoreTrend > 0 ? "↑" : scoreTrend < 0 ? "↓" : "→"}
              </span>
            </div>
          ) : (
            <p className="text-3xl font-semibold text-slate-400 dark:text-gray-500">-</p>
          )}
        </Card>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Exam History Table */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <Card>
        <h2 className="text-base font-semibold text-slate-700 dark:text-gray-200 mb-4">
          시험 기록
        </h2>
        {data.exams.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="border-b border-slate-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-800/50">
                <tr className="text-left text-slate-500 dark:text-gray-400">
                  <th className="py-3 px-4 font-semibold">날짜</th>
                  <th className="py-3 px-4 font-semibold">시험 종류</th>
                  <th className="py-3 px-4 font-semibold">점수</th>
                  <th className="py-3 px-4 font-semibold">등급</th>
                  <th className="py-3 px-4 font-semibold">석차</th>
                </tr>
              </thead>
              <tbody>
                {data.exams.map((e, idx) => (
                  <tr
                    key={e.exam_session_id}
                    className={`border-b border-slate-100 dark:border-gray-700 hover:bg-slate-50 dark:hover:bg-gray-800/30 transition-colors ${
                      idx === 0 ? "bg-sky-50 dark:bg-sky-900/20" : ""
                    }`}
                  >
                    <td className="py-3 px-4 text-slate-900 dark:text-gray-100">
                      {new Date(e.date).toLocaleDateString("ko-KR")}
                      {idx === 0 && (
                        <span className="ml-2 text-xs bg-sky-600 dark:bg-sky-500 text-white px-2 py-0.5 rounded-full">
                          최신
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-700 dark:text-gray-300">
                      {getExamTypeLabel(e.exam_type)}
                    </td>
                    <td className="py-3 px-4">
                      {e.score !== null ? (
                        <span className="font-semibold text-slate-900 dark:text-gray-100">
                          {e.score.toFixed(1)}점
                        </span>
                      ) : (
                        <span className="text-slate-400 dark:text-gray-500">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {e.grade_letter ? (
                        <div className="flex items-center gap-2">
                          <span
                            className={`inline-block px-2 py-0.5 text-sm font-bold rounded ${getGradeBadgeColor(
                              e.grade_letter
                            )}`}
                          >
                            {e.grade_letter}
                          </span>
                          {e.grade_numeric && (
                            <span className="text-xs text-slate-400 dark:text-gray-500">
                              ({e.grade_numeric}등급)
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-400 dark:text-gray-500">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {e.percentile !== null ? (
                        <span className="font-medium text-green-600 dark:text-green-400">
                          {getPercentileRank(e.percentile)}
                        </span>
                      ) : (
                        <span className="text-slate-400 dark:text-gray-500">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-500 dark:text-gray-400">
            <p>시험 기록이 없습니다.</p>
          </div>
        )}
      </Card>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Info Card */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <Card className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
        <p className="text-sm text-green-800 dark:text-green-300">
          💡 <strong>CAT(컴퓨터 적응형 시험)</strong>은 학생의 실력에 맞춰 문제
          난이도를 자동 조절하여 정확한 실력 측정을 제공합니다. 석차는 같은
          난이도 기준으로 환산된 백분위 순위입니다.
        </p>
      </Card>
    </div>
  );
}
