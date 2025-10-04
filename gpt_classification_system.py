#!/usr/bin/env python3
"""
GPT-4.1 Mini Classification System
Advanced question classification using GPT-4.1 mini with enhanced curriculum standards
"""

import json
import os
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import openai
from datetime import datetime
import logging
from enhanced_curriculum_standards import EnhancedCurriculumStandards

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GPTClassificationSystem:
    """
    Advanced GPT-4.1 mini based classification system
    """
    
    def __init__(self, openai_api_key: str):
        """
        Initialize the classification system
        
        Args:
            openai_api_key: OpenAI API key for GPT-4.1 mini
        """
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.curriculum_standards = EnhancedCurriculumStandards()
        self.classification_cache = {}
        self.rate_limit_delay = 1.0  # Delay between API calls
        
    def create_enhanced_classification_prompt(self, question_data: Dict[str, Any]) -> str:
        """
        Create an enhanced prompt for GPT classification
        
        Args:
            question_data: Question data including all content
            
        Returns:
            Formatted prompt for GPT-4.1 mini
        """
        # Get curriculum standards as context
        curriculum_context = self._get_curriculum_context()
        
        # Extract question content
        title = question_data.get('title', '')
        content_en = question_data.get('content', {}).get('question', {}).get('en', '')
        answer_en = question_data.get('content', {}).get('answer', {}).get('en', '')
        solution_en = question_data.get('content', {}).get('solution', {}).get('en', '')
        hints_en = question_data.get('content', {}).get('hints', [])
        
        # Combine hints into a single string
        hints_text = ' '.join([hint.get('en', '') for hint in hints_en if isinstance(hint, dict)])
        
        # Get current metadata
        current_subject = question_data.get('metadata', {}).get('subject', '')
        current_grade = question_data.get('metadata', {}).get('grade_level', '')
        current_difficulty = question_data.get('metadata', {}).get('difficulty', {}).get('level', '')
        
        prompt = f"""
You are an expert educational content classifier specializing in Ontario and US high school curriculum standards. Your task is to accurately classify questions according to official curriculum documents.

CURRICULUM STANDARDS CONTEXT:
{curriculum_context}

QUESTION TO CLASSIFY:
Title: {title}
Content: {content_en}
Answer: {answer_en}
Solution: {solution_en}
Hints: {hints_text}
Current Subject: {current_subject}
Current Grade: {current_grade}
Current Difficulty: {current_difficulty}

CLASSIFICATION INSTRUCTIONS:
1. Carefully analyze the mathematical/scientific concepts being tested
2. Consider the complexity and prerequisites required
3. Match to the most appropriate curriculum standard for both Ontario and US
4. Provide high confidence scores (0.8+) for clear matches, lower scores for ambiguous cases
5. Consider grade-level appropriateness and cognitive development
6. Account for cross-curricular connections where applicable

RESPONSE FORMAT (JSON only, no additional text):
{{
    "ontario_classification": {{
        "grade": "Grade_9|Grade_10|Grade_11|Grade_12",
        "subject": "Mathematics|Physics",
        "course": "exact course name from standards",
        "topic": "exact topic name from standards",
        "subtopic": "most relevant subtopic",
        "confidence": 0.95,
        "difficulty_level": "beginner|intermediate|advanced|expert",
        "reasoning": "brief explanation of why this classification was chosen"
    }},
    "us_classification": {{
        "grade": "Grade_9|Grade_10|Grade_11|Grade_12",
        "subject": "Mathematics|Physics",
        "course": "exact course name from standards",
        "topic": "exact topic name from standards", 
        "subtopic": "most relevant subtopic",
        "confidence": 0.95,
        "difficulty_level": "beginner|intermediate|advanced|expert",
        "reasoning": "brief explanation of why this classification was chosen"
    }},
    "cross_curriculum_analysis": {{
        "concept_overlap": "description of how concepts overlap between curricula",
        "difficulty_comparison": "comparison of difficulty levels between Ontario and US",
        "prerequisite_skills": ["list of prerequisite skills needed"],
        "learning_objectives": ["list of learning objectives this question addresses"]
    }},
    "quality_assessment": {{
        "content_quality": "high|medium|low",
        "pedagogical_value": "high|medium|low", 
        "clarity": "high|medium|low",
        "accuracy": "high|medium|low",
        "suggestions": "any suggestions for improvement"
    }},
    "metadata": {{
        "classification_date": "{datetime.now().isoformat()}",
        "model_version": "gpt-4o-mini",
        "processing_time": "will be filled by system"
    }}
}}

Classify this question now:
"""
        return prompt
    
    def _get_curriculum_context(self) -> str:
        """
        Get relevant curriculum context for the prompt
        
        Returns:
            Formatted curriculum context string
        """
        # Get key topics from both curricula
        ontario_topics = self.curriculum_standards.get_grade_topics('Ontario', 'Mathematics', 'Grade_12')
        us_topics = self.curriculum_standards.get_grade_topics('US', 'Mathematics', 'Grade_12')
        
        context = "ONTARIO CURRICULUM HIGHLIGHTS:\n"
        for topic in ontario_topics[:5]:  # Limit to first 5 topics
            context += f"- {topic['grade']} {topic['course']}: {topic['name']}\n"
            context += f"  Subtopics: {', '.join(topic['subtopics'][:3])}\n"
        
        context += "\nUS CURRICULUM HIGHLIGHTS:\n"
        for topic in us_topics[:5]:  # Limit to first 5 topics
            context += f"- {topic['grade']} {topic['course']}: {topic['name']}\n"
            context += f"  Subtopics: {', '.join(topic['subtopics'][:3])}\n"
        
        return context
    
    async def classify_question_async(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a single question asynchronously
        
        Args:
            question_data: Question data to classify
            
        Returns:
            Classification results
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(question_data)
            if cache_key in self.classification_cache:
                logger.info(f"Using cached classification for question {question_data.get('id', 'unknown')}")
                return self.classification_cache[cache_key]
            
            prompt = self.create_enhanced_classification_prompt(question_data)
            
            # Make API call
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert educational content classifier. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            
            # Clean up response (remove any markdown formatting)
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            result = json.loads(result_text)
            
            # Add processing time
            processing_time = time.time() - start_time
            result['metadata']['processing_time'] = processing_time
            
            # Cache the result
            self.classification_cache[cache_key] = result
            
            logger.info(f"Successfully classified question {question_data.get('id', 'unknown')} in {processing_time:.2f}s")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for question {question_data.get('id', 'unknown')}: {e}")
            return self._create_error_result(str(e), time.time() - start_time)
        except Exception as e:
            logger.error(f"Error classifying question {question_data.get('id', 'unknown')}: {e}")
            return self._create_error_result(str(e), time.time() - start_time)
    
    def classify_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for question classification
        
        Args:
            question_data: Question data to classify
            
        Returns:
            Classification results
        """
        return asyncio.run(self.classify_question_async(question_data))
    
    async def classify_questions_batch_async(self, questions_data: List[Dict[str, Any]], 
                                           batch_size: int = 10, 
                                           delay: float = 1.0) -> List[Dict[str, Any]]:
        """
        Classify multiple questions in batches asynchronously
        
        Args:
            questions_data: List of question data to classify
            batch_size: Number of questions to process in each batch
            delay: Delay between batches in seconds
            
        Returns:
            List of classification results
        """
        total_questions = len(questions_data)
        results = []
        
        logger.info(f"Starting batch classification of {total_questions} questions")
        
        for i in range(0, total_questions, batch_size):
            batch = questions_data[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_questions + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} questions)")
            
            # Process batch concurrently
            batch_tasks = [self.classify_question_async(question) for question in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error in batch {batch_num}, question {j}: {result}")
                    result = self._create_error_result(str(result), 0)
                
                result['original_question_id'] = batch[j].get('id')
                results.append(result)
            
            # Save intermediate results
            if batch_num % 5 == 0:
                await self._save_intermediate_results_async(results, batch_num)
            
            # Delay between batches
            if i + batch_size < total_questions:
                await asyncio.sleep(delay)
        
        logger.info(f"Completed classification of {total_questions} questions")
        return results
    
    def classify_questions_batch(self, questions_data: List[Dict[str, Any]], 
                               batch_size: int = 10, delay: float = 1.0) -> List[Dict[str, Any]]:
        """
        Synchronous wrapper for batch classification
        
        Args:
            questions_data: List of question data to classify
            batch_size: Number of questions to process in each batch
            delay: Delay between batches in seconds
            
        Returns:
            List of classification results
        """
        return asyncio.run(self.classify_questions_batch_async(questions_data, batch_size, delay))
    
    def _generate_cache_key(self, question_data: Dict[str, Any]) -> str:
        """
        Generate a cache key for a question
        
        Args:
            question_data: Question data
            
        Returns:
            Cache key string
        """
        title = question_data.get('title', '')
        content = question_data.get('content', {}).get('question', {}).get('en', '')
        return f"{hash(title + content)}"
    
    def _create_error_result(self, error_message: str, processing_time: float) -> Dict[str, Any]:
        """
        Create an error result structure
        
        Args:
            error_message: Error message
            processing_time: Processing time in seconds
            
        Returns:
            Error result dictionary
        """
        return {
            "error": error_message,
            "ontario_classification": None,
            "us_classification": None,
            "cross_curriculum_analysis": None,
            "quality_assessment": None,
            "metadata": {
                "classification_date": datetime.now().isoformat(),
                "model_version": "gpt-4o-mini",
                "processing_time": processing_time,
                "status": "error"
            }
        }
    
    async def _save_intermediate_results_async(self, results: List[Dict[str, Any]], batch_num: int):
        """Save intermediate results to avoid data loss"""
        filename = f"gpt_classification_results_batch_{batch_num}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved intermediate results to {filename}")
    
    def validate_classification_quality(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate the quality of classification results
        
        Args:
            results: List of classification results
            
        Returns:
            Quality validation report
        """
        total_questions = len(results)
        successful_classifications = len([r for r in results if 'error' not in r])
        failed_classifications = total_questions - successful_classifications
        
        # Analyze confidence scores
        ontario_confidences = []
        us_confidences = []
        
        for result in results:
            if 'error' not in result:
                if result.get('ontario_classification', {}).get('confidence'):
                    ontario_confidences.append(result['ontario_classification']['confidence'])
                if result.get('us_classification', {}).get('confidence'):
                    us_confidences.append(result['us_classification']['confidence'])
        
        # Analyze difficulty distributions
        ontario_difficulties = {}
        us_difficulties = {}
        
        for result in results:
            if 'error' not in result:
                ontario_diff = result.get('ontario_classification', {}).get('difficulty_level')
                us_diff = result.get('us_classification', {}).get('difficulty_level')
                
                if ontario_diff:
                    ontario_difficulties[ontario_diff] = ontario_difficulties.get(ontario_diff, 0) + 1
                if us_diff:
                    us_difficulties[us_diff] = us_difficulties.get(us_diff, 0) + 1
        
        # Analyze quality assessments
        quality_scores = {'content_quality': {}, 'pedagogical_value': {}, 'clarity': {}, 'accuracy': {}}
        
        for result in results:
            if 'error' not in result and 'quality_assessment' in result:
                qa = result['quality_assessment']
                for metric in quality_scores.keys():
                    if metric in qa:
                        value = qa[metric]
                        quality_scores[metric][value] = quality_scores[metric].get(value, 0) + 1
        
        validation_report = {
            "summary": {
                "total_questions": total_questions,
                "successful_classifications": successful_classifications,
                "failed_classifications": failed_classifications,
                "success_rate": successful_classifications / total_questions if total_questions > 0 else 0
            },
            "confidence_analysis": {
                "ontario_avg_confidence": sum(ontario_confidences) / len(ontario_confidences) if ontario_confidences else 0,
                "us_avg_confidence": sum(us_confidences) / len(us_confidences) if us_confidences else 0,
                "high_confidence_ontario": len([c for c in ontario_confidences if c >= 0.8]),
                "high_confidence_us": len([c for c in us_confidences if c >= 0.8])
            },
            "difficulty_distribution": {
                "ontario": ontario_difficulties,
                "us": us_difficulties
            },
            "quality_assessment": quality_scores,
            "recommendations": self._generate_quality_recommendations(results, ontario_confidences, us_confidences)
        }
        
        return validation_report
    
    def _generate_quality_recommendations(self, results: List[Dict[str, Any]], 
                                        ontario_confidences: List[float], 
                                        us_confidences: List[float]) -> List[str]:
        """
        Generate quality improvement recommendations
        
        Args:
            results: Classification results
            ontario_confidences: List of Ontario confidence scores
            us_confidences: List of US confidence scores
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Confidence-based recommendations
        if ontario_confidences:
            avg_ontario_confidence = sum(ontario_confidences) / len(ontario_confidences)
            if avg_ontario_confidence < 0.8:
                recommendations.append("Ontario classification confidence is below 0.8. Consider manual review of low-confidence classifications.")
        
        if us_confidences:
            avg_us_confidence = sum(us_confidences) / len(us_confidences)
            if avg_us_confidence < 0.8:
                recommendations.append("US classification confidence is below 0.8. Consider manual review of low-confidence classifications.")
        
        # Error-based recommendations
        error_count = len([r for r in results if 'error' in r])
        if error_count > len(results) * 0.1:  # More than 10% errors
            recommendations.append(f"High error rate ({error_count} errors). Check API connectivity and prompt quality.")
        
        # Quality assessment recommendations
        low_quality_count = 0
        for result in results:
            if 'error' not in result and 'quality_assessment' in result:
                qa = result['quality_assessment']
                if any(qa.get(metric, 'high') == 'low' for metric in ['content_quality', 'pedagogical_value', 'clarity', 'accuracy']):
                    low_quality_count += 1
        
        if low_quality_count > len(results) * 0.2:  # More than 20% low quality
            recommendations.append(f"Many questions rated as low quality ({low_quality_count}). Consider content review and improvement.")
        
        return recommendations

def main():
    """
    Main function to demonstrate the GPT classification system
    """
    # Load sample questions
    questions_file = 'enhanced_migrated_data/enhanced_dreamseed_questions.json'
    
    if not os.path.exists(questions_file):
        logger.error(f"Questions file not found: {questions_file}")
        return
    
    # Load OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return
    
    # Initialize classification system
    classifier = GPTClassificationSystem(openai_api_key)
    
    # Load questions data
    logger.info("Loading questions data...")
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    # Take a sample for testing (first 20 questions)
    sample_size = min(20, len(questions_data))
    sample_questions = questions_data[:sample_size]
    
    logger.info(f"Classifying {sample_size} questions...")
    
    # Classify questions
    results = classifier.classify_questions_batch(sample_questions, batch_size=5, delay=2.0)
    
    # Validate results
    validation_report = classifier.validate_classification_quality(results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    with open(f'gpt_classification_results_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    with open(f'gpt_validation_report_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("GPT CLASSIFICATION SYSTEM RESULTS")
    print("="*60)
    print(f"Total Questions Processed: {validation_report['summary']['total_questions']}")
    print(f"Successful Classifications: {validation_report['summary']['successful_classifications']}")
    print(f"Success Rate: {validation_report['summary']['success_rate']:.2%}")
    
    print(f"\nConfidence Analysis:")
    print(f"  Ontario Average Confidence: {validation_report['confidence_analysis']['ontario_avg_confidence']:.2f}")
    print(f"  US Average Confidence: {validation_report['confidence_analysis']['us_avg_confidence']:.2f}")
    print(f"  High Confidence Ontario: {validation_report['confidence_analysis']['high_confidence_ontario']}")
    print(f"  High Confidence US: {validation_report['confidence_analysis']['high_confidence_us']}")
    
    print(f"\nRecommendations:")
    for rec in validation_report['recommendations']:
        print(f"  - {rec}")
    
    print(f"\nResults saved to:")
    print(f"  - gpt_classification_results_{timestamp}.json")
    print(f"  - gpt_validation_report_{timestamp}.json")

if __name__ == '__main__':
    main()
