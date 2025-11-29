"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { fetchExamDetail, createOrResumeSession, ExamDetail } from "@/lib/examClient";

export default function ExamDetailPage() {
  const router = useRouter();
  const params = useParams();
  const examId = params.examId as string;

  const [exam, setExam] = useState<ExamDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadExamDetail() {
      try {
        const data = await fetchExamDetail(examId);
        setExam(data);
      } catch (err) {
        console.error("Failed to fetch exam detail:", err);
        setError("시험 정보를 불러오는 데 실패했습니다.");
      } finally {
        setLoading(false);
      }
    }

    loadExamDetail();
  }, [examId]);

  async function handleStartExam() {
    if (!exam) return;

    setStarting(true);
    setError(null);

    try {
      const newSession = await createOrResumeSession(exam.id);
      
      // Navigate to session page
      router.push(`/exams/${exam.id}/session/${newSession.id}`);
    } catch (err) {
      console.error("Failed to start exam session:", err);
      setError("시험 세션을 시작하는 데 실패했습니다.");
      setStarting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">시험 정보를 불러오는 중...</div>
      </div>
    );
  }

  if (error && !exam) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <div className="text-red-800">{error}</div>
        <button
          onClick={() => router.push("/exams")}
          className="mt-4 text-sm text-red-600 hover:text-red-800 underline"
        >
          시험 목록으로 돌아가기
        </button>
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="rounded-lg border bg-white p-12 text-center">
        <div className="text-gray-500">시험을 찾을 수 없습니다.</div>
        <button
          onClick={() => router.push("/exams")}
          className="mt-4 text-sm text-blue-600 hover:text-blue-800 underline"
        >
          시험 목록으로 돌아가기
        </button>
      </div>
    );
  }

  const statusColors = {
    upcoming: "bg-gray-100 text-gray-700",
    in_progress: "bg-orange-100 text-orange-700",
    completed: "bg-green-100 text-green-700",
  };

  const statusLabels = {
    upcoming: "예정됨",
    in_progress: "진행 중",
    completed: "완료됨",
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Back Button */}
      <button
        onClick={() => router.push("/exams")}
        className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
      >
        ← 시험 목록으로
      </button>

      {/* Exam Detail Card */}
      <div className="rounded-lg border bg-white p-8">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{exam.title}</h1>
            <div className="mt-2 flex items-center gap-3">
              <span className="text-sm text-gray-600">과목: {exam.subject}</span>
              <span
                className={`rounded px-2 py-1 text-xs font-medium ${
                  statusColors[exam.status]
                }`}
              >
                {statusLabels[exam.status]}
              </span>
            </div>
          </div>
        </div>

        <div className="prose max-w-none">
          <p className="text-gray-700">{exam.description}</p>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-6 border-t pt-6">
          <div>
            <div className="text-sm text-gray-600">예상 소요 시간</div>
            <div className="mt-1 text-lg font-semibold">{exam.durationMinutes}분</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">총 문항 수</div>
            <div className="mt-1 text-lg font-semibold">{exam.totalQuestions}문항</div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}

        {/* Start Button */}
        <div className="mt-8 flex justify-center">
          <button
            onClick={handleStartExam}
            disabled={starting || exam.status === "completed"}
            className={`px-8 py-3 rounded-lg font-semibold text-white transition ${
              exam.status === "completed"
                ? "bg-gray-400 cursor-not-allowed"
                : starting
                ? "bg-blue-400 cursor-wait"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {starting
              ? "시작하는 중..."
              : exam.status === "in_progress"
              ? "시험 계속하기"
              : exam.status === "completed"
              ? "완료된 시험"
              : "시험 시작하기"}
          </button>
        </div>

        {/* Instructions */}
        <div className="mt-8 rounded-lg bg-blue-50 border border-blue-200 p-6">
          <h3 className="font-semibold text-blue-900 mb-3">시험 안내사항</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li>• 이 시험은 CAT(Computer Adaptive Test) 방식으로 진행됩니다.</li>
            <li>• 각 문제의 난이도는 이전 답변을 기반으로 조정됩니다.</li>
            <li>• 한 번 제출한 답변은 수정할 수 없습니다.</li>
            <li>• 시험 중 브라우저를 닫으면 진행 상황이 저장됩니다.</li>
            <li>• 제한 시간이 있는 경우, 시간이 초과되면 자동으로 제출됩니다.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
