"""DreamSeedAI Governance Backend Module.

This module provides FastAPI integration for the OPA-based governance policy layer.

Components:
- policy_client: OPA HTTP client for policy evaluation
- decorators: @require_policy decorator for route-level policy enforcement
- middleware: PolicyEnforcementMiddleware for global policy enforcement
- metrics: Prometheus metrics for governance monitoring

Usage:
    from governance.backend import (
        get_policy_client,
        require_policy,
        PolicyEnforcementMiddleware,
        metrics
    )

    # Use decorator on routes
    @app.get("/api/protected")
    @require_policy("dreamseedai.access_control.allow")
    async def protected_endpoint(request: Request):
        ...

    # Add global middleware
    app.add_middleware(PolicyEnforcementMiddleware)

    # Record metrics
    metrics.record_policy_evaluation("access_control", "allow", 0.05)
"""

from .policy_client import PolicyEngineClient, get_policy_client
from .decorators import require_policy
from .middleware import PolicyEnforcementMiddleware
from . import metrics

__all__ = [
    # Policy Client
    "PolicyEngineClient",
    "get_policy_client",
    
    # Decorators
    "require_policy",
    
    # Middleware
    "PolicyEnforcementMiddleware",
    
    # Metrics
    "metrics",
]

__version__ = "1.0.0"
