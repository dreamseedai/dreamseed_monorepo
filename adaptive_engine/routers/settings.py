from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, status

from adaptive_engine.config import (
    SelectionPolicy,
    clear_selection_policy,
    get_selection_policy,
    set_selection_policy,
    get_settings,
    list_selection_namespaces,
)


router = APIRouter(prefix="/api/settings", tags=["settings"])


def _require_admin(token: str | None) -> None:
    s = get_settings()
    if s.admin_token and token != s.admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")


@router.get("/selection", response_model=SelectionPolicy)
def get_selection(namespace: str | None = None):
    # no auth for read
    return get_selection_policy(namespace=namespace)


@router.patch("/selection", response_model=SelectionPolicy)
def patch_selection(policy: SelectionPolicy, namespace: str | None = None, x_admin_token: str | None = Header(default=None)) -> SelectionPolicy:
    _require_admin(x_admin_token)
    set_selection_policy(policy, namespace=namespace)
    return get_selection_policy(namespace=namespace)


@router.delete("/selection", response_model=SelectionPolicy)
def delete_selection(namespace: str | None = None, x_admin_token: str | None = Header(default=None)) -> SelectionPolicy:
    _require_admin(x_admin_token)
    clear_selection_policy(namespace=namespace)
    return get_selection_policy(namespace=namespace)


@router.post("/selection/reset-to-env", response_model=SelectionPolicy)
def reset_selection_to_env(namespace: str | None = None, x_admin_token: str | None = Header(default=None)) -> SelectionPolicy:
    _require_admin(x_admin_token)
    clear_selection_policy(namespace=namespace)
    return get_selection_policy(namespace=namespace)


@router.get("", response_model=dict)
def get_effective_settings(namespace: str | None = None) -> dict:
    s = get_settings()
    from adaptive_engine.config import get_selection_policy_info
    p, source, resolved_ns, last = get_selection_policy_info(namespace=namespace, resolve_hierarchy=True)
    return {
        "session_backend": s.session_backend,
        "redis_url": s.redis_url,
        "redis_key_prefix": s.redis_key_prefix,
        "session_ttl_sec": s.session_ttl_sec,
        "estimator": {
            "method": s.estimator_method,
            "prior_mean": s.estimator_prior_mean,
            "prior_sd": s.estimator_prior_sd,
        },
        "stop": {
            "max_items": s.stop_max_items,
            "time_limit_sec": s.stop_time_limit_sec,
            "se_threshold": s.stop_se_threshold,
        },
        "scale": {
            "mean_ref": s.scale_mean_ref,
            "sd_ref": s.scale_sd_ref,
        },
        "selection_policy": p.model_dump(),
        "selection_policy_source": source,
        "selection_policy_resolved_namespace": resolved_ns,
        "selection_policy_last_updated": last,
        "selection_policy_ttl_sec": s.selection_policy_ttl_sec,
        "namespace": namespace,
    }


@router.get("/estimator", response_model=dict)
def get_estimator_settings():
    s = get_settings()
    return {"method": s.estimator_method, "prior_mean": s.estimator_prior_mean, "prior_sd": s.estimator_prior_sd}


