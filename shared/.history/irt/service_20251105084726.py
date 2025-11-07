"""
IRT Service Layer
=================
Business logic for IRT operations: information curves, test assembly, CAT simulation.

Functions:
- item_info_curve(): Calculate Fisher information for single item
- test_info_curve(): Calculate test information (sum of items)
- fetch_item_info_curves(): Load item curves from database
- fetch_test_info_curve(): Load test curve from database
- optimal_theta_range(): Find optimal ability range for test
- estimate_test_reliability(): Estimate reliability from information curve

Usage:
    from shared.irt.service import fetch_item_info_curves
    
    curves = fetch_item_info_curves(db, item_ids=[1, 2, 3])
    for curve in curves:
        print(f"Item {curve.item_id}: max info = {curve.max_info} at θ = {curve.max_info_theta}")
"""
from typing import List, Optional, Tuple

import numpy as np
from sqlalchemy import text
from sqlalchemy.engine import Connection

from .models import (
    InfoCurvePoint,
    IRTModel,
    ItemInfoCurve,
    TestInfoCurve,
)


# ==============================================================================
# Fisher Information Calculations
# ==============================================================================

def item_info_curve(
    a: float,
    b: float,
    c: Optional[float],
    thetas: np.ndarray,
    model: IRTModel = '2PL'
) -> np.ndarray:
    """
    Calculate Fisher information curve for a single item.
    
    Fisher Information:
        I(θ) = Var[∂log L / ∂θ]
    
    2PL Model:
        P(θ) = 1 / (1 + exp(-a(θ - b)))
        I(θ) = a² P(θ) Q(θ)
    
    3PL Model:
        P(θ) = c + (1-c) / (1 + exp(-a(θ - b)))
        I(θ) = a² (P-c)² / [(1-c)² P Q]
    
    1PL Model:
        P(θ) = 1 / (1 + exp(-(θ - b)))
        I(θ) = P(θ) Q(θ)  [a = 1]
    
    Args:
        a: Discrimination parameter (a > 0)
        b: Difficulty parameter
        c: Guessing parameter (0 ≤ c < 1), None for 1PL/2PL
        thetas: Array of ability levels θ
        model: IRT model type ('1PL', '2PL', '3PL')
    
    Returns:
        Array of Fisher information values I(θ)
    
    Example:
        >>> thetas = np.linspace(-4, 4, 81)
        >>> info = item_info_curve(a=1.5, b=-0.5, c=None, thetas=thetas, model='2PL')
        >>> max_info = info.max()
        >>> max_theta = thetas[info.argmax()]
    """
    # Calculate P(θ)
    if model == '3PL' and c is not None:
        # 3PL with guessing
        P = c + (1 - c) / (1 + np.exp(-a * (thetas - b)))
    else:
        # 1PL or 2PL
        if model == '1PL':
            a = 1.0  # Force discrimination to 1
        P = 1 / (1 + np.exp(-a * (thetas - b)))
    
    Q = 1 - P  # Q(θ) = 1 - P(θ)
    
    # Calculate Fisher information
    if model == '3PL' and c is not None:
        # I(θ) = a² (P-c)² / [(1-c)² P Q]
        numerator = (a ** 2) * ((P - c) ** 2)
        denominator = ((1 - c) ** 2) * P * Q
        # Avoid division by zero
        denominator = np.maximum(denominator, 1e-10)
        I = numerator / denominator
    else:
        # 1PL or 2PL: I(θ) = a² P Q
        I = (a ** 2) * P * Q
    
    return I


def test_info_curve(
    items: List[dict],
    thetas: np.ndarray
) -> np.ndarray:
    """
    Calculate test information curve (sum of item curves).
    
    Test Information:
        I_test(θ) = Σ I_i(θ)
    
    Standard Error of Measurement:
        SEM(θ) = 1 / √I_test(θ)
    
    Args:
        items: List of dicts with keys {a, b, c, model}
        thetas: Array of ability levels θ
    
    Returns:
        Array of test information values I_test(θ)
    
    Example:
        >>> items = [
        ...     {'a': 1.2, 'b': -0.5, 'c': None, 'model': '2PL'},
        ...     {'a': 1.5, 'b': 0.0, 'c': None, 'model': '2PL'},
        ...     {'a': 0.8, 'b': 0.8, 'c': 0.2, 'model': '3PL'}
        ... ]
        >>> thetas = np.linspace(-3, 3, 61)
        >>> test_info = test_info_curve(items, thetas)
        >>> sem = 1 / np.sqrt(test_info)
    """
    test_info = np.zeros_like(thetas)
    
    for item in items:
        item_info = item_info_curve(
            a=item['a'],
            b=item['b'],
            c=item.get('c'),
            thetas=thetas,
            model=item.get('model', '2PL')
        )
        test_info += item_info
    
    return test_info


