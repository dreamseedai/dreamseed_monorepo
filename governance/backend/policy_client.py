import os
import logging
import time
from typing import Any, Dict, Optional
from functools import lru_cache

import httpx

from . import audit_logger

logger = logging.getLogger(__name__)


class PolicyEngineClient:
    """OPA Policy Engine client for evaluating policies."""

    def __init__(self, opa_url: Optional[str] = None):
        """
        Initialize the PolicyEngineClient.

        Args:
            opa_url: Base URL of the OPA server. If None, will use environment variable OPA_SERVER_URL or default.
        """
        base_url = opa_url or os.getenv(
            "OPA_SERVER_URL",
            "http://opa-policy-engine.governance.svc.cluster.local:8181",
        )
        self.opa_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=2.0)
        logger.info(f"PolicyEngineClient initialized with OPA base URL: {self.opa_url}")

    async def evaluate(
        self,
        policy_path: str,
        input_data: Optional[Dict[str, Any]] = None,
        return_full_result: bool = False,
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
        # Extract user and resource info for audit logging
        if input_data is None:
            input_data = {}

        user_info = input_data.get("user", {}) or {}
        user_id = user_info.get("id", "anonymous")
        user_role = user_info.get("role", "guest")

        resource = input_data.get("resource", {}) or {}
        resource_path = resource.get("path", "")
        resource_method = resource.get("method", "")

        # Start timing
        start_time = time.perf_counter()

        url = f"{self.opa_url}/v1/data/{policy_path.replace('.', '/')}"
        logger.info(
            f"Evaluating policy at path '{policy_path}' with input: {input_data}"
        )

        try:
            payload = {"input": input_data}
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result_data = response.json()

            # Calculate duration
            end_time = time.perf_counter()
            duration_ms = round((end_time - start_time) * 1000, 2)

            if return_full_result:
                logger.info(
                    f"Full OPA response for policy '{policy_path}': {result_data}"
                )
                return result_data

            # Extract policy decision result
            inner_result = result_data.get("result")
            if inner_result is None:
                logger.error(
                    f"Policy evaluation response missing 'result' field for path '{policy_path}': {result_data}"
                )
                audit_logger.log_policy_error(
                    user_id=user_id,
                    user_role=user_role,
                    resource_path=resource_path,
                    resource_method=resource_method,
                    policy_name=policy_path,
                    reason="Missing result field in OPA response",
                    duration_ms=duration_ms,
                )
                return {"allow": False}

            if isinstance(inner_result, bool):
                result = "allow" if inner_result else "deny"
                reason = None if inner_result else "Policy denied"
                logger.info(
                    f"Policy decision for '{policy_path}': allow = {inner_result}"
                )
                audit_logger.log_policy_evaluation(
                    user_id=user_id,
                    user_role=user_role,
                    resource_path=resource_path,
                    resource_method=resource_method,
                    policy_name=policy_path,
                    result=result,
                    duration_ms=duration_ms,
                    reason=reason,
                )
                return {"allow": inner_result}

            if isinstance(inner_result, dict):
                if "allow" in inner_result and isinstance(inner_result["allow"], bool):
                    decision = inner_result["allow"]
                    result = "allow" if decision else "deny"
                    reason = inner_result.get("reason") if not decision else None
                    logger.info(
                        f"Policy decision for '{policy_path}': allow = {decision}"
                    )
                    audit_logger.log_policy_evaluation(
                        user_id=user_id,
                        user_role=user_role,
                        resource_path=resource_path,
                        resource_method=resource_method,
                        policy_name=policy_path,
                        result=result,
                        duration_ms=duration_ms,
                        reason=reason,
                    )
                    return (
                        {"allow": decision, "reason": reason}
                        if reason
                        else {"allow": decision}
                    )
                else:
                    logger.error(
                        f"Policy result for '{policy_path}' does not contain 'allow' boolean: {inner_result}"
                    )
                    end_time = time.perf_counter()
                    duration_ms = round((end_time - start_time) * 1000, 2)
                    audit_logger.log_policy_error(
                        user_id=user_id,
                        user_role=user_role,
                        resource_path=resource_path,
                        resource_method=resource_method,
                        policy_name=policy_path,
                        reason="Policy result does not contain 'allow' boolean",
                        duration_ms=duration_ms,
                    )
                    return {"allow": False}

            logger.error(
                f"Unexpected policy result type for path '{policy_path}': {type(inner_result)}"
            )
            end_time = time.perf_counter()
            duration_ms = round((end_time - start_time) * 1000, 2)
            audit_logger.log_policy_error(
                user_id=user_id,
                user_role=user_role,
                resource_path=resource_path,
                resource_method=resource_method,
                policy_name=policy_path,
                reason=f"Unexpected policy result type: {type(inner_result)}",
                duration_ms=duration_ms,
            )
            return {"allow": False}

        except httpx.TimeoutException as e:
            end_time = time.perf_counter()
            duration_ms = round((end_time - start_time) * 1000, 2)
            logger.error(f"Policy evaluation timed out for path '{policy_path}': {e}")
            audit_logger.log_policy_error(
                user_id=user_id,
                user_role=user_role,
                resource_path=resource_path,
                resource_method=resource_method,
                policy_name=policy_path,
                reason=f"Timeout: {str(e)}",
                duration_ms=duration_ms,
            )
            return {"allow": False}
        except httpx.HTTPError as e:
            end_time = time.perf_counter()
            duration_ms = round((end_time - start_time) * 1000, 2)
            logger.error(f"Policy evaluation HTTP error for path '{policy_path}': {e}")
            audit_logger.log_policy_error(
                user_id=user_id,
                user_role=user_role,
                resource_path=resource_path,
                resource_method=resource_method,
                policy_name=policy_path,
                reason=f"HTTP Error: {str(e)}",
                duration_ms=duration_ms,
            )
            return {"allow": False}
        except Exception as e:
            end_time = time.perf_counter()
            duration_ms = round((end_time - start_time) * 1000, 2)
            logger.error(
                f"Unexpected error during policy evaluation for path '{policy_path}': {e}"
            )
            audit_logger.log_policy_error(
                user_id=user_id,
                user_role=user_role,
                resource_path=resource_path,
                resource_method=resource_method,
                policy_name=policy_path,
                reason=f"Unexpected error: {str(e)}",
                duration_ms=duration_ms,
            )
            return {"allow": False}

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        await self.client.aclose()
        logger.info("PolicyEngineClient HTTP session closed")


@lru_cache
def get_policy_client() -> PolicyEngineClient:
    """정책 클라이언트 싱글톤 인스턴스 반환."""
    return PolicyEngineClient()
