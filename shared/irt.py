"""Item Response Theory (IRT) utilities.

Implements the 3-Parameter Logistic (3PL) item response function (IRF)
and its Fisher item information function (IIF) for use in adaptive testing.

References
----------
- 3PL IRF: P(θ) = c + (1 - c) / (1 + exp(-a(θ - b)))
- 3PL IIF: I(θ) = a^2 * (Q/P) * ((P - c)/(1 - c))^2, where Q = 1 - P

Notes
-----
- Uses a numerically stable sigmoid to avoid overflow in exp for large |a(θ-b)|.
- Returns 0.0 information in edge cases (P∉(0,1) or 1-c≈0) to avoid division by zero.
"""

from __future__ import annotations

import math
from typing import Final, Mapping, Sequence

_EPS: Final[float] = 1e-12


def _sigmoid(x: float) -> float:
    """Numerically stable logistic sigmoid.

    Returns 1 / (1 + exp(-x)) while avoiding overflow for large |x|.
    """
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


def irf_3pl(theta: float, a: float, b: float, c: float = 0.0) -> float:
    """3PL item response function: Probability of correct answer.

    Parameters
    ----------
    theta : float
        Examinee ability.
    a : float
        Discrimination parameter (a > 0 recommended).
    b : float
        Difficulty parameter.
    c : float, optional
        Guessing (lower asymptote), 0 ≤ c < 1. Default 0.0 (2PL).

    Returns
    -------
    float
        Probability of a correct response in [c, 1).
    """
    # Guard c within [0, 1)
    if c < 0.0:
        c = 0.0
    if c >= 1.0:
        # Degenerate: probability is effectively 1.0
        return 1.0

    z = a * (theta - b)
    s = _sigmoid(z)
    # P = c + (1 - c) * s
    return c + (1.0 - c) * s


def item_information_3pl(theta: float, a: float, b: float, c: float = 0.0) -> float:
    """Fisher information of an item at ability theta (3PL model).

    Uses the common form:
        I(θ) = a^2 * (Q / P) * ((P - c) / (1 - c))^2, with Q = 1 - P

    Parameters
    ----------
    theta : float
        Examinee ability.
    a : float
        Discrimination parameter.
    b : float
        Difficulty parameter.
    c : float, optional
        Guessing parameter, 0 ≤ c < 1.

    Returns
    -------
    float
        Fisher information (≥ 0). Returns 0.0 for edge/degenerate cases.
    """
    P = irf_3pl(theta, a, b, c)
    Q = 1.0 - P

    # Avoid division by zero in edge cases
    if P <= 0.0 + _EPS or P >= 1.0 - _EPS:
        return 0.0
    denom = 1.0 - c
    if abs(denom) < 1e-9:
        return 0.0

    return (a * a) * (Q / P) * (((P - c) / denom) ** 2)


__all__ = [
    "irf_3pl",
    "item_information_3pl",
    "item_information_batch",
    "select_next_by_information",
    "mle_theta_fisher",
    "map_theta_fisher",
    "eap_theta",
    "update_test_info_and_se",
]


# ----------------------------
# Batch and selection helpers
# ----------------------------


def item_information_batch(theta: float, items: list[dict]) -> list[float]:
    """Compute item information for a batch of items.

    items: list of dicts with keys {"a", "b", "c" (optional, default 0.0)}.
    Returns a list of information values aligned with the input order.
    """
    infos: list[float] = []
    for it in items:
        a = float(it["a"])  # required
        b = float(it["b"])  # required
        c = float(it.get("c", 0.0))
        infos.append(item_information_3pl(theta, a, b, c))
    return infos


def select_next_by_information(
    theta: float,
    items: list[dict],
    used_ids: set | None = None,
) -> tuple[dict, float, int]:
    """Select the item with maximum information at ability theta.

    Parameters
    ----------
    theta : float
      Current ability estimate.
    items : list[dict]
      Each item dict must contain keys: id (hashable), a, b, optional c.
    used_ids : set | None
      If provided, excludes items whose id is in this set.

    Returns
    -------
    (item, info_value, index)
      The chosen item dict, its information value, and its index in the input list.
    """
    used_ids = used_ids or set()
    best_idx = -1
    best_info = -1.0
    for idx, it in enumerate(items):
        if it.get("id") in used_ids:
            continue
        info = item_information_3pl(
            theta, float(it["a"]), float(it["b"]), float(it.get("c", 0.0))
        )
        if info > best_info:
            best_info = info
            best_idx = idx
    if best_idx < 0:
        raise ValueError("No selectable items (all used or empty pool)")
    return items[best_idx], best_info, best_idx


