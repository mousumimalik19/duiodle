"""
Core module for Duiodle backend.

Provides configuration management and shared utilities.
"""

from app.core.config import (
    settings,
    get_settings,
    Settings,
    VisionProvider,
    Environment,
    LogLevel,
    validate_vision_config,
    check_startup_requirements,
)

__all__ = [
    "settings",
    "get_settings",
    "Settings",
    "VisionProvider",
    "Environment",
    "LogLevel",
    "validate_vision_config",
    "check_startup_requirements",
]
