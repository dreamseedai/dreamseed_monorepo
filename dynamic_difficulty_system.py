#!/usr/bin/env python3
"""
Dynamic Difficulty Adjustment System
Adaptive difficulty system based on student performance and curriculum standards
"""

import json
import os
try:
    import numpy as np
except ImportError:
    # Fallback for systems without numpy
    class NumpyFallback:
        @staticmethod
        def var(data):
            if len(data) <= 1:
                return 0.0
            mean_val = sum(data) / len(data)
            return sum((x - mean_val) ** 2 for x in data) / (len(data) - 1)
    
    np = NumpyFallback()
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DifficultyLevel(Enum):
    """Difficulty level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class PerformanceLevel(Enum):
    """Student performance level enumeration"""
    STRUGGLING = "struggling"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class StudentPerformance:
    """Student performance data structure"""
    student_id: str
    subject: str
    grade: str
    topic: str
    questions_attempted: int
    questions_correct: int
    average_time_seconds: float
    recent_performance: List[bool]  # Last 10 attempts
    mastery_level: float
    last_updated: datetime

@dataclass
class QuestionDifficulty:
    """Question difficulty data structure"""
    question_id: str
    base_difficulty: DifficultyLevel
    adaptive_difficulty: float  # 0.0 to 1.0
    success_rate: float
    average_time_seconds: float
    prerequisite_skills: List[str]
    learning_objectives: List[str]

class DynamicDifficultySystem:
    """
    Dynamic difficulty adjustment system for adaptive learning
    """
    
    def __init__(self):
        self.difficulty_weights = {
            DifficultyLevel.BEGINNER: 0.2,
            DifficultyLevel.INTERMEDIATE: 0.4,
            DifficultyLevel.ADVANCED: 0.6,
            DifficultyLevel.EXPERT: 0.8
        }
        
        self.performance_thresholds = {
            PerformanceLevel.STRUGGLING: 0.3,
            PerformanceLevel.DEVELOPING: 0.5,
            PerformanceLevel.PROFICIENT: 0.7,
            PerformanceLevel.ADVANCED: 0.85,
            PerformanceLevel.EXPERT: 0.95
        }
        
        self.adaptation_factors = {
            'success_rate_weight': 0.4,
            'time_weight': 0.3,
            'recent_trend_weight': 0.2,
            'mastery_weight': 0.1
        }
    
    def calculate_student_performance_level(self, performance: StudentPerformance) -> PerformanceLevel:
        """
        Calculate student's performance level based on various metrics
        
        Args:
            performance: Student performance data
            
        Returns:
            Performance level
        """
        if performance.questions_attempted < 5:
            return PerformanceLevel.DEVELOPING  # Not enough data
        
        success_rate = performance.questions_correct / performance.questions_attempted
        
        # Consider recent performance trend
        if len(performance.recent_performance) >= 5:
            recent_success_rate = sum(performance.recent_performance) / len(performance.recent_performance)
            # Weight recent performance more heavily
            adjusted_success_rate = 0.7 * recent_success_rate + 0.3 * success_rate
        else:
            adjusted_success_rate = success_rate
        
        # Determine performance level
        if adjusted_success_rate >= self.performance_thresholds[PerformanceLevel.EXPERT]:
            return PerformanceLevel.EXPERT
        elif adjusted_success_rate >= self.performance_thresholds[PerformanceLevel.ADVANCED]:
            return PerformanceLevel.ADVANCED
        elif adjusted_success_rate >= self.performance_thresholds[PerformanceLevel.PROFICIENT]:
            return PerformanceLevel.PROFICIENT
        elif adjusted_success_rate >= self.performance_thresholds[PerformanceLevel.DEVELOPING]:
            return PerformanceLevel.DEVELOPING
        else:
            return PerformanceLevel.STRUGGLING
    
    def calculate_adaptive_difficulty(self, student_performance: StudentPerformance, 
                                    question_difficulty: QuestionDifficulty) -> float:
        """
        Calculate adaptive difficulty for a specific question for a student
        
        Args:
            student_performance: Student's performance data
            question_difficulty: Question's difficulty data
            
        Returns:
            Adaptive difficulty score (0.0 to 1.0)
        """
        # Base difficulty from question
        base_difficulty = self.difficulty_weights[question_difficulty.base_difficulty]
        
        # Student performance level
        performance_level = self.calculate_student_performance_level(student_performance)
        
        # Calculate adaptation factors
        success_rate_factor = self._calculate_success_rate_factor(student_performance)
        time_factor = self._calculate_time_factor(student_performance, question_difficulty)
        recent_trend_factor = self._calculate_recent_trend_factor(student_performance)
        mastery_factor = self._calculate_mastery_factor(student_performance)
        
        # Weighted combination of factors
        adaptation_score = (
            self.adaptation_factors['success_rate_weight'] * success_rate_factor +
            self.adaptation_factors['time_weight'] * time_factor +
            self.adaptation_factors['recent_trend_weight'] * recent_trend_factor +
            self.adaptation_factors['mastery_weight'] * mastery_factor
        )
        
        # Adjust base difficulty based on adaptation
        adaptive_difficulty = base_difficulty + (adaptation_score - 0.5) * 0.4
        
        # Ensure difficulty stays within bounds
        adaptive_difficulty = max(0.0, min(1.0, adaptive_difficulty))
        
        return adaptive_difficulty
    
    def _calculate_success_rate_factor(self, performance: StudentPerformance) -> float:
        """
        Calculate success rate factor for difficulty adjustment
        
        Args:
            performance: Student performance data
            
        Returns:
            Success rate factor (0.0 to 1.0)
        """
        if performance.questions_attempted == 0:
            return 0.5  # Neutral factor
        
        success_rate = performance.questions_correct / performance.questions_attempted
        
        # Map success rate to difficulty factor
        # High success rate -> increase difficulty
        # Low success rate -> decrease difficulty
        if success_rate >= 0.8:
            return 0.8  # High success, increase difficulty
        elif success_rate >= 0.6:
            return 0.6  # Good success, slight increase
        elif success_rate >= 0.4:
            return 0.5  # Moderate success, maintain difficulty
        elif success_rate >= 0.2:
            return 0.4  # Low success, decrease difficulty
        else:
            return 0.2  # Very low success, significantly decrease difficulty
    
    def _calculate_time_factor(self, performance: StudentPerformance, 
                             question_difficulty: QuestionDifficulty) -> float:
        """
        Calculate time-based factor for difficulty adjustment
        
        Args:
            performance: Student performance data
            question_difficulty: Question difficulty data
            
        Returns:
            Time factor (0.0 to 1.0)
        """
        if performance.average_time_seconds == 0 or question_difficulty.average_time_seconds == 0:
            return 0.5  # Neutral factor
        
        # Compare student's time to expected time
        time_ratio = performance.average_time_seconds / question_difficulty.average_time_seconds
        
        # Map time ratio to difficulty factor
        if time_ratio <= 0.5:
            return 0.8  # Very fast, increase difficulty
        elif time_ratio <= 0.8:
            return 0.6  # Fast, slight increase
        elif time_ratio <= 1.2:
            return 0.5  # Normal time, maintain difficulty
        elif time_ratio <= 1.5:
            return 0.4  # Slow, decrease difficulty
        else:
            return 0.2  # Very slow, significantly decrease difficulty
    
    def _calculate_recent_trend_factor(self, performance: StudentPerformance) -> float:
        """
        Calculate recent performance trend factor
        
        Args:
            performance: Student performance data
            
        Returns:
            Recent trend factor (0.0 to 1.0)
        """
        if len(performance.recent_performance) < 3:
            return 0.5  # Not enough recent data
        
        recent_success_rate = sum(performance.recent_performance) / len(performance.recent_performance)
        
        # Calculate trend (improving or declining)
        if len(performance.recent_performance) >= 5:
            first_half = performance.recent_performance[:len(performance.recent_performance)//2]
            second_half = performance.recent_performance[len(performance.recent_performance)//2:]
            
            first_half_rate = sum(first_half) / len(first_half)
            second_half_rate = sum(second_half) / len(second_half)
            
            trend = second_half_rate - first_half_rate
            
            # Adjust factor based on trend
            if trend > 0.2:
                return 0.7  # Improving trend, increase difficulty
            elif trend > 0.1:
                return 0.6  # Slight improvement, slight increase
            elif trend > -0.1:
                return 0.5  # Stable, maintain difficulty
            elif trend > -0.2:
                return 0.4  # Slight decline, decrease difficulty
            else:
                return 0.3  # Declining trend, decrease difficulty
        
        return 0.5  # Default neutral factor
    
    def _calculate_mastery_factor(self, performance: StudentPerformance) -> float:
        """
        Calculate mastery-based factor for difficulty adjustment
        
        Args:
            performance: Student performance data
            
        Returns:
            Mastery factor (0.0 to 1.0)
        """
        mastery_level = performance.mastery_level
        
        # Map mastery level to difficulty factor
        if mastery_level >= 0.9:
            return 0.8  # High mastery, increase difficulty
        elif mastery_level >= 0.7:
            return 0.6  # Good mastery, slight increase
        elif mastery_level >= 0.5:
            return 0.5  # Moderate mastery, maintain difficulty
        elif mastery_level >= 0.3:
            return 0.4  # Low mastery, decrease difficulty
        else:
            return 0.2  # Very low mastery, significantly decrease difficulty
    
    def recommend_question_difficulty(self, student_performance: StudentPerformance, 
                                    available_questions: List[QuestionDifficulty]) -> List[Tuple[str, float]]:
        """
        Recommend questions with appropriate difficulty for a student
        
        Args:
            student_performance: Student's performance data
            available_questions: List of available questions with difficulty data
            
        Returns:
            List of (question_id, adaptive_difficulty) tuples, sorted by appropriateness
        """
        recommendations = []
        
        for question in available_questions:
            adaptive_difficulty = self.calculate_adaptive_difficulty(student_performance, question)
            
            # Calculate appropriateness score
            appropriateness_score = self._calculate_appropriateness_score(
                student_performance, question, adaptive_difficulty
            )
            
            recommendations.append((question.question_id, adaptive_difficulty, appropriateness_score))
        
        # Sort by appropriateness score (higher is better)
        recommendations.sort(key=lambda x: x[2], reverse=True)
        
        return [(qid, diff) for qid, diff, _ in recommendations]
    
    def _calculate_appropriateness_score(self, student_performance: StudentPerformance, 
                                       question_difficulty: QuestionDifficulty, 
                                       adaptive_difficulty: float) -> float:
        """
        Calculate how appropriate a question is for a student
        
        Args:
            student_performance: Student's performance data
            question_difficulty: Question's difficulty data
            adaptive_difficulty: Calculated adaptive difficulty
            
        Returns:
            Appropriateness score (0.0 to 1.0)
        """
        # Base score from adaptive difficulty
        base_score = 1.0 - abs(adaptive_difficulty - 0.5) * 2  # Peak at 0.5 difficulty
        
        # Adjust based on student's current level
        performance_level = self.calculate_student_performance_level(student_performance)
        
        if performance_level == PerformanceLevel.STRUGGLING:
            # Prefer easier questions
            if adaptive_difficulty <= 0.3:
                base_score *= 1.2
            elif adaptive_difficulty >= 0.7:
                base_score *= 0.5
        elif performance_level == PerformanceLevel.DEVELOPING:
            # Prefer moderate difficulty
            if 0.3 <= adaptive_difficulty <= 0.6:
                base_score *= 1.1
        elif performance_level == PerformanceLevel.PROFICIENT:
            # Prefer moderate to advanced difficulty
            if 0.4 <= adaptive_difficulty <= 0.7:
                base_score *= 1.1
        elif performance_level == PerformanceLevel.ADVANCED:
            # Prefer advanced difficulty
            if 0.6 <= adaptive_difficulty <= 0.8:
                base_score *= 1.1
        elif performance_level == PerformanceLevel.EXPERT:
            # Prefer expert difficulty
            if adaptive_difficulty >= 0.7:
                base_score *= 1.2
            elif adaptive_difficulty <= 0.5:
                base_score *= 0.8
        
        # Adjust based on question success rate
        if question_difficulty.success_rate > 0:
            if 0.3 <= question_difficulty.success_rate <= 0.7:
                base_score *= 1.1  # Good success rate range
            elif question_difficulty.success_rate < 0.2 or question_difficulty.success_rate > 0.9:
                base_score *= 0.8  # Too easy or too hard
        
        return min(1.0, base_score)
    
    def update_student_performance(self, student_id: str, question_id: str, 
                                 is_correct: bool, time_spent_seconds: float,
                                 subject: str, grade: str, topic: str) -> StudentPerformance:
        """
        Update student performance data after attempting a question
        
        Args:
            student_id: Student ID
            question_id: Question ID
            is_correct: Whether the answer was correct
            time_spent_seconds: Time spent on the question
            subject: Subject of the question
            grade: Grade level
            topic: Topic of the question
            
        Returns:
            Updated student performance data
        """
        # This would typically load from database
        # For now, we'll create a mock update
        performance = StudentPerformance(
            student_id=student_id,
            subject=subject,
            grade=grade,
            topic=topic,
            questions_attempted=1,
            questions_correct=1 if is_correct else 0,
            average_time_seconds=time_spent_seconds,
            recent_performance=[is_correct],
            mastery_level=0.5,
            last_updated=datetime.now()
        )
        
        return performance
    
    def generate_difficulty_report(self, student_performance: StudentPerformance, 
                                 recent_questions: List[QuestionDifficulty]) -> Dict[str, Any]:
        """
        Generate a difficulty adjustment report for a student
        
        Args:
            student_performance: Student's performance data
            recent_questions: Recent questions attempted
            
        Returns:
            Difficulty adjustment report
        """
        performance_level = self.calculate_student_performance_level(student_performance)
        
        # Calculate adaptive difficulties for recent questions
        adaptive_difficulties = []
        for question in recent_questions:
            adaptive_diff = self.calculate_adaptive_difficulty(student_performance, question)
            adaptive_difficulties.append(adaptive_diff)
        
        # Analyze difficulty trends
        if len(adaptive_difficulties) > 0:
            avg_adaptive_difficulty = sum(adaptive_difficulties) / len(adaptive_difficulties)
            difficulty_variance = np.var(adaptive_difficulties) if len(adaptive_difficulties) > 1 else 0
        else:
            avg_adaptive_difficulty = 0.5
            difficulty_variance = 0
        
        # Generate recommendations
        recommendations = self._generate_difficulty_recommendations(
            student_performance, performance_level, avg_adaptive_difficulty
        )
        
        report = {
            "student_id": student_performance.student_id,
            "subject": student_performance.subject,
            "grade": student_performance.grade,
            "topic": student_performance.topic,
            "performance_level": performance_level.value,
            "current_mastery": student_performance.mastery_level,
            "success_rate": student_performance.questions_correct / max(1, student_performance.questions_attempted),
            "average_time": student_performance.average_time_seconds,
            "adaptive_difficulty_analysis": {
                "average_adaptive_difficulty": avg_adaptive_difficulty,
                "difficulty_variance": difficulty_variance,
                "difficulty_trend": "stable" if difficulty_variance < 0.1 else "variable"
            },
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def _generate_difficulty_recommendations(self, performance: StudentPerformance, 
                                           performance_level: PerformanceLevel, 
                                           avg_adaptive_difficulty: float) -> List[str]:
        """
        Generate difficulty adjustment recommendations
        
        Args:
            performance: Student performance data
            performance_level: Student's performance level
            avg_adaptive_difficulty: Average adaptive difficulty
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if performance_level == PerformanceLevel.STRUGGLING:
            recommendations.append("Consider focusing on foundational concepts and easier questions")
            recommendations.append("Provide additional support and hints")
            if avg_adaptive_difficulty > 0.4:
                recommendations.append("Reduce question difficulty to build confidence")
        
        elif performance_level == PerformanceLevel.DEVELOPING:
            recommendations.append("Gradually increase difficulty as mastery improves")
            recommendations.append("Focus on building proficiency in core concepts")
        
        elif performance_level == PerformanceLevel.PROFICIENT:
            recommendations.append("Introduce more challenging problems to promote growth")
            recommendations.append("Encourage exploration of advanced topics")
        
        elif performance_level == PerformanceLevel.ADVANCED:
            recommendations.append("Provide expert-level challenges")
            recommendations.append("Encourage independent problem-solving")
        
        elif performance_level == PerformanceLevel.EXPERT:
            recommendations.append("Offer research-level problems and projects")
            recommendations.append("Consider mentoring opportunities")
        
        # Time-based recommendations
        if performance.average_time_seconds > 300:  # More than 5 minutes
            recommendations.append("Consider breaking down complex problems into smaller steps")
        elif performance.average_time_seconds < 60:  # Less than 1 minute
            recommendations.append("Encourage deeper analysis and explanation of solutions")
        
        return recommendations

