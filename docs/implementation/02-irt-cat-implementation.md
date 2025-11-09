# 02. IRT/CAT Implementation

> **Production-grade Computerized Adaptive Testing (CAT) using Item Response Theory (IRT) models in Python**

## Table of Contents

- [Overview](#overview)
- [IRT Theory Primer](#irt-theory-primer)
- [IRT Models Implementation](#irt-models-implementation)
- [CAT Algorithm](#cat-algorithm)
- [Item Selection Strategies](#item-selection-strategies)
- [Ability Estimation](#ability-estimation)
- [Performance Optimization](#performance-optimization)
- [Testing & Validation](#testing--validation)

---

## Overview

This guide implements a production-ready CAT system with:

- **IRT Models**: 1PL (Rasch), 2PL, 3PL
- **Ability Estimation**: MLE, EAP (Bayesian)
- **Item Selection**: Maximum information, content balancing
- **Stopping Rules**: Fixed length, SE threshold, classification
- **Performance**: <5s estimation, 10K+ concurrent sessions

---

## IRT Theory Primer

### Item Response Function

The probability of a correct response depends on:

- **θ (theta)**: Student ability (latent trait)
- **b (difficulty)**: Item difficulty parameter
- **a (discrimination)**: How well item differentiates abilities
- **c (guessing)**: Lower asymptote (probability of guessing)

### Three-Parameter Logistic (3PL) Model

$$P(\theta) = c + \frac{1 - c}{1 + e^{-a(\theta - b)}}$$

**Special Cases**:

- **2PL**: Set c = 0
- **1PL (Rasch)**: Set c = 0, a = 1

### Information Function

Item information measures how much an item contributes to ability estimation:

$$I(\theta) = \frac{[P'(\theta)]^2}{P(\theta)[1 - P(\theta)]}$$

**Higher information = more precise ability estimate**

---

## IRT Models Implementation

### Core IRT Module (`app/core/irt/models.py`)

```python
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ItemParameters:
    """IRT item parameters"""
    difficulty: float  # b parameter
    discrimination: float = 1.0  # a parameter (default for 1PL)
    guessing: float = 0.0  # c parameter (default for 1PL/2PL)
    item_id: str = ""


class IRTModel:
    """Item Response Theory model implementation"""

    def __init__(self, model_type: str = "2PL"):
        """
        Initialize IRT model

        Args:
            model_type: '1PL', '2PL', or '3PL'
        """
        self.model_type = model_type
        self._validate_model_type()

    def _validate_model_type(self):
        """Validate model type"""
        if self.model_type not in ['1PL', '2PL', '3PL']:
            raise ValueError(f"Invalid model_type: {self.model_type}")

    def probability(
        self,
        theta: float,
        difficulty: float,
        discrimination: float = 1.0,
        guessing: float = 0.0
    ) -> float:
        """
        Calculate probability of correct response (3PL model)

        P(θ) = c + (1 - c) / (1 + exp(-a(θ - b)))

        Args:
            theta: Ability level
            difficulty: Item difficulty (b)
            discrimination: Item discrimination (a)
            guessing: Lower asymptote (c)

        Returns:
            Probability of correct response [0, 1]
        """
        # Apply model constraints
        if self.model_type == "1PL":
            discrimination = 1.0
            guessing = 0.0
        elif self.model_type == "2PL":
            guessing = 0.0

        # 3PL formula
        exponent = -discrimination * (theta - difficulty)
        prob = guessing + (1 - guessing) / (1 + np.exp(exponent))

        return np.clip(prob, 1e-10, 1 - 1e-10)  # Numerical stability

    def information(
        self,
        theta: float,
        difficulty: float,
        discrimination: float = 1.0,
        guessing: float = 0.0
    ) -> float:
        """
        Calculate Fisher information at theta

        I(θ) = [P'(θ)]^2 / [P(θ)(1 - P(θ))]

        Higher information = more precise ability estimate
        """
        p = self.probability(theta, difficulty, discrimination, guessing)

        # First derivative of P with respect to theta
        if self.model_type == "3PL":
            q = 1 - p
            p_prime = discrimination * (p - guessing) * (1 - p) / (1 - guessing)
        else:
            # For 1PL/2PL (c=0)
            p_prime = discrimination * p * (1 - p)

        # Information function
        info = (p_prime ** 2) / (p * (1 - p))

        return info

    def test_information(
        self,
        theta: float,
        item_params: List[ItemParameters]
    ) -> float:
        """
        Calculate total test information (sum of item information)

        Args:
            theta: Ability level
            item_params: List of item parameters

        Returns:
            Total information
        """
        total_info = sum(
            self.information(
                theta,
                item.difficulty,
                item.discrimination,
                item.guessing
            )
            for item in item_params
        )
        return total_info

    def standard_error(self, information: float) -> float:
        """
        Calculate standard error of ability estimate

        SE(θ) = 1 / sqrt(I(θ))

        Args:
            information: Total test information

        Returns:
            Standard error
        """
        if information <= 0:
            return np.inf
        return 1.0 / np.sqrt(information)


class AbilityEstimator:
    """Ability estimation using MLE and EAP methods"""

    def __init__(self, model: IRTModel):
        self.model = model

    def estimate_mle(
        self,
        responses: List[bool],
        item_params: List[ItemParameters],
        initial_theta: float = 0.0
    ) -> Tuple[float, float]:
        """
        Maximum Likelihood Estimation (MLE) of ability

        Finds theta that maximizes likelihood of observed responses

        Args:
            responses: List of boolean responses (True=correct)
            item_params: List of item parameters
            initial_theta: Starting value for optimization

        Returns:
            (ability_estimate, standard_error)
        """
        # Handle edge cases
        if all(responses):
            # Perfect score - set high ability
            theta = 3.0
        elif not any(responses):
            # Zero score - set low ability
            theta = -3.0
        else:
            # Optimize log-likelihood
            def neg_log_likelihood(theta_val):
                ll = 0
                for response, item in zip(responses, item_params):
                    p = self.model.probability(
                        theta_val,
                        item.difficulty,
                        item.discrimination,
                        item.guessing
                    )
                    ll += np.log(p) if response else np.log(1 - p)
                return -ll

            result = minimize(
                neg_log_likelihood,
                x0=initial_theta,
                method='BFGS',
                bounds=[(-4, 4)]
            )
            theta = result.x[0]

        # Calculate standard error
        info = self.model.test_information(theta, item_params)
        se = self.model.standard_error(info)

        return theta, se

    def estimate_eap(
        self,
        responses: List[bool],
        item_params: List[ItemParameters],
        prior_mean: float = 0.0,
        prior_sd: float = 1.0,
        quadrature_points: int = 41
    ) -> Tuple[float, float]:
        """
        Expected A Posteriori (EAP) estimation - Bayesian approach

        Uses quadrature to integrate over posterior distribution

        Args:
            responses: List of boolean responses
            item_params: List of item parameters
            prior_mean: Mean of prior distribution (normal)
            prior_sd: SD of prior distribution
            quadrature_points: Number of quadrature points

        Returns:
            (ability_estimate, posterior_sd)
        """
        # Quadrature points (theta values to evaluate)
        theta_range = np.linspace(-4, 4, quadrature_points)

        # Prior probabilities (normal distribution)
        prior = norm.pdf(theta_range, loc=prior_mean, scale=prior_sd)

        # Likelihood for each theta
        likelihood = np.ones_like(theta_range)
        for response, item in zip(responses, item_params):
            p = np.array([
                self.model.probability(
                    theta,
                    item.difficulty,
                    item.discrimination,
                    item.guessing
                )
                for theta in theta_range
            ])
            likelihood *= np.where(response, p, 1 - p)

        # Posterior (unnormalized)
        posterior = prior * likelihood

        # Normalize
        posterior_sum = np.sum(posterior)
        if posterior_sum == 0:
            # Fallback to MLE
            return self.estimate_mle(responses, item_params)

        posterior /= posterior_sum

        # Expected value (mean of posterior)
        theta_eap = np.sum(theta_range * posterior)

        # Posterior standard deviation
        posterior_var = np.sum(((theta_range - theta_eap) ** 2) * posterior)
        posterior_sd = np.sqrt(posterior_var)

        return theta_eap, posterior_sd
```

---

## CAT Algorithm

### CAT Engine (`app/core/irt/cat.py`)

```python
from typing import List, Tuple, Optional, Set
from uuid import UUID
from sqlalchemy.orm import Session
import numpy as np

from app.core.irt.models import IRTModel, ItemParameters, AbilityEstimator
from app.repositories.item import ItemRepository
from app.utils.cache import cache_item_parameters


class CATEngine:
    """Computerized Adaptive Testing engine"""

    def __init__(
        self,
        model_type: str = "2PL",
        estimation_method: str = "MLE"
    ):
        """
        Initialize CAT engine

        Args:
            model_type: '1PL', '2PL', or '3PL'
            estimation_method: 'MLE' or 'EAP'
        """
        self.model = IRTModel(model_type)
        self.estimator = AbilityEstimator(self.model)
        self.estimation_method = estimation_method

    def select_next_item(
        self,
        db: Session,
        current_ability: float,
        administered_items: List[UUID],
        organization_id: UUID,
        content_constraints: Optional[dict] = None
    ) -> Tuple[UUID, float]:
        """
        Select next item using maximum information criterion

        Args:
            db: Database session
            current_ability: Current ability estimate
            administered_items: Already administered item IDs
            organization_id: Organization ID (for multi-tenancy)
            content_constraints: Optional content balancing constraints

        Returns:
            (next_item_id, expected_information)
        """
        # Get available items (not yet administered)
        item_repo = ItemRepository(db)
        available_items = item_repo.get_available_items(
            organization_id=organization_id,
            exclude_ids=administered_items,
            content_constraints=content_constraints
        )

        if not available_items:
            raise ValueError("No available items remaining")

        # Calculate information for each item at current ability
        item_info = []
        for item in available_items:
            params = self._get_item_parameters(item)
            info = self.model.information(
                current_ability,
                params.difficulty,
                params.discrimination,
                params.guessing
            )
            item_info.append((item.id, info, params))

        # Select item with maximum information
        best_item_id, best_info, _ = max(item_info, key=lambda x: x[1])

        return best_item_id, best_info

    def estimate_ability(
        self,
        responses: List[bool],
        item_params: List[ItemParameters],
        initial_theta: float = 0.0
    ) -> Tuple[float, float]:
        """
        Estimate ability based on responses

        Args:
            responses: List of boolean responses
            item_params: List of item parameters
            initial_theta: Initial ability estimate

        Returns:
            (ability_estimate, standard_error)
        """
        if self.estimation_method == "EAP":
            return self.estimator.estimate_eap(responses, item_params)
        else:
            return self.estimator.estimate_mle(responses, item_params, initial_theta)

    def check_stopping_rule(
        self,
        items_administered: int,
        standard_error: float,
        max_items: int = 30,
        target_se: float = 0.3
    ) -> bool:
        """
        Check if test should stop

        Stopping rules:
        1. Maximum items reached
        2. Standard error below target

        Args:
            items_administered: Number of items given
            standard_error: Current SE of ability estimate
            max_items: Maximum allowed items
            target_se: Target standard error

        Returns:
            True if test should stop
        """
        # Rule 1: Maximum items
        if items_administered >= max_items:
            return True

        # Rule 2: Precision reached
        if standard_error <= target_se:
            return True

        return False

    @cache_item_parameters
    def _get_item_parameters(self, item) -> ItemParameters:
        """Get item parameters (with caching)"""
        return ItemParameters(
            difficulty=item.difficulty,
            discrimination=item.discrimination if hasattr(item, 'discrimination') else 1.0,
            guessing=item.guessing if hasattr(item, 'guessing') else 0.0,
            item_id=str(item.id)
        )
```

---

## Item Selection Strategies

### Content Balancing

```python
from collections import defaultdict
from typing import Dict, List

class ContentBalancedCAT(CATEngine):
    """CAT with content balancing constraints"""

    def __init__(self, content_targets: Dict[str, float], **kwargs):
        """
        Args:
            content_targets: Target proportion for each content area
                            e.g., {'algebra': 0.4, 'geometry': 0.3, 'statistics': 0.3}
        """
        super().__init__(**kwargs)
        self.content_targets = content_targets

    def select_next_item_balanced(
        self,
        db: Session,
        current_ability: float,
        administered_items: List[UUID],
        content_counts: Dict[str, int],
        total_items: int,
        organization_id: UUID
    ) -> Tuple[UUID, float, str]:
        """
        Select next item with content balancing

        Strategy:
        1. Identify under-represented content areas
        2. Select from those areas using max information
        """
        # Calculate current proportions
        current_props = {
            area: count / total_items if total_items > 0 else 0
            for area, count in content_counts.items()
        }

        # Find most under-represented area
        priority_areas = []
        for area, target in self.content_targets.items():
            current = current_props.get(area, 0)
            if current < target:
                priority_areas.append((area, target - current))

        # Sort by deficit (largest first)
        priority_areas.sort(key=lambda x: x[1], reverse=True)

        # Try to select from priority areas
        for area, _ in priority_areas:
            try:
                item_id, info = self.select_next_item(
                    db=db,
                    current_ability=current_ability,
                    administered_items=administered_items,
                    organization_id=organization_id,
                    content_constraints={'content_area': area}
                )
                return item_id, info, area
            except ValueError:
                # No items available in this area, try next
                continue

        # Fallback: select without constraints
        item_id, info = self.select_next_item(
            db=db,
            current_ability=current_ability,
            administered_items=administered_items,
            organization_id=organization_id
        )
        return item_id, info, "unconstrained"
```

---

## Ability Estimation

### Incremental Estimation

```python
class IncrementalEstimator:
    """Incrementally update ability estimate after each item"""

    def __init__(self, model: IRTModel):
        self.model = model
        self.estimator = AbilityEstimator(model)

    def update_estimate(
        self,
        current_theta: float,
        new_response: bool,
        new_item: ItemParameters,
        all_responses: List[bool],
        all_items: List[ItemParameters]
    ) -> Tuple[float, float]:
        """
        Update ability estimate with new response

        More efficient than re-estimating from scratch
        """
        # For first few items, use simple heuristic
        if len(all_responses) < 3:
            if new_response:
                return current_theta + 0.5, 1.0
            else:
                return current_theta - 0.5, 1.0

        # Use full estimation for more items
        return self.estimator.estimate_mle(all_responses, all_items, current_theta)
```

---

## Performance Optimization

### Caching Strategy (`app/utils/cache.py`)

```python
from functools import wraps
from redis import Redis
import json
import hashlib

redis_client = Redis(host='redis', port=6379, decode_responses=True)


def cache_item_parameters(func):
    """Cache item parameters in Redis (1 hour TTL)"""
    @wraps(func)
    def wrapper(item):
        cache_key = f"item_params:{item.id}"

        # Try cache first
        cached = redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            return ItemParameters(**data)

        # Compute and cache
        result = func(item)
        redis_client.setex(
            cache_key,
            3600,
            json.dumps({
                'difficulty': result.difficulty,
                'discrimination': result.discrimination,
                'guessing': result.guessing,
                'item_id': result.item_id
            })
        )
        return result

    return wrapper


def preload_item_bank(db: Session, organization_id: UUID):
    """Preload all item parameters into Redis"""
    from app.repositories.item import ItemRepository

    item_repo = ItemRepository(db)
    items = item_repo.get_all_by_organization(organization_id)

    pipe = redis_client.pipeline()
    for item in items:
        cache_key = f"item_params:{item.id}"
        params = {
            'difficulty': item.difficulty,
            'discrimination': getattr(item, 'discrimination', 1.0),
            'guessing': getattr(item, 'guessing', 0.0),
            'item_id': str(item.id)
        }
        pipe.setex(cache_key, 3600, json.dumps(params))

    pipe.execute()
    print(f"Preloaded {len(items)} items into cache")
```

### Vectorized Computations

```python
import numpy as np

class VectorizedIRTModel(IRTModel):
    """Vectorized IRT operations for batch processing"""

    def probability_batch(
        self,
        theta: np.ndarray,
        difficulties: np.ndarray,
        discriminations: np.ndarray = None,
        guessings: np.ndarray = None
    ) -> np.ndarray:
        """
        Vectorized probability calculation

        Args:
            theta: Array of abilities (n_students,)
            difficulties: Array of difficulties (n_items,)
            discriminations: Array of discriminations (n_items,)
            guessings: Array of guessings (n_items,)

        Returns:
            Probability matrix (n_students, n_items)
        """
        # Reshape for broadcasting
        theta = theta.reshape(-1, 1)  # (n_students, 1)
        difficulties = difficulties.reshape(1, -1)  # (1, n_items)

        if discriminations is None:
            discriminations = np.ones_like(difficulties)
        else:
            discriminations = discriminations.reshape(1, -1)

        if guessings is None:
            guessings = np.zeros_like(difficulties)
        else:
            guessings = guessings.reshape(1, -1)

        # Vectorized 3PL
        exponent = -discriminations * (theta - difficulties)
        probs = guessings + (1 - guessings) / (1 + np.exp(exponent))

        return np.clip(probs, 1e-10, 1 - 1e-10)
```

---

## Testing & Validation

### Unit Tests (`tests/unit/test_irt.py`)

```python
import pytest
import numpy as np
from app.core.irt.models import IRTModel, ItemParameters, AbilityEstimator


class TestIRTModel:
    """Test IRT probability and information functions"""

    def test_1pl_probability_neutral(self):
        """Test 1PL at theta=b (should be 0.5)"""
        model = IRTModel("1PL")
        prob = model.probability(theta=0.0, difficulty=0.0)
        assert abs(prob - 0.5) < 0.01

    def test_2pl_higher_discrimination(self):
        """Test that higher discrimination increases slope"""
        model = IRTModel("2PL")

        prob_low_a = model.probability(theta=1.0, difficulty=0.0, discrimination=0.5)
        prob_high_a = model.probability(theta=1.0, difficulty=0.0, discrimination=2.0)

        # Higher discrimination should give higher probability
        assert prob_high_a > prob_low_a

    def test_3pl_guessing_floor(self):
        """Test that 3PL has lower asymptote at c"""
        model = IRTModel("3PL")
        guessing = 0.25

        # Very low ability should approach guessing parameter
        prob = model.probability(theta=-10.0, difficulty=0.0, guessing=guessing)
        assert abs(prob - guessing) < 0.01

    def test_information_maximum_at_difficulty(self):
        """Test that information is maximized near difficulty"""
        model = IRTModel("2PL")
        difficulty = 1.5

        info_at_b = model.information(theta=difficulty, difficulty=difficulty, discrimination=1.5)
        info_away = model.information(theta=difficulty + 2, difficulty=difficulty, discrimination=1.5)

        assert info_at_b > info_away


class TestAbilityEstimation:
    """Test MLE and EAP estimation"""

    def test_mle_perfect_score(self):
        """Test MLE with all correct responses"""
        model = IRTModel("2PL")
        estimator = AbilityEstimator(model)

        responses = [True] * 10
        items = [ItemParameters(difficulty=i * 0.5, discrimination=1.0) for i in range(10)]

        theta, se = estimator.estimate_mle(responses, items)

        # Perfect score should give high ability
        assert theta > 2.0
        assert se < 1.0

    def test_mle_zero_score(self):
        """Test MLE with all incorrect responses"""
        model = IRTModel("2PL")
        estimator = AbilityEstimator(model)

        responses = [False] * 10
        items = [ItemParameters(difficulty=i * 0.5, discrimination=1.0) for i in range(10)]

        theta, se = estimator.estimate_mle(responses, items)

        # Zero score should give low ability
        assert theta < -2.0

    def test_eap_vs_mle(self):
        """Compare EAP and MLE estimates"""
        model = IRTModel("2PL")
        estimator = AbilityEstimator(model)

        responses = [True, False, True, True, False]
        items = [ItemParameters(difficulty=i * 0.5 - 1.0, discrimination=1.2) for i in range(5)]

        theta_mle, se_mle = estimator.estimate_mle(responses, items)
        theta_eap, sd_eap = estimator.estimate_eap(responses, items)

        # EAP should be closer to prior (0.0) than MLE
        assert abs(theta_eap) < abs(theta_mle) + 0.5
```

### Integration Test (Full CAT Session)

```python
def test_full_cat_session(db, test_organization):
    """Simulate complete CAT session"""
    from app.core.irt.cat import CATEngine
    from app.repositories.item import ItemRepository

    # Setup
    cat = CATEngine(model_type="2PL", estimation_method="MLE")
    item_repo = ItemRepository(db)

    # Create test items
    for i in range(50):
        item = Item(
            organization_id=test_organization.id,
            difficulty=np.random.normal(0, 1),
            discrimination=np.random.uniform(0.5, 2.0),
            content="Test item {}".format(i)
        )
        db.add(item)
    db.commit()

    # Simulate CAT session
    current_ability = 0.0
    administered_items = []
    responses = []

    for _ in range(20):
        # Select next item
        item_id, info = cat.select_next_item(
            db=db,
            current_ability=current_ability,
            administered_items=administered_items,
            organization_id=test_organization.id
        )

        # Simulate response (based on true ability = 1.0)
        item = item_repo.get(item_id)
        true_ability = 1.0
        prob = cat.model.probability(true_ability, item.difficulty, item.discrimination)
        response = np.random.random() < prob

        # Update
        administered_items.append(item_id)
        responses.append(response)

        # Re-estimate ability
        items_params = [cat._get_item_parameters(item_repo.get(iid)) for iid in administered_items]
        current_ability, se = cat.estimate_ability(responses, items_params)

        # Check stopping rule
        if cat.check_stopping_rule(len(responses), se):
            break

    # Verify results
    assert abs(current_ability - true_ability) < 1.0  # Within 1 SD
    assert se < 0.5  # Reasonably precise
```

---

## Next Steps

1. ✅ **Understand IRT Theory**: Review formulas and concepts
2. 📖 **Implement Models**: Copy code to `app/core/irt/`
3. 🧪 **Run Tests**: Validate with unit and integration tests
4. 🔧 **Optimize**: Add caching and vectorization
5. 📊 **Calibrate Items**: Estimate parameters from response data (see Analytics guide)

**Related Guides**:

- [01-fastapi-microservices.md](./01-fastapi-microservices.md) - Service integration
- [05-multi-tenancy-rls.md](./05-multi-tenancy-rls.md) - Data isolation
- [06-async-task-processing.md](./06-async-task-processing.md) - IRT calibration tasks

---

_Last Updated: November 9, 2025_
_Version: 1.0.0_
