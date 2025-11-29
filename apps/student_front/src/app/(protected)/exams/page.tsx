"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type ExamStatus = "available" | "in-progress" | "completed";

type ExamCard = {
  id: string;
  title: string;
  subject: "math" | "english" | "science";
  description: string;
  estimatedTime: string;
  status: ExamStatus;
  lastAttempt?: string;
};

// Mock data - will be replaced with API calls in Week 3
const mockExams: ExamCard[] = [
  {
    id: "math-diagnostic",
    title: "수학 진단 평가",
    subject: "math",
    description: "CAT 적응형 평가 (약 10-15문항)",
    estimatedTime: "20분",
    status: "available",
  },
  {
    id: "english-diagnostic",
    title: "영어 진단 평가",
    subject: "english",
    description: "CAT 적응형 평가 (약 10-15문항)",
    estimatedTime: "20분",
    status: "available",
  },
  {
    id: "science-diagnostic",
    title: "과학 진단 평가",
    subject: "science",
    description: "CAT 적응형 평가 (약 10-15문항)",
    estimatedTime: "20분",
    status: "available",
  },
];

const subjectColors = {
  math: "bg-blue-100 text-blue-700",
  english: "bg-green-100 text-green-700",
  science: "bg-purple-100 text-purple-700",
};

const subjectLabels = {
  math: "Math",
  english: "English",
  science: "Science",
};

export default function ExamsPage() {
  const router = useRouter();
  const [filter, setFilter] = useState<"all" | "math" | "english" | "science">("all");

  const filteredExams =
    filter === "all"
      ? mockExams
      : mockExams.filter((exam) => exam.subject === filter);

  function handleStartExam(examId: string) {
    router.push(`/exams/${examId}`);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">시험 목록</h1>

      {/* Filter Tabs */}
      <div className="flex gap-4 border-b">
        <button
          onClick={() => setFilter("all")}
          className={`px-4 py-2 text-sm font-medium ${
            filter === "all"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          전체
        </button>
        <button
          onClick={() => setFilter("math")}
          className={`px-4 py-2 text-sm font-medium ${
            filter === "math"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          수학
        </button>
        <button
          onClick={() => setFilter("english")}
          className={`px-4 py-2 text-sm font-medium ${
            filter === "english"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          영어
        </button>
        <button
          onClick={() => setFilter("science")}
          className={`px-4 py-2 text-sm font-medium ${
            filter === "science"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          과학
        </button>
      </div>

      {/* Exam Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        {filteredExams.map((exam) => (
          <div key={exam.id} className="rounded-lg border bg-white p-6">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold">{exam.title}</h3>
                <p className="mt-1 text-sm text-gray-500">{exam.description}</p>
              </div>
              <span
                className={`rounded px-2 py-1 text-xs font-medium ${
                  subjectColors[exam.subject]
                }`}
              >
                {subjectLabels[exam.subject]}
              </span>
            </div>

            {exam.lastAttempt && (
              <div className="mt-3 text-xs text-gray-500">
                마지막 응시: {exam.lastAttempt}
              </div>
            )}

            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                예상 소요 시간: {exam.estimatedTime}
              </div>
              <button
                onClick={() => handleStartExam(exam.id)}
                className={`rounded px-4 py-2 text-sm font-medium text-white transition ${
                  exam.status === "available"
                    ? "bg-blue-600 hover:bg-blue-700"
                    : exam.status === "in-progress"
                    ? "bg-orange-600 hover:bg-orange-700"
                    : "bg-gray-400"
                }`}
                disabled={exam.status === "completed"}
              >
                {exam.status === "available"
                  ? "시작하기"
                  : exam.status === "in-progress"
                  ? "계속하기"
                  : "완료됨"}
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredExams.length === 0 && (
        <div className="rounded-lg border bg-white p-12 text-center">
          <div className="text-gray-500">해당 과목의 시험이 없습니다.</div>
        </div>
      )}
    </div>
  );
}
