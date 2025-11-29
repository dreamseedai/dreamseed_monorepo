// portal_front/src/lib/apiTeacher.ts
/**
 * Teacher API Client
 * 
 * 선생님용 백엔드 API 호출 헬퍼 함수들
 * 
 * 엔드포인트:
 * - GET /api/teachers/{teacher_id}/students
 * - GET /api/teachers/{teacher_id}/students/{student_id}
 */

import { api } from './api';

// ============================================================================
// Types (Backend Pydantic 모델과 1:1 매칭)
// ============================================================================

export type StudentStatus = 'On Track' | 'At Risk' | 'Struggling';

export interface StudentSummary {
  id: string;
  name: string;
  class_id?: string;
  class_name?: string;
  current_ability_theta?: number;
  recent_score?: number; // 0-100
  status: StudentStatus;
  risk_flags?: string[];
}

export interface AbilityPoint {
  label: string; // e.g. "4w ago", "now"
  value: number; // θ 값
}

export interface RecentTest {
  date: string; // ISO8601 or YYYY-MM-DD
  name: string;
  score: number; // 0-100
}

export interface StudentDetail extends StudentSummary {
  ability_trend: AbilityPoint[];
  recent_tests: RecentTest[];
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

export interface ListStudentsParams {
  q?: string; // 이름 검색
  class_id?: string; // 클래스 필터
  status?: string; // "On Track" | "At Risk" | "Struggling" | "all"
  page?: number;
  page_size?: number;
}

/**
 * 학생 목록 조회
 * 
 * @example
 * const response = await teacherApi.listStudents({
 *   q: '홍길동',
 *   status: 'At Risk',
 *   page: 1,
 *   page_size: 20,
 * });
 * 
 * console.log(response.items); // StudentSummary[]
 */
export async function listStudents(
  params: ListStudentsParams = {}
): Promise<PageResponse<StudentSummary>> {
  const queryParams = new URLSearchParams();
  
  if (params.q) queryParams.append('q', params.q);
  if (params.class_id) queryParams.append('class_id', params.class_id);
  if (params.status) queryParams.append('status', params.status);
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.page_size) queryParams.append('page_size', params.page_size.toString());
  
  const queryString = queryParams.toString();
  const url = `/api/teachers/me/students${queryString ? `?${queryString}` : ''}`;
  
  return api<PageResponse<StudentSummary>>(url);
}

/**
 * 학생 상세 정보 조회
 * 
 * @example
 * const student = await teacherApi.getStudentDetail('s1');
 * console.log(student.ability_trend); // AbilityPoint[]
 * console.log(student.recent_tests);  // RecentTest[]
 */
export async function getStudentDetail(studentId: string): Promise<StudentDetail> {
  return api<StudentDetail>(`/api/teachers/me/students/${studentId}`);
}

// ============================================================================
// Namespace export (optional)
// ============================================================================

export const teacherApi = {
  listStudents,
  getStudentDetail,
};
