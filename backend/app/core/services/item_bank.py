"""
DreamSeed AI – ItemBank Service

This module provides:
 - Item lookup for adaptive testing
 - Filtering by difficulty, topic, subject
 - Exclusion of previously attempted items
 - Candidate sampling and sorting by information value
 - Hooks for exposure control & content balancing

Integrated with:
 - app.models.item.Item
 - app.models.core_entities.Attempt
 - app.core.services.exam_engine (item_information)
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.core_entities import Attempt
from app.core.services.exam_engine import item_information


class ItemBankService:
    """
    High-level service for retrieving items for CAT (Computerized Adaptive Testing).

    Supports:
     - Difficulty filtering (theta window)
     - Exclusion of previously attempted items
     - Subject/topic filtering
     - Information-based ranking
     - Exposure control hooks
     - Content balancing

    Usage:
        bank = ItemBankService(db)
        candidates = bank.get_candidate_items(
            exam_session_id=123,
            theta=0.5,
            subject="math",
            topic="algebra"
        )
        next_item = bank.pick_best_item(candidates)
    """

    def __init__(self, session: Session):
        """
        Initialize ItemBank service.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. Load Unattempted Items
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def load_unattempted_items(
        self,
        exam_session_id: int,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> List[Item]:
        """
        Load items not yet attempted in this exam session.

        Supports optional filtering by:
        - subject: "math", "english", "science"
        - topic: "algebra", "geometry", "reading_comprehension"

        Args:
            exam_session_id: Current exam session ID
            subject: Optional subject filter
            topic: Optional topic filter

        Returns:
            List of Item objects that haven't been attempted
        """
        # Fetch attempted item IDs for this session
        attempted_ids = (
            self.session.query(Attempt.item_id)
            .filter(Attempt.exam_session_id == exam_session_id)
            .filter(Attempt.item_id.isnot(None))
            .all()
        )
        attempted_ids = [row[0] for row in attempted_ids]

        # Base query: Items excluding attempted ones
        query = self.session.query(Item)

        if attempted_ids:
            query = query.filter(~Item.id.in_(attempted_ids))

        # Apply optional filters
        if subject:
            # Assuming meta JSON contains subject field
            # Alternative: Add subject column to Item model
            query = query.filter(Item.meta["subject"].astext == subject)

        if topic:
            query = query.filter(Item.topic == topic)

        return query.all()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. Difficulty Window Filtering
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def filter_by_difficulty(
        self,
        items: List[Item],
        theta: float,
        window: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        Filter items by difficulty window relative to current ability.

        Keeps items where |b - theta| <= window
        This focuses item selection on items near the student's ability level,
        which provide maximum information.

        Args:
            items: List of Item objects
            theta: Current ability estimate (-4 to +4 typically)
            window: Difficulty window size (default: 1.0)
                   Smaller = more focused, Larger = more variety

        Returns:
            List of item dicts with IRT parameters (a, b, c)
        """
        filtered = []
        for item in items:
            b = float(item.b)
            if abs(b - theta) <= window:
                filtered.append(
                    {
                        "id": item.id,
                        "a": float(item.a),
                        "b": float(item.b),
                        "c": float(item.c),
                    }
                )
        return filtered

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. Information-Based Ranking
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def rank_by_information(
        self, theta: float, items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank candidate items by Fisher information at current theta.

        Fisher information measures how much precision we gain from
        administering an item. Higher information = better measurement.

        The item with maximum information at current theta is optimal
        for reducing standard error most efficiently.

        Args:
            theta: Current ability estimate
            items: List of item dicts with IRT parameters

        Returns:
            List of item dicts sorted by information (highest first)
            Each dict includes 'info' key with Fisher information value
        """
        ranked = []
        for item in items:
            info = item_information(item["a"], item["b"], item["c"], theta)
            ranked.append({**item, "info": info})

        # Sort by information (highest first)
        ranked.sort(key=lambda x: x["info"], reverse=True)
        return ranked

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4. Combined Candidate Selection
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_candidate_items(
        self,
        exam_session_id: int,
        theta: float,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        window: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        Full pipeline: Load unattempted items → difficulty filter → info rank.

        This is the main method for getting candidate items for adaptive testing.

        Pipeline:
        1. Load items not yet attempted in this session
        2. Filter by subject/topic if specified
        3. Filter by difficulty window (|b - theta| <= window)
        4. Rank by Fisher information at current theta
        5. Return sorted list (highest information first)

        Args:
            exam_session_id: Current exam session ID
            theta: Current ability estimate
            subject: Optional subject filter ("math", "english", etc.)
            topic: Optional topic filter ("algebra", "geometry", etc.)
            window: Difficulty window size (default: 1.0)

        Returns:
            List of item dicts sorted by information
            Each dict contains: id, a, b, c, info

        Usage:
            candidates = bank.get_candidate_items(
                exam_session_id=123,
                theta=0.5,
                subject="math",
                topic="algebra",
                window=1.5
            )
            if candidates:
                next_item = candidates[0]  # Highest information
        """
        # Step 1: Load unattempted items
        raw_items = self.load_unattempted_items(exam_session_id, subject, topic)

        if not raw_items:
            return []

        # Step 2: Apply difficulty window filter
        candidates = self.filter_by_difficulty(raw_items, theta, window=window)

        if not candidates:
            # If difficulty filter is too restrictive, fall back to all unattempted
            candidates = [
                {
                    "id": item.id,
                    "a": float(item.a),
                    "b": float(item.b),
                    "c": float(item.c),
                }
                for item in raw_items
            ]

        # Step 3: Rank by Fisher information
        ranked = self.rank_by_information(theta, candidates)
        return ranked

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5. Pick Best Item
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def pick_best_item(
        self, ranked_items: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Select the best item from ranked candidates.

        Currently returns the first item (highest information).

        Future enhancements:
        - Exposure control: Avoid over-using popular items
        - Randomization: Pick from top N items
        - Content balancing: Ensure topic distribution

        Args:
            ranked_items: List of items sorted by information

        Returns:
            Best item dict, or None if no candidates
        """
        if not ranked_items:
            return None
        return ranked_items[0]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6. Exposure Control (Future Enhancement)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def apply_exposure_control(
        self,
        ranked_items: List[Dict[str, Any]],
        max_exposure: float = 0.25,
    ) -> List[Dict[str, Any]]:
        """
        Filter items by exposure rate to prevent overuse.

        Exposure rate = # times item administered / # total exams

        Args:
            ranked_items: List of candidate items
            max_exposure: Maximum exposure rate (default: 0.25 = 25%)

        Returns:
            Filtered list of items below exposure threshold

        Note:
            Requires exposure tracking in database (not yet implemented)
        """
        # TODO: Implement exposure tracking
        # - Add exposure_count column to items table
        # - Calculate exposure rate
        # - Filter items above threshold
        return ranked_items

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 7. Content Balancing (Future Enhancement)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def apply_content_constraints(
        self,
        ranked_items: List[Dict[str, Any]],
        topic_distribution: Dict[str, int],
        current_distribution: Dict[str, int],
    ) -> List[Dict[str, Any]]:
        """
        Filter items to maintain desired topic distribution.

        Example:
            Target: 50% algebra, 30% geometry, 20% calculus
            Current: 40% algebra, 35% geometry, 25% calculus
            → Prefer algebra items to meet target

        Args:
            ranked_items: List of candidate items
            topic_distribution: Desired distribution {topic: count}
            current_distribution: Current distribution {topic: count}

        Returns:
            Filtered list respecting content constraints

        Note:
            Requires topic metadata in Item model
        """
        # TODO: Implement content balancing
        # - Check current vs target distribution
        # - Filter items from over-represented topics
        # - Boost items from under-represented topics
        return ranked_items


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Usage Examples
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
Example 1: Basic usage in adaptive exam router

def get_next_item(exam_session_id: int, theta: float, db: Session):
    bank = ItemBankService(db)
    
    # Get candidate items
    candidates = bank.get_candidate_items(
        exam_session_id=exam_session_id,
        theta=theta
    )
    
    # Pick best item
    next_item = bank.pick_best_item(candidates)
    
    return next_item


Example 2: Subject-specific exam

def get_next_math_item(exam_session_id: int, theta: float, db: Session):
    bank = ItemBankService(db)
    
    # Get math items only
    candidates = bank.get_candidate_items(
        exam_session_id=exam_session_id,
        theta=theta,
        subject="math"
    )
    
    next_item = bank.pick_best_item(candidates)
    return next_item


Example 3: Topic-focused assessment

def get_next_algebra_item(exam_session_id: int, theta: float, db: Session):
    bank = ItemBankService(db)
    
    # Get algebra items with wide difficulty window
    candidates = bank.get_candidate_items(
        exam_session_id=exam_session_id,
        theta=theta,
        subject="math",
        topic="algebra",
        window=1.5  # Wider window for more variety
    )
    
    next_item = bank.pick_best_item(candidates)
    return next_item


Example 4: Integration with AdaptiveEngine

from app.core.services.exam_engine import AdaptiveEngine

def adaptive_exam_flow(exam_session_id: int, db: Session):
    engine = AdaptiveEngine(initial_theta=0.0)
    bank = ItemBankService(db)
    
    while not engine.should_stop():
        # Get state
        state = engine.get_state()
        
        # Select next item
        candidates = bank.get_candidate_items(
            exam_session_id=exam_session_id,
            theta=state["theta"]
        )
        
        if not candidates:
            break
        
        next_item = bank.pick_best_item(candidates)
        
        # Present item to student...
        # Get response...
        correct = get_student_response()
        
        # Update engine
        params = {
            "a": next_item["a"],
            "b": next_item["b"],
            "c": next_item["c"]
        }
        engine.record_attempt(params, correct)
    
    # Get final results
    final_state = engine.get_state()
    return final_state
"""
