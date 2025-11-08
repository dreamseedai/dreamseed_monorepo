from __future__ import annotations

import math
from typing import List, Optional, Tuple

try:
    import numpy as np
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

"""
Growth forecasting utilities.

Initial approach: treat current theta as Normal(mu, sigma^2), simulate next-K exams as i.i.d Normal with reduced uncertainty
(to reflect information gain). Compute probability to exceed target score.

Later: replace with Bayesian updating or bootstrap with empirical improvements.
"""


def _norm_cdf(x: float) -> float:
    """Standard normal CDF using erf (fallback when scipy unavailable)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _safe_norm_cdf(x: float) -> float:
    """Wrapper for normal CDF that uses scipy if available, else fallback."""
    if HAS_SCIPY:
        from scipy.stats import norm as _norm  # type: ignore
        return float(_norm.cdf(x))
    return _norm_cdf(x)


def prob_reach_target(theta_mu: float, theta_se: float, target: float, k: int = 5, shrink: float = 0.7) -> float:
    """
    Estimate probability of reaching target within next k exams.

    theta_mu: current ability estimate
    theta_se: standard error of current estimate
    target: target ability/score threshold to reach
    k: number of future exams to consider
    shrink: factor to reduce SE per exam (information gain). Effective SE for exam t is se * (shrink**t)

    Returns: probability in [0,1]
    """
    if theta_se is None or theta_se <= 0:
        # no uncertainty → step function
        return 1.0 if theta_mu >= target else 0.0

    # simulate K normals with decreasing variance around mu
    # Probability to exceed at least once: 1 - Prod(P(X_t < target))
    probs_lt = []
    for t in range(1, k + 1):
        se_t = theta_se * (shrink ** t)
        z = (target - theta_mu) / se_t
        probs_lt.append(_safe_norm_cdf(z))  # P(X_t < target)
    
    if HAS_SCIPY:
        import numpy as np  # type: ignore
        p_none = float(np.prod(probs_lt))
    else:
        p_none = math.prod(probs_lt)  # Python 3.8+
    
    return max(0.0, min(1.0, 1.0 - p_none))


def forecast_summary(theta_mu: float, theta_se: Optional[float], target: float, k: int = 5) -> dict:
    p = prob_reach_target(theta_mu, theta_se or 0.0, target, k=k)
    return {
        "target": target,
        "horizon": k,
        "probability": p,
    }
