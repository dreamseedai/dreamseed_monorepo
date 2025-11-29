"""Metrics for DreamSeedAI governance policy layer.

This module defines Prometheus metrics for monitoring policy evaluations,
policy decisions, content filtering, approval workflows, data access,
AI tutor sessions, and other governance-related events. Each metric includes
a descriptive help string and relevant labels for dimensional analysis.

Metrics:
- Policy evaluation metrics: track total evaluations, denials, errors and evaluation durations.
- Policy bundle metrics: track policy bundle reload events and current version.
- AI content metrics: track AI-generated content filtered by policy.
- AI behavior metrics: track enforcement of AI behavior policies (response truncation, link blocking, etc.).
- AI tutor session metrics: track usage of AI tutor sessions (count, active sessions, durations).
- Approval workflow metrics: track approval request counts and pending approvals.
- Data protection metrics: track data access attempts.

All metrics are defined using prometheus_client and are registered on import.
The FastAPI app should expose these on a /metrics endpoint.
"""

from typing import Optional
from prometheus_client import Counter, Histogram, Gauge


# Policy evaluation metrics
policy_evaluations_total = Counter(
    "governance_policy_evaluations_total",
    "Total number of policy evaluations",
    ["policy", "result"],
)
# Tracks the number of times any policy has been evaluated.
# Labels:
#   policy: The name or category of the policy evaluated (e.g., access_control, data_protection).
#   result: The outcome of the evaluation (e.g., "allow", "deny").

policy_deny_total = Counter(
    "governance_policy_deny_total",
    "Total number of policy denials",
    ["policy", "user_role"],
)
# Tracks the number of policy evaluation outcomes that resulted in a denial.
# Labels:
#   policy: The policy that caused the denial.
#   user_role: The role of the user whose action was denied (e.g., student, teacher, parent, admin).

policy_errors_total = Counter(
    "governance_policy_errors_total",
    "Total number of policy evaluation errors",
    ["policy"],
)
# Counts the number of policy evaluation attempts that resulted in an error (e.g., OPA or system errors).
# Labels:
#   policy: The policy being evaluated when the error occurred.

policy_evaluation_duration_seconds = Histogram(
    "governance_policy_evaluation_duration_seconds",
    "Policy evaluation duration in seconds",
    ["policy"],
)
# Measures the duration of policy evaluations (performance of the policy engine).
# Labels:
#   policy: The policy being evaluated. This histogram can be used to calculate latency percentiles (e.g., p95, p99).

# Policy bundle (OPA policy package) metrics
policy_bundle_reload_total = Counter(
    "governance_policy_bundle_reload_total",
    "Total number of policy bundle reloads",
    ["status"],
)
# Counts attempts to reload the policy bundle (hot-reload events).
# Labels:
#   status: The outcome of the reload attempt (e.g., "success", "error").

policy_bundle_version = Gauge(
    "governance_policy_bundle_version", "Current policy bundle version"
)
# Tracks the current version of the loaded policy bundle.
# This gauge should be updated whenever a new policy bundle is successfully loaded.

# AI content filtering metrics
ai_content_filtered_total = Counter(
    "governance_ai_content_filtered_total",
    "Total number of AI content filtered",
    ["filter_type", "severity"],
)
# Counts instances where AI-generated content was filtered or blocked due to content policy.
# Labels:
#   filter_type: Category of content filtered (e.g., profanity, violence, etc.).
#   severity: Severity level of the filtered content (e.g., low, high).

# AI tutor session usage metrics
ai_tutor_sessions_total = Counter(
    "governance_ai_tutor_sessions_total",
    "Total number of AI tutor sessions",
    ["user_role", "status"],
)
# Tracks events related to AI tutor sessions.
# Labels:
#   user_role: The role of the user for the session (e.g., student, teacher).
#   status: The session event status (e.g., "started", "completed", "timeout").

ai_tutor_session_duration_seconds = Histogram(
    "governance_ai_tutor_session_duration_seconds",
    "Duration of AI tutor sessions in seconds",
    ["user_role"],
)
# Measures the duration of AI tutor sessions.
# Labels:
#   user_role: The role of the user for the session. This histogram tracks how long each session lasted.

