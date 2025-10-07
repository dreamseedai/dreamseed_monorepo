import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import TopMpcBanner from '../components/TopMpcBanner';
import ProfileSelect from '../components/ProfileSelect';
import CategoryGrid from '../components/CategoryGrid';
import MyPlanPanel from '../components/MyPlanPanel';
import { postDiagnosticsRun } from '../api/client';
import type { DiagnosticRequest } from '../api/types/profile';
import { useLanguage } from '../contexts/LanguageContext';


// This will be replaced with useLanguage hook



// Selector component (Country/Grade/Goal selection)
const Selector: React.FC<{ onDiagnosticsComplete?: (result: any, context: any) => void }> = ({ onDiagnosticsComplete }) => {
  const { t } = useLanguage();
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
      alert(t('home.quick_start.error'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {t('home.quick_start.country')}
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
            {t('home.quick_start.grade')}
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
            {t('home.quick_start.goal')}
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
          {isLoading ? t('home.quick_start.loading') : t('home.quick_start.cta')}
        </button>
      </div>
    </>
  );
};

// Modules component
const Modules: React.FC = () => {
  const { t } = useLanguage();
  const modules = [
    { name: t('modules.english'), icon: '📖', description: t('modules.english_desc') },
    { name: t('modules.math'), icon: '➗', description: t('modules.math_desc') },
    { name: t('modules.science'), icon: '🔬', description: t('modules.science_desc') },
    { name: t('modules.history'), icon: '🌍', description: t('modules.history_desc') },
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
  const { t } = useLanguage();
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
                    {t('home.hero.title')}
                  </h2>
                  <p className="text-slate-200/90 mb-8 max-w-2xl mx-auto">
                    {t('home.hero.subtitle')}
                  </p>
                  <button
                    onClick={() => navigate('/guides/us')}
                    className="inline-block bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-full transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-400"
                  >
                    {t('home.hero.cta')}
                  </button>
                </div>
              </div>
            </section>

            {/* Quick Start */}
            <section className="mb-10">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {t('home.quick_start.title')}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {t('home.quick_start.subtitle')}
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
                  {t('modules.title')}
                </h3>
              </div>
              <Modules />
            </section>


            {/* Profile Selection */}
            <div className="rounded-xl p-6 mb-12 shadow-lg bg-white/70 dark:bg-slate-800/60 backdrop-blur border border-slate-200/60 dark:border-white/10" id="profile">
              <h3 className="text-lg font-semibold mb-4">Your Profile</h3>
              <ProfileSelect onResult={onPlan} onRequireLogin={onRequireLogin} onCountryChange={setCountry} />
            </div>

            {/* Category Grid */}
            <CategoryGrid />

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
