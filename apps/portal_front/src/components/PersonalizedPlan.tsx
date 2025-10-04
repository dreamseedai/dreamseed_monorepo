import React, { useState, useEffect } from 'react';
import { api, getToken } from '../lib/api';

interface PersonalizedPlanData {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  estimatedTime: string;
  category: string;
  status: 'pending' | 'in_progress' | 'completed';
}

export default function PersonalizedPlan() {
  const [plans, setPlans] = useState<PersonalizedPlanData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    fetchPersonalizedPlans();
  }, []);

  const fetchPersonalizedPlans = async () => {
    try {
      setLoading(true);
      setError('');
      
      // For now, we'll use mock data since the backend doesn't have this endpoint yet
      // In the future, this would call: await api<PersonalizedPlanData[]>('personalized-plans')
      
      // Mock personalized plan data
      const mockPlans: PersonalizedPlanData[] = [
        {
          id: '1',
          title: 'SAT Math Foundation Review',
          description: 'Focus on algebra and geometry fundamentals to build a strong foundation for SAT math section.',
          priority: 'high',
          estimatedTime: '2-3 weeks',
          category: 'Math',
          status: 'pending'
        },
        {
          id: '2',
          title: 'Reading Comprehension Practice',
          description: 'Improve reading speed and comprehension skills through targeted practice exercises.',
          priority: 'high',
          estimatedTime: '1-2 weeks',
          category: 'Reading',
          status: 'pending'
        },
        {
          id: '3',
          title: 'Writing & Language Grammar',
          description: 'Master essential grammar rules and writing conventions for the SAT writing section.',
          priority: 'medium',
          estimatedTime: '1 week',
          category: 'Writing',
          status: 'pending'
        },
        {
          id: '4',
          title: 'Practice Test Strategy',
          description: 'Learn time management and test-taking strategies through full-length practice tests.',
          priority: 'medium',
          estimatedTime: '2 weeks',
          category: 'Strategy',
          status: 'pending'
        }
      ];

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setPlans(mockPlans);
    } catch (err) {
      setError('Failed to load personalized plan. Please try again.');
      console.error('Error fetching personalized plans:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50 border-green-200';
      case 'in_progress': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'pending': return 'text-gray-600 bg-gray-50 border-gray-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your personalized study plan...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">{error}</p>
          <button 
            onClick={fetchPersonalizedPlans}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Your Personalized Study Plan</h1>
        <p className="text-gray-600">
          Based on your profile and goals, here's your customized learning path to achieve your target score.
        </p>
      </div>

      <div className="grid gap-6">
        {plans.map((plan) => (
          <div key={plan.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{plan.title}</h3>
                <p className="text-gray-600 mb-4">{plan.description}</p>
              </div>
              <div className="flex flex-col gap-2 ml-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getPriorityColor(plan.priority)}`}>
                  {plan.priority.toUpperCase()} PRIORITY
                </span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(plan.status)}`}>
                  {plan.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {plan.estimatedTime}
                </span>
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                  {plan.category}
                </span>
              </div>
              
              <div className="flex gap-2">
                {plan.status === 'pending' && (
                  <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                    Start Plan
                  </button>
                )}
                {plan.status === 'in_progress' && (
                  <button className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors">
                    Continue
                  </button>
                )}
                {plan.status === 'completed' && (
                  <button className="px-4 py-2 bg-gray-600 text-white rounded cursor-not-allowed" disabled>
                    Completed
                  </button>
                )}
                <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors">
                  View Details
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Next Steps</h3>
        <ul className="text-blue-800 space-y-1">
          <li>• Start with high-priority items to maximize your score improvement</li>
          <li>• Complete practice tests regularly to track your progress</li>
          <li>• Focus on your weakest areas first for the biggest impact</li>
          <li>• Review and adjust your plan based on your performance</li>
        </ul>
      </div>
    </div>
  );
}