import React from 'react';
import Header from '../../components/Header';

export default function USExamsAdmissions() {
  return (
    <div>
      <Header />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-4">Exams & Admissions</h2>
        <p className="text-gray-600 mb-6">Check out resources and guides for SAT/AP/ACT preparation and admissions procedures (OUAC, etc.).</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a href="/guides/us/exams/sat" className="border rounded-xl p-4 hover:shadow-md transition">
            <h3 className="font-semibold mb-1">SAT Preparation</h3>
            <div className="text-sm text-gray-600">Score-based strategies, recommended learning paths</div>
          </a>
          <a href="/guides/us/exams/ap" className="border rounded-xl p-4 hover:shadow-md transition">
            <h3 className="font-semibold mb-1">AP Preparation</h3>
            <div className="text-sm text-gray-600">Subject selection, difficulty levels, learning roadmap</div>
          </a>
          <a href="/guides/us/exams/act" className="border rounded-xl p-4 hover:shadow-md transition">
            <h3 className="font-semibold mb-1">ACT Preparation</h3>
            <div className="text-sm text-gray-600">Section-specific strategies and time management</div>
          </a>
          <a href="/guides/us/exams/ouac" className="border rounded-xl p-4 hover:shadow-md transition">
            <h3 className="font-semibold mb-1">OUAC Guide</h3>
            <div className="text-sm text-gray-600">Overview of Ontario, Canada application procedures</div>
          </a>
        </div>
      </div>
    </div>
  );
}
