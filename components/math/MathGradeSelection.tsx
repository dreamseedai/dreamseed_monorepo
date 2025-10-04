import React from 'react';
import { useNavigate } from 'react-router-dom';
import './MathGradeSelection.css';

export const MathGradeSelection = () => {
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
    navigate(`/math/categories/${gradeId}`);
  };

  return (
    <div className="math-grade-selection">
      <div className="container">
        <h1 className="page-title">DreamSeedAI Mathematics</h1>
        <p className="page-subtitle">Choose your grade to start solving math problems</p>
        
        <div className="grade-grid">
          {grades.map(grade => (
            <div 
              key={grade.id} 
              className="grade-card"
              onClick={() => handleGradeClick(grade.id)}
            >
              <h3>{grade.name}</h3>
              <p>Mathematics</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
