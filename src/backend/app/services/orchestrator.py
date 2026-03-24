"""
Duiodle Pipeline Orchestrator

Central orchestration layer that connects all engine modules into a unified
processing pipeline for converting hand-drawn sketches into production-ready
React interfaces.

Pipeline Flow:
    1. Vision Processing - Detect shapes from input image
    2. Shape Classification - Map shapes to UI intent hints
    3. Layout Resolution - Build hierarchical component tree
    4. Theme Application - Apply design tokens and styles
    5. Motion Injection - Add animation metadata
    6. Code Generation - Render React + Tailwind code

Usage:
    orchestrator = DuiodleOrchestrator(theme="professional", enable_motion=True)
    result = orchestrator.process_image("sketch.png")
    print(result["react_code"])
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Vision layer imports
from app.engine.vision.processor import (
    MockVisionProcessor,
    VisionProcessorFactory,
    BaseVisionProcessor,
)
from app.engine.vision.classifier import ShapeClassifier

# Layout layer imports
from app.engine.layout.resolver import LayoutResolver

# Theme layer imports
from app.engine.theme.provider import ThemeProvider
from app.engine.theme.tailwind_mapper import TailwindMapper

# Motion layer imports
from app.engine.motion.resolver import MotionResolver

# Codegen layer imports
from app.engine.codegen.react_renderer import ReactRenderer


class PipelineStage(str, Enum):
    """Enumeration of pipeline processing stages."""
    
    VISION = "vision"
    CLASSIFICATION = "classification"
    LAYOUT = "layout"
    THEME = "theme"
    MOTION = "motion"
    CODEGEN = "codegen"


class PipelineError(Exception):
    """
    Exception raised when a pipeline stage fails.
    
    Attributes:
        stage: The pipeline stage where the error occurred.
        message: Human-readable error description.
        original_error: The underlying exception that caused the failure.
    """
    
    def __init__(
        self,
        stage: PipelineStage,
        message: str,
        original_error: Optional[Exception] = None
    ) -> None:
        self.stage = stage
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{stage.value.upper()}] {message}")


@dataclass
class PipelineMetrics:
    """
    Metrics collected during pipeline execution.
    
    Attributes:
        total_duration_ms: Total processing time in milliseconds.
        stage_durations_ms: Duration of each stage in milliseconds.
        shapes_detected: Number of shapes detected by vision layer.
        nodes_generated: Number of nodes in final UI tree.
        warnings: List of non-fatal warnings during processing.
    """
    
    total_duration_ms: float = 0.0
    stage_durations_ms: dict[str, float] = field(default_factory=dict)
    shapes_detected: int = 0
    nodes_generated: int = 0
    warnings: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            "total_duration_ms": round(self.total_duration_ms, 2),
            "stage_durations_ms": {
                k: round(v, 2) for k, v in self.stage_durations_ms.items()
            },
            "shapes_detected": self.shapes_detected,
            "nodes_generated": self.nodes_generated,
            "warnings": self.warnings
        }


@dataclass
class ProcessingResult:
    """
    Complete result from pipeline processing.
    
    Attributes:
        ui_tree: The enriched UI component tree with layout, theme, and motion.
        react_code: Generated React + Tailwind + Framer Motion code.
        metadata: Processing metadata including theme and motion settings.
        metrics: Performance and diagnostic metrics.
        request_id: Unique identifier for this processing request.
    """
    
    ui_tree: dict[str, Any]
    react_code: str
    metadata: dict[str, Any]
    metrics: PipelineMetrics
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert result to dictionary for API response.
        
        Returns:
            Dictionary containing all result data.
        """
        return {
            "request_id": self.request_id,
            "ui_tree": self.ui_tree,
            "react_code": self.react_code,
            "metadata": self.metadata,
            "metrics": self.metrics.to_dict()
        }


