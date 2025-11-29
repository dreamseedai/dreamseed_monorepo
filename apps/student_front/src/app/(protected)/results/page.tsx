"use client";

import { useState } from "react";

interface ExamResult {
  id: number;
  examName: string;
  subject: string;
  score: number;
  maxScore: number;
  date: string;
  duration: number; // minutes
  rank: number;
  totalStudents: number;
}

export default function ResultsPage() {
  const [results] = useState<ExamResult[]>([
    {
      id: 1,
      examName: "중간고사 모의고사",
      subject: "수학",
      score: 85,
      maxScore: 100,
      date: "2025-01-15",
      duration: 50,
      rank: 12,
      totalStudents: 150,
    },
    {
      id: 2,
      examName: "단원평가",
      subject: "영어",
      score: 92,
      maxScore: 100,
      date: "2025-01-10",
      duration: 40,
      rank: 5,
      totalStudents: 150,
    },
    {
      id: 3,
      examName: "전국 모의고사",
      subject: "수학",
      score: 78,
      maxScore: 100,
      date: "2025-01-05",
      duration: 60,
      rank: 45,
      totalStudents: 150,
    },
  ]);

  const getScoreColor = (score: number, maxScore: number) => {
    const percentage = (score / maxScore) * 100;
    if (percentage >= 90) return "text-green-600";
    if (percentage >= 70) return "text-blue-600";
    if (percentage >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const averageScore = results.length > 0 
    ? Math.round(results.reduce((sum, r) => sum + (r.score / r.maxScore) * 100, 0) / results.length)
    : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">성적 분석</h1>

      {/* 성적 요약 */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border bg-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">평균 점수</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">{averageScore}점</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
              <span className="text-xl">📊</span>
            </div>
          </div>
        </div>

        <div className="rounded-lg border bg-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">응시 시험</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">{results.length}개</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-between rounded-full bg-green-100">
              <span className="text-xl">✓</span>
            </div>
          </div>
        </div>

        <div className="rounded-lg border bg-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">최고 점수</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">
                {Math.max(...results.map(r => Math.round((r.score / r.maxScore) * 100)))}점
              </p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-yellow-100">
              <span className="text-xl">🏆</span>
            </div>
          </div>
        </div>
      </div>

      {/* 최근 시험 결과 */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900">최근 시험 결과</h2>
        <div className="mt-4 space-y-4">
          {results.map((result) => (
            <div key={result.id} className="flex items-center justify-between border-b pb-4 last:border-b-0">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-medium text-gray-900">{result.examName}</h3>
                  <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700">
                    {result.subject}
                  </span>
                </div>
                <div className="mt-1 flex items-center gap-4 text-sm text-gray-500">
                  <span>{result.date}</span>
                  <span>•</span>
                  <span>{result.duration}분</span>
                  <span>•</span>
                  <span>
                    {result.rank}위 / {result.totalStudents}명
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className={`text-2xl font-bold ${getScoreColor(result.score, result.maxScore)}`}>
                    {result.score}
                  </p>
                  <p className="text-sm text-gray-500">/ {result.maxScore}</p>
                </div>
                <button className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                  상세보기
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 과목별 성적 추이 */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900">과목별 성적 추이</h2>
        <p className="mt-2 text-sm text-gray-500">
          차트 시각화는 Week 3 이후 구현 예정입니다.
        </p>
        <div className="mt-4 space-y-3">
          {["수학", "영어", "과학"].map((subject) => {
            const subjectResults = results.filter(r => r.subject === subject);
            const avgScore = subjectResults.length > 0
              ? Math.round(subjectResults.reduce((sum, r) => sum + (r.score / r.maxScore) * 100, 0) / subjectResults.length)
              : 0;

            return (
              <div key={subject}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-gray-700">{subject}</span>
                  <span className="text-gray-900">{avgScore}점</span>
                </div>
                <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-gray-200">
                  <div
                    className="h-full rounded-full bg-blue-600"
                    style={{ width: `${avgScore}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
