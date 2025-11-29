// portal_front/src/lib/apiTutor.ts
/**
 * Tutor API Client
 * 
 * 튜터(가정교사)용 백엔드 API 호출 헬퍼 함수들
 * 
 * 엔드포인트:
 * - GET /api/tutors/{tutor_id}/sessions
 * - GET /api/tutors/{tutor_id}/sessions/{session_id}
 */

import { api } from './api';

// ============================================================================
// Types (Backend Pydantic 모델과 1:1 매칭)
// ============================================================================

export type SessionStatus = 'Completed' | 'Upcoming';

export interface TutorSessionSummary {
  id: string;
  date: string; // ISO8601 or YYYY-MM-DD
  student_id: string;
  student_name: string;
  subject: string;
  topic: string;
  status: SessionStatus;
}

export interface TutorSessionTask {
  label: string;
  done: boolean;
}

export interface TutorSessionDetail extends TutorSessionSummary {
  duration_minutes: number;
  notes: string;
  tasks: TutorSessionTask[];
}

export interface PageResponse<T> {
  total_count: number;
  page: number;
  page_size: number;
  items: T[];
}

// ============================================================================
// API Functions
// ============================================================================

export interface ListSessionsParams {
  status?: string; // "Upcoming" | "Completed" | "all"
  page?: number;
  page_size?: number;
}

/**
 * 세션 목록 조회
 * 
 * @example
 * const response = await tutorApi.listSessions({
 *   status: 'Completed',
 *   page: 1,
 *   page_size: 20,
 * });
 * 
 * console.log(response.items); // TutorSessionSummary[]
 */
export async function listSessions(
  params: ListSessionsParams = {}
): Promise<PageResponse<TutorSessionSummary>> {
  const queryParams = new URLSearchParams();
  
  if (params.status) queryParams.append('status', params.status);
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.page_size) queryParams.append('page_size', params.page_size.toString());
  
  const queryString = queryParams.toString();
  const url = `/api/tutors/me/sessions${queryString ? `?${queryString}` : ''}`;
  
  return api<PageResponse<TutorSessionSummary>>(url);
}

/**
 * 세션 상세 정보 조회
 * 
 * @example
 * const session = await tutorApi.getSessionDetail('sess1');
 * console.log(session.notes);  // "개념 이해는 양호..."
 * console.log(session.tasks);  // [{ label, done }]
 */
export async function getSessionDetail(sessionId: string): Promise<TutorSessionDetail> {
  return api<TutorSessionDetail>(`/api/tutors/me/sessions/${sessionId}`);
}

// ============================================================================
// Namespace export (optional)
// ============================================================================

export const tutorApi = {
  listSessions,
  getSessionDetail,
};
