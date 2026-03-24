"""
Motion Engine - Animation Metadata Injection System.

This module provides motion/animation metadata injection for UI trees.
It does NOT render animations or generate frontend code - it only
attaches motion metadata that can be translated to any animation system.

Components:
-----------
physics.py
    Motion presets with physics-based spring animations, easing functions,
    and stagger configurations. Provides framework-agnostic animation
    definitions.

resolver.py
    Main motion injection engine. Traverses themed layout trees and
    attaches appropriate animation metadata to eligible nodes based
    on component type and configuration.

Usage:
------
Basic motion injection:

    >>> from app.engine.motion import MotionResolver, get_motion_preset
    >>> 
    >>> resolver = MotionResolver(enable_motion=True)
    >>> animated_tree = resolver.apply_motion(tree, preset_name="slide_up")

Using convenience function:

    >>> from app.engine.motion import apply_motion_to_tree, MotionStrategy
    >>> 
    >>> result = apply_motion_to_tree(
    ...     tree,
    ...     preset_name="spring_pop",
    ...     enable_motion=True,
    ...     strategy=MotionStrategy.TYPE_BASED,
    ... )

Accessing presets:

    >>> from app.engine.motion import get_motion_preset, get_available_presets
    >>> 
    >>> preset = get_motion_preset("spring_bounce")
    >>> print(preset.to_dict())
    >>> 
    >>> all_presets = get_available_presets()

Custom spring animation:

    >>> from app.engine.motion import create_custom_spring
    >>> 
    >>> custom = create_custom_spring(
    ...     stiffness=300,
    ...     damping=20,
    ...     initial_props={"opacity": 0, "scale": 0.5},
    ...     animate_props={"opacity": 1, "scale": 1},
    ... )

Output Format:
--------------
Motion metadata injected into nodes:

    {
        "type": "button",
        "style": {...},
        "motion": {
            "initial": {"opacity": 0, "y": 20},
            "animate": {"opacity": 1, "y": 0},
            "transition": {"duration": 0.4, "ease": "easeOut"},
            "whileHover": {"scale": 1.02},
            "whileTap": {"scale": 0.98},
            "_preset": "button_interactive",
            "_depth": 2
        },
        "children": [...]
    }

Notes:
------
- The motion layer is independent of theme and layout engines
- Motion can be disabled globally or per-node
- Spacer and divider nodes are excluded by default
- Original trees are never mutated (deep copy is performed)
"""

# Physics module exports
from .physics import (
    # Enums
    TransitionType,
    EasingFunction,
    # Config dataclasses
    SpringConfig,
    TweenConfig,
    StaggerConfig,
    # Main preset class
    MotionPreset,
    # Preset instances (commonly used)
    PRESET_FADE_IN,
    PRESET_SLIDE_UP,
    PRESET_SLIDE_LEFT,
    PRESET_SCALE_IN,
    PRESET_SPRING_POP,
    PRESET_SPRING_BOUNCE,
    PRESET_SPRING_GENTLE,
    PRESET_BUTTON_INTERACTIVE,
    PRESET_CARD_INTERACTIVE,
    PRESET_STAGGER_CHILDREN,
    PRESET_VIEWPORT_FADE,
    PRESET_NONE,
    # Registry functions
    get_motion_preset,
    get_available_presets,
    register_preset,
    get_preset_for_component,
    # Factory functions
    create_custom_spring,
    create_stagger_preset,
)

# Resolver module exports
from .resolver import (
    # Enums
    MotionStrategy,
    StaggerDirection,
    # Config classes
    MotionConfig,
    MotionContext,
    # Main resolver class
    MotionResolver,
    # Convenience functions
    apply_motion_to_tree,
    strip_motion_from_tree,
    get_motion_summary,
)

__all__ = [
    # Physics - Enums
    "TransitionType",
    "EasingFunction",
    # Physics - Config
    "SpringConfig",
    "TweenConfig",
    "StaggerConfig",
    "MotionPreset",
    # Physics - Preset instances
    "PRESET_FADE_IN",
    "PRESET_SLIDE_UP",
    "PRESET_SLIDE_LEFT",
    "PRESET_SCALE_IN",
    "PRESET_SPRING_POP",
    "PRESET_SPRING_BOUNCE",
    "PRESET_SPRING_GENTLE",
    "PRESET_BUTTON_INTERACTIVE",
    "PRESET_CARD_INTERACTIVE",
    "PRESET_STAGGER_CHILDREN",
    "PRESET_VIEWPORT_FADE",
    "PRESET_NONE",
    # Physics - Functions
    "get_motion_preset",
    "get_available_presets",
    "register_preset",
    "get_preset_for_component",
    "create_custom_spring",
    "create_stagger_preset",
    # Resolver - Enums
    "MotionStrategy",
    "StaggerDirection",
    # Resolver - Config
    "MotionConfig",
    "MotionContext",
    # Resolver - Main class
    "MotionResolver",
    # Resolver - Functions
    "apply_motion_to_tree",
    "strip_motion_from_tree",
    "get_motion_summary",
]
