
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
