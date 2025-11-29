"""
DreamSeedAI - IRT/CAT Adaptive Testing Engine (Initial Template)

This module defines the core computational logic for adaptive testing:
- IRT probability function
- Item information function
- Ability (theta) update via MLE / Bayesian EAP
- Adaptive item selection
- Termination conditions
- Session update helpers

This is a clean template that can be expanded into the full adaptive engine.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any
import math

# ---------------------------------------------------------------------------
# 1. IRT Utility Functions (3PL Model)
# ---------------------------------------------------------------------------

def irt_probability(a: float, b: float, c: float, theta: float) -> float:
    """
    Compute probability of correct response using 3PL model.
    
    P(theta) = c + (1-c) / (1 + exp(-a(theta - b)))
    
    Args:
        a: Discrimination parameter (typically 0.5-2.5)
        b: Difficulty parameter (typically -3 to +3)
        c: Guessing parameter (typically 0-0.3)
        theta: Ability estimate (typically -3 to +3)
        
    Returns:
        Probability of correct response (0 to 1)
    """
    # Prevent overflow by clipping exponent
    exponent = -a * (theta - b)
    if exponent > 20:  # exp(20) is very large
        return c
    elif exponent < -20:  # exp(-20) is very small
        return 1.0
    
    try:
        return c + (1 - c) / (1 + math.exp(exponent))
    except OverflowError:
        # Fallback for extreme values
        return c if exponent > 0 else 1.0


def item_information(a: float, b: float, c: float, theta: float) -> float:
    """
    Fisher Information for 3PL model.
    
    I(theta) = (a^2) * ((P-c)^2)/((1-c)^2 * P*(1-P))
    
    Higher information = more precise ability estimation.
    
    Args:
        a: Discrimination parameter
        b: Difficulty parameter
        c: Guessing parameter
        theta: Ability estimate
        
    Returns:
        Information value (higher = more informative)
    """
    p = irt_probability(a, b, c, theta)
    
    # Safety checks
    if p <= 0.001 or p >= 0.999:  # Near boundaries
        return 0.0
    if abs(p - c) < 0.001:  # p ≈ c (at guessing level)
        return 0.0
    if abs(1 - c) < 0.001:  # Degenerate case
        return 0.0
    
    denominator = ((1 - c) ** 2) * p * (1 - p)
    if abs(denominator) < 1e-10:
        return 0.0
    
    return (a ** 2) * ((p - c) ** 2) / denominator


# ---------------------------------------------------------------------------
# 2. Ability Update (Newton-Raphson MLE)
# ---------------------------------------------------------------------------

def update_theta_mle(
    theta: float,
    item_params: List[Dict[str, float]],
    responses: List[bool],
    max_iter: int = 10
) -> float:
    """
    Update theta using Newton-Raphson Maximum Likelihood Estimation.
    
    Iteratively refines ability estimate based on item responses.
    
    Args:
        theta: Current ability estimate
        item_params: List of dicts [{"a":..., "b":..., "c":...}, ...]
        responses: List of booleans (True=correct, False=incorrect)
        max_iter: Maximum iterations for convergence
        
    Returns:
        Updated theta estimate (bounded to [-4, 4])
    """
    curr_theta = max(-4.0, min(4.0, theta))  # Bound initial theta

    for _ in range(max_iter):
        gradient = 0.0
        hessian = 0.0

        for params, correct in zip(item_params, responses):
            a, b, c = params["a"], params["b"], params["c"]
            p = irt_probability(a, b, c, curr_theta)

            # Safety checks for denominators
            if correct:
                if abs(p - c) < 1e-6:  # Avoid division by zero
                    continue
                grad_i = a * (1 - p) / (p - c)
            else:
                if abs(1 - p) < 1e-6:  # Avoid division by zero
                    continue
                grad_i = -a * p / (1 - p)
            gradient += grad_i

            # Second derivative (Hessian)
            hess_i = -(a ** 2) * p * (1 - p)
            hessian += hess_i

        if abs(hessian) < 1e-6:
            break

        step = gradient / hessian
        # Limit step size to prevent wild jumps
        step = max(-1.0, min(1.0, step))
        curr_theta -= step
        
        # Bound theta to reasonable range
        curr_theta = max(-4.0, min(4.0, curr_theta))

        if abs(step) < 1e-3:
            break

    return curr_theta


# ---------------------------------------------------------------------------
# 3. Termination Conditions
# ---------------------------------------------------------------------------

def should_terminate(
    standard_error: Optional[float],
    attempt_count: int,
    max_items: int = 20
) -> bool:
    """
    Termination rule for adaptive test.
    
    Stops when:
    - Standard error < 0.3 (sufficient precision)
    - Or attempt_count >= max_items (maximum length reached)
    
    Args:
        standard_error: Current SE of theta estimate (lower = more precise)
        attempt_count: Number of items administered
        max_items: Maximum items allowed
        
    Returns:
        True if test should terminate
    """
    if standard_error is not None and standard_error < 0.3:
        return True
    if attempt_count >= max_items:
        return True
    return False


# ---------------------------------------------------------------------------
# 4. Item Selection (Simplified)
# ---------------------------------------------------------------------------

def select_next_item(
    theta: float,
    available_items: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Select item that maximizes information at current theta.
    
    Uses maximum information criterion: pick item with highest
    Fisher information at current ability estimate.
    
    Args:
        theta: Current ability estimate
        available_items: List of item metadata dicts with keys:
          {"id": int, "a": float, "b": float, "c": float}
          
    Returns:
        Selected item dict, or None if no items available
    """
    if not available_items:
        return None
        
    best_item = None
    best_info = -1

    for item in available_items:
        info = item_information(item["a"], item["b"], item["c"], theta)
        if info > best_info:
            best_info = info
            best_item = item

    return best_item


