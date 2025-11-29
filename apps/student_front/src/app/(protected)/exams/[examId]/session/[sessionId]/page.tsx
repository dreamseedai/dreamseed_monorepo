"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  fetchCurrentQuestion,
  submitAnswer,
  fetchExamResult,
  QuestionPayload,
  ExamResultSummary,
} from "@/lib/examClient";

type AnswerState = "idle" | "submitting" | "feedback" | "completed";

export default function ExamSessionPage() {
  const router = useRouter();
  const params = useParams();
  const examId = params.examId as string;
  const sessionId = params.sessionId as string;

  const [question, setQuestion] = useState<QuestionPayload | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [answerState, setAnswerState] = useState<AnswerState>("idle");
  const [answerFeedback, setAnswerFeedback] = useState<{
    correct: boolean;
    explanationHtml?: string | undefined;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [result, setResult] = useState<ExamResultSummary | null>(null);

  // Load initial question
  useEffect(() => {
    async function loadQuestion() {
      try {
        const data = await fetchCurrentQuestion(sessionId);
        setQuestion(data);
        setTimeLeft(data.timeRemainingSeconds);
      } catch (err) {
        console.error("Failed to fetch question:", err);
        setError("문제를 불러오는 데 실패했습니다.");
      } finally {
        setLoading(false);
      }
    }

    loadQuestion();
  }, [sessionId]);

  // Timer countdown
  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0 || answerState !== "idle") return;

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft, answerState]);

  // Auto-submit when time runs out
  useEffect(() => {
    if (timeLeft === 0 && answerState === "idle" && question) {
      handleSubmitAnswer();
    }
  }, [timeLeft, answerState, question]);

  async function handleSubmitAnswer() {
    if (!question || !selectedOptionId) return;

    setAnswerState("submitting");
    setError(null);

    try {
      const feedback = await submitAnswer(sessionId, question.id, selectedOptionId);
      setAnswerFeedback(feedback);
      setAnswerState("feedback");
    } catch (err) {
      console.error("Failed to submit answer:", err);
      setError("답안 제출에 실패했습니다.");
      setAnswerState("idle");
    }
  }

  async function handleNextQuestion() {
    setAnswerState("idle");
    setSelectedOptionId(null);
    setAnswerFeedback(null);
    setLoading(true);
    setError(null);

    try {
      const data = await fetchCurrentQuestion(sessionId);
      setQuestion(data);
      setTimeLeft(data.timeRemainingSeconds);
    } catch (err: any) {
      console.error("Failed to fetch next question:", err);
      
      // If no more questions, fetch results
      if (err?.message?.includes("completed") || err?.status === 404) {
        await handleFetchResults();
      } else {
        setError("다음 문제를 불러오는 데 실패했습니다.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleFetchResults() {
    try {
      const summary = await fetchExamResult(sessionId);
      setResult(summary);
      setAnswerState("completed");
    } catch (err) {
      console.error("Failed to fetch results:", err);
      setError("결과를 불러오는 데 실패했습니다.");
    }
  }

  function formatTime(seconds: number | null): string {
    if (seconds === null) return "무제한";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }

  if (loading && !question) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">문제를 불러오는 중...</div>
      </div>
    );
  }

  if (error && !question) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <div className="text-red-800">{error}</div>
        <button
          onClick={() => router.push(`/exams/${examId}`)}
          className="mt-4 text-sm text-red-600 hover:text-red-800 underline"
        >
          시험 상세로 돌아가기
        </button>
      </div>
    );
  }

  // Show results page
  if (answerState === "completed" && result) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="rounded-lg border bg-white p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">시험 완료!</h1>

          <div className="space-y-6">
            <div className="rounded-lg bg-blue-50 border border-blue-200 p-6 text-center">
              <div className="text-4xl font-bold text-blue-900 mb-2">
                {result.score} / {result.totalScore}
              </div>
              <div className="text-sm text-blue-700">총점</div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg border bg-green-50 p-4 text-center">
                <div className="text-2xl font-bold text-green-900">{result.correctCount}</div>
                <div className="text-xs text-green-700">정답</div>
              </div>
              <div className="rounded-lg border bg-red-50 p-4 text-center">
                <div className="text-2xl font-bold text-red-900">{result.wrongCount}</div>
                <div className="text-xs text-red-700">오답</div>
              </div>
              <div className="rounded-lg border bg-gray-50 p-4 text-center">
                <div className="text-2xl font-bold text-gray-900">{result.omittedCount}</div>
                <div className="text-xs text-gray-700">미응답</div>
              </div>
            </div>

            <div className="flex gap-4 justify-center mt-8">
              <button
                onClick={() => router.push("/exams")}
                className="px-6 py-3 rounded-lg bg-gray-200 hover:bg-gray-300 font-semibold text-gray-900 transition"
              >
                시험 목록으로
              </button>
              <button
                onClick={() => router.push("/results")}
                className="px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 font-semibold text-white transition"
              >
                상세 결과 보기
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!question) {
    return (
      <div className="rounded-lg border bg-white p-12 text-center">
        <div className="text-gray-500">문제를 찾을 수 없습니다.</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header - Progress Bar & Timer */}
      <div className="rounded-lg border bg-white p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="text-sm font-medium text-gray-700">
            문제 {question.questionIndex} / {question.totalQuestions}
          </div>
          <div
            className={`text-sm font-semibold ${
              timeLeft !== null && timeLeft < 60 ? "text-red-600" : "text-gray-700"
            }`}
          >
            {formatTime(timeLeft)}
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full transition-all"
            style={{
              width: `${(question.questionIndex / question.totalQuestions) * 100}%`,
            }}
          ></div>
        </div>
      </div>

      {/* Question Card */}
      <div className="rounded-lg border bg-white p-8">
        <div
          className="prose max-w-none mb-8"
          dangerouslySetInnerHTML={{ __html: question.stemHtml }}
        />

        {/* Options */}
        <div className="space-y-3">
          {question.options.map((option) => (
            <button
              key={option.id}
              onClick={() => {
                if (answerState === "idle") {
                  setSelectedOptionId(option.id);
                }
              }}
              disabled={answerState !== "idle"}
              className={`w-full text-left p-4 rounded-lg border-2 transition ${
                selectedOptionId === option.id
                  ? "border-blue-600 bg-blue-50"
                  : "border-gray-300 hover:border-gray-400 bg-white"
              } ${answerState !== "idle" ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
            >
              <div className="flex items-start gap-3">
                <span className="font-semibold text-gray-700 min-w-[30px]">
                  {option.label}.
                </span>
                <span className="flex-1">{option.text}</span>
              </div>
            </button>
          ))}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}

        {/* Feedback Display */}
        {answerState === "feedback" && answerFeedback && (
          <div
            className={`mt-6 rounded-lg border p-6 ${
              answerFeedback.correct
                ? "border-green-200 bg-green-50"
                : "border-red-200 bg-red-50"
            }`}
          >
            <div
              className={`font-semibold mb-3 ${
                answerFeedback.correct ? "text-green-900" : "text-red-900"
              }`}
            >
              {answerFeedback.correct ? "✓ 정답입니다!" : "✗ 오답입니다."}
            </div>
            <div
              className={`prose max-w-none text-sm ${
                answerFeedback.correct ? "text-green-800" : "text-red-800"
              }`}
              dangerouslySetInnerHTML={{ __html: answerFeedback.explanationHtml || "" }}
            />
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex justify-center gap-4">
          {answerState === "idle" && (
            <button
              onClick={handleSubmitAnswer}
              disabled={!selectedOptionId}
              className={`px-8 py-3 rounded-lg font-semibold text-white transition ${
                selectedOptionId
                  ? "bg-blue-600 hover:bg-blue-700"
                  : "bg-gray-400 cursor-not-allowed"
              }`}
            >
              답안 제출
            </button>
          )}

          {answerState === "submitting" && (
            <button
              disabled
              className="px-8 py-3 rounded-lg font-semibold bg-blue-400 text-white cursor-wait"
            >
              제출 중...
            </button>
          )}

          {answerState === "feedback" && (
            <button
              onClick={handleNextQuestion}
              className="px-8 py-3 rounded-lg font-semibold bg-blue-600 hover:bg-blue-700 text-white transition"
            >
              다음 문제
            </button>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="rounded-lg bg-gray-50 border border-gray-200 p-4">
        <p className="text-xs text-gray-600">
          💡 답안을 선택한 후 "답안 제출" 버튼을 눌러주세요. 제출 후에는 수정할 수 없습니다.
        </p>
      </div>
    </div>
  );
}