def main():
    """
    Demonstrate the dynamic difficulty system
    """
    system = DynamicDifficultySystem()
    
    # Create sample student performance
    student_performance = StudentPerformance(
        student_id="student_123",
        subject="Mathematics",
        grade="Grade_10",
        topic="Quadratic Functions",
        questions_attempted=20,
        questions_correct=14,
        average_time_seconds=120,
        recent_performance=[True, True, False, True, True, False, True, True, True, False],
        mastery_level=0.7,
        last_updated=datetime.now()
    )
    
    # Create sample questions
    questions = [
        QuestionDifficulty(
            question_id="q1",
            base_difficulty=DifficultyLevel.INTERMEDIATE,
            adaptive_difficulty=0.4,
            success_rate=0.6,
            average_time_seconds=90,
            prerequisite_skills=["linear functions", "graphing"],
            learning_objectives=["graph quadratic functions", "find vertex"]
        ),
        QuestionDifficulty(
            question_id="q2",
            base_difficulty=DifficultyLevel.ADVANCED,
            adaptive_difficulty=0.6,
            success_rate=0.4,
            average_time_seconds=180,
            prerequisite_skills=["quadratic functions", "factoring"],
            learning_objectives=["solve quadratic equations", "apply quadratic formula"]
        ),
        QuestionDifficulty(
            question_id="q3",
            base_difficulty=DifficultyLevel.EXPERT,
            adaptive_difficulty=0.8,
            success_rate=0.2,
            average_time_seconds=300,
            prerequisite_skills=["advanced algebra", "problem solving"],
            learning_objectives=["complex quadratic applications", "optimization"]
        )
    ]
    
    # Calculate performance level
    performance_level = system.calculate_student_performance_level(student_performance)
    print(f"Student Performance Level: {performance_level.value}")
    
    # Get question recommendations
    recommendations = system.recommend_question_difficulty(student_performance, questions)
    print(f"\nQuestion Recommendations:")
    for question_id, adaptive_difficulty in recommendations:
        print(f"  {question_id}: {adaptive_difficulty:.2f}")
    
    # Generate difficulty report
    report = system.generate_difficulty_report(student_performance, questions)
    print(f"\nDifficulty Report:")
    print(json.dumps(report, indent=2, default=str))

if __name__ == '__main__':
    main()
