import React from 'react';
import Header from '../../components/Header';

export default function USGuideDetail() {
  const slug = typeof window !== 'undefined' ? window.location.pathname.split('/').pop() : '';
  return (
    <div>
      <Header />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-2">Guide: {slug}</h2>
        <div className="prose dark:prose-invert max-w-none">
          <p>This page will show detailed content for the selected guide, including steps, resources, and curated links.</p>
          <ul>
            <li>Overview and objectives</li>
            <li>Recommended timeline</li>
            <li>Resources and practice</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
