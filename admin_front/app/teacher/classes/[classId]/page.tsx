"use client";

/**
 * Teacher Class Dashboard Page
 * 
 * Route: /teacher/classes/[classId]
 * 
 * Shows:
 * - Class summary (average score, exam count)
 * - Student list with latest exam results
 * - Links to individual student pages
 */

import { useParams } from "next/navigation";
import Link from "next/link";
import { useTeacherClassExams } from "@/lib/hooks/useDashboard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { LoadingSpinner, ErrorMessage } from "@/components/ui/LoadingSpinner";

export default function TeacherClassDashboardPage() {
  const params = useParams<{ classId: string }>();
  const classId = params?.classId;
  const { data, isLoading, isError, error } = useTeacherClassExams(classId);

  if (isLoading) return <LoadingSpinner />;
  if (isError)
    return (
      <ErrorMessage
        message={error instanceof Error ? error.message : "데이터를 불러올 수 없습니다."}
      />
    );
  if (!data) return <ErrorMessage message="데이터가 없습니다." />;

  // Calculate statistics
  const scores = data.exam_summary
    .map((e) => e.score)
    .filter((s): s is number => typeof s === "number");
  const avgScore =
    scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : null;

  // Grade distribution
  const gradeCount: { [key: number]: number } = {};
  data.exam_summary.forEach((e) => {
    if (e.grade_numeric !== null) {
      gradeCount[e.grade_numeric] = (gradeCount[e.grade_numeric] || 0) + 1;
    }
  });

  return (
    <div className="space-y-6">
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Page Header */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <PageHeader
        title={data.name}
        subtitle={`${data.subject} · 학생 ${data.student_count}명 · 시험 ${data.exam_summary.length}건`}
        rightSlot={
          <span className="text-xs rounded-full bg-slate-100 dark:bg-gray-700 px-3 py-1.5 text-slate-600 dark:text-gray-300 font-medium">
            DreamSeed CAT · 교사 대시보드
          </span>
        }
      />

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Summary Cards */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Average Score */}
        <Card>
          <h2 className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-2">
            반 평균 점수
          </h2>
          <p className="text-3xl font-semibold text-slate-900 dark:text-gray-100">
            {avgScore !== null ? avgScore.toFixed(1) : "-"}
            <span className="ml-1 text-base text-slate-400 dark:text-gray-500">
              점
            </span>
          </p>
        </Card>

        {/* Total Exams */}
        <Card>
          <h2 className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-2">
            총 시험 수
          </h2>
          <p className="text-3xl font-semibold text-slate-900 dark:text-gray-100">
            {data.exam_summary.length}
            <span className="ml-1 text-base text-slate-400 dark:text-gray-500">
              건
            </span>
          </p>
        </Card>

        {/* Grade Distribution Preview */}
        <Card>
          <h2 className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-2">
            등급 분포
          </h2>
          {Object.keys(gradeCount).length > 0 ? (
            <div className="space-y-1">
              {Object.entries(gradeCount)
                .sort(([a], [b]) => Number(a) - Number(b))
                .slice(0, 3)
                .map(([grade, count]) => (
                  <div
                    key={grade}
                    className="flex justify-between text-sm text-slate-600 dark:text-gray-300"
                  >
                    <span>{grade}등급:</span>
                    <span className="font-semibold">{count}명</span>
                  </div>
                ))}
              {Object.keys(gradeCount).length > 3 && (
                <div className="text-xs text-slate-400 dark:text-gray-500">
                  외 {Object.keys(gradeCount).length - 3}개 등급...
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-400 dark:text-gray-500">
              데이터 없음
            </p>
          )}
        </Card>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Info Card */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <Card className="bg-sky-50 dark:bg-sky-900/20 border-sky-200 dark:border-sky-800">
        <p className="text-sm text-sky-800 dark:text-sky-300">
          💡 <strong>CAT(Computerized Adaptive Testing)</strong> 기반 시험으로
          학생의 수준에 맞는 난이도 문항을 자동 출제합니다. 아래 학생별 요약
          테이블에서 "상세 보기"를 클릭하면 개별 성장 추이를 확인할 수 있습니다.
        </p>
      </Card>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      {/* Student Summary Table */}
      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <Card>
        <h2 className="text-base font-semibold text-slate-700 dark:text-gray-200 mb-4">
          학생별 최근 시험 요약
        </h2>
        {data.students.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="border-b border-slate-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-800/50">
                <tr className="text-left text-slate-500 dark:text-gray-400">
                  <th className="py-3 px-4 font-semibold">학생 ID</th>
                  <th className="py-3 px-4 font-semibold">최근 점수</th>
                  <th className="py-3 px-4 font-semibold">최근 등급</th>
                  <th className="py-3 px-4 font-semibold">응시 횟수</th>
                  <th className="py-3 px-4 font-semibold text-right">작업</th>
                </tr>
              </thead>
              <tbody>
                {data.students.map((s) => {
                  const latest = s.latest_exam;
                  return (
                    <tr
                      key={s.student_id}
                      className="border-b border-slate-100 dark:border-gray-700 hover:bg-slate-50 dark:hover:bg-gray-800/30 transition-colors"
                    >
                      <td className="py-3 px-4 text-slate-900 dark:text-gray-100 font-medium">
                        {s.student_id}
                      </td>
                      <td className="py-3 px-4">
                        {latest?.score != null ? (
                          <span className="font-semibold text-slate-900 dark:text-gray-100">
                            {latest.score.toFixed(1)}점
                          </span>
                        ) : (
                          <span className="text-slate-400 dark:text-gray-500">
                            -
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {latest?.grade_letter ? (
                          <>
                            <span className="font-semibold text-slate-900 dark:text-gray-100">
                              {latest.grade_letter}
                            </span>{" "}
                            {latest.grade_numeric != null && (
                              <span className="text-xs text-slate-400 dark:text-gray-500">
                                ({latest.grade_numeric}등급)
                              </span>
                            )}
                          </>
                        ) : (
                          <span className="text-slate-400 dark:text-gray-500">
                            -
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-900 dark:text-gray-100">
                        {s.exam_count}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/teacher/students/${s.student_id}`}
                          className="text-xs text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300 hover:underline font-medium"
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
          <div className="text-center py-8 text-slate-500 dark:text-gray-400">
            <p>학생 데이터가 없습니다.</p>
          </div>
        )}
      </Card>
    </div>
  );
}
