"""
Week 3 CAT Service - Interface to adaptive_engine for exam sessions

This service provides a clean interface between the exam API and the
existing CAT/IRT engine in adaptive_engine/.

Now integrates with mirt-aligned EAP theta estimation for production use.

Responsibilities:
1. Select next item based on current theta
2. Update theta after each response using EAP (mirt-compatible)
3. Determine termination criteria
4. Calculate final scores
"""

from __future__ import annotations
import math
from typing import Optional, Sequence, List

from app.models.exam_models import (
    Exam,
    ExamItem,
    ExamSession,
    ExamSessionResponse,
)
from app.models.item import Item  # Primary model
from app.services.irt_eap_estimator import (
    IRTResponse,
    estimate_theta_eap,
)


class CatSelectionResult:
    """
    Result of CAT item selection
    """

    def __init__(
        self, item: Item, terminate: bool = False, reason: Optional[str] = None
    ):
        self.item = item
        self.terminate = terminate
        self.reason = reason


async def select_next_item_for_session(
    exam: Exam,
    session: ExamSession,
    responses: Sequence[ExamSessionResponse],
    exam_items: Sequence[ExamItem],
) -> Optional[CatSelectionResult]:
    """
    Select the next item for an adaptive exam session.

    CAT Algorithm (Placeholder - TODO: Connect to adaptive_engine):
    1. Filter out already-answered items
    2. Calculate information function for each candidate
    3. Select item with maximum information at current theta
    4. Check termination criteria (SE < 0.3 or max questions)

    Args:
        exam: Exam metadata
        session: Current exam session
        responses: List of responses so far
        exam_items: Available items in exam pool

    Returns:
        CatSelectionResult with next item, or None if no more items
    """
    # Get already answered item IDs
    answered_item_ids = {r.item_id for r in responses}

    # Filter remaining items
    remaining_exam_items = [
        ei for ei in exam_items if ei.item_id not in answered_item_ids
    ]

    if not remaining_exam_items:
        return None

    # Check max questions
    if len(responses) >= exam.max_questions:
        return CatSelectionResult(
            item=remaining_exam_items[0].item, terminate=True, reason="max_questions"
        )

    # Check SE convergence (if theta_se is available)
    if session.theta_se is not None and session.theta_se < 0.3:
        return CatSelectionResult(
            item=remaining_exam_items[0].item, terminate=True, reason="se_converged"
        )

    # TODO: Connect to actual adaptive_engine
    # For now, use simple difficulty-based selection:
    # Select item closest to current theta estimate
    current_theta = session.theta

    best_item: Optional[ExamItem] = None
    best_info = -1.0

    for ei in remaining_exam_items:
        item = ei.item
        # IRT 3PL information function
        # I(θ) = a² * P(θ) * (1 - P(θ)) / (1 - c)²
        # P(θ) = c + (1 - c) / (1 + exp(-a * (θ - b)))

        a = item.a_discrimination
        b = item.b_difficulty
        c = item.c_guessing

        # Calculate probability
        exponent = -a * (current_theta - b)
        if exponent > 20:  # Prevent overflow
            exponent = 20
        elif exponent < -20:
            exponent = -20

        p_theta = c + (1 - c) / (1 + math.exp(exponent))

        # Calculate information
        if p_theta <= 0 or p_theta >= 1:
            info = 0.0
        else:
            numerator = a * a * p_theta * (1 - p_theta)
            denominator = (1 - c) * (1 - c) if c < 1.0 else 1.0
            info = numerator / denominator if denominator > 0 else 0.0

        if info > best_info:
            best_info = info
            best_item = ei

    if best_item is None:
        # Fallback: just pick first item
        best_item = remaining_exam_items[0]

    return CatSelectionResult(item=best_item.item, terminate=False)


