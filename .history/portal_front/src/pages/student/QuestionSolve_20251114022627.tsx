import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../../lib/api';

interface Question {
  id: string;
  title: string;
  subject: string;
  grade_code: string;
  difficulty_level: string;
  question_type: string;
  content?: string;
  created_at: string;
}

export default function QuestionSolve() {
  const { id } = useParams<{ id: string }>();
  const [question, setQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [aiFeedback, setAiFeedback] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadQuestion();
    }
  }, [id]);

  async function loadQuestion() {
    setLoading(true);
    setError(null);
    try {
      const data = await api<Question>(`/admin/questions/${id}`);
      setQuestion(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load question');
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitted(true);
    setFeedbackLoading(true);
    
    try {
      // Call AI feedback API (포트 8002)
      const response = await fetch('http://localhost:8002/api/ai/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_id: id,
          question_title: question?.title || '',
          question_content: question?.content || '',
          student_answer: answer,
          subject: question?.subject || '',
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setAiFeedback(data.feedback);
      } else {
        setAiFeedback('AI 피드백을 생성할 수 없습니다. 나중에 다시 시도해주세요.');
      }
    } catch (err) {
      console.error('AI feedback error:', err);
      setAiFeedback('AI 서비스에 연결할 수 없습니다.');
    } finally {
      setFeedbackLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">문제를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error || !question) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error || '문제를 찾을 수 없습니다'}
          </div>
          <Link
            to="/student/questions"
            className="mt-4 inline-block text-blue-600 hover:text-blue-700"
          >
            ← 목록으로 돌아가기
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="mb-6">
            <Link
              to="/student/questions"
              className="text-blue-600 hover:text-blue-700 font-medium mb-4 inline-block"
            >
              ← 목록으로
            </Link>

            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              {question.title}
            </h1>

            <div className="flex flex-wrap gap-2 mb-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                {question.subject}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                {question.grade_code}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                {question.difficulty_level}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                {question.question_type}
              </span>
            </div>
          </div>

          {/* Question Content */}
          <div className="mb-8 p-6 bg-gray-50 rounded-lg border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">문제</h2>
            <div className="prose max-w-none">
              {question.content || '문제 내용이 준비 중입니다.'}
            </div>
          </div>

          {/* Answer Form */}
          {!submitted ? (
            <form onSubmit={handleSubmit}>
              <div className="mb-6">
                <label
                  htmlFor="answer"
                  className="block text-lg font-semibold text-gray-900 mb-3"
                >
                  답안 작성
                </label>
                <textarea
                  id="answer"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  rows={8}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="답안을 작성하세요..."
                  required
                />
              </div>

              <div className="flex gap-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                >
                  답안 제출
                </button>
                <button
                  type="button"
                  onClick={() => setAnswer('')}
                  className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  초기화
                </button>
              </div>
            </form>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <svg
                  className="w-6 h-6 text-green-600 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <h3 className="text-lg font-semibold text-green-900">
                  답안이 제출되었습니다!
                </h3>
              </div>
              <p className="text-green-700 mb-4">
                AI 피드백을 준비 중입니다... (Phase 1 MVP - 구현 예정)
              </p>
              <div className="flex gap-4">
                <Link
                  to="/student/questions"
                  className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700"
                >
                  다른 문제 풀기
                </Link>
                <button
                  onClick={() => {
                    setSubmitted(false);
                    setAnswer('');
                  }}
                  className="px-6 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
                >
                  다시 풀기
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
