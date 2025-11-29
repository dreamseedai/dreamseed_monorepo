/**
 * TeacherStudentDashboard Component
 * 
 * 교사용 개별 학생 시험 히스토리 대시보드
 * API: GET /api/dashboard/teacher/students/{studentId}/exams
 */

import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";

type StudentExamHistory = {
  student_id: number;
  student_name: string;
  student_grade: string;
  exams: {
    exam_session_id: number;
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
  }[];
  statistics: {
    total_exams: number;
    avg_score: number;
    max_score: number;
    min_score: number;
    latest_score: number;
  } | null;
};

export const TeacherStudentDashboard: React.FC = () => {
  const { studentId } = useParams<{ studentId: string }>();
  const [data, setData] = useState<StudentExamHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await axios.get(
          `/api/dashboard/teacher/students/${studentId}/exams`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
          }
        );

        setData(res.data);
      } catch (err) {
        console.error("Failed to fetch student dashboard data:", err);
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

  // Theta 추이 데이터
  const thetaData = data.exams
    .filter((e) => e.theta !== null)
    .reverse()
    .map((e, idx) => ({
      index: idx + 1,
      theta: e.theta!,
      date: e.ended_at ? new Date(e.ended_at).toLocaleDateString("ko-KR") : "",
    }));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* 헤더 */}
        <header className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Link
              to="/teacher/dashboard"
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
          <p className="text-sm text-gray-600">
            학생 ID: <span className="font-semibold">{data.student_id}</span>
          </p>
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
                최근 점수
              </h2>
              <p className="text-4xl font-bold text-orange-600">
                {data.statistics.latest_score.toFixed(1)}
                <span className="text-lg text-gray-400 ml-2">점</span>
              </p>
            </div>
          </section>
        )}

        {/* Theta 추이 그래프 (간단 버전) */}
        {thetaData.length > 0 && (
          <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-4">θ (Theta) 능력치 추이</h2>
            <div className="space-y-2">
              {thetaData.map((point, idx) => (
                <div key={idx} className="flex items-center gap-4">
                  <div className="text-sm text-gray-500 w-20">{point.date}</div>
                  <div className="flex-1 flex items-center gap-2">
                    <div className="flex-1 h-8 bg-gray-100 rounded relative overflow-hidden">
                      <div
                        className={`h-full ${
                          point.theta >= 0 ? "bg-blue-500" : "bg-red-500"
                        }`}
                        style={{
                          width: `${Math.abs(point.theta) * 16.67}%`,
                          marginLeft: point.theta >= 0 ? "50%" : "auto",
                          marginRight: point.theta < 0 ? "50%" : "auto",
                        }}
                      />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-xs font-mono font-semibold text-gray-700">
                          {point.theta.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 text-xs text-gray-500">
              * θ(Theta)는 IRT 기반 능력 추정치입니다. 0을 중심으로 -3 ~ +3 범위입니다.
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
                    시험 ID
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    타입
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    날짜
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    점수
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    등급
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    백분위
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    θ (Theta)
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    SE
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.exams.map((exam) => (
                  <tr
                    key={exam.exam_session_id}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="py-3 px-4 font-mono text-gray-600">
                      #{exam.exam_session_id}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                        {exam.exam_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-600">
                      {exam.ended_at
                        ? new Date(exam.ended_at).toLocaleDateString("ko-KR")
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
                              ({exam.grade_numeric})
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
                          {exam.percentile.toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {exam.theta !== null ? (
                        <span className="font-mono text-sm text-gray-700">
                          {exam.theta.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {exam.standard_error !== null ? (
                        <span className="font-mono text-xs text-gray-500">
                          ±{exam.standard_error.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <Link
                        to={`/dashboard/exams/${exam.exam_session_id}`}
                        className="text-blue-600 hover:text-blue-800 hover:underline text-sm font-medium"
                      >
                        상세 →
                      </Link>
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
      </div>
    </div>
  );
};
