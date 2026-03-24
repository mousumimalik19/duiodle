"""
Duiodle API - Main Entry Point

Transform hand-drawn UI sketches into production-ready React code.

This module initializes FastAPI, configures middleware, and defines endpoints.

Author: Duiodle Team
Version: 1.0.0
"""

import logging
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


# =============================================================================
# LOGGING SETUP
# =============================================================================

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def setup_logging() -> logging.Logger:
    """Configure application logging."""
    logger = logging.getLogger("duiodle")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(ColoredFormatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


logger = setup_logging()


# =============================================================================
# PIPELINE LOGGER
# =============================================================================

class PipelineLogger:
    """Logger for tracking Vision → Layout → Code pipeline stages."""
    
    STAGES = ["VISION", "CLASSIFY", "LAYOUT", "THEME", "MOTION", "CODEGEN"]
    ICONS = {
        "VISION": "👁️ ",
        "CLASSIFY": "🏷️ ",
        "LAYOUT": "📐",
        "THEME": "🎨",
        "MOTION": "✨",
        "CODEGEN": "⚛️ ",
    }
    
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.start_time = time.time()
        self.stage_times: dict[str, float] = {}
    
    def start_pipeline(self, filename: str, theme: str):
        logger.info("=" * 50)
        logger.info(f"🚀 Pipeline started [{self.request_id[:8]}]")
        logger.info(f"   File: {filename} | Theme: {theme}")
        logger.info("-" * 50)
    
    def start_stage(self, stage: str):
        self.stage_times[stage] = time.time()
        icon = self.ICONS.get(stage, "▶️")
        num = self.STAGES.index(stage) + 1 if stage in self.STAGES else "?"
        logger.info(f"{icon} [{num}/6] {stage}")
    
    def end_stage(self, stage: str, details: str = ""):
        duration = (time.time() - self.stage_times.get(stage, time.time())) * 1000
        logger.info(f"   ✓ {duration:.1f}ms {details}")
    
    def error_stage(self, stage: str, error: str):
        logger.error(f"   ✗ {stage} failed: {error}")
    
    def end_pipeline(self, success: bool = True):
        total = (time.time() - self.start_time) * 1000
        logger.info("-" * 50)
        if success:
            logger.info(f"🏁 Complete in {total:.1f}ms")
        else:
            logger.error(f"❌ Failed after {total:.1f}ms")
        logger.info("=" * 50)


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class GenerationMetrics(BaseModel):
    total_duration_ms: float
    shapes_detected: int
    nodes_generated: int
    stage_durations: dict[str, float] = {}


class GenerationResponse(BaseModel):
    success: bool
    request_id: str
    ui_tree: dict
    react_code: str
    metadata: dict
    metrics: GenerationMetrics


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: str
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    vision_provider: str
    services: dict[str, str]


# =============================================================================
# LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 DUIODLE API - Starting...")
    logger.info("=" * 60)
    
    # Create upload directory
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    logger.info(f"📁 Uploads: {upload_dir.absolute()}")
    
    # Log configuration
    vision_provider = os.getenv("VISION_PROVIDER", "mock")
    logger.info(f"⚙️  Vision: {vision_provider}")
    logger.info(f"⚙️  Debug: {os.getenv('DEBUG_MODE', 'false')}")
    
    # Check API keys
    if vision_provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  OPENAI_API_KEY missing - using mock")
    elif vision_provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
        logger.warning("⚠️  GEMINI_API_KEY missing - using mock")
    
    logger.info("=" * 60)
    logger.info("✅ Ready to accept requests")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down...")


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Duiodle API",
    description="Transform sketches into React code",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# =============================================================================
# CORS MIDDLEWARE
# =============================================================================

CORS_ORIGINS = [
    "http://localhost:5173",      # Vite
    "http://localhost:3000",      # CRA
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# Add custom origins from env
custom = os.getenv("CORS_ORIGINS", "")
if custom:
    CORS_ORIGINS.extend([o.strip() for o in custom.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# =============================================================================
# REQUEST LOGGING MIDDLEWARE
# =============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    
    request.state.request_id = request_id
    logger.info(f"→ {request.method} {request.url.path} [{request_id}]")
    
    response = await call_next(request)
    
    duration = (time.time() - start) * 1000
    icon = "✓" if response.status_code < 400 else "✗"
    logger.info(f"← {icon} {response.status_code} ({duration:.0f}ms) [{request_id}]")
    
    response.headers["X-Request-ID"] = request_id
    return response


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            request_id=request_id,
        ).model_dump(),
    )


# =============================================================================
# HEALTH ENDPOINTS
# =============================================================================

@app.get("/", tags=["System"])
async def root():
    """API root."""
    return {
        "name": "Duiodle API",
        "tagline": "Where Doodles Become Interfaces",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Health check."""
    provider = os.getenv("VISION_PROVIDER", "mock")
    vision_status = "healthy"
    
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        vision_status = "degraded"
    elif provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
        vision_status = "degraded"
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        vision_provider=provider,
        services={
            "api": "healthy",
            "vision": vision_status,
            "layout": "healthy",
            "theme": "healthy",
            "codegen": "healthy",
        }
    )


# =============================================================================
# MAIN GENERATION ENDPOINT
# =============================================================================

@app.post(
    "/api/v1/generate",
    response_model=GenerationResponse,
    tags=["Generation"],
    summary="Generate React code from sketch",
)
async def generate_from_sketch(
    file: UploadFile = File(..., description="Sketch image (PNG, JPG, WEBP)"),
    theme: str = Form(default="minimal", description="Design theme"),
    enable_motion: bool = Form(default=False, description="Enable animations"),
    motion_preset: str = Form(default="fade_in", description="Motion preset"),
):
    """
    Process a sketch and generate React + Tailwind code.
    
    Pipeline: Vision → Classification → Layout → Theme → Motion → Codegen
    """
    request_id = str(uuid.uuid4())
    pipeline = PipelineLogger(request_id)
    stage_durations: dict[str, float] = {}
    
    # -------------------------------------------------------------------------
    # VALIDATION
    # -------------------------------------------------------------------------
    
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}",
        )
    
    max_size = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large (max {max_size // (1024*1024)}MB)",
        )
    
    valid_themes = ["minimal", "professional", "aesthetic", "playful",
                    "portfolio", "tropical", "gradient", "animated"]
    if theme not in valid_themes:
        theme = "minimal"
    
    # -------------------------------------------------------------------------
    # SAVE FILE
    # -------------------------------------------------------------------------
    
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    ext = Path(file.filename or "sketch.png").suffix or ".png"
    temp_path = upload_dir / f"{request_id}{ext}"
    
    with open(temp_path, "wb") as f:
        f.write(content)
    
    # -------------------------------------------------------------------------
    # RUN PIPELINE
    # -------------------------------------------------------------------------
    
    pipeline.start_pipeline(file.filename or "sketch", theme)
    
    try:
        from app.engine.vision.processor import VisionProcessorFactory
        from app.engine.vision.classifier import ShapeClassifier
        from app.engine.layout.resolver import LayoutResolver
        from app.engine.theme.provider import ThemeProvider
        from app.engine.theme.tailwind_mapper import TailwindMapper
        from app.engine.motion.resolver import MotionResolver
        from app.engine.codegen.react_renderer import ReactRenderer
        
        # STAGE 1: VISION
        pipeline.start_stage("VISION")
        t0 = time.time()
        
        processor = VisionProcessorFactory.create_from_settings()
        detections = processor.run(str(temp_path))
        
        stage_durations["vision"] = (time.time() - t0) * 1000
        pipeline.end_stage("VISION", f"({len(detections)} shapes)")
        
        # STAGE 2: CLASSIFY
        pipeline.start_stage("CLASSIFY")
        t0 = time.time()
        
        classifier = ShapeClassifier()
        classified = classifier.classify_batch(detections)
        
        stage_durations["classify"] = (time.time() - t0) * 1000
        pipeline.end_stage("CLASSIFY", f"({len(classified)} elements)")
        
        # Convert to nodes
        nodes = []
        for shape in classified:
            nodes.append({
                "id": shape.id if hasattr(shape, 'id') else str(uuid.uuid4())[:8],
                "type": shape.ui_hint.value if hasattr(shape.ui_hint, 'value') else str(shape.ui_hint),
                "bbox": shape.bbox.to_dict() if hasattr(shape.bbox, 'to_dict') else shape.bbox,
                "confidence": getattr(shape, 'confidence', 0.9),
            })
        
        # STAGE 3: LAYOUT
        pipeline.start_stage("LAYOUT")
        t0 = time.time()
        
        layout_resolver = LayoutResolver()
        layout_result = layout_resolver.resolve(nodes)
        
        if hasattr(layout_result, 'tree'):
            layout_tree = layout_result.tree
        elif isinstance(layout_result, dict):
            layout_tree = layout_result
        else:
            layout_tree = {"type": "container", "layout": "column", "children": nodes}
        
        stage_durations["layout"] = (time.time() - t0) * 1000
        pipeline.end_stage("LAYOUT", f"({_count_nodes(layout_tree)} nodes)")
        
        # STAGE 4: THEME
        pipeline.start_stage("THEME")
        t0 = time.time()
        
        theme_provider = ThemeProvider()
        themed_tree = theme_provider.apply_theme(layout_tree, theme)
        
        stage_durations["theme"] = (time.time() - t0) * 1000
        pipeline.end_stage("THEME", f"({theme})")
        
        # STAGE 5: MOTION
        pipeline.start_stage("MOTION")
        t0 = time.time()
        
        motion_resolver = MotionResolver(enable_motion=enable_motion)
        motion_tree = motion_resolver.apply_motion(themed_tree, motion_preset)
        
        stage_durations["motion"] = (time.time() - t0) * 1000
        pipeline.end_stage("MOTION", f"({'enabled' if enable_motion else 'disabled'})")
        
        # STAGE 6: CODEGEN
        pipeline.start_stage("CODEGEN")
        t0 = time.time()
        
        mapper = TailwindMapper()
        renderer = ReactRenderer(tailwind_mapper=mapper)
        react_code = renderer.render(motion_tree)
        
        stage_durations["codegen"] = (time.time() - t0) * 1000
        pipeline.end_stage("CODEGEN", f"({len(react_code)} chars)")
        
        # SUCCESS
        pipeline.end_pipeline(success=True)
        
        return GenerationResponse(
            success=True,
            request_id=request_id,
            ui_tree=motion_tree,
            react_code=react_code,
            metadata={
                "theme": theme,
                "motion_enabled": enable_motion,
                "motion_preset": motion_preset if enable_motion else None,
                "filename": file.filename,
            },
            metrics=GenerationMetrics(
                total_duration_ms=sum(stage_durations.values()),
                shapes_detected=len(detections),
                nodes_generated=_count_nodes(motion_tree),
                stage_durations=stage_durations,
            ),
        )
        
    except ImportError as e:
        pipeline.error_stage("IMPORT", str(e))
        pipeline.end_pipeline(success=False)
        raise HTTPException(status_code=500, detail=f"Module error: {e}")
        
    except Exception as e:
        pipeline.error_stage("PIPELINE", str(e))
        pipeline.end_pipeline(success=False)
        logger.exception("Pipeline error")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")
        
    finally:
        # Cleanup
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


def _count_nodes(tree: dict) -> int:
    """Count nodes in tree recursively."""
    if not isinstance(tree, dict):
        return 0
    count = 1
    for child in tree.get("children", []):
        count += _count_nodes(child)
    return count


# =============================================================================
# CONFIGURATION ENDPOINTS
# =============================================================================

@app.get("/api/v1/themes", tags=["Config"])
async def list_themes():
    """List available themes."""
    return {
        "themes": [
            {"id": "minimal", "name": "Minimal"},
            {"id": "professional", "name": "Professional"},
            {"id": "aesthetic", "name": "Aesthetic"},
            {"id": "playful", "name": "Playful"},
            {"id": "portfolio", "name": "Portfolio"},
            {"id": "tropical", "name": "Tropical"},
            {"id": "gradient", "name": "Gradient"},
            {"id": "animated", "name": "Animated"},
        ]
    }


@app.get("/api/v1/presets", tags=["Config"])
async def list_presets():
    """List motion presets."""
    return {
        "presets": [
            {"id": "fade_in", "name": "Fade In"},
            {"id": "slide_up", "name": "Slide Up"},
            {"id": "slide_left", "name": "Slide Left"},
            {"id": "scale_in", "name": "Scale In"},
            {"id": "spring_pop", "name": "Spring Pop"},
            {"id": "spring_bounce", "name": "Spring Bounce"},
        ]
    }


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
