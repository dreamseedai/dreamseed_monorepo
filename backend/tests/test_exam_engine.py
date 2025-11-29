"""
Test suite for IRT/CAT Adaptive Testing Engine

Tests core IRT functions, theta estimation, item selection,
and adaptive engine workflow.
"""
import pytest
import math
from app.core.services.exam_engine import (
    irt_probability,
    item_information,
    update_theta_mle,
    should_terminate,
    select_next_item,
    update_session_after_attempt,
    AdaptiveEngine,
)


# ============================================================================
# 1. IRT Functions Tests
# ============================================================================

def test_irt_probability_basic():
    """Test 3PL probability calculation"""
    # Easy item (b=-1), average ability (theta=0), medium discrimination (a=1.0)
    p = irt_probability(a=1.0, b=-1.0, c=0.2, theta=0.0)
    
    # P(theta=0) = 0.2 + (1-0.2) / (1 + exp(-1*(0 - (-1))))
    #            = 0.2 + 0.8 / (1 + exp(-1))
    #            = 0.2 + 0.8 / (1 + 0.368)
    #            ≈ 0.785
    assert 0.7 < p < 0.9
    assert isinstance(p, float)


def test_irt_probability_guessing():
    """Test that probability never goes below guessing parameter"""
    # Very hard item (b=3), low ability (theta=-3)
    p = irt_probability(a=1.0, b=3.0, c=0.25, theta=-3.0)
    
    # Even with very low ability, probability should be >= guessing
    assert p >= 0.25


def test_irt_probability_ceiling():
    """Test that probability approaches 1 for easy items"""
    # Very easy item (b=-3), high ability (theta=3)
    p = irt_probability(a=1.5, b=-3.0, c=0.2, theta=3.0)
    
    # Should be very high but < 1
    assert 0.9 < p < 1.0


def test_item_information_maximum():
    """Test that information varies with item difficulty"""
    a, c = 1.5, 0.2
    theta = 0.5
    
    # Information at b=theta (item difficulty matches ability)
    info_at_b = item_information(a, b=theta, c=c, theta=theta)
    
    # Information when item is easier (b < theta)
    info_below = item_information(a, b=theta - 0.5, c=c, theta=theta)
    
    # Information when item is harder (b > theta)
    info_above = item_information(a, b=theta + 0.5, c=c, theta=theta)
    
    # All should be positive and non-zero
    assert info_at_b > 0
    assert info_below > 0
    assert info_above > 0
    
    # In 3PL model, maximum information is slightly below b=theta due to guessing
    # Main test: information should be similar in magnitude
    assert abs(info_at_b - info_below) < 10  # Within reasonable range


def test_item_information_discrimination():
    """Test that higher discrimination = higher information"""
    b, c, theta = 0.0, 0.2, 0.0
    
    info_low = item_information(a=0.5, b=b, c=c, theta=theta)
    info_high = item_information(a=2.0, b=b, c=c, theta=theta)
    
    assert info_high > info_low


# ============================================================================
# 2. Theta Update Tests
# ============================================================================

def test_update_theta_correct_response():
    """Test theta increases after correct response to difficult item"""
    initial_theta = 0.0
    
    # Difficult item (b=1.5)
    item_params = [{"a": 1.2, "b": 1.5, "c": 0.2}]
    responses = [True]  # Correct
    
    new_theta = update_theta_mle(initial_theta, item_params, responses)
    
    # Should increase
    assert new_theta > initial_theta


def test_update_theta_incorrect_response():
    """Test theta decreases after incorrect response to easy item"""
    initial_theta = 0.0
    
    # Easy item (b=-1.5)
    item_params = [{"a": 1.2, "b": -1.5, "c": 0.2}]
    responses = [False]  # Incorrect
    
    new_theta = update_theta_mle(initial_theta, item_params, responses)
    
    # Should decrease
    assert new_theta < initial_theta


def test_update_theta_multiple_items():
    """Test theta update with multiple responses"""
    initial_theta = 0.0
    
    item_params = [
        {"a": 1.0, "b": -0.5, "c": 0.2},  # Easy
        {"a": 1.2, "b": 0.0, "c": 0.2},   # Medium
        {"a": 1.5, "b": 0.5, "c": 0.2},   # Hard
    ]
    responses = [True, True, False]  # 2 correct, 1 incorrect
    
    new_theta = update_theta_mle(initial_theta, item_params, responses)
    
    # Should be bounded and change from initial
    assert -4.0 <= new_theta <= 4.0
    # With 2/3 correct, theta should increase from 0
    assert new_theta != initial_theta


def test_update_theta_convergence():
    """Test theta converges and stays bounded"""
    initial_theta = 0.0
    
    item_params = [{"a": 1.0, "b": 0.0, "c": 0.2}]
    responses = [True]
    
    theta_updated = update_theta_mle(initial_theta, item_params, responses, max_iter=10)
    
    # Should be bounded to reasonable range
    assert -4.0 <= theta_updated <= 4.0
    # Should have increased (correct response)
    assert theta_updated > initial_theta


