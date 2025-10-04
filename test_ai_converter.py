#!/usr/bin/env python3
"""
Test script for AI MathML Converter
Tests the converter with sample MathML expressions from the database
"""

import os
import json
from ai_mathml_converter import AIMathMLConverter

def test_ai_converter():
    """Test the AI MathML converter with sample expressions"""
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Initialize converter
    converter = AIMathMLConverter(api_key)
    
    # Test cases from the actual database
    test_cases = [
        {
            "name": "Simple Fraction",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><mfrac><mrow><mn>180</mn><mo>°</mo></mrow><mn>2</mn></mfrac></math>',
            "expected": "\\frac{180°}{2}"
        },
        {
            "name": "Complex Summation",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><msup><mi>k</mi><mn>2</mn></msup></math>',
            "expected": "\\sum_{k=1}^{n} k^2"
        },
        {
            "name": "Matrix",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><mtable><mtr><mtd><mn>1</mn></mtd><mtd><mn>2</mn></mtd></mtr><mtr><mtd><mn>3</mn></mtd><mtd><mn>4</mn></mtd></mtr></mtable></math>',
            "expected": "\\begin{matrix} 1 & 2 \\\\ 3 & 4 \\end{matrix}"
        },
        {
            "name": "Complex Fraction with Variables",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><mfrac><mrow><mi>k</mi><mfenced><mrow><mi>k</mi><mo>+</mo><mn>1</mn></mrow></mfenced></mrow><mn>2</mn></mfrac></math>',
            "expected": "\\frac{k(k+1)}{2}"
        },
        {
            "name": "Square Root",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><msqrt><mrow><mi>n</mi><mo>+</mo><mn>1</mn></mrow></msqrt></math>',
            "expected": "\\sqrt{n+1}"
        },
        {
            "name": "Limit Expression",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><munder><mi>lim</mi><mrow><mi>n</mi><mo>→</mo><mo>∞</mo></mrow></munder><mfrac><mn>1</mn><mi>n</mi></mfrac></math>',
            "expected": "\\lim_{n \\to \\infty} \\frac{1}{n}"
        },
        {
            "name": "Complex Matrix with Variables",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><mfenced><mtable><mtr><mtd><msub><mi>a</mi><mrow><mi>n</mi><mo>+</mo><mn>2</mn></mrow></msub></mtd><mtd><msub><mi>a</mi><mrow><mi>n</mi><mo>+</mo><mn>1</mn></mrow></msub></mtd></mtr><mtr><mtd><msub><mi>a</mi><mrow><mi>n</mi><mo>+</mo><mn>1</mn></mrow></msub></mtd><mtd><msub><mi>a</mi><mi>n</mi></msub></mtd></mtr></mtable></mfenced></math>',
            "expected": "\\begin{pmatrix} a_{n+2} & a_{n+1} \\\\ a_{n+1} & a_n \\end{pmatrix}"
        }
    ]
    
    print("Testing AI MathML Converter")
    print("=" * 60)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Input MathML: {test_case['mathml'][:80]}...")
        
        # Convert using AI
        result = converter.convert_mathml_with_ai(test_case['mathml'])
        
        print(f"Converted LaTeX: {result.converted_latex}")
        print(f"Expected: {test_case['expected']}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Notes: {result.conversion_notes}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        # Check if conversion matches expected (fuzzy match)
        expected_clean = test_case['expected'].replace(' ', '').replace('\\', '')
        actual_clean = result.converted_latex.replace(' ', '').replace('\\', '')
        
        if expected_clean in actual_clean or actual_clean in expected_clean:
            print("✅ Conversion looks correct")
            test_result = "PASS"
        else:
            print("❌ Conversion may need review")
            test_result = "REVIEW"
        
        results.append({
            'test_name': test_case['name'],
            'input_mathml': test_case['mathml'],
            'expected_latex': test_case['expected'],
            'actual_latex': result.converted_latex,
            'confidence': result.confidence,
            'notes': result.conversion_notes,
            'error': result.error_message,
            'test_result': test_result
        })
    
    # Generate test report
    print("\n" + "=" * 60)
    print("TEST REPORT")
    print("=" * 60)
    
    passed = len([r for r in results if r['test_result'] == 'PASS'])
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    for result in results:
        status = "✅" if result['test_result'] == 'PASS' else "❌"
        print(f"{status} {result['test_name']}: {result['test_result']}")
        if result['test_result'] == 'REVIEW':
            print(f"   Expected: {result['expected_latex']}")
            print(f"   Actual:   {result['actual_latex']}")
    
    # Save test results
    with open('ai_converter_test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'test_results': results,
            'summary': {
                'total_tests': total,
                'passed': passed,
                'pass_rate': passed/total*100
            },
            'conversion_stats': converter.conversion_stats
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nTest results saved to ai_converter_test_results.json")
    
    # Generate conversion report
    print("\n" + "=" * 60)
    print("CONVERSION STATISTICS")
    print("=" * 60)
    print(converter.generate_conversion_report())

if __name__ == "__main__":
    test_ai_converter()