# ----------------------------
# Theta estimation
# ----------------------------


def _dP_dtheta(theta: float, a: float, b: float, c: float) -> float:
    """First derivative dP/dθ for 3PL.

    dP/dθ = a * (P - c) * (1 - P) / (1 - c)
    """
    P = irf_3pl(theta, a, b, c)
    return a * (P - c) * (1.0 - P) / max(1.0 - c, 1e-12)


def mle_update_one_step(
    theta: float, a: float, b: float, c: float, y: int
) -> tuple[float, float, float, float]:
    """One-step Newton update for MLE using a single item response.

    Parameters
    ----------
    theta : float
        Current ability estimate.
    a, b, c : float
        Item parameters.
    y : int
        Response (1 for correct, 0 for incorrect).

    Returns
    -------
    (theta_new, delta, score, info)
        Updated theta, the applied step, score gradient, and item Fisher information.
    """
    P = irf_3pl(theta, a, b, c)
    P = min(max(P, _EPS), 1.0 - _EPS)
    dP = _dP_dtheta(theta, a, b, c)
    # Score for single Bernoulli observation
    score = (y - P) * (dP / (P * (1.0 - P)))
    info = item_information_3pl(theta, a, b, c)
    if info <= _EPS:
        return theta, 0.0, score, info
    delta = score / info
    return theta + delta, delta, score, info


def mle_theta_fisher(
    items: Sequence[Mapping],
    responses: Sequence[int],
    initial_theta: float = 0.0,
    max_iter: int = 25,
    tol: float = 1e-4,
) -> float:
    """Estimate θ via Fisher scoring (quasi-Newton) for the 3PL model.

    Gradient: g(θ) = Σ (y - P) * dP/(P(1-P)) = Σ a*(y-P)*(P-c)/((1-c)*P)
    Information: I(θ) = Σ I_i(θ) with I_i from item_information_3pl.
    Update: θ_{t+1} = θ_t + g(θ_t) / I(θ_t)
    """
    if len(items) != len(responses):
        raise ValueError("items and responses must have same length")
    theta = float(initial_theta)
    for _ in range(max_iter):
        g = 0.0
        I_tot = 0.0
        for it, y in zip(items, responses):
            a = float(it["a"])  # type: ignore[index]
            b = float(it["b"])  # type: ignore[index]
            c = float(it.get("c", 0.0))  # type: ignore[call-arg]
            P = irf_3pl(theta, a, b, c)
            if P <= _EPS or P >= 1.0 - _EPS:
                continue
            dP = _dP_dtheta(theta, a, b, c)
            g += (y - P) * (dP / (P * (1.0 - P)))
            I_tot += item_information_3pl(theta, a, b, c)
        if I_tot <= _EPS:
            break
        step = g / I_tot
        theta_new = theta + step
        if abs(theta_new - theta) < tol:
            theta = theta_new
            break
        theta = theta_new
    return theta


def map_theta_fisher(
    items: Sequence[Mapping],
    responses: Sequence[int],
    prior_mean: float = 0.0,
    prior_var: float = 1.0,
    initial_theta: float = 0.0,
    max_iter: int = 25,
    tol: float = 1e-4,
) -> float:
    """MAP estimate of θ using Fisher scoring with a Normal prior N(prior_mean, prior_var).

    Update step uses gradient augmented with prior term and information augmented by 1/prior_var:
      theta_{t+1} = theta_t + (g(θ) - (θ - m)/v) / (I(θ) + 1/v)
    """
    if len(items) != len(responses):
        raise ValueError("items and responses must have same length")
    v = max(prior_var, 1e-12)
    theta = float(initial_theta)
    for _ in range(max_iter):
        g = 0.0
        I_tot = 0.0
        for it, y in zip(items, responses):
            a = float(it["a"])  # type: ignore[index]
            b = float(it["b"])  # type: ignore[index]
            c = float(it.get("c", 0.0))  # type: ignore[call-arg]
            P = irf_3pl(theta, a, b, c)
            if P <= _EPS or P >= 1.0 - _EPS:
                continue
            dP = _dP_dtheta(theta, a, b, c)
            g += (y - P) * (dP / (P * (1.0 - P)))
            I_tot += item_information_3pl(theta, a, b, c)
        # Prior adjustments
        g_post = g - (theta - prior_mean) / v
        I_post = I_tot + 1.0 / v
        if I_post <= _EPS:
            break
        step = g_post / I_post
        theta_new = theta + step
        if abs(theta_new - theta) < tol:
            theta = theta_new
            break
        theta = theta_new
    return theta


