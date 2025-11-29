/**
 * TutorDashboard Component
 * 
 * 튜터용 전체 학생 요약 대시보드
 * API: GET /api/dashboard/tutor/students/exams
 */

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";

type TutorStudentSummary = {
  tutor_id: number;
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
  statistics: {
    total_students: number;
    students_with_exams: number;
    avg_score: number;
    max_score: number;
    min_score: number;
  } | null;
};

export const TutorDashboard: React.FC = () => {
  const [data, setData] = useState<TutorStudentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState<"name" | "score" | "exam_count">("name");

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await axios.get("/api/dashboard/tutor/students/exams", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        });

        setData(res.data);
      } catch (err) {
        console.error("Failed to fetch tutor dashboard data:", err);
        setError("데이터를 불러오는데 실패했습니다.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

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

  // 필터링 및 정렬
  const filteredStudents = data.students
    .filter((student) =>
      student.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === "name") {
        return a.name.localeCompare(b.name);
      } else if (sortBy === "score") {
        const scoreA = a.latest_exam?.score ?? 0;
        const scoreB = b.latest_exam?.score ?? 0;
        return scoreB - scoreA;
      } else if (sortBy === "exam_count") {
        return b.exam_count - a.exam_count;
      }
      return 0;
    });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* 헤더 */}
        <header className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold">튜터 대시보드</h1>
          <p className="text-sm text-gray-600">
            담당 학생:{" "}
            <span className="font-semibold">{data.students.length}</span>명
          </p>
        </header>

        {/* 통계 카드 */}
        {data.statistics && (
          <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-sm font-semibold text-gray-500 mb-2">
                총 학생 수
              </h2>
              <p className="text-4xl font-bold text-blue-600">
                {data.statistics.total_students}
                <span className="text-lg text-gray-400 ml-2">명</span>
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
                시험 응시
              </h2>
              <p className="text-4xl font-bold text-orange-600">
                {data.statistics.students_with_exams}
                <span className="text-lg text-gray-400 ml-2">명</span>
              </p>
            </div>
          </section>
        )}

        {/* 검색 및 정렬 */}
        <section className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="학생 이름 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setSortBy("name")}
                className={`px-4 py-2 rounded-lg ${
                  sortBy === "name"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                이름순
              </button>
              <button
                onClick={() => setSortBy("score")}
                className={`px-4 py-2 rounded-lg ${
                  sortBy === "score"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                점수순
              </button>
              <button
                onClick={() => setSortBy("exam_count")}
                className={`px-4 py-2 rounded-lg ${
                  sortBy === "exam_count"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                응시횟수순
              </button>
            </div>
          </div>
        </section>

        {/* 학생 목록 */}
        <section className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">학생 목록</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredStudents.map((student) => {
              const latest = student.latest_exam;
              return (
                <Link
                  key={student.student_id}
                  to={`/tutor/dashboard/students/${student.student_id}`}
                  className="block border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-semibold text-lg text-gray-900">
                        {student.name}
                      </h3>
                      <p className="text-sm text-gray-500">{student.grade}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-500">응시</div>
                      <div className="font-semibold text-gray-900">
                        {student.exam_count}회
                      </div>
                    </div>
                  </div>
                  {latest ? (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-xs text-gray-500 mb-1">
                            최근 점수
                          </div>
                          <div className="text-xl font-bold text-blue-600">
                            {latest.score?.toFixed(1)}점
                          </div>
                        </div>
                        <div className="text-right">
                          <div
                            className={`inline-block px-3 py-1 rounded text-sm font-semibold ${
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
                            {latest.grade_letter} 등급
                          </div>
                          {latest.theta !== null && (
                            <div className="text-xs text-gray-500 mt-1">
                              θ = {latest.theta.toFixed(2)}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-3 pt-3 border-t border-gray-100 text-center text-sm text-gray-400">
                      시험 기록 없음
                    </div>
                  )}
                </Link>
              );
            })}
          </div>
          {filteredStudents.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              검색 결과가 없습니다.
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
