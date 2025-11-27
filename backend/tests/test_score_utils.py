"""
test_score_utils.py

Unit tests for score_utils module (pure utility functions).

Tests all theta → score/grade conversion functions to ensure:
1. Mathematical correctness
2. Edge case handling
3. Performance (should be <1ms per conversion)

Run:
    cd backend && pytest tests/test_score_utils.py -v
    cd backend && pytest tests/test_score_utils.py::test_performance -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import time
from app.services.score_utils import (
    theta_to_0_100,
    theta_to_t_score,
    theta_to_percentile,
    theta_to_grade_numeric,
    percentile_to_letter_grade,
    summarize_theta,
    score_0_100_to_theta,
    t_score_to_theta,
    batch_summarize_theta,
    theta_to_korean_grade,
    theta_to_sat_score,
)


# ============================================================================
# Test: theta_to_0_100
# ============================================================================

def test_theta_to_0_100_basic():
    """Test basic theta to 0-100 score conversion."""
    assert theta_to_0_100(0.0) == 50.0
    assert theta_to_0_100(-3.0) == 0.0
    assert theta_to_0_100(3.0) == 100.0
    assert theta_to_0_100(1.5) == 75.0
    assert theta_to_0_100(-1.5) == 25.0


def test_theta_to_0_100_clamping():
    """Test clamping outside range."""
    assert theta_to_0_100(-10.0) == 0.0  # Clamp to 0
    assert theta_to_0_100(10.0) == 100.0  # Clamp to 100


def test_theta_to_0_100_custom_range():
    """Test with custom theta range."""
    # Custom range: -2 to 2
    assert theta_to_0_100(0.0, min_theta=-2.0, max_theta=2.0) == 50.0
    assert theta_to_0_100(-2.0, min_theta=-2.0, max_theta=2.0) == 0.0
    assert theta_to_0_100(2.0, min_theta=-2.0, max_theta=2.0) == 100.0


def test_theta_to_0_100_invalid_range():
    """Test error handling for invalid range."""
    with pytest.raises(ValueError, match="max_theta must be greater than min_theta"):
        theta_to_0_100(0.0, min_theta=2.0, max_theta=1.0)


# ============================================================================
# Test: theta_to_t_score
# ============================================================================

def test_theta_to_t_score_basic():
    """Test T-score conversion."""
    assert theta_to_t_score(0.0) == 50.0
    assert theta_to_t_score(1.0) == 60.0
    assert theta_to_t_score(-1.0) == 40.0
    assert theta_to_t_score(2.0) == 70.0


def test_theta_to_t_score_custom_scale():
    """Test T-score with custom mean/sd."""
    # Custom: mean=100, sd=15 (IQ-style)
    assert theta_to_t_score(0.0, mean=100.0, sd=15.0) == 100.0
    assert theta_to_t_score(1.0, mean=100.0, sd=15.0) == 115.0
    assert theta_to_t_score(-1.0, mean=100.0, sd=15.0) == 85.0


# ============================================================================
# Test: theta_to_percentile
# ============================================================================

def test_theta_to_percentile_basic():
    """Test percentile conversion."""
    assert abs(theta_to_percentile(0.0) - 50.0) < 0.1
    assert abs(theta_to_percentile(1.0) - 84.13) < 0.1
    assert abs(theta_to_percentile(-1.0) - 15.87) < 0.1
    assert abs(theta_to_percentile(2.0) - 97.72) < 0.1


def test_theta_to_percentile_extremes():
    """Test percentile at extreme values."""
    assert theta_to_percentile(-3.0) < 1.0  # Very low
    assert theta_to_percentile(3.0) > 99.0  # Very high


# ============================================================================
# Test: theta_to_grade_numeric
# ============================================================================

def test_theta_to_grade_numeric_basic():
    """Test numeric grade conversion (1-9)."""
    assert theta_to_grade_numeric(1.5) == 1  # High ability
    assert theta_to_grade_numeric(0.7) == 2
    assert theta_to_grade_numeric(0.2) == 3
    assert theta_to_grade_numeric(-0.2) == 4
    assert theta_to_grade_numeric(-0.7) == 5
    assert theta_to_grade_numeric(-1.2) == 6
    assert theta_to_grade_numeric(-1.7) == 7
    assert theta_to_grade_numeric(-2.2) == 8
    assert theta_to_grade_numeric(-3.0) == 9  # Low ability


def test_theta_to_grade_numeric_custom_cutoffs():
    """Test with custom cutoffs."""
    cutoffs = (0.5, 0.0, -0.5)  # 3-grade system
    assert theta_to_grade_numeric(0.6, cutoffs=cutoffs) == 1
    assert theta_to_grade_numeric(0.2, cutoffs=cutoffs) == 2
    assert theta_to_grade_numeric(-0.2, cutoffs=cutoffs) == 3
    assert theta_to_grade_numeric(-1.0, cutoffs=cutoffs) == 4


# ============================================================================
# Test: percentile_to_letter_grade
# ============================================================================

def test_percentile_to_letter_grade_basic():
    """Test letter grade conversion."""
    assert percentile_to_letter_grade(95) == "A"
    assert percentile_to_letter_grade(85) == "B"
    assert percentile_to_letter_grade(65) == "C"
    assert percentile_to_letter_grade(35) == "D"
    assert percentile_to_letter_grade(15) == "F"


def test_percentile_to_letter_grade_boundaries():
    """Test grade boundaries."""
    assert percentile_to_letter_grade(90.0) == "B"  # Lower boundary of A
    assert percentile_to_letter_grade(89.9) == "B"
    assert percentile_to_letter_grade(75.0) == "C"  # Lower boundary of B


def test_percentile_to_letter_grade_custom_bands():
    """Test with custom grade bands."""
    custom_bands = {
        "Excellent": (80, 100),
        "Good": (60, 80),
        "Average": (40, 60),
        "Poor": (0, 40),
    }
    assert percentile_to_letter_grade(85, bands=custom_bands) == "Excellent"
    assert percentile_to_letter_grade(65, bands=custom_bands) == "Good"
    assert percentile_to_letter_grade(45, bands=custom_bands) == "Average"
    assert percentile_to_letter_grade(25, bands=custom_bands) == "Poor"


# ============================================================================
# Test: summarize_theta
# ============================================================================

def test_summarize_theta_basic():
    """Test complete theta summary."""
    summary = summarize_theta(0.5)
    
    assert "theta" in summary
    assert "score_0_100" in summary
    assert "t_score" in summary
    assert "percentile" in summary
    assert "grade_numeric" in summary
    assert "grade_letter" in summary
    
    assert summary["theta"] == 0.5
    assert 55 < summary["score_0_100"] < 60
    assert summary["t_score"] == 55.0
    assert 65 < summary["percentile"] < 70
    assert summary["grade_numeric"] == 2
    assert summary["grade_letter"] == "C"


def test_summarize_theta_extremes():
    """Test summary at extreme theta values."""
    # Very high
    high = summarize_theta(2.5)
    assert high["score_0_100"] > 90
    assert high["grade_numeric"] == 1
    assert high["grade_letter"] in ["A", "B"]
    
    # Very low
    low = summarize_theta(-2.5)
    assert low["score_0_100"] < 10
    assert low["grade_numeric"] >= 8
    assert low["grade_letter"] == "F"


# ============================================================================
# Test: Inverse conversions
# ============================================================================

def test_score_0_100_to_theta():
    """Test inverse conversion from score to theta."""
    assert score_0_100_to_theta(50.0) == 0.0
    assert score_0_100_to_theta(75.0) == 1.5
    assert score_0_100_to_theta(25.0) == -1.5
    assert score_0_100_to_theta(0.0) == -3.0
    assert score_0_100_to_theta(100.0) == 3.0


def test_score_theta_roundtrip():
    """Test roundtrip: theta → score → theta."""
    for theta in [-2.0, -1.0, 0.0, 1.0, 2.0]:
        score = theta_to_0_100(theta)
        theta_back = score_0_100_to_theta(score)
        assert abs(theta - theta_back) < 0.001


def test_t_score_to_theta():
    """Test inverse T-score conversion."""
    assert t_score_to_theta(50.0) == 0.0
    assert t_score_to_theta(60.0) == 1.0
    assert t_score_to_theta(40.0) == -1.0


def test_t_score_roundtrip():
    """Test roundtrip: theta → T-score → theta."""
    for theta in [-2.0, -1.0, 0.0, 1.0, 2.0]:
        t_score = theta_to_t_score(theta)
        theta_back = t_score_to_theta(t_score)
        assert abs(theta - theta_back) < 0.001


# ============================================================================
# Test: Batch operations
# ============================================================================

def test_batch_summarize_theta():
    """Test batch theta summarization."""
    theta_list = [-1.0, 0.0, 1.0]
    summaries = batch_summarize_theta(theta_list)
    
    assert len(summaries) == 3
    assert summaries[0]["theta"] == -1.0
    assert summaries[1]["theta"] == 0.0
    assert summaries[2]["theta"] == 1.0
    
    # Check all summaries have required fields
    for summary in summaries:
        assert "score_0_100" in summary
        assert "grade_numeric" in summary


# ============================================================================
# Test: Korean education system
# ============================================================================

def test_theta_to_korean_grade_9grade():
    """Test Korean 9-grade system."""
    # Grade 1: Top 4%
    assert theta_to_korean_grade(2.0, "9grade") == 1
    
    # Grade 5: Around median
    assert theta_to_korean_grade(0.0, "9grade") in [4, 5, 6]
    
    # Grade 9: Bottom
    assert theta_to_korean_grade(-2.5, "9grade") == 9


def test_theta_to_korean_grade_5grade():
    """Test Korean 5-grade system."""
    # Grade 1: Top 20%
    assert theta_to_korean_grade(1.0, "5grade") == 1
    
    # Grade 3: Middle 20%
    assert theta_to_korean_grade(0.0, "5grade") == 3
    
    # Grade 5: Bottom 20%
    assert theta_to_korean_grade(-1.0, "5grade") == 5


def test_theta_to_korean_grade_invalid():
    """Test error handling for invalid system."""
    with pytest.raises(ValueError, match="Unknown system"):
        theta_to_korean_grade(0.0, "invalid")


# ============================================================================
# Test: SAT score conversion
# ============================================================================

def test_theta_to_sat_score():
    """Test SAT score conversion."""
    assert theta_to_sat_score(0.0) == 500
    assert theta_to_sat_score(1.0) == 600
    assert theta_to_sat_score(2.0) == 700
    assert theta_to_sat_score(-1.0) == 400


def test_theta_to_sat_score_clamping():
    """Test SAT score clamping (200-800)."""
    assert theta_to_sat_score(-5.0) == 200  # Clamp to minimum
    assert theta_to_sat_score(5.0) == 800   # Clamp to maximum


# ============================================================================
# Test: Performance
# ============================================================================

def test_performance_single_conversion():
    """Test that single conversion is fast (<1ms)."""
    iterations = 1000
    
    start = time.time()
    for _ in range(iterations):
        summarize_theta(0.5)
    elapsed = time.time() - start
    
    avg_time_ms = (elapsed / iterations) * 1000
    assert avg_time_ms < 1.0, f"Average time {avg_time_ms:.3f}ms exceeds 1ms threshold"
    print(f"\n⚡ Average conversion time: {avg_time_ms:.4f}ms")


def test_performance_batch_conversion():
    """Test batch conversion performance."""
    theta_list = [i * 0.1 for i in range(-30, 31)]  # 61 values
    
    start = time.time()
    summaries = batch_summarize_theta(theta_list)
    elapsed = time.time() - start
    
    assert len(summaries) == 61
    avg_time_ms = (elapsed / len(summaries)) * 1000
    assert avg_time_ms < 1.0, f"Average batch time {avg_time_ms:.3f}ms exceeds 1ms threshold"
    print(f"\n⚡ Batch conversion: {elapsed*1000:.2f}ms total, {avg_time_ms:.4f}ms per item")


# ============================================================================
# Test: Edge cases
# ============================================================================

def test_edge_case_zero_theta():
    """Test behavior at theta=0 (average ability)."""
    summary = summarize_theta(0.0)
    assert summary["score_0_100"] == 50.0
    assert summary["t_score"] == 50.0
    assert abs(summary["percentile"] - 50.0) < 0.1
    assert summary["grade_numeric"] == 3


def test_edge_case_extreme_theta():
    """Test behavior at extreme theta values."""
    # Very high
    high = summarize_theta(5.0)
    assert high["score_0_100"] == 100.0  # Clamped
    assert high["percentile"] > 99.9
    
    # Very low
    low = summarize_theta(-5.0)
    assert low["score_0_100"] == 0.0  # Clamped
    assert low["percentile"] < 0.1


def test_edge_case_fractional_theta():
    """Test with fractional theta values."""
    summary = summarize_theta(0.123456)
    assert isinstance(summary["score_0_100"], float)
    assert isinstance(summary["percentile"], float)
    assert isinstance(summary["grade_numeric"], int)


# ============================================================================
# Integration test: Full workflow
# ============================================================================

def test_integration_exam_scoring():
    """
    Integration test: Simulate exam scoring workflow.
    
    Scenario:
    - Student takes adaptive exam
    - Final theta = 0.75
    - Convert to all score formats
    - Verify consistency
    """
    theta = 0.75
    
    # Get complete summary
    summary = summarize_theta(theta)
    
    # Verify all fields present
    required_fields = [
        "theta", "score_0_100", "t_score", 
        "percentile", "grade_numeric", "grade_letter"
    ]
    for field in required_fields:
        assert field in summary, f"Missing field: {field}"
    
    # Verify value consistency
    assert summary["score_0_100"] > 50  # Above average theta
    assert summary["t_score"] > 50      # Above average T-score
    assert summary["percentile"] > 50   # Above median
    assert summary["grade_numeric"] <= 3  # Good grade
    
    # Additional conversions
    korean_grade = theta_to_korean_grade(theta, "9grade")
    sat_score = theta_to_sat_score(theta)
    
    assert korean_grade <= 3  # Top grades
    assert sat_score > 550    # Above average SAT
    
    print(f"\n📊 Exam Scoring Summary (θ={theta}):")
    print(f"  Score: {summary['score_0_100']:.1f}/100")
    print(f"  Percentile: {summary['percentile']:.1f}%")
    print(f"  Grade: {summary['grade_numeric']} ({summary['grade_letter']})")
    print(f"  Korean Grade: {korean_grade}")
    print(f"  SAT Equivalent: {sat_score}")


# ============================================================================
# Test: Documentation examples
# ============================================================================

def test_docstring_examples():
    """Verify examples from docstrings work correctly."""
    # From theta_to_0_100 docstring
    assert theta_to_0_100(0.0) == 50.0
    assert theta_to_0_100(1.5) == 75.0
    
    # From theta_to_t_score docstring
    assert theta_to_t_score(0.0) == 50.0
    assert theta_to_t_score(1.0) == 60.0
    
    # From theta_to_grade_numeric docstring
    assert theta_to_grade_numeric(1.2) == 1
    assert theta_to_grade_numeric(0.0) == 3