def update_test_info_and_se(
    theta: float, a: float, b: float, c: float, test_info: float
) -> tuple[float, float]:
    """Accumulate test information with the current item and compute SE.

    Returns (new_test_info, se). SE is 1/sqrt(I) if I > 0 else inf.
    """
    i_item = item_information_3pl(theta, a, b, c)
    new_I = (test_info or 0.0) + i_item
    se = (1.0 / new_I) ** 0.5 if new_I > _EPS else float("inf")
    return new_I, se


def eap_theta(
    items: Sequence[Mapping],
    responses: Sequence[int],
    prior_mean: float = 0.0,
    prior_sd: float = 1.0,
    grid_min: float = -4.0,
    grid_max: float = 4.0,
    grid_n: int = 81,
) -> float:
    """Estimate θ via Expected a Posteriori over a Normal prior N(prior_mean, prior_sd^2).

    Uses a uniform grid and unnormalized posterior weights.
    """
    if len(items) != len(responses):
        raise ValueError("items and responses must have same length")
    if grid_n < 5:
        raise ValueError("grid_n too small")
    step = (grid_max - grid_min) / (grid_n - 1)
    thetas = [grid_min + i * step for i in range(grid_n)]

    def log_prior(t: float) -> float:
        z = (t - prior_mean) / max(prior_sd, 1e-12)
        return -0.5 * (z * z) - math.log(prior_sd) if prior_sd > 0 else -math.inf

    def log_likelihood(t: float) -> float:
        ll = 0.0
        for it, y in zip(items, responses):
            a = float(it["a"])  # type: ignore[index]
            b = float(it["b"])  # type: ignore[index]
            c = float(it.get("c", 0.0))  # type: ignore[call-arg]
            P = irf_3pl(t, a, b, c)
            P = min(max(P, _EPS), 1.0 - _EPS)
            ll += y * math.log(P) + (1 - y) * math.log(1.0 - P)
        return ll

    # Log-sum-exp weighting for numerical stability
    logs = [log_prior(t) + log_likelihood(t) for t in thetas]
    m = max(logs)
    weights = [math.exp(v - m) for v in logs]
    w_sum = sum(weights)
    if w_sum <= 0:
        return prior_mean
    return sum(t * w for t, w in zip(thetas, weights)) / w_sum


# ----------------------------
# NumPy vectorized variants (optional)
# ----------------------------
try:  # pragma: no cover - optional dependency
    import numpy as _np  # type: ignore

    def irf_3pl_np(
        theta: float, a: "_np.ndarray", b: "_np.ndarray", c: "_np.ndarray"
    ) -> "_np.ndarray":
        z = a * (theta - b)
        # Vectorized stable sigmoid
        s = _np.where(
            z >= 0,
            1.0 / (1.0 + _np.exp(-z)),
            _np.exp(z) / (1.0 + _np.exp(z)),
        )
        return c + (1.0 - c) * s

    def item_information_np(
        theta: float, a: "_np.ndarray", b: "_np.ndarray", c: "_np.ndarray"
    ) -> "_np.ndarray":
        P = irf_3pl_np(theta, a, b, c)
        Q = 1.0 - P
        denom = _np.maximum(1.0 - c, 1e-12)
        # Guard P within (0,1)
        P_clip = _np.clip(P, _EPS, 1.0 - _EPS)
        return (a * a) * (Q / P_clip) * (((P - c) / denom) ** 2)

    def item_information_batch_np(theta: float, items: list[dict]) -> "_np.ndarray":
        if not items:
            return _np.array([])
        a = _np.array([float(it["a"]) for it in items])
        b = _np.array([float(it["b"]) for it in items])
        c = _np.array([float(it.get("c", 0.0)) for it in items])
        return item_information_np(theta, a, b, c)

except Exception:  # pragma: no cover - numpy not available
    pass
