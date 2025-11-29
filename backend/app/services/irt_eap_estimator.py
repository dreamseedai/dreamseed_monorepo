"""
IRT EAP (Expected A Posteriori) Theta Estimation
Aligned with mirt R package methodology

This module provides theta estimation using the same approach as:
  library(mirt)
  fscores(mod, method="EAP", full.scores=TRUE)

Key features:
- 3PL IRT model (a, b, c parameters)
- Quadrature-based EAP estimation
- Standard error calculation
- Compatible with mirt calibration results

Usage in production CAT:
    from app.services.irt_eap_estimator import IRTResponse, EAPResult, estimate_theta_eap
    
    responses = [IRTResponse(a=1.2, b=-0.5, c=0.2, u=1), ...]
    result = estimate_theta_eap(responses)
    print(f"θ = {result.theta:.3f}, SE = {result.se:.3f}")
"""

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class IRTResponse:
    """Single item response for EAP estimation."""
    a: float  # Discrimination
    b: float  # Difficulty
    c: float  # Guessing
    u: int    # Response (0 or 1)


@dataclass
class EAPResult:
    """Result of EAP theta estimation."""
    theta: float   # Ability estimate
    se: float      # Standard error


def irt_prob_3pl(theta: float | np.ndarray, a: float, b: float, c: float) -> float | np.ndarray:
    """
    Calculate probability of correct response using 3PL IRT model.
    
    P(θ) = c + (1 - c) / (1 + exp(-a * (θ - b)))
    
    Args:
        theta: Ability parameter(s) (scalar or array)
        a: Discrimination parameter (typically 0.5 - 2.5)
        b: Difficulty parameter (typically -3 to +3)
        c: Guessing parameter (typically 0.15 - 0.25 for 4-option MCQ)
    
    Returns:
        Probability of correct response (same shape as theta)
    
    Note:
        This is identical to mirt's probability function with itemtype="3PL"
    """
    exponent = -a * (theta - b)
    # Clamp exponent to prevent overflow (same as mirt does internally)
    exponent = np.clip(exponent, -20, 20)
    return c + (1.0 - c) / (1.0 + np.exp(exponent))


def irt_information_3pl(theta: float, a: float, b: float, c: float) -> float:
    """
    Calculate Fisher information at theta for 3PL model.
    
    I(θ) = a² * P'(θ)² / (P(θ) * (1 - P(θ)))
    
    For 3PL:
    I(θ) = a² * (P(θ) - c)² / ((1 - c)² * P(θ) * (1 - P(θ)))
    
    Args:
        theta: Ability parameter
        a: Discrimination parameter
        b: Difficulty parameter
        c: Guessing parameter
    
    Returns:
        Fisher information (always >= 0)
    """
    P = irt_prob_3pl(theta, a, b, c)
    
    # Prevent division by zero
    if P <= 0.001 or P >= 0.999:
        return 0.0
    
    numerator = a**2 * (P - c)**2
    denominator = (1.0 - c)**2 * P * (1.0 - P)
    
    return float(numerator / denominator)


def estimate_theta_eap(
    responses: Sequence[IRTResponse],
    prior_mean: float = 0.0,
    prior_sd: float = 1.0,
    grid_min: float = -4.0,
    grid_max: float = 4.0,
    grid_step: float = 0.1,
) -> EAPResult:
    """
    EAP theta estimation compatible with mirt::fscores(method='EAP').
    
    Algorithm:
    1. Define prior distribution N(μ, σ²)
    2. Calculate likelihood for each response pattern
    3. Compute posterior = prior × likelihood (normalized)
    4. EAP estimate = E[θ | responses]
    5. SE = sqrt(Var[θ | responses])
    
    Args:
        responses: Sequence of IRTResponse objects
        prior_mean: Mean of prior distribution (default: 0.0)
        prior_sd: SD of prior distribution (default: 1.0)
        grid_min: Minimum theta value for quadrature
        grid_max: Maximum theta value for quadrature
        grid_step: Step size for theta grid
    
    Returns:
        EAPResult with theta and se
    
    Example:
        >>> responses = [
        ...     IRTResponse(a=1.2, b=-0.5, c=0.2, u=1),
        ...     IRTResponse(a=1.5, b=0.0, c=0.2, u=0),
        ... ]
        >>> result = estimate_theta_eap(responses)
        >>> print(f"θ̂ = {result.theta:.3f}, SE = {result.se:.3f}")
        θ̂ = 0.123, SE = 0.456
    """
    if not responses:
        return EAPResult(theta=prior_mean, se=prior_sd)
    
    # 1. Create theta grid (quadrature points)
    theta_grid = np.arange(grid_min, grid_max + grid_step, grid_step)
    
    # 2. Prior distribution: N(prior_mean, prior_sd²)
    prior = (1.0 / (prior_sd * math.sqrt(2 * math.pi))) * np.exp(
        -0.5 * ((theta_grid - prior_mean) / prior_sd) ** 2
    )
    
    # 3. Likelihood for all responses
    likelihood = np.ones_like(theta_grid)
    
    for r in responses:
        # Vectorized probability calculation
        P = irt_prob_3pl(theta_grid, r.a, r.b, r.c)
        # Multiply likelihood by P(u) for each response
        likelihood *= (P if r.u == 1 else (1.0 - P))
        
    # 4. Posterior = prior × likelihood (unnormalized)
    posterior_unnorm = prior * likelihood
    
    # Normalize
    Z = np.sum(posterior_unnorm)
    if Z <= 0 or not np.isfinite(Z):
        # Degenerate case: numerical instability
        # Fall back to prior
        return EAPResult(theta=prior_mean, se=prior_sd)
    
    posterior = posterior_unnorm / Z
    
    # 5. EAP estimate: E[θ | responses]
    theta_hat = float(np.sum(theta_grid * posterior))
    
    # 6. Standard error: SE = sqrt(Var[θ | responses])
    theta2_hat = float(np.sum(theta_grid**2 * posterior))
    theta_variance = max(theta2_hat - theta_hat**2, 1e-6)  # Clamp to positive
    theta_se = math.sqrt(theta_variance)
    
    return EAPResult(theta=theta_hat, se=theta_se)


