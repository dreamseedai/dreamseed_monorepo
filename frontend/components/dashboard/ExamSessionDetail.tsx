/**
 * ExamSessionDetail Component
 * 
 * 시험 세션 상세 정보 (모든 역할 공통)
 * API: GET /api/dashboard/exams/{examSessionId}
 */

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";

type ExamSessionDetail = {
  exam_session_id: number;
  student_id: number;
  student_name: string;
  student_grade: string;
  exam_type: string;
  status: string;
  started_at: string | null;
  ended_at: string | null;
  duration_sec: number | null;
  theta: number | null;
  standard_error: number | null;
  score: number | null;
  grade_numeric: number | null;
  grade_letter: string | null;
  percentile: number | null;
  t_score: number | null;
  attempts: {
    attempt_number: number;
    item_id: number;
    item_difficulty: number;
    student_response: string | null;
    correct_answer: string;
    is_correct: boolean;
    response_time_sec: number | null;
    theta_before: number | null;
    theta_after: number | null;
  }[];
};

export const ExamSessionDetail: React.FC = () => {
  const { examSessionId } = useParams<{ examSessionId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ExamSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTechnicalData, setShowTechnicalData] = useState(true);

  useEffect(() => {
    if (!examSessionId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await axios.get(
          `/api/dashboard/exams/${examSessionId}`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
          }
        );

        setData(res.data);
      } catch (err: any) {
        console.error("Failed to fetch exam session detail:", err);
        if (err.response?.status === 403) {
          setError("접근 권한이 없습니다.");
        } else {
          setError("데이터를 불러오는데 실패했습니다.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [examSessionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            ← 돌아가기
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">데이터가 없습니다.</p>
      </div>
    );
  }

  // 정답률 계산
  const correctCount = data.attempts.filter((a) => a.is_correct).length;
  const accuracy = data.attempts.length > 0
    ? (correctCount / data.attempts.length) * 100
    : 0;

  // 평균 응답 시간
  const avgResponseTime = data.attempts.length > 0
    ? data.attempts
        .filter((a) => a.response_time_sec !== null)
        .reduce((sum, a) => sum + (a.response_time_sec || 0), 0) /
      data.attempts.filter((a) => a.response_time_sec !== null).length
    : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* 헤더 */}
        <header className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate(-1)}
              className="text-blue-600 hover:underline text-sm"
            >
              ← 돌아가기
            </button>
            <button
              onClick={() => setShowTechnicalData(!showTechnicalData)}
              className="text-sm px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded"
            >
              {showTechnicalData ? "기술 정보 숨기기" : "기술 정보 보기"}
            </button>
          </div>
          <h1 className="text-3xl font-bold">
            시험 세션 #{data.exam_session_id}
          </h1>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>
              학생: <span className="font-semibold">{data.student_name}</span> (
              {data.student_grade})
            </span>
            <span>•</span>
            <span>
              타입:{" "}
              <span className="font-semibold">
                {data.exam_type === "mock"
                  ? "모의고사"
                  : data.exam_type === "practice"
                  ? "연습"
                  : "배치고사"}
              </span>
            </span>
            <span>•</span>
            <span>
              상태:{" "}
              <span
                className={`font-semibold ${
                  data.status === "completed"
                    ? "text-green-600"
                    : "text-orange-600"
                }`}
              >
                {data.status === "completed" ? "완료" : "진행중"}
              </span>
            </span>
          </div>
        </header>

        {/* 점수 카드 */}
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-500 mb-2">점수</h2>
            <p className="text-4xl font-bold text-blue-600">
              {data.score !== null ? data.score.toFixed(1) : "-"}
              <span className="text-lg text-gray-400 ml-2">점</span>
            </p>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-500 mb-2">등급</h2>
            {data.grade_letter ? (
              <div>
                <span
                  className={`inline-block px-4 py-2 rounded-lg text-3xl font-bold ${
                    data.grade_letter === "A"
                      ? "bg-green-100 text-green-800"
                      : data.grade_letter === "B"
                      ? "bg-blue-100 text-blue-800"
                      : data.grade_letter === "C"
                      ? "bg-yellow-100 text-yellow-800"
                      : data.grade_letter === "D"
                      ? "bg-orange-100 text-orange-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {data.grade_letter}
                </span>
                {data.grade_numeric && (
                  <span className="text-gray-400 text-sm ml-2">
                    ({data.grade_numeric}등급)
                  </span>
                )}
              </div>
            ) : (
              <span className="text-gray-400">-</span>
            )}
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-500 mb-2">
              백분위
            </h2>
            <p className="text-4xl font-bold text-purple-600">
              {data.percentile !== null ? data.percentile.toFixed(1) : "-"}
              <span className="text-lg text-gray-400 ml-2">%</span>
            </p>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-500 mb-2">
              정답률
            </h2>
            <p className="text-4xl font-bold text-green-600">
              {accuracy.toFixed(1)}
              <span className="text-lg text-gray-400 ml-2">%</span>
            </p>
          </div>
        </section>

        {/* 기술 정보 (선택적) */}
        {showTechnicalData && (data.theta !== null || data.t_score !== null) && (
          <section className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4 text-blue-900">
              📊 기술 통계 (IRT)
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {data.theta !== null && (
                <div>
                  <div className="text-sm text-blue-700 mb-1">
                    θ (Theta) 능력치
                  </div>
                  <div className="text-2xl font-mono font-bold text-blue-900">
                    {data.theta.toFixed(3)}
                    {data.standard_error !== null && (
                      <span className="text-sm text-blue-600 ml-2">
                        ±{data.standard_error.toFixed(3)}
                      </span>
                    )}
                  </div>
                </div>
              )}
              {data.t_score !== null && (
                <div>
                  <div className="text-sm text-blue-700 mb-1">T-Score</div>
                  <div className="text-2xl font-mono font-bold text-blue-900">
                    {data.t_score.toFixed(1)}
                  </div>
                </div>
              )}
              <div>
                <div className="text-sm text-blue-700 mb-1">평균 응답 시간</div>
                <div className="text-2xl font-bold text-blue-900">
                  {avgResponseTime.toFixed(1)}초
                </div>
              </div>
            </div>
          </section>
        )}

        {/* 문항별 응답 내역 */}
        <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">문항별 응답 내역</h2>
          <div className="space-y-3">
            {data.attempts.map((attempt) => (
              <div
                key={attempt.attempt_number}
                className={`border rounded-lg p-4 ${
                  attempt.is_correct
                    ? "border-green-200 bg-green-50"
                    : "border-red-200 bg-red-50"
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-lg text-gray-700">
                      문항 {attempt.attempt_number}
                    </span>
                    <span
                      className={`px-2 py-1 rounded text-sm font-semibold ${
                        attempt.is_correct
                          ? "bg-green-200 text-green-800"
                          : "bg-red-200 text-red-800"
                      }`}
                    >
                      {attempt.is_correct ? "✓ 정답" : "✗ 오답"}
                    </span>
                    <span className="text-sm text-gray-500">
                      난이도:{" "}
                      <span className="font-mono">
                        {attempt.item_difficulty.toFixed(2)}
                      </span>
                    </span>
                  </div>
                  {attempt.response_time_sec !== null && (
                    <span className="text-sm text-gray-500">
                      {attempt.response_time_sec.toFixed(1)}초
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">학생 답안: </span>
                    <span className="font-mono font-semibold">
                      {attempt.student_response || "(무응답)"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">정답: </span>
                    <span className="font-mono font-semibold text-green-700">
                      {attempt.correct_answer}
                    </span>
                  </div>
                </div>

                {showTechnicalData &&
                  attempt.theta_before !== null &&
                  attempt.theta_after !== null && (
                    <div className="mt-3 pt-3 border-t border-gray-300 flex items-center gap-4 text-sm">
                      <span className="text-gray-600">θ 변화:</span>
                      <span className="font-mono">
                        {attempt.theta_before.toFixed(3)}
                      </span>
                      <span className="text-gray-400">→</span>
                      <span className="font-mono font-semibold">
                        {attempt.theta_after.toFixed(3)}
                      </span>
                      <span
                        className={`ml-2 ${
                          attempt.theta_after > attempt.theta_before
                            ? "text-green-600"
                            : attempt.theta_after < attempt.theta_before
                            ? "text-red-600"
                            : "text-gray-600"
                        }`}
                      >
                        (
                        {attempt.theta_after > attempt.theta_before
                          ? "+"
                          : ""}
                        {(attempt.theta_after - attempt.theta_before).toFixed(
                          3
                        )}
                        )
                      </span>
                    </div>
                  )}
              </div>
            ))}
          </div>

          {data.attempts.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              응답 내역이 없습니다.
            </div>
          )}
        </section>

        {/* 시험 정보 */}
        <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">시험 정보</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">시작 시각: </span>
              <span className="font-semibold">
                {data.started_at
                  ? new Date(data.started_at).toLocaleString("ko-KR")
                  : "-"}
              </span>
            </div>
            <div>
              <span className="text-gray-600">종료 시각: </span>
              <span className="font-semibold">
                {data.ended_at
                  ? new Date(data.ended_at).toLocaleString("ko-KR")
                  : "-"}
              </span>
            </div>
            <div>
              <span className="text-gray-600">소요 시간: </span>
              <span className="font-semibold">
                {data.duration_sec
                  ? `${Math.floor(data.duration_sec / 60)}분 ${
                      data.duration_sec % 60
                    }초`
                  : "-"}
              </span>
            </div>
            <div>
              <span className="text-gray-600">총 문항 수: </span>
              <span className="font-semibold">{data.attempts.length}문항</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
