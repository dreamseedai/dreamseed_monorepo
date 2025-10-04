import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';

export default function MathSelectGrade() {
  const navigate = useNavigate();
  
  const grades = [
    { id: 'G06', name: 'Grade 6', description: 'Basic Mathematics' },
    { id: 'G07', name: 'Grade 7', description: 'Pre-Algebra' },
    { id: 'G08', name: 'Grade 8', description: 'Algebra I' },
    { id: 'G09', name: 'Grade 9', description: 'Algebra II' },
    { id: 'G10', name: 'Grade 10', description: 'Geometry' },
    { id: 'G11', name: 'Grade 11', description: 'Pre-Calculus' },
    { id: 'G12', name: 'Grade 12', description: 'Calculus' },
    { id: 'SAT', name: 'SAT', description: 'SAT Math Preparation' },
    { id: 'AP', name: 'AP', description: 'Advanced Placement' }
  ];

  const handleGradeClick = (gradeId: string) => {
    // 수학 문제 서버로 이동
    window.open('http://localhost:8005/', '_blank');
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
      <Header />
      
      <main className="flex-1 pt-20 pb-16 px-4 max-w-6xl mx-auto w-full">
        <div className="md:flex md:gap-6">
          <Sidebar />
          <div className="flex-1">
            {/* Breadcrumb */}
            <nav className="mb-6">
              <ol className="flex items-center space-x-2 text-sm text-gray-500">
                <li>
                  <button 
                    onClick={() => navigate('/')}
                    className="hover:text-blue-600 transition-colors"
                  >
                    Home
                  </button>
                </li>
                <li>/</li>
                <li className="text-gray-800 font-medium">Math</li>
              </ol>
            </nav>

            {/* Hero Section */}
            <section className="py-8" aria-labelledby="math-hero-heading">
              <div className="relative overflow-hidden rounded-2xl shadow-xl">
                <div className="absolute inset-0 bg-[radial-gradient(50%_50%_at_50%_0%,rgba(59,130,246,0.35),rgba(99,102,241,0.25)_40%,transparent_70%)]" />
                <div className="relative bg-blue-600 text-white px-6 py-12 text-center backdrop-blur">
                  <h2 id="math-hero-heading" className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">
                    Mathematics
                  </h2>
                  <p className="text-blue-100 mb-8 max-w-2xl mx-auto">
                    Choose your grade to start solving math problems with curriculum-aligned content.
                  </p>
                  <div className="inline-flex items-center gap-2 rounded-full bg-green-100 text-green-900 border border-green-300 px-3 py-1 text-sm">
                    <span className="text-base">✅</span>
                    <span>Real problems from mpcstudy.com database</span>
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
                    className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 hover:shadow-lg transition-all duration-300 cursor-pointer group hover:scale-105"
                  >
                    <div className="text-center">
                      <div className="text-4xl mb-3">➗</div>
                      <h4 className="text-lg font-semibold text-gray-800 group-hover:text-blue-600 transition-colors">
                        {grade.name}
                      </h4>
                      <p className="text-sm text-gray-600 mt-1">{grade.description}</p>
                      <div className="mt-3 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                        Available
                      </div>
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
                  Our math problems are converted from the original mpcstudy.com database and aligned with 
                  US and Canadian curricula, providing grade-appropriate challenges that help you master 
                  mathematical concepts step by step.
                </p>
              </div>
            </section>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 text-center py-4 text-sm text-gray-500">
        <div>© {new Date().getFullYear()} DreamSeedAI. All rights reserved.</div>
      </footer>
    </div>
  );
}
