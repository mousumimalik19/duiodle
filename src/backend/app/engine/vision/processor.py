"""
Vision Processing Module for Duiodle.

This module provides vision processors that analyze UI sketches:
- MockVisionProcessor: OpenCV-based (development, no API key)
- OpenAIVisionProcessor: GPT-4o Vision API (production)
- GeminiVisionProcessor: Gemini 2.0 Flash API (production)

All processors return DetectedShape objects compatible with the layout engine.

Usage:
    from app.engine.vision.processor import VisionProcessorFactory
    
    # Create processor from settings
    processor = VisionProcessorFactory.create_from_settings()
    
    # Process an image
    shapes = processor.run("/path/to/sketch.png")
"""

from __future__ import annotations

import base64
import json
import logging
import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

# Import configuration
from app.core.config import settings, VisionProvider, validate_vision_config

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class PrimitiveShapeType(str, Enum):
    """Primitive shape types detected by vision."""
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
    Bounding box with coordinates normalized to [0, 1].
    
    Attributes:
        x: Left edge (0 = left, 1 = right)
        y: Top edge (0 = top, 1 = bottom)
        width: Width as fraction of image width
        height: Height as fraction of image height
    """
    x: float
    y: float
    width: float
    height: float
    
    def __post_init__(self) -> None:
        """Clamp values to valid range."""
        self.x = max(0.0, min(1.0, self.x))
        self.y = max(0.0, min(1.0, self.y))
        self.width = max(0.0, min(1.0 - self.x, self.width))
        self.height = max(0.0, min(1.0 - self.y, self.height))
    
    @property
    def center_x(self) -> float:
        return self.x + self.width / 2
    
    @property
    def center_y(self) -> float:
        return self.y + self.height / 2
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height if self.height > 0 else 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "x": round(self.x, 4),
            "y": round(self.y, 4),
            "width": round(self.width, 4),
            "height": round(self.height, 4),
        }


@dataclass
class DetectedShape:
    """
    A shape detected by the vision processor.
    
    This is the output format that feeds into the layout engine.
    """
    id: str
    shape_type: PrimitiveShapeType
    bbox: NormalizedBoundingBox
    confidence: float = 0.8
    ui_hint: str = "container"
    vertex_count: int = 4
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.shape_type.value,
            "bbox": self.bbox.to_dict(),
            "confidence": round(self.confidence, 3),
            "ui_hint": self.ui_hint,
            "vertex_count": self.vertex_count,
            "properties": self.properties,
        }


# =============================================================================
# BASE PROCESSOR
# =============================================================================

class BaseVisionProcessor(ABC):
    """
    Abstract base class for vision processors.
    
    All implementations must provide load_image, preprocess, and detect_shapes.
    """
    
    @abstractmethod
    def load_image(self, source: Union[str, Path, np.ndarray]) -> np.ndarray:
        """Load an image from path or array."""
        pass
    
    @abstractmethod
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for analysis."""
        pass
    
    @abstractmethod
    def detect_shapes(self, image: np.ndarray) -> List[DetectedShape]:
        """Detect shapes in the preprocessed image."""
        pass
    
    def run(self, source: Union[str, Path, np.ndarray]) -> List[DetectedShape]:
        """
        Run the complete vision pipeline.
        
        Args:
            source: Image path or numpy array
            
        Returns:
            List of detected shapes
        """
        logger.info(f"Vision processor starting: {type(self).__name__}")
        image = self.load_image(source)
        processed = self.preprocess(image)
        shapes = self.detect_shapes(processed)
        logger.info(f"Detected {len(shapes)} shapes")
        return shapes


# =============================================================================
# MOCK VISION PROCESSOR (OpenCV)
# =============================================================================

