"""
Duiodle Analyze API - Sketch Processing Endpoints

This module provides REST and WebSocket endpoints for processing
UI sketches through the Duiodle pipeline.

Endpoints:
- POST /analyze: Submit a sketch for processing
- WebSocket /ws/status/{job_id}: Real-time progress updates
- GET /themes: List available themes
- GET /presets: List motion presets
"""

import asyncio
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, Field

from app.services.orchestrator import DuiodleOrchestrator

logger = logging.getLogger("duiodle.analyze")

# Create router
router = APIRouter(tags=["Analyze"])

# Thread pool for CPU-bound operations
executor = ThreadPoolExecutor(max_workers=4)


# ============================================================
# Enums
# ============================================================

class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStage(str, Enum):
    """Pipeline processing stages."""
    UPLOAD = "upload"
    VISION = "vision"
    CLASSIFICATION = "classification"
    LAYOUT = "layout"
    THEME = "theme"
    MOTION = "motion"
    CODEGEN = "codegen"
    COMPLETE = "complete"


# ============================================================
# Request/Response Models
# ============================================================

class AnalyzeResponse(BaseModel):
    """Response for analyze endpoint."""
    success: bool = Field(..., description="Whether the request was accepted")
    job_id: str = Field(..., description="Unique job identifier for tracking")
    message: str = Field(..., description="Status message")
    websocket_url: str = Field(..., description="WebSocket URL for status updates")


class JobStatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str
    status: JobStatus
    stage: Optional[str] = None
    progress: int = Field(0, ge=0, le=100)
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class ThemeInfo(BaseModel):
    """Theme information."""
    name: str
    display_name: str
    description: str
    primary_color: str


class ThemeListResponse(BaseModel):
    """Response for themes list."""
    themes: List[ThemeInfo]
    default: str = "minimal"


class MotionPresetInfo(BaseModel):
    """Motion preset information."""
    name: str
    display_name: str
    description: str


class PresetsListResponse(BaseModel):
    """Response for motion presets list."""
    presets: List[MotionPresetInfo]
    default: str = "fade_in"


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    stage: str
    status: str
    progress: int = Field(0, ge=0, le=100)
    message: Optional[str] = None
    code: Optional[str] = None
    ui_tree: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================
# Job Storage (In-Memory for Demo)
# ============================================================

@dataclass
class Job:
    """Represents a processing job."""
    id: str
    status: JobStatus = JobStatus.PENDING
    stage: PipelineStage = PipelineStage.UPLOAD
    progress: int = 0
    theme: str = "minimal"
    enable_motion: bool = False
    motion_preset: str = "fade_in"
    image_path: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    websockets: Set[WebSocket] = field(default_factory=set)


# Job storage
jobs: Dict[str, Job] = {}


# ============================================================
# WebSocket Connection Manager
# ============================================================

