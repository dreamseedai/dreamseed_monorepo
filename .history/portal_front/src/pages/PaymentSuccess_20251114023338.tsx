import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

interface SubscriptionStatus {
  user_email: string;
  is_active: boolean;
  plan_name: string | null;
  started_at: string | null;
  expires_at: string | null;
}

export default function PaymentSuccess() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (sessionId) {
      // Extract email from session_id (mock format: mock_session_{email}_{plan}_{timestamp})
      const parts = sessionId.split('_');
      const email = parts[2] || 'demo@dreamseed.ai';
      loadSubscription(email);
    }
  }, [sessionId]);

  async function loadSubscription(email: string) {
    try {
      const response = await fetch(
        `http://localhost:8002/api/payment/subscription/${encodeURIComponent(email)}`
      );
      if (response.ok) {
        const data = await response.json();
        setSubscription(data);
      }
    } catch (err) {
      console.error('Failed to load subscription:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
          <p className="mt-4 text-gray-600">구독 정보를 확인하는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg
              className="w-12 h-12 text-green-600"
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
          </div>

          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            🎉 구독이 완료되었습니다!
          </h1>

          {subscription && subscription.is_active ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <h2 className="text-xl font-semibold text-green-900 mb-4">
                {subscription.plan_name}
              </h2>
              <div className="text-left space-y-2">
                <p className="text-gray-700">
                  <span className="font-medium">이메일:</span> {subscription.user_email}
                </p>
                <p className="text-gray-700">
                  <span className="font-medium">시작일:</span>{' '}
                  {subscription.started_at
                    ? new Date(subscription.started_at).toLocaleDateString('ko-KR')
                    : '-'}
                </p>
                <p className="text-gray-700">
                  <span className="font-medium">만료일:</span>{' '}
                  {subscription.expires_at
                    ? new Date(subscription.expires_at).toLocaleDateString('ko-KR')
                    : '-'}
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
              <p className="text-yellow-800">구독 정보를 찾을 수 없습니다.</p>
            </div>
          )}

          <div className="space-y-4">
            <p className="text-gray-600">
              이제 모든 기능을 사용할 수 있습니다!
            </p>

            <div className="flex gap-4 justify-center">
              <Link
                to="/student/questions"
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                문제 풀이 시작하기
              </Link>
              <Link
                to="/"
                className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg font-medium hover:bg-gray-300 transition-colors"
              >
                홈으로
              </Link>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              💡 Phase 1 MVP: Mock 결제 시스템
            </p>
            <p className="text-xs text-gray-400 mt-1">
              실제 Stripe 결제는 Phase 2에서 통합됩니다
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
