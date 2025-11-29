import { apiFetch } from "./apiClient";

// --- Types ---
export type ExamStatus = "upcoming" | "in_progress" | "completed";

export type ExamSummary = {
  id: string;
  title: string;
  subject: string;
  status: ExamStatus;
  scheduledAt: string | null; // optional
  durationMinutes: number | null;
};

export type ExamDetail = {
  id: string;
  title: string;
  description: string;
  subject: string;
  durationMinutes: number;
  totalQuestions: number;
  status: ExamStatus;
};

export type ExamSession = {
  id: string;
  examId: string;
  startedAt: string;
  endsAt: string | null;
  status: "in_progress" | "completed";
};

export type QuestionOption = {
  id: string;
  label: string; // "A", "B", ...
  text: string;
};

export type QuestionPayload = {
  id: string;
  stemHtml: string; // TipTap/MathLive → 렌더할 준비된 HTML (나중에)
  options: QuestionOption[];
  questionIndex: number;
  totalQuestions: number;
  timeRemainingSeconds: number | null;
};

export type SubmitAnswerPayload = {
  correct: boolean;
  explanationHtml?: string;
};

export type ExamResultSummary = {
  sessionId: string;
  examId: string;
  score: number;
  totalScore: number;
  correctCount: number;
  wrongCount: number;
  omittedCount: number;
};

// --- API functions ---

/**
 * 시험 상세 정보 가져오기
 * GET /api/exams/{examId}
 */
export async function fetchExamDetail(examId: string): Promise<ExamDetail> {
  return apiFetch<ExamDetail>(`/api/exams/${examId}`, {}, true);
}

/**
 * 기존 세션 있는지 확인 + 새 세션 생성
 * POST /api/exams/{examId}/sessions
 */
export async function createOrResumeSession(
  examId: string
): Promise<ExamSession> {
  return apiFetch<ExamSession>(
    `/api/exams/${examId}/sessions`,
    {
      method: "POST",
    },
    true
  );
}

/**
 * 현재 문제 가져오기
 * GET /api/exam-sessions/{sessionId}/current-question
 */
export async function fetchCurrentQuestion(
  sessionId: string
): Promise<QuestionPayload> {
  return apiFetch<QuestionPayload>(
    `/api/exam-sessions/${sessionId}/current-question`,
    {},
    true
  );
}

/**
 * 답안 제출
 * POST /api/exam-sessions/{sessionId}/answer
 */
export async function submitAnswer(
  sessionId: string,
  questionId: string,
  selectedOptionId: string
): Promise<SubmitAnswerPayload> {
  return apiFetch<SubmitAnswerPayload>(
    `/api/exam-sessions/${sessionId}/answer`,
    {
      method: "POST",
      body: JSON.stringify({
        question_id: questionId,
        selected_option_id: selectedOptionId,
      }),
    },
    true
  );
}

/**
 * 시험 종료 / 결과 요약
 * GET /api/exam-sessions/{sessionId}/summary
 */
export async function fetchExamResult(
  sessionId: string
): Promise<ExamResultSummary> {
  return apiFetch<ExamResultSummary>(
    `/api/exam-sessions/${sessionId}/summary`,
    {},
    true
  );
}
