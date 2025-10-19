from fastapi import Depends
from .security import get_current_user
from ..rls_context import rls_session


def get_rls_db(user=Depends(get_current_user)):
    roles = user.get("roles") or [user.get("role")] if user.get("role") else []
    is_admin = any(r.lower() == 'admin' for r in roles)
    with rls_session(user.get("org_id"), is_admin=is_admin) as db:
        yield db
