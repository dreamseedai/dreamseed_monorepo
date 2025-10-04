import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';

export default function MathGradeSelection() {
  const navigate = useNavigate();
  const grades = [
    { id: 'G06', name: 'Grade 6' },
    { id: 'G07', name: 'Grade 7' },
    { id: 'G08', name: 'Grade 8' },
    { id: 'G09', name: 'Grade 9' },
    { id: 'G10', name: 'Grade 10' },
    { id: 'G11', name: 'Grade 11' },
    { id: 'G12', name: 'Grade 12' },
    { id: 'SAT', name: 'SAT' },
    { id: 'AP', name: 'AP' }
  ];

  const handleGradeClick = (gradeId: string) => {
    // 수학 문제 서버로 이동 (올바른 URL)
    const mathServerUrl = 'http://localhost:8001/';
    window.open(mathServerUrl, '_blank');
    
    // 향후 내부 라우팅으로 이동할 수 있도록 준비
    // navigate(`/math/categories/${gradeId}`);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
      <Header />
      
      <main className="flex-1 pt-20 pb-16 px-4 max-w-6xl mx-auto w-full">
        <div className="md:flex md:gap-6">
          <Sidebar />
          <div className="flex-1">
            {/* Hero Section */}
            <section className="py-12" aria-labelledby="math-hero-heading">
              <div className="relative overflow-hidden rounded-2xl shadow-xl">
                <div className="absolute inset-0 bg-[radial-gradient(50%_50%_at_50%_0%,rgba(59,130,246,0.35),rgba(99,102,241,0.25)_40%,transparent_70%)]" />
                <div className="relative bg-slate-900/85 text-white px-6 py-12 text-center backdrop-blur">
                  <h2 id="math-hero-heading" className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">
                    DreamSeedAI Mathematics
                  </h2>
                  <p className="text-slate-200/90 mb-8 max-w-2xl mx-auto">
                    Choose your grade to start solving math problems with curriculum-aligned content.
                  </p>
                  <div className="inline-flex items-center gap-2 rounded-full bg-green-100 text-green-900 border border-green-300 px-3 py-1 text-sm">
                    <span className="text-base">✅</span>
                    <span>No login required - Start learning now!</span>
                  </div>
                </div>
              </div>
            </section>

            {/* Grade Selection */}
            <section className="py-8">
              <h3 className="text-2xl font-bold text-center mb-8">Choose Your Grade</h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {grades.map(grade => (
                  <div
                    key={grade.id}
                    onClick={() => handleGradeClick(grade.id)}
                    className="bg-white/70 border border-gray-200/60 backdrop-blur rounded-xl shadow-sm p-6 hover:shadow-lg transition-all duration-300 cursor-pointer group hover:scale-105"
                  >
                    <div className="text-center">
                      <div className="text-4xl mb-3">➗</div>
                      <h4 className="text-lg font-semibold text-gray-800 group-hover:text-blue-600 transition-colors">
                        {grade.name}
                      </h4>
                      <p className="text-sm text-gray-600 mt-1">Mathematics</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Info Section */}
            <section className="py-8">
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                <h4 className="text-lg font-semibold text-blue-900 mb-2">About Our Math Problems</h4>
                <p className="text-blue-800">
                  Our math problems are aligned with US and Canadian curricula, providing 
                  grade-appropriate challenges that help you master mathematical concepts 
                  step by step. <strong>No login required!</strong>
                </p>
              </div>
            </section>

            {/* Quick Access Section */}
            <section className="py-8">
              <div className="bg-green-50 border border-green-200 rounded-xl p-6">
                <h4 className="text-lg font-semibold text-green-900 mb-2">Quick Access</h4>
                <p className="text-green-800 mb-4">
                  Click any grade above to open our math problem system in a new tab.
                </p>
                <div className="flex flex-wrap gap-2">
                  <button 
                    onClick={() => handleGradeClick('G09')}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
                  >
                    Grade 9 Math
                  </button>
                  <button 
                    onClick={() => handleGradeClick('G10')}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
                  >
                    Grade 10 Math
                  </button>
                  <button 
                    onClick={() => handleGradeClick('SAT')}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
                  >
                    SAT Math
                  </button>
                </div>
              </div>
            </section>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 text-center py-4 text-sm text-gray-500">
        <div>© {new Date().getFullYear()} DreamSeedAI. All rights reserved.</div>
        <div className="mt-2">
          <span className="text-green-600">✅ Math problems available without login</span>
        </div>
      </footer>
    </div>
  );
}