"""
API v1 Router Module

This module combines all v1 API routers into a single router
for clean integration with the main FastAPI application.

Routes included:
- /analyze/* - REST endpoints for sketch analysis
- /upload/* - File upload endpoints
- /ws/* - WebSocket endpoints for real-time updates

Usage in main.py:
    from app.api.v1 import router as api_v1_router
    app.include_router(api_v1_router, prefix="/api/v1")
"""

from fastapi import APIRouter

# Import routers from sub-modules
try:
    from .analyze import router as analyze_router
except ImportError:
    analyze_router = None

try:
    from .upload import router as upload_router
except ImportError:
    upload_router = None

try:
    from .live import router as live_router
except ImportError:
    live_router = None

# Create combined v1 router
router = APIRouter()

# Include available routers
if analyze_router:
    router.include_router(
        analyze_router,
        prefix="/analyze",
        tags=["Analyze"]
    )

if upload_router:
    router.include_router(
        upload_router,
        prefix="/upload",
        tags=["Upload"]
    )

if live_router:
    router.include_router(
        live_router,
        prefix="",  # WebSocket routes don't need prefix
        tags=["WebSocket"]
    )

# Export
__all__ = [
    "router",
    "analyze_router",
    "upload_router", 
    "live_router",
]
