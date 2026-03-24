"""
Duiodle Code Generation Engine.

This module provides React + Tailwind + Framer Motion code generation
from enriched UI trees. It handles JSX rendering, motion prop spreading,
and template-based page generation.

Components:
    - ReactRenderer: Main renderer class for converting UI trees to React code
    - RenderConfig: Configuration options for rendering
    - RenderContext: Context passed during recursive rendering

Templates:
    - page.tsx.j2: Full page template with imports
    - component.tsx.j2: Standalone component template
    - layout.tsx.j2: Layout wrapper template

Usage:
    >>> from app.engine.codegen import ReactRenderer, render_tree_to_react
    >>> 
    >>> # Using the class
    >>> renderer = ReactRenderer(tailwind_mapper)
    >>> code = renderer.render(ui_tree)
    >>> 
    >>> # Using convenience function
    >>> code = render_tree_to_react(ui_tree)

Author: Duiodle Team
"""

from .react_renderer import (
    ReactRenderer,
    RenderConfig,
    RenderContext,
    OutputFormat,
    ComponentTag,
    render_tree_to_react,
    render_component,
)

__all__ = [
    # Main classes
    "ReactRenderer",
    "RenderConfig",
    "RenderContext",
    
    # Enums
    "OutputFormat",
    "ComponentTag",
    
    # Convenience functions
    "render_tree_to_react",
    "render_component",
]
