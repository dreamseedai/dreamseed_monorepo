/**
 * TeacherClassDashboard Component
 * 
 * 교사용 반 전체 시험 요약 대시보드
 * API: GET /api/dashboard/teacher/classes/{classId}/exams
 */

import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom"; // Next.js면 useRouter 사용
import axios from "axios";

type ClassExamSummary = {
  class_id: number;
  name: string;
  subject: string;
  grade: string;
  student_count: number;
  exam_sessions: {
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
  students: {
    student_id: number;
    name: string;
    grade: string;
    exam_count: number;
    latest_exam: {
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
    } | null;
  }[];
};

export const TeacherClassDashboard: React.FC = () => {
  const { classId } = useParams<{ classId: string }>();
  const [data, setData] = useState<ClassExamSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!classId) return;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const res = await axios.get(
          `/api/dashboard/teacher/classes/${classId}/exams`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );
        
        setData(res.data);
      } catch (err) {
        console.error('Failed to fetch class dashboard data:', err);
        setError('데이터를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [classId]);

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

  // 반 평균 점수 계산
  const scores = data.exam_sessions
    .map((e) => e.score)
    .filter((s): s is number => typeof s === "number");
  const avgScore =
    scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : null;

  // 등급 분포 계산
  const gradeDistribution: Record<string, number> = {};
  data.exam_sessions.forEach((exam) => {
    if (exam.grade_letter) {
      gradeDistribution[exam.grade_letter] =
        (gradeDistribution[exam.grade_letter] || 0) + 1;
    }
  });

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
            {data.name}
            <span className="text-gray-500 text-xl ml-2">
              ({data.subject} · {data.grade})
            </span>
          </h1>
          <p className="text-sm text-gray-600">
            학생 수: <span className="font-semibold">{data.student_count}</span>명 ·
            최근 시험 수:{" "}
            <span className="font-semibold">{data.exam_sessions.length}</span>건
          </p>
        </header>

        {/* 상단 요약 카드 */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 반 평균 점수 */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <h2 className="text-sm font-semibold text-gray-500 mb-2">
              반 평균 점수
            </h2>
            <p className="text-4xl font-bold text-blue-600">
              {avgScore !== null ? avgScore.toFixed(1) : "-"}
              <span className="text-lg text-gray-400 ml-2">점</span>
            </p>
          </div>

          {/* 시험 수 */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <h2 className="text-sm font-semibold text-gray-500 mb-2">
              완료된 시험
            </h2>
            <p className="text-4xl font-bold text-green-600">
              {data.exam_sessions.length}
              <span className="text-lg text-gray-400 ml-2">건</span>
            </p>
          </div>

          {/* 등급 분포 */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
            <h2 className="text-sm font-semibold text-gray-500 mb-2">
              등급 분포
            </h2>
            <div className="flex gap-2 flex-wrap">
              {Object.entries(gradeDistribution)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([grade, count]) => (
                  <div
                    key={grade}
                    className="px-3 py-1 bg-gray-100 rounded-full text-sm"
                  >
                    <span className="font-semibold">{grade}</span>:{" "}
                    <span className="text-gray-600">{count}</span>
                  </div>
                ))}
              {Object.keys(gradeDistribution).length === 0 && (
                <p className="text-sm text-gray-400">데이터 없음</p>
              )}
            </div>
          </div>
        </section>

        {/* 학생별 요약 테이블 */}
        <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">학생별 최근 시험 요약</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 border-b-2 border-gray-200">
                <tr className="text-left">
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    학생명
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    학년
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700">
                    최근 점수
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
                    응시 횟수
                  </th>
                  <th className="py-3 px-4 font-semibold text-gray-700"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.students.map((student) => {
                  const latest = student.latest_exam;
                  return (
                    <tr
                      key={student.student_id}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <div className="font-medium text-gray-900">
                          {student.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          ID: {student.student_id}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-gray-600">
                        {student.grade}
                      </td>
                      <td className="py-3 px-4">
                        {latest?.score != null ? (
                          <span className="font-semibold text-gray-900">
                            {latest.score.toFixed(1)}점
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {latest?.grade_letter ? (
                          <div className="flex items-center gap-1">
                            <span
                              className={`px-2 py-1 rounded text-xs font-semibold ${
                                latest.grade_letter === "A"
                                  ? "bg-green-100 text-green-800"
                                  : latest.grade_letter === "B"
                                  ? "bg-blue-100 text-blue-800"
                                  : latest.grade_letter === "C"
                                  ? "bg-yellow-100 text-yellow-800"
                                  : latest.grade_letter === "D"
                                  ? "bg-orange-100 text-orange-800"
                                  : "bg-red-100 text-red-800"
                              }`}
                            >
                              {latest.grade_letter}
                            </span>
                            {latest.grade_numeric != null && (
                              <span className="text-gray-400 text-xs">
                                ({latest.grade_numeric}등급)
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {latest?.percentile != null ? (
                          <span className="text-gray-700">
                            {latest.percentile.toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {latest?.theta != null ? (
                          <span className="font-mono text-sm text-gray-700">
                            {latest.theta.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-gray-600">
                        {student.exam_count}회
                      </td>
                      <td className="py-3 px-4">
                        <Link
                          to={`/teacher/dashboard/students/${student.student_id}`}
                          className="text-blue-600 hover:text-blue-800 hover:underline text-sm font-medium"
                        >
                          상세 →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {data.students.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                등록된 학생이 없습니다.
              </div>
            )}
          </div>
        </section>

        {/* 최근 시험 목록 */}
        <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">최근 시험 목록</h2>
          <div className="space-y-3">
            {data.exam_sessions.slice(0, 10).map((exam) => {
              return (
                <div
                  key={exam.exam_session_id}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">
                        시험 #{exam.exam_session_id}
                      </span>
                      <span className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                        {exam.exam_type}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {exam.ended_at
                        ? new Date(exam.ended_at).toLocaleString("ko-KR")
                        : "진행 중"}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-900">
                        {exam.score?.toFixed(1)}점
                      </div>
                      <div className="text-xs text-gray-500">
                        {exam.grade_letter} 등급
                      </div>
                    </div>
                    <Link
                      to={`/dashboard/exams/${exam.exam_session_id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      →
                    </Link>
                  </div>
                </div>
              );
            })}
            {data.exam_sessions.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                완료된 시험이 없습니다.
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};