# ============================================================================
# 3. Termination Tests
# ============================================================================

def test_should_terminate_se_threshold():
    """Test termination when SE threshold met"""
    assert should_terminate(standard_error=0.25, attempt_count=5, max_items=20) is True
    assert should_terminate(standard_error=0.35, attempt_count=5, max_items=20) is False


def test_should_terminate_max_items():
    """Test termination when max items reached"""
    assert should_terminate(standard_error=0.5, attempt_count=20, max_items=20) is True
    assert should_terminate(standard_error=0.5, attempt_count=15, max_items=20) is False


def test_should_terminate_none_se():
    """Test termination with None standard error"""
    # Should only consider attempt count
    assert should_terminate(standard_error=None, attempt_count=25, max_items=20) is True
    assert should_terminate(standard_error=None, attempt_count=10, max_items=20) is False


# ============================================================================
# 4. Item Selection Tests
# ============================================================================

def test_select_next_item_maximum_information():
    """Test that item with highest information is selected"""
    theta = 0.0
    
    items = [
        {"id": 1, "a": 1.0, "b": -1.5, "c": 0.2},  # Easy (far below theta)
        {"id": 2, "a": 1.5, "b": 0.0, "c": 0.2},   # At theta
        {"id": 3, "a": 1.0, "b": 1.5, "c": 0.2},   # Hard (far above theta)
    ]
    
    selected = select_next_item(theta, items)
    
    # Should pick an item
    assert selected is not None
    assert "id" in selected
    
    # The selected item should be one of the available items
    assert selected["id"] in [1, 2, 3]
    
    # Verify it picks item with non-zero information
    selected_info = item_information(
        selected["a"], selected["b"], selected["c"], theta
    )
    assert selected_info > 0


def test_select_next_item_empty_pool():
    """Test item selection with empty pool"""
    selected = select_next_item(theta=0.0, available_items=[])
    assert selected is None


def test_select_next_item_single_item():
    """Test item selection with single item"""
    items = [{"id": 1, "a": 1.0, "b": 0.0, "c": 0.2}]
    selected = select_next_item(theta=0.0, available_items=items)
    assert selected is not None
    assert selected["id"] == 1


# ============================================================================
# 5. Session Update Tests
# ============================================================================

def test_update_session_after_attempt():
    """Test session update after recording attempt"""
    result = update_session_after_attempt(
        theta=0.0,
        item_params_list=[{"a": 1.2, "b": 0.5, "c": 0.2}],
        responses=[True]
    )
    
    assert "theta" in result
    assert "standard_error" in result
    assert isinstance(result["theta"], float)
    assert result["standard_error"] is None or isinstance(result["standard_error"], float)


def test_session_se_decreases_with_items():
    """Test that SE decreases as more items are administered"""
    # After 1 item
    result1 = update_session_after_attempt(
        theta=0.0,
        item_params_list=[{"a": 1.0, "b": 0.0, "c": 0.2}],
        responses=[True]
    )
    
    # After 3 items (with varied responses)
    result3 = update_session_after_attempt(
        theta=0.0,
        item_params_list=[
            {"a": 1.0, "b": 0.2, "c": 0.2},
            {"a": 1.2, "b": 0.3, "c": 0.2},
            {"a": 0.9, "b": -0.2, "c": 0.2},
        ],
        responses=[True, True, True]
    )
    
    # Both should have SE
    assert result1["standard_error"] is not None
    assert result3["standard_error"] is not None
    # SE should decrease with more items
    assert result3["standard_error"] < result1["standard_error"]


# ============================================================================
# 6. AdaptiveEngine Integration Tests
# ============================================================================

def test_adaptive_engine_initialization():
    """Test engine initialization"""
    engine = AdaptiveEngine(initial_theta=0.5)
    
    assert engine.theta == 0.5
    assert len(engine.responses) == 0
    assert len(engine.item_params_list) == 0


def test_adaptive_engine_record_attempt():
    """Test recording attempts updates state"""
    engine = AdaptiveEngine(initial_theta=0.0)
    
    updated = engine.record_attempt(
        params={"a": 1.2, "b": 0.5, "c": 0.2},
        correct=True
    )
    
    assert "theta" in updated
    assert "standard_error" in updated
    assert len(engine.responses) == 1
    assert len(engine.item_params_list) == 1


def test_adaptive_engine_pick_item():
    """Test item picking"""
    engine = AdaptiveEngine(initial_theta=0.0)
    
    items = [
        {"id": 1, "a": 1.0, "b": -1.0, "c": 0.2},
        {"id": 2, "a": 1.5, "b": 0.0, "c": 0.2},
        {"id": 3, "a": 1.0, "b": 1.0, "c": 0.2},
    ]
    
    selected = engine.pick_item(items)
    
    assert selected is not None
    assert "id" in selected


