"use client";

/**
 * Teacher Student Dashboard Page
 * 
 * Route: /teacher/dashboard/students/[studentId]
 * 
 * Displays detailed exam history for an individual student:
 * - All exam sessions
 * - Score trends
 * - Theta and standard error details
 */

import { TeacherStudentDashboard } from "@/components/dashboard";

export default function TeacherStudentPage({
  params,
}: {
  params: { studentId: string };
}) {
  const studentId = parseInt(params.studentId);

  // Validate studentId
  if (isNaN(studentId)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-800 font-semibold mb-2 text-lg">
            잘못된 요청
          </h2>
          <p className="text-red-600 text-sm">
            유효하지 않은 학생 ID입니다: <code>{params.studentId}</code>
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
      <TeacherStudentDashboard studentId={studentId} />
    </div>
  );
}
