#!/usr/bin/env python3
"""
Curriculum Classification System Demo
실제 실행 가능한 데모 스크립트
"""

import json
import os
import asyncio
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_questions():
    """
    Create sample questions for demonstration
    """
    return [
        {
            "id": 1,
            "title": "Linear Equations - Basic",
            "content": {
                "question": {"en": "Solve for x: 2x + 5 = 13"},
                "answer": {"en": "x = 4"},
                "solution": {"en": "Subtract 5 from both sides: 2x = 8, then divide by 2: x = 4"},
                "hints": [{"en": "Remember to perform the same operation on both sides of the equation"}]
            },
            "metadata": {
                "subject": "mathematics",
                "grade_level": 9,
                "difficulty": {"level": "beginner", "score": 1}
            }
        },
        {
            "id": 2,
            "title": "Quadratic Functions - Vertex Form",
            "content": {
                "question": {"en": "Find the vertex of the parabola y = x² - 4x + 3"},
                "answer": {"en": "Vertex at (2, -1)"},
                "solution": {"en": "Complete the square: y = (x-2)² - 1, so vertex is at (2, -1)"},
                "hints": [{"en": "Use the method of completing the square"}]
            },
            "metadata": {
                "subject": "mathematics",
                "grade_level": 10,
                "difficulty": {"level": "intermediate", "score": 3}
            }
        },
        {
            "id": 3,
            "title": "Derivatives - Power Rule",
            "content": {
                "question": {"en": "Find the derivative of f(x) = 3x³ - 2x² + 5x - 1"},
                "answer": {"en": "f'(x) = 9x² - 4x + 5"},
                "solution": {"en": "Apply power rule: d/dx[3x³] = 9x², d/dx[-2x²] = -4x, d/dx[5x] = 5, d/dx[-1] = 0"},
                "hints": [{"en": "Use the power rule: d/dx[x^n] = nx^(n-1)"}]
            },
            "metadata": {
                "subject": "mathematics",
                "grade_level": 12,
                "difficulty": {"level": "advanced", "score": 5}
            }
        },
        {
            "id": 4,
            "title": "Kinematics - Motion in One Dimension",
            "content": {
                "question": {"en": "A car accelerates from rest at 2 m/s² for 10 seconds. What is its final velocity?"},
                "answer": {"en": "20 m/s"},
                "solution": {"en": "Using v = v₀ + at: v = 0 + (2 m/s²)(10 s) = 20 m/s"},
                "hints": [{"en": "Use the kinematic equation v = v₀ + at"}]
            },
            "metadata": {
                "subject": "physics",
                "grade_level": 10,
                "difficulty": {"level": "intermediate", "score": 3}
            }
        },
        {
            "id": 5,
            "title": "Chemical Bonding - Ionic Bonds",
            "content": {
                "question": {"en": "What type of bond forms between sodium and chlorine in NaCl?"},
                "answer": {"en": "Ionic bond"},
                "solution": {"en": "Sodium (metal) donates an electron to chlorine (nonmetal), forming an ionic bond"},
                "hints": [{"en": "Consider the electronegativity difference between the elements"}]
            },
            "metadata": {
                "subject": "chemistry",
                "grade_level": 9,
                "difficulty": {"level": "beginner", "score": 2}
            }
        }
    ]

def demonstrate_curriculum_standards():
    """
    Demonstrate curriculum standards
    """
    print("=" * 80)
    print("ENHANCED CURRICULUM STANDARDS DEMONSTRATION")
    print("=" * 80)
    
    try:
        from enhanced_curriculum_standards import EnhancedCurriculumStandards
        
        standards = EnhancedCurriculumStandards()
        
        print("\n🇨🇦 Ontario Grade 12 Mathematics Courses:")
        ontario_math = standards.get_curriculum_structure('Ontario', 'Mathematics')
        grade_12_courses = ontario_math.get('Grade_12', {})
        for course_name, course_data in grade_12_courses.items():
            print(f"  - {course_name}: {course_data.get('description', '')}")
            for topic in course_data.get('topics', [])[:2]:  # Show first 2 topics
                print(f"    • {topic['name']}")
        
        print("\n🇺🇸 US Grade 12 Mathematics Courses:")
        us_math = standards.get_curriculum_structure('US', 'Mathematics')
        grade_12_courses = us_math.get('Grade_12', {})
        for course_name, course_data in grade_12_courses.items():
            print(f"  - {course_name}: {course_data.get('description', '')}")
            for topic in course_data.get('topics', [])[:2]:  # Show first 2 topics
                print(f"    • {topic['name']}")
        
        print("\n🔍 Topic Search Example:")
        calculus_topics = standards.find_matching_topics(['calculus'])
        print(f"Found {len(calculus_topics)} calculus-related topics:")
        for topic in calculus_topics[:3]:
            print(f"  - {topic['country']} {topic['grade']} {topic['subject']}: {topic['name']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing curriculum standards: {e}")
        return False