class JobConnectionManager:
    """Manages WebSocket connections for job status updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        
        self.active_connections[job_id].add(websocket)
        logger.info(f"WebSocket connected for job {job_id}")
    
    def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        
        logger.info(f"WebSocket disconnected for job {job_id}")
    
    async def send_update(self, job_id: str, message: Dict[str, Any]) -> None:
        """Send an update to all connections for a job."""
        if job_id not in self.active_connections:
            return
        
        disconnected = set()
        
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            self.active_connections[job_id].discard(ws)


# Global connection manager
connection_manager = JobConnectionManager()


# ============================================================
# Progress Callback for Orchestrator
# ============================================================

STAGE_PROGRESS = {
    PipelineStage.UPLOAD: 5,
    PipelineStage.VISION: 20,
    PipelineStage.CLASSIFICATION: 35,
    PipelineStage.LAYOUT: 50,
    PipelineStage.THEME: 65,
    PipelineStage.MOTION: 80,
    PipelineStage.CODEGEN: 95,
    PipelineStage.COMPLETE: 100,
}


async def send_progress_update(
    job_id: str,
    stage: PipelineStage,
    status: str = "processing",
    message: Optional[str] = None,
    code: Optional[str] = None,
    ui_tree: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """Send a progress update through WebSocket."""
    progress = STAGE_PROGRESS.get(stage, 0)
    
    update = WebSocketMessage(
        stage=stage.value,
        status=status,
        progress=progress,
        message=message or f"Processing {stage.value}...",
        code=code,
        ui_tree=ui_tree,
        error=error,
    )
    
    await connection_manager.send_update(job_id, update.model_dump(exclude_none=True))
    
    # Update job record
    if job_id in jobs:
        jobs[job_id].stage = stage
        jobs[job_id].progress = progress


# ============================================================
# Background Processing Task
# ============================================================

async def process_sketch_task(job_id: str) -> None:
    """
    Background task to process a sketch through the pipeline.
    
    Sends real-time updates through WebSocket as each stage completes.
    """
    job = jobs.get(job_id)
    if not job:
        logger.error(f"Job {job_id} not found")
        return
    
    try:
        job.status = JobStatus.PROCESSING
        
        # Stage 1: Vision
        await send_progress_update(job_id, PipelineStage.VISION, message="Detecting shapes in sketch...")
        await asyncio.sleep(0.1)  # Allow WebSocket message to be sent
        
        # Initialize orchestrator
        orchestrator = DuiodleOrchestrator(
            theme=job.theme,
            enable_motion=job.enable_motion,
            motion_preset=job.motion_preset,
        )
        
        # Run vision processing in thread pool
        loop = asyncio.get_event_loop()
        
        try:
            detections = await loop.run_in_executor(
                executor,
                orchestrator.vision_processor.run,
                job.image_path
            )
        except Exception as e:
            raise Exception(f"Vision processing failed: {str(e)}")
        
        # Stage 2: Classification
        await send_progress_update(job_id, PipelineStage.CLASSIFICATION, message="Classifying UI components...")
        await asyncio.sleep(0.1)
        
        try:
            # Convert detections to format expected by classifier
            detection_dicts = []
            for d in detections:
                if hasattr(d, 'to_dict'):
                    detection_dicts.append(d.to_dict())
                elif isinstance(d, dict):
                    detection_dicts.append(d)
                else:
                    detection_dicts.append({
                        "id": getattr(d, 'id', str(uuid.uuid4())),
                        "type": getattr(d, 'shape_type', 'rectangle').value if hasattr(getattr(d, 'shape_type', None), 'value') else str(getattr(d, 'shape_type', 'rectangle')),
                        "bbox": {
                            "x": getattr(d.bbox, 'x', 0) if hasattr(d, 'bbox') else 0,
                            "y": getattr(d.bbox, 'y', 0) if hasattr(d, 'bbox') else 0,
                            "width": getattr(d.bbox, 'width', 0.1) if hasattr(d, 'bbox') else 0.1,
                            "height": getattr(d.bbox, 'height', 0.1) if hasattr(d, 'bbox') else 0.1,
                        },
                        "confidence": getattr(d, 'confidence', 0.9),
                    })
            
            classified = await loop.run_in_executor(
                executor,
                orchestrator.classifier.classify_batch,
                detection_dicts
            )
        except Exception as e:
            raise Exception(f"Classification failed: {str(e)}")
        
        # Stage 3: Layout
        await send_progress_update(job_id, PipelineStage.LAYOUT, message="Building component hierarchy...")
        await asyncio.sleep(0.1)
        
        try:
            # Convert classified to node format
            nodes = []
            for c in classified:
                if hasattr(c, 'to_dict'):
                    node = c.to_dict()
                elif isinstance(c, dict):
                    node = c.copy()
                else:
                    node = {
                        "id": getattr(c, 'id', str(uuid.uuid4())),
                        "type": getattr(c, 'ui_hint', 'container').value if hasattr(getattr(c, 'ui_hint', None), 'value') else str(getattr(c, 'ui_hint', 'container')),
                        "bbox": c.get('bbox', {"x": 0, "y": 0, "width": 0.1, "height": 0.1}) if isinstance(c, dict) else {"x": 0, "y": 0, "width": 0.1, "height": 0.1},
                        "confidence": getattr(c, 'confidence', 0.9) if hasattr(c, 'confidence') else c.get('confidence', 0.9) if isinstance(c, dict) else 0.9,
                    }
                nodes.append(node)
            
            layout_result = await loop.run_in_executor(
                executor,
                orchestrator.layout_resolver.resolve,
                nodes
            )
            
            # Extract tree from result
            if hasattr(layout_result, 'tree'):
                layout_tree = layout_result.tree
            elif isinstance(layout_result, dict):
                layout_tree = layout_result
            else:
                layout_tree = {"type": "container", "children": []}
                
        except Exception as e:
            raise Exception(f"Layout resolution failed: {str(e)}")
        
        # Stage 4: Theme
        await send_progress_update(job_id, PipelineStage.THEME, message=f"Applying {job.theme} theme...")
        await asyncio.sleep(0.1)
        
        try:
            themed_tree = await loop.run_in_executor(
                executor,
                orchestrator.theme_provider.apply_theme,
                layout_tree,
                job.theme
            )
        except Exception as e:
            raise Exception(f"Theme application failed: {str(e)}")
        
        # Stage 5: Motion (if enabled)
        if job.enable_motion:
            await send_progress_update(job_id, PipelineStage.MOTION, message="Adding motion effects...")
            await asyncio.sleep(0.1)
            
            try:
                motion_tree = await loop.run_in_executor(
                    executor,
                    orchestrator.motion_resolver.apply_motion,
                    themed_tree,
                    job.motion_preset
                )
            except Exception as e:
                raise Exception(f"Motion injection failed: {str(e)}")
        else:
            motion_tree = themed_tree
        
        # Stage 6: Code Generation
        await send_progress_update(job_id, PipelineStage.CODEGEN, message="Generating React code...")
        await asyncio.sleep(0.1)
        
        try:
            react_code = await loop.run_in_executor(
                executor,
                orchestrator.renderer.render,
                motion_tree
            )
        except Exception as e:
            raise Exception(f"Code generation failed: {str(e)}")
        
        # Complete
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.result = {
            "ui_tree": motion_tree,
            "react_code": react_code,
            "metadata": {
                "theme": job.theme,
                "motion_enabled": job.enable_motion,
                "motion_preset": job.motion_preset if job.enable_motion else None,
            }
        }
        
        await send_progress_update(
            job_id,
            PipelineStage.COMPLETE,
            status="completed",
            message="Processing complete!",
            code=react_code,
            ui_tree=motion_tree,
        )
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.completed_at = datetime.utcnow()
        
        await send_progress_update(
            job_id,
            job.stage,
            status="failed",
            message="Processing failed",
            error=str(e),
        )


# ============================================================
# REST Endpoints
# ============================================================

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit sketch for processing",
    description="Upload a UI sketch image to be processed through the Duiodle pipeline.",
)
async def analyze_sketch(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Sketch image file (PNG, JPG, WEBP)"),
    theme: str = Form("minimal", description="Design theme to apply"),
    enable_motion: bool = Form(False, description="Enable motion effects"),
    motion_preset: str = Form("fade_in", description="Motion preset to use"),
) -> AnalyzeResponse:
    """
    Submit a sketch for processing.
    
    Accepts an image file and processing parameters, starts background
    processing, and returns a job ID for tracking via WebSocket.
    """
    # Validate file type
    allowed_types = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Allowed: {allowed_types}"
        )
    
    # Validate theme
    valid_themes = ["minimal", "professional", "aesthetic", "playful", "portfolio", "tropical", "gradient", "animated"]
    if theme not in valid_themes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid theme: {theme}. Valid themes: {valid_themes}"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = file.filename.split(".")[-1] if file.filename else "png"
    file_path = os.path.join(upload_dir, f"{job_id}.{file_extension}")
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Saved uploaded file to {file_path}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )
    
    # Create job
    job = Job(
        id=job_id,
        theme=theme,
        enable_motion=enable_motion,
        motion_preset=motion_preset,
        image_path=file_path,
    )
    jobs[job_id] = job
    
    # Start background processing
    background_tasks.add_task(process_sketch_task, job_id)
    
    logger.info(f"Created job {job_id} with theme={theme}, motion={enable_motion}")
    
    return AnalyzeResponse(
        success=True,
        job_id=job_id,
        message="Processing started. Connect to WebSocket for real-time updates.",
        websocket_url=f"/api/v1/ws/status/{job_id}",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Check the current status of a processing job.",
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get the current status of a processing job."""
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = jobs[job_id]
    
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        stage=job.stage.value,
        progress=job.progress,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error=job.error,
    )


