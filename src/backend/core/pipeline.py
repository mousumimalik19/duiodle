"""
Duiodle Pipeline - Core AI Orchestration Module.

This module implements the DuiodlePipeline class, which orchestrates the complete
transformation pipeline from hand-drawn UI sketches to production-ready React code.

Pipeline Stages:
    1. Vision Processing - Extract shapes and raw elements from sketch
    2. Classification - Identify UI component types
    3. Layout Resolution - Build hierarchical structure with flex inference
    4. Validation - Ensure UI structure integrity
    5. Theme Application - Apply design tokens and styling
    6. Motion Injection - Add animation metadata (optional)
    7. Code Generation - Produce React + Tailwind code files

Example:
    >>> from backend.core.pipeline import DuiodlePipeline
    >>> 
    >>> pipeline = DuiodlePipeline()
    >>> result = pipeline.run("sketch.png", theme="professional", motion=True)
    >>> 
    >>> print(result.files["page.tsx"])
    >>> print(result.layout)

Author: Duiodle Engineering Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TypeVar, Callable
from abc import ABC, abstractmethod
import traceback
import json

# Configure module logger
logger = logging.getLogger("duiodle.pipeline")


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class PipelineStage(str, Enum):
    """Enumeration of all pipeline processing stages."""
    
    VISION = "vision"
    CLASSIFICATION = "classification"
    LAYOUT = "layout"
    VALIDATION = "validation"
    THEME = "theme"
    MOTION = "motion"
    CODEGEN = "codegen"
    
    @property
    def display_name(self) -> str:
        """Human-readable stage name."""
        return self.value.replace("_", " ").title()
    
    @property
    def icon(self) -> str:
        """Emoji icon for logging."""
        icons = {
            "vision": "👁️",
            "classification": "🏷️",
            "layout": "📐",
            "validation": "✅",
            "theme": "🎨",
            "motion": "✨",
            "codegen": "⚛️",
        }
        return icons.get(self.value, "•")


class ThemePreset(str, Enum):
    """Available theme presets for UI styling."""
    
    MINIMAL = "minimal"
    PROFESSIONAL = "professional"
    AESTHETIC = "aesthetic"
    PLAYFUL = "playful"
    PORTFOLIO = "portfolio"
    TROPICAL = "tropical"
    GRADIENT = "gradient"
    ANIMATED = "animated"
    DARK = "dark"
    LIGHT = "light"


class ComponentType(str, Enum):
    """Types of UI components detected by the vision system."""
    
    BUTTON = "button"
    NAVBAR = "navbar"
    TEXT_FIELD = "text_field"
    INPUT = "input"
    CARD = "card"
    IMAGE = "image"
    CONTAINER = "container"
    HEADER = "header"
    FOOTER = "footer"
    SIDEBAR = "sidebar"
    ICON = "icon"
    DIVIDER = "divider"
    LIST = "list"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    MODAL = "modal"
    AVATAR = "avatar"
    BADGE = "badge"
    LINK = "link"
    SPACER = "spacer"
    UNKNOWN = "unknown"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class BoundingBox:
    """
    Normalized bounding box coordinates (0-1 scale).
    
    Attributes:
        x: Left position (0-1)
        y: Top position (0-1)
        width: Width (0-1)
        height: Height (0-1)
        confidence: Detection confidence score
    """
    x: float
    y: float
    width: float
    height: float
    confidence: float = 1.0
    
    @property
    def center(self) -> tuple[float, float]:
        """Calculate center point."""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def area(self) -> float:
        """Calculate bounding box area."""
        return self.width * self.height
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
        }


@dataclass
class DetectedComponent:
    """
    A UI component detected by the vision system.
    
    Attributes:
        id: Unique component identifier
        type: Component type (button, card, etc.)
        bbox: Bounding box coordinates
        confidence: Detection confidence (0-1)
        ui_hint: Layout hint from classifier
        properties: Additional detected properties
    """
    id: str
    type: ComponentType
    bbox: BoundingBox
    confidence: float = 1.0
    ui_hint: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "bbox": self.bbox.to_dict(),
            "confidence": self.confidence,
            "ui_hint": self.ui_hint,
            "properties": self.properties,
        }


@dataclass
class LayoutNode:
    """
    A node in the resolved layout tree.
    
    Attributes:
        id: Unique node identifier
        type: Component type
        layout: Flex direction (row/column)
        bbox: Bounding box
        children: Child nodes
        style: Applied theme styles
        motion: Animation metadata
        properties: Additional properties
    """
    id: str
    type: str
    layout: str = "column"
    bbox: Optional[BoundingBox] = None
    children: List["LayoutNode"] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=dict)
    motion: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation (recursive)."""
        result = {
            "id": self.id,
            "type": self.type,
            "layout": self.layout,
            "properties": self.properties,
        }
        
        if self.bbox:
            result["bbox"] = self.bbox.to_dict()
        
        if self.style:
            result["style"] = self.style
        
        if self.motion:
            result["motion"] = self.motion
        
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        
        return result


@dataclass
class ComponentMetadata:
    """
    Metadata about detected components.
    
    Attributes:
        total_count: Total number of components
        by_type: Count by component type
        detection_confidence: Average detection confidence
        layout_depth: Maximum nesting depth
        has_navigation: Whether navigation was detected
        has_forms: Whether form elements were detected
    """
    total_count: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    detection_confidence: float = 0.0
    layout_depth: int = 0
    has_navigation: bool = False
    has_forms: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_count": self.total_count,
            "by_type": self.by_type,
            "detection_confidence": round(self.detection_confidence, 3),
            "layout_depth": self.layout_depth,
            "has_navigation": self.has_navigation,
            "has_forms": self.has_forms,
        }


