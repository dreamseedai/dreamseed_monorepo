"use client";

import { useEffect, useState } from "react";

interface StudyGoal {
  id: number;
  subject: string;
  targetScore: number;
  currentScore: number;
  deadline: string;
  progress: number;
}

export default function StudyPlanPage() {
  const [goals, setGoals] = useState<StudyGoal[]>([
    {
      id: 1,
      subject: "수학",
      targetScore: 90,
      currentScore: 75,
      deadline: "2025-12-31",
      progress: 65,
    },
    {
      id: 2,
      subject: "영어",
      targetScore: 85,
      currentScore: 70,
      deadline: "2025-12-31",
      progress: 55,
    },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">학습 계획</h1>
        <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
          + 목표 추가
        </button>
      </div>

      {/* 학습 목표 카드 */}
      <div className="grid gap-4 md:grid-cols-2">
        {goals.map((goal) => (
          <div key={goal.id} className="rounded-lg border bg-white p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{goal.subject}</h3>
                <p className="mt-1 text-sm text-gray-500">
                  목표: {goal.targetScore}점 | 현재: {goal.currentScore}점
                </p>
              </div>
              <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800">
                진행 중
              </span>
            </div>

            <div className="mt-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">진행도</span>
                <span className="font-medium text-gray-900">{goal.progress}%</span>
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-200">
                <div
                  className="h-full rounded-full bg-blue-600"
                  style={{ width: `${goal.progress}%` }}
                />
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between text-sm">
              <span className="text-gray-500">목표일: {goal.deadline}</span>
              <button className="text-blue-600 hover:text-blue-700">자세히 보기 →</button>
            </div>
          </div>
        ))}
      </div>

      {/* 주간 학습 일정 */}
      <div className="rounded-lg border bg-white p-6">
        <h2 className="text-lg font-semibold text-gray-900">이번 주 학습 일정</h2>
        <div className="mt-4 space-y-3">
          {["월", "화", "수", "목", "금", "토", "일"].map((day, index) => (
            <div key={day} className="flex items-center justify-between border-b pb-3 last:border-b-0">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
                  <span className="text-sm font-medium text-gray-700">{day}</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {index < 5 ? "수학, 영어" : "복습"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {index < 5 ? "19:00 - 21:00" : "자유 시간"}
                  </p>
                </div>
              </div>
              <div className="text-xs text-gray-400">
                {index === 0 ? "오늘" : index < 3 ? "예정" : ""}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI 추천 */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-6">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white">
            ✨
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">AI 학습 추천</h3>
            <p className="mt-1 text-sm text-gray-600">
              수학에서 약점으로 파악된 &quot;방정식&quot; 영역을 집중적으로 학습하면 목표 달성에 도움이 됩니다.
            </p>
            <button className="mt-2 text-sm font-medium text-blue-600 hover:text-blue-700">
              추천 문제 풀기 →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