# ---------------------------------------------------------------------------
# 5. Session Update Helpers
# ---------------------------------------------------------------------------

def update_session_after_attempt(
    theta: float,
    item_params_list: List[Dict[str, float]],
    responses: List[bool]
) -> Dict[str, Optional[float]]:
    """
    Update session theta & standard error after new attempt.
    
    Recalculates ability estimate and precision based on all
    administered items.
    
    Args:
        theta: Current ability estimate
        item_params_list: All item parameters administered so far
        responses: All responses so far
        
    Returns:
        Dict with updated {"theta": float, "standard_error": float}
    """
    new_theta = update_theta_mle(theta, item_params_list, responses)

    # Standard error = 1 / sqrt(sum information)
    total_info = sum(
        item_information(p["a"], p["b"], p["c"], new_theta)
        for p in item_params_list
    )
    new_se = 1 / math.sqrt(total_info) if total_info > 0 else None

    return {"theta": new_theta, "standard_error": new_se}


# ---------------------------------------------------------------------------
# 6. High-Level Engine Interface (for FastAPI integration)
# ---------------------------------------------------------------------------

class AdaptiveEngine:
    """
    High-level CAT (Computerized Adaptive Testing) engine wrapper.
    
    This class maintains session state and provides methods for:
    - Recording item responses
    - Updating ability estimates
    - Selecting next items
    - Checking termination conditions
    
    Usage:
        engine = AdaptiveEngine(initial_theta=0.0)
        
        # Record attempt
        updated = engine.record_attempt(
            params={"a": 1.2, "b": 0.5, "c": 0.2},
            correct=True
        )
        
        # Pick next item
        next_item = engine.pick_item(available_items)
        
        # Check if should stop
        if engine.should_stop(max_items=20):
            # Terminate test
            pass
    """

    def __init__(self, initial_theta: float = 0.0):
        """
        Initialize adaptive engine.
        
        Args:
            initial_theta: Starting ability estimate (default: 0.0 = average)
        """
        self.theta = initial_theta
        self.responses: List[bool] = []
        self.item_params_list: List[Dict[str, float]] = []

    def record_attempt(
        self,
        params: Dict[str, float],
        correct: bool
    ) -> Dict[str, Optional[float]]:
        """
        Store item parameters & correctness and update ability.
        
        Args:
            params: Item parameters {"a": float, "b": float, "c": float}
            correct: Whether response was correct
            
        Returns:
            Updated {"theta": float, "standard_error": float | None}
        """
        self.item_params_list.append(params)
        self.responses.append(correct)

        updated = update_session_after_attempt(
            self.theta, self.item_params_list, self.responses
        )

        self.theta = updated["theta"] or 0.0  # Fallback to 0.0 if None
        return updated

    def pick_item(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Pick next item based on current theta.
        
        Args:
            items: Available items with IRT parameters
            
        Returns:
            Selected item dict, or None if no items available
        """
        return select_next_item(self.theta, items)

    def should_stop(self, max_items: int = 20) -> bool:
        """
        Check if test should terminate.
        
        Args:
            max_items: Maximum items to administer
            
        Returns:
            True if stopping criteria met
        """
        se = None
        current_theta = self.theta  # Use current theta value
        if self.item_params_list:
            total_info = sum(
                item_information(p["a"], p["b"], p["c"], current_theta)
                for p in self.item_params_list
            )
            se = 1 / math.sqrt(total_info) if total_info > 0 else None
        return should_terminate(se, len(self.responses), max_items)

    def get_state(self) -> Dict[str, Any]:
        """
        Get current engine state.
        
        Returns:
            Dict with theta, SE, attempt count, responses
        """
        se = None
        current_theta = self.theta  # Use current theta value
        if self.item_params_list:
            total_info = sum(
                item_information(p["a"], p["b"], p["c"], current_theta)
                for p in self.item_params_list
            )
            se = 1 / math.sqrt(total_info) if total_info > 0 else None

        return {
            "theta": current_theta,
            "standard_error": se,
            "attempt_count": len(self.responses),
            "correct_count": sum(self.responses),
            "accuracy": sum(self.responses) / len(self.responses) if self.responses else None,
        }
