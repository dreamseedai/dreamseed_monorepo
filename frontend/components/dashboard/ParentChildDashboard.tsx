/**
 * ParentChildDashboard Component
 * 
 * 학부모용 자녀 시험 히스토리 대시보드
 * API: GET /api/dashboard/parent/children/{studentId}/exams
 */

import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";

type ParentChildExamHistory = {
  student_id: number;
  student_name: string;
  student_grade: string;
  exams: {
    exam_session_id: number;
    exam_type: string;
    date: string;
    duration_sec: number | null;
    score: number | null;
    grade_numeric: number | null;
    grade_letter: string | null;
    percentile: number | null;
  }[];
  statistics: {
    total_exams: number;
    avg_score: number;
    max_score: number;
    min_score: number;
    recent_trend: string;
  } | null;
};

export const ParentChildDashboard: React.FC = () => {
  const { studentId } = useParams<{ studentId: string }>();
  const [data, setData] = useState<ParentChildExamHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await axios.get(
          `/api/dashboard/parent/children/${studentId}/exams`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
          }
        );

        setData(res.data);
      } catch (err) {
        console.error("Failed to fetch parent dashboard data:", err);
        setError("데이터를 불러오는데 실패했습니다.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

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
          <p className="text-red-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            다시 시도
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

  // 점수 추이 데이터
  const scoreData = data.exams
    .filter((e) => e.score !== null)
    .reverse()
    .slice(-10); // 최근 10개

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* 헤더 */}
        <header className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Link
              to="/parent/dashboard"
              className="text-blue-600 hover:underline text-sm"
            >
              ← 대시보드
            </Link>
          </div>
          <h1 className="text-3xl font-bold">
            {data.student_name}
            <span className="text-gray-500 text-xl ml-2">
              ({data.student_grade})
            </span>
          </h1>
        </header>

        {/* 통계 카드 */}
        {data.statistics && (
          <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-sm font-semibold text-gray-500 mb-2">
                총 시험 수
              </h2>
              <p className="text-4xl font-bold text-blue-600">
                {data.statistics.total_exams}
                <span className="text-lg text-gray-400 ml-2">회</span>
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-sm font-semibold text-gray-500 mb-2">
                평균 점수
              </h2>
              <p className="text-4xl font-bold text-green-600">
                {data.statistics.avg_score.toFixed(1)}
                <span className="text-lg text-gray-400 ml-2">점</span>
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-sm font-semibold text-gray-500 mb-2">
                최고 점수
              </h2>
              <p className="text-4xl font-bold text-purple-600">
                {data.statistics.max_score.toFixed(1)}
                <span className="text-lg text-gray-400 ml-2">점</span>
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-sm font-semibold text-gray-500 mb-2">
                성적 추이
              </h2>
              <p className="text-2xl font-bold text-orange-600">
                {data.statistics.recent_trend === "improving"
                  ? "📈 상승"
                  : data.statistics.recent_trend === "declining"
                  ? "📉 하락"
                  : "➡️ 유지"}
              </p>
            </div>
          </section>
        )}

        {/* 점수 추이 그래프 (간단 버전) */}
        {scoreData.length > 0 && (
          <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-4">점수 추이</h2>
            <div className="space-y-3">
              {scoreData.map((exam) => (
                <div key={exam.exam_session_id} className="flex items-center gap-4">
                  <div className="text-sm text-gray-500 w-24">
                    {new Date(exam.date).toLocaleDateString("ko-KR")}
                  </div>
                  <div className="flex-1 flex items-center gap-2">
                    <div className="flex-1 h-10 bg-gray-100 rounded relative overflow-hidden">
                      <div
                        className={`h-full ${
                          exam.score! >= 80
                            ? "bg-green-500"
                            : exam.score! >= 60
                            ? "bg-blue-500"
                            : exam.score! >= 40
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                        style={{
                          width: `${exam.score}%`,
                        }}
                      />
                      <div className="absolute inset-0 flex items-center px-3">
                        <span className="text-sm font-semibold text-gray-700">
                          {exam.score?.toFixed(1)}점
                        </span>
                      </div>
                    </div>
                    <span
                      className={`px-3 py-1 rounded text-sm font-semibold ${
                        exam.grade_letter === "A"
                          ? "bg-green-100 text-green-800"
                          : exam.grade_letter === "B"
                          ? "bg-blue-100 text-blue-800"
                          : exam.grade_letter === "C"
                          ? "bg-yellow-100 text-yellow-800"
                          : exam.grade_letter === "D"
                          ? "bg-orange-100 text-orange-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {exam.grade_letter}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 시험 히스토리 테이블 */}
        <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">시험 히스토리</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 border-b-2 border-gray-200">
                <tr className="text-left">
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    시험 날짜
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    타입
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    소요 시간
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    점수
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    등급
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    상위 비율
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.exams.map((exam) => (
                  <tr
                    key={exam.exam_session_id}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="py-3 px-4 text-gray-600">
                      {new Date(exam.date).toLocaleDateString("ko-KR")}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                        {exam.exam_type === "mock"
                          ? "모의고사"
                          : exam.exam_type === "practice"
                          ? "연습"
                          : "배치고사"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-600">
                      {exam.duration_sec
                        ? `${Math.floor(exam.duration_sec / 60)}분`
                        : "-"}
                    </td>
                    <td className="py-3 px-4">
                      {exam.score !== null ? (
                        <span className="font-semibold text-gray-900">
                          {exam.score.toFixed(1)}점
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {exam.grade_letter ? (
                        <div className="flex items-center gap-1">
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold ${
                              exam.grade_letter === "A"
                                ? "bg-green-100 text-green-800"
                                : exam.grade_letter === "B"
                                ? "bg-blue-100 text-blue-800"
                                : exam.grade_letter === "C"
                                ? "bg-yellow-100 text-yellow-800"
                                : exam.grade_letter === "D"
                                ? "bg-orange-100 text-orange-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {exam.grade_letter}
                          </span>
                          {exam.grade_numeric && (
                            <span className="text-gray-400 text-xs">
                              ({exam.grade_numeric}등급)
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {exam.percentile !== null ? (
                        <span className="text-gray-700">
                          상위 {(100 - exam.percentile).toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.exams.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                시험 기록이 없습니다.
              </div>
            )}
          </div>
        </section>

        {/* 안내 메시지 */}
        <section className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <p className="text-sm text-blue-800">
            💡 <strong>적응형 시험(CAT)</strong>은 학생의 능력에 맞는 문제를 자동으로
            선택하여 출제합니다. 점수가 낮더라도 학생의 실력에 맞는 문제로 평가되고
            있으니 걱정하지 마세요!
          </p>
        </section>
      </div>
    </div>
  );
};
