"""
core/services/exam_engine.py

DreamSeedAI - IRT/CAT Adaptive Testing Engine (Initial Template)
This module defines the core computational logic for adaptive testing:
- IRT probability function
- Item information function
- Ability (theta) update via MLE / Bayesian EAP
- Adaptive item selection
- Termination conditions
- Session update helpers

This is a clean template that can be expanded into the full adaptive engine.

Version: 1.0
Created: 2025-11-20
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
    
    Parameters:
        a: discrimination parameter (typically 0.5 - 2.0)
        b: difficulty parameter (typically -3.0 to 3.0)
        c: guessing parameter (typically 0.0 - 0.3)
        theta: ability estimate (typically -3.0 to 3.0)
    
    Returns:
        Probability of correct response (0.0 to 1.0)
    """
    return c + (1 - c) / (1 + math.exp(-a * (theta - b)))


def item_information(a: float, b: float, c: float, theta: float) -> float:
    """
    Fisher Information for 3PL item at given theta.
    
    I(theta) = (a^2) * ((P-c)^2) / ((1-c)^2 * P * (1-P))
    
    Parameters:
        a: discrimination parameter
        b: difficulty parameter
        c: guessing parameter
        theta: ability estimate
    
    Returns:
        Information value (higher = more informative)
    """
    p = irt_probability(a, b, c, theta)
    if p <= 0 or p >= 1:
        return 0.0
    return (a ** 2) * ((p - c) ** 2) / (((1 - c) ** 2) * p * (1 - p))


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
    
    Parameters:
        theta: current ability estimate
        item_params: list of dicts [{"a":..., "b":..., "c":...}, ...]
        responses: list of booleans (True = correct, False = incorrect)
        max_iter: maximum iterations (default 10)
    
    Returns:
        Updated theta estimate
    
    Notes:
        - Uses Newton-Raphson iterative method
        - Converges when step size < 0.001
        - Handles edge cases with hessian near zero
    """
    curr_theta = theta

    for _ in range(max_iter):
        gradient = 0.0
        hessian = 0.0

        for params, correct in zip(item_params, responses):
            a, b, c = params["a"], params["b"], params["c"]
            p = irt_probability(a, b, c, curr_theta)

            # Derivative of log-likelihood
            if correct:
                grad_i = a * (1 - p) / (p - c) if (p - c) > 1e-6 else 0
            else:
                grad_i = -a * p / (1 - p) if (1 - p) > 1e-6 else 0
            gradient += grad_i

            # Second derivative
            hess_i = -(a ** 2) * p * (1 - p)
            hessian += hess_i

        if abs(hessian) < 1e-6:
            break

        step = gradient / hessian
        curr_theta -= step

        if abs(step) < 1e-3:
            break

    return curr_theta


def update_theta_eap(
    item_params: List[Dict[str, float]], 
    responses: List[bool],
    prior_mean: float = 0.0,
    prior_sd: float = 1.0,
    quadrature_points: int = 40
) -> float:
    """
    Update theta using Bayesian Expected A Posteriori (EAP) estimation.
    
    Parameters:
        item_params: list of item parameter dicts
        responses: list of response booleans
        prior_mean: prior distribution mean (default 0.0)
        prior_sd: prior distribution standard deviation (default 1.0)
        quadrature_points: number of quadrature points (default 40)
    
    Returns:
        EAP theta estimate
    
    Notes:
        - More stable than MLE for short tests
        - Uses Gaussian quadrature for integration
        - Incorporates prior knowledge
    """
    # Quadrature points and weights (simplified Gaussian quadrature)
    theta_min = prior_mean - 4 * prior_sd
    theta_max = prior_mean + 4 * prior_sd
    theta_range = theta_max - theta_min
    step = theta_range / (quadrature_points - 1)
    
    theta_points = [theta_min + i * step for i in range(quadrature_points)]
    
    # Compute posterior for each theta point
    posteriors = []
    for theta in theta_points:
        # Prior (Gaussian)
        prior = math.exp(-0.5 * ((theta - prior_mean) / prior_sd) ** 2)
        
        # Likelihood
        likelihood = 1.0
        for params, correct in zip(item_params, responses):
            p = irt_probability(params["a"], params["b"], params["c"], theta)
            likelihood *= p if correct else (1 - p)
        
        posteriors.append(prior * likelihood)
    
    # Normalize
    total = sum(posteriors)
    if total < 1e-10:
        return prior_mean
    
    posteriors = [p / total for p in posteriors]
    
    # EAP = weighted average
    eap_theta = sum(t * p for t, p in zip(theta_points, posteriors))
    return eap_theta


# ---------------------------------------------------------------------------
# 3. Termination Conditions
# ---------------------------------------------------------------------------

def should_terminate(
    standard_error: Optional[float], 
    attempt_count: int, 
    max_items: int = 20,
    target_se: float = 0.3
) -> bool:
    """
    Determine if adaptive test should terminate.
    
    Parameters:
        standard_error: current standard error of theta estimate
        attempt_count: number of items administered
        max_items: maximum number of items allowed (default 20)
        target_se: target standard error threshold (default 0.3)
    
    Returns:
        True if test should stop, False otherwise
    
    Termination Rules:
        1. SE < target_se (sufficient precision achieved)
        2. attempt_count >= max_items (maximum length reached)
    """
    # Precision criterion
    if standard_error is not None and standard_error < target_se:
        return True
    
    # Maximum length criterion
    if attempt_count >= max_items:
        return True
    
    return False


# ---------------------------------------------------------------------------
# 4. Item Selection (Maximum Information)
# ---------------------------------------------------------------------------

def select_next_item(
    theta: float, 
    available_items: List[Dict[str, Any]],
    content_constraints: Optional[Dict[str, int]] = None,
    exposure_control: bool = False,
    exposure_rates: Optional[Dict[int, float]] = None,
    max_exposure_rate: float = 0.3
) -> Optional[Dict[str, Any]]:
    """
    Select item that maximizes information at current theta.
    
    Parameters:
        theta: current ability estimate
        available_items: list of item metadata dicts with keys:
            {"id": int, "a": float, "b": float, "c": float, 
             "content_area": str (optional)}
        content_constraints: dict of {content_area: max_count} (optional)
        exposure_control: whether to apply exposure control (default False)
        exposure_rates: dict of {item_id: exposure_rate} (optional)
        max_exposure_rate: maximum allowed exposure rate (default 0.3)
    
    Returns:
        Selected item dict, or None if no items available
    
    Selection Strategy:
        1. Filter items by content constraints
        2. Filter items by exposure control
        3. Select item with maximum information
    """
    if not available_items:
        return None
    
    # Apply content constraints
    if content_constraints:
        # TODO: Implement content balancing logic
        pass
    
    # Apply exposure control
    if exposure_control and exposure_rates:
        available_items = [
            item for item in available_items
            if exposure_rates.get(item["id"], 0.0) < max_exposure_rate
        ]
    
    # Select item with maximum information
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

def compute_standard_error(
    item_params_list: List[Dict[str, float]], 
    theta: float
) -> Optional[float]:
    """
    Compute standard error of theta estimate.
    
    SE(theta) = 1 / sqrt(sum of item information)
    
    Parameters:
        item_params_list: list of item parameter dicts
        theta: current ability estimate
    
    Returns:
        Standard error, or None if no items
    """
    if not item_params_list:
        return None
    
    total_info = sum(
        item_information(p["a"], p["b"], p["c"], theta) 
        for p in item_params_list
    )
    
    return 1 / math.sqrt(total_info) if total_info > 0 else None


def update_session_after_attempt(
    theta: float,
    item_params_list: List[Dict[str, float]],
    responses: List[bool],
    method: str = "mle"
) -> Dict[str, float]:
    """
    Update session theta & standard error after new attempt.
    
    Parameters:
        theta: current ability estimate
        item_params_list: list of all administered item parameters
        responses: list of all response booleans
        method: estimation method ("mle" or "eap", default "mle")
    
    Returns:
        Dict with keys: {"theta": float, "standard_error": float}
    """
    # Update theta
    if method == "eap":
        new_theta = update_theta_eap(item_params_list, responses)
    else:  # mle
        new_theta = update_theta_mle(theta, item_params_list, responses)
    
    # Compute standard error
    new_se = compute_standard_error(item_params_list, new_theta)
    
    return {
        "theta": new_theta, 
        "standard_error": new_se
    }


# ---------------------------------------------------------------------------
# 6. High-Level Engine Interface (for FastAPI integration)
# ---------------------------------------------------------------------------

class AdaptiveEngine:
    """
    High-level CAT engine wrapper.
    This class will be used by FastAPI routers for exam session management.
    
    Usage:
        engine = AdaptiveEngine(initial_theta=0.0)
        
        # Record each attempt
        result = engine.record_attempt(
            params={"a": 1.5, "b": 0.2, "c": 0.2},
            correct=True
        )
        
        # Get next item
        next_item = engine.pick_item(available_items)
        
        # Check termination
        if engine.should_stop():
            final_theta = engine.theta
    """

    def __init__(
        self, 
        initial_theta: float = 0.0,
        estimation_method: str = "mle",
        max_items: int = 20,
        target_se: float = 0.3
    ):
        """
        Initialize adaptive engine.
        
        Parameters:
            initial_theta: starting ability estimate (default 0.0)
            estimation_method: "mle" or "eap" (default "mle")
            max_items: maximum test length (default 20)
            target_se: target standard error (default 0.3)
        """
        self.theta = initial_theta
        self.estimation_method = estimation_method
        self.max_items = max_items
        self.target_se = target_se
        
        self.responses: List[bool] = []
        self.item_params_list: List[Dict[str, float]] = []
        self.item_ids: List[int] = []

    def record_attempt(
        self, 
        item_id: int,
        params: Dict[str, float], 
        correct: bool
    ) -> Dict[str, float]:
        """
        Store item parameters & correctness and update ability.
        
        Parameters:
            item_id: item identifier
            params: dict with keys {"a", "b", "c"}
            correct: whether response was correct
        
        Returns:
            Dict with updated theta and standard_error
        """
        self.item_ids.append(item_id)
        self.item_params_list.append(params)
        self.responses.append(correct)

        updated = update_session_after_attempt(
            self.theta, 
            self.item_params_list, 
            self.responses,
            method=self.estimation_method
        )

        self.theta = updated["theta"]
        return updated

    def pick_item(
        self, 
        available_items: List[Dict[str, Any]],
        exclude_administered: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Pick next item based on current theta.
        
        Parameters:
            available_items: list of item dicts
            exclude_administered: whether to exclude already administered items
        
        Returns:
            Selected item dict, or None
        """
        if exclude_administered:
            available_items = [
                item for item in available_items 
                if item["id"] not in self.item_ids
            ]
        
        return select_next_item(self.theta, available_items)

    def should_stop(self) -> bool:
        """
        Check if test should terminate.
        
        Returns:
            True if termination criteria met
        """
        se = compute_standard_error(self.item_params_list, self.theta)
        return should_terminate(se, len(self.responses), self.max_items, self.target_se)

    def get_final_score(self, scale_mean: float = 500, scale_sd: float = 100) -> int:
        """
        Convert theta to scaled score.
        
        Parameters:
            scale_mean: mean of scaled score distribution (default 500)
            scale_sd: SD of scaled score distribution (default 100)
        
        Returns:
            Scaled score as integer
        """
        return int(scale_mean + scale_sd * self.theta)

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session.
        
        Returns:
            Dict with session statistics
        """
        se = compute_standard_error(self.item_params_list, self.theta)
        
        return {
            "theta": self.theta,
            "standard_error": se,
            "num_items": len(self.responses),
            "num_correct": sum(self.responses),
            "accuracy": sum(self.responses) / len(self.responses) if self.responses else 0.0,
            "scaled_score": self.get_final_score(),
            "should_terminate": self.should_stop()
        }


# ---------------------------------------------------------------------------
# 7. Example Usage (for testing)
# ---------------------------------------------------------------------------

def example_usage():
    """
    Example of how to use the AdaptiveEngine.
    """
    # Sample item bank
    item_bank = [
        {"id": 1, "a": 1.2, "b": -1.0, "c": 0.2},
        {"id": 2, "a": 1.5, "b": 0.0, "c": 0.25},
        {"id": 3, "a": 1.8, "b": 1.0, "c": 0.2},
        {"id": 4, "a": 1.0, "b": -0.5, "c": 0.2},
        {"id": 5, "a": 2.0, "b": 0.5, "c": 0.25},
    ]
    
    # Initialize engine
    engine = AdaptiveEngine(initial_theta=0.0, max_items=5)
    
    print("=== Adaptive Test Session ===")
    print(f"Initial theta: {engine.theta:.3f}\n")
    
    # Simulate test
    for attempt_num in range(1, 6):
        # Pick next item
        next_item = engine.pick_item(item_bank)
        if not next_item:
            print("No more items available")
            break
        
        print(f"Attempt {attempt_num}:")
        print(f"  Item: {next_item['id']} (b={next_item['b']:.2f})")
        
        # Simulate response (simplified)
        prob = irt_probability(
            next_item["a"], next_item["b"], next_item["c"], engine.theta
        )
        import random
        correct = random.random() < prob
        
        # Record attempt
        result = engine.record_attempt(
            item_id=next_item["id"],
            params={"a": next_item["a"], "b": next_item["b"], "c": next_item["c"]},
            correct=correct
        )
        
        print(f"  Response: {'Correct' if correct else 'Incorrect'}")
        print(f"  Updated theta: {result['theta']:.3f}")
        print(f"  SE: {result['standard_error']:.3f if result['standard_error'] else 'N/A'}")
        
        # Check termination
        if engine.should_stop():
            print("\n  >>> Test terminated (criteria met)")
            break
        print()
    
    # Final summary
    summary = engine.get_session_summary()
    print("\n=== Final Summary ===")
    print(f"Theta: {summary['theta']:.3f}")
    print(f"SE: {summary['standard_error']:.3f if summary['standard_error'] else 'N/A'}")
    print(f"Items: {summary['num_items']}")
    print(f"Correct: {summary['num_correct']}/{summary['num_items']}")
    print(f"Scaled Score: {summary['scaled_score']}")


if __name__ == "__main__":
    example_usage()