class MockVisionProcessor(BaseVisionProcessor):
    """
    Mock vision processor using OpenCV.
    
    Uses traditional computer vision (contour detection) for development.
    No API key required.
    """
    
    def __init__(
        self,
        min_area_ratio: float = 0.001,
        blur_kernel_size: int = 5,
        canny_low: int = 50,
        canny_high: int = 150,
    ) -> None:
        self.min_area_ratio = min_area_ratio
        self.blur_kernel_size = blur_kernel_size
        self.canny_low = canny_low
        self.canny_high = canny_high
        
        # Try to import OpenCV
        try:
            import cv2
            self.cv2 = cv2
            self._opencv_available = True
            logger.info("OpenCV loaded successfully")
        except ImportError:
            self._opencv_available = False
            logger.warning("OpenCV not available, using sample data")
    
    def load_image(self, source: Union[str, Path, np.ndarray]) -> np.ndarray:
        if isinstance(source, np.ndarray):
            return source
        
        if not self._opencv_available:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        image = self.cv2.imread(str(path))
        if image is None:
            raise ValueError(f"Could not load image: {path}")
        
        logger.debug(f"Loaded image: {path} ({image.shape})")
        return image
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        if not self._opencv_available:
            return image
        
        if len(image.shape) == 3:
            gray = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        blurred = self.cv2.GaussianBlur(
            gray,
            (self.blur_kernel_size, self.blur_kernel_size),
            0
        )
        
        return blurred
    
    def detect_shapes(self, image: np.ndarray) -> List[DetectedShape]:
        if not self._opencv_available:
            return self._generate_sample_shapes()
        
        height, width = image.shape[:2]
        image_area = width * height
        min_area = image_area * self.min_area_ratio
        
        # Edge detection
        edges = self.cv2.Canny(image, self.canny_low, self.canny_high)
        
        # Find contours
        contours, _ = self.cv2.findContours(
            edges,
            self.cv2.RETR_EXTERNAL,
            self.cv2.CHAIN_APPROX_SIMPLE
        )
        
        shapes: List[DetectedShape] = []
        
        for contour in contours:
            area = self.cv2.contourArea(contour)
            if area < min_area:
                continue
            
            x, y, w, h = self.cv2.boundingRect(contour)
            
            bbox = NormalizedBoundingBox(
                x=x / width,
                y=y / height,
                width=w / width,
                height=h / height,
            )
            
            # Approximate polygon
            epsilon = 0.02 * self.cv2.arcLength(contour, True)
            approx = self.cv2.approxPolyDP(contour, epsilon, True)
            vertex_count = len(approx)
            
            shape_type, ui_hint = self._classify_shape(vertex_count, bbox)
            
            shapes.append(DetectedShape(
                id=f"shape_{uuid.uuid4().hex[:8]}",
                shape_type=shape_type,
                bbox=bbox,
                confidence=0.8,
                ui_hint=ui_hint,
                vertex_count=vertex_count,
            ))
        
        return shapes
    
    def _classify_shape(
        self,
        vertex_count: int,
        bbox: NormalizedBoundingBox
    ) -> tuple[PrimitiveShapeType, str]:
        """Classify shape based on vertex count and geometry."""
        aspect_ratio = bbox.aspect_ratio
        
        if vertex_count == 3:
            return PrimitiveShapeType.TRIANGLE, "icon"
        elif vertex_count == 4:
            if bbox.area < 0.05 and 1.5 < aspect_ratio < 5:
                return PrimitiveShapeType.RECTANGLE, "button"
            elif bbox.area > 0.2:
                return PrimitiveShapeType.RECTANGLE, "container"
            else:
                return PrimitiveShapeType.RECTANGLE, "card"
        elif vertex_count > 6:
            if 0.8 < aspect_ratio < 1.2:
                return PrimitiveShapeType.CIRCLE, "icon"
            else:
                return PrimitiveShapeType.ELLIPSE, "badge"
        else:
            return PrimitiveShapeType.POLYGON, "container"
    
    def _generate_sample_shapes(self) -> List[DetectedShape]:
        """Generate sample shapes when OpenCV unavailable."""
        return [
            DetectedShape(
                id="shape_header",
                shape_type=PrimitiveShapeType.RECTANGLE,
                bbox=NormalizedBoundingBox(0.05, 0.05, 0.9, 0.1),
                confidence=0.9,
                ui_hint="container",
            ),
            DetectedShape(
                id="shape_card1",
                shape_type=PrimitiveShapeType.RECTANGLE,
                bbox=NormalizedBoundingBox(0.05, 0.2, 0.4, 0.3),
                confidence=0.85,
                ui_hint="card",
            ),
            DetectedShape(
                id="shape_card2",
                shape_type=PrimitiveShapeType.RECTANGLE,
                bbox=NormalizedBoundingBox(0.55, 0.2, 0.4, 0.3),
                confidence=0.85,
                ui_hint="card",
            ),
            DetectedShape(
                id="shape_button",
                shape_type=PrimitiveShapeType.RECTANGLE,
                bbox=NormalizedBoundingBox(0.3, 0.6, 0.4, 0.08),
                confidence=0.9,
                ui_hint="button",
            ),
        ]


# =============================================================================
# OPENAI VISION PROCESSOR
# =============================================================================