class DuiodleOrchestrator:
    """
    Central orchestrator for the Duiodle sketch-to-UI pipeline.
    
    Coordinates all engine modules to transform hand-drawn sketches
    into production-ready React interfaces with Tailwind CSS styling
    and optional Framer Motion animations.
    
    Attributes:
        theme: The design theme to apply (e.g., 'minimal', 'professional').
        enable_motion: Whether to inject animation metadata.
        motion_preset: The default motion preset to use when motion is enabled.
    
    Example:
        >>> orchestrator = DuiodleOrchestrator(
        ...     theme="professional",
        ...     enable_motion=True
        ... )
        >>> result = orchestrator.process_image("sketch.png")
        >>> print(result["react_code"])
    """
    
    # Supported themes for validation
    SUPPORTED_THEMES: set[str] = {
        "minimal", "professional", "aesthetic", "playful",
        "portfolio", "tropical", "gradient", "animated"
    }
    
    # Default motion preset
    DEFAULT_MOTION_PRESET: str = "fade_in"
    
    def __init__(
        self,
        theme: str = "minimal",
        enable_motion: bool = False,
        motion_preset: str = "fade_in"
    ) -> None:
        """
        Initialize the orchestrator with all engine modules.
        
        Args:
            theme: Design theme name. Defaults to 'minimal'.
            enable_motion: Whether to enable motion animations. Defaults to False.
            motion_preset: Motion preset to use. Defaults to 'fade_in'.
        
        Raises:
            ValueError: If theme name is not supported.
        """
        # Validate theme
        if theme not in self.SUPPORTED_THEMES:
            raise ValueError(
                f"Unsupported theme '{theme}'. "
                f"Available themes: {', '.join(sorted(self.SUPPORTED_THEMES))}"
            )
        
        self.theme = theme
        self.enable_motion = enable_motion
        self.motion_preset = motion_preset
        
        # Initialize Vision layer - use factory for provider selection
        try:
            self.vision_processor = VisionProcessorFactory.create_from_settings()
        except Exception:
            # Fallback to mock processor if settings fail
            self.vision_processor = MockVisionProcessor()
        self.classifier = ShapeClassifier()
        
        # Initialize Layout layer
        self.layout_resolver = LayoutResolver()
        
        # Initialize Theme layer
        self.theme_provider = ThemeProvider()
        self.tailwind_mapper = TailwindMapper()
        
        # Initialize Motion layer
        self.motion_resolver = MotionResolver(enable_motion=enable_motion)
        
        # Initialize Codegen layer
        self.renderer = ReactRenderer(tailwind_mapper=self.tailwind_mapper)
    
    def process_image(self, image_path: str) -> dict[str, Any]:
        """
        Process an image through the complete Duiodle pipeline.
        
        Takes an input image path, runs it through all processing stages,
        and returns a complete result with UI tree, React code, and metadata.
        
        Args:
            image_path: Path to the input sketch image.
        
        Returns:
            Dictionary containing:
                - ui_tree: The enriched component tree
                - react_code: Generated React code string
                - metadata: Processing metadata
        
        Raises:
            PipelineError: If any stage fails during processing.
            FileNotFoundError: If the input image does not exist.
        
        Example:
            >>> result = orchestrator.process_image("sketch.png")
            >>> print(result["ui_tree"]["type"])
            'container'
        """
        # Validate input file exists
        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"Input image not found: {image_path}")
        
        metrics = PipelineMetrics()
        start_time = time.perf_counter()
        
        # Stage 1: Vision Processing
        detections = self._execute_stage(
            stage=PipelineStage.VISION,
            operation=lambda: self.vision_processor.run(image_path),
            metrics=metrics
        )
        metrics.shapes_detected = len(detections) if detections else 0
        
        # Stage 2: Shape Classification
        classified = self._execute_stage(
            stage=PipelineStage.CLASSIFICATION,
            operation=lambda: self.classifier.classify_batch(detections),
            metrics=metrics
        )
        
        # Stage 3: Layout Resolution
        layout_result = self._execute_stage(
            stage=PipelineStage.LAYOUT,
            operation=lambda: self.layout_resolver.resolve(
                self._convert_classified_to_nodes(classified)
            ),
            metrics=metrics
        )
        
        # Extract layout tree from result
        layout_tree = self._extract_layout_tree(layout_result)
        
        # Stage 4: Theme Application
        themed_tree = self._execute_stage(
            stage=PipelineStage.THEME,
            operation=lambda: self.theme_provider.apply_theme(layout_tree, self.theme),
            metrics=metrics
        )
        
        # Stage 5: Motion Injection
        motion_tree = self._execute_stage(
            stage=PipelineStage.MOTION,
            operation=lambda: self.motion_resolver.apply_motion(
                themed_tree,
                preset_name=self.motion_preset
            ),
            metrics=metrics
        )
        
        # Stage 6: Code Generation
        react_code = self._execute_stage(
            stage=PipelineStage.CODEGEN,
            operation=lambda: self.renderer.render(motion_tree),
            metrics=metrics
        )
        
        # Calculate total duration
        metrics.total_duration_ms = (time.perf_counter() - start_time) * 1000
        metrics.nodes_generated = self._count_nodes(motion_tree)
        
        # Build result
        result = ProcessingResult(
            ui_tree=motion_tree,
            react_code=react_code,
            metadata={
                "theme": self.theme,
                "motion_enabled": self.enable_motion,
                "motion_preset": self.motion_preset if self.enable_motion else None,
                "input_image": str(image_path)
            },
            metrics=metrics
        )
        
        return result.to_dict()
    
    def _execute_stage(
        self,
        stage: PipelineStage,
        operation: callable,
        metrics: PipelineMetrics
    ) -> Any:
        """
        Execute a pipeline stage with timing and error handling.
        
        Args:
            stage: The pipeline stage being executed.
            operation: Callable to execute for this stage.
            metrics: Metrics object to record timing.
        
        Returns:
            The result of the operation.
        
        Raises:
            PipelineError: If the operation fails.
        """
        stage_start = time.perf_counter()
        
        try:
            result = operation()
            metrics.stage_durations_ms[stage.value] = (
                (time.perf_counter() - stage_start) * 1000
            )
            return result
            
        except PipelineError:
            # Re-raise pipeline errors as-is
            raise
            
        except Exception as e:
            metrics.stage_durations_ms[stage.value] = (
                (time.perf_counter() - stage_start) * 1000
            )
            raise PipelineError(
                stage=stage,
                message=f"Stage failed: {str(e)}",
                original_error=e
            ) from e
    
    def _convert_classified_to_nodes(
        self,
        classified: list[Any]
    ) -> list[dict[str, Any]]:
        """
        Convert classified shape objects to node dictionaries for layout resolver.
        
        Args:
            classified: List of classified shape objects from classifier.
        
        Returns:
            List of node dictionaries compatible with layout resolver.
        """
        nodes = []
        
        for item in classified:
            # Handle ClassifiedShape objects
            if hasattr(item, 'to_dict'):
                node_dict = item.to_dict()
            elif hasattr(item, '__dict__'):
                node_dict = vars(item)
            elif isinstance(item, dict):
                node_dict = item
            else:
                continue
            
            # Normalize to expected format
            node = {
                "id": node_dict.get("id", str(uuid.uuid4())),
                "type": str(node_dict.get("ui_hint", node_dict.get("type", "container"))),
                "bbox": self._normalize_bbox(node_dict.get("bbox", {})),
                "confidence": float(node_dict.get("confidence", 0.5)),
                "ui_hint": str(node_dict.get("ui_hint", "container"))
            }
            nodes.append(node)
        
        return nodes
    
    def _normalize_bbox(self, bbox: Any) -> dict[str, float]:
        """
        Normalize bounding box to dictionary format.
        
        Args:
            bbox: Bounding box in various formats.
        
        Returns:
            Dictionary with x, y, width, height keys.
        """
        if isinstance(bbox, dict):
            return {
                "x": float(bbox.get("x", 0)),
                "y": float(bbox.get("y", 0)),
                "width": float(bbox.get("width", 0.1)),
                "height": float(bbox.get("height", 0.1))
            }
        elif hasattr(bbox, "x"):
            return {
                "x": float(bbox.x),
                "y": float(bbox.y),
                "width": float(bbox.width),
                "height": float(bbox.height)
            }
        else:
            return {"x": 0, "y": 0, "width": 0.1, "height": 0.1}
    
    def _extract_layout_tree(self, layout_result: Any) -> dict[str, Any]:
        """
        Extract the layout tree from the layout resolver result.
        
        Args:
            layout_result: Result from layout resolver (may be LayoutResult or dict).
        
        Returns:
            The layout tree as a dictionary.
        """
        if isinstance(layout_result, dict):
            return layout_result
        elif hasattr(layout_result, "tree"):
            return layout_result.tree
        elif hasattr(layout_result, "to_dict"):
            return layout_result.to_dict()
        else:
            # Fallback: create empty container
            return {
                "type": "container",
                "layout": "column",
                "children": []
            }
    
    def _count_nodes(self, tree: dict[str, Any]) -> int:
        """
        Recursively count total nodes in the UI tree.
        
        Args:
            tree: The UI tree to count nodes in.
        
        Returns:
            Total number of nodes including nested children.
        """
        if not isinstance(tree, dict):
            return 0
        
        count = 1
        children = tree.get("children", [])
        
        for child in children:
            count += self._count_nodes(child)
        
        return count
    
    def update_theme(self, new_theme: str) -> None:
        """
        Update the active theme.
        
        Args:
            new_theme: New theme name to apply.
        
        Raises:
            ValueError: If theme is not supported.
        """
        if new_theme not in self.SUPPORTED_THEMES:
            raise ValueError(
                f"Unsupported theme '{new_theme}'. "
                f"Available: {', '.join(sorted(self.SUPPORTED_THEMES))}"
            )
        self.theme = new_theme
    
    def update_motion(
        self,
        enable: bool,
        preset: Optional[str] = None
    ) -> None:
        """
        Update motion settings.
        
        Args:
            enable: Whether to enable motion.
            preset: Optional motion preset name.
        """
        self.enable_motion = enable
        self.motion_resolver = MotionResolver(enable_motion=enable)
        
        if preset:
            self.motion_preset = preset
    
    def get_supported_themes(self) -> list[str]:
        """
        Get list of supported theme names.
        
        Returns:
            Sorted list of available theme names.
        """
        return sorted(self.SUPPORTED_THEMES)
    
    def get_pipeline_info(self) -> dict[str, Any]:
        """
        Get information about the current pipeline configuration.
        
        Returns:
            Dictionary with pipeline configuration details.
        """
        return {
            "theme": self.theme,
            "enable_motion": self.enable_motion,
            "motion_preset": self.motion_preset,
            "supported_themes": self.get_supported_themes(),
            "stages": [stage.value for stage in PipelineStage]
        }


def create_orchestrator(
    theme: str = "minimal",
    enable_motion: bool = False,
    motion_preset: str = "fade_in"
) -> DuiodleOrchestrator:
    """
    Factory function to create a configured orchestrator instance.
    
    Args:
        theme: Design theme to apply.
        enable_motion: Whether to enable animations.
        motion_preset: Motion preset to use.
    
    Returns:
        Configured DuiodleOrchestrator instance.
    
    Example:
        >>> orchestrator = create_orchestrator(theme="professional")
        >>> result = orchestrator.process_image("sketch.png")
    """
    return DuiodleOrchestrator(
        theme=theme,
        enable_motion=enable_motion,
        motion_preset=motion_preset
    )
