import React from 'react';

type PlanCard = { title: string; slug?: string; summary?: string; icon?: string; targetCountry?: 'US'|'CA' };

export default function MyPlanPanel({ cards }: { cards: PlanCard[] }) {
  return (
    <section className="max-w-6xl mx-auto px-4">
      <h3 className="text-lg font-semibold mb-3">Your Recommended Plan</h3>
      {(!cards || cards.length === 0) ? (
        <div className="text-sm text-gray-600">
          Recommendations are being prepared.
          <button
            onClick={() => window.dispatchEvent(new Event('plan:retry'))}
            className="ml-2 inline-flex items-center px-3 py-1 rounded border border-gray-300 hover:bg-gray-50"
          >Retry</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {cards.slice(0, 5).map((c, i) => (
            <a key={`${c.slug}-${i}`} href={c.slug ? `/guides/us/${c.slug}` : '#'} className="bg-green-50 border border-green-200 rounded-lg p-4 hover:shadow-md transition">
              <div className="font-semibold mb-1">{c.icon ? `${c.icon} ` : ''}{c.title}</div>
              <div className="text-xs text-gray-500 mb-1">{c.targetCountry ? `Target: ${c.targetCountry}` : ''}</div>
              <div className="text-sm text-green-800">{c.summary ?? ''}</div>
            </a>
          ))}
        </div>
      )}
    </section>
  );
}