class OpenAIVisionProcessor(BaseVisionProcessor):
    """
    Vision processor using OpenAI's GPT-4o API.
    
    Sends images to GPT-4o for analysis and receives structured UI descriptions.
    API key is loaded from settings.OPENAI_API_KEY.
    """
    
    SYSTEM_PROMPT = """You are a UI analysis expert. Analyze the provided sketch and identify UI elements.

For each element, provide:
1. Type: container, button, input, card, header, text, image, icon, divider, nav, footer
2. Bounding box: normalized coordinates (0-1) as {x, y, width, height}
3. Confidence: 0-1

Respond with ONLY valid JSON:
{
  "elements": [
    {
      "id": "elem_1",
      "type": "button",
      "bbox": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.1},
      "confidence": 0.9,
      "ui_hint": "button",
      "properties": {"label": "Submit"}
    }
  ]
}"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> None:
        # Use settings as defaults
        self.api_key = api_key or settings.OPENAI_API_KEY.get_secret_value()
        self.model = model or settings.VISION_MODEL_OPENAI
        self.max_tokens = max_tokens or settings.VISION_MAX_TOKENS
        self.temperature = temperature or settings.VISION_TEMPERATURE
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY in .env"
            )
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self._available = True
            logger.info(f"OpenAI client initialized ({self.model})")
        except ImportError:
            self._available = False
            logger.error("openai package not installed")
    
    def load_image(self, source: Union[str, Path, np.ndarray]) -> np.ndarray:
        if isinstance(source, np.ndarray):
            try:
                import cv2
                _, buffer = cv2.imencode('.png', source)
                self._image_bytes = buffer.tobytes()
            except ImportError:
                from PIL import Image
                import io
                img = Image.fromarray(source)
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                self._image_bytes = buf.getvalue()
            return source
        
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        with open(path, "rb") as f:
            self._image_bytes = f.read()
        
        return np.zeros((1, 1, 3), dtype=np.uint8)
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        return image
    
    def detect_shapes(self, image: np.ndarray) -> List[DetectedShape]:
        if not self._available:
            logger.error("OpenAI client not available")
            return []
        
        if not hasattr(self, "_image_bytes"):
            logger.error("No image loaded")
            return []
        
        try:
            # Encode to base64
            base64_image = base64.b64encode(self._image_bytes).decode("utf-8")
            
            # Detect MIME type
            if self._image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                mime = "image/png"
            elif self._image_bytes[:2] == b'\xff\xd8':
                mime = "image/jpeg"
            else:
                mime = "image/png"
            
            logger.info(f"Calling OpenAI API ({self.model})...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this UI sketch:"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content[:200]}...")
            
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _parse_response(self, content: str) -> List[DetectedShape]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                logger.error("No JSON in response")
                return []
            
            data = json.loads(json_match.group())
            elements = data.get("elements", [])
            
            shapes: List[DetectedShape] = []
            for elem in elements:
                bbox_data = elem.get("bbox", {})
                bbox = NormalizedBoundingBox(
                    x=float(bbox_data.get("x", 0)),
                    y=float(bbox_data.get("y", 0)),
                    width=float(bbox_data.get("width", 0.1)),
                    height=float(bbox_data.get("height", 0.1)),
                )
                
                shapes.append(DetectedShape(
                    id=elem.get("id", f"elem_{uuid.uuid4().hex[:8]}"),
                    shape_type=PrimitiveShapeType.RECTANGLE,
                    bbox=bbox,
                    confidence=float(elem.get("confidence", 0.8)),
                    ui_hint=elem.get("ui_hint", elem.get("type", "container")),
                    properties=elem.get("properties", {}),
                ))
            
            return shapes
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []


# =============================================================================
# GEMINI VISION PROCESSOR
# =============================================================================

class GeminiVisionProcessor(BaseVisionProcessor):
    """
    Vision processor using Google's Gemini 2.0 Flash API.
    
    API key is loaded from settings.GEMINI_API_KEY.
    """
    
    PROMPT = """Analyze this UI sketch and identify all UI elements.

For each element, provide:
1. Type: container, button, input, card, header, text, image, icon, divider
2. Bounding box: normalized (0-1) as {x, y, width, height}
3. Confidence: 0-1