# ==============================================================================
# Database Operations
# ==============================================================================

def fetch_item_info_curves(
    conn: Connection,
    item_ids: List[int],
    theta_min: float = -4.0,
    theta_max: float = 4.0,
    steps: int = 81
) -> List[ItemInfoCurve]:
    """
    Fetch item information curves from database.
    
    Args:
        conn: SQLAlchemy connection
        item_ids: List of item IDs
        theta_min: Minimum θ value
        theta_max: Maximum θ value
        steps: Number of points on curve
    
    Returns:
        List of ItemInfoCurve objects
    
    Example:
        >>> with engine.connect() as conn:
        ...     curves = fetch_item_info_curves(conn, [1, 2, 3])
        ...     for curve in curves:
        ...         print(f"Item {curve.item_id}: max info = {curve.max_info:.2f}")
    """
    thetas = np.linspace(theta_min, theta_max, steps)
    curves = []
    
    # Load item parameters
    result = conn.execute(
        text("""
            SELECT 
                i.id,
                c.model,
                COALESCE(c.a, 1.0) AS a,
                COALESCE(c.b, 0.0) AS b,
                c.c
            FROM shared_irt.items i
            JOIN shared_irt.item_parameters_current c ON c.item_id = i.id
            WHERE i.id = ANY(:ids)
        """),
        {"ids": item_ids}
    )
    
    rows = result.mappings().all()
    
    for row in rows:
        # Calculate information curve
        info = item_info_curve(
            a=float(row['a']),
            b=float(row['b']),
            c=float(row['c']) if row['c'] is not None else None,
            thetas=thetas,
            model=row['model']
        )
        
        # Find maximum
        max_idx = info.argmax()
        max_info = float(info[max_idx])
        max_info_theta = float(thetas[max_idx])
        
        # Create curve object
        curve = ItemInfoCurve(
            item_id=int(row['id']),
            model=row['model'],
            points=[
                InfoCurvePoint(theta=float(t), info=float(i))
                for t, i in zip(thetas, info)
            ],
            max_info=max_info,
            max_info_theta=max_info_theta
        )
        curves.append(curve)
    
    return curves


def fetch_test_info_curve(
    conn: Connection,
    item_ids: List[int],
    theta_min: float = -4.0,
    theta_max: float = 4.0,
    steps: int = 81
) -> TestInfoCurve:
    """
    Fetch test information curve from database.
    
    Args:
        conn: SQLAlchemy connection
        item_ids: List of item IDs in test
        theta_min: Minimum θ value
        theta_max: Maximum θ value
        steps: Number of points on curve
    
    Returns:
        TestInfoCurve object
    
    Example:
        >>> with engine.connect() as conn:
        ...     test_curve = fetch_test_info_curve(conn, [1, 2, 3, 4, 5])
        ...     print(f"Avg info: {test_curve.avg_info:.2f}")
        ...     sem = 1 / np.sqrt([p.info for p in test_curve.points])
        ...     print(f"Avg SEM: {np.mean(sem):.3f}")
    """
    thetas = np.linspace(theta_min, theta_max, steps)
    
    # Load item parameters
    result = conn.execute(
        text("""
            SELECT 
                i.id,
                c.model,
                COALESCE(c.a, 1.0) AS a,
                COALESCE(c.b, 0.0) AS b,
                c.c
            FROM shared_irt.items i
            JOIN shared_irt.item_parameters_current c ON c.item_id = i.id
            WHERE i.id = ANY(:ids)
        """),
        {"ids": item_ids}
    )
    
    rows = result.mappings().all()
    
    # Build items list
    items = []
    for row in rows:
        items.append({
            'a': float(row['a']),
            'b': float(row['b']),
            'c': float(row['c']) if row['c'] is not None else None,
            'model': row['model']
        })
    
    # Calculate test information
    test_info = test_info_curve(items, thetas)
    
    # Calculate average information
    avg_info = float(np.mean(test_info))
    
    # Create curve object
    curve = TestInfoCurve(
        window_id=0,  # Not associated with specific window
        item_ids=item_ids,
        points=[
            InfoCurvePoint(theta=float(t), info=float(i))
            for t, i in zip(thetas, test_info)
        ],
        avg_info=avg_info
    )
    
    return curve


