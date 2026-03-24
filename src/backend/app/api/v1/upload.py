"""
Upload API Endpoint

This module provides the file upload and processing endpoint for Duiodle.
It handles image uploads, processes them through the AI pipeline, and
returns the structured UI tree along with generated React code.

Endpoints:
    POST /analyze - Upload and process a doodle image
"""

import os
import uuid
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    Depends,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.orchestrator import DuiodleOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Upload & Process"])


# =============================================================================
# Request/Response Models
# =============================================================================

class ProcessingMetadata(BaseModel):
    """Metadata about the processing job."""
    
    job_id: str = Field(..., description="Unique job identifier")
    theme: str = Field(..., description="Applied theme")
    motion_enabled: bool = Field(..., description="Motion effects enabled")
    motion_preset: Optional[str] = Field(None, description="Motion preset used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: str = Field(..., description="Processing timestamp")
    vision_provider: str = Field(..., description="Vision AI provider used")


class UITreeNode(BaseModel):
    """A node in the UI tree."""
    
    id: str = Field(..., description="Node identifier")
    type: str = Field(..., description="Component type")
    layout: Optional[str] = Field(None, description="Layout direction")
    style: Optional[Dict[str, Any]] = Field(None, description="Style properties")
    motion: Optional[Dict[str, Any]] = Field(None, description="Motion properties")
    children: List["UITreeNode"] = Field(default_factory=list)
    
    class Config:
        extra = "allow"


UITreeNode.model_rebuild()


class AnalyzeResponse(BaseModel):
    """Response from the analyze endpoint."""
    
    success: bool = Field(..., description="Processing success status")
    ui_tree: Dict[str, Any] = Field(..., description="Structured UI component tree")
    react_code: str = Field(..., description="Generated React component code")
    metadata: ProcessingMetadata = Field(..., description="Processing metadata")
    errors: List[str] = Field(default_factory=list, description="Any warnings or errors")


class AnalyzeErrorResponse(BaseModel):
    """Error response from the analyze endpoint."""
    
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ThemeInfo(BaseModel):
    """Information about an available theme."""
    
    name: str
    description: str
    preview_colors: Dict[str, str]


class PresetsResponse(BaseModel):
    """Response with available presets."""
    
    themes: List[ThemeInfo]
    motion_presets: List[str]


# =============================================================================
# Helper Functions
# =============================================================================

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/bmp",
}


