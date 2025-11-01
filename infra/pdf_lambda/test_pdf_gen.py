#!/usr/bin/env python3
"""
Test script for exam PDF generation
Usage: python test_pdf_gen.py
"""
import sys
from pathlib import Path

# Add parent dir to path to import exam_renderer
sys.path.insert(0, str(Path(__file__).parent))

from exam_renderer import render_exam_pdf

# Sample exam result data (matches API response schema)
SAMPLE_RESULT = {
    "session_id": "test-session-12345",
    "user_id": "student-001",
    "exam_id": 1,
    "status": "ready",
    "created_at": "2025-10-31T10:30:00Z",
    "summary": {
        "score_raw": 42,
        "score_scaled": 128.5,
        "correct": 18,
        "total": 25,
        "percentile": 67.5,
        "standard_error": 4.2,
    },
    "breakdown": {
        "by_topic": [
            {"topic": "Algebra", "correct": 8, "total": 10},
            {"topic": "Geometry", "correct": 5, "total": 8},
            {"topic": "Probability", "correct": 3, "total": 5},
            {"topic": "Calculus", "correct": 2, "total": 2},
        ]
    },
    "recommendations": [
        "Review probability concepts (60% accuracy)",
        "Practice geometry problems with diagrams",
        "Strong performance in algebra - maintain practice",
    ],
}


def test_pdf_generation():
    print("Testing PDF generation...")

    try:
        pdf_bytes = render_exam_pdf(
            result_data=SAMPLE_RESULT,
            tutor_brand="DreamSeed Academy",
            page_format="A4",
        )

        print(f"✅ PDF generated successfully: {len(pdf_bytes)} bytes")

        # Save to file
        output_path = Path(__file__).parent / "test_exam_result.pdf"
        output_path.write_bytes(pdf_bytes)
        print(f"✅ Saved to: {output_path}")

        return True

    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_letter_format():
    print("\nTesting Letter format...")

    try:
        pdf_bytes = render_exam_pdf(
            result_data=SAMPLE_RESULT,
            tutor_brand="US Tutoring Center",
            page_format="Letter",
        )

        print(f"✅ Letter PDF generated: {len(pdf_bytes)} bytes")

        output_path = Path(__file__).parent / "test_exam_result_letter.pdf"
        output_path.write_bytes(pdf_bytes)
        print(f"✅ Saved to: {output_path}")

        return True

    except Exception as e:
        print(f"❌ Letter PDF generation failed: {e}")
        return False


if __name__ == "__main__":
    success_a4 = test_pdf_generation()
    success_letter = test_letter_format()

    if success_a4 and success_letter:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