def calculate_scaled_score(theta: float, min_score: float = 0.0, max_score: float = 100.0) -> float:
    """
    Convert theta to scaled score (0-100 scale).
    
    Mapping:
        θ = -3.0 → score = 0
        θ =  0.0 → score = 50
        θ = +3.0 → score = 100
    
    Args:
        theta: IRT ability estimate
        min_score: Minimum score value (default: 0)
        max_score: Maximum score value (default: 100)
    
    Returns:
        Scaled score (clamped to [min_score, max_score])
    """
    # Linear transformation: θ ∈ [-3, 3] → score ∈ [0, 100]
    score = 50.0 + (theta / 3.0) * 50.0
    
    # Clamp to valid range
    return max(min_score, min(max_score, score))


def calculate_t_score(theta: float) -> float:
    """
    Convert theta to T-score (mean=50, SD=10).
    
    T = 50 + 10 × θ
    
    Args:
        theta: IRT ability estimate
    
    Returns:
        T-score (typically 20-80 range)
    """
    return 50.0 + 10.0 * theta


def calculate_percentile(theta: float) -> float:
    """
    Convert theta to percentile rank (assuming N(0,1) distribution).
    
    Uses standard normal CDF.
    
    Args:
        theta: IRT ability estimate
    
    Returns:
        Percentile (0-100)
    """
    from scipy.stats import norm
    return float(norm.cdf(theta) * 100.0)


def estimate_termination_se_target(num_items: int, avg_discrimination: float = 1.0) -> float:
    """
    Estimate target SE for CAT termination based on test length.
    
    Rule of thumb:
        SE ≈ 1 / sqrt(n × a²)
    
    Args:
        num_items: Number of items in the test
        avg_discrimination: Average item discrimination (default: 1.0)
    
    Returns:
        Suggested SE threshold for termination
    
    Example:
        >>> estimate_termination_se_target(20, avg_discrimination=1.2)
        0.19245...
    """
    information = num_items * (avg_discrimination ** 2)
    return 1.0 / math.sqrt(information)


if __name__ == "__main__":
    # Example usage and validation
    print("IRT EAP Estimator - Example")
if __name__ == "__main__":
    # Example usage and validation
    print("IRT EAP Estimator - Example")
    print("=" * 50)
    
    # Simulate a short CAT session
    responses = [
        IRTResponse(a=1.2, b=-0.5, c=0.2, u=1),  # Easy item, correct
        IRTResponse(a=1.5, b=0.0, c=0.2, u=1),   # Medium item, correct
        IRTResponse(a=1.8, b=0.5, c=0.2, u=1),   # Hard item, correct
        IRTResponse(a=1.3, b=1.0, c=0.2, u=0),   # Very hard item, incorrect
    ]
    
    print("\nResponses:")
    for i, r in enumerate(responses, 1):
        result = "✓ correct" if r.u == 1 else "✗ incorrect"
        print(f"  Item {i}: a={r.a:.1f}, b={r.b:+.1f}, c={r.c:.1f} → {result}")
    
    eap = estimate_theta_eap(responses)
    
    print(f"\nEAP Estimate:")
    print(f"  θ̂  = {eap.theta:+.3f}")
    print(f"  SE = {eap.se:.3f}")
    print(f"\nScaled Scores:")
    print(f"  0-100 scale: {calculate_scaled_score(eap.theta):.1f}")
    print(f"  T-score:     {calculate_t_score(eap.theta):.1f}")
    print(f"  Percentile:  {calculate_percentile(eap.theta):.1f}%")
    
    print(f"\nTermination Criteria:")
    target_se = estimate_termination_se_target(20, 1.5)
    print(f"  Target SE for 20-item test: {target_se:.3f}")
    print(f"  Current SE: {eap.se:.3f}")
    print(f"  Status: {'✓ Can terminate' if eap.se < target_se else '✗ Continue testing'}")