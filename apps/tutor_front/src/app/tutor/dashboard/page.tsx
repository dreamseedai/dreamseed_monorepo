// apps/tutor_front/src/app/tutor/dashboard/page.tsx
"use client";

import { useEffect, useState } from "react";
import {
  fetchTutorPriorities,
  TutorPriorityListResponse,
  createReportComment,
  ReportCommentSection,
} from "@/lib/tutorClient";

type SubjectOption = {
  value: string;
  label: string;
};

const SUBJECTS: SubjectOption[] = [
  { value: "math", label: "수학" },
  { value: "english", label: "영어" },
  { value: "science", label: "과학" },
];

export default function TutorDashboardPage() {
  const [subject, setSubject] = useState<string>("math");
  const [windowDays, setWindowDays] = useState<number>(14);
  const [data, setData] = useState<TutorPriorityListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 코멘트 모달 상태
  const [commentStudentId, setCommentStudentId] = useState<string | null>(null);
  const [commentSection, setCommentSection] =
    useState<ReportCommentSection>("summary");
  const [commentContent, setCommentContent] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchTutorPriorities(subject, windowDays);
        if (!cancelled) setData(res);
      } catch (err) {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : "우선순위 리스트를 불러오는 중 오류가 발생했습니다.";
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
  }, [subject, windowDays]);

  function openCommentModal(studentId: string) {
    setCommentStudentId(studentId);
    setCommentSection("summary");
    setCommentContent("");
  }

  async function handleSubmitComment() {
    if (!commentStudentId || !commentContent.trim()) return;
    setCommentSubmitting(true);
    try {
      const now = new Date();
      const periodEnd = now.toISOString().slice(0, 10);
      const periodStart = new Date(
        now.getTime() - windowDays * 24 * 60 * 60 * 1000
      )
        .toISOString()
        .slice(0, 10);

      await createReportComment(commentStudentId, {
        periodStart,
        periodEnd,
        section: commentSection,
        language: "ko",
        content: commentContent.trim(),
        publish: true,
      });
      setCommentStudentId(null);
      setCommentContent("");
    } catch (err) {
      const message = err instanceof Error ? err.message : "코멘트 저장 중 오류가 발생했습니다.";
      alert(message);
    } finally {
      setCommentSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">튜터 대시보드</h1>
          <p className="text-sm text-gray-600">
            IRT/CAT 능력치와 활동 데이터를 기반으로 이번 주 개입 우선순위를
            확인하세요.
          </p>
        </div>
        <div className="flex gap-3 text-sm">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">
              과목
            </label>
            <select
              className="rounded-lg border px-3 py-1.5"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            >
              {SUBJECTS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">
              기간(일)
            </label>
            <select
              className="rounded-lg border px-3 py-1.5"
              value={windowDays}
              onChange={(e) => setWindowDays(Number(e.target.value))}
            >
              <option value={7}>7일</option>
              <option value={14}>14일</option>
              <option value={30}>30일</option>
            </select>
          </div>
        </div>
      </header>

      {loading && (
        <p className="text-sm text-gray-500">우선순위 데이터를 불러오는 중...</p>
      )}

      {error && (
        <p className="text-sm text-red-600 whitespace-pre-line">{error}</p>
      )}

      {!loading && !error && data && (
        <div className="overflow-hidden rounded-lg border bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-3 py-2">학생</th>
                <th className="px-3 py-2">학교 / 학년</th>
                <th className="px-3 py-2">수준(Band)</th>
                <th className="px-3 py-2">Δθ(14d)</th>
                <th className="px-3 py-2">위험도</th>
                <th className="px-3 py-2">플래그</th>
                <th className="px-3 py-2">우선순위</th>
                <th className="px-3 py-2 text-right">코멘트</th>
              </tr>
            </thead>
            <tbody>
              {data.students.map((s) => (
                <tr
                  key={s.studentId}
                  className="border-t text-xs hover:bg-gray-50"
                >
                  <td className="px-3 py-2 font-medium">{s.studentName}</td>
                  <td className="px-3 py-2">
                    {s.school ?? "-"} {s.grade ? ` / ${s.grade}` : ""}
                  </td>
                  <td className="px-3 py-2">
                    <span className="inline-flex rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700">
                      {s.thetaBand}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    {s.deltaTheta14d.toFixed(2)}{" "}
                    {s.deltaTheta14d > 0.05
                      ? "↑"
                      : s.deltaTheta14d < -0.05
                      ? "↓"
                      : "→"}
                  </td>
                  <td className="px-3 py-2">{s.riskLevel}</td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {s.flags.map((f) => (
                        <span
                          key={f}
                          className="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-[10px] text-gray-700"
                        >
                          {f}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-2">{s.priorityScore.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right">
                    <button
                      onClick={() => openCommentModal(s.studentId)}
                      className="rounded-md border px-2 py-1 text-[11px] font-semibold hover:bg-gray-100"
                    >
                      코멘트 작성
                    </button>
                  </td>
                </tr>
              ))}
              {data.students.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    className="px-3 py-4 text-center text-xs text-gray-500"
                  >
                    표시할 학생이 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* 코멘트 모달 (아주 단순한 버전) */}
      {commentStudentId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="w-full max-w-md rounded-lg bg-white p-4 shadow-lg">
            <h2 className="mb-2 text-sm font-semibold">
              학부모 리포트 코멘트 작성
            </h2>
            <label className="mb-1 block text-xs font-medium text-gray-600">
              섹션
            </label>
            <select
              className="mb-3 w-full rounded-lg border px-3 py-1.5 text-xs"
              value={commentSection}
              onChange={(e) =>
                setCommentSection(e.target.value as ReportCommentSection)
              }
            >
              <option value="summary">종합 소견</option>
              <option value="next_4w_plan">다음 4주 계획</option>
              <option value="parent_guidance">학부모 가이드</option>
            </select>

            <label className="mb-1 block text-xs font-medium text-gray-600">
              내용 (한국어)
            </label>
            <textarea
              className="h-32 w-full rounded-lg border px-3 py-2 text-xs"
              value={commentContent}
              onChange={(e) => setCommentContent(e.target.value)}
            />

            <div className="mt-3 flex justify-end gap-2">
              <button
                className="rounded-lg px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100"
                onClick={() => setCommentStudentId(null)}
              >
                취소
              </button>
              <button
                disabled={commentSubmitting || !commentContent.trim()}
                onClick={handleSubmitComment}
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {commentSubmitting ? "저장 중..." : "저장 후 발행"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