def validate_upload(file: UploadFile) -> None:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file to validate.
        
    Raises:
        HTTPException: If validation fails.
    """
    # Check filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "No filename provided",
                "error_code": "MISSING_FILENAME"
            }
        )
    
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid file type: {ext}",
                "error_code": "INVALID_FILE_TYPE",
                "allowed": list(ALLOWED_EXTENSIONS)
            }
        )
    
    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid content type: {file.content_type}",
                "error_code": "INVALID_CONTENT_TYPE",
                "allowed": list(ALLOWED_MIME_TYPES)
            }
        )


async def save_upload(file: UploadFile, upload_dir: str) -> Path:
    """
    Save uploaded file to disk.
    
    Args:
        file: Uploaded file.
        upload_dir: Directory to save to.
        
    Returns:
        Path to saved file.
    """
    # Ensure upload directory exists
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = Path(upload_dir) / unique_filename
    
    # Save file
    content = await file.read()
    
    # Check file size
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "error": f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
                "error_code": "FILE_TOO_LARGE",
                "max_size_mb": settings.max_upload_size_mb
            }
        )
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_path


def cleanup_file(file_path: Path) -> None:
    """Remove uploaded file after processing."""
    try:
        if file_path.exists():
            os.remove(file_path)
            logger.debug(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")


# =============================================================================
# API Endpoints
# =============================================================================

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        400: {"model": AnalyzeErrorResponse, "description": "Validation error"},
        413: {"model": AnalyzeErrorResponse, "description": "File too large"},
        500: {"model": AnalyzeErrorResponse, "description": "Processing error"},
    },
    summary="Upload and analyze a UI sketch",
    description="""
    Upload a hand-drawn UI sketch and receive:
    - Structured UI component tree (JSON)
    - Generated React + Tailwind code
    - Applied theme and motion effects
    
    **Supported formats:** PNG, JPG, GIF, WebP, BMP
    **Max file size:** 10MB
    """
)
async def analyze_sketch(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="UI sketch image"),
    theme: str = Form(default="minimal", description="Design theme to apply"),
    enable_motion: bool = Form(default=False, description="Enable motion effects"),
    motion_preset: str = Form(default="fade_in", description="Motion animation preset"),
) -> JSONResponse:
    """
    Process an uploaded UI sketch through the Duiodle pipeline.
    
    This endpoint:
    1. Validates and saves the uploaded image
    2. Runs vision detection (AI or mock)
    3. Builds the UI component hierarchy
    4. Applies theme styling
    5. Adds motion effects (optional)
    6. Generates React + Tailwind code
    
    Args:
        file: The sketch image file.
        theme: Theme to apply (minimal, professional, playful, etc.).
        enable_motion: Whether to include Framer Motion animations.
        motion_preset: Animation preset to use.
        
    Returns:
        JSON response with UI tree and generated code.
    """
    start_time = datetime.utcnow()
    job_id = str(uuid.uuid4())
    file_path: Optional[Path] = None
    
    try:
        # Validate upload
        validate_upload(file)
        
        # Save file temporarily
        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            settings.temp_upload_dir
        )
        file_path = await save_upload(file, upload_dir)
        
        logger.info(f"Processing job {job_id}: {file.filename} with theme={theme}")
        
        # Initialize orchestrator
        orchestrator = DuiodleOrchestrator(
            theme=theme,
            enable_motion=enable_motion,
            motion_preset=motion_preset
        )
        
        # Process image
        result = orchestrator.process_image(str(file_path))
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Build response
        response = AnalyzeResponse(
            success=True,
            ui_tree=result.get("ui_tree", {}),
            react_code=result.get("react_code", ""),
            metadata=ProcessingMetadata(
                job_id=job_id,
                theme=theme,
                motion_enabled=enable_motion,
                motion_preset=motion_preset if enable_motion else None,
                processing_time_ms=processing_time,
                timestamp=datetime.utcnow().isoformat(),
                vision_provider=settings.vision_provider,
            ),
            errors=[]
        )
        
        # Schedule cleanup
        if file_path:
            background_tasks.add_task(cleanup_file, file_path)
        
        return JSONResponse(
            status_code=200,
            content=response.model_dump()
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        if file_path:
            background_tasks.add_task(cleanup_file, file_path)
        raise
        
    except Exception as e:
        logger.error(f"Processing error for job {job_id}: {e}", exc_info=True)
        
        # Cleanup on error
        if file_path:
            background_tasks.add_task(cleanup_file, file_path)
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "error_code": "PROCESSING_ERROR",
                "details": {
                    "job_id": job_id,
                    "stage": "unknown"
                }
            }
        )


@router.get(
    "/presets",
    response_model=PresetsResponse,
    summary="Get available themes and motion presets",
    description="Returns all available design themes and motion animation presets."
)
async def get_presets() -> PresetsResponse:
    """Get available themes and motion presets."""
    
    themes = [
        ThemeInfo(
            name="minimal",
            description="Clean and minimal design with subtle shadows",
            preview_colors={"primary": "#3B82F6", "background": "#FFFFFF", "text": "#1F2937"}
        ),
        ThemeInfo(
            name="professional",
            description="Corporate and professional appearance",
            preview_colors={"primary": "#1E40AF", "background": "#F8FAFC", "text": "#0F172A"}
        ),
        ThemeInfo(
            name="aesthetic",
            description="Modern aesthetic with soft gradients",
            preview_colors={"primary": "#8B5CF6", "background": "#FAFAF9", "text": "#292524"}
        ),
        ThemeInfo(
            name="playful",
            description="Colorful and fun design",
            preview_colors={"primary": "#F472B6", "background": "#FFFBEB", "text": "#7C2D12"}
        ),
        ThemeInfo(
            name="portfolio",
            description="Elegant portfolio style",
            preview_colors={"primary": "#0EA5E9", "background": "#F0F9FF", "text": "#0C4A6E"}
        ),
        ThemeInfo(
            name="tropical",
            description="Vibrant tropical colors",
            preview_colors={"primary": "#10B981", "background": "#ECFDF5", "text": "#064E3B"}
        ),
        ThemeInfo(
            name="gradient",
            description="Modern gradient-based design",
            preview_colors={"primary": "#A855F7", "background": "#FAF5FF", "text": "#581C87"}
        ),
        ThemeInfo(
            name="animated",
            description="Design optimized for animations",
            preview_colors={"primary": "#F97316", "background": "#FFF7ED", "text": "#7C2D12"}
        ),
    ]
    
    motion_presets = [
        "fade_in",
        "slide_up",
        "slide_down",
        "slide_left",
        "slide_right",
        "scale_in",
        "spring_pop",
        "spring_bounce",
        "viewport_fade",
        "stagger_children",
    ]
    
    return PresetsResponse(themes=themes, motion_presets=motion_presets)


@router.post(
    "/analyze/base64",
    response_model=AnalyzeResponse,
    responses={
        400: {"model": AnalyzeErrorResponse},
        500: {"model": AnalyzeErrorResponse},
    },
    summary="Analyze a base64-encoded image",
    description="Process a base64-encoded image without file upload."
)
async def analyze_base64(
    background_tasks: BackgroundTasks,
    image_data: str = Form(..., description="Base64-encoded image data"),
    theme: str = Form(default="minimal"),
    enable_motion: bool = Form(default=False),
    motion_preset: str = Form(default="fade_in"),
) -> JSONResponse:
    """
    Process a base64-encoded image.
    
    Useful for canvas-based drawing tools that capture images as base64.
    """
    import base64
    
    start_time = datetime.utcnow()
    job_id = str(uuid.uuid4())
    file_path: Optional[Path] = None
    
    try:
        # Remove data URL prefix if present
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        # Decode base64
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid base64 data",
                    "error_code": "INVALID_BASE64"
                }
            )
        
        # Check size
        if len(image_bytes) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": f"Image too large. Maximum: {settings.max_upload_size_mb}MB",
                    "error_code": "FILE_TOO_LARGE"
                }
            )
        
        # Save to temp file
        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "..",
            settings.temp_upload_dir
        )
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = Path(upload_dir) / f"{job_id}.png"
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        
        # Process
        orchestrator = DuiodleOrchestrator(
            theme=theme,
            enable_motion=enable_motion,
            motion_preset=motion_preset
        )
        
        result = orchestrator.process_image(str(file_path))
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        response = AnalyzeResponse(
            success=True,
            ui_tree=result.get("ui_tree", {}),
            react_code=result.get("react_code", ""),
            metadata=ProcessingMetadata(
                job_id=job_id,
                theme=theme,
                motion_enabled=enable_motion,
                motion_preset=motion_preset if enable_motion else None,
                processing_time_ms=processing_time,
                timestamp=datetime.utcnow().isoformat(),
                vision_provider=settings.vision_provider,
            ),
            errors=[]
        )
        
        background_tasks.add_task(cleanup_file, file_path)
        
        return JSONResponse(status_code=200, content=response.model_dump())
        
    except HTTPException:
        if file_path:
            background_tasks.add_task(cleanup_file, file_path)
        raise
        
    except Exception as e:
        logger.error(f"Base64 processing error: {e}", exc_info=True)
        
        if file_path:
            background_tasks.add_task(cleanup_file, file_path)
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "error_code": "PROCESSING_ERROR",
            }
        )
