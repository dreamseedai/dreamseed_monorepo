#!/usr/bin/env python3
"""
DreamSeedAI Curriculum Classification Demo
Demonstrates the curriculum classification system
"""

import json
import os
from typing import Dict, List, Any

def create_demo_questions() -> List[Dict[str, Any]]:
    """
    Create sample questions for demonstration
    """
    return [
        {
            "id": 1,
            "title": "Linear Equations",
            "content": {
                "question": {
                    "en": "Solve for x: 2x + 5 = 13"
                },
                "answer": {
                    "en": "x = 4"
                },
                "solution": {
                    "en": "Subtract 5 from both sides: 2x = 8, then divide by 2: x = 4"
                }
            },
            "metadata": {
                "subject": "mathematics",
                "grade_level": 9,
                "difficulty": {
                    "level": "beginner",
                    "score": 1
                }
            }
        },
        {
            "id": 2,
            "title": "Quadratic Functions",
            "content": {
                "question": {
                    "en": "Find the vertex of the parabola y = x² - 4x + 3"
                },
                "answer": {
                    "en": "Vertex at (2, -1)"
                },
                "solution": {
                    "en": "Complete the square: y = (x-2)² - 1, so vertex is at (2, -1)"
                }
            },
            "metadata": {
                "subject": "mathematics",
                "grade_level": 10,
                "difficulty": {
                    "level": "intermediate",
                    "score": 3
                }
            }
        },
        {
            "id": 3,
            "title": "Derivatives",
            "content": {
                "question": {
                    "en": "Find the derivative of f(x) = 3x³ - 2x² + 5x - 1"
                },
                "answer": {
                    "en": "f'(x) = 9x² - 4x + 5"
                },
                "solution": {
                    "en": "Apply power rule: d/dx[3x³] = 9x², d/dx[-2x²] = -4x, d/dx[5x] = 5, d/dx[-1] = 0"
                }
            },
            "metadata": {
                "subject": "mathematics",
                "grade_level": 12,
                "difficulty": {
                    "level": "advanced",
                    "score": 5
                }
            }
        },
        {
            "id": 4,
            "title": "Kinematics",
            "content": {
                "question": {
                    "en": "A car accelerates from rest at 2 m/s² for 10 seconds. What is its final velocity?"
                },
                "answer": {
                    "en": "20 m/s"
                },
                "solution": {
                    "en": "Using v = v₀ + at: v = 0 + (2 m/s²)(10 s) = 20 m/s"
                }
            },
            "metadata": {
                "subject": "physics",
                "grade_level": 10,
                "difficulty": {
                    "level": "intermediate",
                    "score": 3
                }
            }
        },
        {
            "id": 5,
            "title": "Chemical Bonding",
            "content": {
                "question": {
                    "en": "What type of bond forms between sodium and chlorine in NaCl?"
                },
                "answer": {
                    "en": "Ionic bond"
                },
                "solution": {
                    "en": "Sodium (metal) donates an electron to chlorine (nonmetal), forming an ionic bond"
                }
            },
            "metadata": {
                "subject": "chemistry",
                "grade_level": 9,
                "difficulty": {
                    "level": "beginner",
                    "score": 2
                }
            }
        }
    ]

