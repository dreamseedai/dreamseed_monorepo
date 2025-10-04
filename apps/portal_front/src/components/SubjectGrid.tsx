import React from 'react';
import { useNavigate } from 'react-router-dom';

// 기존 과목 목록으로 복구
const AVAILABLE_SUBJECTS = [
  { 
    id: 'english', 
    name: 'English', 
    icon: '📖', 
    description: 'English Language Arts',
    color: 'bg-blue-500',
    hoverColor: 'hover:bg-blue-600',
    isAvailable: true
  },
  { 
    id: 'math', 
    name: 'Math', 
    icon: '➗', 
    description: 'Mathematics',
    color: 'bg-green-500',
    hoverColor: 'hover:bg-green-600',
    isAvailable: true
  },
  { 
    id: 'science', 
    name: 'Science', 
    icon: '🔬', 
    description: 'Science',
    color: 'bg-purple-500',
    hoverColor: 'hover:bg-purple-600',
    isAvailable: true
  },
  { 
    id: 'social-studies', 
    name: 'Social Studies', 
    icon: '🌍', 
    description: 'History & Geography',
    color: 'bg-orange-500',
    hoverColor: 'hover:bg-orange-600',
    isAvailable: true
  }
];

export default function SubjectGrid() {
  const navigate = useNavigate();

  const handleSubjectClick = (subject: typeof AVAILABLE_SUBJECTS[0]) => {
    if (subject.isAvailable) {
      // 기존 가이드 페이지로 이동
      navigate(`/guides/us/${subject.id}`);
    } else {
      alert(`${subject.name} 과목은 준비 중입니다.`);
    }
  };

  return (
    <section className="max-w-6xl mx-auto px-4">
      <div className="mb-6">
        <h3 className="text-2xl font-bold text-gray-800 mb-2">Available Subjects</h3>
        <p className="text-gray-600">Choose a subject to start learning</p>
      </div>

      {/* 기존 과목들 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {AVAILABLE_SUBJECTS.map((subject) => (
          <div
            key={subject.id}
            onClick={() => handleSubjectClick(subject)}
            className={`
              ${subject.color} ${subject.hoverColor}
              text-white rounded-xl p-6 cursor-pointer 
              transform transition-all duration-300 
              hover:scale-105 hover:shadow-lg
              flex flex-col items-center text-center
              min-h-[160px] justify-center
            `}
          >
            <div className="text-4xl mb-3">{subject.icon}</div>
            <h4 className="text-xl font-bold mb-2">{subject.name}</h4>
            <p className="text-sm opacity-90">{subject.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
