#!/usr/bin/env python3
"""
Complete Data Migration Script: mpcstudy.com → DreamSeedAI
Converts MySQL dump data to DreamSeedAI format with MathML → LaTeX conversion
"""

import re
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
from line_based_parser import parse_mysql_dump_line_by_line
from mathml_converter import convert_mathml_in_text

class DreamSeedAIMigrator:
    """
    Complete migration system from mpcstudy.com to DreamSeedAI
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
            'errors': 0
        }
        
        # Subject mapping from mpcstudy.com to DreamSeedAI
        self.subject_mapping = {
            'M': 'mathematics',
            'P': 'physics', 
            'C': 'chemistry',
            'B': 'biology'
        }
        
        # Grade level mapping
        self.grade_mapping = {
            'G06': 6, 'G07': 7, 'G08': 8, 'G09': 9, 'G10': 10, 'G11': 11, 'G12': 12,
            'SAT': 12, 'APP': 12, 'U01': 13  # University level
        }
        
        # Difficulty mapping (based on grade level and question complexity)
        self.difficulty_mapping = {
            6: 'beginner',
            7: 'beginner', 
            8: 'intermediate',
            9: 'intermediate',
            10: 'intermediate',
            11: 'advanced',
            12: 'advanced',
            13: 'expert'
        }
    
    def migrate_dump_file(self, dump_file_path: str, output_dir: str = 'migrated_data'):
        """
        Migrate entire dump file to DreamSeedAI format
        """
        print("=" * 80)
        print("DreamSeedAI Data Migration System")
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
        print("\nStep 2: Converting questions to DreamSeedAI format...")
        total_processed = 0
        
        for stmt_idx, statement in enumerate(insert_statements):
            print(f"Processing INSERT {stmt_idx + 1}/{len(insert_statements)}...")
            
            for record_idx, record in enumerate(statement['records']):
                try:
                    converted_question = self._convert_question_record(record)
                    if converted_question:
                        self.converted_questions.append(converted_question)
                        total_processed += 1
                        
                        if total_processed % 100 == 0:
                            print(f"  Converted {total_processed} questions...")
                            
                except Exception as e:
                    print(f"  ❌ Error converting record {record_idx}: {e}")
                    self.conversion_stats['errors'] += 1
        
        print(f"\n✅ Conversion complete! Processed {total_processed} questions")
        
        # Generate output files
        print("\nStep 3: Generating output files...")
        self._generate_output_files(output_dir)
        
        # Print statistics
        self._print_statistics()
    
    def _convert_question_record(self, record: str) -> Optional[Dict[str, Any]]:
        """
        Convert a single question record to DreamSeedAI format
        """
        try:
            # Parse the record fields
            fields = self._parse_record_fields(record)
            
            if len(fields) < 19:
                return None
            
            # Extract basic information
            question_id = int(fields[0]) if fields[0].isdigit() else None
            subject_code = fields[2] if len(fields) > 2 else 'M'
            grade_code = fields[6] if len(fields) > 6 else 'G10'
            question_text = fields[8] if len(fields) > 8 else ''
            answer_text = fields[9] if len(fields) > 9 else ''
            
            # Convert MathML to LaTeX in question and answer text
            question_text_converted = convert_mathml_in_text(question_text)
            answer_text_converted = convert_mathml_in_text(answer_text)
            
            # Count MathML conversions
            if '<math' in question_text or '<math' in answer_text:
                self.conversion_stats['mathml_conversions'] += 1
            
            # Map to DreamSeedAI format
            dreamseed_question = {
                'id': question_id,
                'title': self._extract_title(question_text_converted),
                'content': {
                    'question': self._clean_html_content(question_text_converted),
                    'answer': self._clean_html_content(answer_text_converted),
                    'explanation': self._extract_explanation(fields),
                    'hints': self._extract_hints(fields)
                },
                'metadata': {
                    'subject': self.subject_mapping.get(subject_code, 'mathematics'),
                    'grade_level': self.grade_mapping.get(grade_code, 10),
                    'difficulty': self._determine_difficulty(grade_code, question_text_converted),
                    'topics': self._extract_topics(question_text_converted, subject_code),
                    'question_type': self._determine_question_type(question_text_converted),
                    'source': 'mpcstudy.com',
                    'original_id': question_id
                },
                'math_content': {
                    'has_mathml': '<math' in question_text or '<math' in answer_text,
                    'latex_expressions': self._extract_latex_expressions(question_text_converted, answer_text_converted),
                    'math_complexity': self._assess_math_complexity(question_text_converted, answer_text_converted)
                },
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Update statistics
            self.conversion_stats['total_questions'] += 1
            subject = dreamseed_question['metadata']['subject']
            if subject == 'mathematics':
                self.conversion_stats['math_questions'] += 1
            elif subject == 'physics':
                self.conversion_stats['physics_questions'] += 1
            elif subject == 'chemistry':
                self.conversion_stats['chemistry_questions'] += 1
            elif subject == 'biology':
                self.conversion_stats['biology_questions'] += 1
            
            return dreamseed_question
            
        except Exception as e:
            print(f"Error converting question: {e}")
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
    
    def _extract_title(self, question_text: str) -> str:
        """
        Extract a title from question text
        """
        # Remove HTML tags and get first meaningful line
        clean_text = re.sub(r'<[^>]+>', ' ', question_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Take first 100 characters as title
        title = clean_text[:100]
        if len(clean_text) > 100:
            title += "..."
        
        return title
    
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
    
    def _extract_explanation(self, fields: List[str]) -> str:
        """
        Extract explanation from fields (if available)
        """
        # Look for explanation in additional fields
        if len(fields) > 10:
            explanation = fields[10]
            return self._clean_html_content(explanation)
        return ""
    
    def _extract_hints(self, fields: List[str]) -> List[str]:
        """
        Extract hints from fields (if available)
        """
        hints = []
        # Look for hints in additional fields
        if len(fields) > 11:
            hint_text = fields[11]
            if hint_text.strip():
                hints.append(self._clean_html_content(hint_text))
        return hints
    
    def _determine_difficulty(self, grade_code: str, question_text: str) -> str:
        """
        Determine question difficulty based on grade level and content
        """
        grade_level = self.grade_mapping.get(grade_code, 10)
        base_difficulty = self.difficulty_mapping.get(grade_level, 'intermediate')
        
        # Adjust based on content complexity
        if any(word in question_text.lower() for word in ['prove', 'derive', 'theorem', 'complex']):
            if base_difficulty == 'intermediate':
                return 'advanced'
            elif base_difficulty == 'advanced':
                return 'expert'
        
        return base_difficulty
    
    def _extract_topics(self, question_text: str, subject_code: str) -> List[str]:
        """
        Extract topics from question text
        """
        topics = []
        
        # Subject-specific topic extraction
        if subject_code == 'M':  # Mathematics
            math_topics = {
                'algebra': ['equation', 'solve', 'variable', 'polynomial', 'factor'],
                'geometry': ['triangle', 'circle', 'angle', 'area', 'perimeter', 'volume'],
                'calculus': ['derivative', 'integral', 'limit', 'function', 'differentiation'],
                'trigonometry': ['sin', 'cos', 'tan', 'angle', 'triangle'],
                'statistics': ['mean', 'median', 'mode', 'probability', 'distribution']
            }
            
            for topic, keywords in math_topics.items():
                if any(keyword in question_text.lower() for keyword in keywords):
                    topics.append(topic)
        
        elif subject_code == 'P':  # Physics
            physics_topics = {
                'mechanics': ['force', 'motion', 'velocity', 'acceleration', 'momentum'],
                'thermodynamics': ['temperature', 'heat', 'energy', 'entropy'],
                'electromagnetism': ['electric', 'magnetic', 'field', 'charge', 'current'],
                'optics': ['light', 'wave', 'reflection', 'refraction', 'lens'],
                'quantum': ['quantum', 'particle', 'wave', 'photon', 'electron']
            }
            
            for topic, keywords in physics_topics.items():
                if any(keyword in question_text.lower() for keyword in keywords):
                    topics.append(topic)
        
        # If no specific topics found, add general subject
        if not topics:
            topics.append(self.subject_mapping.get(subject_code, 'general'))
        
        return topics
    
    def _determine_question_type(self, question_text: str) -> str:
        """
        Determine question type based on content
        """
        text_lower = question_text.lower()
        
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
    
    def _extract_latex_expressions(self, question_text: str, answer_text: str) -> List[str]:
        """
        Extract LaTeX expressions from text
        """
        latex_expressions = []
        
        # Find LaTeX expressions (between $ signs)
        latex_pattern = r'\$([^$]+)\$'
        
        for text in [question_text, answer_text]:
            matches = re.findall(latex_pattern, text)
            latex_expressions.extend(matches)
        
        return list(set(latex_expressions))  # Remove duplicates
    
    def _assess_math_complexity(self, question_text: str, answer_text: str) -> str:
        """
        Assess mathematical complexity
        """
        combined_text = (question_text + ' ' + answer_text).lower()
        
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
    
    def _generate_output_files(self, output_dir: str):
        """
        Generate output files in various formats
        """
        import os
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate JSON file
        json_file = os.path.join(output_dir, 'dreamseed_questions.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.converted_questions, f, indent=2, ensure_ascii=False)
        print(f"✅ Generated JSON file: {json_file}")
        
        # Generate CSV file for analysis
        csv_file = os.path.join(output_dir, 'dreamseed_questions.csv')
        if self.converted_questions:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.converted_questions[0].keys())
                writer.writeheader()
                writer.writerows(self.converted_questions)
            print(f"✅ Generated CSV file: {csv_file}")
        
        # Generate summary report
        report_file = os.path.join(output_dir, 'migration_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("DreamSeedAI Migration Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Migration Date: {datetime.now()}\n")
            f.write(f"Total Questions: {self.conversion_stats['total_questions']}\n")
            f.write(f"Mathematics: {self.conversion_stats['math_questions']}\n")
            f.write(f"Physics: {self.conversion_stats['physics_questions']}\n")
            f.write(f"Chemistry: {self.conversion_stats['chemistry_questions']}\n")
            f.write(f"Biology: {self.conversion_stats['biology_questions']}\n")
            f.write(f"MathML Conversions: {self.conversion_stats['mathml_conversions']}\n")
            f.write(f"Errors: {self.conversion_stats['errors']}\n")
        print(f"✅ Generated report: {report_file}")
    
    def _print_statistics(self):
        """
        Print migration statistics
        """
        print("\n" + "=" * 50)
        print("MIGRATION STATISTICS")
        print("=" * 50)
        print(f"Total Questions Converted: {self.conversion_stats['total_questions']}")
        print(f"  - Mathematics: {self.conversion_stats['math_questions']}")
        print(f"  - Physics: {self.conversion_stats['physics_questions']}")
        print(f"  - Chemistry: {self.conversion_stats['chemistry_questions']}")
        print(f"  - Biology: {self.conversion_stats['biology_questions']}")
        print(f"MathML Conversions: {self.conversion_stats['mathml_conversions']}")
        print(f"Errors: {self.conversion_stats['errors']}")
        print(f"Success Rate: {((self.conversion_stats['total_questions'] - self.conversion_stats['errors']) / max(1, self.conversion_stats['total_questions']) * 100):.1f}%")
        print("=" * 50)

def main():
    """
    Main function to run the migration
    """
    migrator = DreamSeedAIMigrator()
    
    # Run migration
    dump_file_path = '/var/www/mpcstudy.com/mpcstudy_db.sql'
    output_dir = 'migrated_data'
    
    migrator.migrate_dump_file(dump_file_path, output_dir)

if __name__ == '__main__':
    main()