def demonstrate_gpt_classification():
    """
    Demonstrate GPT classification system
    """
    print("\n" + "=" * 80)
    print("GPT CLASSIFICATION SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Check for API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please set your OpenAI API key to test GPT classification")
        return False
    
    try:
        from gpt_classification_system import GPTClassificationSystem
        
        classifier = GPTClassificationSystem(openai_api_key)
        sample_questions = create_sample_questions()
        
        print(f"\n🤖 Classifying {len(sample_questions)} sample questions...")
        
        # Classify first question as example
        result = classifier.classify_question(sample_questions[0])
        
        if 'error' not in result:
            print("✅ Classification successful!")
            print(f"\n📊 Classification Results for Question 1:")
            
            ontario_class = result.get('ontario_classification', {})
            us_class = result.get('us_classification', {})
            
            if ontario_class:
                print(f"  🇨🇦 Ontario: {ontario_class.get('grade', '')} {ontario_class.get('course', '')} - {ontario_class.get('topic', '')}")
                print(f"     Confidence: {ontario_class.get('confidence', 0):.2f}")
                print(f"     Difficulty: {ontario_class.get('difficulty_level', '')}")
            
            if us_class:
                print(f"  🇺🇸 US: {us_class.get('grade', '')} {us_class.get('course', '')} - {us_class.get('topic', '')}")
                print(f"     Confidence: {us_class.get('confidence', 0):.2f}")
                print(f"     Difficulty: {us_class.get('difficulty_level', '')}")
            
            if 'quality_assessment' in result:
                qa = result['quality_assessment']
                print(f"  📈 Quality: {qa.get('content_quality', '')} | Pedagogical: {qa.get('pedagogical_value', '')}")
        else:
            print(f"❌ Classification failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing GPT classification system: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during GPT classification: {e}")
        return False

def demonstrate_dynamic_difficulty():
    """
    Demonstrate dynamic difficulty system
    """
    print("\n" + "=" * 80)
    print("DYNAMIC DIFFICULTY SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    try:
        from dynamic_difficulty_system import DynamicDifficultySystem, StudentPerformance, QuestionDifficulty, DifficultyLevel
        
        system = DynamicDifficultySystem()
        
        # Create sample student performance
        student_performance = StudentPerformance(
            student_id="demo_student",
            subject="Mathematics",
            grade="Grade_10",
            topic="Quadratic Functions",
            questions_attempted=15,
            questions_correct=11,
            average_time_seconds=120,
            recent_performance=[True, True, False, True, True, False, True, True, True, False],
            mastery_level=0.73,
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
            )
        ]
        
        print(f"👨‍🎓 Student Performance Analysis:")
        performance_level = system.calculate_student_performance_level(student_performance)
        print(f"  Performance Level: {performance_level.value}")
        print(f"  Success Rate: {student_performance.questions_correct}/{student_performance.questions_attempted} ({student_performance.questions_correct/student_performance.questions_attempted:.1%})")
        print(f"  Mastery Level: {student_performance.mastery_level:.1%}")
        print(f"  Average Time: {student_performance.average_time_seconds} seconds")
        
        print(f"\n🎯 Question Recommendations:")
        recommendations = system.recommend_question_difficulty(student_performance, questions)
        for question_id, adaptive_difficulty in recommendations:
            print(f"  {question_id}: Adaptive Difficulty {adaptive_difficulty:.2f}")
        
        print(f"\n📊 Difficulty Report:")
        report = system.generate_difficulty_report(student_performance, questions)
        print(f"  Current Mastery: {report['current_mastery']:.1%}")
        print(f"  Average Adaptive Difficulty: {report['adaptive_difficulty_analysis']['average_adaptive_difficulty']:.2f}")
        print(f"  Recommendations: {len(report['recommendations'])} suggestions")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing dynamic difficulty system: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during dynamic difficulty demonstration: {e}")
        return False

