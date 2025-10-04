#!/usr/bin/env python3
"""
Integrated Curriculum Classification System
Complete system for curriculum-based question classification and adaptive learning
"""

import json
import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Import our custom modules
from enhanced_curriculum_standards import EnhancedCurriculumStandards
from gpt_classification_system import GPTClassificationSystem
from dynamic_difficulty_system import DynamicDifficultySystem, StudentPerformance, QuestionDifficulty, DifficultyLevel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegratedCurriculumSystem:
    """
    Integrated system combining curriculum standards, GPT classification, and dynamic difficulty
    """
    
    def __init__(self, openai_api_key: str):
        """
        Initialize the integrated system
        
        Args:
            openai_api_key: OpenAI API key for GPT-4.1 mini
        """
        self.curriculum_standards = EnhancedCurriculumStandards()
        self.gpt_classifier = GPTClassificationSystem(openai_api_key)
        self.difficulty_system = DynamicDifficultySystem()
        
        logger.info("Integrated Curriculum System initialized successfully")
    
    async def process_questions_complete(self, questions_data: List[Dict[str, Any]], 
                                       sample_size: int = 50) -> Dict[str, Any]:
        """
        Complete processing pipeline for questions
        
        Args:
            questions_data: List of question data
            sample_size: Number of questions to process
            
        Returns:
            Complete processing results
        """
        logger.info(f"Starting complete processing of {min(sample_size, len(questions_data))} questions")
        
        # Step 1: Take sample
        sample_questions = questions_data[:sample_size]
        
        # Step 2: GPT Classification
        logger.info("Step 1: GPT Classification")
        classification_results = await self.gpt_classifier.classify_questions_batch_async(
            sample_questions, batch_size=5, delay=2.0
        )
        
        # Step 3: Validate and enhance classifications
        logger.info("Step 2: Validation and Enhancement")
        enhanced_results = self._enhance_classification_results(classification_results)
        
        # Step 4: Generate difficulty assessments
        logger.info("Step 3: Difficulty Assessment")
        difficulty_assessments = self._generate_difficulty_assessments(enhanced_results)
        
        # Step 5: Create adaptive learning recommendations
        logger.info("Step 4: Adaptive Learning Recommendations")
        adaptive_recommendations = self._generate_adaptive_recommendations(enhanced_results, difficulty_assessments)
        
        # Step 6: Generate comprehensive report
        logger.info("Step 5: Generating Comprehensive Report")
        comprehensive_report = self._generate_comprehensive_report(
            enhanced_results, difficulty_assessments, adaptive_recommendations
        )
        
        return {
            "classification_results": enhanced_results,
            "difficulty_assessments": difficulty_assessments,
            "adaptive_recommendations": adaptive_recommendations,
            "comprehensive_report": comprehensive_report,
            "processing_metadata": {
                "total_questions_processed": len(sample_questions),
                "processing_date": datetime.now().isoformat(),
                "system_version": "1.0.0"
            }
        }
    
    def _enhance_classification_results(self, classification_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance classification results with additional analysis
        
        Args:
            classification_results: Raw classification results from GPT
            
        Returns:
            Enhanced classification results
        """
        enhanced_results = []
        
        for result in classification_results:
            if 'error' in result:
                enhanced_results.append(result)
                continue
            
            # Add curriculum alignment analysis
            result['curriculum_alignment_analysis'] = self._analyze_curriculum_alignment(result)
            
            # Add learning objective mapping
            result['learning_objectives'] = self._map_learning_objectives(result)
            
            # Add prerequisite analysis
            result['prerequisites'] = self._analyze_prerequisites(result)
            
            # Add cross-curriculum connections
            result['cross_curriculum_connections'] = self._find_cross_curriculum_connections(result)
            
            enhanced_results.append(result)
        
        return enhanced_results
    
    def _analyze_curriculum_alignment(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze curriculum alignment between Ontario and US standards
        
        Args:
            result: Classification result
            
        Returns:
            Curriculum alignment analysis
        """
        ontario_class = result.get('ontario_classification', {})
        us_class = result.get('us_classification', {})
        
        alignment_score = 0.0
        alignment_notes = []
        
        if ontario_class and us_class:
            # Compare grade levels
            ontario_grade = ontario_class.get('grade', '')
            us_grade = us_class.get('grade', '')
            
            if ontario_grade == us_grade:
                alignment_score += 0.3
                alignment_notes.append("Same grade level")
            else:
                alignment_notes.append(f"Different grade levels: {ontario_grade} vs {us_grade}")
            
            # Compare subjects
            ontario_subject = ontario_class.get('subject', '')
            us_subject = us_class.get('subject', '')
            
            if ontario_subject == us_subject:
                alignment_score += 0.3
                alignment_notes.append("Same subject")
            else:
                alignment_notes.append(f"Different subjects: {ontario_subject} vs {us_subject}")
            
            # Compare topics
            ontario_topic = ontario_class.get('topic', '')
            us_topic = us_class.get('topic', '')
            
            if ontario_topic.lower() == us_topic.lower():
                alignment_score += 0.4
                alignment_notes.append("Same topic")
            else:
                alignment_notes.append(f"Different topics: {ontario_topic} vs {us_topic}")
        
        return {
            "alignment_score": alignment_score,
            "alignment_level": "high" if alignment_score >= 0.8 else "medium" if alignment_score >= 0.5 else "low",
            "notes": alignment_notes
        }
    
    def _map_learning_objectives(self, result: Dict[str, Any]) -> List[str]:
        """
        Map question to specific learning objectives
        
        Args:
            result: Classification result
            
        Returns:
            List of learning objectives
        """
        objectives = []
        
        ontario_class = result.get('ontario_classification', {})
        us_class = result.get('us_classification', {})
        
        if ontario_class:
            topic = ontario_class.get('topic', '')
            subtopic = ontario_class.get('subtopic', '')
            
            # Map to curriculum standards
            topics = self.curriculum_standards.find_matching_topics([topic, subtopic], 'Ontario')
            for topic_data in topics:
                if 'learning_objectives' in topic_data:
                    objectives.extend(topic_data['learning_objectives'])
        
        if us_class:
            topic = us_class.get('topic', '')
            subtopic = us_class.get('subtopic', '')
            
            # Map to curriculum standards
            topics = self.curriculum_standards.find_matching_topics([topic, subtopic], 'US')
            for topic_data in topics:
                if 'learning_objectives' in topic_data:
                    objectives.extend(topic_data['learning_objectives'])
        
        return list(set(objectives))  # Remove duplicates
    
    def _analyze_prerequisites(self, result: Dict[str, Any]) -> List[str]:
        """
        Analyze prerequisite skills for the question
        
        Args:
            result: Classification result
            
        Returns:
            List of prerequisite skills
        """
        prerequisites = []
        
        ontario_class = result.get('ontario_classification', {})
        us_class = result.get('us_classification', {})
        
        if ontario_class:
            topic = ontario_class.get('topic', '')
            subtopic = ontario_class.get('subtopic', '')
            
            # Map to curriculum standards
            topics = self.curriculum_standards.find_matching_topics([topic, subtopic], 'Ontario')
            for topic_data in topics:
                if 'prerequisites' in topic_data:
                    prerequisites.extend(topic_data['prerequisites'])
        
        if us_class:
            topic = us_class.get('topic', '')
            subtopic = us_class.get('subtopic', '')
            
            # Map to curriculum standards
            topics = self.curriculum_standards.find_matching_topics([topic, subtopic], 'US')
            for topic_data in topics:
                if 'prerequisites' in topic_data:
                    prerequisites.extend(topic_data['prerequisites'])
        
        return list(set(prerequisites))  # Remove duplicates
    
    def _find_cross_curriculum_connections(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find connections between different curriculum areas
        
        Args:
            result: Classification result
            
        Returns:
            List of cross-curriculum connections
        """
        connections = []
        
        ontario_class = result.get('ontario_classification', {})
        us_class = result.get('us_classification', {})
        
        if ontario_class and us_class:
            # Find related topics in other subjects
            ontario_topic = ontario_class.get('topic', '')
            us_topic = us_class.get('topic', '')
            
            # Search for related topics in other subjects
            related_topics = self.curriculum_standards.find_matching_topics([ontario_topic, us_topic])
            
            for topic in related_topics:
                if topic['subject'] != ontario_class.get('subject', ''):
                    connections.append({
                        "curriculum": topic['country'],
                        "subject": topic['subject'],
                        "topic": topic['name'],
                        "connection_type": "related_concept"
                    })
        
        return connections
    
    def _generate_difficulty_assessments(self, enhanced_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate difficulty assessments for questions
        
        Args:
            enhanced_results: Enhanced classification results
            
        Returns:
            List of difficulty assessments
        """
        difficulty_assessments = []
        
        for result in enhanced_results:
            if 'error' in result:
                continue
            
            # Extract difficulty information
            ontario_difficulty = result.get('ontario_classification', {}).get('difficulty_level', 'intermediate')
            us_difficulty = result.get('us_classification', {}).get('difficulty_level', 'intermediate')
            
            # Map to difficulty levels
            ontario_level = DifficultyLevel(ontario_difficulty)
            us_level = DifficultyLevel(us_difficulty)
            
            # Calculate average difficulty
            avg_difficulty = (self.difficulty_system.difficulty_weights[ontario_level] + 
                            self.difficulty_system.difficulty_weights[us_level]) / 2
            
            assessment = {
                "question_id": result.get('original_question_id'),
                "ontario_difficulty": ontario_difficulty,
                "us_difficulty": us_difficulty,
                "average_difficulty": avg_difficulty,
                "difficulty_variance": abs(self.difficulty_system.difficulty_weights[ontario_level] - 
                                         self.difficulty_system.difficulty_weights[us_level]),
                "recommended_difficulty": self._recommend_difficulty(ontario_level, us_level),
                "prerequisites": result.get('prerequisites', []),
                "learning_objectives": result.get('learning_objectives', [])
            }
            
            difficulty_assessments.append(assessment)
        
        return difficulty_assessments
    
    def _recommend_difficulty(self, ontario_level: DifficultyLevel, us_level: DifficultyLevel) -> str:
        """
        Recommend appropriate difficulty level
        
        Args:
            ontario_level: Ontario difficulty level
            us_level: US difficulty level
            
        Returns:
            Recommended difficulty level
        """
        ontario_weight = self.difficulty_system.difficulty_weights[ontario_level]
        us_weight = self.difficulty_system.difficulty_weights[us_level]
        
        avg_weight = (ontario_weight + us_weight) / 2
        
        if avg_weight >= 0.7:
            return "expert"
        elif avg_weight >= 0.5:
            return "advanced"
        elif avg_weight >= 0.3:
            return "intermediate"
        else:
            return "beginner"
    
    def _generate_adaptive_recommendations(self, enhanced_results: List[Dict[str, Any]], 
                                         difficulty_assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate adaptive learning recommendations
        
        Args:
            enhanced_results: Enhanced classification results
            difficulty_assessments: Difficulty assessments
            
        Returns:
            List of adaptive recommendations
        """
        recommendations = []
        
        # Group questions by curriculum and difficulty
        curriculum_groups = {}
        
        for i, result in enumerate(enhanced_results):
            if 'error' in result:
                continue
            
            ontario_class = result.get('ontario_classification', {})
            us_class = result.get('us_classification', {})
            difficulty = difficulty_assessments[i] if i < len(difficulty_assessments) else {}
            
            # Ontario recommendations
            if ontario_class:
                ontario_key = f"Ontario_{ontario_class.get('grade', '')}_{ontario_class.get('subject', '')}"
                if ontario_key not in curriculum_groups:
                    curriculum_groups[ontario_key] = []
                
                curriculum_groups[ontario_key].append({
                    "question_id": result.get('original_question_id'),
                    "topic": ontario_class.get('topic', ''),
                    "difficulty": difficulty.get('ontario_difficulty', 'intermediate'),
                    "confidence": ontario_class.get('confidence', 0.5),
                    "learning_objectives": result.get('learning_objectives', [])
                })
            
            # US recommendations
            if us_class:
                us_key = f"US_{us_class.get('grade', '')}_{us_class.get('subject', '')}"
                if us_key not in curriculum_groups:
                    curriculum_groups[us_key] = []
                
                curriculum_groups[us_key].append({
                    "question_id": result.get('original_question_id'),
                    "topic": us_class.get('topic', ''),
                    "difficulty": difficulty.get('us_difficulty', 'intermediate'),
                    "confidence": us_class.get('confidence', 0.5),
                    "learning_objectives": result.get('learning_objectives', [])
                })
        
        # Generate recommendations for each curriculum group
        for curriculum_key, questions in curriculum_groups.items():
            recommendation = {
                "curriculum": curriculum_key,
                "total_questions": len(questions),
                "difficulty_distribution": self._calculate_difficulty_distribution(questions),
                "topic_coverage": self._calculate_topic_coverage(questions),
                "learning_progression": self._generate_learning_progression(questions),
                "recommended_sequence": self._recommend_question_sequence(questions)
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_difficulty_distribution(self, questions: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate difficulty distribution for a set of questions
        
        Args:
            questions: List of questions
            
        Returns:
            Difficulty distribution
        """
        distribution = {"beginner": 0, "intermediate": 0, "advanced": 0, "expert": 0}
        
        for question in questions:
            difficulty = question.get('difficulty', 'intermediate')
            if difficulty in distribution:
                distribution[difficulty] += 1
        
        return distribution
    
    def _calculate_topic_coverage(self, questions: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate topic coverage for a set of questions
        
        Args:
            questions: List of questions
            
        Returns:
            Topic coverage
        """
        topic_coverage = {}
        
        for question in questions:
            topic = question.get('topic', 'Unknown')
            topic_coverage[topic] = topic_coverage.get(topic, 0) + 1
        
        return topic_coverage
    
    def _generate_learning_progression(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate learning progression for questions
        
        Args:
            questions: List of questions
            
        Returns:
            Learning progression
        """
        # Sort questions by difficulty
        difficulty_order = ["beginner", "intermediate", "advanced", "expert"]
        sorted_questions = sorted(questions, key=lambda x: difficulty_order.index(x.get('difficulty', 'intermediate')))
        
        progression = []
        for i, question in enumerate(sorted_questions):
            progression.append({
                "step": i + 1,
                "question_id": question['question_id'],
                "topic": question['topic'],
                "difficulty": question['difficulty'],
                "confidence": question['confidence'],
                "learning_objectives": question['learning_objectives']
            })
        
        return progression
    
    def _recommend_question_sequence(self, questions: List[Dict[str, Any]]) -> List[str]:
        """
        Recommend optimal question sequence
        
        Args:
            questions: List of questions
            
        Returns:
            Recommended question sequence
        """
        # Sort by confidence and difficulty
        sorted_questions = sorted(questions, key=lambda x: (x.get('confidence', 0), x.get('difficulty', 'intermediate')), reverse=True)
        
        return [q['question_id'] for q in sorted_questions]
    
    def _generate_comprehensive_report(self, enhanced_results: List[Dict[str, Any]], 
                                     difficulty_assessments: List[Dict[str, Any]], 
                                     adaptive_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive system report
        
        Args:
            enhanced_results: Enhanced classification results
            difficulty_assessments: Difficulty assessments
            adaptive_recommendations: Adaptive recommendations
            
        Returns:
            Comprehensive report
        """
        # Calculate statistics
        total_questions = len(enhanced_results)
        successful_classifications = len([r for r in enhanced_results if 'error' not in r])
        
        # Curriculum distribution
        ontario_distribution = {}
        us_distribution = {}
        
        for result in enhanced_results:
            if 'error' not in result:
                ontario_class = result.get('ontario_classification', {})
                us_class = result.get('us_classification', {})
                
                if ontario_class:
                    key = f"{ontario_class.get('grade', '')}_{ontario_class.get('subject', '')}"
                    ontario_distribution[key] = ontario_distribution.get(key, 0) + 1
                
                if us_class:
                    key = f"{us_class.get('grade', '')}_{us_class.get('subject', '')}"
                    us_distribution[key] = us_distribution.get(key, 0) + 1
        
        # Quality metrics
        high_confidence_ontario = len([r for r in enhanced_results 
                                     if r.get('ontario_classification', {}).get('confidence', 0) >= 0.8])
        high_confidence_us = len([r for r in enhanced_results 
                                if r.get('us_classification', {}).get('confidence', 0) >= 0.8])
        
        report = {
            "system_overview": {
                "total_questions_processed": total_questions,
                "successful_classifications": successful_classifications,
                "success_rate": successful_classifications / total_questions if total_questions > 0 else 0,
                "processing_date": datetime.now().isoformat()
            },
            "curriculum_distribution": {
                "ontario": ontario_distribution,
                "us": us_distribution
            },
            "quality_metrics": {
                "high_confidence_ontario": high_confidence_ontario,
                "high_confidence_us": high_confidence_us,
                "average_confidence_ontario": self._calculate_average_confidence(enhanced_results, 'ontario'),
                "average_confidence_us": self._calculate_average_confidence(enhanced_results, 'us')
            },
            "difficulty_analysis": {
                "total_difficulty_assessments": len(difficulty_assessments),
                "difficulty_distribution": self._calculate_overall_difficulty_distribution(difficulty_assessments)
            },
            "adaptive_learning": {
                "curriculum_groups": len(adaptive_recommendations),
                "total_learning_progressions": sum(len(rec.get('learning_progression', [])) for rec in adaptive_recommendations)
            },
            "recommendations": self._generate_system_recommendations(enhanced_results, difficulty_assessments)
        }
        
        return report
    
    def _calculate_average_confidence(self, results: List[Dict[str, Any]], curriculum: str) -> float:
        """
        Calculate average confidence for a curriculum
        
        Args:
            results: Classification results
            curriculum: 'ontario' or 'us'
            
        Returns:
            Average confidence
        """
        confidences = []
        for result in results:
            if 'error' not in result:
                confidence = result.get(f'{curriculum}_classification', {}).get('confidence', 0)
                if confidence > 0:
                    confidences.append(confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _calculate_overall_difficulty_distribution(self, difficulty_assessments: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate overall difficulty distribution
        
        Args:
            difficulty_assessments: Difficulty assessments
            
        Returns:
            Overall difficulty distribution
        """
        distribution = {"beginner": 0, "intermediate": 0, "advanced": 0, "expert": 0}
        
        for assessment in difficulty_assessments:
            recommended = assessment.get('recommended_difficulty', 'intermediate')
            if recommended in distribution:
                distribution[recommended] += 1
        
        return distribution
    
    def _generate_system_recommendations(self, enhanced_results: List[Dict[str, Any]], 
                                       difficulty_assessments: List[Dict[str, Any]]) -> List[str]:
        """
        Generate system-level recommendations
        
        Args:
            enhanced_results: Enhanced classification results
            difficulty_assessments: Difficulty assessments
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Analyze success rate
        total_questions = len(enhanced_results)
        successful_classifications = len([r for r in enhanced_results if 'error' not in r])
        success_rate = successful_classifications / total_questions if total_questions > 0 else 0
        
        if success_rate < 0.9:
            recommendations.append(f"Classification success rate is {success_rate:.2%}. Consider improving prompt quality or data preprocessing.")
        
        # Analyze confidence scores
        ontario_avg_confidence = self._calculate_average_confidence(enhanced_results, 'ontario')
        us_avg_confidence = self._calculate_average_confidence(enhanced_results, 'us')
        
        if ontario_avg_confidence < 0.8:
            recommendations.append("Ontario classification confidence is below 0.8. Consider manual review of low-confidence classifications.")
        
        if us_avg_confidence < 0.8:
            recommendations.append("US classification confidence is below 0.8. Consider manual review of low-confidence classifications.")
        
        # Analyze difficulty distribution
        difficulty_dist = self._calculate_overall_difficulty_distribution(difficulty_assessments)
        total_difficulties = sum(difficulty_dist.values())
        
        if total_difficulties > 0:
            expert_ratio = difficulty_dist['expert'] / total_difficulties
            beginner_ratio = difficulty_dist['beginner'] / total_difficulties
            
            if expert_ratio > 0.4:
                recommendations.append("High proportion of expert-level questions. Consider adding more beginner and intermediate questions.")
            
            if beginner_ratio > 0.6:
                recommendations.append("High proportion of beginner-level questions. Consider adding more advanced questions for challenge.")
        
        return recommendations

async def main():
    """
    Main function to demonstrate the integrated system
    """
    # Load OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return
    
    # Initialize integrated system
    system = IntegratedCurriculumSystem(openai_api_key)
    
    # Load sample questions
    questions_file = 'enhanced_migrated_data/enhanced_dreamseed_questions.json'
    
    if not os.path.exists(questions_file):
        logger.error(f"Questions file not found: {questions_file}")
        return
    
    logger.info("Loading questions data...")
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    # Process questions
    sample_size = 30  # Process 30 questions for demonstration
    results = await system.process_questions_complete(questions_data, sample_size)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with open(f'integrated_curriculum_results_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # Print summary
    report = results['comprehensive_report']
    print("\n" + "="*80)
    print("INTEGRATED CURRICULUM SYSTEM RESULTS")
    print("="*80)
    print(f"Total Questions Processed: {report['system_overview']['total_questions_processed']}")
    print(f"Successful Classifications: {report['system_overview']['successful_classifications']}")
    print(f"Success Rate: {report['system_overview']['success_rate']:.2%}")
    
    print(f"\nQuality Metrics:")
    print(f"  Ontario Average Confidence: {report['quality_metrics']['average_confidence_ontario']:.2f}")
    print(f"  US Average Confidence: {report['quality_metrics']['average_confidence_us']:.2f}")
    print(f"  High Confidence Ontario: {report['quality_metrics']['high_confidence_ontario']}")
    print(f"  High Confidence US: {report['quality_metrics']['high_confidence_us']}")
    
    print(f"\nCurriculum Distribution:")
    print(f"  Ontario: {report['curriculum_distribution']['ontario']}")
    print(f"  US: {report['curriculum_distribution']['us']}")
    
    print(f"\nDifficulty Analysis:")
    print(f"  Distribution: {report['difficulty_analysis']['difficulty_distribution']}")
    
    print(f"\nAdaptive Learning:")
    print(f"  Curriculum Groups: {report['adaptive_learning']['curriculum_groups']}")
    print(f"  Learning Progressions: {report['adaptive_learning']['total_learning_progressions']}")
    
    print(f"\nSystem Recommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
    
    print(f"\nResults saved to: integrated_curriculum_results_{timestamp}.json")

if __name__ == '__main__':
    asyncio.run(main())
