"""Settings module for backward compatibility.

This module re-exports the Config class from core.config as Settings,
providing backward compatibility for legacy code that imports from settings.
"""

from __future__ import annotations

from .core.config import Config

# Re-export Config as Settings for backward compatibility
Settings = Config

# Create a singleton instance
settings = Config()

__all__ = ["Settings", "settings"]

