/**
 * dashboard.ts
 * 
 * API client for dashboard endpoints
 * 
 * Endpoints:
 * - GET /api/dashboard/teacher/classes/{classId}/exams
 * - GET /api/dashboard/teacher/students/{studentId}/exams
 * - GET /api/dashboard/parent/children/{studentId}/exams
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Types
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export type TeacherClassExamSummary = {
  class_id: number;
  name: string;
  subject: string;
  student_count: number;
  exam_summary: {
    exam_session_id: number;
    student_id: number;
    exam_type: string;
    ended_at: string | null;
    score: number | null;
    grade_numeric: number | null;
    grade_letter: string | null;
  }[];
  students: {
    student_id: number;
    latest_exam: {
      exam_session_id: number;
      ended_at: string | null;
      score: number | null;
      grade_numeric: number | null;
      grade_letter: string | null;
    } | null;
    exam_count: number;
  }[];
};

export type TeacherStudentExamHistory = {
  student_id: number;
  exams: {
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
  }[];
};

export type ParentChildExams = {
  student_id: number;
  exams: {
    exam_session_id: number;
    exam_type: string;
    date: string;
    score: number | null;
    grade_numeric: number | null;
    grade_letter: string | null;
    percentile: number | null;
  }[];
};

export type ClassStatistics = {
  class_id: number;
  average_score: number | null;
  grade_distribution: { [grade: number]: number };
  score_distribution: { bin: number; count: number }[];
  total_exams: number;
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// API Client
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiGet<T>(endpoint: string): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      // TODO: Add authentication header when ready
      // Authorization: `Bearer ${getToken()}`,
    },
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(
      `API error (${res.status}): ${res.statusText} - ${errorText}`
    );
  }

  return res.json();
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Exported API Functions
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export const getTeacherClassExams = (classId: string | number) =>
  apiGet<TeacherClassExamSummary>(
    `/api/dashboard/teacher/classes/${classId}/exams`
  );

export const getTeacherStudentExams = (studentId: string | number) =>
  apiGet<TeacherStudentExamHistory>(
    `/api/dashboard/teacher/students/${studentId}/exams`
  );

export const getParentChildExams = (studentId: string | number) =>
  apiGet<ParentChildExams>(
    `/api/dashboard/parent/children/${studentId}/exams`
  );

export const getClassStatistics = (classId: string | number) =>
  apiGet<ClassStatistics>(
    `/api/dashboard/teacher/classes/${classId}/statistics`
  );
