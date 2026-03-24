"""
API Module

This module provides the versioned API routers for the Duiodle backend.

Available API versions:
- v1: Current stable API

Usage:
    from app.api import api_router
    app.include_router(api_router)
"""

from fastapi import APIRouter

from .v1 import router as v1_router

# Create main API router
api_router = APIRouter()

# Include versioned routers
api_router.include_router(v1_router, prefix="/v1", tags=["v1"])

# Export
__all__ = ["api_router", "v1_router"]
