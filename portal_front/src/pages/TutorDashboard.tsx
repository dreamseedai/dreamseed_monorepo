import React from 'react';

export default function TutorDashboard() {
  const params = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '');
  const sessionId = params.get('session');

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <a href="/" className="font-bold text-slate-900">DreamSeedAI</a>
          <nav className="text-sm">
            <a href="/wizard" className="text-blue-600">Wizard</a>
          </nav>
        </div>
      </header>

      <main className="max-w-3xl mx-auto p-4">
        <h1 className="text-2xl font-bold mb-2">Tutor Dashboard</h1>
        <p className="text-slate-600 mb-6">Minimal placeholder for V1. More analytics and assignments coming in Phase 2.</p>

        <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6">
          <h2 className="text-lg font-semibold mb-2">Current Session</h2>
          {sessionId ? (
            <div className="space-y-2">
              <p>
                Session ID: <code className="bg-slate-100 px-2 py-1 rounded">{sessionId}</code>
              </p>
              <div className="flex gap-3 flex-wrap">
                <a
                  className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                  href={`/api/seedtest/exams/${sessionId}/result/pdf?brand=Tutor`}
                  target="_blank"
                  rel="noreferrer"
                >
                  📄 Download PDF
                </a>
                <a
                  className="inline-flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-900 px-4 py-2 rounded-lg"
                  href={`/apps/exam?session=${encodeURIComponent(sessionId)}`}
                >
                  🧪 Open Exam Player
                </a>
              </div>
            </div>
          ) : (
            <p>No session selected. Use the <a href="/wizard" className="underline">Wizard</a> to create your first exam.</p>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <h3 className="font-semibold mb-1">Next Steps</h3>
            <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">
              <li>Invite a student and have them complete the exam</li>
              <li>Download the results PDF for review with parents</li>
              <li>Assign the next practice set (coming soon)</li>
            </ul>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <h3 className="font-semibold mb-1">Coming Soon</h3>
            <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">
              <li>Student invitations and roster</li>
              <li>Assignment tracking and progress</li>
              <li>Payment and subscription management</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
