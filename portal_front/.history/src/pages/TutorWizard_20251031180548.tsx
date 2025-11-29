import React, { useState } from 'react';
import { api } from '../lib/api';

interface QuickStartResponse {
  session_id: string;
  exam_id: string;
  pdf_url: string;
  dashboard_url: string;
  next_steps: string[];
  estimated_time_minutes: number;
}

export default function TutorWizard() {
  const [step, setStep] = useState<'welcome' | 'setup' | 'success'>('welcome');
  const [tutorName, setTutorName] = useState('');
  const [subject, setSubject] = useState('Math');
  const [gradeLevel, setGradeLevel] = useState('G10');
  const [numQuestions, setNumQuestions] = useState(10);
  const [difficulty, setDifficulty] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<QuickStartResponse | null>(null);

  const handleWelcomeNext = () => {
    if (!tutorName.trim()) {
      setError('Please enter your name');
      return;
    }
    setError('');
    setStep('setup');
  };

  const handleCreateExam = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api('/seedtest/wizard/quick-start', {
        method: 'POST',
        body: JSON.stringify({
          tutor_name: tutorName,
          subject,
          grade_level: gradeLevel,
          num_questions: numQuestions,
          difficulty,
        }),
      }) as QuickStartResponse;

      setResult(response);
      setStep('success');
    } catch (err: any) {
      setError(err.message || 'Failed to create exam');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = () => {
    if (result) {
      window.open(result.pdf_url, '_blank');
    }
  };

  // Step 1: Welcome
  if (step === 'welcome') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Welcome to DreamSeed! 👋
            </h1>
            <p className="text-gray-600">
              Let's create your first exam in under 60 seconds
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Name or School Name
              </label>
              <input
                type="text"
                value={tutorName}
                onChange={(e) => setTutorName(e.target.value)}
                placeholder="Ms. Kim / Seoul Academy"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                autoFocus
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              onClick={handleWelcomeNext}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition duration-200"
            >
              Get Started →
            </button>
          </div>

          <div className="mt-6 text-center text-sm text-gray-500">
            <p>⏱️ First PDF in ≤60 minutes</p>
          </div>
        </div>
      </div>
    );
  }

  // Step 2: Exam Setup
  if (step === 'setup') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-2xl w-full">
          <div className="mb-6">
            <button
              onClick={() => setStep('welcome')}
              className="text-blue-600 hover:text-blue-700 flex items-center text-sm mb-4"
            >
              ← Back
            </button>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Quick Exam Setup
            </h2>
            <p className="text-gray-600">
              Choose your preferences - we'll handle the rest!
            </p>
          </div>

          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject
                </label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Math">Math</option>
                  <option value="English">English</option>
                  <option value="Science">Science</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Grade Level
                </label>
                <select
                  value={gradeLevel}
                  onChange={(e) => setGradeLevel(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="G9">Grade 9</option>
                  <option value="G10">Grade 10</option>
                  <option value="G11">Grade 11</option>
                  <option value="G12">Grade 12</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Questions: {numQuestions}
              </label>
              <input
                type="range"
                min="5"
                max="25"
                value={numQuestions}
                onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>5 (Quick)</span>
                <span>25 (Comprehensive)</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Difficulty
              </label>
              <div className="grid grid-cols-3 gap-3">
                {['easy', 'medium', 'hard'].map((level) => (
                  <button
                    key={level}
                    onClick={() => setDifficulty(level)}
                    className={`py-3 rounded-lg font-medium transition ${
                      difficulty === level
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {level.charAt(0).toUpperCase() + level.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              onClick={handleCreateExam}
              disabled={loading}
              className={`w-full py-4 rounded-lg font-semibold transition ${
                loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {loading ? 'Creating Exam...' : '✨ Create My First Exam'}
            </button>
          </div>

          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-900">
              <strong>Estimated time:</strong> {numQuestions * 2 + 5} minutes
              (exam + review)
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Step 3: Success
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-2xl w-full">
        <div className="text-center mb-6">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Exam Created Successfully!
          </h2>
          <p className="text-gray-600">
            Session ID: <code className="bg-gray-100 px-2 py-1 rounded">{result?.session_id}</code>
          </p>
        </div>

        {result && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl p-6">
              <h3 className="text-xl font-semibold mb-4">Next Steps:</h3>
              <ol className="space-y-2">
                {result.next_steps.map((step, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="flex-shrink-0 w-6 h-6 bg-white text-blue-600 rounded-full flex items-center justify-center text-sm font-bold mr-3 mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={handleDownloadPDF}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition"
              >
                📄 Download PDF
              </button>
              <a
                href={result.dashboard_url}
                className="bg-gray-100 hover:bg-gray-200 text-gray-900 font-semibold py-3 rounded-lg transition text-center"
              >
                📊 Go to Dashboard
              </a>
            </div>

            <div className="text-center">
              <button
                onClick={() => {
                  setStep('welcome');
                  setTutorName('');
                  setResult(null);
                }}
                className="text-blue-600 hover:text-blue-700 text-sm"
              >
                Create Another Exam →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
