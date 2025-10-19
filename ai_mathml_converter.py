#!/usr/bin/env python3
"""
AI-Powered MathML to MathLive Converter
Uses GPT-4.1 mini to intelligently convert complex MathML expressions to MathLive format
"""

import os
import json
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from ai_client import get_openai_client, get_model

@dataclass
class ConversionResult:
    original_mathml: str
    converted_latex: str
    confidence: float
    conversion_notes: str
    display_mode: bool = False
    error_message: Optional[str] = None

class AIMathMLConverter:
    """AI-powered MathML to MathLive converter using GPT-4.1 mini"""
    
    def __init__(self, api_key: Optional[str] = None):
        api = api_key or os.getenv('OPENAI_API_KEY')
        self.client = get_openai_client(api)
        self.conversion_cache = {}
        self.conversion_stats = {
            'total_processed': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0
        }
    
    def extract_mathml_from_content(self, content: str) -> List[Tuple[str, int]]:
        """Extract all MathML expressions from content with their positions"""
        mathml_patterns = [
            r'<math[^>]*>.*?</math>',
            r'<m:math[^>]*>.*?</m:math>',
            r'<math xmlns[^>]*>.*?</math>',
        ]
        
        mathml_expressions = []
        for pattern in mathml_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                mathml_expressions.append((match.group(0), match.start()))
        
        return mathml_expressions
    
    def create_conversion_prompt(self, mathml: str) -> str:
        """Create a detailed prompt for GPT to convert MathML to MathLive LaTeX"""
        return f"""
You are an expert mathematician and LaTeX specialist. Your task is to convert MathML expressions to MathLive-compatible LaTeX format.

**MathML Input:**
```xml
{mathml}
```

**Conversion Requirements:**
1. Convert to clean, valid LaTeX syntax that works with MathLive
2. Preserve mathematical meaning exactly
3. Use proper LaTeX commands and structures
4. Handle complex expressions like matrices, fractions, superscripts, subscripts
5. Ensure proper spacing and formatting
6. Use display mode (\\[ \\]) for complex expressions, inline mode (\\( \\)) for simple ones

**MathLive LaTeX Guidelines:**
- Use \\frac{{numerator}}{{denominator}} for fractions
- Use ^{{exponent}} for superscripts, _{{subscript}} for subscripts
- Use \\sum_{{i=1}}^{{n}} for summations
- Use \\int_{{a}}^{{b}} for integrals
- Use \\sqrt{{expression}} for square roots
- Use \\begin{{matrix}} ... \\end{{matrix}} for matrices
- Use \\left( and \\right) for proper parentheses sizing
- Use \\cdot for multiplication dots
- Use \\times for cross products
- Use \\pm for plus-minus
- Use \\infty for infinity
- Use \\alpha, \\beta, \\gamma, etc. for Greek letters

**Output Format:**
Provide your response as a JSON object with these fields:
{{
    "latex": "converted LaTeX expression",
    "display_mode": true/false,
    "confidence": 0.0-1.0,
    "notes": "any conversion notes or assumptions made",
    "complexity": "simple/medium/complex"
}}

**Examples:**
Input: <math><mfrac><mn>1</mn><mn>2</mn></mfrac></math>
Output: {{"latex": "\\frac{{1}}{{2}}", "display_mode": false, "confidence": 1.0, "notes": "Simple fraction", "complexity": "simple"}}

Input: <math><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><msup><mi>k</mi><mn>2</mn></msup></math>
Output: {{"latex": "\\sum_{{k=1}}^{{n}} k^2", "display_mode": true, "confidence": 1.0, "notes": "Summation with limits", "complexity": "medium"}}

Now convert the provided MathML expression:
"""

    def convert_mathml_with_ai(self, mathml: str) -> ConversionResult:
        """Convert MathML to MathLive LaTeX using GPT-4.1 mini"""
        
        # Check cache first
        if mathml in self.conversion_cache:
            return self.conversion_cache[mathml]
        
        try:
            prompt = self.create_conversion_prompt(mathml)
            
            response = self.client.chat.completions.create(
                model=get_model(),
                messages=[
                    {"role": "system", "content": "You are an expert mathematician and LaTeX specialist. Convert MathML to MathLive LaTeX format with high accuracy."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=1000
            )
            
            # Parse the JSON response
            response_text = response.choices[0].message.content.strip()
            # Strip fenced code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Extract JSON from response (handle cases where GPT adds extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            result_data = None
            if json_match:
                try:
                    result_data = json.loads(json_match.group(0))
                except Exception:
                    # fall back to naive parse by removing trailing text and retry once
                    cleaned = re.sub(r'^.*?(\{)', r'\1', response_text, flags=re.DOTALL)
                    cleaned = re.sub(r'(\})[^\}]*$', r'\1', cleaned, flags=re.DOTALL)
                    try:
                        result_data = json.loads(cleaned)
                    except Exception:
                        result_data = None
            if result_data:
                
                # Create conversion result
                result = ConversionResult(
                    original_mathml=mathml,
                    converted_latex=result_data.get('latex', ''),
                    confidence=result_data.get('confidence', 0.5),
                    conversion_notes=result_data.get('notes', ''),
                    display_mode=bool(result_data.get('display_mode', False)),
                    error_message=None
                )
                
                # Update stats
                self.conversion_stats['total_processed'] += 1
                if result.converted_latex:
                    self.conversion_stats['successful_conversions'] += 1
                    if result.confidence >= 0.8:
                        self.conversion_stats['high_confidence'] += 1
                    elif result.confidence >= 0.6:
                        self.conversion_stats['medium_confidence'] += 1
                    else:
                        self.conversion_stats['low_confidence'] += 1
                else:
                    self.conversion_stats['failed_conversions'] += 1
                
                # Cache the result
                self.conversion_cache[mathml] = result
                
                return result
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            error_result = ConversionResult(
                original_mathml=mathml,
                converted_latex='',
                confidence=0.0,
                conversion_notes='',
                error_message=str(e)
            )
            
            self.conversion_stats['total_processed'] += 1
            self.conversion_stats['failed_conversions'] += 1
            
            return error_result
    
    def process_content_batch(self, content_list: List[str], batch_size: int = 10) -> List[Dict]:
        """Process multiple content items in batches"""
        results = []
        
        for i in range(0, len(content_list), batch_size):
            batch = content_list[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(content_list) + batch_size - 1)//batch_size}")
            
            for content in batch:
                mathml_expressions = self.extract_mathml_from_content(content)
                
                content_result = {
                    'original_content': content,
                    'mathml_expressions': [],
                    'converted_content': content
                }
                
                # Convert each MathML expression
                for mathml, position in mathml_expressions:
                    conversion_result = self.convert_mathml_with_ai(mathml)
                    content_result['mathml_expressions'].append({
                        'position': position,
                        'mathml': mathml,
                        'conversion': asdict(conversion_result)
                    })
                    
                    # Replace in content
                    if conversion_result.converted_latex:
                        if getattr(conversion_result, 'display_mode', False):
                            latex_wrapper = f"\\[{conversion_result.converted_latex}\\]"
                        else:
                            latex_wrapper = f"\\({conversion_result.converted_latex}\\)"
                        
                        content_result['converted_content'] = content_result['converted_content'].replace(mathml, latex_wrapper)
                
                results.append(content_result)
            
            # Add delay between batches to respect API limits
            if i + batch_size < len(content_list):
                time.sleep(1)
        
        return results
    
    def save_conversion_results(self, results: List[Dict], output_file: str):
        """Save conversion results to JSON file"""
        output_data = {
            'conversion_stats': self.conversion_stats,
            'results': results,
            'timestamp': time.time()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Conversion results saved to {output_file}")
    
    def generate_conversion_report(self) -> str:
        """Generate a detailed conversion report"""
        stats = self.conversion_stats
        total = stats['total_processed']
        
        if total == 0:
            return "No conversions processed yet."
        
        success_rate = (stats['successful_conversions'] / total) * 100
        high_conf_rate = (stats['high_confidence'] / total) * 100
        
        report = f"""
=== AI MathML Conversion Report ===
Total Processed: {total}
Successful Conversions: {stats['successful_conversions']} ({success_rate:.1f}%)
Failed Conversions: {stats['failed_conversions']} ({(100-success_rate):.1f}%)

Confidence Distribution:
- High Confidence (≥0.8): {stats['high_confidence']} ({high_conf_rate:.1f}%)
- Medium Confidence (0.6-0.8): {stats['medium_confidence']} ({(stats['medium_confidence']/total)*100:.1f}%)
- Low Confidence (<0.6): {stats['low_confidence']} ({(stats['low_confidence']/total)*100:.1f}%)

Cache Hit Rate: {len(self.conversion_cache)} unique expressions processed
"""
        return report

def main():
    """Main function to demonstrate the AI MathML converter"""
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    # Initialize converter
    converter = AIMathMLConverter(api_key)
    
    # Sample MathML expressions from the database
    sample_mathml = [
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><mfrac><mrow><mn>180</mn><mo>°</mo></mrow><mn>2</mn></mfrac></math>',
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><msup><mi>k</mi><mn>2</mn></msup></math>',
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><mtable><mtr><mtd><mn>1</mn></mtd><mtd><mn>2</mn></mtd></mtr><mtr><mtd><mn>3</mn></mtd><mtd><mn>4</mn></mtd></mtr></mtable></math>'
    ]
    
    print("Testing AI MathML Converter...")
    print("=" * 50)
    
    for i, mathml in enumerate(sample_mathml, 1):
        print(f"\nTest {i}:")
        print(f"Input MathML: {mathml[:100]}...")
        
        result = converter.convert_mathml_with_ai(mathml)
        
        print(f"Converted LaTeX: {result.converted_latex}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Notes: {result.conversion_notes}")
        if result.error_message:
            print(f"Error: {result.error_message}")
    
    # Generate report
    print("\n" + "=" * 50)
    print(converter.generate_conversion_report())

if __name__ == "__main__":
    main()