# ==============================================================================
# Test Assembly Utilities
# ==============================================================================

def optimal_theta_range(
    test_info: np.ndarray,
    thetas: np.ndarray,
    info_threshold: float = 10.0
) -> Tuple[float, float]:
    """
    Find optimal ability range where test provides sufficient information.
    
    Args:
        test_info: Array of test information values
        thetas: Array of corresponding θ values
        info_threshold: Minimum acceptable information (default: 10 → SEM = 0.316)
    
    Returns:
        Tuple of (theta_min, theta_max) for optimal range
    
    Example:
        >>> test_info = test_info_curve(items, thetas)
        >>> theta_min, theta_max = optimal_theta_range(test_info, thetas)
        >>> print(f"Test is reliable for θ ∈ [{theta_min:.2f}, {theta_max:.2f}]")
    """
    above_threshold = test_info >= info_threshold
    
    if not above_threshold.any():
        # No region meets threshold
        return (float(thetas[0]), float(thetas[-1]))
    
    # Find first and last index above threshold
    indices = np.where(above_threshold)[0]
    first_idx = indices[0]
    last_idx = indices[-1]
    
    theta_min = float(thetas[first_idx])
    theta_max = float(thetas[last_idx])
    
    return (theta_min, theta_max)


def estimate_test_reliability(
    test_info: np.ndarray,
    theta_distribution_mean: float = 0.0,
    theta_distribution_sd: float = 1.0
) -> float:
    """
    Estimate test reliability from information curve.
    
    Marginal Reliability:
        ρ = 1 - 1 / (σ²_θ I_avg + 1)
    
    where I_avg is average information weighted by θ distribution.
    
    Args:
        test_info: Array of test information values
        theta_distribution_mean: Mean of θ distribution in population
        theta_distribution_sd: SD of θ distribution in population
    
    Returns:
        Reliability coefficient (0 to 1)
    
    Example:
        >>> test_info = test_info_curve(items, thetas)
        >>> reliability = estimate_test_reliability(test_info)
        >>> print(f"Test reliability: {reliability:.3f}")
    """
    # Average information
    I_avg = float(np.mean(test_info))
    
    # Population variance
    sigma_sq = theta_distribution_sd ** 2
    
    # Marginal reliability
    reliability = 1 - 1 / (sigma_sq * I_avg + 1)
    
    return max(0.0, min(1.0, reliability))  # Clamp to [0, 1]


def standard_error_of_measurement(
    test_info: np.ndarray
) -> np.ndarray:
    """
    Calculate standard error of measurement from test information.
    
    SEM(θ) = 1 / √I_test(θ)
    
    Args:
        test_info: Array of test information values
    
    Returns:
        Array of SEM values
    
    Example:
        >>> test_info = test_info_curve(items, thetas)
        >>> sem = standard_error_of_measurement(test_info)
        >>> print(f"Avg SEM: {np.mean(sem):.3f}")
        >>> print(f"Min SEM: {np.min(sem):.3f} (at θ = {thetas[sem.argmin()]:.2f})")
    """
    # Avoid division by zero
    test_info = np.maximum(test_info, 1e-10)
    sem = 1 / np.sqrt(test_info)
    return sem


# ==============================================================================
# CAT Simulation Utilities
# ==============================================================================

def select_next_item_mfi(
    remaining_items: List[dict],
    theta_current: float
) -> int:
    """
    Select next item using Maximum Fisher Information (MFI) criterion.
    
    Args:
        remaining_items: List of dicts with keys {id, a, b, c, model}
        theta_current: Current ability estimate θ
    
    Returns:
        Index of selected item in remaining_items list
    
    Example:
        >>> remaining = [
        ...     {'id': 1, 'a': 1.2, 'b': -0.5, 'c': None, 'model': '2PL'},
        ...     {'id': 2, 'a': 1.5, 'b': 0.0, 'c': None, 'model': '2PL'}
        ... ]
        >>> idx = select_next_item_mfi(remaining, theta_current=0.2)
        >>> selected_item = remaining[idx]
    """
    max_info = -1.0
    best_idx = 0
    
    thetas = np.array([theta_current])
    
    for idx, item in enumerate(remaining_items):
        info = item_info_curve(
            a=item['a'],
            b=item['b'],
            c=item.get('c'),
            thetas=thetas,
            model=item.get('model', '2PL')
        )[0]
        
        if info > max_info:
            max_info = info
            best_idx = idx
    
    return best_idx


