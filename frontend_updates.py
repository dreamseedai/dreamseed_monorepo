#!/usr/bin/env python3
"""
DreamSeedAI Frontend Updates
Updates frontend components to work with new enhanced schema and adaptive learning
"""

import os
from typing import Dict, List, Any

class FrontendUpdater:
    """Updates frontend components for enhanced functionality"""
    
    def create_question_component(self) -> str:
        """Generate enhanced question component with adaptive learning"""
        return '''
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { MathLive } from 'mathlive';
import { Hint, BookOpen, Clock, Target } from 'lucide-react';

interface QuestionProps {
  question: {
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
  };
  onAnswer: (answer: string, timeSpent: number) => void;
  onHint: (hintIndex: number) => void;
  language?: 'en' | 'ko' | 'zh';
}

export const EnhancedQuestionComponent: React.FC<QuestionProps> = ({
  question,
  onAnswer,
  onHint,
  language = 'en'
}) => {
  const [studentAnswer, setStudentAnswer] = useState('');
  const [timeSpent, setTimeSpent] = useState(0);
  const [hintsUsed, setHintsUsed] = useState<number[]>([]);
  const [showSolution, setShowSolution] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [startTime] = useState(Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeSpent(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, [startTime]);

  const getContent = (field: string) => {
    const content = question.content as any;
    return content[`${field}_${language}`] || content[`${field}_en`] || '';
  };

  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-orange-100 text-orange-800';
      case 'expert': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleHintClick = (hintIndex: number) => {
    if (!hintsUsed.includes(hintIndex)) {
      setHintsUsed([...hintsUsed, hintIndex]);
      onHint(hintIndex);
    }
  };

  const handleSubmitAnswer = () => {
    onAnswer(studentAnswer, timeSpent);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Question Header */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl font-bold">
                {question.title}
              </CardTitle>
              <div className="flex gap-2 mt-2">
                <Badge className={getDifficultyColor(question.metadata.difficulty_level)}>
                  {question.metadata.difficulty_level}
                </Badge>
                <Badge variant="outline">
                  Grade {question.metadata.grade_level}
                </Badge>
                <Badge variant="outline">
                  {question.metadata.subject}
                </Badge>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="w-4 h-4" />
                {Math.floor(timeSpent / 60)}:{(timeSpent % 60).toString().padStart(2, '0')}
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          {/* Question Content */}
          <div className="prose max-w-none mb-6">
            <div 
              className="text-lg leading-relaxed"
              dangerouslySetInnerHTML={{ __html: getContent('question') }}
            />
          </div>

          {/* Math Content */}
          {question.math_content.has_mathml && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold mb-2">Mathematical Expressions:</h4>
              {question.math_content.latex_expressions.map((latex, index) => (
                <div key={index} className="mb-2">
                  <MathLive
                    readOnly
                    value={latex}
                    className="math-expression"
                  />
                </div>
              ))}
            </div>
          )}

          {/* Answer Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              Your Answer:
            </label>
            <textarea
              value={studentAnswer}
              onChange={(e) => setStudentAnswer(e.target.value)}
              className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
              placeholder="Enter your answer here..."
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 mb-6">
            <Button onClick={handleSubmitAnswer} className="bg-blue-600 hover:bg-blue-700">
              Submit Answer
            </Button>
            <Button 
              variant="outline" 
              onClick={() => setShowSolution(!showSolution)}
            >
              <BookOpen className="w-4 h-4 mr-2" />
              {showSolution ? 'Hide' : 'Show'} Solution
            </Button>
          </div>

          {/* Hints */}
          {question.content.hints.length > 0 && (
            <div className="mb-6">
              <h4 className="font-semibold mb-3 flex items-center">
                <Hint className="w-5 h-5 mr-2" />
                Hints ({hintsUsed.length}/{question.content.hints.length})
              </h4>
              <div className="space-y-2">
                {question.content.hints.map((hint, index) => (
                  <div key={hint.id} className="flex items-start gap-3">
                    <Button
                      size="sm"
                      variant={hintsUsed.includes(index) ? "default" : "outline"}
                      onClick={() => handleHintClick(index)}
                      disabled={hintsUsed.includes(index)}
                      className="mt-1"
                    >
                      Hint {index + 1}
                    </Button>
                    {hintsUsed.includes(index) && (
                      <div className="flex-1 p-3 bg-blue-50 rounded-lg">
                        <div dangerouslySetInnerHTML={{ 
                          __html: hint[`hint_text_${language}`] || hint.hint_text_en 
                        }} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Solution */}
          {showSolution && getContent('solution') && (
            <div className="mb-6 p-4 bg-green-50 rounded-lg">
              <h4 className="font-semibold mb-2 text-green-800">Solution:</h4>
              <div 
                className="prose max-w-none text-green-700"
                dangerouslySetInnerHTML={{ __html: getContent('solution') }}
              />
            </div>
          )}

          {/* Explanation */}
          {showExplanation && getContent('explanation') && (
            <div className="mb-6 p-4 bg-purple-50 rounded-lg">
              <h4 className="font-semibold mb-2 text-purple-800">Explanation:</h4>
              <div 
                className="prose max-w-none text-purple-700"
                dangerouslySetInnerHTML={{ __html: getContent('explanation') }}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Adaptive Learning Info */}
      {question.adaptive_learning && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2" />
              Learning Objectives
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {question.adaptive_learning.learning_objectives.length > 0 && (
                <div>
                  <h5 className="font-semibold mb-2">What you'll learn:</h5>
                  <ul className="list-disc list-inside space-y-1">
                    {question.adaptive_learning.learning_objectives.map((objective, index) => (
                      <li key={index} className="text-sm">{objective}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {question.adaptive_learning.prerequisites.length > 0 && (
                <div>
                  <h5 className="font-semibold mb-2">Prerequisites:</h5>
                  <div className="flex flex-wrap gap-2">
                    {question.adaptive_learning.prerequisites.map((prereq, index) => (
                      <Badge key={index} variant="secondary">{prereq}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quality Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Content Quality</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Content Quality</span>
                <span className={getQualityColor(question.quality_metrics.content_quality_score)}>
                  {(question.quality_metrics.content_quality_score * 100).toFixed(0)}%
                </span>
              </div>
              <Progress value={question.quality_metrics.content_quality_score * 100} />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Math Accuracy</span>
                <span className={getQualityColor(question.quality_metrics.math_accuracy_score)}>
                  {(question.quality_metrics.math_accuracy_score * 100).toFixed(0)}%
                </span>
              </div>
              <Progress value={question.quality_metrics.math_accuracy_score * 100} />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Pedagogical Value</span>
                <span className={getQualityColor(question.quality_metrics.pedagogical_value_score)}>
                  {(question.quality_metrics.pedagogical_value_score * 100).toFixed(0)}%
                </span>
              </div>
              <Progress value={question.quality_metrics.pedagogical_value_score * 100} />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Accessibility</span>
                <span className={getQualityColor(question.quality_metrics.accessibility_score)}>
                  {(question.quality_metrics.accessibility_score * 100).toFixed(0)}%
                </span>
              </div>
              <Progress value={question.quality_metrics.accessibility_score * 100} />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
'''
    
    def create_adaptive_learning_dashboard(self) -> str:
        """Generate adaptive learning dashboard component"""
        return '''
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  Target, 
  BookOpen, 
  Clock, 
  Award,
  Brain,
  BarChart3
} from 'lucide-react';

interface LearningAnalytics {
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

interface AdaptiveLearningDashboardProps {
  studentId: string;
  analytics: LearningAnalytics;
  onStartSession: (subject: string) => void;
}

export const AdaptiveLearningDashboard: React.FC<AdaptiveLearningDashboardProps> = ({
  studentId,
  analytics,
  onStartSession
}) => {
  const [selectedSubject, setSelectedSubject] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'all'>('week');

  const overallAccuracy = analytics.overall_performance.total_attempts > 0 
    ? (analytics.overall_performance.correct_attempts / analytics.overall_performance.total_attempts) * 100
    : 0;

  const getMasteryColor = (level: number) => {
    if (level >= 0.8) return 'text-green-600';
    if (level >= 0.6) return 'text-yellow-600';
    if (level >= 0.4) return 'text-orange-600';
    return 'text-red-600';
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty >= 1.5) return 'text-red-600';
    if (difficulty >= 1.2) return 'text-orange-600';
    if (difficulty >= 0.8) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Learning Dashboard</h1>
          <p className="text-gray-600">Track your progress and adaptive learning journey</p>
        </div>
        <div className="flex gap-3">
          <Button onClick={() => onStartSession('mathematics')} className="bg-blue-600">
            <BookOpen className="w-4 h-4 mr-2" />
            Start Math Session
          </Button>
          <Button variant="outline" onClick={() => onStartSession('physics')}>
            Start Physics Session
          </Button>
        </div>
      </div>

      {/* Overall Performance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Overall Accuracy</p>
                <p className="text-2xl font-bold">{overallAccuracy.toFixed(1)}%</p>
              </div>
              <Target className="w-8 h-8 text-blue-600" />
            </div>
            <Progress value={overallAccuracy} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Questions</p>
                <p className="text-2xl font-bold">{analytics.overall_performance.total_attempts}</p>
              </div>
              <BookOpen className="w-8 h-8 text-green-600" />
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {analytics.overall_performance.correct_attempts} correct
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg. Time</p>
                <p className="text-2xl font-bold">
                  {Math.round(analytics.overall_performance.avg_time_per_question / 60)}m
                </p>
              </div>
              <Clock className="w-8 h-8 text-orange-600" />
            </div>
            <p className="text-sm text-gray-500 mt-1">per question</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Current Level</p>
                <p className={`text-2xl font-bold ${getDifficultyColor(analytics.overall_performance.avg_difficulty)}`}>
                  {analytics.overall_performance.avg_difficulty.toFixed(1)}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-600" />
            </div>
            <p className="text-sm text-gray-500 mt-1">difficulty level</p>
          </CardContent>
        </Card>
      </div>

      {/* Subject Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Subject Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {analytics.subject_performance.map((subject) => {
              const accuracy = subject.total_attempts > 0 
                ? (subject.correct_attempts / subject.total_attempts) * 100 
                : 0;
              
              return (
                <div key={subject.subject} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold capitalize">{subject.subject}</h4>
                      <Badge variant="outline">
                        {accuracy.toFixed(1)}% accuracy
                      </Badge>
                    </div>
                    <Progress value={accuracy} className="mb-2" />
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>{subject.correct_attempts}/{subject.total_attempts} correct</span>
                      <span>Avg: {Math.round(subject.avg_time / 60)}m per question</span>
                    </div>
                  </div>
                  <Button 
                    size="sm" 
                    onClick={() => onStartSession(subject.subject)}
                    className="ml-4"
                  >
                    Practice
                  </Button>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Topic Mastery */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Brain className="w-5 h-5 mr-2" />
            Topic Mastery
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {analytics.topic_progress.map((topic) => (
              <div key={`${topic.subject}-${topic.topic}`} className="p-4 border rounded-lg">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h5 className="font-semibold capitalize">{topic.topic}</h5>
                    <p className="text-sm text-gray-600 capitalize">{topic.subject}</p>
                  </div>
                  <Badge 
                    variant={topic.mastery_level >= 0.8 ? "default" : "secondary"}
                    className={getMasteryColor(topic.mastery_level)}
                  >
                    {(topic.mastery_level * 100).toFixed(0)}%
                  </Badge>
                </div>
                <Progress value={topic.mastery_level * 100} className="mb-2" />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>{topic.questions_correct}/{topic.questions_attempted} correct</span>
                  <span className={getDifficultyColor(topic.current_difficulty)}>
                    Level {topic.current_difficulty.toFixed(1)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Sessions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Award className="w-5 h-5 mr-2" />
            Recent Learning Sessions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {analytics.recent_sessions.map((session) => (
              <div key={session.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <Badge variant="outline" className="capitalize">
                      {session.session_type}
                    </Badge>
                    <Badge variant="secondary" className="capitalize">
                      {session.subject}
                    </Badge>
                    <span className="text-sm text-gray-600">
                      {new Date(session.started_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>{session.correct_answers}/{session.total_questions} correct</span>
                    <span>{session.duration_minutes} minutes</span>
                    <span>Score: {session.session_score?.toFixed(1) || 'N/A'}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold">
                    {session.total_questions > 0 
                      ? ((session.correct_answers / session.total_questions) * 100).toFixed(0)
                      : 0}%
                  </div>
                  <div className="text-xs text-gray-500">accuracy</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
'''
    
    def create_frontend_files(self):
        """Create all frontend update files"""
        
        # Create directories
        os.makedirs('frontend_updates/components', exist_ok=True)
        os.makedirs('frontend_updates/hooks', exist_ok=True)
        os.makedirs('frontend_updates/services', exist_ok=True)
        os.makedirs('frontend_updates/types', exist_ok=True)
        
        # Generate component files
        with open('frontend_updates/components/EnhancedQuestionComponent.tsx', 'w', encoding='utf-8') as f:
            f.write(self.create_question_component())
        
        with open('frontend_updates/components/AdaptiveLearningDashboard.tsx', 'w', encoding='utf-8') as f:
            f.write(self.create_adaptive_learning_dashboard())
        
        # Generate API service
        api_service = '''
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
'''
        
        with open('frontend_updates/services/api.ts', 'w', encoding='utf-8') as f:
            f.write(api_service)
        
        # Generate custom hooks
        hooks = '''
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
'''
        
        with open('frontend_updates/hooks/useDreamSeedAI.ts', 'w', encoding='utf-8') as f:
            f.write(hooks)
        
        print("✅ Frontend update files created successfully!")
        print("📁 Files created in 'frontend_updates/' directory:")
        print("   - components/EnhancedQuestionComponent.tsx")
        print("   - components/AdaptiveLearningDashboard.tsx")
        print("   - services/api.ts")
        print("   - hooks/useDreamSeedAI.ts")

def main():
    """Main function to create frontend updates"""
    updater = FrontendUpdater()
    updater.create_frontend_files()

if __name__ == '__main__':
    main()
