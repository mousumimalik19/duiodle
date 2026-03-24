"""
Duiodle Engine Module

AI-powered processing engines for sketch analysis and UI generation.

Submodules:
- vision: Shape detection and classification
- layout: Component hierarchy and positioning
- theme: Design token application
- motion: Animation metadata injection
- codegen: React code generation
"""

from app.engine.vision import (
    MockVisionProcessor,
    OpenAIVisionProcessor,
    GeminiVisionProcessor,
    VisionProcessorFactory,
    ShapeClassifier,
)
from app.engine.layout import LayoutResolver
from app.engine.theme import ThemeProvider, TailwindMapper
from app.engine.motion import MotionResolver
from app.engine.codegen import ReactRenderer

__all__ = [
    # Vision
    "MockVisionProcessor",
    "OpenAIVisionProcessor",
    "GeminiVisionProcessor",
    "VisionProcessorFactory",
    "ShapeClassifier",
    # Layout
    "LayoutResolver",
    # Theme
    "ThemeProvider",
    "TailwindMapper",
    # Motion
    "MotionResolver",
    # Codegen
    "ReactRenderer",
]
