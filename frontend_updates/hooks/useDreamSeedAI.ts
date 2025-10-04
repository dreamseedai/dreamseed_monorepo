
import { useState, useEffect, useCallback } from 'react';
import { dreamSeedAIService, Question, LearningAnalytics } from '../services/api';

// Hook for managing question state
export const useQuestion = (questionId: string) => {
  const [question, setQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchQuestion = async () => {
      try {
        setLoading(true);
        const data = await dreamSeedAIService.getQuestion(questionId);
        setQuestion(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch question');
      } finally {
        setLoading(false);
      }
    };

    if (questionId) {
      fetchQuestion();
    }
  }, [questionId]);

  return { question, loading, error };
};

// Hook for adaptive learning session
export const useLearningSession = (studentId: string) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startSession = useCallback(async (subject: string, sessionType: string = 'practice') => {
    try {
      setLoading(true);
      const response = await dreamSeedAIService.createLearningSession({
        student_id: studentId,
        session_type: sessionType,
        subject,
        initial_difficulty: 1.0
      });
      setSessionId(response.session_id);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start session');
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  const recordAttempt = useCallback(async (data: {
    question_id: string;
    student_answer?: string;
    is_correct: boolean;
    time_spent_seconds: number;
    difficulty_at_attempt: number;
    hints_used?: number;
  }) => {
    if (!sessionId) return null;

    try {
      const response = await dreamSeedAIService.recordQuestionAttempt({
        ...data,
        session_id: sessionId,
        student_id: studentId
      });
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record attempt');
      return null;
    }
  }, [sessionId, studentId]);

  return {
    sessionId,
    loading,
    error,
    startSession,
    recordAttempt
  };
};

// Hook for student analytics
export const useStudentAnalytics = (studentId: string) => {
  const [analytics, setAnalytics] = useState<LearningAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const data = await dreamSeedAIService.getStudentAnalytics(studentId);
        setAnalytics(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
      } finally {
        setLoading(false);
      }
    };

    if (studentId) {
      fetchAnalytics();
    }
  }, [studentId]);

  const refreshAnalytics = useCallback(async () => {
    if (studentId) {
      try {
        setLoading(true);
        const data = await dreamSeedAIService.getStudentAnalytics(studentId);
        setAnalytics(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
      } finally {
        setLoading(false);
      }
    }
  }, [studentId]);

  return { analytics, loading, error, refreshAnalytics };
};

// Hook for personalized questions
export const usePersonalizedQuestions = (studentId: string, subject: string) => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQuestions = useCallback(async (limit: number = 10) => {
    try {
      setLoading(true);
      const data = await dreamSeedAIService.getPersonalizedQuestions(studentId, subject, limit);
      setQuestions(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch personalized questions');
    } finally {
      setLoading(false);
    }
  }, [studentId, subject]);

  useEffect(() => {
    if (studentId && subject) {
      fetchQuestions();
    }
  }, [studentId, subject, fetchQuestions]);

  return { questions, loading, error, fetchQuestions };
};
