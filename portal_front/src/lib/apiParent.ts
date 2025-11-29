// portal_front/src/lib/apiParent.ts
/**
 * Parent API Client
 * 
 * 학부모용 백엔드 API 호출 헬퍼 함수들
 * 
 * 엔드포인트:
 * - GET /api/parents/{parent_id}/children/{child_id}
 */

import { api } from './api';
import type { StudentDetail, AbilityPoint, RecentTest } from './apiTeacher';

// ============================================================================
// Types (Backend Pydantic 모델과 1:1 매칭)
// ============================================================================

export interface ChildDetail extends StudentDetail {
  study_time_month?: string; // e.g. "12h / month"
  strengths: string[]; // e.g. ["도형", "함수 응용"]
  areas_to_improve: string[]; // e.g. ["확률", "통계"]
  recent_activity: Array<{
    date: string;
    description: string;
  }>;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * 자녀 상세 정보 조회
 * 
 * @example
 * const child = await parentApi.getChildDetail('c1');
 * console.log(child.strengths);         // ["도형", "함수 응용"]
 * console.log(child.areas_to_improve);  // ["확률", "통계"]
 * console.log(child.recent_activity);   // [{ date, description }]
 */
export async function getChildDetail(childId: string): Promise<ChildDetail> {
  return api<ChildDetail>(`/api/parents/me/children/${childId}`);
}

// ============================================================================
// Namespace export (optional)
// ============================================================================

export const parentApi = {
  getChildDetail,
};
