"""
Extended R Plumber GLMM Analytics Client

Additional methods for advanced analysis endpoints.
"""

from typing import Any, Dict, List, Optional
from .r_plumber import RPlumberClient


class ExtendedRPlumberClient(RPlumberClient):
    """Extended client with additional analysis endpoints"""
    
    async def glmm_ranef(
        self,
        model: Dict[str, Any],
        group: str,
        ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get random effects for specific groups
        
        Args:
            model: Compact model from glmm_fit()
            group: Group name ("student_id" or "item_id")
            ids: Optional list of specific IDs to return
        
        Returns:
            Dict with random_effects for the specified group
        """
        payload: Dict[str, Any] = {"model": model, "group": group}
        if ids:
            payload["ids"] = ids
        
        return await self._request("POST", "/glmm/ranef", payload)
    
    async def glmm_coef(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get model coefficients summary
        
        Args:
            model: Compact model from glmm_fit()
        
        Returns:
            Dict with fixed_effects and random_effects_summary
        """
        payload = {"model": model}
        return await self._request("POST", "/glmm/coef", payload)
    
    async def student_abilities(
        self,
        model: Dict[str, Any],
        student_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Batch estimate student abilities
        
        Args:
            model: Compact GLMM model
            student_ids: List of student IDs
        
        Returns:
            Dict with abilities dict and summary statistics
        """
        payload = {"model": model, "student_ids": student_ids}
        return await self._request("POST", "/analysis/student-abilities", payload)
    
    async def item_difficulties(
        self,
        model: Dict[str, Any],
        item_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Batch estimate item difficulties
        
        Args:
            model: Compact GLMM model
            item_ids: List of item IDs
        
        Returns:
            Dict with difficulties dict and summary statistics
        """
        payload = {"model": model, "item_ids": item_ids}
        return await self._request("POST", "/analysis/item-difficulties", payload)
    
    async def expected_scores(
        self,
        model: Dict[str, Any],
        student_id: str,
        item_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate expected scores for a student on specific items
        
        Args:
            model: Compact GLMM model
            student_id: Student ID
            item_ids: List of item IDs
        
        Returns:
            Dict with expected_scores, total, and average
        """
        payload = {
            "model": model,
            "student_id": student_id,
            "item_ids": item_ids
        }
        return await self._request("POST", "/analysis/expected-scores", payload)
    
    async def recommend_items(
        self,
        model: Dict[str, Any],
        student_id: str,
        item_pool: List[str],
        target_probability: float = 0.7,
        n_items: int = 5
    ) -> Dict[str, Any]:
        """
        Recommend items based on target difficulty
        
        Args:
            model: Compact GLMM model
            student_id: Student ID
            item_pool: List of available item IDs
            target_probability: Target success probability (default 0.7)
            n_items: Number of items to recommend (default 5)
        
        Returns:
            Dict with recommended_items and expected_probabilities
        """
        payload = {
            "model": model,
            "student_id": student_id,
            "item_pool": item_pool,
            "target_probability": target_probability,
            "n_items": n_items
        }
        return await self._request("POST", "/analysis/recommend-items", payload)
    
    async def model_compare(
        self,
        observations: List[Dict[str, Any]],
        formulas: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple model formulas using AIC/BIC
        
        Args:
            observations: Same as glmm_fit()
            formulas: List of R formula strings to compare
        
        Returns:
            Dict with comparisons list and best_model
        """
        payload = {"observations": observations, "formulas": formulas}
        return await self._request("POST", "/analysis/model-compare", payload)


def create_extended_r_plumber_client(
    base_url: str,
    internal_token: Optional[str] = None,
    timeout: float = 30.0
) -> ExtendedRPlumberClient:
    """
    Factory function to create extended R Plumber client
    
    Usage:
        client = create_extended_r_plumber_client(
            base_url=settings.R_PLUMBER_BASE_URL,
            internal_token=settings.R_PLUMBER_INTERNAL_TOKEN
        )
        
        # Student abilities
        abilities = await client.student_abilities(model, ["s1", "s2", "s3"])
        
        # Item recommendations
        recommendations = await client.recommend_items(
            model, "s1", ["i1", "i2", "i3"], target_probability=0.7
        )
    """
    return ExtendedRPlumberClient(
        base_url=base_url,
        timeout=timeout,
        internal_token=internal_token
    )

