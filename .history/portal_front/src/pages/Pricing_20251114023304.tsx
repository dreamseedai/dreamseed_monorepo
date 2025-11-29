import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

interface Plan {
  id: string;
  name: string;
  price: number;
  currency: string;
  interval: string;
  features: string[];
}

export default function Pricing() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState('demo@dreamseed.ai');

  useEffect(() => {
    loadPlans();
  }, []);

  async function loadPlans() {
    try {
      const response = await fetch('http://localhost:8002/api/payment/plans');
      if (!response.ok) throw new Error('Failed to load plans');
      const data = await response.json();
      setPlans(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubscribe(planId: string) {
    try {
      const response = await fetch('http://localhost:8002/api/payment/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan_id: planId,
          user_email: userEmail,
        }),
      });

      if (!response.ok) throw new Error('Checkout failed');

      const data = await response.json();
      // Redirect to checkout (or success page in mock mode)
      window.location.href = data.checkout_url;
    } catch (err: any) {
      alert('구독 처리 중 오류가 발생했습니다: ' + err.message);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">플랜을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            DreamSeed 구독 플랜
          </h1>
          <p className="text-xl text-gray-600">
            AI 기반 학습으로 목표를 달성하세요
          </p>
          <Link
            to="/"
            className="mt-4 inline-block text-blue-600 hover:text-blue-700"
          >
            ← 홈으로 돌아가기
          </Link>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6 max-w-2xl mx-auto">
            {error}
          </div>
        )}

        {/* Demo Email Input */}
        <div className="max-w-md mx-auto mb-8">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            사용자 이메일 (데모용)
          </label>
          <input
            type="email"
            value={userEmail}
            onChange={(e) => setUserEmail(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="your@email.com"
          />
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`bg-white rounded-2xl shadow-xl overflow-hidden transform transition-all hover:scale-105 ${
                plan.id === 'basic_monthly' ? 'border-2 border-blue-500' : ''
              }`}
            >
              {plan.id === 'basic_monthly' && (
                <div className="bg-blue-500 text-white text-center py-2 text-sm font-semibold">
                  🎓 Phase 1 MVP 추천
                </div>
              )}

              <div className="p-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  {plan.name}
                </h3>
                <div className="mb-6">
                  <span className="text-5xl font-extrabold text-gray-900">
                    ${plan.price}
                  </span>
                  <span className="text-gray-600 ml-2">/ {plan.interval}</span>
                </div>

                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start">
                      <svg
                        className="w-6 h-6 text-green-500 mr-2 flex-shrink-0"
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
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleSubscribe(plan.id)}
                  className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${
                    plan.id === 'basic_monthly'
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-800 text-white hover:bg-gray-900'
                  }`}
                >
                  구독하기
                </button>

                {plan.id === 'basic_monthly' && (
                  <p className="mt-4 text-center text-sm text-gray-500">
                    Phase 1 MVP - Mock 결제 (즉시 활성화)
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center text-gray-600">
          <p className="mb-2">💳 Phase 1 MVP: Mock 결제 시스템</p>
          <p className="text-sm">
            실제 Stripe 결제는 Phase 2에서 통합됩니다
          </p>
        </div>
      </div>
    </div>
  );
}