@router.get(
    "/jobs/{job_id}/result",
    summary="Get job result",
    description="Get the final result of a completed job.",
)
async def get_job_result(job_id: str) -> Dict[str, Any]:
    """Get the result of a completed job."""
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = jobs[job_id]
    
    if job.status == JobStatus.PENDING or job.status == JobStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail="Job is still processing"
        )
    
    if job.status == JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Job failed: {job.error}"
        )
    
    return {
        "success": True,
        "job_id": job_id,
        "result": job.result,
    }


@router.get(
    "/themes",
    response_model=ThemeListResponse,
    summary="List available themes",
    description="Get a list of all available design themes.",
)
async def list_themes() -> ThemeListResponse:
    """Get list of available themes."""
    themes = [
        ThemeInfo(
            name="minimal",
            display_name="Minimal",
            description="Clean and simple design with subtle colors",
            primary_color="#000000",
        ),
        ThemeInfo(
            name="professional",
            display_name="Professional",
            description="Corporate-friendly design with blue accents",
            primary_color="#2563eb",
        ),
        ThemeInfo(
            name="aesthetic",
            display_name="Aesthetic",
            description="Soft pastels and rounded corners",
            primary_color="#ec4899",
        ),
        ThemeInfo(
            name="playful",
            display_name="Playful",
            description="Vibrant colors and bold shapes",
            primary_color="#f59e0b",
        ),
        ThemeInfo(
            name="portfolio",
            display_name="Portfolio",
            description="Elegant dark theme for showcasing work",
            primary_color="#8b5cf6",
        ),
        ThemeInfo(
            name="tropical",
            display_name="Tropical",
            description="Warm, nature-inspired color palette",
            primary_color="#10b981",
        ),
        ThemeInfo(
            name="gradient",
            display_name="Gradient",
            description="Modern gradient backgrounds and effects",
            primary_color="#6366f1",
        ),
        ThemeInfo(
            name="animated",
            display_name="Animated",
            description="Theme optimized for motion effects",
            primary_color="#06b6d4",
        ),
    ]
    
    return ThemeListResponse(themes=themes, default="minimal")


