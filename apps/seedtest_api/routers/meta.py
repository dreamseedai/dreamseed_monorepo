from __future__ import annotations

from fastapi import APIRouter

from ..settings import settings
from ..services import legacy_mpc_adapter as legacy


router = APIRouter(prefix=f"{settings.API_PREFIX}", tags=["meta"])


@router.get("/meta", summary="API meta and adapter mode")
def get_meta():
    enabled = bool(getattr(settings, "USE_MPC_LEGACY_READONLY", False))
    src = "none"
    try:
        if enabled and hasattr(legacy, "is_pg_configured") and legacy.is_pg_configured():
            src = "postgres"
        elif enabled and hasattr(legacy, "is_mysql_configured") and legacy.is_mysql_configured():
            src = "mysql"
        elif enabled and hasattr(legacy, "is_http_configured") and legacy.is_http_configured():
            src = "http"
    except Exception:
        # Keep defaults if any detection errors
        pass

    return {
        "api_prefix": settings.API_PREFIX,
        "legacy_readonly_enabled": enabled,
        "legacy_source": src,
        "features": {
            "idempotency": bool(getattr(settings, "ENABLE_IDEMPOTENCY", True)),
            "if_match_required": bool(getattr(settings, "REQUIRE_IF_MATCH_PRECONDITION", False)),
        },
    }