ai_tutor_sessions_active = Gauge(
    "governance_ai_tutor_sessions_active", "Current number of active AI tutor sessions"
)
# Tracks the current number of ongoing AI tutor sessions.
# This gauge is incremented when a session starts and decremented when a session ends.

# Approval workflow metrics
approval_requests_total = Counter(
    "governance_approval_requests_total",
    "Total number of approval requests",
    ["action_type", "status"],
)
# Counts events in the approval workflow.
# Labels:
#   action_type: The type of action requiring approval (e.g., "delete_lesson", "export_data").
#   status: The status of the approval event (e.g., "pending", "approved", "denied").
# Increment with status="pending" when a request is created, and with "approved"/"denied" when resolved.

approval_pending = Gauge("governance_approval_pending", "Number of pending approvals")
# Tracks the current number of approval requests that are pending (awaiting decision).
# This gauge increases when a new approval request is created and decreases when a request is approved or denied.

# Data protection metrics
data_access_total = Counter(
    "governance_data_access_total",
    "Total number of data access attempts",
    ["data_type", "result"],
)
# Counts attempts to access protected or sensitive data.
# Labels:
#   data_type: The category of data accessed (e.g., "personal_info", "exam_scores").
#   result: The outcome of the access attempt (e.g., "allowed", "denied").

# AI behavior policy enforcement metrics
ai_response_truncated_total = Counter(
    "governance_ai_response_truncated_total",
    "Total number of AI responses truncated due to length policy",
)
# Counts how many times an AI response was truncated because it exceeded the allowed length.

ai_external_links_blocked_total = Counter(
    "governance_ai_external_links_blocked_total",
    "Total number of external links blocked in AI responses",
)
# Counts how many times an external link was removed or blocked from an AI-generated response due to policy.

ai_academic_misconduct_prevented_total = Counter(
    "governance_ai_academic_misconduct_prevented_total",
    "Total number of academic misconduct attempts prevented by AI policy",
)
# Counts instances where the AI refused a user request due to academic integrity policy (e.g., not solving an exam or assignment for the user).

# Rate limiting policy metrics
api_call_limit_exceeded_total = Counter(
    "governance_rate_limit_api_call_exceeded_total",
    "Total number of times API call rate limit was exceeded",
)
# Counts the number of user API calls that were blocked because the API rate limit was exceeded.

session_time_limit_exceeded_total = Counter(
    "governance_rate_limit_session_time_exceeded_total",
    "Total number of times an AI tutor session time limit was exceeded",
)
# Counts how many AI tutor sessions were terminated or blocked due to exceeding the allowed session duration.

resource_quota_exceeded_total = Counter(
    "governance_rate_limit_resource_quota_exceeded_total",
    "Total number of times a resource quota was exceeded",
)
# Counts the number of times a user exceeded a resource usage quota (e.g., storage quota), resulting in a denial.


def record_policy_evaluation(policy: str, result: str, duration: float) -> None:
    """Record a completed policy evaluation.

    Increments the total policy evaluations counter and observes the evaluation duration.
    Should be called for each policy evaluation that returns a decision.

    Args:
        policy (str): The name or category of the policy evaluated.
        result (str): The result of the evaluation ("allow" or "deny").
        duration (float): The time taken for the evaluation (in seconds).
    """
    # Update total evaluations count and latency histogram
    policy_evaluations_total.labels(policy=policy, result=result).inc()
    policy_evaluation_duration_seconds.labels(policy=policy).observe(duration)


def increment_policy_deny(policy: str, user_role: str) -> None:
    """Increment the policy denial counter for a given policy and user role.

    Call this when a policy evaluation results in a denial (access denied).

    Args:
        policy (str): The name of the policy that denied the action.
        user_role (str): The role of the user whose action was denied.
    """
    policy_deny_total.labels(policy=policy, user_role=user_role).inc()


def increment_policy_error(policy: str) -> None:
    """Increment the policy error counter for a given policy.

    Call this when a policy evaluation fails due to an error.

    Args:
        policy (str): The name of the policy being evaluated when an error occurred.
    """
    policy_errors_total.labels(policy=policy).inc()