Return ONLY valid JSON:
{
  "elements": [
    {
      "id": "elem_1",
      "type": "button",
      "bbox": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.1},
      "confidence": 0.9,
      "ui_hint": "button"
    }
  ]
}"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY.get_secret_value()
        self.model = model or settings.VISION_MODEL_GEMINI
        self.max_tokens = max_tokens or settings.VISION_MAX_TOKENS
        self.temperature = temperature or settings.VISION_TEMPERATURE
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY in .env"
            )
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
            self.client = genai.GenerativeModel(self.model)
            self._available = True
            logger.info(f"Gemini client initialized ({self.model})")
        except ImportError:
            self._available = False
            logger.error("google-generativeai package not installed")
    
    def load_image(self, source: Union[str, Path, np.ndarray]) -> np.ndarray:
        if isinstance(source, np.ndarray):
            try:
                import cv2
                _, buffer = cv2.imencode('.png', source)
                self._image_bytes = buffer.tobytes()
            except ImportError:
                from PIL import Image
                import io
                img = Image.fromarray(source)
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                self._image_bytes = buf.getvalue()
            return source
        
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        with open(path, "rb") as f:
            self._image_bytes = f.read()
        
        return np.zeros((1, 1, 3), dtype=np.uint8)
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        return image
    
    def detect_shapes(self, image: np.ndarray) -> List[DetectedShape]:
        if not self._available:
            logger.error("Gemini client not available")
            return []
        
        if not hasattr(self, "_image_bytes"):
            logger.error("No image loaded")
            return []
        
        try:
            # Detect MIME type
            if self._image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                mime = "image/png"
            elif self._image_bytes[:2] == b'\xff\xd8':
                mime = "image/jpeg"
            else:
                mime = "image/png"
            
            image_part = {
                "mime_type": mime,
                "data": self._image_bytes
            }
            
            logger.info(f"Calling Gemini API ({self.model})...")
            
            response = self.client.generate_content(
                [self.PROMPT, image_part],
                generation_config={
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
            )
            
            logger.debug(f"Gemini response: {response.text[:200]}...")
            
            return self._parse_response(response.text)
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _parse_response(self, content: str) -> List[DetectedShape]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                logger.error("No JSON in response")
                return []
            
            data = json.loads(json_match.group())
            elements = data.get("elements", [])
            
            shapes: List[DetectedShape] = []
            for elem in elements:
                bbox_data = elem.get("bbox", {})
                bbox = NormalizedBoundingBox(
                    x=float(bbox_data.get("x", 0)),
                    y=float(bbox_data.get("y", 0)),
                    width=float(bbox_data.get("width", 0.1)),
                    height=float(bbox_data.get("height", 0.1)),
                )
                
                shapes.append(DetectedShape(
                    id=elem.get("id", f"elem_{uuid.uuid4().hex[:8]}"),
                    shape_type=PrimitiveShapeType.RECTANGLE,
                    bbox=bbox,
                    confidence=float(elem.get("confidence", 0.8)),
                    ui_hint=elem.get("ui_hint", elem.get("type", "container")),
                    properties=elem.get("properties", {}),
                ))
            
            return shapes
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []


# =============================================================================
# FACTORY
# =============================================================================

class VisionProcessorFactory:
    """
    Factory for creating vision processor instances.
    
    Reads from settings to determine which processor to create.
    
    Usage:
        processor = VisionProcessorFactory.create_from_settings()
        shapes = processor.run("sketch.png")
    """
    
    _processors = {
        VisionProvider.MOCK: MockVisionProcessor,
        VisionProvider.OPENAI: OpenAIVisionProcessor,
        VisionProvider.GEMINI: GeminiVisionProcessor,
    }
    
    @classmethod
    def create_from_settings(cls) -> BaseVisionProcessor:
        """
        Create processor based on settings.
        
        Falls back to MockVisionProcessor if configuration is invalid.
        """
        provider = settings.VISION_PROVIDER
        
        is_valid, message = validate_vision_config()
        if not is_valid:
            logger.warning(f"Vision config invalid: {message}")
            logger.info("Falling back to MockVisionProcessor")
            return MockVisionProcessor()
        
        logger.info(f"Creating vision processor: {provider.value}")
        return cls._processors[provider]()
    
    @classmethod
    def create(
        cls,
        provider: Union[str, VisionProvider],
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseVisionProcessor:
        """
        Create a specific processor.
        
        Args:
            provider: Provider name or enum
            api_key: API key (overrides settings)
            **kwargs: Additional processor arguments
        """
        if isinstance(provider, str):
            try:
                provider = VisionProvider(provider.lower())
            except ValueError:
                logger.warning(f"Unknown provider '{provider}', using mock")
                provider = VisionProvider.MOCK
        
        if provider == VisionProvider.MOCK:
            return MockVisionProcessor(**kwargs)
        elif provider == VisionProvider.OPENAI:
            return OpenAIVisionProcessor(api_key=api_key, **kwargs)
        elif provider == VisionProvider.GEMINI:
            return GeminiVisionProcessor(api_key=api_key, **kwargs)
        else:
            return MockVisionProcessor(**kwargs)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers."""
        available = [VisionProvider.MOCK.value]
        
        if settings.OPENAI_API_KEY.get_secret_value():
            available.append(VisionProvider.OPENAI.value)
        
        if settings.GEMINI_API_KEY.get_secret_value():
            available.append(VisionProvider.GEMINI.value)
        
        return available
