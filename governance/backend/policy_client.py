import os
import logging
from typing import Any, Dict, Optional
from functools import lru_cache

import httpx

logger = logging.getLogger(__name__)

class PolicyEngineClient:
    """OPA Policy Engine client for evaluating policies."""
    
    def __init__(self, opa_url: Optional[str] = None):
        """
        Initialize the PolicyEngineClient.

        Args:
            opa_url: Base URL of the OPA server. If None, will use environment variable OPA_SERVER_URL or default.
        """
        base_url = opa_url or os.getenv("OPA_SERVER_URL", "http://opa-policy-engine.governance.svc.cluster.local:8181")
        self.opa_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=2.0)
        logger.info(f"PolicyEngineClient initialized with OPA base URL: {self.opa_url}")

    async def evaluate(
        self,
        policy_path: str,
        input_data: Optional[Dict[str, Any]] = None,
        return_full_result: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate a policy query against the OPA policy engine.

        Args:
            policy_path: The OPA policy path (e.g., "dreamseedai/access_control/allow" or "dreamseedai.access_control.allow").
            input_data: Input data for the policy evaluation.
            return_full_result: If True, return the full OPA response; if False, return only the policy decision.

        Returns:
            The policy evaluation result. By default, this is a dictionary containing at least an "allow" key.
            If return_full_result is True, the entire response from OPA is returned.
        """
        url = f"{self.opa_url}/v1/data/{policy_path.replace('.', '/')}"
        logger.info(f"Evaluating policy at path '{policy_path}' with input: {input_data}")
        
        try:
            payload = {"input": input_data} if input_data is not None else {"input": {}}
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result_data = response.json()
            
            if return_full_result:
                logger.info(f"Full OPA response for policy '{policy_path}': {result_data}")
                return result_data
            
            # Extract policy decision result
            inner_result = result_data.get("result")
            if inner_result is None:
                logger.error(f"Policy evaluation response missing 'result' field for path '{policy_path}': {result_data}")
                return {"allow": False}
            
            if isinstance(inner_result, bool):
                logger.info(f"Policy decision for '{policy_path}': allow = {inner_result}")
                return {"allow": inner_result}
            
            if isinstance(inner_result, dict):
                if "allow" in inner_result and isinstance(inner_result["allow"], bool):
                    decision = inner_result["allow"]
                    logger.info(f"Policy decision for '{policy_path}': allow = {decision}")
                    return {"allow": decision}
                else:
                    logger.error(f"Policy result for '{policy_path}' does not contain 'allow' boolean: {inner_result}")
                    return {"allow": False}
            
            logger.error(f"Unexpected policy result type for path '{policy_path}': {type(inner_result)}")
            return {"allow": False}
            
        except httpx.TimeoutException as e:
            logger.error(f"Policy evaluation timed out for path '{policy_path}': {e}")
            return {"allow": False}
        except httpx.HTTPError as e:
            logger.error(f"Policy evaluation HTTP error for path '{policy_path}': {e}")
            return {"allow": False}
        except Exception as e:
            logger.error(f"Unexpected error during policy evaluation for path '{policy_path}': {e}")
            return {"allow": False}

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        await self.client.aclose()
        logger.info("PolicyEngineClient HTTP session closed")

@lru_cache
def get_policy_client() -> PolicyEngineClient:
    """정책 클라이언트 싱글톤 인스턴스 반환."""
    return PolicyEngineClient()
