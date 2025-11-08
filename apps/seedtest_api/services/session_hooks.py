"""Session lifecycle hooks for triggering background tasks.

This module provides hooks that can be called during session lifecycle events
(e.g., session completion) to trigger background processing like IRT theta updates.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def on_session_complete(user_id: str, session_id: Optional[str] = None) -> None:
    """Hook called when a session is completed.
    
    Triggers background tasks:
    - IRT theta update (if enabled)
    - Other post-session analytics
    
    Args:
        user_id: User identifier
        session_id: Session ID (optional, for logging)
    """
    # Check if IRT online update is enabled
    enable_irt_update = os.getenv("ENABLE_IRT_ONLINE_UPDATE", "false").lower() == "true"
    
    if enable_irt_update:
        try:
            from .irt_update_service import trigger_ability_update
            
            logger.info(
                f"Triggering theta update for user={user_id} session={session_id}",
                extra={"user_id": user_id, "session_id": session_id, "event": "session_complete"},
            )
            
            # Trigger non-blocking theta update
            trigger_ability_update(user_id, session_id, background=True)
            
            logger.info(
                f"Theta update triggered successfully for user={user_id} session={session_id}",
                extra={"user_id": user_id, "session_id": session_id},
            )
        except Exception as e:
            # Don't fail session completion if theta update fails
            logger.warning(
                f"Failed to trigger theta update for user={user_id} session={session_id}: {e}",
                extra={"user_id": user_id, "session_id": session_id, "error": str(e)},
                exc_info=True,
            )


def on_session_start(user_id: str, session_id: Optional[str] = None) -> None:
    """Hook called when a session is started.
    
    Currently a placeholder for future functionality.
    
    Args:
        user_id: User identifier
        session_id: Session ID (optional)
    """
    pass


__all__ = ["on_session_complete", "on_session_start"]