def demonstrate_curriculum_standards():
    """
    Demonstrate the curriculum standards structure
    """
    print("=" * 60)
    print("DREAMSEEDAI CURRICULUM STANDARDS DEMO")
    print("=" * 60)
    
    # US Standards Example
    print("\n🇺🇸 US CURRICULUM STANDARDS")
    print("-" * 30)
    
    us_math_g9 = {
        "Algebra_I": [
            "Linear equations and inequalities",
            "Functions and relations", 
            "Systems of equations",
            "Polynomials and factoring",
            "Quadratic functions",
            "Exponential functions",
            "Data analysis and statistics"
        ]
    }
    
    print("Grade 9 Mathematics (Algebra I):")
    for topic in us_math_g9["Algebra_I"]:
        print(f"  • {topic}")
    
    us_math_g12 = {
        "Calculus": [
            "Derivatives",
            "Applications of derivatives",
            "Integrals", 
            "Applications of integrals",
            "Differential equations"
        ]
    }
    
    print("\nGrade 12 Mathematics (Calculus):")
    for topic in us_math_g12["Calculus"]:
        print(f"  • {topic}")
    
    # Canada Standards Example
    print("\n🇨🇦 CANADA CURRICULUM STANDARDS")
    print("-" * 30)
    
    canada_math_g9 = {
        "Mathematics_9": [
            "Number sense and operations",
            "Algebra and patterns",
            "Geometry and measurement",
            "Data management and probability",
            "Financial literacy"
        ]
    }
    
    print("Grade 9 Mathematics:")
    for topic in canada_math_g9["Mathematics_9"]:
        print(f"  • {topic}")
    
    canada_math_g12 = {
        "Calculus_and_Vectors": [
            "Limits and continuity",
            "Derivatives",
            "Applications of derivatives",
            "Integrals",
            "Vectors in two and three dimensions"
        ]
    }
    
    print("\nGrade 12 Mathematics (Calculus and Vectors):")
    for topic in canada_math_g12["Calculus_and_Vectors"]:
        print(f"  • {topic}")

def demonstrate_classification_process():
    """
    Demonstrate the classification process
    """
    print("\n" + "=" * 60)
    print("CURRICULUM CLASSIFICATION PROCESS")
    print("=" * 60)
    
    demo_questions = create_demo_questions()
    
    print(f"\n📚 Sample Questions to Classify: {len(demo_questions)}")
    print("-" * 40)
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{i}. {question['title']}")
        print(f"   Subject: {question['metadata']['subject']}")
        print(f"   Current Grade: {question['metadata']['grade_level']}")
        print(f"   Difficulty: {question['metadata']['difficulty']['level']}")
        print(f"   Question: {question['content']['question']['en'][:50]}...")
    
    print(f"\n🤖 GPT-4.1 Mini Classification Process:")
    print("-" * 40)
    print("1. Analyze question content and concepts")
    print("2. Match to US curriculum standards")
    print("3. Match to Canada curriculum standards") 
    print("4. Assign confidence scores")
    print("5. Determine difficulty levels")
    print("6. Generate reasoning for classification")
    
    # Simulate classification results
    print(f"\n📊 Expected Classification Results:")
    print("-" * 40)
    
    expected_results = [
        {
            "question_id": 1,
            "us_classification": {
                "grade": "G9",
                "subject": "Mathematics",
                "course": "Algebra_I",
                "topic": "Linear equations and inequalities",
                "confidence": 0.95
            },
            "canada_classification": {
                "grade": "G9", 
                "subject": "Mathematics",
                "course": "Mathematics_9",
                "topic": "Algebra and patterns",
                "confidence": 0.90
            }
        },
        {
            "question_id": 2,
            "us_classification": {
                "grade": "G10",
                "subject": "Mathematics", 
                "course": "Geometry",
                "topic": "Quadratic functions",
                "confidence": 0.88
            },
            "canada_classification": {
                "grade": "G10",
                "subject": "Mathematics",
                "course": "Mathematics_10", 
                "topic": "Quadratic relations",
                "confidence": 0.92
            }
        },
        {
            "question_id": 3,
            "us_classification": {
                "grade": "G12",
                "subject": "Mathematics",
                "course": "Calculus",
                "topic": "Derivatives",
                "confidence": 0.98
            },
            "canada_classification": {
                "grade": "G12",
                "subject": "Mathematics",
                "course": "Calculus_and_Vectors",
                "topic": "Derivatives", 
                "confidence": 0.96
            }
        }
    ]
    
    for result in expected_results:
        print(f"\nQuestion {result['question_id']}:")
        print(f"  US: {result['us_classification']['grade']} {result['us_classification']['course']} - {result['us_classification']['topic']} (Confidence: {result['us_classification']['confidence']})")
        print(f"  Canada: {result['canada_classification']['grade']} {result['canada_classification']['course']} - {result['canada_classification']['topic']} (Confidence: {result['canada_classification']['confidence']})")

