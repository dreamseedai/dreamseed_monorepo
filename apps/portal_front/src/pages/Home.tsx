import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import TopMpcBanner from '../components/TopMpcBanner';
import ProfileSelect from '../components/ProfileSelect';
import CategoryGrid from '../components/CategoryGrid';
import MyPlanPanel from '../components/MyPlanPanel';
import { startCheckout } from '../lib/pay';
import { postDiagnosticsRun } from '../api/client';
import type { DiagnosticRequest } from '../api/types/profile';

// Environment variables
const BILLING_ENABLED = import.meta.env.VITE_BILLING_ENABLED === 'true';
const PAID_READY = import.meta.env.VITE_PAID_READY === 'true';

// English text content
const t = {
  hero_title: "Plan your path with DreamSeedAI",
  hero_subtitle: "Personalised guides, study plans, and expert recommendations for US/CA students",
  hero_cta: "Browse US Guides",
  quick_start_title: "Quick Start",
  quick_start_subtitle: "Select your country, grade, and goals to get a personalized study plan",
  modules_title: "Learning Modules",
  plans_title: "Pricing Plans",
  plans_note_enabled: "Billing Enabled",
  plans_note_disabled: "Content Loading...",
  free: {
    name: "Free",
    price: "Free",
    blurb: "Basic learning materials and guides",
    features: [
      "Basic study guides",
      "Limited problem solving",
      "Community support",
      "Basic AI recommendations"
    ],
    cta: "Start Free"
  },
  pro: {
    name: "Pro",
    price: "$25/month",
    blurb: "Personalized study plans and advanced features",
    features: [
      "Personalized study plans",
      "Unlimited problem solving",
      "Advanced AI recommendations",
      "Progress tracking",
      "Priority support"
    ],
    cta: "Upgrade to Pro"
  },
  premium: {
    name: "Premium",
    price: "$99/month (Student)",
    blurb: "Premium features with 1:1 mentoring",
    features: [
      "All Pro features",
      "1:1 mentoring sessions",
      "Advanced analytics dashboard",
      "Expert consultation",
      "Priority support",
      "Family/School packages available"
    ],
    cta: "Upgrade to Premium"
  }
};

