"""
Legacy settings module for backward compatibility.

This module is kept for backward compatibility with older code that imports
from `seedtest_api.settings`. New code should use `seedtest_api.core.config.Config`.
"""

from .core.config import Config

# Create a Settings class that mirrors Config for backward compatibility
Settings = Config

# Default instance
settings = Settings()

__all__ = ["Settings", "settings"]
