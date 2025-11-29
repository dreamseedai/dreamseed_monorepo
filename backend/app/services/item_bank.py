"""
item_bank.py

DreamSeedAI – ItemBank Service

This module provides:
 - Item lookup for adaptive testing
 - Filtering by difficulty, topic, subject
 - Exclusion of previously attempted items
 - Candidate sampling and sorting by information value
 - Hooks for exposure control & content balancing

Integrated with:
 - app.models.core_models_expanded.Item
 - app.services.exam_engine.AdaptiveEngine (uses item_information function)

Usage:
    bank = ItemBankService(db_session)
    candidates = await bank.get_candidate_items(
        exam_session_id=1,
        theta=0.5,
        subject="mathematics",
        topic="algebra"
    )
    best_item = bank.pick_best_item(candidates)
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.core_models_expanded import Item, Attempt
from app.services.exam_engine import item_information


class ItemBankService:
    """
    High-level service for retrieving items for CAT (Computerized Adaptive Testing).
    
    Supports:
     - Difficulty filtering (theta window)
     - Exclusion of previously attempted items
     - Subject/topic filtering
     - Information-based ranking
     - Exposure control (optional)
    
    Usage:
        bank = ItemBankService(db)
        candidates = await bank.get_candidate_items(
            exam_session_id=1,
            theta=0.5
        )
        next_item = bank.pick_best_item(candidates)
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize ItemBank service.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    # ------------------------------------------------------------------
    # 1. Load unattempted items
    # ------------------------------------------------------------------
    async def load_unattempted_items(
        self,
        exam_session_id: int,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> List[Item]:
        """
        Load items not yet attempted in this session.
        
        Supports optional subject/topic filters.
        
        Args:
            exam_session_id: ID of the exam session
            subject: Optional subject filter (from item.meta['subject'])
            topic: Optional topic filter (from item.topic)
        
        Returns:
            List of Item ORM objects not yet attempted
        
        Example:
            items = await bank.load_unattempted_items(
                exam_session_id=1,
                subject="mathematics",
                topic="algebra_linear_equations"
            )
        """
        # Fetch attempted item IDs
        stmt_attempted = select(Attempt.item_id).where(
            Attempt.exam_session_id == exam_session_id
        )
        result = await self.session.execute(stmt_attempted)
        attempted_ids = [row[0] for row in result.all()]

        # Base query: Items excluding attempted
        if attempted_ids:
            stmt_items = select(Item).where(Item.id.not_in(attempted_ids))
        else:
            stmt_items = select(Item)

        # Optional subject filter (from JSON meta field)
        if subject:
            # PostgreSQL JSONB query
            stmt_items = stmt_items.where(
                Item.meta["subject"].astext == subject
            )

        # Optional topic filter
        if topic:
            stmt_items = stmt_items.where(Item.topic == topic)

        result = await self.session.execute(stmt_items)
        return result.scalars().all()

    # ------------------------------------------------------------------
    # 2. Difficulty window filtering
    # ------------------------------------------------------------------
    def filter_by_difficulty(
        self,
        items: List[Item],
        theta: float,
        window: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        Filter items by difficulty window: |b - theta| <= window
        
        Items with difficulty parameter 'b' close to current theta
        are more informative for ability estimation.
        
        Args:
            items: List of Item ORM objects
            theta: Current ability estimate
            window: Difficulty window size (default: 1.0)
        
        Returns:
            List of dicts with IRT params and item ID
        
        Example:
            # Only keep items within ±1.0 of current theta
            filtered = bank.filter_by_difficulty(
                items=raw_items,
                theta=0.5,
                window=1.0
            )
            # Result: items with b in range [-0.5, 1.5]
        """
        filtered = []
        for it in items:
            b = float(it.b)
            if abs(b - theta) <= window:
                filtered.append({
                    "id": it.id,
                    "a": float(it.a),
                    "b": float(it.b),
                    "c": float(it.c),
                    "topic": it.topic,
                })
        return filtered

    # ------------------------------------------------------------------
    # 3. Information-based ranking
    # ------------------------------------------------------------------
    def rank_by_information(
        self,
        theta: float,
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank candidate items by Fisher information at current theta.
        
        Items providing maximum information are ranked first.
        This implements the core CAT item selection strategy.
        
        Args:
            theta: Current ability estimate
            items: List of item dicts with IRT parameters
        
        Returns:
            List of items sorted by information (descending)
        
        Example:
            ranked = bank.rank_by_information(
                theta=0.5,
                items=[
                    {"id": 1, "a": 1.5, "b": 0.2, "c": 0.2},
                    {"id": 2, "a": 1.2, "b": 0.8, "c": 0.25}
                ]
            )
            # ranked[0] = item with highest information at theta=0.5
        """
        ranked = []
        for it in items:
            # Calculate Fisher information at current theta
            info = item_information(it["a"], it["b"], it["c"], theta)
            ranked.append({**it, "info": info})
        
        # Sort by information (descending)
        ranked.sort(key=lambda x: x["info"], reverse=True)
        return ranked

    # ------------------------------------------------------------------
    # 4. Combine steps: full candidate selection
    # ------------------------------------------------------------------
    async def get_candidate_items(
        self,
        exam_session_id: int,
        theta: float,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty_window: float = 1.0,
        max_candidates: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Complete pipeline: Load unattempted items → difficulty filter → info rank.
        
        This is the main method for adaptive item selection.
        
        Args:
            exam_session_id: ID of the exam session
            theta: Current ability estimate
            subject: Optional subject filter
            topic: Optional topic filter
            difficulty_window: Window for difficulty filtering (default: 1.0)
            max_candidates: Optional limit on number of candidates returned
        
        Returns:
            List of item dicts ranked by information, with 'info' field added
        
        Example:
            candidates = await bank.get_candidate_items(
                exam_session_id=1,
                theta=0.5,
                subject="mathematics",
                difficulty_window=1.5
            )
            # Returns: [
            #   {"id": 5, "a": 1.5, "b": 0.6, "c": 0.2, "info": 0.85},
            #   {"id": 3, "a": 1.2, "b": 0.3, "c": 0.25, "info": 0.72},
            #   ...
            # ]
        """
        # Step 1: Load unattempted items
        raw_items = await self.load_unattempted_items(
            exam_session_id=exam_session_id,
            subject=subject,
            topic=topic
        )

        if not raw_items:
            return []

        # Step 2: Apply difficulty window filter
        candidates = self.filter_by_difficulty(
            items=raw_items,
            theta=theta,
            window=difficulty_window
        )

        # If difficulty filter is too strict, fall back to all items
        if not candidates:
            candidates = [
                {
                    "id": it.id,
                    "a": float(it.a),
                    "b": float(it.b),
                    "c": float(it.c),
                    "topic": it.topic,
                }
                for it in raw_items
            ]

        # Step 3: Rank by information
        ranked = self.rank_by_information(theta, candidates)

        # Optional: Limit number of candidates
        if max_candidates and len(ranked) > max_candidates:
            ranked = ranked[:max_candidates]

        return ranked

    # ------------------------------------------------------------------
    # 5. Pick the best item
    # ------------------------------------------------------------------
    def pick_best_item(
        self,
        ranked_items: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Select the best item from ranked candidates.
        
        By default, returns the item with highest information.
        Can be extended for exposure control or content balancing.
        
        Args:
            ranked_items: List of items ranked by information
        
        Returns:
            Best item dict or None if no candidates
        
        Example:
            best = bank.pick_best_item(candidates)
            if best:
                print(f"Selected item {best['id']} with info {best['info']:.3f}")
        """
        if not ranked_items:
            return None
        
        # Simple strategy: pick item with maximum information
        return ranked_items[0]

    # ------------------------------------------------------------------
    # 6. Exposure control (advanced)
    # ------------------------------------------------------------------
    async def pick_item_with_exposure_control(
        self,
        ranked_items: List[Dict[str, Any]],
        max_exposure: float = 0.2,
        randomization_window: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """
        Select item with exposure control strategy.
        
        Instead of always picking the maximum information item,
        randomly select from top N items to prevent overexposure.
        
        Args:
            ranked_items: List of items ranked by information
            max_exposure: Maximum exposure rate per item (0.0-1.0)
            randomization_window: Number of top items to consider
        
        Returns:
            Selected item dict or None
        
        Note:
            This is a placeholder for advanced exposure control.
            Full implementation would track item usage across all sessions.
        """
        if not ranked_items:
            return None

        # Simple randomization: pick from top N items
        import random
        window_size = min(randomization_window, len(ranked_items))
        candidates = ranked_items[:window_size]
        
        # TODO: Implement actual exposure tracking
        # For now, just use weighted random selection based on information
        weights = [item["info"] for item in candidates]
        selected = random.choices(candidates, weights=weights, k=1)[0]
        
        return selected

    # ------------------------------------------------------------------
    # 7. Content balancing
    # ------------------------------------------------------------------
    async def pick_item_with_content_balance(
        self,
        exam_session_id: int,
        ranked_items: List[Dict[str, Any]],
        target_distribution: Dict[str, float],
    ) -> Optional[Dict[str, Any]]:
        """
        Select item while maintaining content balance across topics.
        
        Ensures exam covers topics according to target distribution.
        
        Args:
            exam_session_id: ID of the exam session
            ranked_items: List of items ranked by information
            target_distribution: Dict mapping topic -> target proportion
                Example: {"algebra": 0.4, "geometry": 0.3, "statistics": 0.3}
        
        Returns:
            Selected item dict or None
        
        Example:
            best = await bank.pick_item_with_content_balance(
                exam_session_id=1,
                ranked_items=candidates,
                target_distribution={
                    "algebra": 0.5,
                    "geometry": 0.3,
                    "statistics": 0.2
                }
            )
        """
        if not ranked_items:
            return None

        # Count current topic distribution
        stmt = select(Attempt.item_id).where(
            Attempt.exam_session_id == exam_session_id
        )
        result = await self.session.execute(stmt)
        attempted_ids = [row[0] for row in result.all()]

        # Load attempted items to count topics
        if attempted_ids:
            stmt = select(Item).where(Item.id.in_(attempted_ids))
            result = await self.session.execute(stmt)
            attempted_items = result.scalars().all()
            
            topic_counts = {}
            for item in attempted_items:
                topic = item.topic or "unknown"
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            total_attempts = len(attempted_items)
        else:
            topic_counts = {}
            total_attempts = 0

        # Calculate which topics are underrepresented
        topic_deficits = {}
        for topic, target_prop in target_distribution.items():
            current_prop = topic_counts.get(topic, 0) / max(total_attempts, 1)
            deficit = target_prop - current_prop
            topic_deficits[topic] = deficit

        # Find most underrepresented topic
        most_needed_topic = max(topic_deficits.items(), key=lambda x: x[1])[0]

        # Try to select item from most needed topic
        for item in ranked_items:
            if item.get("topic") == most_needed_topic:
                return item

        # If no item from needed topic, fall back to best item
        return ranked_items[0]


# ----------------------------------------------------------------------
# Integration Example with Adaptive Exam Router
# ----------------------------------------------------------------------
"""
Example integration in api/routers/adaptive_exam.py:

@router.get("/next")
async def get_next_item(
    exam_session_id: int,
    session: AsyncSession = Depends(get_db),
):
    # Load exam session
    exam_sess = await load_exam_session(exam_session_id, session)
    
    # Use ItemBank service
    bank = ItemBankService(session)
    candidates = await bank.get_candidate_items(
        exam_session_id=exam_session_id,
        theta=float(exam_sess.theta),
        subject="mathematics",
        difficulty_window=1.5
    )
    
    # Pick best item
    best_item = bank.pick_best_item(candidates)
    
    if not best_item:
        return {"completed": True, "message": "No items available"}
    
    # Load full item from DB
    stmt = select(Item).where(Item.id == best_item["id"])
    item = (await session.execute(stmt)).scalar_one()
    
    return {
        "item": {
            "id": item.id,
            "question_text": item.question_text,
            "meta": item.meta
        },
        "info": best_item["info"],
        "theta": float(exam_sess.theta)
    }
"""
