// apps/tutor_front/src/lib/tutorClient.ts
import { apiFetch } from "./apiClient";

export type TutorPriorityStudent = {
  studentId: string;
  studentName: string;
  school: string | null;
  grade: string | null;
  theta: number;
  thetaBand: string;
  deltaTheta14d: number;
  priorityScore: number;
  riskLevel: string;
  flags: string[];
  recommendedFocus: string[];
};

export type TutorPriorityListResponse = {
  tutorId: string;
  subject: string;
  generatedAt: string;
  windowDays: number;
  students: TutorPriorityStudent[];
};

export async function fetchTutorPriorities(
  subject: string,
  windowDays = 14
): Promise<TutorPriorityListResponse> {
  const qs = new URLSearchParams({
    subject,
    windowDays: String(windowDays),
  });
  return apiFetch<TutorPriorityListResponse>(
    `/tutor/priorities?${qs.toString()}`,
    {},
    true
  );
}

export type ReportCommentSection = "summary" | "next_4w_plan" | "parent_guidance";

export type CreateReportCommentPayload = {
  periodStart: string; // ISO date
  periodEnd: string;   // ISO date
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
