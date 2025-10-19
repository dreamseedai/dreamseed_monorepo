#!/usr/bin/env python3
"""
DreamSeedAI Curriculum Classifier
Classifies questions according to US/Canada high school curriculum standards
using GPT-4.1 mini batch API
"""

import json
import os
import time
from typing import Dict, List, Any, Optional
from ai_client import get_openai_client, get_model
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CurriculumClassifier:
    """
    Classifies questions according to US/Canada curriculum standards
    """
    
    def __init__(self, openai_api_key: str):
        """
        Initialize the classifier with OpenAI API key
        
        Args:
            openai_api_key: OpenAI API key for GPT-4.1 mini batch
        """
        self.client = get_openai_client(openai_api_key)
        self.curriculum_standards = self._define_curriculum_standards()
        
    def _define_curriculum_standards(self) -> Dict[str, Any]:
        """
        Define US/Canada high school curriculum standards
        """
        return {
            "US_Standards": {
                "Mathematics": {
                    "G9": {
                        "Algebra_I": [
                            "Linear equations and inequalities",
                            "Functions and relations",
                            "Systems of equations",
                            "Polynomials and factoring",
                            "Quadratic functions",
                            "Exponential functions",
                            "Data analysis and statistics"
                        ]
                    },
                    "G10": {
                        "Geometry": [
                            "Points, lines, and planes",
                            "Angles and parallel lines",
                            "Triangles and congruence",
                            "Quadrilaterals",
                            "Similarity and proportions",
                            "Right triangles and trigonometry",
                            "Circles and arcs",
                            "Area and perimeter",
                            "Volume and surface area"
                        ]
                    },
                    "G11": {
                        "Algebra_II": [
                            "Complex numbers",
                            "Polynomial functions",
                            "Rational functions",
                            "Exponential and logarithmic functions",
                            "Trigonometric functions",
                            "Sequences and series",
                            "Probability and statistics",
                            "Conic sections"
                        ]
                    },
                    "G12": {
                        "Pre_Calculus": [
                            "Advanced functions",
                            "Trigonometric identities",
                            "Polar coordinates",
                            "Vectors",
                            "Matrices",
                            "Limits and continuity"
                        ],
                        "Calculus": [
                            "Derivatives",
                            "Applications of derivatives",
                            "Integrals",
                            "Applications of integrals",
                            "Differential equations"
                        ]
                    }
                },
                "Physics": {
                    "G9": {
                        "Physical_Science": [
                            "Motion and forces",
                            "Energy and work",
                            "Waves and sound",
                            "Light and optics",
                            "Electricity basics",
                            "Magnetism basics"
                        ]
                    },
                    "G10": {
                        "Physics_I": [
                            "Kinematics",
                            "Dynamics",
                            "Energy and momentum",
                            "Rotational motion",
                            "Simple harmonic motion",
                            "Fluid mechanics"
                        ]
                    },
                    "G11": {
                        "Physics_II": [
                            "Electric fields and forces",
                            "Magnetic fields and forces",
                            "Electromagnetic induction",
                            "AC circuits",
                            "Wave properties",
                            "Optics and interference"
                        ]
                    },
                    "G12": {
                        "AP_Physics": [
                            "Advanced mechanics",
                            "Thermodynamics",
                            "Electromagnetic fields",
                            "Quantum mechanics",
                            "Special relativity",
                            "Nuclear physics"
                        ]
                    }
                },
                "Chemistry": {
                    "G9": {
                        "Physical_Science": [
                            "Atomic structure",
                            "Periodic table",
                            "Chemical bonding",
                            "Chemical reactions",
                            "Acids and bases",
                            "Solutions and mixtures"
                        ]
                    },
                    "G10": {
                        "Chemistry_I": [
                            "Stoichiometry",
                            "Gas laws",
                            "Thermochemistry",
                            "Chemical equilibrium",
                            "Reaction rates",
                            "Electrochemistry"
                        ]
                    },
                    "G11": {
                        "Chemistry_II": [
                            "Organic chemistry basics",
                            "Biochemistry",
                            "Nuclear chemistry",
                            "Environmental chemistry",
                            "Analytical chemistry",
                            "Industrial chemistry"
                        ]
                    },
                    "G12": {
                        "AP_Chemistry": [
                            "Advanced stoichiometry",
                            "Thermodynamics",
                            "Kinetics and equilibrium",
                            "Electrochemistry",
                            "Organic chemistry",
                            "Nuclear chemistry"
                        ]
                    }
                },
                "Biology": {
                    "G9": {
                        "Life_Science": [
                            "Cell structure and function",
                            "Cell division",
                            "Genetics basics",
                            "Evolution",
                            "Ecology",
                            "Human body systems"
                        ]
                    },
                    "G10": {
                        "Biology_I": [
                            "Molecular biology",
                            "Genetics and heredity",
                            "Evolution and natural selection",
                            "Ecology and ecosystems",
                            "Plant biology",
                            "Animal biology"
                        ]
                    },
                    "G11": {
                        "Biology_II": [
                            "Advanced genetics",
                            "Biotechnology",
                            "Human anatomy and physiology",
                            "Microbiology",
                            "Environmental biology",
                            "Conservation biology"
                        ]
                    },
                    "G12": {
                        "AP_Biology": [
                            "Biochemistry",
                            "Cell biology",
                            "Genetics and molecular biology",
                            "Evolution and diversity",
                            "Ecology and behavior",
                            "Human physiology"
                        ]
                    }
                }
            },
            "Canada_Standards": {
                "Mathematics": {
                    "G9": {
                        "Mathematics_9": [
                            "Number sense and operations",
                            "Algebra and patterns",
                            "Geometry and measurement",
                            "Data management and probability",
                            "Financial literacy"
                        ]
                    },
                    "G10": {
                        "Mathematics_10": [
                            "Linear relations",
                            "Quadratic relations",
                            "Trigonometry",
                            "Analytic geometry",
                            "Data management"
                        ]
                    },
                    "G11": {
                        "Functions_11": [
                            "Quadratic functions",
                            "Exponential functions",
                            "Trigonometric functions",
                            "Discrete functions",
                            "Financial applications"
                        ]
                    },
                    "G12": {
                        "Advanced_Functions": [
                            "Polynomial functions",
                            "Exponential and logarithmic functions",
                            "Trigonometric functions",
                            "Combinations of functions"
                        ],
                        "Calculus_and_Vectors": [
                            "Limits and continuity",
                            "Derivatives",
                            "Applications of derivatives",
                            "Integrals",
                            "Vectors in two and three dimensions"
                        ],
                        "Data_Management": [
                            "Probability",
                            "Statistics",
                            "Distributions",
                            "Hypothesis testing",
                            "Regression analysis"
                        ]
                    }
                },
                "Physics": {
                    "G9": {
                        "Science_9": [
                            "Electricity and magnetism",
                            "Energy and motion",
                            "Waves and sound",
                            "Light and optics"
                        ]
                    },
                    "G10": {
                        "Science_10": [
                            "Motion and forces",
                            "Energy transformations",
                            "Electricity and magnetism",
                            "Waves and radiation"
                        ]
                    },
                    "G11": {
                        "Physics_11": [
                            "Kinematics",
                            "Forces and motion",
                            "Energy and momentum",
                            "Waves and sound",
                            "Light and geometric optics"
                        ]
                    },
                    "G12": {
                        "Physics_12": [
                            "Forces and motion",
                            "Energy and momentum",
                            "Electric and magnetic fields",
                            "Electromagnetic radiation",
                            "Quantum mechanics",
                            "Special relativity"
                        ]
                    }
                },
                "Chemistry": {
                    "G9": {
                        "Science_9": [
                            "Atomic theory",
                            "Chemical bonding",
                            "Chemical reactions",
                            "Solutions and mixtures"
                        ]
                    },
                    "G10": {
                        "Science_10": [
                            "Chemical reactions",
                            "Acids and bases",
                            "Chemical bonding",
                            "Organic chemistry basics"
                        ]
                    },
                    "G11": {
                        "Chemistry_11": [
                            "Atomic structure",
                            "Chemical bonding",
                            "Chemical reactions",
                            "Solutions and solubility",
                            "Acids and bases"
                        ]
                    },
                    "G12": {
                        "Chemistry_12": [
                            "Reaction kinetics",
                            "Chemical equilibrium",
                            "Acids and bases",
                            "Oxidation and reduction",
                            "Organic chemistry"
                        ]
                    }
                },
                "Biology": {
                    "G9": {
                        "Science_9": [
                            "Cell biology",
                            "Genetics",
                            "Evolution",
                            "Ecology"
                        ]
                    },
                    "G10": {
                        "Science_10": [
                            "Cell division",
                            "Genetics and heredity",
                            "Evolution",
                            "Ecology and ecosystems"
                        ]
                    },
                    "G11": {
                        "Biology_11": [
                            "Cell biology",
                            "Genetics",
                            "Evolution",
                            "Ecology",
                            "Human biology"
                        ]
                    },
                    "G12": {
                        "Biology_12": [
                            "Cell biology",
                            "Genetics and molecular biology",
                            "Evolution",
                            "Ecology",
                            "Human anatomy and physiology"
                        ]
                    }
                }
            }
        }
    
    def create_classification_prompt(self, question_data: Dict[str, Any]) -> str:
        """
        Create a prompt for classifying a question according to curriculum standards
        
        Args:
            question_data: Question data including title, content, and metadata
            
        Returns:
            Formatted prompt for GPT-4.1 mini
        """
        curriculum_text = json.dumps(self.curriculum_standards, indent=2)
        
        prompt = f"""
You are an expert educational content classifier specializing in US and Canadian high school curriculum standards.

Your task is to classify the following question according to both US and Canadian curriculum standards.

CURRICULUM STANDARDS:
{curriculum_text}

QUESTION TO CLASSIFY:
Title: {question_data.get('title', '')}
Content: {question_data.get('content', {}).get('question', {}).get('en', '')}
Answer: {question_data.get('content', {}).get('answer', {}).get('en', '')}
Solution: {question_data.get('content', {}).get('solution', {}).get('en', '')}
Current Subject: {question_data.get('metadata', {}).get('subject', '')}
Current Grade: {question_data.get('metadata', {}).get('grade_level', '')}
Current Difficulty: {question_data.get('metadata', {}).get('difficulty', {}).get('level', '')}

INSTRUCTIONS:
1. Analyze the question content to determine the most appropriate classification
2. Consider the mathematical/scientific concepts being tested
3. Match to the closest curriculum standard for both US and Canada
4. Provide confidence scores (0-1) for each classification

RESPONSE FORMAT (JSON):
{{
    "us_classification": {{
        "grade": "G9|G10|G11|G12",
        "subject": "Mathematics|Physics|Chemistry|Biology",
        "course": "specific course name",
        "topic": "specific topic from curriculum",
        "confidence": 0.95
    }},
    "canada_classification": {{
        "grade": "G9|G10|G11|G12", 
        "subject": "Mathematics|Physics|Chemistry|Biology",
        "course": "specific course name",
        "topic": "specific topic from curriculum",
        "confidence": 0.95
    }},
    "reasoning": "Brief explanation of classification decisions",
    "difficulty_assessment": {{
        "us_difficulty": "beginner|intermediate|advanced|expert",
        "canada_difficulty": "beginner|intermediate|advanced|expert",
        "reasoning": "Why this difficulty level was chosen"
    }},
    "curriculum_alignment": {{
        "us_alignment": 0.95,
        "canada_alignment": 0.90,
        "notes": "Any special considerations or edge cases"
    }}
}}

Classify this question now:
"""
        return prompt
    
    def classify_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a single question using GPT-4.1 mini
        
        Args:
            question_data: Question data to classify
            
        Returns:
            Classification results
        """
        try:
            prompt = self.create_classification_prompt(question_data)
            
            response = self.client.chat.completions.create(
                model=get_model(),
                messages=[
                    {"role": "system", "content": "You are an expert educational content classifier. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error classifying question: {e}")
            return {
                "error": str(e),
                "us_classification": None,
                "canada_classification": None
            }
    
    def classify_questions_batch(self, questions_data: List[Dict[str, Any]], 
                                batch_size: int = 10, delay: float = 1.0) -> List[Dict[str, Any]]:
        """
        Classify multiple questions in batches
        
        Args:
            questions_data: List of question data to classify
            batch_size: Number of questions to process in each batch
            delay: Delay between batches in seconds
            
        Returns:
            List of classification results
        """
        results = []
        total_questions = len(questions_data)
        
        logger.info(f"Starting batch classification of {total_questions} questions")
        
        for i in range(0, total_questions, batch_size):
            batch = questions_data[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_questions + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} questions)")
            
            batch_results = []
            for j, question in enumerate(batch):
                try:
                    result = self.classify_question(question)
                    result['original_question_id'] = question.get('id')
                    batch_results.append(result)
                    
                    if (j + 1) % 5 == 0:
                        logger.info(f"  Processed {j + 1}/{len(batch)} questions in batch")
                        
                except Exception as e:
                    logger.error(f"Error processing question {question.get('id', 'unknown')}: {e}")
                    batch_results.append({
                        'original_question_id': question.get('id'),
                        'error': str(e)
                    })
            
            results.extend(batch_results)
            
            # Save intermediate results
            if batch_num % 5 == 0:
                self._save_intermediate_results(results, batch_num)
            
            # Delay between batches to respect rate limits
            if i + batch_size < total_questions:
                time.sleep(delay)
        
        logger.info(f"Completed classification of {total_questions} questions")
        return results
    
    def _save_intermediate_results(self, results: List[Dict[str, Any]], batch_num: int):
        """Save intermediate results to avoid data loss"""
        filename = f"curriculum_classification_batch_{batch_num}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved intermediate results to {filename}")
    
    def generate_classification_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive classification report
        
        Args:
            results: List of classification results
            
        Returns:
            Classification statistics and analysis
        """
        total_questions = len(results)
        successful_classifications = len([r for r in results if 'error' not in r])
        failed_classifications = total_questions - successful_classifications
        
        # US Classification Statistics
        us_grades = {}
        us_subjects = {}
        us_courses = {}
        us_topics = {}
        
        # Canada Classification Statistics
        canada_grades = {}
        canada_subjects = {}
        canada_courses = {}
        canada_topics = {}
        
        # Difficulty Analysis
        us_difficulties = {}
        canada_difficulties = {}
        
        # Confidence Analysis
        us_confidences = []
        canada_confidences = []
        
        for result in results:
            if 'error' in result:
                continue
                
            # US Classification
            if result.get('us_classification'):
                us_class = result['us_classification']
                us_grades[us_class.get('grade', 'Unknown')] = us_grades.get(us_class.get('grade', 'Unknown'), 0) + 1
                us_subjects[us_class.get('subject', 'Unknown')] = us_subjects.get(us_class.get('subject', 'Unknown'), 0) + 1
                us_courses[us_class.get('course', 'Unknown')] = us_courses.get(us_class.get('course', 'Unknown'), 0) + 1
                us_topics[us_class.get('topic', 'Unknown')] = us_topics.get(us_class.get('topic', 'Unknown'), 0) + 1
                us_confidences.append(us_class.get('confidence', 0))
            
            # Canada Classification
            if result.get('canada_classification'):
                canada_class = result['canada_classification']
                canada_grades[canada_class.get('grade', 'Unknown')] = canada_grades.get(canada_class.get('grade', 'Unknown'), 0) + 1
                canada_subjects[canada_class.get('subject', 'Unknown')] = canada_subjects.get(canada_class.get('subject', 'Unknown'), 0) + 1
                canada_courses[canada_class.get('course', 'Unknown')] = canada_courses.get(canada_class.get('course', 'Unknown'), 0) + 1
                canada_topics[canada_class.get('topic', 'Unknown')] = canada_topics.get(canada_class.get('topic', 'Unknown'), 0) + 1
                canada_confidences.append(canada_class.get('confidence', 0))
            
            # Difficulty Analysis
            if result.get('difficulty_assessment'):
                diff_assess = result['difficulty_assessment']
                us_difficulties[diff_assess.get('us_difficulty', 'Unknown')] = us_difficulties.get(diff_assess.get('us_difficulty', 'Unknown'), 0) + 1
                canada_difficulties[diff_assess.get('canada_difficulty', 'Unknown')] = canada_difficulties.get(diff_assess.get('canada_difficulty', 'Unknown'), 0) + 1
        
        report = {
            "classification_summary": {
                "total_questions": total_questions,
                "successful_classifications": successful_classifications,
                "failed_classifications": failed_classifications,
                "success_rate": successful_classifications / total_questions if total_questions > 0 else 0
            },
            "us_curriculum_distribution": {
                "grades": us_grades,
                "subjects": us_subjects,
                "courses": us_courses,
                "topics": us_topics,
                "difficulties": us_difficulties,
                "average_confidence": sum(us_confidences) / len(us_confidences) if us_confidences else 0
            },
            "canada_curriculum_distribution": {
                "grades": canada_grades,
                "subjects": canada_subjects,
                "courses": canada_courses,
                "topics": canada_topics,
                "difficulties": canada_difficulties,
                "average_confidence": sum(canada_confidences) / len(canada_confidences) if canada_confidences else 0
            },
            "curriculum_comparison": {
                "grade_alignment": self._calculate_alignment(us_grades, canada_grades),
                "subject_alignment": self._calculate_alignment(us_subjects, canada_subjects),
                "difficulty_alignment": self._calculate_alignment(us_difficulties, canada_difficulties)
            },
            "recommendations": self._generate_recommendations(results)
        }
        
        return report
    
    def _calculate_alignment(self, us_data: Dict, canada_data: Dict) -> float:
        """Calculate alignment between US and Canada distributions"""
        all_keys = set(us_data.keys()) | set(canada_data.keys())
        if not all_keys:
            return 0.0
        
        total_us = sum(us_data.values())
        total_canada = sum(canada_data.values())
        
        if total_us == 0 or total_canada == 0:
            return 0.0
        
        alignment = 0.0
        for key in all_keys:
            us_ratio = us_data.get(key, 0) / total_us
            canada_ratio = canada_data.get(key, 0) / total_canada
            alignment += min(us_ratio, canada_ratio)
        
        return alignment
    
    def _generate_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on classification results"""
        recommendations = []
        
        # Analyze confidence scores
        us_confidences = [r.get('us_classification', {}).get('confidence', 0) for r in results if 'us_classification' in r]
        canada_confidences = [r.get('canada_classification', {}).get('confidence', 0) for r in results if 'canada_classification' in r]
        
        if us_confidences:
            avg_us_confidence = sum(us_confidences) / len(us_confidences)
            if avg_us_confidence < 0.8:
                recommendations.append("US classification confidence is low. Consider manual review of low-confidence classifications.")
        
        if canada_confidences:
            avg_canada_confidence = sum(canada_confidences) / len(canada_confidences)
            if avg_canada_confidence < 0.8:
                recommendations.append("Canada classification confidence is low. Consider manual review of low-confidence classifications.")
        
        # Analyze curriculum coverage
        us_subjects = set()
        canada_subjects = set()
        for result in results:
            if result.get('us_classification'):
                us_subjects.add(result['us_classification'].get('subject', ''))
            if result.get('canada_classification'):
                canada_subjects.add(result['canada_classification'].get('subject', ''))
        
        if len(us_subjects) < 4:
            recommendations.append("Limited subject coverage in US classification. Consider expanding question diversity.")
        
        if len(canada_subjects) < 4:
            recommendations.append("Limited subject coverage in Canada classification. Consider expanding question diversity.")
        
        return recommendations

def main():
    """
    Main function to run curriculum classification
    """
    # Load questions data
    questions_file = 'enhanced_migrated_data/enhanced_dreamseed_questions.json'
    
    if not os.path.exists(questions_file):
        logger.error(f"Questions file not found: {questions_file}")
        return
    
    # Load OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return
    
    # Initialize classifier
    classifier = CurriculumClassifier(openai_api_key)
    
    # Load questions data
    logger.info("Loading questions data...")
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    # Take a sample for testing (first 100 questions)
    sample_size = min(100, len(questions_data))
    sample_questions = questions_data[:sample_size]
    
    logger.info(f"Classifying {sample_size} questions...")
    
    # Classify questions
    results = classifier.classify_questions_batch(sample_questions, batch_size=5, delay=2.0)
    
    # Generate report
    report = classifier.generate_classification_report(results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with open(f'curriculum_classification_results_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    with open(f'curriculum_classification_report_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("CURRICULUM CLASSIFICATION SUMMARY")
    print("="*60)
    print(f"Total Questions Processed: {report['classification_summary']['total_questions']}")
    print(f"Successful Classifications: {report['classification_summary']['successful_classifications']}")
    print(f"Success Rate: {report['classification_summary']['success_rate']:.2%}")
    
    print(f"\nUS Curriculum Distribution:")
    print(f"  Grades: {report['us_curriculum_distribution']['grades']}")
    print(f"  Subjects: {report['us_curriculum_distribution']['subjects']}")
    print(f"  Average Confidence: {report['us_curriculum_distribution']['average_confidence']:.2f}")
    
    print(f"\nCanada Curriculum Distribution:")
    print(f"  Grades: {report['canada_curriculum_distribution']['grades']}")
    print(f"  Subjects: {report['canada_curriculum_distribution']['subjects']}")
    print(f"  Average Confidence: {report['canada_curriculum_distribution']['average_confidence']:.2f}")
    
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    print(f"\nResults saved to:")
    print(f"  - curriculum_classification_results_{timestamp}.json")
    print(f"  - curriculum_classification_report_{timestamp}.json")

if __name__ == '__main__':
    main()
