"use client";

/**
 * Teacher Student Dashboard Page
 * 
 * Route: /teacher/students/[studentId]
 * 
 * Shows:
 * - Student exam history
 * - All exam details (score, grade, theta, SE)
 * - Performance statistics
 */

import { useParams } from "next/navigation";
import Link from "next/link";
import { useTeacherStudentExams } from "@/lib/hooks/useDashboard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { LoadingSpinner, ErrorMessage } from "@/components/ui/LoadingSpinner";

export default function TeacherStudentDashboardPage() {
  const params = useParams<{ studentId: string }>();
  const studentId = params?.studentId;
  const { data, isLoading, isError, error } = useTeacherStudentExams(studentId);

  if (isLoading) return <LoadingSpinner />;
  if (isError)
    return (
      <ErrorMessage
        message={error instanceof Error ? error.message : "데이터를 불러올 수 없습니다."}
      />
    );
  if (!data) return <ErrorMessage message="데이터가 없습니다." />;

  const latest = data.exams[0];
  const completedExams = data.exams.filter((e) => e.status === "completed");

  // Calculate statistics
  const scores = completedExams
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

  // Status badge
  const getStatusBadge = (status: string) => {
    const badges: { [key: string]: { color: string; label: string } } = {
      completed: { color: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400", label: "완료" },
      in_progress: { color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400", label: "진행중" },
      abandoned: { color: "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300", label: "중단" },
    };
    const badge = badges[status] || badges.abandoned;
    return (
      <span className={`inline-block px-2 py-0.5 text-xs font-semibold rounded-full ${badge.color}`}>
        {badge.label}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Back Link & Page Header */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <div>
        <Link
          href="/teacher/dashboard"
          className="text-sm text-sky-600 dark:text-sky-400 hover:underline mb-2 inline-block"
        >
          ← 대시보드로 돌아가기
        </Link>
      </div>

      <PageHeader
        title={`학생 ${data.student_id} 시험 히스토리`}
        subtitle={
          latest
            ? `최근 시험 (${getExamTypeLabel(latest.exam_type)}): ${
                latest.score != null ? `${latest.score.toFixed(1)}점` : "-"
              } · 등급: ${latest.grade_letter ?? "-"}`
            : "시험 기록이 없습니다."
        }
      />

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Statistics Cards */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Exams */}
        <Card>
          <h2 className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-1">
            총 시험 수
          </h2>
          <p className="text-2xl font-semibold text-slate-900 dark:text-gray-100">
            {data.exams.length}
            <span className="text-sm text-slate-400 dark:text-gray-500 ml-1">건</span>
          </p>
        </Card>

        {/* Average Score */}
        <Card>
          <h2 className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-1">
            평균 점수
          </h2>
          <p className="text-2xl font-semibold text-sky-600 dark:text-sky-400">
            {avgScore !== null ? avgScore.toFixed(1) : "-"}
            <span className="text-sm text-slate-400 dark:text-gray-500 ml-1">점</span>
          </p>
        </Card>

        {/* Latest Score */}
        <Card>
          <h2 className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-1">
            최근 점수
          </h2>
          <p className="text-2xl font-semibold text-green-600 dark:text-green-400">
            {latest?.score !== null && latest?.score !== undefined
              ? latest.score.toFixed(1)
              : "-"}
            <span className="text-sm text-slate-400 dark:text-gray-500 ml-1">점</span>
          </p>
        </Card>

        {/* Score Trend */}
        <Card>
          <h2 className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-1">
            점수 추이
          </h2>
          {scoreTrend !== null ? (
            <p
              className={`text-2xl font-semibold ${
                scoreTrend > 0
                  ? "text-green-600 dark:text-green-400"
                  : scoreTrend < 0
                  ? "text-red-600 dark:text-red-400"
                  : "text-slate-600 dark:text-gray-400"
              }`}
            >
              {scoreTrend > 0 ? "+" : ""}
              {scoreTrend.toFixed(1)}
              <span className="text-base ml-1">
                {scoreTrend > 0 ? "↑" : scoreTrend < 0 ? "↓" : "→"}
              </span>
            </p>
          ) : (
            <p className="text-2xl font-semibold text-slate-400 dark:text-gray-500">-</p>
          )}
        </Card>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Exam History Table */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <Card>
        <h2 className="text-base font-semibold text-slate-700 dark:text-gray-200 mb-4">
          시험 목록
        </h2>
        {data.exams.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="border-b border-slate-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-800/50">
                <tr className="text-left text-slate-500 dark:text-gray-400">
                  <th className="py-3 px-4 font-semibold">날짜</th>
                  <th className="py-3 px-4 font-semibold">유형</th>
                  <th className="py-3 px-4 font-semibold">상태</th>
                  <th className="py-3 px-4 font-semibold">점수</th>
                  <th className="py-3 px-4 font-semibold">등급</th>
                  <th className="py-3 px-4 font-semibold">θ (Theta)</th>
                  <th className="py-3 px-4 font-semibold">SE</th>
                </tr>
              </thead>
              <tbody>
                {data.exams.map((e) => (
                  <tr
                    key={e.exam_session_id}
                    className="border-b border-slate-100 dark:border-gray-700 hover:bg-slate-50 dark:hover:bg-gray-800/30 transition-colors"
                  >
                    <td className="py-3 px-4 text-slate-900 dark:text-gray-100">
                      {new Date(e.ended_at ?? e.started_at).toLocaleDateString("ko-KR", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-3 px-4 text-slate-700 dark:text-gray-300">
                      {getExamTypeLabel(e.exam_type)}
                    </td>
                    <td className="py-3 px-4">{getStatusBadge(e.status)}</td>
                    <td className="py-3 px-4">
                      {e.score != null ? (
                        <span className="font-semibold text-slate-900 dark:text-gray-100">
                          {e.score.toFixed(1)}점
                        </span>
                      ) : (
                        <span className="text-slate-400 dark:text-gray-500">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {e.grade_letter ? (
                        <>
                          <span className="font-semibold text-slate-900 dark:text-gray-100">
                            {e.grade_letter}
                          </span>{" "}
                          {e.grade_numeric != null && (
                            <span className="text-xs text-slate-400 dark:text-gray-500">
                              ({e.grade_numeric}등급)
                            </span>
                          )}
                        </>
                      ) : (
                        <span className="text-slate-400 dark:text-gray-500">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-700 dark:text-gray-300">
                      {e.theta != null ? e.theta.toFixed(2) : "-"}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-500 dark:text-gray-400">
                      {e.standard_error != null ? e.standard_error.toFixed(2) : "-"}
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
      <Card className="bg-sky-50 dark:bg-sky-900/20 border-sky-200 dark:border-sky-800">
        <p className="text-sm text-sky-800 dark:text-sky-300">
          💡 <strong>θ (Theta)</strong>는 IRT 능력 추정치이며,{" "}
          <strong>SE (Standard Error)</strong>는 추정 정확도입니다. SE가 낮을수록
          더 정확한 측정입니다.
        </p>
      </Card>
    </div>
  );
}
