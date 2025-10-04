
// Enhanced API service for DreamSeedAI
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v2';

export interface Question {
  id: string;
  title: string;
  content: {
    question_en: string;
    question_ko?: string;
    question_zh?: string;
    answer_en?: string;
    solution_en?: string;
    explanation_en?: string;
    hints: Array<{
      id: string;
      hint_text_en: string;
      hint_text_ko?: string;
      hint_text_zh?: string;
      hint_order: number;
    }>;
  };
  metadata: {
    subject: string;
    grade_level: number;
    difficulty_level: string;
    difficulty_score: number;
    topics: string[];
    question_type: string;
  };
  math_content: {
    has_mathml: boolean;
    latex_expressions: string[];
    math_complexity: string;
  };
  adaptive_learning?: {
    prerequisites: string[];
    learning_objectives: string[];
    assessment_criteria: string[];
    min_difficulty: number;
    max_difficulty: number;
    optimal_difficulty: number;
    success_indicators: string[];
  };
  quality_metrics: {
    content_quality_score: number;
    math_accuracy_score: number;
    pedagogical_value_score: number;
    accessibility_score: number;
  };
}

export interface LearningAnalytics {
  overall_performance: {
    total_attempts: number;
    correct_attempts: number;
    avg_time_per_question: number;
    avg_difficulty: number;
  };
  subject_performance: Array<{
    subject: string;
    total_attempts: number;
    correct_attempts: number;
    avg_time: number;
    avg_difficulty: number;
  }>;
  topic_progress: Array<{
    subject: string;
    topic: string;
    mastery_level: number;
    questions_attempted: number;
    questions_correct: number;
    current_difficulty: number;
    learning_velocity: number;
  }>;
  recent_sessions: Array<{
    id: string;
    session_type: string;
    subject: string;
    total_questions: number;
    correct_answers: number;
    session_score: number;
    duration_minutes: number;
    started_at: string;
    completed_at?: string;
  }>;
}

class DreamSeedAIService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Question endpoints
  async getQuestion(questionId: string): Promise<Question> {
    const response = await this.api.get(`/questions/${questionId}`);
    return response.data;
  }

  async getQuestions(filters: {
    subject?: string;
    grade_level?: number;
    difficulty_level?: string;
    topics?: string[];
    has_mathml?: boolean;
    limit?: number;
    offset?: number;
  } = {}): Promise<Question[]> {
    const response = await this.api.get('/questions', { params: filters });
    return response.data;
  }

  async searchQuestions(query: string, language: string = 'en', limit: number = 20): Promise<Question[]> {
    const response = await this.api.get('/questions/search', {
      params: { q: query, language, limit }
    });
    return response.data;
  }

  async getPersonalizedQuestions(studentId: string, subject: string, limit: number = 10): Promise<Question[]> {
    const response = await this.api.post('/questions/personalized', {
      student_id: studentId,
      subject,
      limit
    });
    return response.data;
  }

  async getQuestionStatistics(): Promise<any> {
    const response = await this.api.get('/questions/statistics');
    return response.data;
  }

  // Adaptive Learning endpoints
  async createLearningSession(data: {
    student_id: string;
    session_type: string;
    subject: string;
    grade_level?: number;
    initial_difficulty?: number;
  }): Promise<{ session_id: string }> {
    const response = await this.api.post('/learning/sessions', data);
    return response.data;
  }

  async recordQuestionAttempt(data: {
    session_id: string;
    question_id: string;
    student_id: string;
    student_answer?: string;
    is_correct: boolean;
    time_spent_seconds: number;
    attempts_count?: number;
    difficulty_at_attempt: number;
    hints_used?: number;
  }): Promise<{
    attempt_id: string;
    new_difficulty: number;
    success: boolean;
  }> {
    const response = await this.api.post('/learning/attempts', data);
    return response.data;
  }

  async getStudentAnalytics(studentId: string): Promise<LearningAnalytics> {
    const response = await this.api.get(`/learning/analytics/${studentId}`);
    return response.data;
  }
}

export const dreamSeedAIService = new DreamSeedAIService();