@router.get(
    "/presets",
    response_model=PresetsListResponse,
    summary="List motion presets",
    description="Get a list of all available motion presets.",
)
async def list_motion_presets() -> PresetsListResponse:
    """Get list of available motion presets."""
    presets = [
        MotionPresetInfo(
            name="fade_in",
            display_name="Fade In",
            description="Simple fade-in effect",
        ),
        MotionPresetInfo(
            name="slide_up",
            display_name="Slide Up",
            description="Slide in from bottom",
        ),
        MotionPresetInfo(
            name="slide_left",
            display_name="Slide Left",
            description="Slide in from right",
        ),
        MotionPresetInfo(
            name="scale_in",
            display_name="Scale In",
            description="Scale up from center",
        ),
        MotionPresetInfo(
            name="spring_pop",
            display_name="Spring Pop",
            description="Bouncy spring animation",
        ),
        MotionPresetInfo(
            name="spring_bounce",
            display_name="Spring Bounce",
            description="Energetic bounce effect",
        ),
        MotionPresetInfo(
            name="stagger_children",
            display_name="Stagger Children",
            description="Cascade animation for child elements",
        ),
    ]
    
    return PresetsListResponse(presets=presets, default="fade_in")


# ============================================================
# WebSocket Endpoint
# ============================================================

@router.websocket("/ws/status/{job_id}")
async def websocket_job_status(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job status updates.
    
    Connect to receive progress updates as the pipeline processes
    your sketch. Messages include:
    
    - stage: Current processing stage
    - status: "processing", "completed", or "failed"
    - progress: Percentage complete (0-100)
    - message: Human-readable status message
    - code: Generated React code (when complete)
    - ui_tree: Component tree (when complete)
    - error: Error message (if failed)
    """
    await connection_manager.connect(job_id, websocket)
    
    try:
        # Check if job exists
        if job_id not in jobs:
            await websocket.send_json({
                "stage": "error",
                "status": "failed",
                "progress": 0,
                "error": f"Job {job_id} not found",
            })
            await websocket.close()
            return
        
        job = jobs[job_id]
        
        # Send current status immediately
        initial_message = {
            "stage": job.stage.value,
            "status": job.status.value,
            "progress": job.progress,
            "message": f"Connected to job {job_id}",
        }
        
        # Include result if already complete
        if job.status == JobStatus.COMPLETED and job.result:
            initial_message["code"] = job.result.get("react_code")
            initial_message["ui_tree"] = job.result.get("ui_tree")
        elif job.status == JobStatus.FAILED:
            initial_message["error"] = job.error
        
        await websocket.send_json(initial_message)
        
        # Keep connection alive and wait for updates
        while True:
            try:
                # Wait for client messages (ping/pong or close)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle ping
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_json({"type": "keepalive"})
                except:
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        connection_manager.disconnect(job_id, websocket)
