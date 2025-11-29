"use client";

/**
 * Teacher Class Dashboard Page
 * 
 * Route: /teacher/dashboard/classes/[classId]
 * 
 * Displays comprehensive overview of a class's exam results:
 * - Class average score
 * - Grade distribution
 * - Student-by-student summary table
 */

import { TeacherClassDashboard } from "@/components/dashboard";

export default function TeacherClassPage({
  params,
}: {
  params: { classId: string };
}) {
  const classId = parseInt(params.classId);

  // Validate classId
  if (isNaN(classId)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-800 font-semibold mb-2 text-lg">
            잘못된 요청
          </h2>
          <p className="text-red-600 text-sm">
            유효하지 않은 반 ID입니다: <code>{params.classId}</code>
          </p>
          <a
            href="/teacher/dashboard"
            className="inline-block mt-4 text-blue-600 hover:underline text-sm"
          >
            ← 대시보드로 돌아가기
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <TeacherClassDashboard classId={classId} />
    </div>
  );
}