def demonstrate_integrated_system():
    """
    Demonstrate integrated system
    """
    print("\n" + "=" * 80)
    print("INTEGRATED CURRICULUM SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Check for API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Skipping integrated system demonstration")
        return False
    
    try:
        from integrated_curriculum_system import IntegratedCurriculumSystem
        
        system = IntegratedCurriculumSystem(openai_api_key)
        sample_questions = create_sample_questions()
        
        print(f"\n🔄 Processing {len(sample_questions)} questions through integrated system...")
        
        # Process questions
        results = asyncio.run(system.process_questions_complete(sample_questions, len(sample_questions)))
        
        report = results['comprehensive_report']
        
        print("✅ Integrated processing completed!")
        print(f"\n📈 System Overview:")
        print(f"  Total Questions: {report['system_overview']['total_questions_processed']}")
        print(f"  Success Rate: {report['system_overview']['success_rate']:.1%}")
        
        print(f"\n🎯 Quality Metrics:")
        print(f"  Ontario Confidence: {report['quality_metrics']['average_confidence_ontario']:.2f}")
        print(f"  US Confidence: {report['quality_metrics']['average_confidence_us']:.2f}")
        
        print(f"\n📚 Curriculum Distribution:")
        print(f"  Ontario: {report['curriculum_distribution']['ontario']}")
        print(f"  US: {report['curriculum_distribution']['us']}")
        
        print(f"\n🎓 Adaptive Learning:")
        print(f"  Curriculum Groups: {report['adaptive_learning']['curriculum_groups']}")
        print(f"  Learning Progressions: {report['adaptive_learning']['total_learning_progressions']}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'demo_results_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing integrated system: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during integrated system demonstration: {e}")
        return False

def main():
    """
    Main demonstration function
    """
    print("🚀 DreamSeedAI Curriculum Classification System Demo")
    print("=" * 80)
    
    # Check environment
    print("🔍 Checking system environment...")
    
    # Check for required files
    required_files = [
        'enhanced_curriculum_standards.py',
        'gpt_classification_system.py',
        'dynamic_difficulty_system.py',
        'integrated_curriculum_system.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return
    
    print("✅ All required files found")
    
    # Check for API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if openai_api_key:
        print("✅ OpenAI API key found")
    else:
        print("⚠️  OpenAI API key not found - some features will be limited")
    
    # Run demonstrations
    demonstrations = [
        ("Curriculum Standards", demonstrate_curriculum_standards),
        ("GPT Classification", demonstrate_gpt_classification),
        ("Dynamic Difficulty", demonstrate_dynamic_difficulty),
        ("Integrated System", demonstrate_integrated_system)
    ]
    
    results = {}
    
    for name, demo_func in demonstrations:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            results[name] = demo_func()
        except Exception as e:
            print(f"❌ Error in {name} demonstration: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("DEMONSTRATION SUMMARY")
    print("=" * 80)
    
    for name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{name}: {status}")
    
    successful_demos = sum(results.values())
    total_demos = len(results)
    
    print(f"\nOverall Success Rate: {successful_demos}/{total_demos} ({successful_demos/total_demos:.1%})")
    
    if successful_demos == total_demos:
        print("\n🎉 All demonstrations completed successfully!")
        print("\nNext Steps:")
        print("1. Set your OpenAI API key: export OPENAI_API_KEY='your_key_here'")
        print("2. Run full classification: python3 integrated_curriculum_system.py")
        print("3. Apply to your database: python3 curriculum_updater.py")
        print("4. Start the API server: python3 curriculum_api.py")
    else:
        print(f"\n⚠️  {total_demos - successful_demos} demonstration(s) failed")
        print("Check the error messages above for troubleshooting")

if __name__ == '__main__':
    main()
