"""
R Plumber GLMM Analytics Client for SeedTest API

This client provides async methods to interact with the R Plumber microservice
for advanced statistical analysis (GLMM).
"""

import httpx
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class RPlumberClient:
    """Client for R Plumber GLMM Analytics Service"""
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        internal_token: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        Initialize R Plumber client
        
        Args:
            base_url: Base URL of R Plumber service (e.g., http://r-glmm-plumber:8000)
            timeout: Request timeout in seconds
            internal_token: Optional internal authentication token
            max_retries: Number of retries for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.internal_token = internal_token
        self.max_retries = max_retries
    
    def _headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {"Content-Type": "application/json"}
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json_data: Optional JSON payload
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPStatusError: For HTTP error responses
            httpx.RequestError: For network errors
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method == "GET":
                        response = await client.get(url, headers=self._headers())
                    elif method == "POST":
                        response = await client.post(
                            url, json=json_data, headers=self._headers()
                        )
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.RequestError as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"R Plumber request failed after {self.max_retries} attempts: {e}")
                    raise
                logger.warning(f"R Plumber request attempt {attempt + 1} failed, retrying...")
                continue
    
    async def health(self) -> Dict[str, Any]:
        """
        Check service health
        
        Returns:
            Health status dict with status, service, version, etc.
        """
        return await self._request("GET", "/healthz")
    
    async def glmm_fit(
        self,
        observations: List[Dict[str, Any]],
        formula: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fit binomial GLMM model
        
        Args:
            observations: List of observation dicts with keys:
                - student_id: str
                - item_id: str
                - correct: int (0 or 1)
            formula: Optional R formula string
                (default: "correct ~ 1 + (1|student_id) + (1|item_id)")
        
        Returns:
            Dict with:
                - success: bool
                - model: Compact model representation
                - summary: Model summary statistics
                - warnings: List of warning messages (if any)
        
        Example:
            result = await client.glmm_fit([
                {"student_id": "s1", "item_id": "i1", "correct": 1},
                {"student_id": "s1", "item_id": "i2", "correct": 0},
            ])
        """
        payload: Dict[str, Any] = {"observations": observations}
        if formula:
            payload["formula"] = formula
        
        return await self._request("POST", "/glmm/fit", payload)
    
    async def glmm_predict(
        self,
        model: Dict[str, Any],
        newdata: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Make predictions from GLMM model
        
        Args:
            model: Compact model from glmm_fit()
            newdata: List of new observation dicts with keys:
                - student_id: str
                - item_id: str
        
        Returns:
            Dict with:
                - success: bool
                - predictions: List of probabilities
                - n_predictions: int
        
        Example:
            result = await client.glmm_predict(
                model=fitted_model,
                newdata=[{"student_id": "s1", "item_id": "i3"}]
            )
        """
        payload = {"model": model, "newdata": newdata}
        return await self._request("POST", "/glmm/predict", payload)
    
    async def forecast_summary(
        self,
        mean: float,
        sd: float,
        target: float
    ) -> Dict[str, Any]:
        """
        Calculate forecast probabilities using Normal approximation
        
        Args:
            mean: Mean of the distribution
            sd: Standard deviation (must be positive)
            target: Target value
        
        Returns:
            Dict with:
                - success: bool
                - z_score: float
                - prob_above: float
                - prob_below: float
                - prob_match_approx: float
        
        Example:
            result = await client.forecast_summary(
                mean=0.7, sd=0.1, target=0.8
            )
        """
        payload = {"mean": mean, "sd": sd, "target": target}
        return await self._request("POST", "/forecast/summary", payload)
    
    async def glmm_diagnose(
        self,
        observations: List[Dict[str, Any]],
        formula: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get model diagnostics without full model return
        
        Args:
            observations: Same as glmm_fit()
            formula: Optional R formula
        
        Returns:
            Dict with:
                - success: bool
                - convergence: int (0 = converged)
                - n_obs: int
                - n_groups: dict
                - aic: float
                - bic: float
                - warnings: list
        """
        payload: Dict[str, Any] = {"observations": observations}
        if formula:
            payload["formula"] = formula
        
        return await self._request("POST", "/glmm/diagnose", payload)


# Factory function for dependency injection
def create_r_plumber_client(
    base_url: str,
    internal_token: Optional[str] = None,
    timeout: float = 30.0
) -> RPlumberClient:
    """
    Factory function to create R Plumber client
    
    Usage in FastAPI:
        from apps.seedtest_api.clients.r_plumber import create_r_plumber_client
        
        client = create_r_plumber_client(
            base_url=settings.R_PLUMBER_BASE_URL,
            internal_token=settings.R_PLUMBER_INTERNAL_TOKEN
        )
    """
    return RPlumberClient(
        base_url=base_url,
        timeout=timeout,
        internal_token=internal_token
    )

