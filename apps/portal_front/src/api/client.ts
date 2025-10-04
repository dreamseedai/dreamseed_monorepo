import type { DiagnosticRequest, DiagnosticResponse } from './types/profile';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8006' : '');

export async function postDiagnosticsRun(request: DiagnosticRequest): Promise<DiagnosticResponse> {
  const response = await fetch(`${API_URL}/api/diagnostics/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Diagnostic request failed: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function getProfile(userId: string) {
  const response = await fetch(`${API_URL}/api/profile/${userId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Profile request failed: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function updateProfile(profile: any) {
  const response = await fetch(`${API_URL}/api/profile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(profile),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Profile update failed: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function postShare(payload: any): Promise<{id: string; url: string}> {
  const response = await fetch(`${API_URL}/api/share`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ payload }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to create share');
  }

  return response.json();
}


