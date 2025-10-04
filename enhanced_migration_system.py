#!/usr/bin/env python3
"""
Enhanced DreamSeedAI Migration System
Complete data transformation with proper schema mapping, MathLive integration,
adaptive learning metadata, and multilingual support
"""

import re
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from line_based_parser import parse_mysql_dump_line_by_line
from mathml_converter import convert_mathml_in_text

@dataclass
class QuestionRecord:
    """Structured representation of a question record"""
    id: int
    user_id: int
    subject_code: str
    grade_id: int
    level_id: int
    category_id: int
    grade_code: str
    question_number: int
    question_title: str
    question_content: str
    answer_content: str
    solution_content: str
    hint_content: str
    explanation_content: str
    difficulty_level: int
    topic_tags: str
    created_at: str
    updated_at: str
    status: str

class EnhancedDreamSeedAIMigrator:
    """
    Enhanced migration system with proper schema mapping and advanced features
    """
    
    def __init__(self):
        self.converted_questions = []
        self.conversion_stats = {
            'total_questions': 0,
            'math_questions': 0,
            'physics_questions': 0,
            'chemistry_questions': 0,
            'biology_questions': 0,
            'mathml_conversions': 0,
            'translation_ready': 0,
            'adaptive_learning_ready': 0,
            'errors': 0
        }
        
        # Enhanced subject mapping with proper categorization
        self.subject_mapping = {
            'M': {
                'subject': 'mathematics',
                'category': 'STEM',
                'subjects': ['algebra', 'geometry', 'calculus', 'statistics', 'trigonometry']
            },
            'P': {
                'subject': 'physics',
                'category': 'STEM', 
                'subjects': ['mechanics', 'thermodynamics', 'electromagnetism', 'optics', 'quantum']
            },
            'C': {
                'subject': 'chemistry',
                'category': 'STEM',
                'subjects': ['organic', 'inorganic', 'physical', 'analytical', 'biochemistry']
            },
            'B': {
                'subject': 'biology',
                'category': 'STEM',
                'subjects': ['cell_biology', 'genetics', 'ecology', 'anatomy', 'physiology']
            }
        }
        
        # Enhanced grade level mapping with DreamSeedAI standards
        self.grade_mapping = {
            'G06': {'grade': 6, 'level': 'middle_school', 'dreamseed_code': 'G6'},
            'G07': {'grade': 7, 'level': 'middle_school', 'dreamseed_code': 'G7'},
            'G08': {'grade': 8, 'level': 'middle_school', 'dreamseed_code': 'G8'},
            'G09': {'grade': 9, 'level': 'high_school', 'dreamseed_code': 'G9'},
            'G10': {'grade': 10, 'level': 'high_school', 'dreamseed_code': 'G10'},
            'G11': {'grade': 11, 'level': 'high_school', 'dreamseed_code': 'G11'},
            'G12': {'grade': 12, 'level': 'high_school', 'dreamseed_code': 'G12'},
            'SAT': {'grade': 12, 'level': 'standardized_test', 'dreamseed_code': 'SAT'},
            'APP': {'grade': 12, 'level': 'advanced_placement', 'dreamseed_code': 'AP'},
            'U01': {'grade': 13, 'level': 'university', 'dreamseed_code': 'UNI'}
        }
        
        # Enhanced difficulty mapping with adaptive learning support
        self.difficulty_mapping = {
            0: {'level': 'beginner', 'score': 1, 'adaptive_factor': 0.8},
            1: {'level': 'beginner', 'score': 2, 'adaptive_factor': 0.9},
            2: {'level': 'intermediate', 'score': 3, 'adaptive_factor': 1.0},
            3: {'level': 'intermediate', 'score': 4, 'adaptive_factor': 1.1},
            4: {'level': 'advanced', 'score': 5, 'adaptive_factor': 1.2},
            5: {'level': 'advanced', 'score': 6, 'adaptive_factor': 1.3},
            6: {'level': 'expert', 'score': 7, 'adaptive_factor': 1.4},
            7: {'level': 'expert', 'score': 8, 'adaptive_factor': 1.5}
        }
        
        # Topic extraction patterns for adaptive learning
        self.topic_patterns = {
            'mathematics': {
                'algebra': ['equation', 'solve', 'variable', 'polynomial', 'factor', 'quadratic', 'linear'],
                'geometry': ['triangle', 'circle', 'angle', 'area', 'perimeter', 'volume', 'coordinate'],
                'calculus': ['derivative', 'integral', 'limit', 'function', 'differentiation', 'integration'],
                'trigonometry': ['sin', 'cos', 'tan', 'angle', 'triangle', 'trigonometric'],
                'statistics': ['mean', 'median', 'mode', 'probability', 'distribution', 'standard deviation'],
                'number_theory': ['prime', 'factor', 'gcd', 'lcm', 'divisibility', 'modular']
            },
            'physics': {
                'mechanics': ['force', 'motion', 'velocity', 'acceleration', 'momentum', 'energy', 'work'],
                'thermodynamics': ['temperature', 'heat', 'energy', 'entropy', 'gas', 'pressure'],
                'electromagnetism': ['electric', 'magnetic', 'field', 'charge', 'current', 'voltage'],
                'optics': ['light', 'wave', 'reflection', 'refraction', 'lens', 'mirror'],
                'quantum': ['quantum', 'particle', 'wave', 'photon', 'electron', 'uncertainty']
            },
            'chemistry': {
                'organic': ['carbon', 'hydrocarbon', 'alkane', 'alkene', 'alcohol', 'ester'],
                'inorganic': ['metal', 'nonmetal', 'salt', 'oxide', 'acid', 'base'],
                'physical': ['thermodynamics', 'kinetics', 'equilibrium', 'reaction rate'],
                'analytical': ['concentration', 'molarity', 'titration', 'spectroscopy'],
                'biochemistry': ['protein', 'enzyme', 'metabolism', 'biomolecule']
            },
            'biology': {
                'cell_biology': ['cell', 'membrane', 'organelle', 'mitochondria', 'nucleus'],
                'genetics': ['gene', 'DNA', 'RNA', 'chromosome', 'mutation', 'inheritance'],
                'ecology': ['ecosystem', 'population', 'community', 'biodiversity', 'environment'],
                'anatomy': ['organ', 'tissue', 'system', 'structure', 'function'],
                'physiology': ['metabolism', 'respiration', 'circulation', 'nervous', 'endocrine']
            }
        }
    
    def migrate_dump_file(self, dump_file_path: str, output_dir: str = 'enhanced_migrated_data'):
        """
        Enhanced migration with proper schema mapping and advanced features
        """
        print("=" * 80)
        print("Enhanced DreamSeedAI Migration System")
        print("=" * 80)
        print(f"Source: {dump_file_path}")
        print(f"Output: {output_dir}")
        print(f"Started: {datetime.now()}")
        print()
        
        # Parse the dump file
        print("Step 1: Parsing MySQL dump file...")
        insert_statements = parse_mysql_dump_line_by_line(dump_file_path, 'tbl_question')
        
        if not insert_statements:
            print("❌ No INSERT statements found!")
            return
        
        print(f"✅ Found {len(insert_statements)} INSERT statements")
        
        # Process each INSERT statement
        print("\nStep 2: Converting questions with enhanced schema mapping...")
        total_processed = 0
        
        for stmt_idx, statement in enumerate(insert_statements):
            print(f"Processing INSERT {stmt_idx + 1}/{len(insert_statements)}...")
            
            for record_idx, record in enumerate(statement['records']):
                try:
                    # Parse record into structured format
                    question_record = self._parse_question_record(record)
                    if question_record:
                        # Convert to enhanced DreamSeedAI format
                        converted_question = self._convert_to_enhanced_format(question_record)
                        if converted_question:
                            self.converted_questions.append(converted_question)
                            total_processed += 1
                            
                            if total_processed % 100 == 0:
                                print(f"  Converted {total_processed} questions...")
                                
                except Exception as e:
                    print(f"  ❌ Error converting record {record_idx}: {e}")
                    self.conversion_stats['errors'] += 1
        
        print(f"\n✅ Enhanced conversion complete! Processed {total_processed} questions")
        
        # Generate enhanced output files
        print("\nStep 3: Generating enhanced output files...")
        self._generate_enhanced_output_files(output_dir)
        
        # Print enhanced statistics
        self._print_enhanced_statistics()
    
    def _parse_question_record(self, record: str) -> Optional[QuestionRecord]:
        """
        Parse record into structured QuestionRecord format
        """
        try:
            fields = self._parse_record_fields(record)
            
            if len(fields) < 19:
                return None
            
            return QuestionRecord(
                id=int(fields[0]) if fields[0].isdigit() else 0,
                user_id=int(fields[1]) if fields[1].isdigit() else 0,
                subject_code=fields[2] if len(fields) > 2 else 'M',
                grade_id=int(fields[3]) if fields[3].isdigit() else 0,
                level_id=int(fields[4]) if fields[4].isdigit() else 0,
                category_id=int(fields[5]) if fields[5].isdigit() else 0,
                grade_code=fields[6] if len(fields) > 6 else 'G10',
                question_number=int(fields[7]) if fields[7].isdigit() else 0,
                question_title=fields[8] if len(fields) > 8 else '',
                question_content=fields[9] if len(fields) > 9 else '',
                answer_content=fields[10] if len(fields) > 10 else '',
                solution_content=fields[11] if len(fields) > 11 else '',
                hint_content=fields[12] if len(fields) > 12 else '',
                explanation_content=fields[13] if len(fields) > 13 else '',
                difficulty_level=int(fields[14]) if fields[14].isdigit() else 0,
                topic_tags=fields[15] if len(fields) > 15 else '',
                created_at=fields[16] if len(fields) > 16 else '',
                updated_at=fields[17] if len(fields) > 17 else '',
                status=fields[18] if len(fields) > 18 else ''
            )
            
        except Exception as e:
            print(f"Error parsing question record: {e}")
            return None
    
    def _parse_record_fields(self, record: str) -> List[str]:
        """
        Parse record fields, handling quoted strings and escaped characters
        """
        fields = []
        current_field = ''
        in_quotes = False
        quote_char = None
        escape_next = False
        
        for char in record:
            if escape_next:
                current_field += char
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                current_field += char
                continue
            
            if char in ('"', "'"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                current_field += char
            elif char == ',' and not in_quotes:
                fields.append(current_field.strip())
                current_field = ''
            else:
                current_field += char
        
        if current_field:
            fields.append(current_field.strip())
        
        return fields
    
    def _convert_to_enhanced_format(self, question_record: QuestionRecord) -> Optional[Dict[str, Any]]:
        """
        Convert QuestionRecord to enhanced DreamSeedAI format
        """
        try:
            # Get subject information
            subject_info = self.subject_mapping.get(question_record.subject_code, 
                                                   self.subject_mapping['M'])
            
            # Get grade information
            grade_info = self.grade_mapping.get(question_record.grade_code,
                                               self.grade_mapping['G10'])
            
            # Get difficulty information
            difficulty_info = self.difficulty_mapping.get(question_record.difficulty_level,
                                                         self.difficulty_mapping[0])
            
            # Convert MathML to LaTeX
            question_content_converted = convert_mathml_in_text(question_record.question_content)
            answer_content_converted = convert_mathml_in_text(question_record.answer_content)
            solution_content_converted = convert_mathml_in_text(question_record.solution_content)
            
            # Count MathML conversions
            if any('<math' in content for content in [question_record.question_content, 
                                                     question_record.answer_content, 
                                                     question_record.solution_content]):
                self.conversion_stats['mathml_conversions'] += 1
            
            # Extract topics for adaptive learning
            topics = self._extract_enhanced_topics(question_content_converted, 
                                                  subject_info['subject'])
            
            # Determine question type
            question_type = self._determine_question_type(question_content_converted)
            
            # Create enhanced DreamSeedAI question
            enhanced_question = {
                'id': question_record.id,
                'title': self._extract_title(question_record.question_title),
                'content': {
                    'question': {
                        'en': self._clean_html_content(question_content_converted),
                        'ko': '',  # Ready for translation
                        'zh': ''   # Ready for translation
                    },
                    'answer': {
                        'en': self._clean_html_content(answer_content_converted),
                        'ko': '',  # Ready for translation
                        'zh': ''   # Ready for translation
                    },
                    'solution': {
                        'en': self._clean_html_content(solution_content_converted),
                        'ko': '',  # Ready for translation
                        'zh': ''   # Ready for translation
                    },
                    'hints': {
                        'en': [self._clean_html_content(question_record.hint_content)] if question_record.hint_content else [],
                        'ko': [],  # Ready for translation
                        'zh': []   # Ready for translation
                    },
                    'explanation': {
                        'en': self._clean_html_content(question_record.explanation_content),
                        'ko': '',  # Ready for translation
                        'zh': ''   # Ready for translation
                    }
                },
                'metadata': {
                    'subject': subject_info['subject'],
                    'category': subject_info['category'],
                    'grade_level': grade_info['grade'],
                    'grade_code': grade_info['dreamseed_code'],
                    'education_level': grade_info['level'],
                    'difficulty': {
                        'level': difficulty_info['level'],
                        'score': difficulty_info['score'],
                        'adaptive_factor': difficulty_info['adaptive_factor']
                    },
                    'topics': topics,
                    'question_type': question_type,
                    'source': 'mpcstudy.com',
                    'original_id': question_record.id,
                    'original_grade_id': question_record.grade_id,
                    'original_level_id': question_record.level_id,
                    'original_category_id': question_record.category_id
                },
                'math_content': {
                    'has_mathml': any('<math' in content for content in [
                        question_record.question_content, 
                        question_record.answer_content, 
                        question_record.solution_content
                    ]),
                    'latex_expressions': self._extract_latex_expressions(
                        question_content_converted, answer_content_converted, solution_content_converted),
                    'math_complexity': self._assess_math_complexity(
                        question_content_converted, answer_content_converted, solution_content_converted)
                },
                'adaptive_learning': {
                    'prerequisites': self._extract_prerequisites(topics, subject_info['subject']),
                    'learning_objectives': self._extract_learning_objectives(question_content_converted, topics),
                    'assessment_criteria': self._generate_assessment_criteria(question_type, difficulty_info['level']),
                    'adaptive_difficulty_range': self._calculate_adaptive_difficulty_range(difficulty_info),
                    'success_indicators': self._generate_success_indicators(question_type, topics)
                },
                'translation_status': {
                    'en': 'complete',
                    'ko': 'pending',
                    'zh': 'pending'
                },
                'quality_metrics': {
                    'content_quality_score': self._assess_content_quality(question_content_converted),
                    'math_accuracy_score': self._assess_math_accuracy(question_content_converted),
                    'pedagogical_value_score': self._assess_pedagogical_value(question_content_converted, topics),
                    'accessibility_score': self._assess_accessibility(question_content_converted)
                },
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # Update statistics
            self.conversion_stats['total_questions'] += 1
            subject = enhanced_question['metadata']['subject']
            if subject == 'mathematics':
                self.conversion_stats['math_questions'] += 1
            elif subject == 'physics':
                self.conversion_stats['physics_questions'] += 1
            elif subject == 'chemistry':
                self.conversion_stats['chemistry_questions'] += 1
            elif subject == 'biology':
                self.conversion_stats['biology_questions'] += 1
            
            # Mark as translation ready
            self.conversion_stats['translation_ready'] += 1
            self.conversion_stats['adaptive_learning_ready'] += 1
            
            return enhanced_question
            
        except Exception as e:
            print(f"Error converting question: {e}")
            return None
    
    def _extract_enhanced_topics(self, content: str, subject: str) -> List[str]:
        """
        Extract topics with enhanced pattern matching for adaptive learning
        """
        topics = []
        content_lower = content.lower()
        
        if subject in self.topic_patterns:
            for topic, keywords in self.topic_patterns[subject].items():
                if any(keyword in content_lower for keyword in keywords):
                    topics.append(topic)
        
        # If no specific topics found, add general subject
        if not topics:
            topics.append('general')
        
        return topics
    
    def _extract_prerequisites(self, topics: List[str], subject: str) -> List[str]:
        """
        Extract prerequisite knowledge based on topics
        """
        prerequisites = []
        
        # Define prerequisite mappings
        prerequisite_map = {
            'calculus': ['algebra', 'trigonometry'],
            'advanced_algebra': ['basic_algebra'],
            'organic_chemistry': ['basic_chemistry'],
            'quantum_physics': ['classical_physics', 'mathematics'],
            'genetics': ['cell_biology', 'basic_biology']
        }
        
        for topic in topics:
            if topic in prerequisite_map:
                prerequisites.extend(prerequisite_map[topic])
        
        return list(set(prerequisites))  # Remove duplicates
    
    def _extract_learning_objectives(self, content: str, topics: List[str]) -> List[str]:
        """
        Extract learning objectives from question content
        """
        objectives = []
        
        # Common learning objective patterns
        objective_patterns = [
            r'find\s+(\w+)',
            r'calculate\s+(\w+)',
            r'solve\s+(\w+)',
            r'determine\s+(\w+)',
            r'explain\s+(\w+)',
            r'prove\s+(\w+)'
        ]
        
        for pattern in objective_patterns:
            matches = re.findall(pattern, content.lower())
            for match in matches:
                objectives.append(f"Learn to {match}")
        
        return objectives[:5]  # Limit to 5 objectives
    
    def _generate_assessment_criteria(self, question_type: str, difficulty: str) -> List[str]:
        """
        Generate assessment criteria based on question type and difficulty
        """
        criteria = []
        
        if question_type == 'multiple_choice':
            criteria.extend(['Correct answer selection', 'Understanding of concepts'])
        elif question_type == 'problem_solving':
            criteria.extend(['Solution methodology', 'Correct calculations', 'Final answer accuracy'])
        elif question_type == 'proof':
            criteria.extend(['Logical reasoning', 'Mathematical rigor', 'Step-by-step justification'])
        
        if difficulty in ['advanced', 'expert']:
            criteria.append('Critical thinking skills')
        
        return criteria
    
    def _calculate_adaptive_difficulty_range(self, difficulty_info: Dict) -> Dict[str, int]:
        """
        Calculate adaptive difficulty range for personalized learning
        """
        base_score = difficulty_info['score']
        adaptive_factor = difficulty_info['adaptive_factor']
        
        return {
            'min_difficulty': max(1, int(base_score * 0.7)),
            'max_difficulty': min(10, int(base_score * 1.3)),
            'optimal_difficulty': base_score,
            'adaptive_factor': adaptive_factor
        }
    
    def _generate_success_indicators(self, question_type: str, topics: List[str]) -> List[str]:
        """
        Generate success indicators for adaptive learning
        """
        indicators = []
        
        if question_type == 'multiple_choice':
            indicators.append('Correct answer selection within time limit')
        elif question_type == 'problem_solving':
            indicators.append('Complete solution with correct methodology')
            indicators.append('Accurate final answer')
        
        indicators.extend([
            f'Demonstrates understanding of {topic}' for topic in topics[:3]
        ])
        
        return indicators
    
    def _assess_content_quality(self, content: str) -> float:
        """
        Assess content quality score (0-1)
        """
        score = 0.5  # Base score
        
        # Length check
        if len(content) > 100:
            score += 0.1
        
        # Structure check
        if any(tag in content for tag in ['<br>', '<p>', '<div>']):
            score += 0.1
        
        # Math content check
        if '$' in content or '<math' in content:
            score += 0.2
        
        # Clarity check
        if not any(word in content.lower() for word in ['error', 'undefined', 'missing']):
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_math_accuracy(self, content: str) -> float:
        """
        Assess mathematical accuracy score (0-1)
        """
        score = 0.8  # Base score for math content
        
        # Check for common math errors
        error_patterns = [
            r'undefined',
            r'error',
            r'\\text\{Error',
            r'not well-formed'
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, content):
                score -= 0.2
        
        return max(0.0, score)
    
    def _assess_pedagogical_value(self, content: str, topics: List[str]) -> float:
        """
        Assess pedagogical value score (0-1)
        """
        score = 0.6  # Base score
        
        # Topic diversity
        if len(topics) > 1:
            score += 0.1
        
        # Question complexity
        if any(word in content.lower() for word in ['explain', 'why', 'how', 'prove']):
            score += 0.2
        
        # Real-world connection
        if any(word in content.lower() for word in ['real', 'practical', 'example', 'application']):
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_accessibility(self, content: str) -> float:
        """
        Assess accessibility score (0-1)
        """
        score = 0.7  # Base score
        
        # Alt text for images (if any)
        if '<img' in content and 'alt=' in content:
            score += 0.1
        
        # Clear structure
        if any(tag in content for tag in ['<h1>', '<h2>', '<h3>', '<strong>', '<em>']):
            score += 0.1
        
        # Readable length
        if 50 < len(content) < 2000:
            score += 0.1
        
        return min(1.0, score)
    
    def _extract_title(self, title: str) -> str:
        """
        Extract clean title from question title
        """
        clean_title = re.sub(r'<[^>]+>', '', title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        if len(clean_title) > 100:
            clean_title = clean_title[:100] + "..."
        
        return clean_title
    
    def _clean_html_content(self, content: str) -> str:
        """
        Clean HTML content while preserving structure
        """
        # Convert MathML to LaTeX (already done, but ensure it's clean)
        content = convert_mathml_in_text(content)
        
        # Clean up HTML entities
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&ndash;': '–',
            '&mdash;': '—',
            '&hellip;': '…',
        }
        
        for entity, char in html_entities.items():
            content = content.replace(entity, char)
        
        # Clean up extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def _determine_question_type(self, content: str) -> str:
        """
        Determine question type based on content
        """
        text_lower = content.lower()
        
        if any(word in text_lower for word in ['choose', 'select', 'which', 'what is']):
            return 'multiple_choice'
        elif any(word in text_lower for word in ['solve', 'find', 'calculate', 'compute']):
            return 'problem_solving'
        elif any(word in text_lower for word in ['prove', 'show', 'demonstrate']):
            return 'proof'
        elif any(word in text_lower for word in ['explain', 'describe', 'why']):
            return 'explanation'
        else:
            return 'general'
    
    def _extract_latex_expressions(self, *contents: str) -> List[str]:
        """
        Extract LaTeX expressions from multiple content strings
        """
        latex_expressions = []
        
        for content in contents:
            # Find LaTeX expressions (between $ signs)
            latex_pattern = r'\$([^$]+)\$'
            matches = re.findall(latex_pattern, content)
            latex_expressions.extend(matches)
        
        return list(set(latex_expressions))  # Remove duplicates
    
    def _assess_math_complexity(self, *contents: str) -> str:
        """
        Assess mathematical complexity across multiple content strings
        """
        combined_text = ' '.join(contents).lower()
        
        # Count mathematical elements
        math_elements = [
            'frac', 'sqrt', 'sum', 'int', 'lim', 'derivative', 'integral',
            'matrix', 'vector', 'equation', 'theorem', 'proof'
        ]
        
        complexity_score = sum(1 for element in math_elements if element in combined_text)
        
        if complexity_score >= 5:
            return 'high'
        elif complexity_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_enhanced_output_files(self, output_dir: str):
        """
        Generate enhanced output files with multiple formats
        """
        import os
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate main JSON file
        json_file = os.path.join(output_dir, 'enhanced_dreamseed_questions.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.converted_questions, f, indent=2, ensure_ascii=False)
        print(f"✅ Generated enhanced JSON file: {json_file}")
        
        # Generate CSV file for analysis
        csv_file = os.path.join(output_dir, 'enhanced_dreamseed_questions.csv')
        if self.converted_questions:
            # Flatten the nested structure for CSV
            flattened_questions = []
            for q in self.converted_questions:
                flat_q = {
                    'id': q['id'],
                    'title': q['title'],
                    'subject': q['metadata']['subject'],
                    'grade_level': q['metadata']['grade_level'],
                    'difficulty_level': q['metadata']['difficulty']['level'],
                    'difficulty_score': q['metadata']['difficulty']['score'],
                    'topics': '|'.join(q['metadata']['topics']),
                    'question_type': q['metadata']['question_type'],
                    'has_mathml': q['math_content']['has_mathml'],
                    'math_complexity': q['math_content']['math_complexity'],
                    'content_quality_score': q['quality_metrics']['content_quality_score'],
                    'math_accuracy_score': q['quality_metrics']['math_accuracy_score'],
                    'pedagogical_value_score': q['quality_metrics']['pedagogical_value_score'],
                    'accessibility_score': q['quality_metrics']['accessibility_score'],
                    'translation_ready': all(q['translation_status'][lang] in ['complete', 'pending'] 
                                           for lang in ['en', 'ko', 'zh']),
                    'adaptive_learning_ready': len(q['adaptive_learning']['prerequisites']) > 0
                }
                flattened_questions.append(flat_q)
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=flattened_questions[0].keys())
                writer.writeheader()
                writer.writerows(flattened_questions)
            print(f"✅ Generated enhanced CSV file: {csv_file}")
        
        # Generate translation-ready files
        self._generate_translation_files(output_dir)
        
        # Generate adaptive learning configuration
        self._generate_adaptive_learning_config(output_dir)
        
        # Generate quality assessment report
        self._generate_quality_report(output_dir)
        
        # Generate summary report
        report_file = os.path.join(output_dir, 'enhanced_migration_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Enhanced DreamSeedAI Migration Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Migration Date: {datetime.now()}\n")
            f.write(f"Total Questions: {self.conversion_stats['total_questions']}\n")
            f.write(f"Mathematics: {self.conversion_stats['math_questions']}\n")
            f.write(f"Physics: {self.conversion_stats['physics_questions']}\n")
            f.write(f"Chemistry: {self.conversion_stats['chemistry_questions']}\n")
            f.write(f"Biology: {self.conversion_stats['biology_questions']}\n")
            f.write(f"MathML Conversions: {self.conversion_stats['mathml_conversions']}\n")
            f.write(f"Translation Ready: {self.conversion_stats['translation_ready']}\n")
            f.write(f"Adaptive Learning Ready: {self.conversion_stats['adaptive_learning_ready']}\n")
            f.write(f"Errors: {self.conversion_stats['errors']}\n")
        print(f"✅ Generated enhanced report: {report_file}")
    
    def _generate_translation_files(self, output_dir: str):
        """
        Generate files ready for translation pipeline
        """
        # English content for translation
        en_content = []
        for q in self.converted_questions:
            en_content.append({
                'id': q['id'],
                'question': q['content']['question']['en'],
                'answer': q['content']['answer']['en'],
                'solution': q['content']['solution']['en'],
                'hints': q['content']['hints']['en'],
                'explanation': q['content']['explanation']['en']
            })
        
        # Save English content for translation
        en_file = os.path.join(output_dir, 'translation_source_en.json')
        with open(en_file, 'w', encoding='utf-8') as f:
            json.dump(en_content, f, indent=2, ensure_ascii=False)
        print(f"✅ Generated translation source file: {en_file}")
    
    def _generate_adaptive_learning_config(self, output_dir: str):
        """
        Generate adaptive learning configuration
        """
        config = {
            'adaptive_learning_settings': {
                'difficulty_adjustment_factor': 0.1,
                'success_threshold': 0.8,
                'failure_threshold': 0.3,
                'max_attempts': 3,
                'prerequisite_check': True
            },
            'topic_hierarchy': self.topic_patterns,
            'difficulty_mapping': self.difficulty_mapping,
            'grade_mapping': self.grade_mapping
        }
        
        config_file = os.path.join(output_dir, 'adaptive_learning_config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Generated adaptive learning config: {config_file}")
    
    def _generate_quality_report(self, output_dir: str):
        """
        Generate quality assessment report
        """
        quality_stats = {
            'content_quality': {
                'high': sum(1 for q in self.converted_questions if q['quality_metrics']['content_quality_score'] > 0.8),
                'medium': sum(1 for q in self.converted_questions if 0.5 <= q['quality_metrics']['content_quality_score'] <= 0.8),
                'low': sum(1 for q in self.converted_questions if q['quality_metrics']['content_quality_score'] < 0.5)
            },
            'math_accuracy': {
                'high': sum(1 for q in self.converted_questions if q['quality_metrics']['math_accuracy_score'] > 0.8),
                'medium': sum(1 for q in self.converted_questions if 0.5 <= q['quality_metrics']['math_accuracy_score'] <= 0.8),
                'low': sum(1 for q in self.converted_questions if q['quality_metrics']['math_accuracy_score'] < 0.5)
            },
            'pedagogical_value': {
                'high': sum(1 for q in self.converted_questions if q['quality_metrics']['pedagogical_value_score'] > 0.8),
                'medium': sum(1 for q in self.converted_questions if 0.5 <= q['quality_metrics']['pedagogical_value_score'] <= 0.8),
                'low': sum(1 for q in self.converted_questions if q['quality_metrics']['pedagogical_value_score'] < 0.5)
            }
        }
        
        quality_file = os.path.join(output_dir, 'quality_assessment_report.json')
        with open(quality_file, 'w', encoding='utf-8') as f:
            json.dump(quality_stats, f, indent=2, ensure_ascii=False)
        print(f"✅ Generated quality assessment report: {quality_file}")
    
    def _print_enhanced_statistics(self):
        """
        Print enhanced migration statistics
        """
        print("\n" + "=" * 60)
        print("ENHANCED MIGRATION STATISTICS")
        print("=" * 60)
        print(f"Total Questions Converted: {self.conversion_stats['total_questions']}")
        print(f"  - Mathematics: {self.conversion_stats['math_questions']}")
        print(f"  - Physics: {self.conversion_stats['physics_questions']}")
        print(f"  - Chemistry: {self.conversion_stats['chemistry_questions']}")
        print(f"  - Biology: {self.conversion_stats['biology_questions']}")
        print(f"MathML Conversions: {self.conversion_stats['mathml_conversions']}")
        print(f"Translation Ready: {self.conversion_stats['translation_ready']}")
        print(f"Adaptive Learning Ready: {self.conversion_stats['adaptive_learning_ready']}")
        print(f"Errors: {self.conversion_stats['errors']}")
        print(f"Success Rate: {((self.conversion_stats['total_questions'] - self.conversion_stats['errors']) / max(1, self.conversion_stats['total_questions']) * 100):.1f}%")
        print("=" * 60)

def main():
    """
    Main function to run the enhanced migration
    """
    migrator = EnhancedDreamSeedAIMigrator()
    
    # Run enhanced migration
    dump_file_path = '/var/www/mpcstudy.com/mpcstudy_db.sql'
    output_dir = 'enhanced_migrated_data'
    
    migrator.migrate_dump_file(dump_file_path, output_dir)

if __name__ == '__main__':
    main()
