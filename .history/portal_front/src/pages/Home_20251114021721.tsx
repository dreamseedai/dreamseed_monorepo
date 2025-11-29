import React, { useRef, useState } from 'react';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import TopMpcBanner from '../components/TopMpcBanner';
import ProfileSelect from '../components/ProfileSelect';
import CategoryGrid from '../components/CategoryGrid';
import MyPlanPanel from '../components/MyPlanPanel';
import { startCheckout } from '../lib/pay';
import CopyAllButton from '../components/CopyAllButton';
import { FEATURES } from '../lib/FEATURES';

export default function HomePage() {
  const [recommendations, setRecommendations] = useState<{ title:string; slug:string }[]>([]);
  const ctaRef = useRef<HTMLDivElement | null>(null);

  const categories = [
    { title: 'English', slug: 'english' },
    { title: 'Math', slug: 'math' },
    { title: 'Science', slug: 'science' },
    { title: 'Social Studies', slug: 'social-studies' },
    { title: 'Languages', slug: 'languages' },
    { title: 'Arts', slug: 'arts' },
    { title: 'Exams & Admissions', slug: 'exams-admissions', subtopics: ['SAT','AP','ACT','OUAC'] as any },
    { title: 'Extracurricular & Leadership', slug: 'extracurricular' },
    { title: 'CS & Engineering', slug: 'cs-engineering' },
    { title: 'Economics & Social Sciences', slug: 'economics-social' },
    { title: 'Personal Skills & Well‑being', slug: 'personal-skills' },
    { title: 'Scholarship & Finances', slug: 'scholarship-finances' },
  ];

  // ProfileSelect에서 백엔드 호출 후 결과를 전달받습니다
  function onPlan(cards: { title: string; slug?: string }[]) {
    setRecommendations(cards.map(c => ({ title: c.title, slug: c.slug || '#' })));
  }
  function onRequireLogin() {
    try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch {}
  }
  const [country, setCountry] = useState<'US'|'CA'>('US');

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
      <Header />
      <TopMpcBanner />

      {/* Main */}
      <main className="flex-1 pt-20 pb-16 px-4 max-w-6xl mx-auto w-full">
        <div className="md:flex md:gap-6">
          <Sidebar />
          <div className="flex-1">
        {/* Hero */}
        <section className="py-12" aria-labelledby="hero-heading">
          <div className="relative overflow-hidden rounded-2xl shadow-xl">
            <div className="absolute inset-0 bg-[radial-gradient(50%_50%_at_50%_0%,rgba(59,130,246,0.35),rgba(99,102,241,0.25)_40%,transparent_70%)]" />
            <div className="relative bg-slate-900/85 text-white px-6 py-12 text-center backdrop-blur">
              <h2 id="hero-heading" className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">Plan your path with DreamSeedAI</h2>
              <p className="text-slate-200/90 mb-8 max-w-2xl mx-auto">Personalised guides, study plans, and expert recommendations for US/CA students.</p>
              <div className="flex items-center justify-center gap-3 flex-wrap">
                <a href="/guides/us" className="inline-block bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-full transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-400">Explore US Guides</a>
                <a href="/student/questions" className="inline-block bg-green-600 hover:bg-green-500 text-white px-6 py-3 rounded-full transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-green-400">문제 풀이 (Phase 1 MVP)</a>
                {FEATURES.TUTOR_WIZARD && (
                  <a href="/wizard" className="inline-block bg-white/10 hover:bg-white/20 text-white px-6 py-3 rounded-full transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-white">
                    Create Your First Exam
                  </a>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Profile Selection */}
        <div className="rounded-xl p-6 mb-12 shadow-lg bg-white/70 dark:bg-slate-800/60 backdrop-blur border border-slate-200/60 dark:border-white/10" id="profile">
          <h3 className="text-lg font-semibold mb-4">Your Profile</h3>
          <ProfileSelect onResult={onPlan} onRequireLogin={onRequireLogin} onCountryChange={setCountry} />
        </div>

        {/* Exams notice badge (sticky for mobile) */}
        <div className="mb-6 sticky top-0 z-10">
          <div className="inline-flex items-center gap-2 rounded-full bg-yellow-100 text-yellow-900 border border-yellow-300 px-3 py-1 text-sm">
            <span className="text-base">🎯</span>
            <span>
              시험 대비는{' '}
              <a href="/guides/us/exams-admissions" className="underline font-medium">
                Exams & Admissions
              </a>
              에서 확인하세요
            </span>
          </div>
        </div>

        {/* Category Grid (2D + responsive) */}
        <CategoryGrid country={country.toLowerCase() as any} />

        {/* My Plan Panel */}
        <MyPlanPanel cards={recommendations} />

        {/* Subscribe CTA (big blue box) */}
        <section className="rounded-2xl p-8 text-center shadow-lg bg-gradient-to-br from-blue-600 to-indigo-600 text-white relative">
          <div ref={ctaRef} id="ds-subscribe-cta" className="space-y-2">
            <h3 className="text-xl font-semibold">Subscribe for Full Access</h3>
            <p className="text-white/90">Unlock exclusive guides, personalised recommendations, and more.</p>
            <button onClick={() => startCheckout()} className="inline-block bg-white text-slate-900 px-6 py-3 rounded-full hover:bg-slate-100 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-white">Subscribe Now</button>
          </div>
          {/* Copy-all button at the bottom-right of the blue box */}
          <div className="absolute right-3 bottom-3">
            <CopyAllButton targetRef={ctaRef as any} label="복사" />
          </div>
        </section>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 text-center py-4 text-sm text-gray-500">
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


