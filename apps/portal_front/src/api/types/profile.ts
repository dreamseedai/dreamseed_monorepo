export type Country = "US" | "CA" | "KR" | "CN";
export type Grade = "G9" | "G10" | "G11" | "G12";
export type Goal =
  | "SAT_1500_PLUS"
  | "AP_5"
  | "COLLEGE_ADMISSIONS"
  | "TOEFL_IELTS";

export interface UserProfile {
  userId: string;
  country: Country;
  grade: Grade;
  goals: Goal[];
  languages: ("en" | "ko" | "zh-Hans" | "zh-Hant")[];
  // 과거 성적/모의고사/약점 요약 등은 추후 확장
  history?: {
    sat?: { math?: number; rw?: number; date?: string }[];
    ap?: { subject: string; score?: number; date?: string }[];
  };
}

export interface DiagnosticRequest {
  userId: string;
  context: {
    country: Country;
    grade: Grade;
    goal: Goal;
  };
  evidence?: {
    quizAnswers?: Array<{ id: string; answer: string }>;
    pastScores?: Record<string, number>;
  };
}

export interface DiagnosticResponse {
  userId: string;
  summary: string;                 // 현재 수준 요약
  weaknesses: string[];            // 약점 태그
  recommendedModules: string[];    // 권장 모듈 키
  recommendedProblems: Array<{ id: string; title: string }>;
  nextWeekPlan: Array<{ day: string; tasks: string[] }>;
  tokenUsage?: { prompt: number; completion: number; total: number };
}