// Badge component
const Badge: React.FC<{ tone?: 'success' | 'warn' | 'info' | 'default'; children: React.ReactNode }> = ({ 
  tone = 'default', 
  children 
}) => {
  const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
  const toneClasses = {
    success: "bg-green-100 text-green-800",
    warn: "bg-yellow-100 text-yellow-800",
    info: "bg-blue-100 text-blue-800",
    default: "bg-gray-100 text-gray-800"
  };
  
  return (
    <span className={`${baseClasses} ${toneClasses[tone]}`}>
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

// Selector component (Country/Grade/Goal selection)
const Selector: React.FC<{ onDiagnosticsComplete?: (result: any, context: any) => void }> = ({ onDiagnosticsComplete }) => {
  const [country, setCountry] = useState('US');
  const [grade, setGrade] = useState('G11');
  const [goal, setGoal] = useState('SAT1500');
  const [isLoading, setIsLoading] = useState(false);

  const countries = [
    { value: 'US', label: 'United States (US)' },
    { value: 'CA', label: 'Canada (CA)' }
  ];

  const grades = [
    { value: 'G9', label: 'Grade 9' },
    { value: 'G10', label: 'Grade 10' },
    { value: 'G11', label: 'Grade 11' },
    { value: 'G12', label: 'Grade 12' }
  ];

  const goals = [
    { value: 'SAT_1500_PLUS', label: 'SAT 1500+' },
    { value: 'ACT_35_PLUS', label: 'ACT 35+' },
    { value: 'AP_5', label: 'AP Score 5' },
    { value: 'IB_7', label: 'IB Score 7' }
  ];

  const handleDiagnostics = async () => {
    setIsLoading(true);
    try {
      const request: DiagnosticRequest = {
        userId: 'demo-user',
        context: {
          country: country as any,
          grade: grade as any,
          goal: goal as any
        }
      };

      const result = await postDiagnosticsRun(request);
      const context = { country, grade, goal };
      
      if (onDiagnosticsComplete) {
        onDiagnosticsComplete(result, context);
      }
    } catch (error) {
      console.error('Diagnostics failed:', error);
      alert('Diagnostics failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Country
          </label>
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
          >
            {countries.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Grade
          </label>
          <select
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
          >
            {grades.map((g) => (
              <option key={g.value} value={g.value}>{g.label}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Goal
          </label>
          <select
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
          >
            {goals.map((g) => (
              <option key={g.value} value={g.value}>{g.label}</option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="mt-4 text-center">
        <button
          onClick={handleDiagnostics}
          disabled={isLoading}
          className={`
            px-6 py-3 rounded-lg font-medium transition-colors
            ${isLoading 
              ? 'bg-gray-400 text-white cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700 text-white'
            }
          `}
        >
          {isLoading ? 'Running diagnostics...' : 'Get My Strategy'}
        </button>
      </div>
    </>
  );
};

// Modules component
const Modules: React.FC = () => {
  const modules = [
    { name: 'English', icon: '📖', description: 'Literature and Writing' },
    { name: 'Math', icon: '➗', description: 'Mathematics and Statistics' },
    { name: 'Science', icon: '🔬', description: 'Science and Experiments' },
    { name: 'Social Studies', icon: '🌍', description: 'Social Sciences' },
    { name: 'AP Courses', icon: '🎓', description: 'Advanced Placement' },
    { name: 'Test Prep', icon: '📝', description: 'Test Preparation' }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {modules.map((module, index) => (
        <div
          key={index}
          className="p-4 rounded-xl bg-white dark:bg-slate-800 border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow cursor-pointer"
        >
          <div className="text-2xl mb-2">{module.icon}</div>
          <h4 className="font-semibold text-gray-900 dark:text-white mb-1">{module.name}</h4>
          <p className="text-xs text-gray-600 dark:text-gray-400">{module.description}</p>
        </div>
      ))}
    </div>
  );
};

export default function HomePage() {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState<{ title: string; slug: string }[]>([]);

  // Existing categories array
  const categories = [
    { id: 'english', name: 'English', icon: '📖', href: '/guides/us/english' },
    { id: 'math', name: 'Math', icon: '➗', href: '/guides/us/math' },
    { id: 'science', name: 'Science', icon: '🔬', href: '/guides/us/science' },
    { id: 'social-studies', name: 'Social Studies', icon: '🌍', href: '/guides/us/social-studies' }
  ];

  // Receive results from ProfileSelect after backend call
  function onPlan(cards: { title: string; slug?: string }[]) {
    setRecommendations(cards.map(c => ({ title: c.title, slug: c.slug || '#' })));
  }
  
  function onRequireLogin() {
    // Redirect to login page
    window.location.href = '/login';
  }

  function handlePlanSelect(plan: string) {
    if (plan === 'Free') {
      // Start with free account
      console.log('Starting with free account');
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

  function handleDiagnosticsComplete(result: any, context: any) {
    // Navigate to plan results page with diagnostic results
    navigate('/plan', { 
      state: { 
        result, 
        context 
      } 
    });
  }
  
  const [country, setCountry] = useState<'US' | 'CA'>('US');

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
      <Header />
      <TopMpcBanner />

      {/* Main */}
      <main className="flex-1 pt-20 pb-16 px-4 max-w-6xl mx-auto w-full">
        <div className="md:flex md:gap-6">
          <Sidebar />
          <div className="flex-1">
            {/* Under Construction Banner */}
            <section className="mb-8">
              <div className="bg-yellow-400 text-yellow-900 px-6 py-4 rounded-lg text-center shadow-lg">
                <h1 className="text-3xl md:text-4xl font-bold mb-2">
                  🚧 Under Construction 🚧
                </h1>
                <p className="text-lg font-semibold">
                  This site is currently under development
                </p>
              </div>
            </section>

            {/* Hero */}
            <section className="py-12" aria-labelledby="hero-heading">
              <div className="relative overflow-hidden rounded-2xl shadow-xl">
                <div className="absolute inset-0 bg-[radial-gradient(50%_50%_at_50%_0%,rgba(59,130,246,0.35),rgba(99,102,241,0.25)_40%,transparent_70%)]" />
                <div className="relative bg-slate-900/85 text-white px-6 py-12 text-center backdrop-blur">
                  <h2 id="hero-heading" className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">
                    {t.hero_title}
                  </h2>
                  <p className="text-slate-200/90 mb-8 max-w-2xl mx-auto">
                    {t.hero_subtitle}
                  </p>
                  <button 
                    onClick={() => navigate('/guides/us')}
                    className="inline-block bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-full transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-400"
                  >
                    {t.hero_cta}
                  </button>
                </div>
              </div>
            </section>

            {/* Quick Start */}
            <section className="mb-10">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {t.quick_start_title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {t.quick_start_subtitle}
                </p>
              </div>
              <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
                <Selector onDiagnosticsComplete={handleDiagnosticsComplete} />
              </div>
            </section>

            {/* Modules */}
            <section className="mb-10">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {t.modules_title}
                </h3>
              </div>
              <Modules />
            </section>

            {/* Plans */}
            <section className="mb-10">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {t.plans_title}
                </h3>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => navigate('/plans')}
                    className="text-sm text-blue-600 hover:text-blue-800 underline"
                  >
                    View Plan Comparison
                  </button>
                  <button
                    onClick={() => navigate('/saved')}
                    className="text-sm text-blue-600 hover:text-blue-800 underline"
                  >
                    Saved Plans
                  </button>
                  {BILLING_ENABLED && PAID_READY ? (
                    <Badge tone="success">{t.plans_note_enabled}</Badge>
                  ) : (
                    <Badge tone="warn">{t.plans_note_disabled}</Badge>
                  )}
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <PlanCard
                  title={t.free.name}
                  price={t.free.price}
                  blurb={t.free.blurb}
                  features={t.free.features}
                  cta={t.free.cta}
                  badge={<Badge>Start</Badge>}
                  onPlanSelect={handlePlanSelect}
                />

                <PlanCard
                  title={t.pro.name}
                  price={t.pro.price}
                  blurb={t.pro.blurb}
                  features={t.pro.features}
                  cta={t.pro.cta}
                  highlight
                  disabled={!BILLING_ENABLED || !PAID_READY}
                  badge={!PAID_READY ? <Badge tone="warn">Coming soon</Badge> : <Badge tone="info">Popular</Badge>}
                  onPlanSelect={handlePlanSelect}
                />

                <PlanCard
                  title={t.premium.name}
                  price={t.premium.price}
                  blurb={t.premium.blurb}
                  features={t.premium.features}
                  cta={t.premium.cta}
                  disabled={!BILLING_ENABLED || !PAID_READY}
                  badge={!PAID_READY ? <Badge tone="warn">Coming soon</Badge> : <Badge tone="success">Best value</Badge>}
                  onPlanSelect={handlePlanSelect}
                />
              </div>
            </section>

            {/* Profile Selection */}
            <div className="rounded-xl p-6 mb-12 shadow-lg bg-white/70 dark:bg-slate-800/60 backdrop-blur border border-slate-200/60 dark:border-white/10" id="profile">
              <h3 className="text-lg font-semibold mb-4">Your Profile</h3>
              <ProfileSelect onResult={onPlan} onRequireLogin={onRequireLogin} onCountryChange={setCountry} />
            </div>

            {/* Category Grid */}
            <CategoryGrid categories={categories} />

            {/* My Plan Panel */}
            <MyPlanPanel cards={recommendations} />

            {/* Subscribe CTA */}
            <section className="rounded-2xl p-8 text-center shadow-lg bg-gradient-to-br from-blue-600 to-indigo-600 text-white">
              <h3 className="text-xl font-semibold mb-2">Subscribe for Full Access</h3>
              <p className="text-white/90 mb-6">Unlock exclusive guides, personalised recommendations, and more.</p>
              <button 
                onClick={() => startCheckout()} 
                className="inline-block bg-white text-slate-900 px-6 py-3 rounded-full hover:bg-slate-100 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-white"
              >
                Subscribe Now
              </button>
            </section>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 dark:bg-gray-800 text-center py-4 text-sm text-gray-500 dark:text-gray-400">
        <div>© {new Date().getFullYear()} DreamSeedAI. All rights reserved.</div>
        <div className="space-x-3 mt-2">
          <a href="#" className="hover:underline">About Us</a>
          <a href="#" className="hover:underline">Terms of Service</a>
          <a href="#" className="hover:underline">Privacy Policy</a>
        </div>
      </footer>
    </div>
  );
}