@router.patch("/estimator", response_model=dict)
def patch_estimator_settings(payload: dict, x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    s = get_settings()
    if "method" in payload and isinstance(payload["method"], str):
        setattr(s, "estimator_method", payload["method"])  # type: ignore[arg-type]
    if "prior_mean" in payload and isinstance(payload["prior_mean"], (int, float)):
        setattr(s, "estimator_prior_mean", float(payload["prior_mean"]))
    if "prior_sd" in payload and isinstance(payload["prior_sd"], (int, float)):
        setattr(s, "estimator_prior_sd", float(payload["prior_sd"]))
    return {"method": s.estimator_method, "prior_mean": s.estimator_prior_mean, "prior_sd": s.estimator_prior_sd}


@router.get("/scale", response_model=dict)
def get_scale_settings():
    s = get_settings()
    return {"mean_ref": s.scale_mean_ref, "sd_ref": s.scale_sd_ref}


@router.patch("/scale", response_model=dict)
def patch_scale_settings(payload: dict, x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    s = get_settings()
    if "mean_ref" in payload and isinstance(payload["mean_ref"], (int, float)):
        setattr(s, "scale_mean_ref", float(payload["mean_ref"]))
    if "sd_ref" in payload and isinstance(payload["sd_ref"], (int, float)):
        setattr(s, "scale_sd_ref", float(payload["sd_ref"]))
    return {"mean_ref": s.scale_mean_ref, "sd_ref": s.scale_sd_ref}


@router.get("/stop", response_model=dict)
def get_stop_settings():
    s = get_settings()
    return {
        "max_items": s.stop_max_items,
        "time_limit_sec": s.stop_time_limit_sec,
        "se_threshold": s.stop_se_threshold,
    }


@router.patch("/stop", response_model=dict)
def patch_stop_settings(payload: dict, x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    s = get_settings()
    # Update allowed fields if present in payload
    if "max_items" in payload and isinstance(payload["max_items"], int):
        setattr(s, "stop_max_items", int(payload["max_items"]))
    if "time_limit_sec" in payload:
        v = payload["time_limit_sec"]
        setattr(s, "stop_time_limit_sec", (int(v) if v is not None else None))
    if "se_threshold" in payload and isinstance(payload["se_threshold"], (int, float)):
        setattr(s, "stop_se_threshold", float(payload["se_threshold"]))
    return {
        "max_items": s.stop_max_items,
        "time_limit_sec": s.stop_time_limit_sec,
        "se_threshold": s.stop_se_threshold,
    }


@router.get("/irt-updater", response_model=dict)
def get_irt_updater_settings():
    s = get_settings()
    return {
        "enabled": s.irt_update_enabled,
        "interval_sec": s.irt_update_interval_sec,
        "method": s.irt_update_method,
        "target_correct_rate": s.irt_target_correct_rate,
        "learning_rate": s.irt_learning_rate,
        "min_responses": s.irt_min_responses,
        "max_items_per_run": s.irt_update_max_items_per_run,
        "stats_view": s.irt_stats_view,
        "items_table": s.items_table,
        "change_log_table": s.irt_change_log_table,
    }


@router.patch("/irt-updater", response_model=dict)
def patch_irt_updater_settings(payload: dict, x_admin_token: str | None = Header(default=None)):
    _require_admin(x_admin_token)
    s = get_settings()
    # Booleans/flags
    if "enabled" in payload:
        setattr(s, "irt_update_enabled", bool(payload["enabled"]))
    if "interval_sec" in payload and isinstance(payload["interval_sec"], int):
        setattr(s, "irt_update_interval_sec", int(payload["interval_sec"]))
    # Method config
    if "method" in payload and isinstance(payload["method"], str):
        setattr(s, "irt_update_method", payload["method"])  # type: ignore[arg-type]
    if "target_correct_rate" in payload and isinstance(payload["target_correct_rate"], (int, float)):
        setattr(s, "irt_target_correct_rate", float(payload["target_correct_rate"]))
    if "learning_rate" in payload and isinstance(payload["learning_rate"], (int, float)):
        setattr(s, "irt_learning_rate", float(payload["learning_rate"]))
    if "min_responses" in payload:
        v = payload["min_responses"]
        setattr(s, "irt_min_responses", (int(v) if v is not None else None))
    if "max_items_per_run" in payload:
        v = payload["max_items_per_run"]
        setattr(s, "irt_update_max_items_per_run", (int(v) if v is not None else None))
    # Object names
    if "stats_view" in payload and isinstance(payload["stats_view"], str):
        setattr(s, "irt_stats_view", payload["stats_view"])  # type: ignore[arg-type]
    if "items_table" in payload and isinstance(payload["items_table"], str):
        setattr(s, "items_table", payload["items_table"])  # type: ignore[arg-type]
    if "change_log_table" in payload:
        v = payload["change_log_table"]
        setattr(s, "irt_change_log_table", (str(v) if v is not None else None))
    return {
        "enabled": s.irt_update_enabled,
        "interval_sec": s.irt_update_interval_sec,
        "method": s.irt_update_method,
        "target_correct_rate": s.irt_target_correct_rate,
        "learning_rate": s.irt_learning_rate,
        "min_responses": s.irt_min_responses,
        "max_items_per_run": s.irt_update_max_items_per_run,
        "stats_view": s.irt_stats_view,
        "items_table": s.items_table,
        "change_log_table": s.irt_change_log_table,
    }


@router.get("/namespaces", response_model=dict)
def list_namespaces(include_global: bool = True) -> dict:
    names = list_selection_namespaces(include_global=include_global)
    # also return resolved policy and metadata for each namespace for convenience
    from adaptive_engine.config import get_selection_policy_info
    policies = {}
    for ns in names:
        p, source, resolved_ns, last = get_selection_policy_info(namespace=(ns or None), resolve_hierarchy=True)
        policies[ns] = {
            "policy": p.model_dump(),
            "source": source,
            "resolved_namespace": resolved_ns,
            "last_updated": last,
        }
    return {"namespaces": names, "policies": policies}
