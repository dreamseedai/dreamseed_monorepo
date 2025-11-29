// apps/parent_front/src/app/parent/reports/page.tsx
"use client";

import { useEffect, useState } from "react";
import {
  fetchParentChildren,
  ParentChildrenResponse,
  downloadParentReportPdf,
} from "@/lib/parentClient";

type PeriodOption = {
  value: string;
  label: string;
};

const PERIODS: PeriodOption[] = [
  { value: "last4w", label: "최근 4주" },
  { value: "last8w", label: "최근 8주" },
  { value: "semester", label: "이번 학기" },
];

export default function ParentReportsPage() {
  const [data, setData] = useState<ParentChildrenResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const [period, setPeriod] = useState<string>("last4w");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchParentChildren();
        if (!cancelled) {
          setData(res);
          if (res.children.length > 0) {
            setSelectedChildId(res.children[0].id);
          }
        }
      } catch (err) {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : "자녀 정보를 불러오는 중 오류가 발생했습니다.";
          setError(message);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleDownload() {
    if (!selectedChildId) return;
    setDownloading(true);
    try {
      const blob = await downloadParentReportPdf(selectedChildId, period);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `DreamSeed_Report_${selectedChildId}_${period}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      const message = err instanceof Error ? err.message : "리포트를 다운로드하는 중 오류가 발생했습니다.";
      alert(message);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">학습 리포트</h1>
        <p className="text-sm text-gray-600">
          자녀를 선택하고 기간을 선택하신 후 PDF 리포트를 다운로드할 수 있습니다.
        </p>
      </header>

      {loading && (
        <p className="text-sm text-gray-500">자녀 정보를 불러오는 중...</p>
      )}
      {error && (
        <p className="text-sm text-red-600 whitespace-pre-line">{error}</p>
      )}

      {!loading && !error && data && (
        <div className="space-y-4 rounded-lg border bg-white p-4 text-sm">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">
                자녀
              </label>
              <select
                className="min-w-[200px] rounded-lg border px-3 py-1.5"
                value={selectedChildId ?? ""}
                onChange={(e) => setSelectedChildId(e.target.value || null)}
              >
                {data.children.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}{" "}
                    {c.school ? ` / ${c.school}` : ""}{" "}
                    {c.grade ? ` / ${c.grade}` : ""}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">
                기간
              </label>
              <select
                className="rounded-lg border px-3 py-1.5"
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
              >
                {PERIODS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            disabled={!selectedChildId || downloading}
            onClick={handleDownload}
            className="mt-4 inline-flex rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {downloading ? "리포트 생성 중..." : "PDF 리포트 다운로드"}
          </button>

          <p className="mt-3 text-xs text-gray-500">
            리포트에는 학교 선생님, 학원 선생님, 튜터의 코멘트와 함께
            DreamSeedAI의 IRT/CAT 분석 결과가 포함됩니다.
          </p>
        </div>
      )}
    </div>
  );
}
