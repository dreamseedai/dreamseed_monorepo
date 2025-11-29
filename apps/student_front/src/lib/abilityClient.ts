/**
 * Student Ability API Client
 * 
 * Provides type-safe wrappers for student ability dashboard APIs:
 * - GET /abilities/me/summary - Subject ability summaries
 * - GET /abilities/me/trend - Theta trend over time
 * 
 * Usage:
 *   import { fetchMyAbilitySummary } from '@/lib/abilityClient';
 *   
 *   const summary = await fetchMyAbilitySummary();
 *   console.log(summary.subjects[0].theta);
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001/api';

// ============================================================================
// Types
// ============================================================================

export type ThetaBand = 'A' | 'B+' | 'B' | 'C' | 'D';
export type RiskLevel = 'low' | 'medium' | 'high';

export interface SubjectAbilitySummary {
  subject: string;
  theta: number;
  thetaSe: number;
  thetaBand: ThetaBand;
  percentile: number;
  deltaTheta7d: number | null;
  riskLevel: RiskLevel;
  statusLabel: string;
  recommendedAction: string;
}

export interface AbilitySummaryResponse {
  studentId: string;
  asOf: string;
  subjects: SubjectAbilitySummary[];
}

export interface ThetaTrendPoint {
  calibratedAt: string;
  theta: number;
  thetaSe: number;
}

export interface ThetaTrendResponse {
  subject: string;
  points: ThetaTrendPoint[];
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Fetch authenticated user's ability summary (all subjects).
 * 
 * Requires: Student role + valid JWT token
 * 
 * Returns:
 *   - subjects: Array of subject summaries with theta, band, percentile, etc.
 *   - asOf: Timestamp of most recent calibration
 * 
 * Example:
 *   const summary = await fetchMyAbilitySummary();
 *   summary.subjects.forEach(s => {
 *     console.log(`${s.subject}: θ=${s.theta}, Band=${s.thetaBand}`);
 *   });
 */
export async function fetchMyAbilitySummary(): Promise<AbilitySummaryResponse> {
  const token = getAccessToken();
  
  const response = await fetch(`${API_BASE_URL}/abilities/me/summary`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Fetch theta trend for a specific subject.
 * 
 * Requires: Student role + valid JWT token
 * 
 * Args:
 *   - subject: Subject name (e.g., 'math', 'english')
 *   - days: Number of days to look back (default: 60)
 * 
 * Returns:
 *   - subject: Subject name
 *   - points: Array of (timestamp, theta, thetaSe) tuples, sorted by time ASC
 * 
 * Example:
 *   const trend = await fetchMyThetaTrend('math', 30);
 *   // Render line chart with trend.points
 */
export async function fetchMyThetaTrend(
  subject: string,
  days: number = 60
): Promise<ThetaTrendResponse> {
  const token = getAccessToken();
  
  const response = await fetch(
    `${API_BASE_URL}/abilities/me/trend?subject=${encodeURIComponent(subject)}&days=${days}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Get access token from localStorage.
 * 
 * TODO: Replace with your auth provider's token retrieval method
 * (e.g., NextAuth, Auth0, custom JWT storage)
 */
function getAccessToken(): string {
  if (typeof window === 'undefined') {
    throw new Error('Cannot access localStorage on server side');
  }
  
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('No access token found. Please log in.');
  }
  
  return token;
}

/**
 * Get theta band color for UI styling.
 * 
 * Usage:
 *   <span className={getThetaBandColor(subject.thetaBand)}>
 *     {subject.thetaBand}
 *   </span>
 */
export function getThetaBandColor(band: ThetaBand): string {
  const colors: Record<ThetaBand, string> = {
    'A': 'text-green-700 bg-green-100',
    'B+': 'text-blue-700 bg-blue-100',
    'B': 'text-gray-700 bg-gray-100',
    'C': 'text-yellow-700 bg-yellow-100',
    'D': 'text-red-700 bg-red-100',
  };
  return colors[band] || 'text-gray-700 bg-gray-100';
}

/**
 * Get risk level color for UI styling.
 */
export function getRiskLevelColor(level: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    'low': 'text-green-700 bg-green-100',
    'medium': 'text-yellow-700 bg-yellow-100',
    'high': 'text-red-700 bg-red-100',
  };
  return colors[level] || 'text-gray-700 bg-gray-100';
}

/**
 * Format delta theta for display.
 * 
 * Example:
 *   formatDeltaTheta(0.15) => "+0.15 ↑"
 *   formatDeltaTheta(-0.08) => "-0.08 ↓"
 */
export function formatDeltaTheta(delta: number | null): string {
  if (delta === null) return 'N/A';
  const sign = delta >= 0 ? '+' : '';
  const arrow = delta > 0 ? '↑' : delta < 0 ? '↓' : '→';
  return `${sign}${delta.toFixed(2)} ${arrow}`;
}
