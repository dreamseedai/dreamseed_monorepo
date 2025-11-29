// apps/parent_front/src/lib/parentClient.ts
import { apiFetch } from "./apiClient";

export type ParentChild = {
  id: string;
  name: string;
  school: string | null;
  grade: string | null;
};

export type ParentChildrenResponse = {
  parentId: string;
  children: ParentChild[];
};

export async function fetchParentChildren(): Promise<ParentChildrenResponse> {
  return apiFetch<ParentChildrenResponse>("/parent/children", {}, true);
}

export async function downloadParentReportPdf(
  studentId: string,
  period: string
): Promise<Blob> {
  const token =
    typeof window !== "undefined"
      ? window.localStorage.getItem("access_token")
      : null;

  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/parent/reports/${studentId}/pdf?period=${encodeURIComponent(
      period
    )}`,
    {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }
  );
  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      detail = typeof data === "object" && data !== null && "detail" in data
        ? String(data.detail)
        : JSON.stringify(data);
    } catch {
      detail = res.statusText;
    }
    throw new Error(`Failed to download report: ${res.status} ${detail}`);
  }
  return res.blob();
}