def estimate_theta_eap(
    responses: List[Tuple[dict, bool]],
    prior_mean: float = 0.0,
    prior_sd: float = 1.0,
    quad_points: int = 41
) -> Tuple[float, float]:
    """
    Estimate ability using Expected A Posteriori (EAP) method.
    
    EAP(θ) = ∫ θ L(θ) p(θ) dθ / ∫ L(θ) p(θ) dθ
    
    Args:
        responses: List of (item_dict, is_correct) tuples
        prior_mean: Prior mean μ
        prior_sd: Prior SD σ
        quad_points: Number of quadrature points
    
    Returns:
        Tuple of (theta_estimate, posterior_sd)
    
    Example:
        >>> responses = [
        ...     ({'a': 1.2, 'b': -0.5, 'c': None, 'model': '2PL'}, True),
        ...     ({'a': 1.5, 'b': 0.0, 'c': None, 'model': '2PL'}, False)
        ... ]
        >>> theta_est, theta_sd = estimate_theta_eap(responses)
    """
    # Quadrature points
    thetas = np.linspace(prior_mean - 4 * prior_sd, prior_mean + 4 * prior_sd, quad_points)
    
    # Prior density
    prior = np.exp(-0.5 * ((thetas - prior_mean) / prior_sd) ** 2)
    prior = prior / np.sum(prior)  # Normalize
    
    # Likelihood
    likelihood = np.ones(quad_points)
    
    for item, is_correct in responses:
        # P(θ)
        if item.get('model') == '3PL' and item.get('c') is not None:
            P = item['c'] + (1 - item['c']) / (1 + np.exp(-item['a'] * (thetas - item['b'])))
        else:
            a = item['a'] if item.get('model') != '1PL' else 1.0
            P = 1 / (1 + np.exp(-a * (thetas - item['b'])))
        
        # L(θ|y) = P(θ) if correct, 1-P(θ) if incorrect
        if is_correct:
            likelihood *= P
        else:
            likelihood *= (1 - P)
    
    # Posterior
    posterior = likelihood * prior
    posterior = posterior / np.sum(posterior)  # Normalize
    
    # EAP estimate
    theta_eap = float(np.sum(thetas * posterior))
    
    # Posterior SD
    theta_var = np.sum(((thetas - theta_eap) ** 2) * posterior)
    theta_sd = float(np.sqrt(theta_var))
    
    return (theta_eap, theta_sd)


# ==============================================================================
# Exposure Control
# ==============================================================================

def update_exposure_counts(
    conn: Connection,
    item_ids: List[int],
    increment: int = 1
):
    """
    Update exposure counts for administered items.
    
    Args:
        conn: SQLAlchemy connection
        item_ids: List of item IDs to update
        increment: Count increment (default: 1)
    
    Example:
        >>> with engine.begin() as conn:
        ...     update_exposure_counts(conn, [1, 2, 3])
    """
    conn.execute(
        text("""
            UPDATE shared_irt.items
            SET exposure_count = exposure_count + :inc,
                updated_at = now()
            WHERE id = ANY(:ids)
        """),
        {"ids": item_ids, "inc": increment}
    )


def get_exposure_balanced_items(
    conn: Connection,
    candidate_items: List[int],
    max_exposure_rate: float = 0.3
) -> List[int]:
    """
    Filter items by exposure rate for Sympson-Hetter method.
    
    Args:
        conn: SQLAlchemy connection
        candidate_items: List of candidate item IDs
        max_exposure_rate: Maximum allowed exposure rate
    
    Returns:
        List of eligible item IDs (exposure < max_rate)
    
    Example:
        >>> with engine.connect() as conn:
        ...     candidates = [1, 2, 3, 4, 5]
        ...     eligible = get_exposure_balanced_items(conn, candidates, max_exposure_rate=0.2)
    """
    result = conn.execute(
        text("""
            SELECT 
                i.id,
                i.exposure_count,
                COALESCE(
                    i.exposure_count::float / NULLIF((
                        SELECT SUM(exposure_count) FROM shared_irt.items
                    ), 0),
                    0
                ) AS exposure_rate
            FROM shared_irt.items i
            WHERE i.id = ANY(:ids)
              AND COALESCE(
                  i.exposure_count::float / NULLIF((
                      SELECT SUM(exposure_count) FROM shared_irt.items
                  ), 0),
                  0
              ) <= :max_rate
        """),
        {"ids": candidate_items, "max_rate": max_exposure_rate}
    )
    
    eligible = [row[0] for row in result]
    return eligible