def demonstrate_api_usage():
    """
    Demonstrate API usage examples
    """
    print("\n" + "=" * 60)
    print("CURRICULUM API USAGE EXAMPLES")
    print("=" * 60)
    
    print("\n🔗 API Endpoints:")
    print("-" * 20)
    print("• POST /curriculum/recommendations - Get curriculum-based recommendations")
    print("• POST /curriculum/progress - Update student progress")
    print("• GET /curriculum/progress/{student_id} - Get student progress")
    print("• POST /curriculum/analytics - Get comprehensive analytics")
    print("• GET /curriculum/standards - Get curriculum standards")
    print("• GET /curriculum/statistics - Get classification statistics")
    
    print(f"\n📝 Example API Requests:")
    print("-" * 25)
    
    # Recommendation request example
    recommendation_request = {
        "student_id": "student_123",
        "country": "US",
        "subject": "Mathematics",
        "grade": "G10",
        "course": "Geometry",
        "limit": 10,
        "difficulty_preference": "intermediate"
    }
    
    print("1. Get Curriculum Recommendations:")
    print(json.dumps(recommendation_request, indent=2))
    
    # Progress update example
    progress_request = {
        "student_id": "student_123",
        "country": "US",
        "subject": "Mathematics",
        "grade": "G10",
        "course": "Geometry",
        "topic": "Quadratic functions",
        "question_id": "question_456",
        "is_correct": True,
        "time_spent_seconds": 120
    }
    
    print("\n2. Update Curriculum Progress:")
    print(json.dumps(progress_request, indent=2))
    
    # Analytics request example
    analytics_request = {
        "student_id": "student_123",
        "country": "US",
        "subject": "Mathematics"
    }
    
    print("\n3. Get Curriculum Analytics:")
    print(json.dumps(analytics_request, indent=2))

def demonstrate_benefits():
    """
    Demonstrate the benefits of curriculum classification
    """
    print("\n" + "=" * 60)
    print("BENEFITS OF CURRICULUM CLASSIFICATION")
    print("=" * 60)
    
    benefits = [
        {
            "title": "🎯 Accurate Curriculum Alignment",
            "description": "Questions are properly aligned with US and Canada curriculum standards",
            "impact": "Students get questions that match their actual coursework"
        },
        {
            "title": "📈 Improved Learning Outcomes", 
            "description": "Personalized recommendations based on curriculum progress",
            "impact": "Better academic performance and engagement"
        },
        {
            "title": "🌍 Global Compatibility",
            "description": "Support for multiple countries' educational systems",
            "impact": "Expanded market reach and user satisfaction"
        },
        {
            "title": "🤖 AI-Powered Classification",
            "description": "GPT-4.1 mini provides accurate and consistent classification",
            "impact": "Scalable and cost-effective content organization"
        },
        {
            "title": "📊 Detailed Analytics",
            "description": "Comprehensive progress tracking and performance insights",
            "impact": "Data-driven learning optimization"
        },
        {
            "title": "🔄 Continuous Improvement",
            "description": "Feedback loop for classification accuracy enhancement",
            "impact": "Ever-improving content quality and relevance"
        }
    ]
    
    for benefit in benefits:
        print(f"\n{benefit['title']}")
        print(f"  Description: {benefit['description']}")
        print(f"  Impact: {benefit['impact']}")

def main():
    """
    Main demonstration function
    """
    print("🚀 DreamSeedAI Curriculum Classification System Demo")
    
    # Demonstrate curriculum standards
    demonstrate_curriculum_standards()
    
    # Demonstrate classification process
    demonstrate_classification_process()
    
    # Demonstrate API usage
    demonstrate_api_usage()
    
    # Demonstrate benefits
    demonstrate_benefits()
    
    print("\n" + "=" * 60)
    print("🎉 DEMO COMPLETE!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Set your OpenAI API key in .env file")
    print("2. Run: python3 curriculum_classifier.py")
    print("3. Apply schema updates: psql dreamseedai < curriculum_schema_update.sql")
    print("4. Update database: python3 curriculum_updater.py")
    print("5. Start API server: python3 curriculum_api.py")
    print("\nYour questions will be perfectly aligned with US and Canada curricula! 🌟")

if __name__ == '__main__':
    main()
