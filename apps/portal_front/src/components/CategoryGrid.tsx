import React from 'react';

type Category = { id: string; name: string; slug: string; desc?: string; icon?: string };
type Stage = { id: string; label: string };

const CATEGORIES: Category[] = [
  { id: 'eng', name: 'English', slug: 'english', icon: '📖' },
  { id: 'math', name: 'Math', slug: 'math', icon: '➗' },
  { id: 'sci', name: 'Science', slug: 'science', icon: '🔬' },
  { id: 'soc', name: 'Social Studies', slug: 'social-studies', icon: '🌍' },
  { id: 'lang', name: 'Languages', slug: 'languages', icon: '🈴' },
  { id: 'arts', name: 'Arts', slug: 'arts', icon: '🎨' },
  { id: 'exam', name: 'Exams & Admissions', slug: 'exams-admissions', icon: '🎯' },
  { id: 'xtra', name: 'Extracurricular & Leadership', slug: 'extracurricular', icon: '🏅' },
  { id: 'cs', name: 'CS & Engineering', slug: 'cs-engineering', icon: '💻' },
  { id: 'econ', name: 'Economics & Social Sciences', slug: 'economics-social', icon: '📊' },
  { id: 'well', name: 'Personal Skills & Well-being', slug: 'personal-skills', icon: '🧠' },
  { id: 'sch', name: 'Scholarship & Finances', slug: 'scholarship-finances', icon: '💰' },
];

const STAGES: Stage[] = [
  { id: 'G9', label: 'Grade 9' },
  { id: 'G10', label: 'Grade 10' },
  { id: 'G11', label: 'Grade 11' },
  { id: 'G12', label: 'Grade 12' },
];

export default function CategoryGrid({ country = 'us' }: { country?: 'us' | 'ca' }) {
  const base = country.toLowerCase() === 'ca' ? '/guides/ca' : '/guides/us';

  // Large screens: 2D matrix (stages x categories, first 4 columns visible for brevity)
  // Small screens: category cards list (1-2-3-4 responsive columns)
  return (
    <section className="max-w-6xl mx-auto px-4">
      <h3 className="text-lg font-semibold mb-4">Explore Guides</h3>

      {/* Mobile/Tablet: responsive category cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:hidden gap-4 mb-8">
        {CATEGORIES.map((c) => (
          <a
            key={c.id}
            href={`${base}/${c.slug}`}
            className="bg-white/70 border border-gray-200/60 backdrop-blur rounded-lg shadow-sm p-4 hover:shadow-md transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-600"
            aria-label={`Open ${c.name} guides`}
          >
            <div className="flex items-center gap-2 mb-1"><span className="text-xl">{c.icon}</span><h4 className="text-md font-semibold">{c.name}</h4></div>
            <div className="text-sm text-gray-600">Learn more</div>
          </a>
        ))}
      </div>

      {/* Desktop: 2D grid (stages x categories) */}
      <div className="hidden lg:block overflow-x-auto">
        <div className="min-w-[900px]">
          <div className="grid" style={{ gridTemplateColumns: `200px repeat(4, minmax(0,1fr))` }}>
            {/* Header */}
            <div></div>
            {CATEGORIES.slice(0, 4).map((c) => (
              <div key={`head-${c.id}`} className="px-3 py-2 text-sm font-semibold text-gray-700">{c.name}</div>
            ))}
            {/* Rows */}
            {STAGES.map((s) => (
              <React.Fragment key={s.id}>
                <div className="px-3 py-2 text-sm font-medium text-gray-800 bg-gray-50 sticky left-0">{s.label}</div>
                {CATEGORIES.slice(0, 4).map((c) => (
                  <a
                    key={`${s.id}-${c.id}`}
                    href={`${base}/${c.slug}`}
                    title={`${s.label} · ${c.name}`}
                    aria-label={`${s.label} · ${c.name}`}
                  className="m-2 block rounded-lg border border-gray-200/60 bg-white/70 backdrop-blur p-3 hover:shadow-md transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-blue-600"
                  >
                    <div className="flex items-center gap-2 mb-1"><span className="text-xl">{c.icon}</span><div className="font-semibold text-sm">{c.name}</div></div>
                    <div className="text-xs text-gray-500">Learn more</div>
                  </a>
                ))}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
