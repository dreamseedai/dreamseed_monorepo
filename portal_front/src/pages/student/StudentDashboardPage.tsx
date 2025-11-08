/**
 * Student Emotive Dashboard Page
 * ===============================
 * Clean, emotive UI for student mood tracking, goals, and AI encouragement.
 * 
 * Features:
 * - Weekly growth display
 * - Mood tracking (happy/neutral/sad)
 * - Study streak counter
 * - Goal management
 * - AI-generated encouragement messages
 * 
 * Requires:
 * - JWT/session with 'student' role
 * - Valid tenant_id and user_id (student_id)
 */
import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

type Goal = {
  id: string;
  title: string;
  target_date?: string | null;
  done?: boolean;
};

type DashboardData = {
  week_growth: number;
  today_mood?: string | null;
  streak_days: number;
  goals: Goal[];
  ai_message?: string | null;
  ai_tone?: string | null;
};

export default function StudentDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard data
  const fetchDashboard = async () => {
    try {
      const response = await fetch('/api/student/dashboard', {
        headers: { 'Accept': 'application/json' }
      });
      
      if (\!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const json = await response.json();
      setData(json);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  // Set mood
  const setMood = async (mood: string) => {
    try {
      const response = await fetch('/api/student/mood', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mood })
      });
      
      if (\!response.ok) {
        throw new Error('Failed to set mood');
      }
      
      // Refresh dashboard
      await fetchDashboard();
    } catch (err) {
      console.error('Error setting mood:', err);
    }
  };

  // Add goal
  const addGoal = async () => {
    const title = prompt('오늘의 목표를 적어주세요 (예: 인수분해 3문제 풀기)');
    if (\!title) return;

    try {
      const response = await fetch('/api/student/goals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title })
      });
      
      if (\!response.ok) {
        throw new Error('Failed to add goal');
      }
      
      // Refresh dashboard
      await fetchDashboard();
    } catch (err) {
      console.error('Error adding goal:', err);
      alert('목표 추가에 실패했습니다');
    }
  };

  // Complete goal
  const completeGoal = async (goalId: string) => {
    try {
      const response = await fetch(`/api/student/goals/${goalId}/done`, {
        method: 'POST'
      });
      
      if (\!response.ok) {
        throw new Error('Failed to complete goal');
      }
      
      // Refresh dashboard
      await fetchDashboard();
    } catch (err) {
      console.error('Error completing goal:', err);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-500">로딩중…</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <Card className="p-6 max-w-md">
          <div className="text-lg font-semibold text-red-600 mb-2">오류 발생</div>
          <div className="text-gray-600">{error}</div>
          <Button onClick={fetchDashboard} className="mt-4">다시 시도</Button>
        </Card>
      </div>
    );
  }

  // No data
  if (\!data) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="text-lg text-gray-500">데이터 없음</div>
      </div>
    );
  }

  // Main dashboard
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-3xl font-bold text-gray-800">나의 하루 ✨</div>

      {/* Stats Cards */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* Weekly Growth */}
        <Card className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <div className="text-sm text-blue-600 font-medium mb-2">이번 주 성장률</div>
          <div className="text-4xl font-bold text-blue-700">
            {data.week_growth >= 0 ? '+' : ''}{data.week_growth.toFixed(2)}
          </div>
          <div className="text-sm text-blue-600 mt-2">작게라도 매일 전진 ✨</div>
        </Card>

        {/* Mood Selector */}
        <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <div className="text-sm text-purple-600 font-medium mb-3">오늘의 기분</div>
          <div className="flex gap-2">
            {[
              { mood: 'happy', emoji: '😊', label: '좋아요' },
              { mood: 'neutral', emoji: '😐', label: '보통' },
              { mood: 'sad', emoji: '😞', label: '힘들어요' }
            ].map(({ mood, emoji, label }) => (
              <Button
                key={mood}
                variant={data.today_mood === mood ? 'default' : 'secondary'}
                onClick={() => setMood(mood)}
                className="flex-1 flex flex-col items-center py-3"
              >
                <span className="text-2xl mb-1">{emoji}</span>
                <span className="text-xs">{label}</span>
              </Button>
            ))}
          </div>
        </Card>

        {/* Streak Counter */}
        <Card className="p-6 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <div className="text-sm text-green-600 font-medium mb-2">연속 학습</div>
          <div className="text-4xl font-bold text-green-700">{data.streak_days}일</div>
          <div className="text-sm text-green-600 mt-2">작은 꾸준함이 큰 힘 💪</div>
        </Card>
      </div>

      {/* Goals Section */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="text-xl font-semibold text-gray-800">오늘의 목표 🎯</div>
          <Button onClick={addGoal} variant="default">
            + 목표 추가
          </Button>
        </div>

        {data.goals.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-lg mb-2">아직 목표가 없어요</div>
            <div className="text-sm">오늘 달성하고 싶은 작은 목표를 추가해보세요\!</div>
          </div>
        ) : (
          <ul className="space-y-3">
            {data.goals.map((goal) => (
              <li
                key={goal.id}
                className="flex items-center justify-between bg-white rounded-xl p-4 shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={goal.done}
                    onChange={() => completeGoal(goal.id)}
                    className="w-5 h-5 rounded border-gray-300"
                  />
                  <span className={goal.done ? 'line-through text-gray-400' : 'text-gray-800'}>
                    {goal.title}
                  </span>
                </div>
                {goal.target_date && (
                  <span className="text-sm text-gray-500">
                    📅 {new Date(goal.target_date).toLocaleDateString('ko-KR')}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* AI Encouragement Message */}
      {data.ai_message && (
        <Card className="p-6 bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200">
          <div className="flex items-start gap-3">
            <div className="text-3xl">🤖</div>
            <div className="flex-1">
              <div className="text-sm font-medium text-orange-600 mb-2">
                AI 응원 메시지 {data.ai_tone === 'gentle' ? '💖' : data.ai_tone === 'energetic' ? '⚡' : '✨'}
              </div>
              <div className="text-base text-gray-800 leading-relaxed">
                {data.ai_message}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