@dataclass
class GeneratedFiles:
    """
    Collection of generated code files.
    
    Attributes:
        page: Main page component code
        layout: Layout wrapper code
        components: Individual component files
        styles: CSS/Tailwind styles (if any)
        types: TypeScript type definitions (if any)
    """
    page: str = ""
    layout: str = ""
    components: Dict[str, str] = field(default_factory=dict)
    styles: Optional[str] = None
    types: Optional[str] = None
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert to flat dictionary of filename -> code.
        
        Returns:
            Dictionary mapping file paths to code content.
        """
        files = {}
        
        if self.page:
            files["page.tsx"] = self.page
        
        if self.layout:
            files["layout.tsx"] = self.layout
        
        for name, code in self.components.items():
            # Ensure proper path formatting
            if not name.startswith("components/"):
                name = f"components/{name}"
            if not name.endswith(".tsx"):
                name = f"{name}.tsx"
            files[name] = code
        
        if self.styles:
            files["styles.css"] = self.styles
        
        if self.types:
            files["types.ts"] = self.types
        
        return files


@dataclass
class StageResult:
    """
    Result from a single pipeline stage.
    
    Attributes:
        stage: Stage that produced this result
        success: Whether the stage succeeded
        duration_ms: Execution time in milliseconds
        data: Output data from the stage
        error: Error message if failed
        warnings: Non-fatal warnings
    """
    stage: PipelineStage
    success: bool
    duration_ms: float
    data: Any = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """
    Complete result from the Duiodle pipeline.
    
    This is the main output structure returned by DuiodlePipeline.run().
    
    Attributes:
        success: Whether the pipeline completed successfully
        request_id: Unique request identifier
        components: List of detected UI components
        layout: Resolved layout tree
        theme: Applied theme name
        motion: Whether motion was enabled
        files: Generated code files
        metadata: Component detection metadata
        stage_results: Results from each pipeline stage
        total_duration_ms: Total processing time
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool
    request_id: str
    components: List[Dict[str, Any]]
    layout: Dict[str, Any]
    theme: str
    motion: bool
    files: Dict[str, str]
    metadata: ComponentMetadata
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    total_duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        
        Returns:
            Complete result as a dictionary.
        """
        return {
            "success": self.success,
            "request_id": self.request_id,
            "components": self.components,
            "layout": self.layout,
            "theme": self.theme,
            "motion": self.motion,
            "files": self.files,
            "metadata": self.metadata.to_dict(),
            "total_duration_ms": round(self.total_duration_ms, 2),
            "errors": self.errors,
            "warnings": self.warnings,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert to JSON string.
        
        Args:
            indent: JSON indentation level.
            
        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class PipelineConfig:
    """
    Configuration for the Duiodle pipeline.
    
    Attributes:
        default_theme: Default theme if not specified
        enable_motion_default: Default motion setting
        motion_preset: Default animation preset
        vision_provider: Vision AI provider (mock, openai, gemini)
        validation_strict: Fail on validation errors
        generate_layout_file: Generate layout.tsx
        generate_component_files: Generate individual component files
        max_nesting_depth: Maximum layout nesting depth
        enable_spacers: Inject spacer nodes
        log_level: Logging level
    """
    default_theme: str = "minimal"
    enable_motion_default: bool = False
    motion_preset: str = "fade_in"
    vision_provider: str = "mock"
    validation_strict: bool = False
    generate_layout_file: bool = True
    generate_component_files: bool = True
    max_nesting_depth: int = 10
    enable_spacers: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate theme
        valid_themes = [t.value for t in ThemePreset]
        if self.default_theme not in valid_themes:
            logger.warning(
                f"Unknown theme '{self.default_theme}', using 'minimal'"
            )
            self.default_theme = "minimal"


# =============================================================================
# EXCEPTIONS
# =============================================================================

class PipelineError(Exception):
    """
    Exception raised when a pipeline stage fails.
    
    Attributes:
        stage: The pipeline stage that failed
        message: Error description
        original_error: The underlying exception (if any)
    """
    
    def __init__(
        self,
        stage: PipelineStage,
        message: str,
        original_error: Optional[Exception] = None
    ):
        self.stage = stage
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{stage.value.upper()}] {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "stage": self.stage.value,
            "message": self.message,
            "original_error": str(self.original_error) if self.original_error else None,
        }


class ValidationError(PipelineError):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str, violations: List[str] = None):
        super().__init__(PipelineStage.VALIDATION, message)
        self.violations = violations or []


# =============================================================================
# PIPELINE LOGGER
# =============================================================================

class PipelineLogger:
    """
    Specialized logger for pipeline execution tracking.
    
    Provides structured logging with stage icons, timing,
    and progress tracking.
    """
    
    def __init__(self, request_id: str, log_level: str = "INFO"):
        """
        Initialize pipeline logger.
        
        Args:
            request_id: Unique request identifier.
            log_level: Logging level.
        """
        self.request_id = request_id
        self.logger = logging.getLogger(f"duiodle.pipeline.{request_id[:8]}")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.stage_times: Dict[str, float] = {}
        self.start_time: Optional[float] = None
    
    def start_pipeline(self, image_path: str, theme: str, motion: bool) -> None:
        """Log pipeline start."""
        self.start_time = time.perf_counter()
        self.logger.info("=" * 60)
        self.logger.info(f"🚀 DUIODLE PIPELINE - Starting")
        self.logger.info(f"   ├── Request ID: {self.request_id}")
        self.logger.info(f"   ├── Image: {image_path}")
        self.logger.info(f"   ├── Theme: {theme}")
        self.logger.info(f"   └── Motion: {'enabled' if motion else 'disabled'}")
        self.logger.info("-" * 60)
    
    def start_stage(self, stage: PipelineStage, step: int, total: int) -> float:
        """
        Log stage start and return start time.
        
        Args:
            stage: Pipeline stage starting.
            step: Current step number.
            total: Total number of steps.
            
        Returns:
            Start timestamp.
        """
        start = time.perf_counter()
        self.logger.info(
            f"{stage.icon}  [{step}/{total}] {stage.display_name.upper()} - Starting..."
        )
        return start
    
    def end_stage(
        self,
        stage: PipelineStage,
        start_time: float,
        result_info: str = ""
    ) -> float:
        """
        Log stage completion and return duration.
        
        Args:
            stage: Pipeline stage completed.
            start_time: Stage start timestamp.
            result_info: Additional result information.
            
        Returns:
            Duration in milliseconds.
        """
        duration_ms = (time.perf_counter() - start_time) * 1000
        self.stage_times[stage.value] = duration_ms
        
        info = f" → {result_info}" if result_info else ""
        self.logger.info(
            f"   └── ✓ {stage.display_name} completed in {duration_ms:.1f}ms{info}"
        )
        return duration_ms
    
    def stage_warning(self, stage: PipelineStage, message: str) -> None:
        """Log stage warning."""
        self.logger.warning(f"   ⚠️  [{stage.value}] {message}")
    
    def stage_error(self, stage: PipelineStage, error: str) -> None:
        """Log stage error."""
        self.logger.error(f"   ❌ [{stage.value}] {error}")
    
    def end_pipeline(self, success: bool) -> float:
        """
        Log pipeline completion.
        
        Args:
            success: Whether pipeline succeeded.
            
        Returns:
            Total duration in milliseconds.
        """
        if self.start_time is None:
            return 0.0
        
        total_ms = (time.perf_counter() - self.start_time) * 1000
        
        self.logger.info("-" * 60)
        if success:
            self.logger.info(f"🏁 PIPELINE COMPLETED SUCCESSFULLY")
        else:
            self.logger.info(f"❌ PIPELINE FAILED")
        self.logger.info(f"   └── Total time: {total_ms:.1f}ms")
        self.logger.info("=" * 60)
        
        return total_ms


# =============================================================================
# MAIN PIPELINE CLASS
# =============================================================================

class DuiodlePipeline:
    """
    Duiodle AI Pipeline - Transforms sketches into React code.
    
    This class orchestrates the complete transformation pipeline from
    hand-drawn UI sketches to production-ready React + Tailwind code.
    
    Pipeline Stages:
        1. Vision - Extract shapes and raw elements from sketch
        2. Classification - Identify UI component types
        3. Layout - Build hierarchical structure with flex inference
        4. Validation - Ensure UI structure integrity
        5. Theme - Apply design tokens and styling
        6. Motion - Add animation metadata (optional)
        7. Codegen - Produce React component code
    
    Example:
        >>> pipeline = DuiodlePipeline()
        >>> result = pipeline.run("sketch.png", theme="professional", motion=True)
        >>> 
        >>> # Access generated code
        >>> print(result.files["page.tsx"])
        >>> 
        >>> # Access layout structure
        >>> print(result.layout)
        >>> 
        >>> # Check metadata
        >>> print(result.metadata.total_count, "components detected")
    
    Attributes:
        config: Pipeline configuration.
        vision_processor: Vision processing engine.
        classifier: Shape to component classifier.
        layout_resolver: Layout tree builder.
        theme_provider: Theme application engine.
        motion_resolver: Animation metadata injector.
        code_renderer: React code generator.
        validator: Structure validator.
    """
    
    # Number of pipeline stages
    TOTAL_STAGES = 7
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the Duiodle pipeline.
        
        Args:
            config: Pipeline configuration. Uses defaults if not provided.
        """
        self.config = config or PipelineConfig()
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper(), logging.INFO),
            format="%(message)s"
        )
        
        # Initialize engines (lazy loading)
        self._vision_processor = None
        self._classifier = None
        self._layout_resolver = None
        self._theme_provider = None
        self._motion_resolver = None
        self._code_renderer = None
        self._validator = None
        
        logger.info(f"DuiodlePipeline initialized with config: {self.config}")
    
    # =========================================================================
    # LAZY LOADING PROPERTIES
    # =========================================================================
    
    @property
    def vision_processor(self):
        """Lazy-load vision processor."""
        if self._vision_processor is None:
            try:
                from backend.app.engine.vision.processor import VisionProcessorFactory
                self._vision_processor = VisionProcessorFactory.create(
                    self.config.vision_provider
                )
            except ImportError:
                logger.warning("Vision processor not available, using mock")
                self._vision_processor = MockVisionProcessor()
        return self._vision_processor
    
    @property
    def classifier(self):
        """Lazy-load shape classifier."""
        if self._classifier is None:
            try:
                from backend.app.engine.vision.classifier import ShapeClassifier
                self._classifier = ShapeClassifier()
            except ImportError:
                logger.warning("Classifier not available, using mock")
                self._classifier = MockClassifier()
        return self._classifier
    
    @property
    def layout_resolver(self):
        """Lazy-load layout resolver."""
        if self._layout_resolver is None:
            try:
                from backend.app.engine.layout.resolver import LayoutResolver
                self._layout_resolver = LayoutResolver()
            except ImportError:
                logger.warning("Layout resolver not available, using mock")
                self._layout_resolver = MockLayoutResolver()
        return self._layout_resolver
    
    @property
    def theme_provider(self):
        """Lazy-load theme provider."""
        if self._theme_provider is None:
            try:
                from backend.app.engine.theme.provider import ThemeProvider
                self._theme_provider = ThemeProvider()
            except ImportError:
                logger.warning("Theme provider not available, using mock")
                self._theme_provider = MockThemeProvider()
        return self._theme_provider
    
    @property
    def motion_resolver(self):
        """Lazy-load motion resolver."""
        if self._motion_resolver is None:
            try:
                from backend.app.engine.motion.resolver import MotionResolver
                self._motion_resolver = MotionResolver(enable_motion=True)
            except ImportError:
                logger.warning("Motion resolver not available, using mock")
                self._motion_resolver = MockMotionResolver()
        return self._motion_resolver
    
    @property
    def code_renderer(self):
        """Lazy-load code renderer."""
        if self._code_renderer is None:
            try:
                from backend.app.engine.codegen.react_renderer import ReactRenderer
                self._code_renderer = ReactRenderer()
            except ImportError:
                logger.warning("Code renderer not available, using mock")
                self._code_renderer = MockCodeRenderer()
        return self._code_renderer
    
    @property
    def validator(self):
        """Lazy-load validator."""
        if self._validator is None:
            try:
                from backend.app.services.validator import StructureValidator
                self._validator = StructureValidator()
            except ImportError:
                logger.warning("Validator not available, using mock")
                self._validator = MockValidator()
        return self._validator
    
    # =========================================================================
    # MAIN RUN METHOD
    # =========================================================================
    
    def run(
        self,
        image: Union[str, Path, bytes],
        theme: str = "minimal",
        motion: bool = True,
        motion_preset: str = "fade_in"
    ) -> PipelineResult:
        """
        Run the complete Duiodle transformation pipeline.
        
        This method orchestrates all pipeline stages from image input
        to React code output.
        
        Args:
            image: Input image path, Path object, or raw bytes.
            theme: Theme preset name (minimal, professional, etc.).
            motion: Whether to enable motion/animation metadata.
            motion_preset: Animation preset name.
            
        Returns:
            PipelineResult containing:
                - components: Detected UI components
                - layout: Resolved layout tree
                - files: Generated React code files
                - metadata: Detection statistics
                
        Raises:
            PipelineError: If a critical stage fails.
            
        Example:
            >>> result = pipeline.run("sketch.png", theme="professional")
            >>> print(result.files["page.tsx"])
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Initialize logger
        pipeline_logger = PipelineLogger(request_id, self.config.log_level)
        
        # Normalize image path
        image_path = str(image) if isinstance(image, (str, Path)) else "<bytes>"
        
        # Log pipeline start
        pipeline_logger.start_pipeline(image_path, theme, motion)
        
        # Initialize result containers
        stage_results: Dict[str, StageResult] = {}
        errors: List[str] = []
        warnings: List[str] = []
        
        # Default values
        components: List[Dict[str, Any]] = []
        layout: Dict[str, Any] = {}
        files: Dict[str, str] = {}
        metadata = ComponentMetadata()
        
        try:
            # ─────────────────────────────────────────────────────────────────
            # STAGE 1: VISION PROCESSING
            # ─────────────────────────────────────────────────────────────────
            start = pipeline_logger.start_stage(PipelineStage.VISION, 1, self.TOTAL_STAGES)
            
            try:
                raw_detections = self._run_vision(image)
                duration = pipeline_logger.end_stage(
                    PipelineStage.VISION, start,
                    f"Detected {len(raw_detections)} shapes"
                )
                stage_results["vision"] = StageResult(
                    stage=PipelineStage.VISION,
                    success=True,
                    duration_ms=duration,
                    data={"shape_count": len(raw_detections)}
                )
            except Exception as e:
                pipeline_logger.stage_error(PipelineStage.VISION, str(e))
                raise PipelineError(PipelineStage.VISION, str(e), e)
            
            # ─────────────────────────────────────────────────────────────────
            # STAGE 2: CLASSIFICATION
            # ─────────────────────────────────────────────────────────────────
            start = pipeline_logger.start_stage(
                PipelineStage.CLASSIFICATION, 2, self.TOTAL_STAGES
            )
            
            try:
                classified_components = self._run_classification(raw_detections)
                components = [c.to_dict() if hasattr(c, 'to_dict') else c 
                             for c in classified_components]
                duration = pipeline_logger.end_stage(
                    PipelineStage.CLASSIFICATION, start,
                    f"Classified {len(components)} components"
                )
                stage_results["classification"] = StageResult(
                    stage=PipelineStage.CLASSIFICATION,
                    success=True,
                    duration_ms=duration,
                    data={"component_count": len(components)}
                )
            except Exception as e:
                pipeline_logger.stage_error(PipelineStage.CLASSIFICATION, str(e))
                raise PipelineError(PipelineStage.CLASSIFICATION, str(e), e)
            
            # ─────────────────────────────────────────────────────────────────
            # STAGE 3: LAYOUT RESOLUTION
            # ─────────────────────────────────────────────────────────────────
            start = pipeline_logger.start_stage(PipelineStage.LAYOUT, 3, self.TOTAL_STAGES)
            
            try:
                layout_tree = self._run_layout(classified_components)
                layout = layout_tree if isinstance(layout_tree, dict) else layout_tree.to_dict()
                
                # Calculate layout metadata
                node_count = self._count_nodes(layout)
                depth = self._calculate_depth(layout)
                
                duration = pipeline_logger.end_stage(
                    PipelineStage.LAYOUT, start,
                    f"Built tree with {node_count} nodes, depth {depth}"
                )
                stage_results["layout"] = StageResult(
                    stage=PipelineStage.LAYOUT,
                    success=True,
                    duration_ms=duration,
                    data={"node_count": node_count, "depth": depth}
                )
            except Exception as e:
                pipeline_logger.stage_error(PipelineStage.LAYOUT, str(e))
                raise PipelineError(PipelineStage.LAYOUT, str(e), e)
            
            # ─────────────────────────────────────────────────────────────────
            # STAGE 4: VALIDATION
            # ─────────────────────────────────────────────────────────────────
            start = pipeline_logger.start_stage(
                PipelineStage.VALIDATION, 4, self.TOTAL_STAGES
            )
            
            try:
                validation_result = self._run_validation(layout)
                
                if validation_result.get("warnings"):
                    for warning in validation_result["warnings"]:
                        warnings.append(warning)
                        pipeline_logger.stage_warning(PipelineStage.VALIDATION, warning)
                
                duration = pipeline_logger.end_stage(
                    PipelineStage.VALIDATION, start,
                    "Structure valid" if validation_result.get("valid", True) else "Issues found"
                )
                stage_results["validation"] = StageResult(
                    stage=PipelineStage.VALIDATION,
                    success=True,
                    duration_ms=duration,
                    data=validation_result,
                    warnings=validation_result.get("warnings", [])
                )
            except ValidationError as e:
                if self.config.validation_strict:
                    pipeline_logger.stage_error(PipelineStage.VALIDATION, str(e))
                    raise
                else:
                    warnings.append(str(e))
                    pipeline_logger.stage_warning(PipelineStage.VALIDATION, str(e))
            except Exception as e:
                pipeline_logger.stage_warning(PipelineStage.VALIDATION, str(e))
                warnings.append(f"Validation warning: {e}")
            
            # ─────────────────────────────────────────────────────────────────
            # STAGE 5: THEME APPLICATION
            # ─────────────────────────────────────────────────────────────────
            start = pipeline_logger.start_stage(PipelineStage.THEME, 5, self.TOTAL_STAGES)
            
            try:
                themed_layout = self._apply_theme(layout, theme)
                layout = themed_layout
                
                duration = pipeline_logger.end_stage(
                    PipelineStage.THEME, start,
                    f"Applied '{theme}' theme"
                )
                stage_results["theme"] = StageResult(
                    stage=PipelineStage.THEME,
                    success=True,
                    duration_ms=duration,
                    data={"theme": theme}
                )
            except Exception as e:
                pipeline_logger.stage_warning(PipelineStage.THEME, str(e))
                warnings.append(f"Theme application warning: {e}")
            
            # ─────────────────────────────────────────────────────────────────
            # STAGE 6: MOTION INJECTION
            # ─────────────────────────────────────────────────────────────────
            start = pipeline_logger.start_stage(PipelineStage.MOTION, 6, self.TOTAL_STAGES)
            
            try:
                if motion:
                    motion_layout = self._inject_motion(layout, motion_preset)
                    layout = motion_layout
                    pipeline_logger.end_stage(
                        PipelineStage.MOTION, start,
                        f"Injected '{motion_preset}' animations"
                    )
                else:
                    pipeline_logger.end_stage(
                        PipelineStage.MOTION, start,
                        "Skipped (motion disabled)"
                    )
                
                stage_results["motion"] = StageResult(
                    stage=PipelineStage.MOTION,
                    success=True,
                    duration_ms=(time.perf_counter() - start) * 1000,
                    data={"enabled": motion, "preset": motion_preset if motion else None}
                )
            except Exception as e:
                pipeline_logger.stage_warning(PipelineStage.MOTION, str(e))
                warnings.append(f"Motion injection warning: {e}")
            
            # ─────────────────────────────────────────────────────────────────
            # STAGE 7: CODE GENERATION
            # ─────────────────────────────────────────────────────────────────
            start = pipeline_logger.start_stage(PipelineStage.CODEGEN, 7, self.TOTAL_STAGES)
            
            try:
                generated_files = self._generate_code(layout)
                files = generated_files.to_dict() if isinstance(generated_files, GeneratedFiles) else generated_files
                
                total_lines = sum(code.count('\n') + 1 for code in files.values())
                
                duration = pipeline_logger.end_stage(
                    PipelineStage.CODEGEN, start,
                    f"Generated {len(files)} files, {total_lines} lines"
                )
                stage_results["codegen"] = StageResult(
                    stage=PipelineStage.CODEGEN,
                    success=True,
                    duration_ms=duration,
                    data={"file_count": len(files), "total_lines": total_lines}
                )
            except Exception as e:
                pipeline_logger.stage_error(PipelineStage.CODEGEN, str(e))
                raise PipelineError(PipelineStage.CODEGEN, str(e), e)
            
            # ─────────────────────────────────────────────────────────────────
            # BUILD METADATA
            # ─────────────────────────────────────────────────────────────────
            metadata = self._build_metadata(components, layout)
            
            # Log success
            total_duration = pipeline_logger.end_pipeline(success=True)
            
            return PipelineResult(
                success=True,
                request_id=request_id,
                components=components,
                layout=layout,
                theme=theme,
                motion=motion,
                files=files,
                metadata=metadata,
                stage_results=stage_results,
                total_duration_ms=total_duration,
                errors=[],
                warnings=warnings,
            )
            
        except PipelineError as e:
            # Log failure
            total_duration = pipeline_logger.end_pipeline(success=False)
            
            errors.append(str(e))
            
            return PipelineResult(
                success=False,
                request_id=request_id,
                components=components,
                layout=layout,
                theme=theme,
                motion=motion,
                files=files,
                metadata=metadata,
                stage_results=stage_results,
                total_duration_ms=total_duration,
                errors=errors,
                warnings=warnings,
            )
        
        except Exception as e:
            # Unexpected error
            total_duration = pipeline_logger.end_pipeline(success=False)
            
            error_msg = f"Unexpected error: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            errors.append(str(e))
            
            return PipelineResult(
                success=False,
                request_id=request_id,
                components=components,
                layout=layout,
                theme=theme,
                motion=motion,
                files=files,
                metadata=metadata,
                stage_results=stage_results,
                total_duration_ms=total_duration,
                errors=errors,
                warnings=warnings,
            )
    
    # =========================================================================
    # STAGE METHODS
    # =========================================================================
    
    def _run_vision(
        self,
        image: Union[str, Path, bytes]
    ) -> List[Dict[str, Any]]:
        """
        Execute vision processing stage.
        
        Handles sketch preprocessing and primitive shape detection.
        
        Args:
            image: Input image path or bytes.
            
        Returns:
            List of detected shape dictionaries.
            
        Raises:
            PipelineError: If vision processing fails.
        """
        # Handle bytes input
        if isinstance(image, bytes):
            # Save to temp file for processing
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(image)
                image_path = f.name
        else:
            image_path = str(image)
        
        # Run vision processor
        detections = self.vision_processor.run(image_path)
        
        # Normalize output format
        if hasattr(detections, '__iter__') and not isinstance(detections, (str, dict)):
            return [
                d.to_dict() if hasattr(d, 'to_dict') else d
                for d in detections
            ]
        
        return detections if isinstance(detections, list) else []
    
    def _run_classification(
        self,
        detections: List[Dict[str, Any]]
    ) -> List[DetectedComponent]:
        """
        Execute classification stage.
        
        Maps detected shapes to UI component types.
        
        Args:
            detections: Raw shape detections from vision stage.
            
        Returns:
            List of classified UI components.
        """
        classified = self.classifier.classify_batch(detections)
        
        # Convert to DetectedComponent objects
        components = []
        for item in classified:
            if isinstance(item, dict):
                # Parse from dict
                bbox_data = item.get("bbox", {})
                bbox = BoundingBox(
                    x=bbox_data.get("x", 0),
                    y=bbox_data.get("y", 0),
                    width=bbox_data.get("width", 0.1),
                    height=bbox_data.get("height", 0.1),
                    confidence=bbox_data.get("confidence", item.get("confidence", 1.0))
                )
                
                # Determine component type
                ui_hint = item.get("ui_hint", item.get("type", "unknown"))
                try:
                    comp_type = ComponentType(ui_hint.lower())
                except ValueError:
                    comp_type = ComponentType.UNKNOWN
                
                component = DetectedComponent(
                    id=item.get("id", str(uuid.uuid4())[:8]),
                    type=comp_type,
                    bbox=bbox,
                    confidence=item.get("confidence", 1.0),
                    ui_hint=ui_hint,
                    properties=item.get("properties", {})
                )
                components.append(component)
            else:
                # Already a component object
                components.append(item)
        
        return components
    
    def _run_layout(
        self,
        components: List[Union[DetectedComponent, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Execute layout resolution stage.
        
        Builds hierarchical layout structure with:
        - Component grouping
        - Parent-child nesting
        - Flex direction inference
        - Reading order sorting
        
        Args:
            components: Classified UI components.
            
        Returns:
            Resolved layout tree dictionary.
        """
        # Convert to dict format for resolver
        nodes = [
            c.to_dict() if hasattr(c, 'to_dict') else c
            for c in components
        ]
        
        # Run layout resolver
        result = self.layout_resolver.resolve(nodes)
        
        # Extract tree from result
        if hasattr(result, 'tree'):
            return result.tree
        elif isinstance(result, dict):
            return result.get('tree', result)
        else:
            return result
    
    def _run_validation(
        self,
        layout: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute validation stage.
        
        Validates the inferred UI structure for:
        - Required properties
        - Valid nesting relationships
        - Reasonable dimensions
        
        Args:
            layout: Layout tree to validate.
            
        Returns:
            Validation result with 'valid' bool and 'warnings' list.
        """
        try:
            result = self.validator.validate(layout)
            
            if isinstance(result, bool):
                return {"valid": result, "warnings": []}
            elif isinstance(result, dict):
                return result
            else:
                return {"valid": True, "warnings": []}
                
        except Exception as e:
            return {"valid": False, "warnings": [str(e)]}
    
    def _apply_theme(
        self,
        layout: Dict[str, Any],
        theme: str
    ) -> Dict[str, Any]:
        """
        Apply theme tokens to layout tree.
        
        Injects style metadata including:
        - Colors (primary, background, text)
        - Typography (font family, sizes)
        - Spacing (padding, margins)
        - Border radius
        - Shadows
        
        Args:
            layout: Layout tree to theme.
            theme: Theme preset name.
            
        Returns:
            Themed layout tree with style metadata.
        """
        themed = self.theme_provider.apply_theme(layout, theme)
        return themed
    
    def _inject_motion(
        self,
        layout: Dict[str, Any],
        preset: str = "fade_in"
    ) -> Dict[str, Any]:
        """
        Inject motion/animation metadata.
        
        Adds Framer Motion-compatible animation data:
        - initial: Starting state
        - animate: Animated state
        - transition: Animation timing
        
        Args:
            layout: Themed layout tree.
            preset: Animation preset name.
            
        Returns:
            Layout tree with motion metadata.
        """
        # Update motion resolver settings
        if hasattr(self.motion_resolver, 'enable_motion'):
            self.motion_resolver.enable_motion = True
        
        motion_layout = self.motion_resolver.apply_motion(layout, preset)
        return motion_layout
    
    def _generate_code(
        self,
        layout: Dict[str, Any]
    ) -> GeneratedFiles:
        """
        Generate React + Tailwind code files.
        
        Produces:
        - page.tsx: Main page component
        - layout.tsx: Layout wrapper (optional)
        - components/*.tsx: Individual components (optional)
        
        Args:
            layout: Complete layout tree with styles and motion.
            
        Returns:
            GeneratedFiles object containing all code.
        """
        files = GeneratedFiles()
        
        # Generate main page
        page_code = self.code_renderer.render(layout)
        files.page = page_code
        
        # Generate layout wrapper (if configured)
        if self.config.generate_layout_file:
            try:
                if hasattr(self.code_renderer, 'render_layout'):
                    files.layout = self.code_renderer.render_layout(layout)
                else:
                    files.layout = self._generate_layout_wrapper()
            except Exception:
                pass  # Layout file is optional
        
        # Generate individual components (if configured)
        if self.config.generate_component_files:
            try:
                if hasattr(self.code_renderer, 'render_components'):
                    files.components = self.code_renderer.render_components(layout)
                else:
                    files.components = self._extract_components(layout)
            except Exception:
                pass  # Component files are optional
        
        return files
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _build_metadata(
        self,
        components: List[Dict[str, Any]],
        layout: Dict[str, Any]
    ) -> ComponentMetadata:
        """
        Build metadata about detected components.
        
        Args:
            components: List of detected components.
            layout: Resolved layout tree.
            
        Returns:
            ComponentMetadata object.
        """
        # Count by type
        by_type: Dict[str, int] = {}
        for comp in components:
            comp_type = comp.get("type", "unknown")
            by_type[comp_type] = by_type.get(comp_type, 0) + 1
        
        # Calculate average confidence
        confidences = [c.get("confidence", 1.0) for c in components]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Check for navigation and forms
        nav_types = {"navbar", "header", "sidebar", "nav", "menu"}
        form_types = {"input", "text_field", "checkbox", "radio", "dropdown", "button"}
        
        has_nav = any(t in nav_types for t in by_type.keys())
        has_forms = any(t in form_types for t in by_type.keys())
        
        return ComponentMetadata(
            total_count=len(components),
            by_type=by_type,
            detection_confidence=avg_confidence,
            layout_depth=self._calculate_depth(layout),
            has_navigation=has_nav,
            has_forms=has_forms,
        )
    
    def _count_nodes(self, tree: Dict[str, Any]) -> int:
        """Recursively count nodes in layout tree."""
        count = 1
        for child in tree.get("children", []):
            count += self._count_nodes(child)
        return count
    
    def _calculate_depth(self, tree: Dict[str, Any], current: int = 0) -> int:
        """Calculate maximum depth of layout tree."""
        max_depth = current
        for child in tree.get("children", []):
            child_depth = self._calculate_depth(child, current + 1)
            max_depth = max(max_depth, child_depth)
        return max_depth
    
    def _generate_layout_wrapper(self) -> str:
        """Generate a basic layout wrapper component."""
        return '''import React from "react";

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
}
'''
    
    def _extract_components(
        self,
        layout: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract individual components from layout tree."""
        components: Dict[str, str] = {}
        
        def extract_recursive(node: Dict[str, Any]) -> None:
            node_type = node.get("type", "").lower()
            
            # Only extract certain component types
            extractable = {"button", "card", "input", "navbar", "footer", "sidebar"}
            
            if node_type in extractable:
                name = f"{node_type.title()}"
                if name not in components:
                    components[name] = self._generate_component_stub(node)
            
            for child in node.get("children", []):
                extract_recursive(child)
        
        extract_recursive(layout)
        return components
    
    def _generate_component_stub(self, node: Dict[str, Any]) -> str:
        """Generate a stub component file."""
        name = node.get("type", "Component").title()
        return f'''import React from "react";

interface {name}Props {{
  className?: string;
  children?: React.ReactNode;
}}

export default function {name}({{ className = "", children }}: {name}Props) {{
  return (
    <div className={{`{name.lower()} ${{className}}`}}>
      {{children}}
    </div>
  );
}}
'''


# =============================================================================
# MOCK IMPLEMENTATIONS (Fallbacks)
# =============================================================================

class MockVisionProcessor:
    """Mock vision processor for development/testing."""
    
    def run(self, image_path: str) -> List[Dict[str, Any]]:
        """Return mock detections."""
        return [
            {
                "id": "shape_1",
                "type": "rectangle",
                "bbox": {"x": 0.1, "y": 0.05, "width": 0.8, "height": 0.1},
                "confidence": 0.95,
            },
            {
                "id": "shape_2",
                "type": "rectangle",
                "bbox": {"x": 0.1, "y": 0.2, "width": 0.35, "height": 0.3},
                "confidence": 0.88,
            },
            {
                "id": "shape_3",
                "type": "rectangle",
                "bbox": {"x": 0.55, "y": 0.2, "width": 0.35, "height": 0.3},
                "confidence": 0.90,
            },
            {
                "id": "shape_4",
                "type": "rectangle",
                "bbox": {"x": 0.3, "y": 0.6, "width": 0.4, "height": 0.08},
                "confidence": 0.85,
            },
        ]


class MockClassifier:
    """Mock classifier for development/testing."""
    
    def classify_batch(
        self,
        detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Return mock classifications."""
        ui_hints = ["navbar", "card", "card", "button"]
        
        classified = []
        for i, det in enumerate(detections):
            hint = ui_hints[i] if i < len(ui_hints) else "container"
            classified.append({
                **det,
                "ui_hint": hint,
                "type": hint,
            })
        
        return classified


class MockLayoutResolver:
    """Mock layout resolver for development/testing."""
    
    def resolve(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return mock layout tree."""
        return {
            "id": "root",
            "type": "container",
            "layout": "column",
            "children": [
                {
                    "id": "nav",
                    "type": "navbar",
                    "layout": "row",
                    "children": [],
                },
                {
                    "id": "content",
                    "type": "container",
                    "layout": "row",
                    "children": [
                        {"id": "card1", "type": "card", "children": []},
                        {"id": "card2", "type": "card", "children": []},
                    ],
                },
                {
                    "id": "cta",
                    "type": "button",
                    "children": [],
                },
            ],
        }


class MockThemeProvider:
    """Mock theme provider for development/testing."""
    
    def apply_theme(
        self,
        layout: Dict[str, Any],
        theme: str
    ) -> Dict[str, Any]:
        """Apply mock theme styles."""
        import copy
        themed = copy.deepcopy(layout)
        
        def apply_recursive(node: Dict[str, Any]) -> None:
            node["style"] = {
                "background": "#ffffff",
                "text": "#111827",
                "radius": "8px",
                "shadow": "sm",
            }
            for child in node.get("children", []):
                apply_recursive(child)
        
        apply_recursive(themed)
        themed["_theme"] = theme
        
        return themed


class MockMotionResolver:
    """Mock motion resolver for development/testing."""
    
    def __init__(self, enable_motion: bool = True):
        self.enable_motion = enable_motion
    
    def apply_motion(
        self,
        layout: Dict[str, Any],
        preset: str = "fade_in"
    ) -> Dict[str, Any]:
        """Apply mock motion metadata."""
        import copy
        motion_layout = copy.deepcopy(layout)
        
        if not self.enable_motion:
            return motion_layout
        
        def apply_recursive(node: Dict[str, Any]) -> None:
            if node.get("type") != "spacer":
                node["motion"] = {
                    "initial": {"opacity": 0, "y": 20},
                    "animate": {"opacity": 1, "y": 0},
                    "transition": {"duration": 0.3, "type": "spring"},
                }
            for child in node.get("children", []):
                apply_recursive(child)
        
        apply_recursive(motion_layout)
        return motion_layout


class MockCodeRenderer:
    """Mock code renderer for development/testing."""
    
    def render(self, layout: Dict[str, Any]) -> str:
        """Generate mock React code."""
        return '''import React from "react";
import { motion } from "framer-motion";

export default function Page() {
  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <motion.nav 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg shadow-sm p-4 mb-6"
      >
        <h1 className="text-xl font-semibold">Duiodle Generated UI</h1>
      </motion.nav>
      
      <div className="grid grid-cols-2 gap-6 mb-6">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-lg shadow-sm p-6"
        >
          <h2 className="text-lg font-medium">Card 1</h2>
          <p className="text-gray-600">Generated content area</p>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-lg shadow-sm p-6"
        >
          <h2 className="text-lg font-medium">Card 2</h2>
          <p className="text-gray-600">Generated content area</p>
        </motion.div>
      </div>
      
      <motion.button
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium"
      >
        Get Started
      </motion.button>
    </main>
  );
}
'''


class MockValidator:
    """Mock validator for development/testing."""
    
    def validate(self, layout: Dict[str, Any]) -> Dict[str, Any]:
        """Perform mock validation."""
        warnings = []
        
        # Check for empty layout
        if not layout.get("children"):
            warnings.append("Layout has no children")
        
        return {
            "valid": True,
            "warnings": warnings,
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_pipeline(
    theme: str = "minimal",
    enable_motion: bool = True,
    vision_provider: str = "mock",
    **kwargs
) -> DuiodlePipeline:
    """
    Factory function to create a configured pipeline.
    
    Args:
        theme: Default theme preset.
        enable_motion: Whether to enable motion by default.
        vision_provider: Vision AI provider (mock, openai, gemini).
        **kwargs: Additional configuration options.
        
    Returns:
        Configured DuiodlePipeline instance.
        
    Example:
        >>> pipeline = create_pipeline(
        ...     theme="professional",
        ...     enable_motion=True,
        ...     vision_provider="openai"
        ... )
        >>> result = pipeline.run("sketch.png")
    """
    config = PipelineConfig(
        default_theme=theme,
        enable_motion_default=enable_motion,
        vision_provider=vision_provider,
        **kwargs
    )
    
    return DuiodlePipeline(config)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "DuiodlePipeline",
    "create_pipeline",
    
    # Data structures
    "PipelineResult",
    "PipelineStage",
    "PipelineConfig",
    "DetectedComponent",
    "LayoutNode",
    "BoundingBox",
    "ComponentMetadata",
    "GeneratedFiles",
    "StageResult",
    
    # Enums
    "ThemePreset",
    "ComponentType",
    
    # Exceptions
    "PipelineError",
    "ValidationError",
    
    # Logger
    "PipelineLogger",
]
