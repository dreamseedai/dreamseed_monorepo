// apps/teacher_front/src/lib/teacherClient.ts
import { apiFetch } from "./apiClient";

// Teacher와 Tutor는 거의 동일한 API를 사용하지만,
// Teacher는 school organization에만 접근 가능

export type TeacherStudent = {
  studentId: string;
  studentName: string;
  school: string | null;
  grade: string | null;
  className: string | null;
  theta: number;
  thetaBand: string;
  deltaTheta14d: number;
  priorityScore: number;
  riskLevel: string;
  flags: string[];
  recommendedFocus: string[];
};

export type TeacherClassListResponse = {
  teacherId: string;
  organizationName: string;
  className: string;
  subject: string;
  generatedAt: string;
  windowDays: number;
  students: TeacherStudent[];
};

export async function fetchTeacherClassList(
  subject: string,
  className?: string,
  windowDays = 14
): Promise<TeacherClassListResponse> {
  const qs = new URLSearchParams({
    subject,
    windowDays: String(windowDays),
  });
  if (className) {
    qs.append("class", className);
  }
  return apiFetch<TeacherClassListResponse>(
    `/teacher/class-list?${qs.toString()}`,
    {},
    true
  );
}

export type ReportCommentSection = "summary" | "next_4w_plan" | "parent_guidance";

export type CreateReportCommentPayload = {
  periodStart: string;
  periodEnd: string;
  section: ReportCommentSection;
  language?: "ko" | "en";
  content: string;
  publish?: boolean;
};

export async function createReportComment(
  studentId: string,
  payload: CreateReportCommentPayload
): Promise<void> {
  await apiFetch<void>(
    `/teacher/reports/${studentId}/comments`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    true
  );
}