async def build_irt_responses_for_session(
    responses: Sequence[ExamSessionResponse],
    new_item: Optional[Item] = None,
    is_correct: Optional[bool] = None,
) -> List[IRTResponse]:
    """
    Convert ExamSessionResponse records to IRTResponse list for EAP estimation.

    Args:
        responses: Previous responses from session
        new_item: Optional new item to append
        is_correct: Optional correctness for new item

    Returns:
        List of IRTResponse objects
    """
    irt_responses: List[IRTResponse] = []

    # Add all previous responses
    for resp in responses:
        irt_responses.append(
            IRTResponse(
                a=resp.item.a_discrimination,
                b=resp.item.b_difficulty,
                c=resp.item.c_guessing,
                u=1 if resp.is_correct else 0,
            )
        )

    # Add new response if provided
    if new_item is not None and is_correct is not None:
        irt_responses.append(
            IRTResponse(
                a=new_item.a_discrimination,
                b=new_item.b_difficulty,
                c=new_item.c_guessing,
                u=1 if is_correct else 0,
            )
        )

    return irt_responses


async def update_theta_for_response(
    session: ExamSession,
    responses: Sequence[ExamSessionResponse],
    new_item: Item,
    is_correct: bool,
) -> tuple[float, float]:
    """
    Update theta estimate using mirt-aligned EAP method.

    This is the PRODUCTION implementation that:
    1. Collects all responses (including the new one)
    2. Calls irt_eap_estimator.estimate_theta_eap()
    3. Returns (theta_hat, theta_se)

    The results should match R mirt's fscores(..., method="EAP") within 0.01.

    Args:
        session: Current exam session
        responses: All previous responses (excluding current one)
        new_item: Item that was just answered
        is_correct: Whether answer was correct

    Returns:
        Tuple of (new_theta, new_theta_se)

    Note:
        This replaces the previous placeholder implementation.
        For offline calibration of (a, b, c) parameters, use R mirt package.
    """
    # Build IRTResponse list
    irt_responses = await build_irt_responses_for_session(
        responses=responses,
        new_item=new_item,
        is_correct=is_correct,
    )

    # Call mirt-aligned EAP estimator
    eap_result = estimate_theta_eap(
        responses=irt_responses,
        prior_mean=0.0,  # Standard normal prior
        prior_sd=1.0,
    )

    return eap_result.theta, eap_result.se


async def calculate_raw_score(
    session: ExamSession,
    responses: Sequence[ExamSessionResponse],
) -> float:
    """
    Calculate raw score (sum of correct * max_score).

    Args:
        session: Exam session
        responses: List of responses

    Returns:
        Raw score (0.0 to total_possible)
    """
    raw_score = 0.0
    for resp in responses:
        if resp.is_correct:
            # Assuming max_score = 1.0 per item for now
            # In future, could load item.max_score
            raw_score += 1.0

    return raw_score


def calculate_scaled_score(
    theta: float,
    score_min: float = 0.0,
    score_max: float = 100.0,
    theta_min: float = -3.0,
    theta_max: float = 3.0,
) -> float:
    """
    Convert theta to scaled score (e.g., 0-100).

    Formula: score = min + (theta - theta_min) / (theta_max - theta_min) * (max - min)

    Args:
        theta: IRT ability estimate
        score_min: Minimum score
        score_max: Maximum score
        theta_min: Minimum expected theta
        theta_max: Maximum expected theta

    Returns:
        Scaled score
    """
    if theta < theta_min:
        theta = theta_min
    elif theta > theta_max:
        theta = theta_max

    score = score_min + (theta - theta_min) / (theta_max - theta_min) * (
        score_max - score_min
    )
    return round(score, 2)


# TODO: Future enhancements
# 1. Connect to adaptive_engine/exam_engine.py for actual CAT logic
# 2. Implement content balancing (topic distribution)
# 3. Implement exposure control (item usage tracking)
# 4. Add multi-stage adaptive testing support
# 5. Implement Bayesian theta estimation (MAP)
