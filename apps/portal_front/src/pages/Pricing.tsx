import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';

const BILLING_ENABLED = String(import.meta.env.VITE_BILLING_ENABLED || "false") === "true";
const PAID_READY = String(import.meta.env.VITE_PAID_READY || "false") === "true";

// Badge component
const Badge: React.FC<{ tone?: 'success' | 'warn' | 'info' | 'default'; children: React.ReactNode }> =
  ({ tone = 'default', children }) => {
    const toneClasses = {
      success: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
      warn: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
      info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      default: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${toneClasses[tone]}`}>
        {children}
      </span>
    );
  };

// PlanCard component
const PlanCard: React.FC<{
  title: string;
  price: string;
  blurb: string;
  features: string[];
  cta: string;
  highlight?: boolean;
  disabled?: boolean;
  badge?: React.ReactNode;
  onPlanSelect?: (plan: string) => void;
}> = ({ title, price, blurb, features, cta, highlight = false, disabled = false, badge, onPlanSelect }) => {
  const cardClasses = `
    relative p-6 rounded-2xl border-2 transition-all duration-200
    ${highlight ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700'}
    ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-lg hover:scale-105'}
    bg-white dark:bg-slate-800
  `;

  return (
    <div className={cardClasses}>
      {badge && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          {badge}
        </div>
      )}

      <div className="text-center mb-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">{title}</h3>
        <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">{price}</div>
        <p className="text-gray-600 dark:text-gray-300 text-sm">{blurb}</p>
      </div>

      <ul className="space-y-3 mb-6">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start">
            <svg className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            <span className="text-gray-700 dark:text-gray-300 text-sm">{feature}</span>
          </li>
        ))}
      </ul>

      <button
        className={`
          w-full py-3 px-4 rounded-lg font-medium transition-colors
          ${highlight
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-700 dark:hover:bg-gray-600'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        disabled={disabled}
        onClick={() => {
          if (!disabled && onPlanSelect) {
            onPlanSelect(title);
          }
        }}
      >
        {cta}
      </button>
    </div>
  );
};

export default function PricingPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  function handlePlanSelect(plan: string) {
    if (plan === 'Free') {
      // Start with free account
      console.log('Starting with free account');
      navigate('/');
    } else {
      // Navigate to checkout page
      const planMap: { [key: string]: string } = {
        'Pro': 'pro',
        'Premium': 'premium_student'
      };
      const planParam = planMap[plan] || 'pro';
      navigate(`/checkout?plan=${planParam}`);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Header */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              {t('pricing.title')}
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              {t('pricing.subtitle')}
            </p>
          </div>
        </div>
      </div>

      {/* Pricing Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Status Badge */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {t('plans.status')}
            </span>
            {BILLING_ENABLED && PAID_READY ? (
              <Badge tone="success">{t('plans.note_enabled')}</Badge>
            ) : (
              <Badge tone="warn">{t('plans.note_disabled')}</Badge>
            )}
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid gap-8 md:grid-cols-3 max-w-5xl mx-auto">
          <PlanCard
            title={t('plans.free.name')}
            price={t('plans.free.price')}
            blurb={t('plans.free.blurb')}
            features={t('plans.free.features').split('|')}
            cta={t('plans.free.cta')}
            badge={<Badge>Start</Badge>}
            onPlanSelect={handlePlanSelect}
          />

          <PlanCard
            title={t('plans.pro.name')}
            price={t('plans.pro.price')}
            blurb={t('plans.pro.blurb')}
            features={t('plans.pro.features').split('|')}
            cta={t('plans.pro.cta')}
            highlight
            disabled={!BILLING_ENABLED || !PAID_READY}
            badge={!PAID_READY ? <Badge tone="warn">Coming soon</Badge> : <Badge tone="info">Popular</Badge>}
            onPlanSelect={handlePlanSelect}
          />

          <PlanCard
            title={t('plans.premium.name')}
            price={t('plans.premium.price')}
            blurb={t('plans.premium.blurb')}
            features={t('plans.premium.features').split('|')}
            cta={t('plans.premium.cta')}
            disabled={!BILLING_ENABLED || !PAID_READY}
            badge={!PAID_READY ? <Badge tone="warn">Coming soon</Badge> : <Badge tone="success">Best value</Badge>}
            onPlanSelect={handlePlanSelect}
          />
        </div>

        {/* FAQ Section */}
        <div className="mt-16 max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white text-center mb-8">
            {t('pricing.faq_title')}
          </h2>
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('pricing.faq1_q')}
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                {t('pricing.faq1_a')}
              </p>
            </div>
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('pricing.faq2_q')}
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                {t('pricing.faq2_a')}
              </p>
            </div>
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {t('pricing.faq3_q')}
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                {t('pricing.faq3_a')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
