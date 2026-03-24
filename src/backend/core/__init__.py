"""
Duiodle Core Module.

This module contains the central pipeline orchestrator and core utilities
for the Duiodle AI-powered design platform.
"""

from backend.core.pipeline import (
    DuiodlePipeline,
    PipelineResult,
    PipelineStage,
    PipelineError,
    ComponentMetadata,
    GeneratedFiles,
    PipelineConfig,
    create_pipeline,
)

__all__ = [
    # Main pipeline
    "DuiodlePipeline",
    "create_pipeline",
    
    # Result types
    "PipelineResult",
    "ComponentMetadata",
    "GeneratedFiles",
    
    # Configuration
    "PipelineConfig",
    
    # Errors
    "PipelineError",
    "PipelineStage",
]
