import numpy as np
from typing import Iterable, Mapping, Tuple
from adaptive_engine.utils.irt_math import irt_probability, fisher_information


def update_theta(
    theta_prev: float,
    a: float,
    b: float,
    c: float,
    correct: bool,
    step_size: float = 0.1,
) -> float:
    """Simple MLE-like gradient update for theta.

    theta_new = theta_prev + step_size * (y - p) * a, clipped to [-4, 4].
    """
    p = irt_probability(theta_prev, a, b, c)
    y = 1.0 if correct else 0.0
    gradient = y - p
    theta_new = theta_prev + step_size * gradient * a
    return float(np.clip(theta_new, -4.0, 4.0))


def estimate_standard_error(theta: float, answered_items: list[dict]) -> float:
    """Estimate standard error via sum Fisher information of answered items.

    answered_items: list of {"info": float}
    """
    if not answered_items:
        return 1.0
    info_sum = float(sum((item.get("info", 0.0) or 0.0) for item in answered_items))
    if info_sum <= 0:
        return 1.0
    return float(np.sqrt(1.0 / info_sum))


# ---- Extended estimators: MLE, MAP, EAP ----


def _clip_theta(theta: float) -> float:
    return float(np.clip(theta, -4.0, 4.0))


def _log_likelihood(theta: float, responses: Iterable[Mapping]) -> float:
    """Log-likelihood for 3PL given responses.

    responses: iterable of mappings with keys: a, b, c, correct (bool or 0/1)
    """
    ll = 0.0
    for r in responses:
        a = float(r.get("a", 1.0))
        b = float(r.get("b", 0.0))
        c = float(r.get("c", 0.2))
        y = 1.0 if bool(r.get("correct", False)) else 0.0
        p = float(irt_probability(theta, a, b, c))
        # numerical safety
        p = float(np.clip(p, 1e-9, 1.0 - 1e-9))
        ll += y * np.log(p) + (1.0 - y) * np.log(1.0 - p)
    return float(ll)


def _log_posterior(
    theta: float, responses: Iterable[Mapping], prior_mu: float, prior_sigma: float
) -> float:
    ll = _log_likelihood(theta, responses)
    # Gaussian prior N(mu, sigma^2)
    if prior_sigma <= 0:
        return ll
    prior_term = -0.5 * ((theta - prior_mu) ** 2) / (prior_sigma**2)
    return float(ll + prior_term)


def _num_grad_hess(func, theta: float, eps: float = 1e-4) -> Tuple[float, float]:
    """Numerical first and second derivatives of scalar function at theta."""
    t_m = theta - eps
    t_p = theta + eps
    f0 = func(theta)
    f_m = func(t_m)
    f_p = func(t_p)
    # central difference
    grad = (f_p - f_m) / (2.0 * eps)
    hess = (f_p - 2.0 * f0 + f_m) / (eps**2)
    return float(grad), float(hess)


def mle_theta_newton(
    responses: Iterable[Mapping],
    theta0: float = 0.0,
    max_iter: int = 25,
    tol: float = 1e-4,
) -> float:
    """Compute MLE for theta via Newton–Raphson on log-likelihood (using numeric derivatives).

    - Handles edge cases: if all responses are correct or all incorrect, returns boundary (±4).
    - Returns theta in [-4, 4].
    """
    # Edge-case: empty
    responses = list(responses)
    if not responses:
        return 0.0
    ys = [1.0 if bool(r.get("correct", False)) else 0.0 for r in responses]
    if all(y == 1.0 for y in ys):
        return 4.0
    if all(y == 0.0 for y in ys):
        return -4.0

    theta = float(theta0)
    f = lambda t: _log_likelihood(t, responses)
    for _ in range(max_iter):
        g, h = _num_grad_hess(f, theta)
        if abs(h) < 1e-8:
            break
        step = g / h
        theta_new = theta - step
        theta_new = _clip_theta(theta_new)
        if abs(theta_new - theta) < tol:
            theta = theta_new
            break
        theta = theta_new
    return _clip_theta(theta)


def map_theta_newton(
    responses: Iterable[Mapping],
    theta0: float = 0.0,
    prior_mu: float = 0.0,
    prior_sigma: float = 1.0,
    max_iter: int = 25,
    tol: float = 1e-4,
) -> float:
    """Compute MAP estimate for theta via Newton–Raphson on log-posterior with Gaussian prior.

    Uses numeric derivatives of log-posterior. Returns theta in [-4, 4].
    """
    responses = list(responses)
    if not responses:
        return float(np.clip(prior_mu, -4.0, 4.0))

    theta = float(theta0)
    f = lambda t: _log_posterior(t, responses, prior_mu, prior_sigma)
    for _ in range(max_iter):
        g, h = _num_grad_hess(f, theta)
        if abs(h) < 1e-8:
            break
        step = g / h
        theta_new = theta - step
        theta_new = _clip_theta(theta_new)
        if abs(theta_new - theta) < tol:
            theta = theta_new
            break
        theta = theta_new
    return _clip_theta(theta)


def eap_theta(
    responses: Iterable[Mapping],
    prior_mu: float = 0.0,
    prior_sigma: float = 1.0,
    grid_min: float = -4.0,
    grid_max: float = 4.0,
    grid_points: int = 201,
) -> float:
    """Compute EAP (posterior mean) via grid-based numerical integration.

    Simple and robust for 1D; good for POC/online estimates.
    """
    responses = list(responses)
    if not responses:
        return float(np.clip(prior_mu, -4.0, 4.0))

    thetas = np.linspace(grid_min, grid_max, grid_points)
    # compute unnormalized posterior density at each theta
    logpost = np.array(
        [_log_posterior(float(t), responses, prior_mu, prior_sigma) for t in thetas],
        dtype=float,
    )
    # avoid underflow: subtract max
    logpost -= np.max(logpost)
    w = np.exp(logpost)
    w_sum = float(np.sum(w))
    if w_sum <= 0:
        return float(np.clip(prior_mu, -4.0, 4.0))
    mean = float(np.sum(thetas * w) / w_sum)
    return _clip_theta(mean)


def estimate_theta(
    responses: Iterable[Mapping],
    method: str = "mle",
    theta0: float = 0.0,
    prior_mu: float = 0.0,
    prior_sigma: float = 1.0,
) -> float:
    """Unified API to estimate theta via MLE, MAP, or EAP.

    responses: iterable of mappings with keys {a,b,c,correct}.
    method: 'mle' | 'map' | 'eap'
    """
    m = method.lower()
    if m == "mle":
        return mle_theta_newton(responses, theta0=theta0)
    if m == "map":
        return map_theta_newton(
            responses, theta0=theta0, prior_mu=prior_mu, prior_sigma=prior_sigma
        )
    if m == "eap":
        return eap_theta(responses, prior_mu=prior_mu, prior_sigma=prior_sigma)
    # fallback
    return mle_theta_newton(responses, theta0=theta0)