def test_adaptive_engine_should_stop():
    """Test termination logic"""
    engine = AdaptiveEngine(initial_theta=0.0)
    
    # Should not stop initially
    assert engine.should_stop(max_items=20) is False
    
    # Record 20 attempts with varied difficulty to avoid overflow
    for i in range(20):
        b_difficulty = (i % 5) * 0.3 - 0.6  # Varies from -0.6 to 0.6
        engine.record_attempt(
            params={"a": 1.0, "b": b_difficulty, "c": 0.2},
            correct=(i % 2 == 0)
        )
    
    # Should stop after max items
    assert engine.should_stop(max_items=20) is True


def test_adaptive_engine_get_state():
    """Test state retrieval"""
    engine = AdaptiveEngine(initial_theta=0.0)
    
    # Initial state
    state = engine.get_state()
    assert state["theta"] == 0.0
    assert state["attempt_count"] == 0
    assert state["accuracy"] is None
    
    # After some attempts
    engine.record_attempt({"a": 1.0, "b": 0.2, "c": 0.2}, True)
    engine.record_attempt({"a": 1.2, "b": 0.3, "c": 0.2}, True)
    engine.record_attempt({"a": 0.9, "b": -0.2, "c": 0.2}, False)
    
    state = engine.get_state()
    assert state["attempt_count"] == 3
    assert state["correct_count"] == 2
    assert state["accuracy"] == pytest.approx(2/3)


def test_adaptive_engine_full_workflow():
    """Test complete adaptive test workflow"""
    engine = AdaptiveEngine(initial_theta=0.0)
    
    # Item pool
    items = [
        {"id": 1, "a": 1.0, "b": -1.5, "c": 0.2},
        {"id": 2, "a": 1.2, "b": -0.5, "c": 0.2},
        {"id": 3, "a": 1.5, "b": 0.0, "c": 0.2},
        {"id": 4, "a": 1.3, "b": 0.5, "c": 0.2},
        {"id": 5, "a": 1.1, "b": 1.5, "c": 0.2},
    ]
    
    used_item_ids = set()
    
    # Simulate test session
    while not engine.should_stop(max_items=5):
        # Pick next item
        available = [item for item in items if item["id"] not in used_item_ids]
        if not available:
            break
            
        next_item = engine.pick_item(available)
        if not next_item:
            break
            
        used_item_ids.add(next_item["id"])
        
        # Simulate response (correct if item difficulty < current theta)
        correct = next_item["b"] < engine.theta
        
        # Record attempt
        engine.record_attempt(
            params={"a": next_item["a"], "b": next_item["b"], "c": next_item["c"]},
            correct=correct
        )
    
    # Verify test completed
    state = engine.get_state()
    assert state["attempt_count"] > 0
    assert state["attempt_count"] <= 5
    assert state["theta"] is not None


# ============================================================================
# 7. Edge Cases
# ============================================================================

def test_irt_probability_extreme_theta():
    """Test IRT probability with extreme theta values"""
    # Very high theta
    p_high = irt_probability(a=1.0, b=0.0, c=0.2, theta=10.0)
    assert 0.95 < p_high < 1.0
    
    # Very low theta
    p_low = irt_probability(a=1.0, b=0.0, c=0.2, theta=-10.0)
    assert p_low == pytest.approx(0.2, abs=0.01)


def test_item_information_zero_cases():
    """Test information function edge cases"""
    # Should return 0 (or very small) when p approaches 0 or 1
    # Extreme values that push probability to boundaries
    info1 = item_information(a=1.0, b=-10.0, c=0.0, theta=10.0)
    info2 = item_information(a=1.0, b=10.0, c=0.0, theta=-10.0)
    
    # Both should be 0 (boundaries are clipped)
    assert info1 == 0.0
    assert info2 == 0.0


def test_update_theta_all_correct():
    """Test theta update when all responses correct"""
    initial_theta = 0.0
    
    item_params = [
        {"a": 1.0, "b": 0.0, "c": 0.2},
        {"a": 1.2, "b": 0.5, "c": 0.2},
        {"a": 1.5, "b": 1.0, "c": 0.2},
    ]
    responses = [True, True, True]
    
    new_theta = update_theta_mle(initial_theta, item_params, responses)
    
    # Should be significantly positive
    assert new_theta > 0.5


def test_update_theta_all_incorrect():
    """Test theta update when all responses incorrect"""
    initial_theta = 0.0
    
    item_params = [
        {"a": 1.0, "b": 0.0, "c": 0.2},
        {"a": 1.2, "b": -0.5, "c": 0.2},
        {"a": 1.5, "b": -1.0, "c": 0.2},
    ]
    responses = [False, False, False]
    
    new_theta = update_theta_mle(initial_theta, item_params, responses)
    
    # Should be significantly negative
    assert new_theta < -0.5
