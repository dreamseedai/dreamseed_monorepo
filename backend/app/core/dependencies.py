"""
Common FastAPI dependencies for authentication and authorization
"""
from app.core.users import current_active_user

# Re-export for backward compatibility
get_current_user = current_active_user