def record_policy_bundle_reload(status: str, version: Optional[float] = None) -> None:
    """Record a policy bundle reload attempt.

    Increments the policy bundle reload counter with the given status.
    If a new version is provided on a successful reload, updates the bundle version gauge.

    Args:
        status (str): Outcome of the reload attempt ("success" or "error").
        version (float, optional): New policy bundle version if reload was successful.
    """
    policy_bundle_reload_total.labels(status=status).inc()
    if status == "success" and version is not None:
        # Update current bundle version on successful reload
        policy_bundle_version.set(version)


def increment_content_filtered(filter_type: str, severity: str) -> None:
    """Increment the AI content filtered counter.

    Call this when AI-generated content is filtered/blocked by the content policy.

    Args:
        filter_type (str): Category of content that was filtered (e.g., "profanity", "violence").
        severity (str): Severity level of the content filtered (e.g., "low", "high").
    """
    ai_content_filtered_total.labels(filter_type=filter_type, severity=severity).inc()


def start_tutor_session(user_role: str) -> None:
    """Record the start of an AI tutor session.

    Increments the tutor sessions counter (status="started") and the active sessions gauge.

    Args:
        user_role (str): The role of the user starting the session.
    """
    ai_tutor_sessions_total.labels(user_role=user_role, status="started").inc()
    ai_tutor_sessions_active.inc()


def end_tutor_session(user_role: str, duration: float, timed_out: bool = False) -> None:
    """Record the end of an AI tutor session.

    Increments the tutor sessions counter (with status "completed" or "timeout"), updates the session duration histogram, and decrements the active sessions gauge.

    Args:
        user_role (str): The role of the user who had the session.
        duration (float): The duration of the session in seconds.
        timed_out (bool): True if the session ended due to a time limit (timeout), False if ended normally.
    """
    status = "timeout" if timed_out else "completed"
    ai_tutor_sessions_total.labels(user_role=user_role, status=status).inc()
    ai_tutor_session_duration_seconds.labels(user_role=user_role).observe(duration)
    ai_tutor_sessions_active.dec()


def record_approval_request(action_type: str) -> None:
    """Record the creation of a new approval request.

    Increments the approval requests counter (status="pending") and increases the pending approvals gauge.

    Args:
        action_type (str): The type of action requiring approval.
    """
    approval_requests_total.labels(action_type=action_type, status="pending").inc()
    approval_pending.inc()


def approve_request(action_type: str) -> None:
    """Record the approval of a request.

    Increments the approval requests counter (status="approved") and decreases the pending approvals gauge.

    Args:
        action_type (str): The type of action that was approved.
    """
    approval_requests_total.labels(action_type=action_type, status="approved").inc()
    approval_pending.dec()


def deny_request(action_type: str) -> None:
    """Record the denial of a request.

    Increments the approval requests counter (status="denied") and decreases the pending approvals gauge.

    Args:
        action_type (str): The type of action that was denied.
    """
    approval_requests_total.labels(action_type=action_type, status="denied").inc()
    approval_pending.dec()


def increment_data_access(data_type: str, result: str) -> None:
    """Increment the data access counter for a given data type and result.

    Call this whenever a protected data access is attempted.

    Args:
        data_type (str): The category of data that was accessed.
        result (str): The outcome of the access attempt ("allowed" or "denied").
    """
    data_access_total.labels(data_type=data_type, result=result).inc()


def increment_response_truncated() -> None:
    """Increment the counter for truncated AI responses.

    Call this when an AI response is truncated due to the length policy.
    """
    ai_response_truncated_total.inc()


def increment_external_link_blocked() -> None:
    """Increment the counter for external links blocked.

    Call this when an external link in an AI response is removed/blocked due to policy.
    """
    ai_external_links_blocked_total.inc()


def increment_misconduct_prevented() -> None:
    """Increment the counter for prevented academic misconduct attempts.

    Call this when the AI refuses a request due to the academic misconduct policy.
    """
    ai_academic_misconduct_prevented_total.inc()
