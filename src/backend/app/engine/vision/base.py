"""
Base Vision Processor Module

This module defines the abstract interface for all vision processors
in the Duiodle system. It establishes the contract for image loading,
preprocessing, and shape detection operations.

The base class is designed for easy extension, allowing future
integration of deep learning models (YOLO, etc.) while maintaining
a consistent API.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import numpy as np


class PrimitiveShapeType(str, Enum):
    """
    Enumeration of primitive shape types detected by vision processors.
    
    These are raw geometric primitives, NOT UI components.
    The classification layer maps these to UI intent hints.
    """
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    LINE = "line"
    TRIANGLE = "triangle"
    ELLIPSE = "ellipse"
    POLYGON = "polygon"
    TEXT_REGION = "text_region"
    UNKNOWN = "unknown"


@dataclass
class NormalizedBoundingBox:
    """
    A bounding box with coordinates normalized to [0, 1] range.
    
    Normalization is relative to the source image dimensions,
    making the coordinates resolution-independent.
    
    Attributes:
        x: Left edge position (0 = left edge, 1 = right edge)
        y: Top edge position (0 = top edge, 1 = bottom edge)
        width: Box width as fraction of image width
        height: Box height as fraction of image height
    """
    x: float
    y: float
    width: float
    height: float
    
    def __post_init__(self) -> None:
        """Validate that all values are in [0, 1] range."""
        for field_name, value in [
            ("x", self.x),
            ("y", self.y),
            ("width", self.width),
            ("height", self.height),
        ]:
            if not 0 <= value <= 1:
                raise ValueError(
                    f"{field_name} must be in [0, 1] range, got {value}"
                )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
    
    @property
    def center_x(self) -> float:
        """Calculate normalized center X coordinate."""
        return self.x + (self.width / 2)
    
    @property
    def center_y(self) -> float:
        """Calculate normalized center Y coordinate."""
        return self.y + (self.height / 2)
    
    @property
    def area(self) -> float:
        """Calculate normalized area (as fraction of total image area)."""
        return self.width * self.height
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio (width / height)."""
        if self.height == 0:
            return float('inf')
        return self.width / self.height


@dataclass
class DetectedShape:
    """
    Represents a single shape detected by the vision processor.
    
    This is a raw detection result containing only geometric information.
    UI semantics are added by the classifier layer.
    
    Attributes:
        id: Unique identifier for this detection
        shape_type: The primitive geometric type
        bbox: Normalized bounding box
        confidence: Detection confidence score [0, 1]
        vertex_count: Number of vertices (for polygons)
        raw_contour: Original contour points (optional, for debugging)
    """
    id: str
    shape_type: PrimitiveShapeType
    bbox: NormalizedBoundingBox
    confidence: float
    vertex_count: Optional[int] = None
    raw_contour: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Excludes raw_contour as it's not JSON-serializable.
        """
        return {
            "id": self.id,
            "type": self.shape_type.value,
            "bbox": self.bbox.to_dict(),
            "confidence": self.confidence,
            "vertex_count": self.vertex_count,
        }


class BaseVisionProcessor(ABC):
    """
    Abstract base class for vision processors.
    
    This class defines the interface for all vision processing implementations.
    Concrete implementations may use traditional CV techniques (OpenCV) or
    deep learning models (YOLO, etc.).
    
    The processing pipeline follows these stages:
    1. load_image() - Load image from path or array
    2. preprocess() - Prepare image for detection
    3. detect_shapes() - Identify geometric primitives
    4. run() - Execute the full pipeline
    
    Example:
        processor = ConcreteVisionProcessor()
        detections = processor.run("sketch.png")
        for shape in detections:
            print(f"Found {shape.shape_type} at {shape.bbox}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the vision processor.
        
        Args:
            config: Optional configuration dictionary for processor settings.
                   Supported keys depend on the concrete implementation.
        """
        self._config = config or {}
        self._image: Optional[np.ndarray] = None
        self._image_width: int = 0
        self._image_height: int = 0
    
    @property
    def image_dimensions(self) -> tuple[int, int]:
        """Return the dimensions (width, height) of the loaded image."""
        return (self._image_width, self._image_height)
    
    @property
    def is_image_loaded(self) -> bool:
        """Check if an image has been loaded."""
        return self._image is not None
    
    @abstractmethod
    def load_image(
        self,
        source: Union[str, Path, np.ndarray]
    ) -> np.ndarray:
        """
        Load an image from a file path or NumPy array.
        
        Args:
            source: Either a file path (str/Path) or a NumPy array
                   containing the image data.
        
        Returns:
            The loaded image as a NumPy array in BGR format.
        
        Raises:
            FileNotFoundError: If the file path does not exist.
            ValueError: If the input format is invalid.
        """
        pass
    
    @abstractmethod
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess the image for shape detection.
        
        This may include operations like:
        - Grayscale conversion
        - Noise reduction
        - Thresholding
        - Edge detection
        
        Args:
            image: Input image as NumPy array.
        
        Returns:
            Preprocessed image ready for detection.
        """
        pass
    
    @abstractmethod
    def detect_shapes(
        self,
        preprocessed_image: np.ndarray
    ) -> List[DetectedShape]:
        """
        Detect geometric shapes in the preprocessed image.
        
        Args:
            preprocessed_image: Image that has been preprocessed.
        
        Returns:
            List of DetectedShape objects with normalized bounding boxes.
        """
        pass
    
    def run(
        self,
        source: Union[str, Path, np.ndarray]
    ) -> List[DetectedShape]:
        """
        Execute the full vision processing pipeline.
        
        This is the main entry point for processing images.
        
        Args:
            source: Image source (file path or NumPy array).
        
        Returns:
            List of detected shapes with normalized coordinates.
        """
        image = self.load_image(source)
        preprocessed = self.preprocess(image)
        return self.detect_shapes(preprocessed)
    
    def run_to_dict(
        self,
        source: Union[str, Path, np.ndarray]
    ) -> List[Dict[str, Any]]:
        """
        Execute the pipeline and return results as dictionaries.
        
        Convenience method for API responses.
        
        Args:
            source: Image source (file path or NumPy array).
        
        Returns:
            List of detection dictionaries.
        """
        detections = self.run(source)
        return [d.to_dict() for d in detections]
    
    def normalize_coordinates(
        self,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> NormalizedBoundingBox:
        """
        Convert pixel coordinates to normalized [0, 1] coordinates.
        
        Args:
            x: Left edge in pixels
            y: Top edge in pixels
            width: Width in pixels
            height: Height in pixels
        
        Returns:
            NormalizedBoundingBox with values in [0, 1] range.
        
        Raises:
            ValueError: If image dimensions are not set.
        """
        if self._image_width == 0 or self._image_height == 0:
            raise ValueError(
                "Image dimensions not set. Load an image first."
            )
        
        return NormalizedBoundingBox(
            x=max(0, min(1, x / self._image_width)),
            y=max(0, min(1, y / self._image_height)),
            width=max(0, min(1, width / self._image_width)),
            height=max(0, min(1, height / self._image_height)),
        )
