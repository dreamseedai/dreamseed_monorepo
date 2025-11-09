# DreamSeedAI Governance Backend

## Overview

The DreamSeedAI Governance Backend is a policy enforcement layer for the DreamSeedAI platform. It integrates Open Policy Agent (OPA) with a FastAPI application to ensure that all actions taken by the AI and users comply with defined governance rules. This backend implements the Policy Layer of DreamSeedAI's architecture, translating high-level governance directives into real-time enforcement in the system. Key features include:

- **Central Policy Engine**: Uses OPA as a centralized decision engine for access control, content filtering, approval workflows, and other policies.

- **FastAPI Integration**: Provides decorators and middleware to easily enforce policy checks on API endpoints in a FastAPI app.

- **Real-Time Policy Updates**: Supports hot-reloading of policies (via Kubernetes ConfigMap bundles) so that policy changes take effect without downtime.

- **Audit Logging**: Captures audit logs of policy decisions (especially denials) for transparency and traceability.

- **Metrics & Monitoring**: Exposes Prometheus metrics for all policy enforcement actions, allowing monitoring of policy evaluation counts, latencies, denials, etc., and integration with Grafana dashboards and alerting.

In summary, the governance backend ensures that "what ought to happen" (as defined by governance rules) is programmatically enforced at runtime in the DreamSeedAI system, with full visibility and accountability for those enforcement actions.

## Architecture

The governance backend is built around an integration of FastAPI (for the web service) and OPA (for policy decision making). The FastAPI app uses a combination of a global middleware and per-route decorators to intercept incoming requests and consult the OPA policy engine before executing business logic. An overview of the architecture is given below.

### Architecture diagram (OPA + FastAPI Integration)

```
[ User Request ] 
       │
       ▼
[ FastAPI Application ] ──(incoming request)──▶ **PolicyEnforcementMiddleware** (ASGI)
                           (global check)         │
                           ├── calls ──▶ **PolicyEngineClient** (OPA client)
                           │                   │
                           │                   └── HTTP POST ──▶ [ OPA Server ] (policy engine)
                           │                                   (evaluates rules)
                           │                   ◀── decision (allow/deny) ──┘ 
                           │
                           ├── logs decision ──▶ **AuditLogger** (records event)
                           ├── updates ────────▶ **Prometheus Metrics** (counters, histograms)
                           │
                    allow? ▼
                           ├── **Allowed** ──▶ (proceed to endpoint handler) ──▶ **Normal Response**
                           └── **Denied** ──▶ (skip handler) ──▶ **403 Forbidden response**
```

In the above ASCII diagram, the request goes through a policy check before reaching any protected endpoint logic:

1. The FastAPI app includes a **PolicyEnforcementMiddleware** that intercepts each request (except for some excluded paths like health checks and metrics).

2. The middleware uses the **PolicyEngineClient** to query the OPA server with details of the request (user info, resource, action).

3. The OPA server evaluates the relevant Rego policies and returns a decision (typically an `allow` boolean and possibly a `reason`).

4. The middleware then logs the decision via the **AuditLogger** and updates Prometheus metrics counters/histograms (e.g., increment total evaluations, count a denial, record latency).

5. If the decision is `allow`, the request proceeds to the normal endpoint handler; if `deny`, the middleware short-circuits and returns a 403 Forbidden response with an error message.

6. Additionally, developers can apply a `@require_policy` decorator on specific routes for fine-grained policy checks (e.g., different policies per endpoint) – the decorator will perform a similar evaluation by calling OPA (using the same client) and raising a 403 if the policy is violated.

### Mermaid Diagram

```mermaid
flowchart TD
    subgraph FastAPI Service
        direction TB
        A[User Request] --> B{{Policy Check}}
        B -->|Evaluate| C[PolicyEngineClient<br/>(calls OPA)]
        C --> D[OPA Server<br/>(Policy Engine)]
        D --> C
        C --> E[Decision Result<br/>(allow/deny)]
        E --> F[Audit Logger<br/>(log event)]
        E --> G[Metrics<br/>(update counters)]
        E -->|allow true| H[Endpoint Handler]
        E -->|allow false| X[Return 403 Forbidden]
        H --> I[Normal Response]
        X --> I
    end
    I --> J[Response to User]
```

**Mermaid Diagram**: Policy enforcement flow in the FastAPI application. In this flow, the PolicyEngineClient calls out to the OPA Server to get a decision. The result is logged (AuditLogger) and recorded in metrics, then used to either continue to the endpoint or block the request.

### OPA Server

The OPA policy engine runs as a separate service (e.g., a container in the Kubernetes cluster). It holds the organization's policy bundle (written in Rego). The FastAPI governance backend communicates with OPA via HTTP API calls. Policies can be updated in OPA by updating a ConfigMap (containing policy bundles) and triggering a reload, which allows dynamic policy changes without modifying application code. This separation of policy logic (OPA) from application code (FastAPI) provides flexibility and clear governance control.

### Audit Logger & Metrics

