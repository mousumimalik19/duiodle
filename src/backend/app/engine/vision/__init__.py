"""
Vision Engine Module for Duiodle.

This module provides computer vision capabilities for detecting
and classifying shapes in UI sketches.

Components:
- BaseVisionProcessor: Abstract base class for all processors
- MockVisionProcessor: OpenCV-based processor for development
- OpenAIVisionProcessor: GPT-4o powered vision analysis
- GeminiVisionProcessor: Gemini 2.0 Flash vision analysis
- VisionProcessorFactory: Factory for creating processors
- ShapeClassifier: Classifies detected shapes into UI components

Usage:
    from app.engine.vision import VisionProcessorFactory
    
    # Create processor based on settings
    processor = VisionProcessorFactory.create_from_settings()
    
    # Process an image
    shapes = processor.run("/path/to/sketch.png")

Configuration:
    Set VISION_PROVIDER in .env to choose the processor:
    - mock: OpenCV-based (no API key needed)
    - openai: GPT-4o Vision API
    - gemini: Gemini 2.0 Flash API
"""

from .base import (
    BaseVisionProcessor,
    PrimitiveShapeType,
    NormalizedBoundingBox,
    DetectedShape,
)

from .processor import (
    MockVisionProcessor,
    OpenAIVisionProcessor,
    GeminiVisionProcessor,
    VisionProcessorFactory,
)

from .classifier import (
    ShapeClassifier,
    UIHint,
    ClassificationRule,
    ClassifiedShape,
)

__all__ = [
    # Base classes
    "BaseVisionProcessor",
    "PrimitiveShapeType",
    "NormalizedBoundingBox",
    "DetectedShape",
    # Processors
    "MockVisionProcessor",
    "OpenAIVisionProcessor",
    "GeminiVisionProcessor",
    "VisionProcessorFactory",
    # Classifier
    "ShapeClassifier",
    "UIHint",
    "ClassificationRule",
    "ClassifiedShape",
]
