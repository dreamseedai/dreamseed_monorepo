from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class BaseEngine:
    """Ability estimation engine contract.

    Implementations should return (theta, standard_error, method_name).
    Inputs are permissive to allow future enrichment without breaking API.
    """

    name: str = "base"

    def estimate_ability(
        self,
        *,
        score_scaled: Optional[float] = None,
        ability_estimate: Optional[float] = None,
        standard_error: Optional[float] = None,
        topics: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[float, Optional[float], str]:
        raise NotImplementedError


class HeuristicEngine(BaseEngine):
    name = "heuristic"

    def estimate_ability(
        self,
        *,
        score_scaled: Optional[float] = None,
        ability_estimate: Optional[float] = None,
        standard_error: Optional[float] = None,
        topics: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[float, Optional[float], str]:
        # Prefer provided ability_estimate when available
        if isinstance(ability_estimate, (int, float)):
            theta = float(ability_estimate)
        else:
            # Simple mapping from scaled score back to theta-like scale
            if isinstance(score_scaled, (int, float)):
                val = float(score_scaled)
                theta = (val - 100.0) / 50.0
            else:
                theta = 0.0
        se = float(standard_error) if isinstance(standard_error, (int, float)) else None
        return theta, se, self.name


class IrtEngine(BaseEngine):
    name = "irt"

    def estimate_ability(
        self,
        *,
        score_scaled: Optional[float] = None,
        ability_estimate: Optional[float] = None,
        standard_error: Optional[float] = None,
        topics: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[float, Optional[float], str]:
        # Placeholder: use a slightly different transform as a stub
        if isinstance(ability_estimate, (int, float)):
            theta = float(ability_estimate)
        elif isinstance(score_scaled, (int, float)):
            # Assume scaled ~ linear transform of theta: scaled = 100 + 60*theta
            theta = (float(score_scaled) - 100.0) / 60.0
        else:
            theta = 0.0
        se = float(standard_error) if isinstance(standard_error, (int, float)) else None
        return theta, se, self.name


class MixedEffectsEngine(BaseEngine):
    name = "mixed_effects"

    def estimate_ability(
        self,
        *,
        score_scaled: Optional[float] = None,
        ability_estimate: Optional[float] = None,
        standard_error: Optional[float] = None,
        topics: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[float, Optional[float], str]:
        # Future: fit/evaluate a mixed-effects model using accumulated responses.
        # For now, fall back to heuristic mapping while signaling method name.
        if isinstance(ability_estimate, (int, float)):
            theta = float(ability_estimate)
        elif isinstance(score_scaled, (int, float)):
            theta = (float(score_scaled) - 100.0) / 50.0
        else:
            theta = 0.0
        se = float(standard_error) if isinstance(standard_error, (int, float)) else None
        return theta, se, self.name


def get_engine(name: str) -> BaseEngine:
    key = (name or "").strip().lower()
    if key == IrtEngine.name:
        return IrtEngine()
    if key == MixedEffectsEngine.name or key.replace("-", "_") == MixedEffectsEngine.name:
        return MixedEffectsEngine()
    # default
    return HeuristicEngine()