Both allowed and denied decisions can be recorded. The **AuditLogger** writes structured logs for each policy evaluation (especially useful for denials or other significant events), helping administrators audit what decisions were made. In parallel, the system updates Prometheus metrics counters for every evaluation, which enables real-time monitoring of policy enforcement (for example, counting how many requests were denied, measuring how long policy checks take, etc.). These metrics feed into Grafana dashboards and Alertmanager rules (e.g., to send alerts if there's a spike in policy denials).

## Components

The governance backend consists of several components/modules, each responsible for part of the policy enforcement functionality:

- **policy_client.py** – The Policy engine client for OPA. This module defines a `PolicyEngineClient` class that communicates with the OPA server's REST API to evaluate policies. It handles sending the input data to OPA and retrieving the decision result (allow/deny and related info). A singleton client instance is used (for connection reuse).

- **decorators.py** – Defines decorators for enforcing policies on specific FastAPI endpoints. The primary decorator provided is `@require_policy(...)` which can be applied to FastAPI route functions. This decorator checks a given policy for that endpoint before executing the function, automatically returning a 403 error if the policy is not satisfied.

- **middleware.py** – Implements a `PolicyEnforcementMiddleware` (Starlette BaseHTTPMiddleware) that applies policy checks globally to every request. This is useful for enforcing baseline policies (like access control) for all endpoints, or protecting endpoints in a generic way without needing individual decorators. The middleware can skip certain paths (health checks, metrics, docs, etc.) and will block unauthorized requests early in the request lifecycle.

- **metrics.py** – Defines Prometheus metrics objects (counters, gauges, histograms) to track policy evaluations and related events. These metrics are updated in the decorator and middleware whenever policies are evaluated or decisions are made. The metrics allow ops teams to monitor the governance system's activity and performance (e.g., how many policy checks are happening, how many denials, latency of policy queries, etc.).

- **audit_logger.py** – Provides an audit logging utility to record the outcomes of policy evaluations. It uses Python's logging system to emit structured logs for policy decisions (particularly denials or important actions) at a configurable log level. This module ensures that every critical policy enforcement event is captured for later review or compliance audits. The AuditLogger could also be extended to send notifications (for example, send a Slack message or an email on certain policy violations) if needed.

Each of these components works together to enforce policies: the middleware and decorators call the policy client, which contacts OPA; results are passed to the audit logger and metrics for logging and monitoring. Below, we detail the installation, usage, and reference for these components.

## Installation & Setup

To use the governance backend in your FastAPI project, you should ensure the required dependencies are installed and the environment is configured correctly.

### Dependencies

The governance backend relies on a few key Python packages (make sure these are in your environment or project requirements):

- **FastAPI and Starlette** – the web framework (FastAPI) and its underlying ASGI toolkit (Starlette) are used for building the API service and middleware.

- **httpx** – used by `policy_client.py` for making asynchronous HTTP calls to the OPA server.

- **prometheus_client** – used in `metrics.py` to define and expose metrics for Prometheus scraping.

- **(Standard Library)** `logging`, `functools`, `typing` – used for logging, caching, and type annotations respectively in various modules.

If this module is part of the DreamSeedAI monorepo, these dependencies might already be included. Otherwise, you can install them via pip:

```bash
pip install fastapi httpx prometheus_client
```

### Environment Variables

The governance backend uses environment variables for configuration. The following variables can be set:

| Environment Variable | Default Value | Description |
|---------------------|---------------|-------------|
| `OPA_SERVER_URL` | `http://opa-policy-engine.governance.svc.cluster.local:8181` | URL of the OPA server to query for policy decisions. In a Kubernetes deployment, this might be the internal service URL for OPA (as shown, assuming service name `opa-policy-engine` in namespace `governance`). For local testing, you might use `http://localhost:8181`. |
| `AUDIT_LOG_LEVEL` | `INFO` | Logging level for the Audit Logger. Determines the verbosity of audit logs. For example, `DEBUG` may log all policy evaluations (allow and deny with full input detail), `INFO` might log only important events (like denials or errors), and `WARNING`/`ERROR` could restrict to only policy violations or failures. |

To configure these, you can export them in your environment or, in Kubernetes, set them in the Deployment manifest or ConfigMap for the governance backend. For example, to run the FastAPI app locally with a local OPA, you might do:

```bash
export OPA_SERVER_URL="http://localhost:8181"
export AUDIT_LOG_LEVEL="DEBUG"
```

### Initial Setup

1. **OPA Server**: Ensure you have an OPA server running and loaded with the necessary policies. In Kubernetes, this will be handled by deploying the OPA container (see Deployment section). For local development, you can run OPA locally and load your Rego policies.

2. **FastAPI App Integration**: In your FastAPI application, import the governance backend modules. You will typically attach the `PolicyEnforcementMiddleware` to the app and use `@require_policy` on specific routes (see examples below).

3. **Prometheus Integration**: If using metrics, make sure to expose the `/metrics` endpoint of your app (Prometheus will scrape metrics from there). The `prometheus_client` library will accumulate metrics and output them in the expected format. Integrate a Prometheus instance or ensure your cluster's Prometheus is configured to scrape the governance backend service.

4. **Logging**: Configure the logging as needed for your application. By default, FastAPI/uvicorn logs to stdout. The AuditLogger will use the standard logging infrastructure. You may want to route the audit logs to a specific sink or file if running on a server, but typically leaving them in stdout (to be picked up by `kubectl logs` or logging agent) is sufficient. Use `AUDIT_LOG_LEVEL` to adjust verbosity.

Once dependencies are installed and environment variables are set, you can proceed to use the governance backend in your code.

## Usage Examples

Below are examples of how to use the governance backend components in a FastAPI application.

### 1. Applying the Policy Decorator to an Endpoint

You can use the `@require_policy` decorator from `decorators.py` to enforce a policy on a specific API endpoint. For example, to protect a lesson retrieval endpoint so that only authorized users can access it (per the access control policy):

```python
from fastapi import FastAPI, APIRouter, Request
from governance.backend import require_policy

app = FastAPI()
router = APIRouter()

@router.get("/lessons/{lesson_id}")
@require_policy("dreamseedai.access_control.allow")
async def get_lesson(lesson_id: int, request: Request):
    """
    Retrieve a lesson. This endpoint is protected by an access control policy:
    only authorized roles (e.g., the lesson's teacher or an admin) will pass.
    """
    # If the policy check passes, this code runs; otherwise a 403 is returned.
    return {"lesson_id": lesson_id, "content": "Lesson content goes here."}

app.include_router(router)
```

In this example:

- We import `require_policy` and apply it above the endpoint function.
- The argument `"dreamseedai.access_control.allow"` is the policy path in OPA that should be evaluated. This corresponds to a rule in the Rego policy (for access control) that returns an `allow` decision.
- The decorator will automatically gather the necessary input (by default, it includes the user info from `request.state.user`, the request path and method as resource info, etc.) and call OPA via the policy client.
- If the policy denies access (`allow == false`), FastAPI will return a 403 Forbidden response with details about the policy violation. If allowed, the endpoint executes normally and returns the lesson data.

**Custom input builder**: The `require_policy` decorator optionally accepts an `input_builder` function. This can be used if you need to supply custom input data to OPA beyond the default. For example, you might want to include specific resource attributes or call a database to augment input. You can provide a callable that takes `(request, *args, **kwargs)` and returns a dict to be used as the policy input. If not provided, a default input with `user`, `resource`, and `action` is used as shown in the code above.

### 2. Enabling the Global Policy Middleware

In addition to per-route decorators, you can enforce policies globally using the middleware. The `PolicyEnforcementMiddleware` in `middleware.py` will run for every incoming request. Typically, you add this to your FastAPI app at startup:

```python
from fastapi import FastAPI
from governance.backend import PolicyEnforcementMiddleware

app = FastAPI()

# Add global policy enforcement middleware.
# This will automatically evaluate the base policy (e.g., access control) for each request.
# It skips certain endpoints (health checks, docs, metrics) by default.
app.add_middleware(PolicyEnforcementMiddleware)

# ... include routers, etc., as usual ...
```

Once this middleware is added:

- Each request will trigger a policy evaluation (for example, using a default policy like `"dreamseedai.access_control.allow"` to check basic permissions).
- If the request is not allowed by policy, it short-circuits and returns a 403 response without reaching your route handler.
- If allowed, processing continues normally.
- The middleware's `_should_evaluate` method excludes some paths (you can see in the code it excludes `/health`, `/metrics`, `/docs`, `/openapi.json` by default). You can modify or extend this if needed (e.g., to exclude other public endpoints).

The middleware is useful for broad policies you want applied everywhere (like general access control or request rate limiting policies).

You can use both the middleware and specific decorators in combination:

- The middleware can enforce system-wide rules (like "user must be authenticated and active" or basic RBAC).
- Decorators can enforce additional endpoint-specific rules (like "user must be an admin to call this particular endpoint"). The decorator will run after the middleware (since the request reaches the route function only if middleware didn't already block it).

### 3. Exposing the Metrics Endpoint

To allow Prometheus to scrape the metrics, you need to expose an HTTP endpoint that outputs the metrics data. The `prometheus_client` library collects metrics in a global registry and can format them as text. A simple way to expose metrics in FastAPI is to add a route like `/metrics`:

```python
from fastapi import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    metrics_data = generate_latest()  # collects metrics from the default registry
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
```

This endpoint will return the current metrics in the plaintext format Prometheus expects. The governance backend's metrics (defined in `metrics.py`) are automatically registered in the global Prometheus registry when they are imported. By hitting `GET /metrics`, you'll see outputs like:

```
# HELP governance_policy_evaluations_total Total number of policy evaluations
# TYPE governance_policy_evaluations_total counter
governance_policy_evaluations_total{policy="dreamseedai.access_control.allow", result="allow"} 42
governance_policy_evaluations_total{policy="dreamseedai.access_control.allow", result="deny"} 5
...
# HELP governance_policy_evaluation_duration_seconds Policy evaluation duration in seconds
# TYPE governance_policy_evaluation_duration_seconds histogram
governance_policy_evaluation_duration_seconds_bucket{policy="dreamseedai.access_control.allow", le="0.001"} 30
...
```

and so on for each metric (see Monitoring section for a full list). Be sure that:

- This `/metrics` route is not protected by any authentication (Prometheus needs to scrape it freely). In the middleware `_should_evaluate`, it is excluded, which is good.
- Your deployment (if in Kubernetes) has the proper annotations or ServiceMonitor so that Prometheus knows to scrape this endpoint.

### 4. Audit Logging Usage

The audit logging is largely automatic. By default, the policy middleware and decorator will utilize the audit logger to record events. Ensure that the log level is set via `AUDIT_LOG_LEVEL` appropriately. For example, in development you might set `AUDIT_LOG_LEVEL="DEBUG"` to see all decisions logged in the console. In production, `INFO` might be sufficient (only notable events).

The audit logger automatically records structured JSON logs to stdout for each policy evaluation. Example log entry:

```json
{
  "timestamp": "2025-11-08T12:00:00.123456+00:00",
  "event_type": "policy_evaluation",
  "user_id": "student123",
  "user_role": "student",
  "resource_path": "/lessons/5",
  "resource_method": "POST",
  "policy_name": "dreamseedai.access_control.allow",
  "result": "deny",
  "duration_ms": 4.23,
  "reason": "Access denied by policy"
}
```

Every policy decision, especially denials, will leave an audit trail entry in stdout, which can be collected by Kubernetes logging agents or external log aggregators.

## API Reference

This section provides a reference for the main classes and functions provided by the governance backend modules:

### policy_client.py

**Class `PolicyEngineClient`** – Client for interacting with the OPA policy engine.

- **Constructor**: `PolicyEngineClient(opa_url: str = None)` – Creates a client. If `opa_url` is not provided, it will default to the value of the `OPA_SERVER_URL` environment variable (or a compiled-in default, such as the cluster internal URL). It initializes an `httpx.AsyncClient` for making requests.

- **Async Method** `evaluate(policy_path: str, input_data: Dict[str, Any], return_full_result: bool = False) -> Dict[str, Any]` – Evaluate a policy query against OPA.
  - `policy_path` is the path in OPA's data hierarchy for the policy decision you want (for example `"dreamseedai.access_control.allow"` corresponds to OPA data document `dreamseedai/access_control/allow` that yields a boolean).
  - `input_data` is a dictionary of input to pass to the policy (this will be wrapped as `{"input": input_data}` in the request to OPA).
  - If `return_full_result` is `False` (default), it will return just the result portion of OPA's response (e.g., `{"allow": True}` or `{"allow": False, "reason": "some reason"}` depending on your policy output structure). If `True`, it returns the entire response JSON from OPA (which might include things like query explanations if enabled).
  - On success, returns a dict of the policy decision. Typically, you'd check `result.get("allow")` in that dict. On failure (e.g., OPA not reachable or returns error), it catches the exception and returns a result with `{"allow": False}` to be safe (treating errors as denial for security).
  - **Automatically logs audit events** for every evaluation (allow/deny/error) with timestamp, user info, resource info, and duration.

- **Method** `close()` – Closes the underlying HTTP client session. This should be called on shutdown if using the client directly. (In normal FastAPI usage, you might rely on the event loop closing to clean up, but a cleanup routine could call this via FastAPI shutdown event.)

- The `PolicyEngineClient` is designed to be used as a singleton (since creating a new HTTP client for every request is costly).

**Function `get_policy_client() -> PolicyEngineClient`** – A module-level function decorated with `@lru_cache` that returns a singleton instance of `PolicyEngineClient`. The first call will create the client (with default OPA URL), and subsequent calls return the same instance. Use this in your code to get the shared client, e.g. `policy_client = get_policy_client()`.

### decorators.py

**Function `require_policy(policy_path: str, input_builder: Optional[Callable[[Request, ...], Dict]] = None, deny_status_code: int = 403)`** – FastAPI decorator factory for policy enforcement.

- This function returns a decorator that can be applied to FastAPI endpoint functions.

- **Parameters**:
  - `policy_path`: The policy data path (in dot notation) to evaluate, for example `"dreamseedai.access_control.allow"`. This should correspond to a rule in OPA that returns an allow/deny decision.
  - `input_builder`: (Optional) A custom function to build the input data for the policy from the request and function arguments. If provided, it should be an async function (or regular function) that returns a dict. If not provided, a default input is constructed (which includes `request.state.user` if available, and basic request info).
  - `deny_status_code`: The HTTP status code to return if the policy check fails. Defaults to 403 Forbidden, but you could set 401 or others if appropriate.

- **Behavior**:
  - When a request comes into the decorated endpoint, the wrapper will extract the FastAPI `Request` object (from args or kwargs).
  - It builds the `input_data` for the policy:
    - If `input_builder` is given, it calls `input_builder(request, *args, **kwargs)` to get the input dict.
    - If not, it uses a simple default:
      ```python
      input_data = {
          "user": getattr(request.state, "user", {}),
          "resource": {"path": request.url.path, "method": request.method},
          "action": request.method.lower()
      }
      ```
      This assumes `request.state.user` contains a user dict (set by an auth dependency or middleware).
  - It then obtains a `PolicyEngineClient` (via `get_policy_client()`) and calls `await policy_client.evaluate(policy_path, input_data)`.
  - If the result does not have `allow == True`, it raises an `HTTPException(deny_status_code)` to immediately return an error. The exception's detail will include a JSON with an error message, the policy that was violated, and a reason if provided:
    ```json
    {
      "error": "Policy violation",
      "policy": "dreamseedai.access_control.allow",
      "reason": "Access denied"
    }
    ```
  - If the policy allows, the wrapper calls the original function and returns its result.
  - This decorator is async-compatible (the wrapper is defined as `async def` so it works with async endpoints).

- **Usage**: See the Usage Examples section above for a demonstration. You simply add `@require_policy("policy.path")` above your route. You can also stack it with other decorators (e.g., FastAPI's `@get` or other dependencies).

- **Audit Logging**: The decorator relies on the `PolicyEngineClient.evaluate()` method which automatically logs all policy evaluations (allow/deny/error) to the audit logger with full context.

### middleware.py

**Class `PolicyEnforcementMiddleware(BaseHTTPMiddleware)`** – Global ASGI middleware for policy checks.

- You typically add this to the FastAPI app using `app.add_middleware(PolicyEnforcementMiddleware)`.
- It overrides the `dispatch` method to intercept requests.

**Logic**:

- On each request, it first calls `_should_evaluate(request)` (an internal method) to determine if this request should be subject to a policy check. By default, `_should_evaluate` returns `False` for certain whitelisted paths (commonly health checks or monitoring endpoints). The code sets `excluded_paths = {"/health", "/metrics", "/docs", "/openapi.json"}`; if `request.url.path` is in that set, it will skip policy evaluation.

- If `_should_evaluate` returns `True` (meaning the request is a normal API request that should be governed), the middleware will:
  - Call the policy engine to evaluate the access. In the code, it specifically calls the `"dreamseedai.access_control.allow"` policy with input constructed similarly (user from `request.state.user`, resource path and method).
  - If the result is not `allow`, it immediately returns a `JSONResponse(status_code=403, content={"error": "Access denied by policy"})`. This prevents the request from reaching any further handlers.
  - If allowed, it calls `await call_next(request)` to pass control to the next component (which could be another middleware or ultimately the FastAPI route handler).
  - The response from `call_next` is then returned (if not blocked).

**Audit Logging**: The middleware automatically logs all policy evaluations through the `PolicyEngineClient.evaluate()` method, which records every decision (allow/deny/error) with full context to the audit logger.

**Configuration**: If needed, you can:
- Subclass or modify `_should_evaluate` to refine which requests are checked.
- Customize the `excluded_paths` set by passing it to the constructor: `PolicyEnforcementMiddleware(app, excluded_paths=["/health", "/custom-public"])`.
- The policy path used in middleware is hard-coded to `"dreamseedai.access_control.allow"` but could be made configurable if needed.

**Important**: Order of middleware matters in FastAPI/Starlette. Ensure that this governance middleware is added after any authentication middleware that populates `request.state.user`. Typically, you might not have a separate auth middleware if you use FastAPI dependency injection for auth, in which case ensure that when the policy client evaluates, it has the necessary info. If `request.state.user` is empty, your policies should handle that (likely deny by default).

### metrics.py

**Metrics definitions**: This module defines various Prometheus metric objects to track the governance system. The metrics are created as module-level variables (instances of `Counter`, `Histogram`, `Gauge` from `prometheus_client`). They are labeled to allow granular analysis by policy name, outcome, etc.

**Key Metrics**:

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `governance_policy_evaluations_total` | Counter | `policy`, `result` | Total number of policy evaluations performed. Counts every OPA call for a decision. |
| `governance_policy_deny_total` | Counter | `policy`, `user_role` | Counts policy denials. Helps track how many denials occur by policy and user role. |
| `governance_policy_errors_total` | Counter | `policy` | Counts policy evaluation errors (network failures, unexpected errors). Should ideally stay at 0. |
| `governance_policy_evaluation_duration_seconds` | Histogram | `policy` | Measures the duration (latency) of policy evaluations. Monitors performance of policy checks. |
| `governance_policy_bundle_reload_total` | Counter | `status` | Counts the number of times the policy bundle has been reloaded in OPA (labels: "success" or "error"). |
| `governance_policy_bundle_version` | Gauge | - | Indicates the current version of the policy bundle loaded (numeric version, timestamp, or hash). |
| `governance_ai_content_filtered_total` | Counter | `filter_type`, `severity` | Counts instances of AI content being filtered/blocked by policy (e.g., profanity, hate_speech). |
| `governance_ai_tutor_sessions_total` | Counter | `user_role`, `status` | Counts AI tutor sessions subject to policy (started/ended/compliant/terminated). |
| `governance_approval_requests_total` | Counter | `action_type`, `status` | Counts the number of approval workflow requests processed (approved/denied/pending). |
| `governance_approval_pending` | Gauge | - | Current number of pending approval requests waiting for admin/teacher approval. |
| `governance_data_access_total` | Counter | `data_type`, `result` | Counts data access attempts subject to data protection policies (allowed/blocked). |

**Usage of metrics**: These metric objects are imported and used in the middleware/decorators. For example, each call to OPA might do:

```python
from . import metrics

metrics.policy_evaluations_total.labels(
    policy="dreamseedai.access_control.allow",
    result="allow"
).inc()
```

Denials would increment `policy_deny_total` with appropriate labels. The histogram `policy_evaluation_duration_seconds` can be used with a context timer to observe how long `policy_client.evaluate()` took.

You generally do not need to manipulate these metrics manually outside of the governance backend; they work behind the scenes. Just ensure your app exposes them via `/metrics` and that Prometheus is scraping them.

**Extending metrics**: If you wish to add new metrics, you can extend this module following the same pattern. For example, if you wanted to count Slack notifications sent, you could add a counter here.

(For a complete list of metric values and monitoring setup, see the **Monitoring** section below.)

### audit_logger.py

**Audit Logger Utility**: This module is responsible for logging audit events. It uses Python's standard logging with a named logger (`logging.getLogger("governance.audit")`).

**Configuration**: The logger's level is set based on the `AUDIT_LOG_LEVEL` environment variable. For instance:
- If `AUDIT_LOG_LEVEL="INFO"`, the audit logger will log INFO and above (INFO, WARNING, ERROR).
- If set to `DEBUG`, it will log very verbose details.

**Functions**:

**`log_policy_evaluation(user_id, user_role, resource_path, resource_method, policy_name, result, duration_ms, reason=None)`**

Logs a policy evaluation decision (allow/deny).

- **Parameters**:
  - `user_id` (str): The user identifier
  - `user_role` (str): The user's role
  - `resource_path` (str): The resource path being accessed
  - `resource_method` (str): The HTTP method (GET, POST, etc.)
  - `policy_name` (str): The policy path evaluated
  - `result` (str): Either "allow" or "deny"
  - `duration_ms` (int/float): Duration of the evaluation in milliseconds
  - `reason` (str, optional): Additional reason for the decision (typically for denials)

- **Behavior**: 
  - Composes a structured JSON log message with UTC timestamp
  - Logs at INFO level for `allow` results
  - Logs at WARNING level for `deny` results
  - Raises `ValueError` if result is not "allow" or "deny"

**`log_policy_error(user_id, user_role, resource_path, resource_method, policy_name, reason, duration_ms)`**

Logs a policy evaluation error.

- **Parameters**: Same as `log_policy_evaluation`, but `reason` is required and describes the error.

- **Behavior**: 
  - Composes a structured JSON log message with result="error"
  - Always logs at ERROR level
  - Used when OPA calls fail or return unexpected errors

**Log Format**: Audit logs are structured as JSON for easier parsing. Example output:

```json
{
  "timestamp": "2025-11-08T10:30:45.123456+00:00",
  "event_type": "policy_evaluation",
  "user_id": "user123",
  "user_role": "student",
  "resource_path": "/api/lessons/42",
  "resource_method": "GET",
  "policy_name": "dreamseedai.access_control.allow",
  "result": "allow",
  "duration_ms": 4.23
}
```

**Integration**: The `PolicyEngineClient.evaluate()` method automatically calls the audit logger for every policy evaluation. The `require_policy` decorator and `PolicyEnforcementMiddleware` rely on this centralized logging—you normally don't need to call the audit logger explicitly.

However, you can use it for additional manual logging if needed (e.g., logging manual administrative actions, or logging an override event where an admin bypassed a policy).

**Example manual usage**:

```python
from governance.backend import audit_logger

audit_logger.log_policy_evaluation(
    user_id="admin123",
    user_role="administrator",
    resource_path="/api/override/student/456",
    resource_method="POST",
    policy_name="manual_override",
    result="allow",
    duration_ms=0,
    reason="Admin override approved by supervisor"
)
```

**Note on Slack/Alerts**: While the audit logger itself does not send Slack messages, the presence of detailed logs enables the monitoring stack to trigger alerts. Alertmanager rules can watch for high rates of denials or specific keywords in logs. In our design, we rely on metrics for alerting instead. If needed, the audit logger could be extended to call a Slack webhook directly for each violation, but this is usually redundant if metrics+Alertmanager is configured.

---

By using the above classes and functions, the DreamSeedAI governance backend ensures that policy logic is cleanly separated and easily maintainable. Next, we discuss how to monitor this system and deploy it in a Kubernetes environment.

## Monitoring

Monitoring and auditing are critical aspects of the governance backend. There are two main facets: **Audit Logs** and **Prometheus Metrics**.

### Audit Logs

**Format & Content**: Audit logs provide a record of policy enforcement decisions. Each log entry is structured as JSON and typically includes:

- **Timestamp**: When the event occurred (UTC ISO 8601 format)
- **User Identity**: Who initiated the action (user ID and role). This comes from `request.state.user` or equivalent.
- **Action**: What action was attempted (HTTP method: GET, POST, etc.)
- **Resource**: What resource or endpoint was accessed (e.g., `/lessons/123`)
- **Policy**: Which policy was evaluated (e.g., `dreamseedai.access_control.allow`)
- **Decision**: The outcome of the policy check (`allow`, `deny`, or `error`)
- **Duration**: How long the policy evaluation took (in milliseconds)
- **Reason**: (If available) A short reason for denial. In our implementation, OPA policies can set a `reason` field in the result when `allow` is false (for example, "User role not permitted" or "Outside allowed hours").

**Example Log Entries**:

Allowed request (INFO level):
```json
{
  "timestamp": "2025-11-08T12:34:56.123456+00:00",
  "event_type": "policy_evaluation",
  "user_id": "teacher42",
  "user_role": "teacher",
  "resource_path": "/lessons/5",
  "resource_method": "GET",
  "policy_name": "dreamseedai.access_control.allow",
  "result": "allow",
  "duration_ms": 3.45
}
```

Denied request (WARNING level):
```json
{
  "timestamp": "2025-11-08T12:35:10.789012+00:00",
  "event_type": "policy_evaluation",
  "user_id": "student17",
  "user_role": "student",
  "resource_path": "/exams/2/submit",
  "resource_method": "POST",
  "policy_name": "dreamseedai.access_control.allow",
  "result": "deny",
  "duration_ms": 4.23,
  "reason": "submission window closed"
}
```

Error case (ERROR level):
```json
{
  "timestamp": "2025-11-08T12:36:20.345678+00:00",
  "event_type": "policy_evaluation",
  "user_id": "student99",
  "user_role": "student",
  "resource_path": "/api/data",
  "resource_method": "GET",
  "policy_name": "dreamseedai.access_control.allow",
  "result": "error",
  "duration_ms": 5001.23,
  "reason": "Timeout: Request to OPA timed out after 5000ms"
}
```

These logs let administrators audit what is happening. For example, an admin could investigate why a student's action was denied and see the exact reason, or verify that teachers are only accessing their own students' data (by seeing only allowed logs for those cases).

**Log Levels**: We use the `AUDIT_LOG_LEVEL` environment variable to control verbosity:

- **DEBUG**: Log every policy check (allowed or denied) with full input context if needed. Useful in development or troubleshooting specific issues.
- **INFO** (default): Log all policy evaluations. Allowed requests log at INFO, denials at WARNING, errors at ERROR. This gives a complete audit trail.
- **WARNING**: Only log denials and errors. Normal allowed operations don't appear, reducing noise.
- **ERROR**: Only log critical failures (policy engine unreachable, evaluation errors).

By default, we recommend **INFO** level for production. This gives a clear audit trail of all policy decisions without excessive verbosity. Increase to DEBUG when actively debugging policy behavior.

**Storing and Accessing Logs**: In Kubernetes, these logs are part of the container's stdout/stderr. Ensure you have log aggregation (e.g., Elasticsearch/Kibana, Loki, or cloud logging) to retain them. The audit log is crucial for after-the-fact reviews and for compliance (showing that the system is enforcing rules). You may also configure a longer retention period for these logs compared to regular application logs, since they might be needed for audits.

### Prometheus Metrics

The governance backend emits a rich set of Prometheus metrics that allow real-time monitoring and historical analysis of policy enforcement. Here is the complete list of metrics provided:

#### Core Policy Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `governance_policy_evaluations_total` | Counter | `policy`, `result` | Total count of policy evaluations. Use to calculate overall rate of policy checks and proportion of allowed vs denied decisions. |
| `governance_policy_deny_total` | Counter | `policy`, `user_role` | Total count of policy denials. Track which policies are denying actions and which user roles encounter denials. |
| `governance_policy_errors_total` | Counter | `policy` | Total count of errors during policy evaluation. Should ideally remain zero. Indicates OPA connectivity or runtime errors. |
| `governance_policy_evaluation_duration_seconds` | Histogram | `policy` | Duration of policy evaluation calls to OPA. Monitors performance—should be milliseconds for local OPA. |
| `governance_policy_bundle_reload_total` | Counter | `status` | Count of policy bundle reload events (`status`: "success" or "error"). Monitors if policy updates are propagating. |
| `governance_policy_bundle_version` | Gauge | - | Current version of the loaded policy bundle. Set to integer/build number corresponding to policy set. |

#### AI Content & Tutor Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `governance_ai_content_filtered_total` | Counter | `filter_type`, `severity` | Total AI content pieces filtered/blocked (`filter_type`: "profanity", "harassment", "PII"; `severity`: "low", "high"). |
| `governance_ai_tutor_sessions_total` | Counter | `user_role`, `status` | Total AI tutor sessions observed/moderated (`status`: "started", "ended", "terminated"). |

#### Approval Workflow Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `governance_approval_requests_total` | Counter | `action_type`, `status` | Total approval workflow requests (`action_type`: "extra_exam_attempt", "content_publish"; `status`: "approved", "denied", "pending"). |
| `governance_approval_pending` | Gauge | - | Current number of pending approvals. Alert if backlog grows. |

#### Data Protection Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `governance_data_access_total` | Counter | `data_type`, `result` | Total data access attempts governed by policy (`data_type`: "student_record", "analytics_report"; `result`: "allowed", "blocked"). |

**Usage Examples**:

These metrics are emitted automatically during runtime. To view them, use the `/metrics` endpoint. In a Grafana dashboard, you can create visualizations such as:

- **Pie chart** of allow vs deny (using `governance_policy_evaluations_total` split by `result`)
- **Time-series graph** of policy denials over time (stacked by `policy` or `user_role`)
- **Histogram heatmap** of evaluation durations (from the histogram metric)
- **Gauge** showing current approval backlog (from `governance_approval_pending`)
- **Counter** for content filtered (to see if there's a spike in filtered content)

**Example PromQL Queries**:

```promql
# Policy denial rate (per second)
rate(governance_policy_deny_total[5m])

# Policy evaluation latency (95th percentile)
histogram_quantile(0.95, rate(governance_policy_evaluation_duration_seconds_bucket[5m]))

# Percentage of requests denied
100 * sum(rate(governance_policy_evaluations_total{result="deny"}[5m])) 
  / sum(rate(governance_policy_evaluations_total[5m]))

# Current approval backlog
governance_approval_pending
```

**Alerting**: The DreamSeedAI ops setup includes Prometheus Alertmanager rules (see `governance-alerts.yaml`) that use these metrics. For example:

- **Alert** if the rate of denials (`governance_policy_deny_total`) goes above a threshold (could indicate misconfiguration or abuse attempt)
- **Alert** if any policy evaluation errors occur (`governance_policy_errors_total > 0`)
- **Alert** if high-severity content filtering events spike (using `severity="high"` label on `governance_ai_content_filtered_total`)
- **Alert** if approval backlog (`governance_approval_pending`) exceeds a certain number for sustained time
- **Alert** if policy bundle reload fails (`governance_policy_bundle_reload_total{status="error"}` increases)

These ensure the devops team is notified quickly if, for example, the policy engine is down (errors) or a new policy is unintentionally blocking too much (denial rate surge).

**Complete Visibility**: By monitoring both logs and metrics, you get a complete picture:
- **Logs** give you detailed context on individual events (who, what, why denied)
- **Metrics** give you aggregated trends and system health (how often things are happening, performance, etc.)

Together, they form the governance monitoring solution.

## Deployment

The governance backend is designed to run in a containerized environment (e.g., Kubernetes) alongside the OPA engine. Deployment involves configuring both the FastAPI service and the OPA service, as well as setting up ConfigMaps for policies and configs.

### Kubernetes Manifests

The repository includes Kubernetes manifest files under the `governance/ops/k8s/` directory for deploying the governance components. Key files include:

#### OPA Server Components

- **`deployment-opa.yaml`**: Kubernetes Deployment for the OPA policy engine
  - Container: `openpolicyagent/opa:latest`
  - Command: `opa run --server --addr=:8181 --config-file=/config/config.yaml --bundle /policies`
  - Mounts: ConfigMaps for config and policy bundle
  - Resources: CPU/memory limits and requests
  - Health checks: liveness and readiness probes

- **`service-opa.yaml`**: Kubernetes Service for OPA
  - Type: ClusterIP
  - DNS: `opa-policy-engine.governance.svc.cluster.local:8181`
  - Exposes port 8181 for policy queries

- **`configmap-opa-config.yaml`**: ConfigMap containing OPA server configuration
  - Bundle configuration (watch for updates)
  - Decision logging settings
  - Status reporting

- **`configmap-policy-bundle.yaml`**: ConfigMap containing Rego policy files
  - Contains all `.rego` policy files from `governance/policies/`
  - Mounted at `/policies` in OPA container
  - OPA watches for changes and auto-reloads

#### Monitoring & Scaling

- **`servicemonitor-opa.yaml`**: ServiceMonitor for Prometheus Operator
  - Scrapes OPA metrics at `/metrics`
  - Interval: 30s
  - Labels for Prometheus discovery

- **`hpa-opa.yaml`**: HorizontalPodAutoscaler for OPA
  - Target: 70% CPU utilization
  - Min replicas: 2
  - Max replicas: 10
  - Ensures policy queries remain fast under load

### Environment Configuration

Ensure the following environment variables are set in your FastAPI application deployment:

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `OPA_SERVER_URL` | `http://opa-policy-engine.governance.svc.cluster.local:8181` | Yes | OPA server endpoint for policy evaluations |
| `AUDIT_LOG_LEVEL` | `INFO` | No | Audit logger verbosity (DEBUG/INFO/WARNING/ERROR) |

### Deployment Checklist

Before deploying to production, verify the following:

**Prerequisites**:
- [ ] Kubernetes cluster is running (v1.21+)
- [ ] `kubectl` configured with cluster access
- [ ] `governance` namespace exists: `kubectl create namespace governance`
- [ ] Prometheus Operator installed (for ServiceMonitor)
- [ ] Grafana configured for dashboard visualization

**OPA Deployment**:
- [ ] Apply OPA ConfigMaps:
  ```bash
  kubectl apply -f governance/ops/k8s/configmap-opa-config.yaml
  kubectl apply -f governance/ops/k8s/configmap-policy-bundle.yaml
  ```
- [ ] Apply OPA Deployment and Service:
  ```bash
  kubectl apply -f governance/ops/k8s/deployment-opa.yaml
  kubectl apply -f governance/ops/k8s/service-opa.yaml
  ```
- [ ] Verify OPA is running:
  ```bash
  kubectl get pods -n governance -l app=opa-policy-engine
  kubectl logs -n governance -l app=opa-policy-engine
  ```
- [ ] Test OPA health:
  ```bash
  kubectl port-forward -n governance svc/opa-policy-engine 8181:8181
  curl http://localhost:8181/health
  ```

**FastAPI Backend Deployment**:
- [ ] Build Docker image with governance backend:
  ```bash
  docker build -t dreamseedai/governance-backend:latest .
  ```
- [ ] Apply FastAPI Deployment (update your app deployment manifest to include governance backend code)
- [ ] Verify environment variables are set correctly
- [ ] Check logs for audit log output:
  ```bash
  kubectl logs -n governance -l app=your-fastapi-app | grep "governance.audit"
  ```

**Monitoring Setup**:
- [ ] Apply ServiceMonitor:
  ```bash
  kubectl apply -f governance/ops/k8s/servicemonitor-opa.yaml
  ```
- [ ] Apply HPA:
  ```bash
  kubectl apply -f governance/ops/k8s/hpa-opa.yaml
  ```
- [ ] Verify Prometheus is scraping OPA metrics:
  - Check Prometheus targets: `http://<prometheus-url>/targets`
  - Query: `up{job="opa-policy-engine"}`
- [ ] Import Grafana dashboard (if available in `governance/ops/dashboards/`)
- [ ] Configure Alertmanager rules (see `governance/ops/alerts/governance-alerts.yaml`)

**Testing**:
- [ ] Test policy evaluation from FastAPI app:
  ```bash
  curl -X POST http://your-fastapi-app/api/test-endpoint \
    -H "Authorization: Bearer <token>"
  # Should see audit log in pod logs
  ```
- [ ] Verify metrics endpoint:
  ```bash
  curl http://your-fastapi-app/metrics | grep governance_
  ```
- [ ] Test policy update:
  - Edit policy in `governance/policies/`
  - Update ConfigMap: `kubectl create configmap governance-policy-bundle --from-file=governance/policies/ -n governance --dry-run=client -o yaml | kubectl apply -f -`
  - Verify OPA reloads: `kubectl logs -n governance -l app=opa-policy-engine | grep "bundle loaded"`

### Updating Policies

To update policies in production:

1. **Edit policy files** in `governance/policies/`
2. **Test locally** (see Phase 1 documentation)
3. **Update ConfigMap**:
   ```bash
   kubectl create configmap governance-policy-bundle \
     --from-file=governance/policies/ \
     -n governance \
     --dry-run=client -o yaml | kubectl apply -f -
   ```
4. **Verify reload**:
   ```bash
   kubectl logs -n governance -l app=opa-policy-engine --tail=50 | grep bundle
   ```
5. **Monitor metrics**: Check `governance_policy_bundle_reload_total{status="success"}` increments

### Namespace Configuration

It's recommended to deploy governance components in a dedicated namespace:

```bash
kubectl create namespace governance
kubectl label namespace governance monitoring=enabled
```

This isolates governance components and allows for namespace-level RBAC policies.

For more detailed deployment steps and environment-specific instructions, refer to the ops documentation or the Kubernetes manifests in `governance/ops/k8s/`.

## Troubleshooting

### Common Issues

#### 1. OPA Connection Failures

**Symptoms**: 
- HTTP 500 errors on protected endpoints
- Audit logs show `result="error"` with "Connection refused" or "Timeout"
- Metric `governance_policy_errors_total` increasing

**Solutions**:

- **Check OPA Service is running**:
  ```bash
  kubectl get pods -n governance -l app=opa-policy-engine
  kubectl get svc -n governance opa-policy-engine
  ```

- **Verify OPA_SERVER_URL is correct**:
  ```bash
  kubectl get deployment -n governance your-fastapi-app -o yaml | grep OPA_SERVER_URL
  ```
  Should be: `http://opa-policy-engine.governance.svc.cluster.local:8181`

- **Test OPA connectivity from FastAPI pod**:
  ```bash
  kubectl exec -n governance -it <fastapi-pod-name> -- curl http://opa-policy-engine.governance.svc.cluster.local:8181/health
  ```
  Should return: `{"status": "ok"}`

- **Check OPA logs for errors**:
  ```bash
  kubectl logs -n governance -l app=opa-policy-engine --tail=100
  ```

#### 2. Policy Evaluation Timeouts

**Symptoms**:
- Slow response times on protected endpoints
- Audit logs show high `duration_ms` values (>1000ms)
- Metric `governance_policy_evaluation_duration_seconds` showing high latency

**Solutions**:

- **Check OPA resource usage**:
  ```bash
  kubectl top pods -n governance -l app=opa-policy-engine
  ```
  If CPU/memory is high, consider scaling or increasing resource limits.

- **Scale OPA horizontally**:
  ```bash
  kubectl scale deployment -n governance opa-policy-engine --replicas=3
  ```
  Or wait for HPA to auto-scale if configured.

- **Check for complex policies**: Review Rego policies for inefficient rules or loops.

- **Verify network latency**: If OPA is in a different namespace/cluster, network latency may be the issue.

#### 3. Authentication/User Context Missing

**Symptoms**:
- All requests denied even for authorized users
- Audit logs show `user_id="anonymous"` and `user_role="guest"`
- Policy denies with reason like "No authenticated user"

**Solutions**:

- **Verify authentication middleware order**: Ensure auth middleware runs BEFORE governance middleware:
  ```python
  app.add_middleware(AuthenticationMiddleware)  # FIRST
  app.add_middleware(PolicyEnforcementMiddleware)  # SECOND
  ```

- **Check `request.state.user` is set**: Add debug logging in auth middleware to verify user is populated.

- **Test with explicit user context**:
  ```python
  from governance.backend import get_policy_client
  
  client = get_policy_client()
  result = await client.evaluate(
      "dreamseedai.access_control.allow",
      {
          "user": {"id": "test123", "role": "student"},
          "resource": {"path": "/api/lessons", "method": "GET"}
      }
  )
  print(result)  # Should show allow/deny based on policy
  ```

#### 4. Audit Logs Not Appearing

**Symptoms**:
- No JSON logs visible in pod logs
- Grafana shows no audit events

**Solutions**:

- **Check AUDIT_LOG_LEVEL**:
  ```bash
  kubectl get deployment -n governance your-fastapi-app -o yaml | grep AUDIT_LOG_LEVEL
  ```
  Should be `INFO` or `DEBUG` for verbose logging.

- **Verify logger configuration**: Check that stdout logging is not being suppressed by application logging config.

- **Search logs for audit entries**:
  ```bash
  kubectl logs -n governance <fastapi-pod-name> | grep '"event_type":"policy_evaluation"'
  ```

- **Check log aggregation**: If using log aggregation (ELK, Loki), verify logs are being collected from the `governance.audit` logger.

#### 5. Policy Bundle Not Reloading

**Symptoms**:
- Policy changes don't take effect
- Metric `governance_policy_bundle_reload_total{status="success"}` not incrementing
- OPA logs don't show "bundle loaded" messages

**Solutions**:

- **Verify ConfigMap was updated**:
  ```bash
  kubectl get configmap -n governance governance-policy-bundle -o yaml
  ```

- **Check OPA is watching for changes**: Ensure OPA config has bundle watching enabled:
  ```yaml
  bundles:
    governance:
      resource: /policies
      polling:
        min_delay_seconds: 10
        max_delay_seconds: 30
  ```

- **Force OPA pod restart** (if ConfigMap update doesn't trigger reload):
  ```bash
  kubectl rollout restart deployment -n governance opa-policy-engine
  ```

- **Check for Rego syntax errors**: OPA won't load a bundle with syntax errors:
  ```bash
  kubectl logs -n governance -l app=opa-policy-engine | grep -i error
  ```

#### 6. Metrics Not Appearing in Prometheus

**Symptoms**:
- Grafana dashboards show "No data"
- Prometheus target shows as down

**Solutions**:

- **Verify `/metrics` endpoint is accessible**:
  ```bash
  kubectl port-forward -n governance <fastapi-pod-name> 8000:8000
  curl http://localhost:8000/metrics | grep governance_
  ```

- **Check ServiceMonitor is applied** (if using Prometheus Operator):
  ```bash
  kubectl get servicemonitor -n governance
  ```

- **Verify Prometheus is scraping the target**:
  - Go to Prometheus UI → Status → Targets
  - Look for `governance-backend` or similar
  - Check for errors

- **Check service selector labels match**:
  ```bash
  kubectl get svc -n governance your-fastapi-app -o yaml
  kubectl get pods -n governance -l <labels-from-service>
  ```

### Debugging Tips

#### Enable DEBUG Logging

Set `AUDIT_LOG_LEVEL=DEBUG` to see all policy evaluations:

```bash
kubectl set env deployment/your-fastapi-app -n governance AUDIT_LOG_LEVEL=DEBUG
```

This will log every policy check (allow and deny) with full context.

#### Test OPA Policies Directly

Use `opa` CLI or curl to test policies directly:

```bash
# Port-forward to OPA
kubectl port-forward -n governance svc/opa-policy-engine 8181:8181

# Test a policy
curl -X POST http://localhost:8181/v1/data/dreamseedai/access_control/allow \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "user": {"id": "test123", "role": "student"},
      "resource": {"path": "/api/lessons", "method": "GET"}
    }
  }'
```

#### Check Policy Evaluation Metrics

Query Prometheus for policy evaluation patterns:

```promql
# Total evaluations by result
sum by (result) (governance_policy_evaluations_total)

# Denial rate over time
rate(governance_policy_deny_total[5m])

# Error rate (should be 0)
rate(governance_policy_errors_total[5m])

# Evaluation latency
histogram_quantile(0.95, rate(governance_policy_evaluation_duration_seconds_bucket[5m]))
```

#### Review Policy Bundle Loading

Check OPA logs for bundle status:

```bash
kubectl logs -n governance -l app=opa-policy-engine | grep -E "bundle|policy"
```

Look for messages like:
- `Bundle loaded successfully`
- `Activated bundle governance`
- Any error messages about policy compilation

#### Increase Log Verbosity

For more detailed OPA logging, update OPA deployment args:

```yaml
args:
  - "run"
  - "--server"
  - "--addr=:8181"
  - "--log-level=debug"  # Add this
  - "--config-file=/config/config.yaml"
  - "--bundle=/policies"
```

### Getting Help

If issues persist:

1. **Collect diagnostic information**:
   ```bash
   kubectl describe pod -n governance <pod-name>
   kubectl logs -n governance <pod-name> --previous  # If pod crashed
   kubectl get events -n governance --sort-by='.lastTimestamp'
   ```

2. **Check Prometheus metrics** for patterns (denial spikes, error rates, latency)

3. **Review audit logs** for specific denied requests and reasons

4. **Test policies in isolation** using OPA CLI or playground

5. **Consult Phase 1 documentation** for Rego policy syntax and testing

---

## Summary

The DreamSeedAI Governance Backend provides a production-ready policy enforcement solution with:

- **Centralized Policy Engine** via OPA for consistent, auditable decisions
- **FastAPI Integration** through decorators and middleware
- **Real-Time Monitoring** with Prometheus metrics and Grafana dashboards
- **Comprehensive Audit Logging** with structured JSON output
- **Kubernetes-Native Deployment** with auto-scaling and health checks

By following this documentation, you can deploy, monitor, and maintain a robust governance system that enforces policies across all API endpoints while providing full visibility into access decisions.

For additional resources:
- **Phase 1**: Kubernetes + Rego policies (`governance/ops/k8s/`)
- **Phase 2**: FastAPI backend integration (`governance/backend/`)
- **Phase 3**: Monitoring & audit logging (this document)

