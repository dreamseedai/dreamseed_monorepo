import React, { useEffect, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import type { DiagnosticResponse } from "../api/types/profile";
import { postShare } from "../api/client";

export default function PlanResult() {
  const navigate = useNavigate();
  const loc = useLocation() as any;
  const [searchParams] = useSearchParams();
  const [result, setResult] = useState<DiagnosticResponse | undefined>(loc?.state?.result);
  const [context, setContext] = useState(loc?.state?.context);
  const [brandMode, setBrandMode] = useState(false);

  // Decode data from URL parameters
  useEffect(() => {
    const dataParam = searchParams.get('data');
    if (dataParam && !result) {
      try {
        const decoded = JSON.parse(atob(dataParam));
        setResult(decoded.result);
        setContext(decoded.context);
      } catch (error) {
        console.error('Failed to decode plan data:', error);
      }
    }
  }, [searchParams, result]);

  // Local save
  const handleSaveLocal = () => {
    if (result && context) {
      const savedPlans = JSON.parse(localStorage.getItem('dreamseed.savedPlans') || '[]');
      const newItem = {
        id: Date.now().toString(),
        result,
        context,
        savedAt: new Date().toISOString()
      };
      savedPlans.push(newItem);
      localStorage.setItem('dreamseed.savedPlans', JSON.stringify(savedPlans));
      alert('Plan saved locally!');
    }
  };

  // Copy link
  const handleCopyLink = async () => {
    if (!result || !context) return;
    
    const payload = { result, context };
    try {
      // Try to create short link via API
      const out = await postShare(payload);
      const absolute = `${window.location.origin}${out.url}`;
      await navigator.clipboard.writeText(absolute);
      alert('Short share link copied to clipboard!');
    } catch {
      // Fallback to Base64 link if API fails
      const b64 = btoa(unescape(encodeURIComponent(JSON.stringify(payload))))
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=+$/, "");
      const url = `${window.location.origin}/plan?data=${b64}`;
      await navigator.clipboard.writeText(url);
      alert('Share link copied to clipboard!');
    }
  };

  // PDF export
  const handleExportPdf = () => {
    setBrandMode(false);
    window.print();
  };

  // Branded PDF export
  const handleExportBrandedPdf = () => {
    setBrandMode(true);
    setTimeout(() => {
      window.print();
      setTimeout(() => setBrandMode(false), 300);
    }, 100);
  };

  // Calendar download (.ics)
  const handleDownloadIcs = () => {
    if (!result?.nextWeekPlan) return;

    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay() + 1); // Set to Monday

    const dayMap: { [key: string]: number } = {
      'Monday': 0, 'Mon': 0,
      'Tuesday': 1, 'Tue': 1,
      'Wednesday': 2, 'Wed': 2,
      'Thursday': 3, 'Thu': 3,
      'Friday': 4, 'Fri': 4,
      'Saturday': 5, 'Sat': 5,
      'Sunday': 6, 'Sun': 6
    };

    const lines = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//DreamSeedAI//Study Plan//EN',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH'
    ];

    result.nextWeekPlan.forEach((dayPlan, index) => {
      const dayOffset = dayMap[dayPlan.day] || index;
      const eventDate = new Date(startOfWeek);
      eventDate.setDate(startOfWeek.getDate() + dayOffset);
      
      const startTime = new Date(eventDate);
      startTime.setHours(18, 0, 0, 0); // Start at 18:00
      
      const endTime = new Date(startTime);
      endTime.setHours(19, 0, 0, 0); // 1 hour

      const formatDate = (date: Date) => {
        return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
      };

      lines.push('BEGIN:VEVENT');
      lines.push(`UID:dreamseed-${Date.now()}-${index}@dreamseedai.com`);
      lines.push(`DTSTART:${formatDate(startTime)}`);
      lines.push(`DTEND:${formatDate(endTime)}`);
      lines.push(`SUMMARY:${dayPlan.tasks.join(' | ')}`);
      lines.push(`DESCRIPTION:${dayPlan.tasks.join('\\n')}`);
      lines.push('STATUS:CONFIRMED');
      lines.push('END:VEVENT');
    });

    lines.push('END:VCALENDAR');
    
    const blob = new Blob([lines.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'DreamSeedAI_next_week_plan.ics';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  // Generate Google Calendar URL for individual events
  const generateGoogleCalendarUrl = (dayPlan: any, index: number) => {
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay() + 1); // Set to Monday

    const dayMap: { [key: string]: number } = {
      'Monday': 0, 'Mon': 0,
      'Tuesday': 1, 'Tue': 1,
      'Wednesday': 2, 'Wed': 2,
      'Thursday': 3, 'Thu': 3,
      'Friday': 4, 'Fri': 4,
      'Saturday': 5, 'Sat': 5,
      'Sunday': 6, 'Sun': 6
    };

    const dayOffset = dayMap[dayPlan.day] || index;
    const eventDate = new Date(startOfWeek);
    eventDate.setDate(startOfWeek.getDate() + dayOffset);
    
    const startTime = new Date(eventDate);
    startTime.setHours(18, 0, 0, 0); // Start at 18:00
    
    const endTime = new Date(startTime);
    endTime.setHours(19, 0, 0, 0); // 1 hour

    const formatDate = (date: Date) => {
      return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    };

    const title = encodeURIComponent(dayPlan.tasks.join(' | '));
    const details = encodeURIComponent(dayPlan.tasks.join('\n'));
    const start = formatDate(startTime);
    const end = formatDate(endTime);

    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${start}/${end}&details=${details}`;
  };

  if (!result) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10">
        <h1 className="text-2xl font-bold">Plan Results</h1>
        <p className="mt-2 text-gray-600">You accessed this page directly. Please run diagnostics first by clicking "View My Strategy" on the home page.</p>
        <button 
          className="mt-4 rounded-2xl px-4 py-2 text-sm font-semibold bg-gray-900 text-white" 
          onClick={() => navigate("/")}
        >
          Go Home
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 print:px-0">
      {/* Print styles */}
      <style>{`
        @media print {
          .print-hide { display: none !important; }
          .print-container { padding: 24px; }
          .page-break { page-break-before: always; }
          .border { border: 1px solid #e5e7eb !important; }
          body { font-size: 12px; }
          h1 { font-size: 18px; }
          h2 { font-size: 14px; }
        }
      `}</style>

      {/* Action buttons */}
      <div className="print-hide flex flex-wrap gap-3 justify-end mb-6">
        <button 
          className="rounded-2xl px-4 py-2 text-sm font-semibold bg-white ring-1 ring-gray-300 hover:bg-gray-50" 
          onClick={handleSaveLocal}
        >
          Save Locally
        </button>
        <button 
          className="rounded-2xl px-4 py-2 text-sm font-semibold bg-white ring-1 ring-gray-300 hover:bg-gray-50" 
          onClick={handleCopyLink}
        >
          Copy Link
        </button>
        <button 
          className="rounded-2xl px-4 py-2 text-sm font-semibold bg-white ring-1 ring-gray-300 hover:bg-gray-50" 
          onClick={handleDownloadIcs}
        >
          Calendar(.ics)
        </button>
        <button 
          className="rounded-2xl px-4 py-2 text-sm font-semibold bg-white ring-1 ring-gray-300 hover:bg-gray-50" 
          onClick={handleExportPdf}
        >
          PDF (Simple)
        </button>
        <button 
          className="rounded-2xl px-4 py-2 text-sm font-semibold bg-gray-900 text-white" 
          onClick={handleExportBrandedPdf}
        >
          PDF (Brand Cover)
        </button>
      </div>

      {/* Brand Cover (shown only in brandMode) */}
      {brandMode && (
        <section className="print-container border rounded-2xl p-10 mb-8">
          {/* Simple Logo (SVG) */}
          <div className="mb-8">
            <svg width="120" height="28" viewBox="0 0 120 28" aria-hidden="true">
              <rect x="0" y="10" width="28" height="8" rx="4" fill="#1f2937"></rect>
              <text x="40" y="18" fontSize="16" fontWeight="700" fill="#1f2937">DreamSeedAI</text>
            </svg>
          </div>
          <h1 className="text-3xl font-extrabold">Personalized Strategy</h1>
          {context && (
            <p className="mt-2 text-sm text-gray-600">
              {context.country} / {context.grade} / {context.goal}
            </p>
          )}
          <p className="mt-6 text-gray-700">
            This report summarizes your recommended focus areas and weekly plan generated by DreamSeedAI.
          </p>
          <p className="mt-2 text-xs text-gray-500">
            Generated: {new Date().toLocaleString()}
          </p>
        </section>
      )}

      {/* Page break before content */}
      {brandMode && <div className="page-break" />}

      {/* Content */}
      <div className="print-container">
        <h1 className="text-2xl font-bold">Custom Strategy Summary</h1>
        {context && (
          <p className="mt-1 text-sm text-gray-600">
            Context: {context.country} / {context.grade} / {context.goal}
          </p>
        )}

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border p-4">
            <h2 className="font-semibold">Summary</h2>
            <p className="mt-1 text-sm text-gray-700">{result.summary}</p>
          </div>
          <div className="rounded-2xl border p-4">
            <h2 className="font-semibold">Weaknesses</h2>
            <ul className="mt-1 list-disc list-inside text-sm text-gray-700">
              {result.weaknesses.map(w => <li key={w}>{w}</li>)}
            </ul>
          </div>
        </div>

        <div className="mt-4 rounded-2xl border p-4">
          <h2 className="font-semibold">Recommended Modules</h2>
          <div className="mt-2 flex flex-wrap gap-2">
            {result.recommendedModules.map(m => (
              <span key={m} className="rounded-full bg-gray-900 text-white text-xs px-2.5 py-0.5">
                {m}
              </span>
            ))}
          </div>
        </div>

        <div className="mt-4 rounded-2xl border p-4">
          <h2 className="font-semibold">Recommended Problems</h2>
          <ul className="mt-1 list-disc list-inside text-sm text-gray-700">
            {result.recommendedProblems.map(p => <li key={p.id}>{p.title}</li>)}
          </ul>
        </div>

        <div className="mt-4 rounded-2xl border p-4">
          <h2 className="font-semibold">Next Week Plan</h2>
          <ul className="mt-1 text-sm text-gray-700">
            {result.nextWeekPlan.map((d, i) => (
              <li key={i} className="mb-1 flex items-center justify-between">
                <div>
                  <span className="font-medium mr-2">{d.day}</span>
                  {d.tasks.join(" · ")}
                </div>
                <a
                  href={generateGoogleCalendarUrl(d, i)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  Add to Google Calendar
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Navigation buttons */}
      <div className="mt-6 flex gap-3 print-hide">
        <button 
          className="rounded-2xl px-4 py-2 text-sm font-semibold bg-white ring-1 ring-gray-300 hover:bg-gray-50" 
          onClick={() => navigate("/")}
        >
          Reset
        </button>
        <button 
          className="rounded-2xl px-4 py-2 text-sm font-semibold bg-gray-900 text-white" 
          onClick={() => navigate("/checkout?plan=pro")}
        >
          Start with Pro
        </button>
      </div>
    </div>
  );
}