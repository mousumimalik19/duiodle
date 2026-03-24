"""
Configuration Management for Duiodle Backend.

This module provides centralized configuration using Pydantic Settings.
All settings are loaded from environment variables or a .env file.

Security Features:
- API keys stored as SecretStr (never logged/serialized)
- Startup validation for required configuration
- Clear error messages for missing settings

Usage:
    from app.core.config import settings
    
    # Access regular settings
    provider = settings.VISION_PROVIDER
    
    # Access secrets (explicit call required)
    api_key = settings.OPENAI_API_KEY.get_secret_value()
    
    # Check if vision is properly configured
    if settings.is_vision_enabled:
        processor = create_processor()
"""

from __future__ import annotations

import logging
import sys
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, List, Optional, Set

from pydantic import (
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# ENUMERATIONS
# =============================================================================

class VisionProvider(str, Enum):
    """Supported vision processing providers."""
    MOCK = "mock"
    OPENAI = "openai"
    GEMINI = "gemini"


class Environment(str, Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# =============================================================================
# SETTINGS CLASS
# =============================================================================

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or .env file.
    The .env file should be in the backend directory.
    """
    
    # -------------------------------------------------------------------------
    # Project Settings
    # -------------------------------------------------------------------------
    
    PROJECT_NAME: str = Field(
        default="Duiodle",
        description="Application display name"
    )
    
    PROJECT_VERSION: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    PROJECT_DESCRIPTION: str = Field(
        default="Where Doodles Become Interfaces",
        description="Application tagline"
    )
    
    API_V1_STR: str = Field(
        default="/api/v1",
        description="API v1 prefix"
    )
    
    # -------------------------------------------------------------------------
    # Environment Settings
    # -------------------------------------------------------------------------
    
    DEBUG_MODE: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment"
    )
    
    # -------------------------------------------------------------------------
    # API Keys (SECRETS)
    # -------------------------------------------------------------------------
    
    OPENAI_API_KEY: SecretStr = Field(
        default=SecretStr(""),
        description="OpenAI API key for GPT-4o Vision"
    )
    
    GEMINI_API_KEY: SecretStr = Field(
        default=SecretStr(""),
        description="Google Gemini API key"
    )
    
    # -------------------------------------------------------------------------
    # Vision Provider Settings
    # -------------------------------------------------------------------------
    
    VISION_PROVIDER: VisionProvider = Field(
        default=VisionProvider.MOCK,
        description="Which AI provider to use for vision"
    )
    
    VISION_MODEL_OPENAI: str = Field(
        default="gpt-4o",
        description="OpenAI model for vision"
    )
    
    VISION_MODEL_GEMINI: str = Field(
        default="gemini-2.0-flash-exp",
        description="Gemini model for vision"
    )
    
    VISION_MAX_TOKENS: int = Field(
        default=4096,
        ge=100,
        le=16384,
        description="Max tokens for vision response"
    )
    
    VISION_TEMPERATURE: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for vision API"
    )
    
    # -------------------------------------------------------------------------
    # CORS Settings
    # -------------------------------------------------------------------------
    
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origins"
    )
    
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="Allow credentials in CORS"
    )
    
    # -------------------------------------------------------------------------
    # Upload Settings
    # -------------------------------------------------------------------------
    
    MAX_UPLOAD_SIZE_MB: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum upload size in MB"
    )
    
    UPLOAD_DIR: str = Field(
        default="/tmp/duiodle_uploads",
        description="Temporary upload directory"
    )
    
    ALLOWED_EXTENSIONS: Set[str] = Field(
        default={".png", ".jpg", ".jpeg", ".webp", ".gif"},
        description="Allowed file extensions"
    )
    
    # -------------------------------------------------------------------------
    # Logging Settings
    # -------------------------------------------------------------------------
    
    LOG_LEVEL: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    
    LOG_FORMAT: str = Field(
        default="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        description="Log format string"
    )
    
    # -------------------------------------------------------------------------
    # Server Settings
    # -------------------------------------------------------------------------
    
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    
    PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port"
    )
    
    # -------------------------------------------------------------------------
    # Pydantic Configuration
    # -------------------------------------------------------------------------
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_extensions(cls, v: Any) -> Set[str]:
        """Parse extensions from comma-separated string."""
        if isinstance(v, str):
            return {ext.strip().lower() for ext in v.split(",") if ext.strip()}
        return v
    
    @model_validator(mode="after")
    def validate_api_keys_for_provider(self) -> "Settings":
        """Validate that API keys are present for selected provider."""
        if self.ENVIRONMENT == Environment.PRODUCTION:
            if self.VISION_PROVIDER == VisionProvider.OPENAI:
                if not self.OPENAI_API_KEY.get_secret_value():
                    raise ValueError(
                        "OPENAI_API_KEY is required when VISION_PROVIDER=openai in production"
                    )
            elif self.VISION_PROVIDER == VisionProvider.GEMINI:
                if not self.GEMINI_API_KEY.get_secret_value():
                    raise ValueError(
                        "GEMINI_API_KEY is required when VISION_PROVIDER=gemini in production"
                    )
        return self
    
    # -------------------------------------------------------------------------
    # Computed Properties
    # -------------------------------------------------------------------------
    
    @property
    def max_upload_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    @property
    def is_development(self) -> bool:
        """Check if in development mode."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if in production mode."""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    @property
    def is_vision_enabled(self) -> bool:
        """Check if real vision processing is available."""
        if self.VISION_PROVIDER == VisionProvider.MOCK:
            return True
        if self.VISION_PROVIDER == VisionProvider.OPENAI:
            return bool(self.OPENAI_API_KEY.get_secret_value())
        if self.VISION_PROVIDER == VisionProvider.GEMINI:
            return bool(self.GEMINI_API_KEY.get_secret_value())
        return False
    
    @property
    def active_api_key(self) -> Optional[str]:
        """Get API key for the active provider."""
        if self.VISION_PROVIDER == VisionProvider.OPENAI:
            return self.OPENAI_API_KEY.get_secret_value() or None
        if self.VISION_PROVIDER == VisionProvider.GEMINI:
            return self.GEMINI_API_KEY.get_secret_value() or None
        return None
    
    def get_vision_model(self) -> str:
        """Get model name for active provider."""
        if self.VISION_PROVIDER == VisionProvider.OPENAI:
            return self.VISION_MODEL_OPENAI
        if self.VISION_PROVIDER == VisionProvider.GEMINI:
            return self.VISION_MODEL_GEMINI
        return "mock"


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    Get the singleton settings instance.
    
    Uses lru_cache to ensure only one instance exists.
    """
    return Settings()


# Create singleton for easy import
settings = get_settings()


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_vision_config() -> tuple[bool, str]:
    """
    Validate vision configuration.
    
    Returns:
        Tuple of (is_valid, message)
    """
    provider = settings.VISION_PROVIDER
    
    if provider == VisionProvider.MOCK:
        return True, "Mock vision processor (no API key needed)"
    
    if provider == VisionProvider.OPENAI:
        if settings.OPENAI_API_KEY.get_secret_value():
            return True, f"OpenAI vision enabled ({settings.VISION_MODEL_OPENAI})"
        return False, "OPENAI_API_KEY is missing"
    
    if provider == VisionProvider.GEMINI:
        if settings.GEMINI_API_KEY.get_secret_value():
            return True, f"Gemini vision enabled ({settings.VISION_MODEL_GEMINI})"
        return False, "GEMINI_API_KEY is missing"
    
    return False, f"Unknown provider: {provider}"


def check_startup_requirements() -> None:
    """
    Validate configuration at startup.
    
    Logs warnings in development, exits in production if critical.
    """
    logger = logging.getLogger(__name__)
    
    # Configure logging
    logging.basicConfig(
        level=settings.LOG_LEVEL.value,
        format=settings.LOG_FORMAT,
    )
    
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT.value}")
    logger.info(f"Debug mode: {settings.DEBUG_MODE}")
    
    # Validate vision
    is_valid, message = validate_vision_config()
    
    if is_valid:
        logger.info(f"Vision: {message}")
    else:
        logger.error(f"Vision error: {message}")
        
        if settings.is_production:
            logger.critical("Cannot start in production without valid vision config")
            sys.exit(1)
        else:
            logger.warning("Falling back to mock vision processor")
    
    # Create upload directory
    upload_path = Path(settings.UPLOAD_DIR)
    try:
        upload_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Upload directory: {upload_path}")
    except Exception as e:
        logger.warning(f"Could not create upload directory: {e}")
    
    logger.info("Startup checks completed")


# =============================================================================
# .ENV TEMPLATE GENERATOR
# =============================================================================

def generate_env_template() -> str:
    """Generate .env.example content."""
    return '''# =============================================================================
# DUIODLE BACKEND CONFIGURATION
# =============================================================================
# Copy this file to .env and configure your values.
# NEVER commit .env to version control!

# -----------------------------------------------------------------------------
# Project Settings
# -----------------------------------------------------------------------------
PROJECT_NAME=Duiodle
DEBUG_MODE=false
ENVIRONMENT=development

# -----------------------------------------------------------------------------
# API Keys (REQUIRED for real AI vision)
# -----------------------------------------------------------------------------
# OpenAI: https://platform.openai.com/api-keys
OPENAI_API_KEY=

# Gemini: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=

# -----------------------------------------------------------------------------
# Vision Provider
# -----------------------------------------------------------------------------
# Options: mock, openai, gemini
# - mock: Uses OpenCV (free, good for development)
# - openai: Uses GPT-4o Vision API
# - gemini: Uses Gemini 2.0 Flash API
VISION_PROVIDER=mock
VISION_MODEL_OPENAI=gpt-4o
VISION_MODEL_GEMINI=gemini-2.0-flash-exp

# -----------------------------------------------------------------------------
# CORS Settings
# -----------------------------------------------------------------------------
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# -----------------------------------------------------------------------------
# Upload Settings
# -----------------------------------------------------------------------------
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=/tmp/duiodle_uploads

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_LEVEL=INFO

# -----------------------------------------------------------------------------
# Server
# -----------------------------------------------------------------------------
HOST=0.0.0.0
PORT=8000
'''


if __name__ == "__main__":
    print(generate_env_template())
